from algos import BrickByBrick, LimitedCourseStride
from bonds import StretcherBond
from wall import Wall


def test_brick_by_brick_places_all():
    wall = Wall(width=1830, height=600, bond=StretcherBond())
    wall.generate_bond_design()
    wall.assign_support_relations()
    algo = BrickByBrick(wall)
    placed = 0
    while True:
        nxt = algo.next_brick()
        if not nxt:
            break
        nxt.place()
        placed += 1
    assert wall.complete
    assert placed == sum(len(c) for c in wall.courses)


def test_limited_course_stride_progress():
    wall = Wall(width=1830, height=600, bond=StretcherBond())
    wall.generate_bond_design()
    wall.assign_support_relations()
    algo = LimitedCourseStride(wall, max_courses=3, build_envelope=(800, 1300))

    # Place a few strides
    strides = 0
    total_placed = 0
    for _ in range(5):
        placed = algo.complete_stride()
        if placed == 0:
            break
        total_placed += placed
        strides += 1

    assert total_placed > 0
    assert strides > 0
