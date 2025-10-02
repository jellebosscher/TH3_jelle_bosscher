from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from brick import Brick
    from wall import Wall


class BuildAlgorithm:
    """Abstract base class for different wall building algorithms."""

    def __init__(self, wall: Wall) -> None:
        self.wall = wall

    @abstractmethod
    def next_brick(self) -> Brick | None:
        raise NotImplementedError

    @abstractmethod
    def complete_stride(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def statistics(self) -> dict[str, int]:
        raise NotImplementedError

    def place_next_brick(self) -> bool:
        """Place the next brick in the build sequence, if available."""
        brick = self.next_brick()
        if brick is None:
            return False
        brick.place()
        return True
