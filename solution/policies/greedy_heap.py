from solution.policies.helpers import build_urgent_trip

"""
With the use of the greedy.py, we try to deliver the urgent orders first with the
earliest delivery window as the priority
"""

def dispatch(parcel, context):
    return build_urgent_trip(parcel, context)