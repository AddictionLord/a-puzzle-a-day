import pytest

from apad.ascii import render_ascii
from apad.board import target_cells
from apad.pieces import PIECES, orientations

EXPECTED_ORIENTATIONS = {
    "F": 8,
    "I": 2,
    "L": 8,
    "N": 8,
    "P": 8,
    "T": 4,
    "U": 4,
    "V": 4,
    "Y": 8,
    "Z": 4,
}


def test_piece_set():
    """Ten pentominoes covering 50 cells."""
    assert sorted(PIECES) == sorted(EXPECTED_ORIENTATIONS)
    assert sum(len(orientations(name)[0]) for name in PIECES) == 50


@pytest.mark.parametrize("name", sorted(EXPECTED_ORIENTATIONS))
def test_orientation_counts(name):
    """Each piece has the expected number of distinct orientations, all normalized."""
    shapes = orientations(name)
    assert len(shapes) == EXPECTED_ORIENTATIONS[name]
    assert len(set(shapes)) == len(shapes)
    for shape in shapes:
        assert len(shape) == 5
        assert min(r for r, _ in shape) == 0
        assert min(c for _, c in shape) == 0


def test_unknown_piece():
    """Unknown piece name raises ValueError."""
    with pytest.raises(ValueError):
        orientations("X")


def test_render_ascii():
    """Renderer marks placed cells with the piece name and brackets targets."""
    targets = target_cells(10, 16, 4)
    text = render_ascii({"I": frozenset({(0, 0), (0, 1), (0, 2), (0, 3), (0, 4)})}, targets)
    lines = text.splitlines()
    assert len(lines) == 6
    assert lines[0].count("I") == 5
    assert "[16]" in text
    assert "[Pá]" in text
