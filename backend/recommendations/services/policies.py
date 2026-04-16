from typing import Mapping, Protocol


INTERACTION_WEIGHTS = {
    "like": 5.0,
    "watched": 3.0,
    "watchlist": 2.5,
    "view": 1.0,
    "search": 0.5,
    "dislike": -3.0,
}


class InteractionWeightPolicy(Protocol):
    def weight_for(self, interaction_type: str) -> float: ...


class DefaultInteractionWeightPolicy:
    def __init__(self, weights: Mapping[str, float] | None = None):
        # Allow tests or future feature work to override the default action weights without editing engine code.
        self._weights = dict(weights or INTERACTION_WEIGHTS)

    def weight_for(self, interaction_type: str) -> float:
        return self._weights.get(interaction_type, 1.0)
