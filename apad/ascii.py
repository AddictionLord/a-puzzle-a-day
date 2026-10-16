from apad.board import COLS, LAYOUT, ROWS, Placements, Targets


def render_ascii(placements: Placements, targets: Targets) -> str:
    owner = {cell: name for name, shape in placements.items() for cell in shape}
    lines = []
    for r in range(ROWS):
        tokens = []
        for c in range(COLS):
            label = LAYOUT[r][c]
            if label is None:
                tokens.append("    ")
            elif (r, c) in owner:
                tokens.append(f" {owner[(r, c)]}  ")
            elif (r, c) in targets:
                tokens.append(f"[{label:^2}]" if len(label) <= 2 else f"[{label[:2]}]")
            else:
                tokens.append(f"{label:^4}" if label else " ·  ")
        lines.append("".join(tokens).rstrip())
    return "\n".join(lines)
