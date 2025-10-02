from loguru import logger

from bond import Bond
from config import (
    BED_JOINT_HEIGHT,
    BRICK_HEIGHT,
)
from course import Course


class Wall:
    """
    Represents a wall to be constructed, including its dimensions, bond type,
    and the courses of bricks that make up the wall.

    Functions are provided to adjust dimensions to legal sizes, generate the
    bond design, validate the design, and manage structural relationships
    between bricks required to determine valid placements.
    """

    def __init__(self, width: int, height: int, bond: Bond) -> None:
        self.width = width
        self.height = height
        self.bond = bond
        self.adjust_dimensions_to_bond()
        self.courses: list[Course] = []

    def adjust_dimensions_to_bond(self) -> None:
        """Snap width & height to nearest legal modular sizes."""
        vertical_unit = BRICK_HEIGHT + BED_JOINT_HEIGHT

        def adjust(dim: float, joint: float, unit: float, label: str) -> float:
            n = max(1, round((dim + joint) / unit))
            legal = n * unit - joint
            if abs(dim - legal) > 1e-6:
                logger.info(
                    f"Adjusted wall {label} from {dim} mm to {legal} mm (n={n})."
                )
                return legal
            logger.info(f"Wall {label} is already legal at {dim} mm. (n={n})")
            return legal

        self.width = self.bond.get_adjusted_width(self.width)
        self.height = adjust(self.height, BED_JOINT_HEIGHT, vertical_unit, "height")

    @property
    def complete(self) -> bool:
        return all(brick.placed for course in self.courses for brick in course)

    def generate_bond_design(self) -> list[Course]:
        logger.info("Building wall...")
        rows = int(
            (self.height + BED_JOINT_HEIGHT) // (BRICK_HEIGHT + BED_JOINT_HEIGHT)
        )
        logger.info(f"Wall will have {rows} rows.")
        self.courses = [self.bond.create_course(row, self) for row in range(rows)]

    def validate_design(self) -> bool:
        """Validate that all courses are equal to the wall width."""
        for i, course in enumerate(self.courses):
            course_width = course.width()
            if course_width != self.width:
                logger.error(
                    f"Course {i} width {course_width} mm does not match wall width {self.width} mm."
                )
                return False
        logger.info("All courses validated successfully.")
        return True

    def assign_support_relations(self) -> None:
        """Populate structural relationships between bricks."""
        if len(self.courses) < 2:
            return
        for below, current in zip(self.courses, self.courses[1:]):
            for brick in current:
                if brick.x_start is None or brick.x_end is None:
                    continue
                left = brick.x_start + 1
                right = brick.x_end - 1
                supports = [
                    b
                    for b in below
                    if b.x_start is not None
                    and b.x_end is not None
                    and not (b.x_end <= left or b.x_start >= right)
                ]
                for s in supports:
                    brick.supports.append(s)
                    s.loads.append(brick)

    def debug_support_relations(self) -> None:
        for i, course in enumerate(self.courses):
            logger.info(f"course {i}:")
            for b in course:
                logger.info(f"  Brick={b.id()} [{b.x_start},{b.x_end})")
                logger.info(
                    f"    Supports={[support.id() for support in b.supports] if b.supports else 'Ground'}"
                )
                logger.info(
                    f"    Loads={[load.id() for load in b.loads] if b.loads else 'None'}"
                )

    def validate_support_relations(self) -> None:
        for course in self.courses:
            for b in course:
                if b.row == 0:
                    if b.supports:
                        logger.error(
                            f"Brick {b.id()} on ground row should not have supports."
                        )
                else:
                    if not b.supports:
                        logger.error(
                            f"Brick {b.id()} should have supports but has none."
                        )

    def __str__(self) -> str:
        return "\n\n".join(str(course) for course in self.courses[::-1])
