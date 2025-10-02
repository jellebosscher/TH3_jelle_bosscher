from brick import Brick, HalfBrick
from config import BRICK_LENGTH, HALF_BRICK_LENGTH, HEAD_JOINT_LENGTH
from course import Course


def test_course_append_and_width():
    course = Course(width=BRICK_LENGTH * 2 + HEAD_JOINT_LENGTH)
    assert course.append(Brick(), row=0)
    # After one brick width equals brick length
    assert course.width() == BRICK_LENGTH
    # Add second brick should fit exactly with joint
    assert course.append(Brick(), row=0)
    expected_width = BRICK_LENGTH * 2 + HEAD_JOINT_LENGTH
    assert course.width() == expected_width
    # Third should not fit
    assert not course.append(Brick(), 0)


def test_course_can_fit_multiple():
    course = Course(width=BRICK_LENGTH + HALF_BRICK_LENGTH + HEAD_JOINT_LENGTH)
    assert course.append(Brick(), 0)
    assert course.can_fit(HalfBrick())
    assert course.append(HalfBrick(), 0)
    # No more room
    assert not course.can_fit(HalfBrick())
