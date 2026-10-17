import io
from pathlib import Path
from typing import Dict, List, Tuple

import plotly.graph_objects as go
import pytest

from pentaday.board import PLAYABLE, target_cells
from pentaday.game import (
    NO_SOLUTION,
    GameState,
    execute,
    format_orientations,
    parse_targets,
    run_repl,
)
from pentaday.pieces import PIECES, orientations
from pentaday.plot import PIECE_COLORS, TARGET_COLOR, board_figure

TARGETS = target_cells(11, 16, 4)

SOLUTION_GRID: List[str] = [
    "FFPPPNTTT",
    "IFFPPNNTL",
    "IFZVVVNTL",
    "I.ZZZVN.L",
    "IUUUZVYLL",
    "IU.UYYYY ",
]


def _moves_from_grid(grid: List[str]) -> Dict[str, Tuple[int, int, int]]:
    cells: Dict[str, List[Tuple[int, int]]] = {}
    for r, line in enumerate(grid):
        for c, name in enumerate(line):
            if name in PIECES:
                cells.setdefault(name, []).append((r, c))
    moves = {}
    for name, shape in cells.items():
        row = min(r for r, _ in shape)
        col = min(c for _, c in shape)
        normalized = frozenset((r - row, c - col) for r, c in shape)
        moves[name] = (orientations(name).index(normalized), row, col)
    return moves


SOLUTION: Dict[str, Tuple[int, int, int]] = _moves_from_grid(SOLUTION_GRID)


@pytest.fixture
def state() -> GameState:
    """Empty game for NOV 16 Fri."""
    return GameState(TARGETS)


@pytest.fixture
def solved_state() -> GameState:
    """Game for NOV 16 Fri with the known solution placed."""
    game = GameState(TARGETS)
    for name, (orientation, row, col) in SOLUTION.items():
        game.place(name, orientation, row, col)
    return game


def test_known_solution_is_solved(solved_state: GameState) -> None:
    """Placing a full known solution solves the puzzle."""
    assert solved_state.is_solved()
    assert solved_state.remaining_pieces() == []
    covered = set().union(*solved_state.placements.values())
    assert covered == PLAYABLE - set(TARGETS)


def test_partial_solution_not_solved(solved_state: GameState) -> None:
    """Removing one piece from a solution un-solves it."""
    solved_state.remove("Y")
    assert not solved_state.is_solved()
    assert solved_state.remaining_pieces() == ["Y"]


def test_place_remove_reset_round_trip(state: GameState) -> None:
    """Place, remove and reset keep placements and remaining pieces consistent."""
    state.place("I", 0, 0, 0)
    assert state.placements == {"I": frozenset((0, c) for c in range(5))}
    assert "I" not in state.remaining_pieces()
    state.remove("I")
    assert state.placements == {}
    assert state.remaining_pieces() == sorted(PIECES)
    state.place("I", 0, 0, 0)
    state.place("F", 0, 1, 4)
    state.reset()
    assert state.placements == {}
    assert len(state.remaining_pieces()) == len(PIECES)


def test_placements_is_a_copy(state: GameState) -> None:
    """Mutating the returned placements does not change the game."""
    state.place("I", 0, 0, 0)
    state.placements.clear()
    assert "I" in state.placements


def test_place_offsets_normalized_origin(state: GameState) -> None:
    """(row, col) offsets the normalized orientation shape."""
    state.place("T", 0, 0, 4)
    shape = orientations("T")[0]
    assert state.placements["T"] == frozenset((r, c + 4) for r, c in shape)


