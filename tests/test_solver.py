from typing import FrozenSet, List, Tuple

import pytest

from apad.board import PLAYABLE, Cell, Placements, Targets, target_cells
from apad.pieces import PIECES
from apad.solver import count_solutions, solve, solve_partial

LIS_16_PA = target_cells(11, 16, 4)


@pytest.fixture(scope="module")
def all_lis_16_pa() -> List[Placements]:
    """All solutions for 16 LIS Pá."""
    return solve(LIS_16_PA, limit=None)


def check_solution(solution: Placements, targets: Targets) -> None:
    assert sorted(solution) == sorted(PIECES)
    covered = [cell for shape in solution.values() for cell in shape]
    assert len(covered) == len(set(covered)) == 50
    assert set(covered) == PLAYABLE - set(targets)


def as_key(solution: Placements) -> FrozenSet[Tuple[str, FrozenSet[Cell]]]:
    return frozenset(solution.items())


@pytest.mark.parametrize(
    "date", [(1, 1, 0), (2, 29, 3), (5, 14, 6), (10, 16, 4), (11, 16, 4), (12, 31, 2)]
)
def test_first_solution_valid(date: Tuple[int, int, int]) -> None:
    """First solution covers every non-target cell once and uses each piece once."""
    targets = target_cells(*date)
    solutions = solve(targets)
    assert len(solutions) == 1
    check_solution(solutions[0], targets)


def test_count_solutions_lis_16_pa() -> None:
    """16 LIS Pá has 168 solutions, matching the scratch solver."""
    assert count_solutions(LIS_16_PA) == 168


def test_all_solutions_valid_and_distinct(all_lis_16_pa: List[Placements]) -> None:
    """Every enumerated solution is valid and no solution repeats."""
    assert len(all_lis_16_pa) == 168
    for solution in all_lis_16_pa:
        check_solution(solution, LIS_16_PA)
    assert len({as_key(s) for s in all_lis_16_pa}) == 168


@pytest.mark.parametrize("limit", [1, 2, 5, 167, 168, 1000])
def test_limit_prefix(all_lis_16_pa: List[Placements], limit: int) -> None:
    """limit=N returns the first min(N, total) solutions of the full enumeration."""
    assert solve(LIS_16_PA, limit=limit) == all_lis_16_pa[:limit]


@pytest.mark.parametrize("limit", [0, -1])
def test_limit_invalid(limit: int) -> None:
    """Non-positive limits raise ValueError."""
    with pytest.raises(ValueError):
        solve(LIS_16_PA, limit=limit)


@pytest.mark.parametrize(
    "targets", [((0, 0), (0, 0), (0, 1)), ((0, 0), (0, 1), (5, 8)), ((0, 0), (0, 1))]
)
def test_invalid_targets(targets: Targets) -> None:
    """Duplicate, off-board or missing target cells raise ValueError."""
    with pytest.raises(ValueError):
        solve(targets)


def test_solve_partial_valid(all_lis_16_pa: List[Placements]) -> None:
    """Completions keep the fixed pieces and match the filtered full enumeration."""
    reference = all_lis_16_pa[-1]
    fixed = {name: reference[name] for name in ("F", "L", "U")}
    completions = solve_partial(LIS_16_PA, fixed, limit=None)
    for solution in completions:
        check_solution(solution, LIS_16_PA)
    expected = {as_key(s) for s in all_lis_16_pa if all(s[name] == fixed[name] for name in fixed)}
    assert as_key(reference) in expected
    assert {as_key(s) for s in completions} == expected
    assert len(completions) == len(expected)


def test_solve_partial_limit(all_lis_16_pa: List[Placements]) -> None:
    """solve_partial honours limit and defaults to one completion."""
    fixed = {"I": all_lis_16_pa[0]["I"]}
    assert len(solve_partial(LIS_16_PA, fixed)) == 1
    assert len(solve_partial(LIS_16_PA, fixed, limit=3)) == 3


def test_solve_partial_complete(all_lis_16_pa: List[Placements]) -> None:
    """A full valid solution as fixed returns itself."""
    reference = all_lis_16_pa[0]
    assert solve_partial(LIS_16_PA, reference) == [reference]


def test_solve_partial_dead_end() -> None:
    """A valid partial placement that isolates a cell has no completion."""
    fixed = {
        "L": frozenset({(0, 1), (0, 2), (0, 3), (0, 4), (1, 1)}),
        "I": frozenset({(1, 0), (2, 0), (3, 0), (4, 0), (5, 0)}),
    }
    assert solve_partial(LIS_16_PA, fixed) == []


@pytest.mark.parametrize(
    "fixed",
    [
        {"X": frozenset({(0, 0), (0, 1), (0, 2), (0, 3), (0, 4)})},
        {"I": frozenset({(0, 0), (0, 1), (0, 2), (0, 3), (1, 0)})},
        {"I": frozenset({(0, 5), (0, 6), (0, 7), (0, 8), (0, 9)})},
        {"I": frozenset({(5, 4), (5, 5), (5, 6), (5, 7), (5, 8)})},
        {"I": frozenset({(3, 0), (3, 1), (3, 2), (3, 3), (3, 4)})},
        {
            "I": frozenset({(0, 0), (0, 1), (0, 2), (0, 3), (0, 4)}),
            "L": frozenset({(0, 4), (1, 4), (2, 4), (3, 4), (3, 5)}),
        },
    ],
    ids=["unknown-piece", "wrong-shape", "off-board", "notch", "covers-target", "overlap"],
)
def test_solve_partial_invalid(fixed: Placements) -> None:
    """Invalid fixed placements raise ValueError."""
    with pytest.raises(ValueError):
        solve_partial(LIS_16_PA, fixed)


@pytest.mark.slow
def test_every_month_day_solvable() -> None:
    """Every month and day 1-31 is solvable, cycling through weekdays."""
    for month in range(1, 13):
        for day in range(1, 32):
            targets = target_cells(month, day, (day + month) % 7)
            solutions = solve(targets)
            assert solutions
            check_solution(solutions[0], targets)
