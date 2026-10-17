import argparse
import datetime
import logging
import time
from functools import cache
from typing import Dict, Iterator, List, Tuple, Union

from pentaday.ascii import render_ascii
from pentaday.board import (
    COLS,
    PLAYABLE,
    ROWS,
    Cell,
    Placements,
    Shape,
    Targets,
    target_cells,
    targets_for_date,
)
from pentaday.pieces import PIECES, orientations

logger = logging.getLogger(__name__)

Placement = Tuple[int, int, Tuple[int, ...]]

PIECE_NAMES: Tuple[str, ...] = tuple(sorted(PIECES))
CELL_INDEX: Dict[Cell, int] = {cell: cell[0] * COLS + cell[1] for cell in sorted(PLAYABLE)}
INDEX_CELL: Dict[int, Cell] = {index: cell for cell, index in CELL_INDEX.items()}
BOARD_MASK: int = sum(1 << index for index in CELL_INDEX.values())

_NOT_FIRST_COL: int = sum(1 << index for (_, c), index in CELL_INDEX.items() if c != 0)
_NOT_LAST_COL: int = sum(1 << index for (_, c), index in CELL_INDEX.items() if c != COLS - 1)
_NUM_BITS: int = ROWS * COLS


def solve(targets: Targets, limit: Union[int, None] = 1) -> List[Placements]:
    return solve_partial(targets, {}, limit)


def count_solutions(targets: Targets) -> int:
    target_mask = _target_mask(targets)
    live = [p for p in _all_placements() if not p[1] & target_mask]
    return sum(1 for _ in _search(BOARD_MASK & ~target_mask, 0, live, []))


def solve_partial(
    targets: Targets, fixed: Placements, limit: Union[int, None] = 1
) -> List[Placements]:
    if limit is not None and limit < 1:
        msg = f"limit must be a positive integer or None, got {limit}"
        raise ValueError(msg)
    target_mask = _target_mask(targets)
    fixed_mask, used = _fixed_masks(fixed, target_mask)
    blocked = target_mask | fixed_mask
    live = [p for p in _all_placements() if not p[1] & blocked and not used >> p[0] & 1]
    solutions: List[Placements] = []
    for chosen in _search(BOARD_MASK & ~blocked, used, live, []):
        solutions.append(_to_placements(fixed, chosen))
        if limit is not None and len(solutions) >= limit:
            break
    return solutions


def main(argv: Union[List[str], None] = None) -> None:
    parser = argparse.ArgumentParser(description="Solve the Pentaday calendar puzzle.")
    parser.add_argument(
        "--date", type=datetime.date.fromisoformat, help="YYYY-MM-DD (default today)"
    )
    parser.add_argument("--month", type=int, help="1-12")
    parser.add_argument("--day", type=int, help="1-31")
    parser.add_argument("--weekday", type=int, help="0-6, Monday = 0")
    output = parser.add_mutually_exclusive_group()
    output.add_argument("--limit", type=int, default=1, help="number of solutions to print")
    output.add_argument("--all", action="store_true", help="print every solution")
    output.add_argument("--count", action="store_true", help="only count the solutions")
    args = parser.parse_args(argv)
    if args.limit < 1:
        parser.error("--limit must be at least 1")
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    targets = _parse_targets(parser, args)
    start = time.perf_counter()
    if args.count:
        count = count_solutions(targets)
        logger.info("%d solutions in %.3f s", count, time.perf_counter() - start)
        return
    solutions = solve(targets, None if args.all else args.limit)
    elapsed = time.perf_counter() - start
    for number, solution in enumerate(solutions, start=1):
        print(f"Solution {number}:")
        print(render_ascii(solution, targets))
        print()
    logger.info("%d solution(s) in %.3f s", len(solutions), elapsed)


def _search(
    empty: int, used: int, live: List[Placement], path: List[Placement]
) -> Iterator[List[Placement]]:
    if not empty:
        yield path
        return
    if not _regions_divisible(empty):
        return
    live = [p for p in live if not used >> p[0] & 1 and p[1] & empty == p[1]]
    for placement in _choose_column(empty, used, live):
        path.append(placement)
        yield from _search(empty ^ placement[1], used | 1 << placement[0], live, path)
        path.pop()