@pytest.mark.parametrize(
    ("setup", "move", "message"),
    [
        ([], ("W", 0, 0, 0), "unknown piece"),
        ([("I", 0, 0, 0)], ("I", 0, 1, 0), "already on the board"),
        ([], ("I", 2, 0, 0), "orientations 0..1"),
        ([], ("I", -1, 0, 0), "orientations 0..1"),
        ([], ("I", 0, 0, 5), "off the board"),
        ([], ("I", 0, -1, 0), "off the board"),
        ([], ("I", 1, 2, 9), "off the board"),
        ([], ("I", 0, 5, 4), "notch"),
        ([("I", 0, 0, 0)], ("F", 0, 0, 2), "overlap piece I"),
        ([], ("I", 1, 0, 1), "target cell"),
        ([], ("I", 0, 3, 3), "Fri"),
    ],
)
def test_place_invalid(
    state: GameState,
    setup: List[Tuple[str, int, int, int]],
    move: Tuple[str, int, int, int],
    message: str,
) -> None:
    """Each invalid move raises ValueError with a descriptive message and changes nothing."""
    for args in setup:
        state.place(*args)
    before = state.placements
    with pytest.raises(ValueError, match=message):
        state.place(*move)
    assert state.placements == before


def test_remove_missing_piece(state: GameState) -> None:
    """Removing a piece that is not on the board raises ValueError."""
    with pytest.raises(ValueError, match="not on the board"):
        state.remove("F")


def test_execute_place_and_remove(state: GameState) -> None:
    """The place and remove commands drive the game state."""
    output, done = execute(state, "place f 0 0 0")
    assert not done
    assert "F" in state.placements
    assert "Remaining:" in output
    execute(state, "remove F")
    assert state.placements == {}


def test_execute_show_and_reset(state: GameState) -> None:
    """Show prints the target and board; reset clears it."""
    execute(state, "place I 0 0 0")
    output, _ = execute(state, "show")
    assert output.startswith("Target: NOV 16 Fri")
    assert output.count("I") >= 5
    execute(state, "reset")
    assert state.placements == {}


def test_execute_pieces(state: GameState) -> None:
    """Pieces lists only the remaining pieces with orientation indices."""
    execute(state, "place I 0 0 0")
    output, _ = execute(state, "pieces")
    assert "I:" not in output
    assert "F:" in output
    assert "  0     1     2     3     4     5     6     7" in output
    single, _ = execute(state, "pieces t")
    assert single == format_orientations("T")


def test_format_orientations() -> None:
    """Orientation drawings show one indexed column per orientation."""
    lines = format_orientations("I").splitlines()
    assert lines[0] == "I:"
    assert lines[1].split() == ["0", "1"]
    assert lines[2].split() == ["#####", "#"]
    assert len(lines) == 7


@pytest.mark.parametrize(
    ("line", "message"),
    [
        ("dance", "unknown command"),
        ("place F 0 0", "usage: place"),
        ("place F a 0 0", "must be integers"),
        ("remove", "usage: remove"),
        ("show extra", "usage: show"),
        ("pieces Q", "unknown piece"),
        ("plot a.html b.html", "usage: plot"),
    ],
)
def test_execute_invalid(state: GameState, line: str, message: str) -> None:
    """Malformed commands raise ValueError."""
    with pytest.raises(ValueError, match=message):
        execute(state, line)


def test_execute_quit_help_blank(state: GameState) -> None:
    """Quit ends the loop, help lists commands, blank lines are ignored."""
    assert execute(state, "quit") == ("Bye.", True)
    assert "place NAME ORIENT ROW COL" in execute(state, "help")[0]
    assert execute(state, "   ") == ("", False)


def test_execute_plot_html(state: GameState, tmp_path: Path) -> None:
    """Plot with a file argument writes HTML."""
    path = tmp_path / "board.html"
    output, _ = execute(state, f"plot {path}")
    assert path.exists()
    assert str(path) in output


def test_run_repl_continues_after_errors_and_congratulates(state: GameState) -> None:
    """The REPL prints errors, keeps going, and congratulates on a solution."""
    moves = [f"place {name} {o} {r} {c}" for name, (o, r, c) in SOLUTION.items()]
    lines = ["bogus", "place I 9 0 0", *moves, "quit", "show"]
    out = io.StringIO()
    run_repl(state, lines, out)
    text = out.getvalue()
    assert "error: unknown command" in text
    assert "error: piece I has orientations" in text
    assert "Congratulations" in text
    assert text.rstrip().endswith("Bye.")


