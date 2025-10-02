from __future__ import annotations

from typing import TYPE_CHECKING

from bond import Bond
from brick import FullBrick, HalfBrick
from config import (
    BRICK_LENGTH,
    HALF_BRICK_LENGTH,
    HEAD_JOINT_LENGTH,
)
from course import Course

if TYPE_CHECKING:
    from wall import Wall


class StretcherBond(Bond):
    MIN_WIDTH = BRICK_LENGTH + HALF_BRICK_LENGTH + HEAD_JOINT_LENGTH
    INCREMENT = HALF_BRICK_LENGTH + HEAD_JOINT_LENGTH

    def __init__(self):
        super().__init__(name="Stretcher Bond")
        self.min_width = self.MIN_WIDTH
        self.increment = self.INCREMENT

    def create_course(self, row: int, wall: Wall) -> Course:
        """Create a course for the given row number."""
        course = Course(width=wall.width)

        if row % 2 != 0:
            course.append(HalfBrick(), row)

        while True:
            brick = FullBrick()
            # Add bricks until we can no longer fit one
            if not course.append(brick, row):
                break

        # Add a half brick if there is enough space
        remaining_width = wall.width - course.width()
        if remaining_width >= HALF_BRICK_LENGTH:
            course.append(HalfBrick(), row)

        return course
