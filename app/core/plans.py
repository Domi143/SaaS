from dataclasses import dataclass


PLAN_FREE = "free"
PLAN_PLUS = "plus"
PLAN_PRO = "pro"


@dataclass(frozen=True)
class PlanLimits:
    name: str
    max_workspaces: int
    max_records: int
    storage_limit_bytes: int


PLAN_LIMITS: dict[str, PlanLimits] = {
    PLAN_FREE: PlanLimits(
        name=PLAN_FREE,
        max_workspaces=1,
        max_records=1_000,
        storage_limit_bytes=100 * 1024 * 1024,  # 100 MB
    ),
    PLAN_PLUS: PlanLimits(
        name=PLAN_PLUS,
        max_workspaces=5,
        max_records=50_000,
        storage_limit_bytes=5 * 1024 * 1024 * 1024,  # 5 GB
    ),
    PLAN_PRO: PlanLimits(
        name=PLAN_PRO,
        max_workspaces=50,
        max_records=500_000,
        storage_limit_bytes=50 * 1024 * 1024 * 1024,  # 50 GB
    ),
}


def get_plan_limits(plan_name: str) -> PlanLimits:
    return PLAN_LIMITS.get(plan_name, PLAN_LIMITS[PLAN_FREE])

