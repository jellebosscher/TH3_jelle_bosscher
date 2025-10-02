from __future__ import annotations

import random
from typing import TYPE_CHECKING

from loguru import logger

from bond import Bond
from brick import FullBrick, HalfBrick, ThreeQuarterBrick
from config import (
    BED_JOINT_HEIGHT,
    BRICK_HEIGHT,
    HALF_BRICK_LENGTH,
    HEAD_JOINT_LENGTH,
    QUARTER_BRICK_LENGTH,
    THREE_QUARTER_BRICK_LENGTH,
)
from course import Course

if TYPE_CHECKING:
    from wall import Wall

from ortools.sat.python import cp_model


def solve_wild_brick(
    rows,
    cols_quarter,  # number of quarter-brick columns (full=4, half=2, three-quarter=3)
    max_stagger_steps=6,  # allowed maximum consecutive step transitions
    verbose=True,
) -> tuple[list[list[str]], list[tuple[str, int, int, int]]] | None:
    """
    Solve the Wild Bond layout using constraint programming.
    Returns a tuple of (placement grid, list of bricks) or None if no solution found.

    """
    model = cp_model.CpModel()

    R = rows
    C = cols_quarter

    # --- Variables ---
    full_start = {}
    half_start = {}
    threeq_start = {}

    # Possible start positions for each brick type
    for r in range(R):
        for s in range(C):
            if s + 4 <= C:
                full_start[(r, s)] = model.NewBoolVar(f"F_r{r}_s{s}")
            if s + 2 <= C:
                half_start[(r, s)] = model.NewBoolVar(f"H_r{r}_s{s}")
        # Three-quarter bricks only at start (0) and end (C-3) if they fit
        if C >= 3:
            threeq_start[(r, 0)] = model.NewBoolVar(f"T_r{r}_s0")
            if C - 3 != 0:  # avoid duplicate when C == 3
                threeq_start[(r, C - 3)] = model.NewBoolVar(f"T_r{r}_s{C-3}")

    # # Possible start positions for each brick type
    # for r in range(R):
    #     for s in range(C):
    #         if s + 4 <= C:
    #             full_start[(r, s)] = model.NewBoolVar(f"F_r{r}_s{s}")
    #         if s + 2 <= C:
    #             half_start[(r, s)] = model.NewBoolVar(f"H_r{r}_s{s}")
    #         if s + 3 <= C:
    #             threeq_start[(r, s)] = model.NewBoolVar(f"T_r{r}_s{s}")

    # # 3q bricks can only be at the very start or very end positions of a course
    # for r in range(R):
    #     for s in range(C):
    #         if (r, s) in threeq_start:
    #             # Only allow 3q bricks at position 0 or C-3
    #             if s != 0 and s != C - 3:
    #                 model.Add(threeq_start[(r, s)] == 0)

    # Coverage:
    # every cell can only be covered exactly once
    for r in range(R):
        for c in range(C):
            covering_vars = []
            for s in range(max(0, c - 3), c + 1):
                if (r, s) in full_start and s <= c <= s + 3:
                    covering_vars.append(full_start[(r, s)])
            for s in range(max(0, c - 1), c + 1):
                if (r, s) in half_start and s <= c <= s + 1:
                    covering_vars.append(half_start[(r, s)])
            for s in range(max(0, c - 2), c + 1):
                if (r, s) in threeq_start and s <= c <= s + 2:
                    covering_vars.append(threeq_start[(r, s)])
            model.Add(sum(covering_vars) == 1)

    # --- Joint variables ---
    # A joint is where a brick ends (at the quarter-brick level)
    # We create joint variables at every possible joint position (beyond the wall edges)
    # Endings are determined by tracing forwards from brick start positions
    end_at = {}
    for r in range(R):
        for b in range(C):
            ends = []
            if (r, b - 3) in full_start:
                ends.append(full_start[(r, b - 3)])
            if (r, b - 1) in half_start:
                ends.append(half_start[(r, b - 1)])
            if (r, b - 2) in threeq_start:
                ends.append(threeq_start[(r, b - 2)])
            if ends:
                end_at[(r, b)] = model.NewBoolVar(f"end_r{r}_at{b}")
                model.Add(sum(ends) >= 1).OnlyEnforceIf(end_at[(r, b)])
                model.Add(sum(ends) == 0).OnlyEnforceIf(end_at[(r, b)].Not())
            else:
                v = model.NewBoolVar(f"end_r{r}_at{b}_const0")
                model.Add(v == 0)
                end_at[(r, b)] = v

    # Joint variables: a joint exists where a brick ends and the next brick starts
    # Any cell boundary can be a joint (if we were using quarter bricks), except the wall edges
    # Joints are only valid if there is a brick ending before them
    # Since joints are between bricks, we sort of index them at the end of the previous brick
    joint = {}
    for r in range(R):
        for b in range(1, C):
            joint[(r, b)] = model.NewBoolVar(f"joint_r{r}_b{b}")
            model.Add(joint[(r, b)] == end_at[(r, b - 1)])

    # --- Constraint 1: No joints directly above each other ---
    for r in range(R - 1):
        for b in range(1, C):
            model.Add(joint[(r, b)] + joint[(r + 1, b)] <= 1)

    # --- Constraint 2: No two half bricks next to each other (except edges) ---
    for r in range(R):
        for b in range(1, C):
            end_half_var = half_start.get((r, b - 1), model.NewConstant(0))
            start_half_var = half_start.get((r, b), model.NewConstant(0))
            if 1 < b < C - 1:
                model.Add(end_half_var + start_half_var <= 1)

    # --- Constraint 3: Limit consecutive staggered steps (diagonals) ---
    step = {}
    for r in range(R - 1):
        for b in range(1, C):
            for d in (-1, 1):
                b2 = b + d
                if 1 <= b2 <= C - 1:
                    v = model.NewBoolVar(f"step_r{r}_b{b}_d{d}")
                    model.Add(v <= joint[(r, b)])
                    model.Add(v <= joint[(r + 1, b2)])
                    model.Add(v >= joint[(r, b)] + joint[(r + 1, b2)] - 1)
                    step[(r, b, d)] = v
                else:
                    step[(r, b, d)] = model.NewConstant(0)

    L = max_stagger_steps
    for d in (-1, 1):
        for r0 in range(0, R - L):
            for b in range(1, C):
                b_end = b + (L - 1) * d
                if 1 <= b_end <= C - 1:
                    trans_vars = [step[(r0 + i, b + i * d, d)] for i in range(L)]
                    model.Add(sum(trans_vars) <= L - 1)

    # --- Constraint 4: Limit long back-and-forth (zigzag) stepping ---
    # Prevents patterns like: joint at b, then b+1, then b, then b+1 ... (or the reverse)
    # for more than max_stagger_steps consecutive rows.
    # We build alternating joint sequences over adjacent column pairs (b,b+1) and (b,b-1).
    L2 = max_stagger_steps + 1
    # Zigzag over (b, b+1)
    for r0 in range(0, R - L2 + 1):
        for b in range(1, C - 1):  # need b and b+1 both valid joint columns
            pattern = [joint[(r0 + i, b + (i % 2))] for i in range(L2)]
            # Not all rows in this window may alternate perfectly
            model.Add(sum(pattern) <= L2 - 1)

    # Zigzag over (b, b-1)
    for r0 in range(0, R - L2 + 1):
        for b in range(2, C):  # need b and b-1 both valid
            pattern = [joint[(r0 + i, b - (i % 2))] for i in range(L2)]
            model.Add(sum(pattern) <= L2 - 1)

    # Objective: fewer half bricks
    total_half = (
        sum(half_start.values()) if half_start else model.NewIntVar(0, 0, "zero")
    )
    model.Minimize(total_half)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 30.0
    solver.parameters.num_search_workers = 8

    status = solver.Solve(model)
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        print("No solution found.")
        return None

    # Extract solution
    placement = [["." for _ in range(C)] for _ in range(R)]
    bricks = []
    for (r, s), v in full_start.items():
        if solver.Value(v):
            for x in range(s, s + 4):
                placement[r][x] = "F"
            bricks.append(("full", r, s, s + 3))
    for (r, s), v in half_start.items():
        if solver.Value(v):
            for x in range(s, s + 2):
                placement[r][x] = "H"
            bricks.append(("half", r, s, s + 1))
    for (r, s), v in threeq_start.items():
        if solver.Value(v):
            for x in range(s, s + 3):
                placement[r][x] = "T"
            bricks.append(("3q", r, s, s + 2))

    if verbose:
        print(f"Status: {solver.StatusName(status)}")
        for r in range(R):
            print(f"{r:02d}: {''.join(placement[r])}")

    return placement, bricks


