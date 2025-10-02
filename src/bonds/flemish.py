from __future__ import annotations

from typing import TYPE_CHECKING

from loguru import logger

from bond import Bond
from brick import FullBrick, HalfBrick, QuarterBrick
from config import (
    BRICK_LENGTH,
    HALF_BRICK_LENGTH,
    HEAD_JOINT_LENGTH,
    QUARTER_BRICK_LENGTH,
)
from course import Course

if TYPE_CHECKING:
    from wall import Wall


class FlemishBond(Bond):

    # FB-HB-FB
    MIN_WIDTH = BRICK_LENGTH + HALF_BRICK_LENGTH + BRICK_LENGTH + HEAD_JOINT_LENGTH * 2
    # Allow HB-FB increments
    INCREMENT = BRICK_LENGTH + HALF_BRICK_LENGTH + HEAD_JOINT_LENGTH * 2

    def __init__(self):
        super().__init__(name="Flemish Bond")
        self.min_width = self.MIN_WIDTH
        self.increment = self.INCREMENT
        logger.info(
            f"Flemish Bond: min_width={self.min_width} mm, increment={self.increment} mm"
        )

    def create_course(self, row: int, wall: Wall) -> Course:
        """
        Creates a course of bricks for a given row number and wall width.
        - Even rows: Stretcher bond (alternating Full and Half bricks).
        - Odd rows: Flemish bond pattern.
        """

        course = Course(width=wall.width)

        if row % 2 == 0:
            course.append(FullBrick(), row)
            while True:
                half_b = HalfBrick()
                full_b = FullBrick()

                if course.can_fit_multiple([half_b, full_b]):
                    course.append(half_b, row)
                    course.append(full_b, row)
                else:
                    break
        else:
            # --- ODD ROWS: Flemish Bond Pattern ---
            # The required width for the fixed closing sequence
            # (Joint + Quarter + Joint + Half)
            closing_width = (
                HEAD_JOINT_LENGTH
                + QUARTER_BRICK_LENGTH
                + HEAD_JOINT_LENGTH
                + HALF_BRICK_LENGTH
            )

            # 1. Add starting sequence
            course.append(HalfBrick(), row)
            course.append(QuarterBrick(), row)
            course.append(FullBrick(), row)

            # 2. Fill the middle with alternating Half and Full bricks
            is_next_a_half = True
            while True:
                next_brick = HalfBrick() if is_next_a_half else FullBrick()

                # Check if the next brick PLUS the closing sequence will fit
                required_width_for_step = (
                    next_brick.length + HEAD_JOINT_LENGTH + closing_width
                )

                if course.width() + required_width_for_step <= course.width_limit:
                    course.append(next_brick, row)
                    is_next_a_half = not is_next_a_half
                else:
                    break  # Not enough space for the next brick and the closing sequence

            # 3. Add closing sequence
            course.append(QuarterBrick(), row)
            course.append(HalfBrick(), row)

        return course
