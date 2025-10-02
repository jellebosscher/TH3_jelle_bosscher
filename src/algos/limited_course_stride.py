from __future__ import annotations

from enum import Enum
from math import ceil
from typing import TYPE_CHECKING

from algorithm import BuildAlgorithm
from config import (
    BED_JOINT_HEIGHT,
    BRICK_HEIGHT,
    HEAD_JOINT_LENGTH,
)

if TYPE_CHECKING:
    from brick import Brick
    from wall import Course, Wall


class Direction(Enum):
    L2R = "left_to_right"
    R2L = "right_to_left"


class LimitedCourseStride(BuildAlgorithm):
    """Algorithm for building a wall with a limited row stride."""

    def __init__(
        self,
        wall: Wall,
        max_courses: int = 4,
        build_envelope: tuple[int, int] = (800, 1300),
    ) -> None:
        super().__init__(wall)
        self.max_courses = max_courses
        self.build_envelope = build_envelope  # (horizontal_width, vertical_height)
        self.direction = Direction.L2R

        self.sections = ceil(len(wall.courses) / max_courses)
        self.current_section = 0
        self.current_stride = 0
        self.platform_moves = 0

        self.current_stride_x_min = 0
        self.current_stride_y_min = 0

    def _get_current_wall_subset(self) -> list[Course]:
        return self.wall.courses[
            self.current_section
            * self.max_courses : (self.current_section + 1)
            * self.max_courses
        ][::-1]

    def get_directional_course(self, course: Course) -> Course:
        if self.direction == Direction.L2R:
            return course
        else:
            return list(reversed(course))

    def next_brick(self) -> Brick | None:
        """
        Return the next unplaced brick in the current section that satisfies
        brick_condition. If none found in the section, advance to the next
        section and continue. Returns None when all sections are exhausted.
        """
        while self.current_section < self.sections:
            # courses in this section (already reversed in helper)
            wall_subset = self._get_current_wall_subset()

            # Iterate from lowest to highest (or keep original ordering if desired)
            for course in reversed(wall_subset):
                for brick in self.get_directional_course(course):
                    if self.brick_condition(brick):
                        brick.stride_index = self.current_stride
                        return brick

            if all(brick.placed for brick in wall_subset[0]):
                if self.step_vertically():
                    continue
                return None
            else:
                if not self.step_horizontally(wall_subset[0]):
                    return None
        return None

    def complete_stride(self) -> int:
        """Place all remaining placeable bricks belonging to the current stride.

        Uses next_brick() for retrieval. Stops when:
        - No further bricks are available, or
        - The first brick of the next stride is encountered (it is buffered).
        Returns the number of bricks placed in the current stride.
        """
        start_stride = self.current_stride
        placed = 0
        while True:
            brick = self.next_brick()
            if brick is None:
                break
            if brick.stride_index != start_stride:
                break
            brick.place()
            placed += 1
        return placed

    def step_vertically(self) -> bool:
        """Advance to the next vertical section.

        We only increment the stride index if the new section's lowest course
        does not fit inside the current vertical build envelope window. The
        vertical envelope height is build_envelope[1].
        Direction is toggled each section for a serpentine pattern; horizontal
        window is reset appropriately.
        """
        self.current_section += 1
        if self.current_section >= self.sections:
            return False
        course_height = BRICK_HEIGHT + BED_JOINT_HEIGHT

        # Lowest course index in the new section
        section_height = self.max_courses * course_height

        reachable_height = self.current_stride_y_min + self.build_envelope[1]
        required_height = min(
            (self.current_section + 1) * section_height, self.wall.height
        )

        if required_height > reachable_height:
            self.current_stride_y_min += required_height - section_height
            self.platform_moves += 1

        # Toggle direction & reset horizontal position to the appropriate edge
        if self.direction == Direction.R2L:
            self.direction = Direction.L2R
            self.current_stride_x_min = 0
        else:  # L2R -> R2L
            self.direction = Direction.R2L
            horizontal_width = self.build_envelope[0]
            self.current_stride_x_min = max(0, self.wall.width - horizontal_width)
        return True

    def step_horizontally(self, top_course: Course) -> bool:
        """Slide the horizontal build envelope window based on placed bricks.

        Logic:
        - If no bricks in top_course are placed: no movement, no stride increment.
        - L2R: left boundary moves to (max placed x_end + head joint), clamped.
        - R2L: right boundary targets (min placed x_start - head joint); derive left boundary.
        - Stride index increments only if the window position actually changes.

        Assumptions:
        - brick.x_start < brick.x_end.
        - build_envelope width may be larger than wall width (clamped to 0 origin).
        """
        placed = [b for b in top_course if b.placed]
        if not placed:
            return False

        envelope_width = self.build_envelope[0]
        # Maximum valid left origin so that window fits inside wall width
        max_left_origin = max(0, self.wall.width - envelope_width)

        if self.direction == Direction.L2R:
            candidate = max(b.x_end for b in placed) + HEAD_JOINT_LENGTH
            new_x_min = min(max_left_origin, max(0, candidate))
        else:  # R2L
            right_edge_target = min(b.x_start for b in placed) - HEAD_JOINT_LENGTH
            new_x_min = right_edge_target - envelope_width
            new_x_min = max(0, new_x_min)
            new_x_min = min(new_x_min, max_left_origin)

        if new_x_min != self.current_stride_x_min:
            self.current_stride_x_min = new_x_min
            self.current_stride += 1

        return True

    def brick_condition(self, brick: Brick) -> bool:
        """
        Check if the brick is allowed to be placed:
        - Brick is within the build envelope.
        - Brick supports are place or is on the ground.
        """
        if brick.placed:
            return False

        x_max = self.current_stride_x_min + self.build_envelope[0]
        if not (self.current_stride_x_min <= brick.x_start < x_max):
            return False

        if not (self.current_stride_x_min < brick.x_end <= x_max):
            return False

        if brick.row == 0:
            return True

        return all(support.placed for support in brick.supports)

    def statistics(self) -> dict[str, int]:
        strides = self.current_stride + 1

        bricks = [b for course in self.wall.courses for b in course if b.placed]
        total_bricks = len(bricks)
        average_bricks_per_stride = total_bricks / (strides) if strides > 0 else 0
        total_courses = len(self.wall.courses)
        total_brick_length = sum(b.length for b in bricks)

        return {
            "total_robot_moves": strides - 1,
            "total_platform_moves": self.platform_moves,
            "average_bricks_per_stride": average_bricks_per_stride,
            "total_bricks": total_bricks,
            "total_brick_length": total_brick_length,
            "total_courses": total_courses,
        }
