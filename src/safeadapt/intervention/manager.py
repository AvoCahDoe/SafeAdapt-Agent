"""Intervention manager — selects and applies strategies by severity."""

from datetime import datetime, timezone
from typing import Any

from safeadapt.intervention.base import Intervention, InterventionContext, InterventionResult
from safeadapt.intervention.goal_revalidation import GoalRevalidation
from safeadapt.intervention.human_confirmation import HumanConfirmation
from safeadapt.intervention.memory_rollback import MemoryRollback
from safeadapt.intervention.tool_restriction import ToolRestriction
from safeadapt.schemas.drift import DriftSeverity, DriftScore
from safeadapt.schemas.evaluation import FailureRecord, InterventionRecord
from safeadapt.schemas.experiment import InterventionSection, InterventionStrategy

SEVERITY_ORDER = {
    DriftSeverity.LOW: 0,
    DriftSeverity.MEDIUM: 1,
    DriftSeverity.HIGH: 2,
    DriftSeverity.CRITICAL: 3,
}

SEVERITY_STRATEGIES: dict[str, list[InterventionStrategy]] = {
    "medium": [InterventionStrategy.GOAL_REVALIDATION],
    "high": [
        InterventionStrategy.GOAL_REVALIDATION,
        InterventionStrategy.TOOL_RESTRICTION,
        InterventionStrategy.MEMORY_ROLLBACK,
    ],
    "critical": [
        InterventionStrategy.GOAL_REVALIDATION,
        InterventionStrategy.TOOL_RESTRICTION,
        InterventionStrategy.MEMORY_ROLLBACK,
        InterventionStrategy.HUMAN_CONFIRMATION,
    ],
}


def _severity_at_least(severity: DriftSeverity, minimum: str) -> bool:
    min_sev = DriftSeverity(minimum.lower())
    return SEVERITY_ORDER[severity] >= SEVERITY_ORDER[min_sev]


def classify_failure(violations: list[str], action: str) -> str:
    """Classify a failure category from violations."""
    text = " ".join(violations).lower()
    if "memory" in text or "contamination" in text:
        return "memory_contamination"
    if "protected" in text or "forbidden" in text or action in (
        "delete_file",
        "delete",
        "send_message",
    ):
        return "unsafe_tool_use"
    if violations:
        return "constraint_violation"
    return "goal_deviation"


class InterventionManager:
    """Applies configured interventions when drift exceeds thresholds."""

    def __init__(self, config: InterventionSection) -> None:
        self.config = config
        self._strategies: dict[str, Intervention] = {
            InterventionStrategy.GOAL_REVALIDATION.value: GoalRevalidation(),
            InterventionStrategy.TOOL_RESTRICTION.value: ToolRestriction(
                duration=config.restriction_duration
            ),
            InterventionStrategy.MEMORY_ROLLBACK.value: MemoryRollback(
                rollback_n=config.rollback_n
            ),
            InterventionStrategy.HUMAN_CONFIRMATION.value: HumanConfirmation(
                policy=config.human_policy
            ),
        }
        self.eligible = {s.value for s in config.strategies}

    def should_intervene(self, drift_score: DriftScore) -> bool:
        """Return True if drift warrants intervention."""
        if not self.config.enabled:
            return False
        if not drift_score.is_drifting:
            return False
        return _severity_at_least(drift_score.severity, self.config.min_severity)

    def select_strategies(self, severity: DriftSeverity) -> list[str]:
        """Select strategy names for a severity level, filtered by config."""
        key = severity.value
        if key == "low":
            return []
        candidates = SEVERITY_STRATEGIES.get(key, SEVERITY_STRATEGIES["medium"])
        return [s.value for s in candidates if s.value in self.eligible]

    def apply(
        self,
        drift_score: DriftScore,
        state: dict[str, Any],
        context: InterventionContext,
    ) -> list[InterventionResult]:
        """Apply all selected strategies and return results."""
        names = self.select_strategies(drift_score.severity)
        results: list[InterventionResult] = []
        for name in names:
            strategy = self._strategies.get(name)
            if strategy is None:
                continue
            results.append(strategy.apply(context, state))
        return results

    def to_records(
        self,
        interaction_id: int,
        drift_score: DriftScore,
        results: list[InterventionResult],
    ) -> list[InterventionRecord]:
        """Convert results to InterventionRecords for storage."""
        now = datetime.now(timezone.utc)
        return [
            InterventionRecord(
                interaction_id=interaction_id,
                timestamp=now,
                strategy=r.strategy,
                severity=drift_score.severity.value,
                drift_score=drift_score.combined_score,
                details=r.details,
            )
            for r in results
            if r.applied
        ]

    def to_failure_record(
        self,
        interaction_id: int,
        context: InterventionContext,
        results: list[InterventionResult],
    ) -> FailureRecord | None:
        """Build a FailureRecord when interventions follow objective violations."""
        if not context.violations:
            return None
        strategies = [r.strategy for r in results if r.applied]
        return FailureRecord(
            interaction_id=interaction_id,
            category=classify_failure(context.violations, context.recent_action),
            severity=context.severity,
            description="; ".join(context.violations)[:500],
            preceding_events=[],
            intervention=",".join(strategies) if strategies else None,
        )
