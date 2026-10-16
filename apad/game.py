import argparse
import datetime
import sys
from typing import Callable, Dict, Iterable, Iterator, List, TextIO, Tuple, Union

from apad.ascii import render_ascii
from apad.board import (
    LAYOUT,
    PLAYABLE,
    Cell,
    Placements,
    Shape,
    Targets,
    target_cells,
    targets_for_date,
)
from apad.pieces import PIECES, orientations
from apad.plot import board_figure

HELP = """Commands:
  show                          print the board
  pieces [NAME ...]             draw the orientations of the remaining (or named) pieces
  place NAME ORIENT ROW COL     place a piece; ORIENT indexes its orientations (see `pieces`),
                                (ROW, COL) is where the drawing's top-left corner goes
  remove NAME                   take a piece off the board
  reset                         clear the board
  plot [FILE.html]              open the board in a browser, or write it to an HTML file
  help                          show this help
  quit                          leave the game"""

Handler = Callable[["GameState", List[str]], str]


class GameState:
    def __init__(self, targets: Targets) -> None:
        self.targets: Targets = targets
        self._placements: Placements = {}

    @property
    def placements(self) -> Placements:
        return dict(self._placements)

    def place(self, name: str, orientation: int, row: int, col: int) -> None:
        if name not in PIECES:
            msg = f"unknown piece {name!r}, expected one of {', '.join(sorted(PIECES))}"
            raise ValueError(msg)
        if name in self._placements:
            msg = f"piece {name} is already on the board; remove it first"
            raise ValueError(msg)
        shapes = orientations(name)
        if not 0 <= orientation < len(shapes):
            msg = f"piece {name} has orientations 0..{len(shapes) - 1}, got {orientation}"
            raise ValueError(msg)
        cells = frozenset((row + dr, col + dc) for dr, dc in shapes[orientation])
        self._check_cells(name, cells)
        self._placements[name] = cells

    def remove(self, name: str) -> None:
        if name not in self._placements:
            msg = f"piece {name!r} is not on the board"
            raise ValueError(msg)
        del self._placements[name]

    def reset(self) -> None:
        self._placements.clear()

    def is_solved(self) -> bool:
        covered = {cell for shape in self._placements.values() for cell in shape}
        return covered == PLAYABLE - set(self.targets)

    def remaining_pieces(self) -> List[str]:
        return [name for name in sorted(PIECES) if name not in self._placements]

    def _check_cells(self, name: str, cells: Shape) -> None:
        outside = sorted(cells - PLAYABLE)
        if outside:
            msg = f"piece {name} is off the board or on the notch at {_format_cells(outside)}"
            raise ValueError(msg)
        for other, shape in sorted(self._placements.items()):
            overlap = sorted(cells & shape)
            if overlap:
                msg = f"piece {name} would overlap piece {other} at {_format_cells(overlap)}"
                raise ValueError(msg)
        covered_targets = sorted(cells & set(self.targets))
        if covered_targets:
            labels = ", ".join(str(LAYOUT[r][c]) for r, c in covered_targets)
            msg = f"piece {name} would cover target cell(s) {labels}"
            raise ValueError(msg)


def main(argv: Union[List[str], None] = None) -> None:
    targets = parse_targets(argv)
    state = GameState(targets)
    prompt = "> " if sys.stdin.isatty() else ""
    run_repl(state, _read_lines(prompt), sys.stdout)


def parse_targets(argv: Union[List[str], None] = None) -> Targets:
    parser = argparse.ArgumentParser(
        prog="python -m apad.game",
        description="Play A-Puzzle-A-Day: cover everything but the month, day and weekday.",
    )
    parser.add_argument(
        "--date",
        type=datetime.date.fromisoformat,
        help="target date as YYYY-MM-DD (default: today)",
    )
    parser.add_argument("--month", type=int, help="month 1-12")
    parser.add_argument("--day", type=int, help="day 1-31")
    parser.add_argument("--weekday", type=int, help="weekday 0-6, Monday = 0")
    args = parser.parse_args(argv)
    explicit = [args.month, args.day, args.weekday]
    if any(value is not None for value in explicit):
        if args.date is not None:
            parser.error("--date cannot be combined with --month/--day/--weekday")
        if any(value is None for value in explicit):
            parser.error("--month, --day and --weekday must be given together")
        try:
            return target_cells(args.month, args.day, args.weekday)
        except ValueError as exc:
            parser.error(str(exc))
    return targets_for_date(args.date or datetime.date.today())