class WildBond(Bond):
    """
    Wild Bond (Wildverband) implementated using constraint programming.
    """

    MIN_WIDTH = HALF_BRICK_LENGTH + THREE_QUARTER_BRICK_LENGTH + HEAD_JOINT_LENGTH
    INCREMENT = HALF_BRICK_LENGTH + HEAD_JOINT_LENGTH

    def __init__(self, seed: int = None) -> None:
        super().__init__(name="Wild Bond (SAT)")
        self.min_width = self.MIN_WIDTH
        self.increment = self.INCREMENT
        self.random = random.Random(seed)
        logger.info(
            f"Wild Bond: min_width={self.min_width} mm, increment={self.increment} mm"
        )

    def prepare_solution(self, wall: Wall, max_stagger_steps=6) -> None:
        cols_quarter = (wall.width - QUARTER_BRICK_LENGTH) // (
            QUARTER_BRICK_LENGTH + HEAD_JOINT_LENGTH
        ) + 1
        rows = (
            int((wall.height - BRICK_HEIGHT) // (BRICK_HEIGHT + BED_JOINT_HEIGHT)) + 1
        )

        result = solve_wild_brick(
            rows=rows,
            cols_quarter=cols_quarter,
            max_stagger_steps=max_stagger_steps,
            verbose=False,
        )
        if result is None:
            raise ValueError("No solution found for the given wall dimensions.")
        self.solution = result

    def create_course(self, row: int, wall: Wall) -> Course:
        """Create a course for the given row number."""
        if self.solution is None:
            raise ValueError(
                "No solution available for Wild Bond. Call prepare_solution() first."
            )
        placement, _ = self.solution
        course = Course(width=wall.width)
        i = 0
        while i < len(placement[row]):
            brick_code = placement[row][i]
            if brick_code == "F":
                brick = FullBrick()
                i += 4
            elif brick_code == "H":
                brick = HalfBrick()
                i += 2
            elif brick_code == "T":
                brick = ThreeQuarterBrick()
                i += 3
            else:
                raise ValueError(f"Unknown brick code '{brick_code}' in placement.")
            if not course.append(brick, row):
                logger.warning(f"Could not fit brick {brick} in course at row {row}.")
        return course
