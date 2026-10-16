from functools import cache
from typing import Dict, List, Set, Tuple

from apad.board import Cell, Shape

PIECES: Dict[str, List[str]] = {
    "F": [".##", "##.", ".#."],
    "I": ["#####"],
    "L": ["####", "#..."],
    "N": ["##..", ".###"],
    "P": ["##", "##", "#."],
    "T": ["###", ".#.", ".#."],
    "U": ["#.#", "###"],
    "V": ["#..", "#..", "###"],
    "Y": ["####", ".#.."],
    "Z": ["##.", ".#.", ".##"],
}


def orientations(name: str) -> List[Shape]:
    if name not in PIECES:
        msg = f"unknown piece {name!r}, expected one of {sorted(PIECES)}"
        raise ValueError(msg)
    return list(_orientations(name))


@cache
def _orientations(name: str) -> Tuple[Shape, ...]:
    cells = {(r, c) for r, row in enumerate(PIECES[name]) for c, ch in enumerate(row) if ch == "#"}
    seen: Set[Shape] = set()
    result: List[Shape] = []
    for flip in (False, True):
        current = {(r, -c) for r, c in cells} if flip else set(cells)
        for _ in range(4):
            current = {(c, -r) for r, c in current}
            shape = _normalize(current)
            if shape not in seen:
                seen.add(shape)
                result.append(shape)
    return tuple(sorted(result, key=sorted))


def _normalize(cells: Set[Cell]) -> Shape:
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return frozenset((r - min_r, c - min_c) for r, c in cells)
