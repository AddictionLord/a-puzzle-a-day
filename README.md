# a-puzzle-a-day

Game and solver for a Czech calendar pentomino puzzle: cover the 6×9 board with 10 pentominoes,
leaving only today's month, day and weekday visible. See [PLAN.md](PLAN.md).

```bash
pip install -e ".[dev]"
python -m pytest
```

## Play

```bash
python -m apad.game                                  # today's date
python -m apad.game --date 2026-10-16
python -m apad.game --month 11 --day 16 --weekday 4  # LIS 16 Pá (Monday = 0)
```

Commands: `show`, `pieces [NAME ...]` (orientations with their indices), `place F 3 2 4`
(piece, orientation index, row and column of the drawing's top-left corner), `remove F`, `reset`,
`plot [out.html]` (plotly board in the browser or written to HTML), `help`, `quit`.
