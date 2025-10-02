from enum import Enum

from config import (
    BRICK_LENGTH,
    HALF_BRICK_LENGTH,
    QUARTER_BRICK_LENGTH,
    THREE_QUARTER_BRICK_LENGTH,
)


class BrickState(Enum):
    EMPTY = "empty"
    PLACED = "placed"


class Brick:
    """
    A brick in the wall.
    """

    def __init__(self, length: int = BRICK_LENGTH):
        self.uid = None
        self.state = BrickState.EMPTY
        self.length = length

        self.row = -1
        self.brick_index = -1
        self.stride_index = -1

        # Horizontal placement (mm) set when added to a Layer
        self.x_start: int | None = None
        self.x_end: int | None = None
        self.supports: list[Brick] = []
        self.loads: list[Brick] = []

    def place(self):
        self.state = BrickState.PLACED

    @property
    def placed(self):
        return self.state == BrickState.PLACED

    def id(self):
        return f"R{self.row}B{self.brick_index}"


class FullBrick(Brick):
    def __init__(self):
        super().__init__(length=BRICK_LENGTH)


class HalfBrick(Brick):
    def __init__(self):
        super().__init__(length=HALF_BRICK_LENGTH)


class QuarterBrick(Brick):
    def __init__(self):
        super().__init__(length=QUARTER_BRICK_LENGTH)


class ThreeQuarterBrick(Brick):
    def __init__(self):
        super().__init__(length=THREE_QUARTER_BRICK_LENGTH)
