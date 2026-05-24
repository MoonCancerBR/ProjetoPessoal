def hex_color(value):
    """Converts a hex string like '#RRGGBB' to an (R, G, B) tuple."""
    if isinstance(value, tuple) and len(value) >= 3:
        return value
    value = str(value).lstrip("#")
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))
