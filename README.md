# a-puzzle-a-day

Game and solver for a Czech calendar pentomino puzzle: cover the 6×9 board with 10 pentominoes,
leaving only today's month, day and weekday visible. See [PLAN.md](PLAN.md).

```bash
pip install -e ".[dev]"
python -m pytest
python -m pytest -m "not slow"
```

## Solver

```bash
python -m apad.solver                                  # first solution for today
python -m apad.solver --date 2026-10-16 --limit 3      # first three solutions for a date
python -m apad.solver --month 11 --day 16 --weekday 4 --all
python -m apad.solver --month 11 --day 16 --weekday 4 --count
python -m scripts.check_all_dates                      # all 12 x 31 x 7 triples
```

`--weekday` uses Monday = 0. From Python:

```python
from apad.board import target_cells
from apad.solver import count_solutions, solve, solve_partial

targets = target_cells(11, 16, 4)
first = solve(targets)
every = solve(targets, limit=None)
count_solutions(targets)
solve_partial(targets, {"I": first[0]["I"]}, limit=1)
```