def run_repl(state: GameState, lines: Iterable[str], out: TextIO) -> None:
    out.write(f"Target: {_target_text(state)}\nType `help` for commands.\n\n{show(state)}\n")
    for line in lines:
        try:
            output, done = execute(state, line)
        except ValueError as exc:
            output, done = f"error: {exc}", False
        if output:
            out.write(output + "\n")
        if done:
            return


def execute(state: GameState, line: str) -> Tuple[str, bool]:
    tokens = line.split()
    if not tokens:
        return "", False
    command, args = tokens[0].lower(), tokens[1:]
    if command in ("quit", "exit", "q"):
        return "Bye.", True
    if command not in COMMANDS:
        msg = f"unknown command {tokens[0]!r}; type `help` for the list"
        raise ValueError(msg)
    return COMMANDS[command](state, args), False


def show(state: GameState) -> str:
    return render_ascii(state.placements, state.targets)


def format_orientations(name: str) -> str:
    drawings = [_shape_lines(shape) for shape in orientations(name)]
    height = max(len(drawing) for drawing in drawings)
    width = max(len(line) for drawing in drawings for line in drawing) + 3
    padded = [drawing + [""] * (height - len(drawing)) for drawing in drawings]
    rows = ["".join(f"{index:<{width}}" for index in range(len(drawings)))]
    rows += ["".join(f"{lines[i]:<{width}}" for lines in padded) for i in range(height)]
    return "\n".join([f"{name}:"] + ["  " + row.rstrip() for row in rows])


def _cmd_show(state: GameState, args: List[str]) -> str:
    _expect_args("show", args, 0)
    return f"Target: {_target_text(state)}\n{show(state)}"


def _cmd_pieces(state: GameState, args: List[str]) -> str:
    names = [arg.upper() for arg in args] or state.remaining_pieces()
    unknown = [name for name in names if name not in PIECES]
    if unknown:
        msg = f"unknown piece(s) {', '.join(unknown)}, expected one of {', '.join(sorted(PIECES))}"
        raise ValueError(msg)
    if not names:
        return "All pieces are on the board."
    return "\n\n".join(format_orientations(name) for name in names)


def _cmd_place(state: GameState, args: List[str]) -> str:
    _expect_args("place NAME ORIENT ROW COL", args, 4)
    try:
        orientation, row, col = (int(arg) for arg in args[1:])
    except ValueError:
        msg = f"ORIENT, ROW and COL must be integers, got {' '.join(args[1:])}"
        raise ValueError(msg) from None
    state.place(args[0].upper(), orientation, row, col)
    return _board_after_move(state)


def _cmd_remove(state: GameState, args: List[str]) -> str:
    _expect_args("remove NAME", args, 1)
    state.remove(args[0].upper())
    return _board_after_move(state)


def _cmd_reset(state: GameState, args: List[str]) -> str:
    _expect_args("reset", args, 0)
    state.reset()
    return show(state)


def _cmd_plot(state: GameState, args: List[str]) -> str:
    if len(args) > 1:
        msg = "usage: plot [FILE.html]"
        raise ValueError(msg)
    figure = board_figure(state.placements, state.targets)
    if args:
        figure.write_html(args[0])
        return f"Wrote {args[0]}"
    figure.show()
    return "Opened the board in the browser."


def _cmd_help(state: GameState, args: List[str]) -> str:
    return HELP


COMMANDS: Dict[str, Handler] = {
    "show": _cmd_show,
    "pieces": _cmd_pieces,
    "place": _cmd_place,
    "remove": _cmd_remove,
    "reset": _cmd_reset,
    "plot": _cmd_plot,
    "help": _cmd_help,
}


def _board_after_move(state: GameState) -> str:
    board = show(state)
    if state.is_solved():
        return f"{board}\n\nCongratulations, the puzzle is solved for {_target_text(state)}!"
    return f"{board}\nRemaining: {' '.join(state.remaining_pieces()) or '-'}"


def _expect_args(usage: str, args: List[str], count: int) -> None:
    if len(args) != count:
        msg = f"usage: {usage}"
        raise ValueError(msg)


def _target_text(state: GameState) -> str:
    return " ".join(str(LAYOUT[r][c]) for r, c in state.targets)


def _shape_lines(shape: Shape) -> List[str]:
    height = max(r for r, _ in shape) + 1
    width = max(c for _, c in shape) + 1
    return ["".join("#" if (r, c) in shape else "." for c in range(width)) for r in range(height)]


def _format_cells(cells: List[Cell]) -> str:
    return ", ".join(f"({r}, {c})" for r, c in cells)


def _read_lines(prompt: str) -> Iterator[str]:
    while True:
        try:
            yield input(prompt)
        except EOFError:
            return


if __name__ == "__main__":
    main()
