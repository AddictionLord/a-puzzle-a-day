import datetime
from typing import Dict, FrozenSet, List, Tuple, Union

Cell = Tuple[int, int]
Shape = FrozenSet[Cell]
Placements = Dict[str, Shape]
Targets = Tuple[Cell, Cell, Cell]

ROWS = 6
COLS = 9

MONTHS: List[str] = [
    "LED",
    "ÚNO",
    "BŘE",
    "DUB",
    "KVĚ",
    "ČVN",
    "ČVC",
    "SRP",
    "ZÁŘ",
    "ŘÍJ",
    "LIS",
    "PRO",
]
WEEKDAYS: List[str] = ["Po", "Út", "St", "Čt", "Pá", "So", "Ne"]
BLANK = ""

LAYOUT: List[List[Union[str, None]]] = [
    ["LED", "ÚNO", "BŘE", "DUB", "1", "2", "3", "Po", "Út"],
    ["KVĚ", "4", "5", "6", "7", "8", "9", "St", BLANK],
    ["ČVN", "10", "11", "12", "13", "31", "15", "Čt", BLANK],
    ["ČVC", "16", "17", "18", "19", "20", "21", "Pá", "So"],
    ["SRP", "22", "23", "24", "25", "26", "27", BLANK, "Ne"],
    ["ZÁŘ", "ŘÍJ", "LIS", "PRO", "28", "29", "30", "14", None],
]

PLAYABLE: FrozenSet[Cell] = frozenset(
    (r, c) for r in range(ROWS) for c in range(COLS) if LAYOUT[r][c] is not None
)

LABEL_TO_CELL: Dict[str, Cell] = {
    label: (r, c)
    for r, row in enumerate(LAYOUT)
    for c, label in enumerate(row)
    if label is not None and label != BLANK
}


def target_cells(month: int, day: int, weekday: int) -> Targets:
    if not 1 <= month <= 12:
        msg = f"month must be in 1..12, got {month}"
        raise ValueError(msg)
    if not 1 <= day <= 31:
        msg = f"day must be in 1..31, got {day}"
        raise ValueError(msg)
    if not 0 <= weekday <= 6:
        msg = f"weekday must be in 0..6 (Monday = 0), got {weekday}"
        raise ValueError(msg)
    return (
        LABEL_TO_CELL[MONTHS[month - 1]],
        LABEL_TO_CELL[str(day)],
        LABEL_TO_CELL[WEEKDAYS[weekday]],
    )


def targets_for_date(date: datetime.date) -> Targets:
    return target_cells(date.month, date.day, date.weekday())
