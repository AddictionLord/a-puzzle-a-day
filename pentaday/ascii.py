from pentaday.board import COLS, LAYOUT, ROWS, Placements, Targets

CELL_WIDTH = 6


def render_ascii(placements: Placements, targets: Targets) -> str:
    owner = {cell: name for name, shape in placements.items() for cell in shape}
    lines = []
    for r in range(ROWS):
        tokens = []
        for c in range(COLS):
            label = LAYOUT[r][c]
            if label is None:
                tokens.append(" " * CELL_WIDTH)
            elif (r, c) in owner:
                tokens.append(f"{owner[(r, c)]:^{CELL_WIDTH}}")
            elif (r, c) in targets:
                tokens.append(f"{'[' + label + ']':^{CELL_WIDTH}}")
            else:
                tokens.append(f"{label or '·':^{CELL_WIDTH}}")
        lines.append("".join(tokens).rstrip())
    return "\n".join(lines)
