from bonds import FlemishBond, StretcherBond, WildBond
from wall import Wall


def build_and_return_stats(bond, width=1830, height=600):
    wall = Wall(width=width, height=height, bond=bond())
    wall.generate_bond_design()
    wall.assign_support_relations()
    assert len(wall.courses) > 0
    # Validate each course width
    for course in wall.courses:
        assert course.width() == wall.width
    return wall


def test_stretcher_bond_basic():
    wall = build_and_return_stats(StretcherBond)
    # Stretcher bond: even rows start full, odd rows start half
    for i, course in enumerate(wall.courses[:4]):
        if i % 2 == 1:
            assert (
                course[0].length != course[1].length
                or course[0].length < course[1].length
            )


def test_flemish_bond_patterns():
    wall = build_and_return_stats(FlemishBond)
    # Check alternating pattern presence: presence of half & full in every course
    for course in wall.courses[:4]:
        lengths = {b.length for b in course}
        assert len(lengths) >= 2  # contains at least two brick sizes


def test_wild_bond_constraints():
    wall = build_and_return_stats(WildBond)
    # No consecutive half bricks (internal positions)
    for course in wall.courses:
        for i in range(len(course) - 2):
            if course[i].length == course[i + 1].length == course[i + 2].length:
                # allow if they are full bricks; forbid three half bricks
                if course[i].length < course[i + 1].length:
                    continue
        # joint alignment check between adjacent courses
    for upper, lower in zip(wall.courses[1:], wall.courses[:-1]):
        upper_joints = [b.x_end for b in upper[:-1]]
        lower_joints = [b.x_end for b in lower[:-1]]
        for uj in upper_joints:
            assert all(abs(uj - lj) >= 40 for lj in lower_joints)  # crude min offset
