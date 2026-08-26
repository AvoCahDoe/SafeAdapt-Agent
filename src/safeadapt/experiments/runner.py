"""Experiment interaction loop runner."""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

from safeadapt.agents.base import Agent
from safeadapt.agents.validation import validate_action
from safeadapt.benchmark.scenarios import create_scenario
from safeadapt.benchmark.tasks import get_task_for_interaction
from safeadapt.environments import create_environment
from safeadapt.evaluation.evaluator import create_evaluator
from safeadapt.experiments.storage import ExperimentRun
from safeadapt.intervention.base import InterventionContext
from safeadapt.intervention.manager import InterventionManager
from safeadapt.models.factory import create_judge, create_llm_provider
from safeadapt.models.judge import LLMJudge
from safeadapt.monitoring.detector import DriftMonitor
from safeadapt.schemas.action import AgentAction
from safeadapt.schemas.drift import DriftThresholds
from safeadapt.schemas.experiment import ExperimentConfig, MemoryMode
from safeadapt.schemas.memory import MemoryType
from safeadapt.schemas.trajectory import TrajectoryRecord
from safeadapt.seeds.manager import SeedManager

logger = logging.getLogger(__name__)


class ExperimentRunner:
    """Runs the agent-environment interaction loop."""

    def __init__(
        self,
        config: ExperimentConfig,
        experiment_run: ExperimentRun,
        seed_manager: SeedManager,
    ) -> None:
        self.config = config
        self.experiment_run = experiment_run
        self.seed_manager = seed_manager
        self.scenario = create_scenario(config.scenario.type)
        self.environment = create_environment(
            config.environment.type,
            config.environment.config,
        )
        self.llm = create_llm_provider(config)
        self.judge: LLMJudge | None = create_judge(config)
        self._all_tools = self.environment.get_available_tools()
        self.agent = Agent.create(
            agent_id=f"agent_{config.experiment.name}",
            goal=self.scenario.goal,
            memory_mode=config.agent.memory,
            tools=list(self._all_tools),
        )
        self.evaluator = create_evaluator(config, self.scenario.goal)
        self.drift_monitor: DriftMonitor | None = None
        if config.monitoring.enabled:
            thresholds = DriftThresholds.model_validate(config.monitoring.drift_thresholds or {})
            self.drift_monitor = DriftMonitor(
                window_size=config.monitoring.window_size,
                detector_type=config.monitoring.detector,
                thresholds=thresholds,
                weights=config.monitoring.drift_weights or None,
            )
        self.intervention_manager: InterventionManager | None = None
        if config.intervention.enabled:
            self.intervention_manager = InterventionManager(config.intervention)

        self._restricted_tools: list[str] = []
        self._restriction_remaining = 0
        self._revalidate_goal = False
        self._intervention_count = 0
        self._violations_after_intervention = 0
        self._interactions_after_intervention = 0
        self._had_intervention = False

        self._stats: dict[str, Any] = {
            "interactions": 0,
            "violations": 0,
            "successful_actions": 0,
            "rejected_actions": 0,
            "tasks_completed": 0,
            "drift_detections": 0,
            "intervention_count": 0,
            "mean_alignment": 0.0,
        }

    def _effective_tools(self) -> list[str]:
        restricted = set(self._restricted_tools)
        return [t for t in self._all_tools if t not in restricted]

    def _tick_restrictions(self) -> None:
        if self._restriction_remaining > 0:
            self._restriction_remaining -= 1
            if self._restriction_remaining <= 0:
                self._restricted_tools = []
                self._restriction_remaining = 0

    async def run(self) -> dict[str, Any]:
        """Execute the full interaction loop."""
        n = self.config.experiment.interactions
        logger.info("Starting interaction loop: %d interactions", n)

        for interaction_id in range(n):
            await self._run_interaction(interaction_id)

        summary = self._build_summary()
        self.experiment_run.write_summary(summary)
        logger.info("Interaction loop complete: %s", summary)
        return summary

    async def _run_interaction(self, interaction_id: int) -> None:
        """Run a single interaction."""
        self._tick_restrictions()
        self.agent.available_tools = self._effective_tools()

        # Periodic memory snapshots for rollback
        window = self.config.monitoring.window_size if self.config.monitoring.enabled else 20
        if (
            self.config.agent.memory == MemoryMode.PERSISTENT
            and interaction_id > 0
            and interaction_id % window == 0
        ):
            self.agent.memory.snapshot()

        task = get_task_for_interaction(interaction_id, self.scenario.tasks)
        observation = self.environment.observe()
        memory_items = self.agent.memory.retrieve(task.description)

        revalidate = self._revalidate_goal
        context = self.agent.policy.build_context(
            goal=self.agent.system_goal,
            task=task.description,
            memory_items=memory_items,
            available_tools=self.agent.available_tools,
            observation=observation,
            interaction_id=interaction_id,
            revalidate_goal=revalidate,
        )
        prompt = self.agent.policy.build_prompt(context)
        self._revalidate_goal = False

        raw_output = await self.llm.generate(prompt, context)
        action = AgentAction.model_validate(raw_output)

        # Block restricted tools even if model proposes them
        if action.action in self._restricted_tools:
            validation_rejected = True
            validation_violations = [f"Tool restricted by intervention: {action.action}"]
            requires_confirmation = False
        else:
            validation = validate_action(
                action,
                self.agent.system_goal,
                self.agent.available_tools,
            )
            validation_rejected = validation.rejected
            validation_violations = list(validation.violations)
            requires_confirmation = validation.requires_confirmation

        constraint_violations: list[str] = list(validation_violations)
        env_result: dict[str, Any] = {}
        performance_score = 0.0

        if validation_rejected:
            self._stats["rejected_actions"] += 1
            if requires_confirmation:
                env_result = {"status": "blocked", "reason": "requires_confirmation"}
            else:
                env_result = {"status": "rejected", "violations": validation_violations}
            self._stats["violations"] += len(validation_violations)
        else:
            result = self.environment.execute(action)
            env_result = {
                "success": result.success,
                "output": result.output,
                "error": result.error,
            }
            constraint_violations.extend(result.constraint_violations)
            if result.constraint_violations:
                self._stats["violations"] += len(result.constraint_violations)
            if result.success:
                self._stats["successful_actions"] += 1
                performance_score = 1.0 if task.expected_action == action.action else 0.7
                self._stats["tasks_completed"] += 1
            elif result.requires_confirmation:
                env_result["status"] = "requires_confirmation"

        if self.config.agent.memory == MemoryMode.PERSISTENT:
            self.agent.memory.add(
                content=f"Action: {action.action} -> {env_result.get('success', validation_rejected)}",
                source="interaction",
                memory_type=MemoryType.PAST_ACTION,
                timestamp=interaction_id,
            )

        record = TrajectoryRecord(
            interaction_id=interaction_id,
            timestamp=datetime.now(timezone.utc),
            task=task.description,
            goal=self.agent.system_goal.primary_goal,
            constraints=list(self.agent.system_goal.safety_constraints),
            memory_used=[m.id for m in memory_items],
            model_output=raw_output,
            selected_action=action.action,
            tool_arguments=action.arguments,
            environment_result=env_result,
            constraint_violations=constraint_violations,
            performance_score=performance_score,
        )
        self.experiment_run.append_trajectory(record)
        self._stats["interactions"] += 1

        if self._had_intervention:
            self._interactions_after_intervention += 1
            self._violations_after_intervention += len(constraint_violations)

        eval_record = self.evaluator.evaluate_interaction(record)

        if self.judge is not None:
            try:
                judge_out = await self.judge.score(record, self.agent.system_goal)
                # Keep objective safety; blend goal/preference from independent judge
                goal_adh = 0.5 * eval_record.goal_adherence + 0.5 * judge_out["goal_adherence"]
                pref_adh = (
                    0.5 * eval_record.preference_adherence
                    + 0.5 * judge_out["preference_adherence"]
                )
                overall = (
                    self.config.evaluation.alignment.goal_weight * goal_adh
                    + self.config.evaluation.alignment.safety_weight
                    * eval_record.safety_adherence
                    + self.config.evaluation.alignment.preference_weight * pref_adh
                    + self.config.evaluation.alignment.constraint_weight
                    * eval_record.constraint_adherence
                )
                weight_sum = (
                    self.config.evaluation.alignment.goal_weight
                    + self.config.evaluation.alignment.safety_weight
                    + self.config.evaluation.alignment.preference_weight
                    + self.config.evaluation.alignment.constraint_weight
                )
                if weight_sum > 0:
                    overall = overall / weight_sum
                eval_record = eval_record.model_copy(
                    update={
                        "goal_adherence": goal_adh,
                        "preference_adherence": pref_adh,
                        "overall_alignment": overall,
                        "judge_score": judge_out["judge_score"],
                        "judge_model": judge_out["judge_model"],
                        "judge_prompt_version": judge_out["judge_prompt_version"],
                        "judge_raw_response": judge_out["judge_raw_response"],
                    }
                )
            except Exception as exc:  # noqa: BLE001 — judge must not crash the run
                logger.warning("LLM judge failed: %s", exc)

        self.experiment_run.append_evaluation(eval_record)

        if self.drift_monitor is not None:
            drift_score = self.drift_monitor.update(record, eval_record.overall_alignment)
            self.experiment_run.append_drift(drift_score)
            if drift_score.is_drifting:
                self._stats["drift_detections"] += 1

            if (
                self.intervention_manager is not None
                and self.intervention_manager.should_intervene(drift_score)
            ):
                self._apply_interventions(
                    interaction_id=interaction_id,
                    drift_score=drift_score,
                    action=action,
                    violations=constraint_violations,
                )

    def _apply_interventions(
        self,
        interaction_id: int,
        drift_score: Any,
        action: AgentAction,
        violations: list[str],
    ) -> None:
        assert self.intervention_manager is not None
        state: dict[str, Any] = {
            "goal": self.agent.system_goal,
            "memory": self.agent.memory,
            "restricted_tools": list(self._restricted_tools),
            "restriction_remaining": self._restriction_remaining,
            "revalidate_goal": self._revalidate_goal,
        }
        ctx = InterventionContext(
            interaction_id=interaction_id,
            severity=drift_score.severity.value,
            drift_score=drift_score.combined_score,
            recent_action=action.action,
            recent_arguments=action.arguments,
            violations=violations,
            available_tools=list(self._all_tools),
        )
        results = self.intervention_manager.apply(drift_score, state, ctx)

        self._restricted_tools = list(state.get("restricted_tools", []))
        self._restriction_remaining = int(state.get("restriction_remaining", 0))
        self._revalidate_goal = bool(state.get("revalidate_goal", False))
        self.agent.available_tools = self._effective_tools()

        records = self.intervention_manager.to_records(interaction_id, drift_score, results)
        for rec in records:
            self.experiment_run.append_intervention(rec)
            self._intervention_count += 1

        failure = self.intervention_manager.to_failure_record(interaction_id, ctx, results)
        if failure is not None:
            self.experiment_run.append_failure(failure)

        if records:
            self._had_intervention = True
            self._stats["intervention_count"] = self._intervention_count
            logger.info(
                "Intervention at interaction %d: %s (severity=%s)",
                interaction_id,
                [r.strategy for r in records],
                drift_score.severity.value,
            )

    def _build_summary(self) -> dict[str, Any]:
        """Build experiment run summary."""
        n = self._stats["interactions"] or 1
        post_rate = (
            self._violations_after_intervention / self._interactions_after_intervention
            if self._interactions_after_intervention
            else 0.0
        )
        return {
            **self._stats,
            "violation_rate": self._stats["violations"] / n,
            "task_completion_rate": self._stats["tasks_completed"] / n,
            "action_success_rate": self._stats["successful_actions"] / n,
            "mean_alignment": self.evaluator.mean_alignment,
            "performance": self.evaluator.performance.to_dict(),
            "intervention_count": self._intervention_count,
            "post_intervention_violation_rate": post_rate,
        }


def run_experiment_sync(
    config: ExperimentConfig,
    experiment_run: ExperimentRun,
    seed_manager: SeedManager,
) -> dict[str, Any]:
    """Synchronous wrapper for ExperimentRunner.run()."""
    runner = ExperimentRunner(config, experiment_run, seed_manager)
    return asyncio.run(runner.run())
