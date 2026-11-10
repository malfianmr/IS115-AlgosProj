"""Rule 5 with MIN_FILL = 70%: send a van only if at least 70% full,
unless waiting 10 more minutes would cause harm. See zones_wait.py."""

from typing import Dict, List

from solution.policies.zones_wait import dispatch_with_wait

MIN_FILL = 0.70


def dispatch(parcel: Dict[str, dict], context: dict) -> List[str]:
    return dispatch_with_wait(parcel, context, MIN_FILL)
