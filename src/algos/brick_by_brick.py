from __future__ import annotations

from typing import TYPE_CHECKING

from algorithm import BuildAlgorithm

if TYPE_CHECKING:
    from brick import Brick


class BrickByBrick(BuildAlgorithm):
    """
    Sequentially returns the next brick to place, does not take into
    account the build envelope or any aspects of the robot.

    This algorithm is primarily intended for testing and baseline comparisons.
    """

    def __init__(self, wall):
        super().__init__(wall)
        self.current_course = 0
        self.sections = len(wall.courses)

    def next_brick(self) -> Brick | None:

        while self.current_course < self.sections:
            wall_subset = self.wall.courses[
                self.current_course : self.current_course + 1
            ]

            for course in reversed(wall_subset):
                for brick in course:
                    if self.brick_condition(brick):
                        return brick

            self.current_course += 1
        return None

    def brick_condition(self, brick: Brick) -> bool:
        """
        Check if the brick is allowed to be placed:
        - Brick is within the build envelope.
        - Brick supports are place or is on the ground.
        """
        if brick.placed:
            return False

        if brick.row == 0:
            return True

        return all(support.placed for support in brick.supports)

    def statistics(self) -> dict[str, int]:
        bricks = [b for course in self.wall.courses for b in course if b.placed]
        total_bricks = len(bricks)
        total_courses = len(self.wall.courses)
        total_brick_length = sum(b.length for b in bricks)

        return {
            "total_bricks": total_bricks,
            "total_brick_length": total_brick_length,
            "total_courses": total_courses,
        }
