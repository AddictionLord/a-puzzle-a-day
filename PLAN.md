# A-Puzzle-A-Day: plan

## 1. Problem model

### Board (from the photo)

6 rows × 9 cols, `(row, col)`, row 0 = top, col 0 = left.

| r\c | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|---|---|---|---|---|---|---|---|---|---|
| 0 | LED | ÚNO | BŘE | DUB | 1 | 2 | 3 | Po | Út |
| 1 | KVĚ | 4 | 5 | 6 | 7 | 8 | 9 | St | · |
| 2 | ČVN | 10 | 11 | 12 | 13 | **31** | 15 | Čt | · |
| 3 | ČVC | 16 | 17 | 18 | 19 | 20 | 21 | Pá | So |
| 4 | SRP | 22 | 23 | 24 | 25 | 26 | 27 | · | Ne |
| 5 | ZÁŘ | ŘÍJ | LIS | PRO | 28 | 29 | 30 | **14** | ✗ |

- `✗` (5,8) is the notch: not part of the board. In the photo it is **bottom-right**, not top-right.
- `·` (1,8), (2,8), (4,7) are blank but playable: they must be covered.
- 31 and 14 are swapped relative to reading order. Encode exactly as engraved.
- Cell count: 12 months + 31 days + 7 weekdays + 3 blanks = 53 playable cells.

### Goal

Leave exactly **three** cells uncovered: month, day, weekday. 53 − 3 = 50 = 10 pentominoes × 5.

### Pieces

10 distinct free pentominoes, rotation and reflection allowed: **F I L N P T U V Y Z** (W and X are absent).
Identified from the photo; validated with a scratch solver: the board model is solvable for every one of
60 random (month, day, weekday) triples, and 16 LIS Pá has 168 solutions.

Orientation counts (sanity test): F 8, I 2, L 8, N 8, P 8, T 4, U 4, V 4, Y 8, Z 4 → 58.

### Date

Target = any (month, day, weekday) triple; default = today via `datetime.date.today()`.
Note: 16 Nov 2026 is a Monday; Friday 16th is 16 Oct 2026 (ŘÍJ).

## 2. Solver algorithm

Piece-first backtracking ("place piece 1, then piece 2, ...") branches over
piece × orientation × position and only discovers dead holes late. Use cell-first exact cover instead
(Knuth's Algorithm X):

- Exact-cover matrix: columns = 50 cells to cover + 10 piece columns; rows = every legal placement
  (piece, orientation, offset) that avoids the 3 target cells.
- Represent cells and placements as Python `int` bitmasks (53 bits).
- At each node pick the empty cell with the fewest candidate placements (MRV); the simplest variant,
  the lowest-index empty cell, already finds all 168 solutions for one date in ~6 s in pure Python.
- Prune: any connected empty region whose size is not a multiple of 5 → backtrack.
- Return the first solution, the first N, or all of them.

## 3. Repository layout

```
apad/
    __init__.py
    board.py      # step 0: layout, labels, Cell type, target_cells(month, day, weekday)
    pieces.py     # step 0: piece shapes, orientations(name)
    ascii.py      # step 0: render_ascii(placements, targets) -> str
    game.py       # agent A
    plot.py       # agent A: plotly renderer
    solver.py     # agent B
tests/
    test_board.py, test_pieces.py   # step 0
    test_game.py                    # agent A
    test_solver.py                  # agent B
scripts/
    check_all_dates.py              # agent B
pyproject.toml                      # step 0: ruff config, pytest, plotly dependency
```

### Shared contract (step 0, on `main`)

```python
Cell = Tuple[int, int]
Shape = FrozenSet[Cell]
Placements = Dict[str, Shape]

ROWS, COLS = 6, 9
LAYOUT: List[List[Union[str, None]]]
PLAYABLE: FrozenSet[Cell]


def target_cells(month: int, day: int, weekday: int) -> Tuple[Cell, Cell, Cell]: ...
def targets_for_date(date: datetime.date) -> Tuple[Cell, Cell, Cell]: ...


PIECES: Dict[str, List[str]]


def orientations(name: str) -> List[Shape]: ...


def render_ascii(placements: Placements, targets: Tuple[Cell, Cell, Cell]) -> str: ...
```

`month` is 1–12, `day` 1–31, `weekday` 0–6 with Monday = 0 (`datetime.date.weekday()`).

## 4. Work split

### Step 0: scaffold (orchestrator, committed to `main`)

The contract above with tests: 53 playable cells, total piece area 50, orientation counts, label
round-trip for every month/day/weekday. Both branches start from this commit, so they touch disjoint
files and cannot conflict.

### Agent A: `feat/game`

1. `GameState(targets)`: `place(name, orientation, row, col)`, `remove(name)`, `reset()`,
   `is_solved()`, `remaining_pieces()`. `place` raises `ValueError` for: unknown or already placed
   piece, out of board / notch, overlap, covering a target cell.
2. `apad/plot.py`: plotly figure of the board with labels, pieces colored, targets highlighted.
3. Interactive CLI `python -m apad.game [--date YYYY-MM-DD | --month M --day D --weekday W]`;
   commands: `show`, `pieces` (print each remaining piece's orientations with their indices),
   `place F 3 2 4`, `remove F`, `reset`, `plot`, `quit`.
4. `tests/test_game.py`: each invalid move raises; placing a known solution yields `is_solved()`.

### Agent B: `feat/solver`

1. `apad/solver.py`: placement precomputation, bitmask Algorithm X with MRV and region pruning;
   `solve(targets, limit: Union[int, None] = 1) -> List[Placements]`, `count_solutions(targets) -> int`.
2. CLI `python -m apad.solver [--date ... | --month --day --weekday] [--limit N | --all] [--count]`,
   prints solutions with `render_ascii`.
3. `scripts/check_all_dates.py`: every month × day 1–31 × weekday (2604 triples) has at least one
   solution; reports min/median/max solve time.
4. `tests/test_solver.py`: every returned solution covers all non-target cells exactly once and uses each
   piece once; `count_solutions` for 16 LIS Pá == 168 (cross-checks the scratch solver).

### Integration

1. Merge `feat/solver` first (depends only on step 0).
2. Merge `main` into `feat/game`, add a `hint` command (solver completes the current partial state,
   reveals one piece) and `solve`; merge.
3. Merge criteria for both PRs: `ruff check`, `ruff format --check`, `pytest` green.
