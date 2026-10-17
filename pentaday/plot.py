from typing import Dict, List

import plotly.graph_objects as go

from pentaday.board import COLS, LAYOUT, PLAYABLE, ROWS, Placements, Targets
from pentaday.pieces import PIECES

CELL_PX = 72
EMPTY_COLOR = "#f4efe6"
TARGET_COLOR = "#b91c1c"
GRID_COLOR = "#ffffff"
TEXT_COLOR = "#1f2937"
TARGET_TEXT_COLOR = "#ffffff"
PIECE_COLORS: Dict[str, str] = dict(
    zip(
        sorted(PIECES),
        [
            "#66c5cc",
            "#f6cf71",
            "#f89c74",
            "#dcb0f2",
            "#87c55f",
            "#9eb9f3",
            "#fe88b1",
            "#c9db74",
            "#8be0a4",
            "#b497e7",
        ],
        strict=True,
    )
)


def board_figure(placements: Placements, targets: Targets) -> go.Figure:
    owner = {cell: name for name, shape in placements.items() for cell in shape}
    shapes: List[Dict[str, object]] = []
    annotations: List[Dict[str, object]] = []
    for r, c in sorted(PLAYABLE):
        label = str(LAYOUT[r][c])
        name = owner.get((r, c))
        if name is not None:
            fill, text, color = PIECE_COLORS[name], f"<b>{name}</b>", TEXT_COLOR
        elif (r, c) in targets:
            fill, text, color = TARGET_COLOR, f"<b>{label}</b>", TARGET_TEXT_COLOR
        else:
            fill, text, color = EMPTY_COLOR, label, TEXT_COLOR
        shapes.append(_cell_rect(r, c, fill))
        annotations.append(
            {
                "x": c + 0.5,
                "y": r + 0.5,
                "text": text,
                "showarrow": False,
                "font": {"size": 16, "color": color},
            }
        )
    target_text = " ".join(str(LAYOUT[r][c]) for r, c in targets)
    figure = go.Figure()
    figure.update_layout(
        title={"text": f"Pentaday: {target_text}", "x": 0.5},
        shapes=shapes,
        annotations=annotations,
        width=COLS * CELL_PX + 40,
        height=ROWS * CELL_PX + 100,
        margin={"l": 20, "r": 20, "t": 70, "b": 20},
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
        showlegend=False,
    )
    figure.update_xaxes(range=[0, COLS], visible=False, constrain="domain")
    figure.update_yaxes(
        range=[ROWS, 0], visible=False, scaleanchor="x", scaleratio=1, constrain="domain"
    )
    return figure


def _cell_rect(r: int, c: int, fill: str) -> Dict[str, object]:
    return {
        "type": "rect",
        "x0": c,
        "x1": c + 1,
        "y0": r,
        "y1": r + 1,
        "fillcolor": fill,
        "line": {"color": GRID_COLOR, "width": 2},
        "layer": "below",
    }
