import datetime

import pytest

from apad.board import BLANK, LAYOUT, PLAYABLE, target_cells, targets_for_date


def test_playable_cell_count():
    """Board has 53 playable cells: 12 months, 31 days, 7 weekdays, 3 blanks."""
    assert len(PLAYABLE) == 53
    assert (5, 8) not in PLAYABLE
    assert sum(label == BLANK for row in LAYOUT for label in row) == 3


@pytest.mark.parametrize("month", range(1, 13))
@pytest.mark.parametrize("day", range(1, 32))
def test_target_cells_distinct_and_playable(month, day):
    """Every month/day/weekday triple maps to three distinct playable cells."""
    for weekday in range(7):
        cells = target_cells(month, day, weekday)
        assert len(set(cells)) == 3
        assert set(cells) <= PLAYABLE


def test_engraved_quirks():
    """31 and 14 sit where engraved, not in reading order."""
    assert target_cells(1, 31, 0)[1] == (2, 5)
    assert target_cells(1, 14, 0)[1] == (5, 7)


def test_targets_for_date():
    """Friday 16 Oct 2026 maps to ŘÍJ, 16, Pá."""
    assert targets_for_date(datetime.date(2026, 10, 16)) == ((5, 1), (3, 1), (3, 7))


@pytest.mark.parametrize("args", [(0, 1, 0), (13, 1, 0), (1, 0, 0), (1, 32, 0), (1, 1, 7)])
def test_target_cells_invalid(args):
    """Out-of-range inputs raise ValueError."""
    with pytest.raises(ValueError):
        target_cells(*args)