def test_parse_targets() -> None:
    """CLI date options resolve to target cells."""
    assert parse_targets(["--month", "11", "--day", "16", "--weekday", "4"]) == TARGETS
    assert parse_targets(["--date", "2026-10-16"]) == target_cells(10, 16, 4)


@pytest.mark.parametrize(
    "argv",
    [
        ["--month", "11", "--day", "16"],
        ["--date", "2026-10-16", "--month", "11", "--day", "16", "--weekday", "4"],
        ["--month", "13", "--day", "16", "--weekday", "4"],
        ["--date", "16.10.2026"],
    ],
)
def test_parse_targets_invalid(argv: List[str]) -> None:
    """Incomplete, conflicting or out-of-range CLI options exit with an error."""
    with pytest.raises(SystemExit):
        parse_targets(argv)


def test_board_figure_empty() -> None:
    """Empty board: one shape and one label per playable cell, targets highlighted."""
    figure = board_figure({}, TARGETS)
    assert isinstance(figure, go.Figure)
    assert len(figure.layout.shapes) == len(PLAYABLE)
    assert len(figure.layout.annotations) == len(PLAYABLE)
    highlighted = [s for s in figure.layout.shapes if s.fillcolor == TARGET_COLOR]
    assert sorted((int(s.y0), int(s.x0)) for s in highlighted) == sorted(TARGETS)
    assert not any(s.x0 == 8 and s.y0 == 5 for s in figure.layout.shapes)
    texts = {a.text for a in figure.layout.annotations}
    assert {"JAN", "FEB", "31", "14", "Sun"} <= texts
    assert figure.layout.yaxis.scaleanchor == "x"


def test_board_figure_solved(solved_state: GameState) -> None:
    """Solved board: placed cells show the piece letter in the piece color."""
    figure = board_figure(solved_state.placements, TARGETS)
    assert len(figure.layout.shapes) == len(PLAYABLE)
    piece_texts = {f"<b>{name}</b>" for name in PIECES}
    letters = [a.text for a in figure.layout.annotations if a.text in piece_texts]
    assert len(letters) == len(PLAYABLE) - len(TARGETS)
    fills = {s.fillcolor for s in figure.layout.shapes}
    assert fills == set(PIECE_COLORS.values()) | {TARGET_COLOR}
    assert len(set(PIECE_COLORS.values())) == len(PIECES)


def test_hint_move_keeps_puzzle_solvable(state: GameState) -> None:
    """Hint suggests a legal move after which the puzzle can still be completed."""
    output, done = execute(state, "hint")
    assert not done
    assert output.startswith("Try: place ")
    execute(state, output.removeprefix("Try: "))
    assert len(state.placements) == 1
    execute(state, "solve")
    assert state.is_solved()


def test_solve_completes_partial_position(state: GameState) -> None:
    """Solve keeps the pieces already placed and fills in the rest."""
    for name in ("F", "P", "T"):
        state.place(name, *SOLUTION[name])
    fixed = state.placements
    output, _ = execute(state, "solve")
    assert "Congratulations" in output
    assert all(state.placements[name] == shape for name, shape in fixed.items())


def test_hint_and_solve_dead_position(state: GameState) -> None:
    """A position that isolates a cell reports no solution and leaves the board unchanged."""
    cup = frozenset({(0, 0), (0, 2), (1, 0), (1, 1), (1, 2)})
    state.place("U", orientations("U").index(cup), 0, 0)
    assert execute(state, "hint") == (NO_SOLUTION, False)
    assert execute(state, "solve") == (NO_SOLUTION, False)
    assert list(state.placements) == ["U"]


def test_hint_when_solved(solved_state: GameState) -> None:
    """Hint on a solved board raises."""
    with pytest.raises(ValueError, match="already solved"):
        execute(solved_state, "hint")