def _choose_column(empty: int, used: int, live: List[Placement]) -> List[Placement]:
    cell_counts = [0] * _NUM_BITS
    piece_counts = [0] * len(PIECE_NAMES)
    for piece, _, cells in live:
        piece_counts[piece] += 1
        for cell in cells:
            cell_counts[cell] += 1
    best_count = len(live) + 1
    best_cell = -1
    rest = empty
    while rest:
        bit = rest & -rest
        index = bit.bit_length() - 1
        if cell_counts[index] < best_count:
            best_count = cell_counts[index]
            best_cell = index
        rest ^= bit
    best_piece = -1
    for piece, count in enumerate(piece_counts):
        if not used >> piece & 1 and count < best_count:
            best_count = count
            best_piece = piece
    if best_count == 0:
        return []
    if best_piece >= 0:
        return [p for p in live if p[0] == best_piece]
    cell_bit = 1 << best_cell
    return [p for p in live if p[1] & cell_bit]


def _regions_divisible(empty: int) -> bool:
    rest = empty
    while rest:
        region = rest & -rest
        while True:
            grown = (
                region
                | ((region << 1) & _NOT_FIRST_COL)
                | ((region >> 1) & _NOT_LAST_COL)
                | (region << COLS)
                | (region >> COLS)
            ) & rest
            if grown == region:
                break
            region = grown
        if region.bit_count() % 5:
            return False
        rest ^= region
    return True


@cache
def _all_placements() -> Tuple[Placement, ...]:
    placements: List[Placement] = []
    for piece, name in enumerate(PIECE_NAMES):
        for shape in orientations(name):
            for dr in range(ROWS):
                for dc in range(COLS):
                    cells = [(r + dr, c + dc) for r, c in shape]
                    if all(cell in CELL_INDEX for cell in cells):
                        indices = tuple(sorted(CELL_INDEX[cell] for cell in cells))
                        placements.append((piece, _cells_mask(cells), indices))
    return tuple(placements)


def _cells_mask(cells: Union[List[Cell], Shape, Targets]) -> int:
    return sum(1 << CELL_INDEX[cell] for cell in cells)


def _target_mask(targets: Targets) -> int:
    if len(targets) != 3 or len(set(targets)) != 3:
        msg = f"targets must be three distinct cells, got {targets!r}"
        raise ValueError(msg)
    if not set(targets) <= PLAYABLE:
        msg = f"targets must be playable cells, got {targets!r}"
        raise ValueError(msg)
    return _cells_mask(targets)


def _fixed_masks(fixed: Placements, target_mask: int) -> Tuple[int, int]:
    fixed_mask = 0
    used = 0
    for name, shape in fixed.items():
        if name not in PIECES:
            msg = f"unknown piece {name!r}"
            raise ValueError(msg)
        if not set(shape) <= PLAYABLE:
            msg = f"piece {name} leaves the board: {sorted(shape)}"
            raise ValueError(msg)
        if _normalize(shape) not in orientations(name):
            msg = f"cells {sorted(shape)} are not an orientation of piece {name}"
            raise ValueError(msg)
        mask = _cells_mask(shape)
        if mask & target_mask:
            msg = f"piece {name} covers a target cell"
            raise ValueError(msg)
        if mask & fixed_mask:
            msg = f"piece {name} overlaps another fixed piece"
            raise ValueError(msg)
        fixed_mask |= mask
        used |= 1 << PIECE_NAMES.index(name)
    return fixed_mask, used


def _normalize(shape: Shape) -> Shape:
    min_r = min(r for r, _ in shape)
    min_c = min(c for _, c in shape)
    return frozenset((r - min_r, c - min_c) for r, c in shape)


def _to_placements(fixed: Placements, chosen: List[Placement]) -> Placements:
    solution: Placements = {name: frozenset(shape) for name, shape in fixed.items()}
    for piece, _, cells in chosen:
        solution[PIECE_NAMES[piece]] = frozenset(INDEX_CELL[index] for index in cells)
    return dict(sorted(solution.items()))


def _parse_targets(parser: argparse.ArgumentParser, args: argparse.Namespace) -> Targets:
    explicit = [args.month, args.day, args.weekday]
    if any(value is not None for value in explicit):
        if args.date is not None or any(value is None for value in explicit):
            parser.error("use either --date or all of --month, --day and --weekday")
        try:
            return target_cells(args.month, args.day, args.weekday)
        except ValueError as error:
            parser.error(str(error))
    return targets_for_date(args.date if args.date is not None else datetime.date.today())


if __name__ == "__main__":
    main()
