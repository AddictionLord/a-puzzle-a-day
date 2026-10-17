import argparse
import logging
import statistics
import sys
import time
from typing import List, Tuple

from pentaday.board import WEEKDAYS, target_cells
from pentaday.solver import solve

logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Check that every (month, day 1-31, weekday) triple has a solution."
    )
    parser.add_argument("--months", type=int, nargs="+", default=list(range(1, 13)))
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    failures, times = check_dates(args.months)
    logger.info("checked %d triples, %d without a solution", len(times), len(failures))
    for month, day, weekday in failures:
        logger.info("  no solution: month %d, day %d, %s", month, day, WEEKDAYS[weekday])
    logger.info(
        "first-solution time: min %.4f s, median %.4f s, max %.4f s, total %.1f s",
        min(times),
        statistics.median(times),
        max(times),
        sum(times),
    )
    if failures:
        sys.exit(1)


def check_dates(months: List[int]) -> Tuple[List[Tuple[int, int, int]], List[float]]:
    failures: List[Tuple[int, int, int]] = []
    times: List[float] = []
    for month in months:
        for day in range(1, 32):
            for weekday in range(7):
                start = time.perf_counter()
                solutions = solve(target_cells(month, day, weekday), limit=1)
                times.append(time.perf_counter() - start)
                if not solutions:
                    failures.append((month, day, weekday))
    return failures, times


if __name__ == "__main__":
    main()
