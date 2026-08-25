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
from safeadapt.experiments.storage import ExperimentRun
from safeadapt.models.llm import LLMProvider
from safeadapt.models.mock import MockLLMProvider
from safeadapt.schemas.action import AgentAction
from safeadapt.schemas.experiment import ExperimentConfig, MemoryMode
from safeadapt.schemas.memory import MemoryType
from safeadapt.schemas.trajectory import TrajectoryRecord
from safeadapt.seeds.manager import SeedManager

logger = logging.getLogger(__name__)


def _create_llm_provider(config: ExperimentConfig) -> LLMProvider:
    """Create LLM provider from experiment config."""
    params = config.model.parameters
    if config.model.provider == "mock":
        return MockLLMProvider(
            seed=config.experiment.seed,
            drift_rate=params.get("drift_rate", 0.001),
            violation_probability=params.get("violation_probability", 0.01),
            drift_mode=params.get("drift_mode", "gradual"),
        )
    raise ValueError(f"Unsupported model provider: {config.model.provider}")


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
        self.llm = _create_llm_provider(config)
        self.agent = Agent.create(
            agent_id=f"agent_{config.experiment.name}",
            goal=self.scenario.goal,
            memory_mode=config.agent.memory,
            tools=self.environment.get_available_tools(),
        )
        self._stats: dict[str, Any] = {
            "interactions": 0,
            "violations": 0,
            "successful_actions": 0,
            "rejected_actions": 0,
            "tasks_completed": 0,
        }

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
        task = get_task_for_interaction(interaction_id, self.scenario.tasks)
        observation = self.environment.observe()
        memory_items = self.agent.memory.retrieve(task.description)

        context = self.agent.policy.build_context(
            goal=self.agent.system_goal,
            task=task.description,
            memory_items=memory_items,
            available_tools=self.agent.available_tools,
            observation=observation,
            interaction_id=interaction_id,
        )
        prompt = self.agent.policy.build_prompt(context)

        raw_output = await self.llm.generate(prompt, context)
        action = AgentAction.model_validate(raw_output)

        validation = validate_action(
            action,
            self.agent.system_goal,
            self.agent.available_tools,
        )

        constraint_violations: list[str] = list(validation.violations)
        env_result: dict[str, Any] = {}
        performance_score = 0.0

        if validation.rejected:
            self._stats["rejected_actions"] += 1
            if validation.requires_confirmation:
                env_result = {"status": "blocked", "reason": "requires_confirmation"}
            else:
                env_result = {"status": "rejected", "violations": validation.violations}
            self._stats["violations"] += len(validation.violations)
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
                content=f"Action: {action.action} -> {env_result.get('success', validation.rejected)}",
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

    def _build_summary(self) -> dict[str, Any]:
        """Build experiment run summary."""
        n = self._stats["interactions"] or 1
        return {
            **self._stats,
            "violation_rate": self._stats["violations"] / n,
            "task_completion_rate": self._stats["tasks_completed"] / n,
            "action_success_rate": self._stats["successful_actions"] / n,
        }


def run_experiment_sync(
    config: ExperimentConfig,
    experiment_run: ExperimentRun,
    seed_manager: SeedManager,
) -> dict[str, Any]:
    """Synchronous wrapper for ExperimentRunner.run()."""
    runner = ExperimentRunner(config, experiment_run, seed_manager)
    return asyncio.run(runner.run())
