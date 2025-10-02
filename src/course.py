from typing import Any

from brick import Brick
from config import (
    HEAD_JOINT_LENGTH,
)


class Course(list[Brick]):
    """
    A Course is a horizontal layer of bricks in a wall.
    It manages the placement of bricks within the course, ensuring they fit within the specified width.
    """

    def __init__(self, *args: Any, width: int = 2000, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.width_limit = width
        self._current_span_mm = 0

    def width(self) -> int:
        return sum(brick.length for brick in self) + HEAD_JOINT_LENGTH * (len(self) - 1)

    def append(self, brick: Brick, row: int) -> bool:
        """
        Append a brick to the course if it fits within the width limit.
        """
        if not self.can_fit(brick):
            return False

        if not self:
            brick.x_start = 0
        else:
            brick.x_start = self[-1].x_end + HEAD_JOINT_LENGTH

        brick.x_end = brick.x_start + brick.length
        brick.row = row
        brick.brick_index = len(self)
        super().append(brick)
        return True

    def can_fit(self, brick: Brick, width: int = None) -> bool:
        """
        Check if a brick can fit in the course, optionally within a given width.
        """
        width_required = brick.length + (HEAD_JOINT_LENGTH if self else 0)
        if width is None:
            width = self.width_limit
        return self.width() + width_required <= width

    def can_fit_multiple(self, bricks: list[Brick]) -> bool:
        total_length = sum(brick.length for brick in bricks)
        width_required = total_length + (
            HEAD_JOINT_LENGTH * (len(bricks) - 1) if self else 0
        )
        return self.width() + width_required <= self.width_limit
