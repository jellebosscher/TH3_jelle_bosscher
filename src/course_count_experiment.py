from loguru import logger

from algos.limited_course_stride import LimitedCourseStride
from bonds import StretcherBond
from wall import Wall


def score(stats: dict) -> tuple[int, int, float]:
    """Return a tuple usable for selecting the best configuration.

    Order of optimization:
      1. Maximize average bricks per stride (efficiency) -> implemented as negative for min sort
      2. Minimize robot moves (total strides)
      3. Minimize platform moves (vertical relocations are expensive)
    """
    return (
        -stats.get("average_bricks_per_stride", 0.0),
        stats.get("total_robot_moves", 10**9),
        stats.get("total_platform_moves", 10**9),
    )


def run_experiment(
    width: int = 2300,
    height: int = 2000,
    max_courses_range: range = range(1, 9),
    build_envelope: tuple[int, int] = (800, 1300),
):
    """
    Run an experiment varying the max_courses parameter of LimitedCourseStride.
    Logs detailed statistics for each configuration and selects the best one based on defined criteria.

    For now, the wall dimensions and bond type are fixed.

    The best configuration is determined by:
    1. Maximizing average bricks per stride (least important)
    2. Minimizing total robot moves (second priority)
    3. Minimizing total platform moves (most important)

    This seems to correlate well with the average bricks per stride.

    Returns the best max_courses value and its statistics.
    """

    results: list[tuple[int, dict]] = []

    for i in max_courses_range:
        logger.info("")
        logger.info(f"--- Testing LimitedCourseStride with max_courses={i} ---")
        wall = Wall(width=width, height=height, bond=StretcherBond())
        wall.generate_bond_design()
        wall.assign_support_relations()
        algo = LimitedCourseStride(wall, max_courses=i, build_envelope=build_envelope)

        # Build the entire wall
        while True:
            placed = algo.complete_stride()
            if placed == 0:
                break
        if not wall.complete:
            logger.warning(
                f"Wall is not fully complete after building, skipping stats for max_courses={i}."
            )
            continue

        stats = algo.statistics()
        results.append((i, stats))
        logger.info("Statistics:")
        for key, value in stats.items():
            logger.info(f"  {key}: {value}")

    # Summary table
    logger.info("")
    logger.info("=== Summary ===")
    header = (
        f"{'max_courses':>11} | {'plat_moves':>10} | {'robot_moves':>11} | "
        f"{'avg_bricks/stride':>16} | {'total_bricks':>12} | {'courses':>7}"
    )
    logger.info(header)
    logger.info("-" * len(header))
    for i, stats in results:
        logger.info(
            f"{i:11d} | {stats['total_platform_moves']:10d} | {stats['total_robot_moves']:11d} | "
            f"{stats['average_bricks_per_stride']:16.2f} | {stats['total_bricks']:12d} | {stats['total_courses']:7d}"
        )

    best_i, best_stats = min(results, key=lambda t: score(t[1]))
    logger.info("")
    logger.info("=== Best Configuration ===")
    logger.info(
        f"max_courses={best_i} (platform_moves={best_stats['total_platform_moves']}, "
        f"robot_moves={best_stats['total_robot_moves']}, "
        f"avg_bricks/stride={best_stats['average_bricks_per_stride']:.2f})"
    )

    logger.info(
        "Selection criteria: minimize platform moves, then robot moves, then maximize average bricks per stride."
    )

    return best_i, best_stats


if __name__ == "__main__":
    run_experiment()
