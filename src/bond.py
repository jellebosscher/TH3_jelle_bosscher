from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    from wall import Course, Wall


class Bond:
    """
    Abstract base class for different brick bonds.
    """

    def __init__(self, name: str) -> None:
        self.name = name
        self.min_width: int = 0
        self.increment: int = 0

    def get_adjusted_width(self, wall_width: int) -> int:
        """
        Adjusts the wall width to the closest valid dimension for the bond.

        The method first ensures the width meets the minimum requirement, then
        adjusts it to the nearest multiple of the bond's increment.
        """
        adjusted_width = wall_width
        if adjusted_width < self.min_width:
            logger.warning(
                f"Wall width {adjusted_width} mm is less than minimum {self.min_width} mm for {self.name}. "
                f"Adjusting to {self.min_width} mm."
            )
            adjusted_width = self.min_width

        if self.increment > 0:
            remainder = (adjusted_width - self.min_width) % self.increment

            if remainder != 0:
                # If the remainder is more than half the increment, round up.
                if remainder > self.increment / 2:
                    new_width = adjusted_width + (self.increment - remainder)
                # Otherwise, round down (this includes the halfway point).
                else:
                    new_width = adjusted_width - remainder

                logger.warning(
                    f"Wall width {adjusted_width} mm does not conform to for {self.name}. "
                    f"Adjusting to closest width: {new_width} mm."
                )
                adjusted_width = new_width

        # If no adjustments were made, the original width was valid.
        if adjusted_width == wall_width:
            logger.info(f"Wall width {wall_width} mm is valid for {self.name}.")

        return adjusted_width

    @abstractmethod
    def create_course(self, row: int, wall: Wall) -> Course:
        pass

    def __str__(self) -> str:
        return self.name
