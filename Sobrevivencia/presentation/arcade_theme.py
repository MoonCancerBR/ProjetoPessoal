import math

import pygame

if __package__:
    from ..data.constants import COLORS, SCREEN_HEIGHT, SCREEN_WIDTH
    from .ui_utils import hex_color
else:
    from Sobrevivencia.data.constants import COLORS, SCREEN_HEIGHT, SCREEN_WIDTH
    from Sobrevivencia.presentation.ui_utils import hex_color


ARCADE = {
    "bg": "#05050A",
    "panel": "#0B1020",
    "panel_2": "#111827",
    "line": "#26385E",
    "line_hot": "#28D7FF",
    "text": "#FFF7D6",
    "muted": "#A7B0C7",
    "shadow": "#02030A",
    "coin": "#FFD447",
    "danger": "#FF3B58",
    "success": "#35F06B",
    "upgrade": "#D96CFF",
}


ALTAR_STYLE = {
    "weapon_altar": {"label": "ARMAS", "color": "#FF5C3B", "glyph": "W"},
    "stamps_altar": {"label": "SELOS", "color": "#28D7FF", "glyph": "S"},
    "skill_altar": {"label": "SKILLS", "color": "#D96CFF", "glyph": "K"},
    "stat_altar": {"label": "STATUS", "color": "#FFD447", "glyph": "+"},
    "black_market_altar": {"label": "MERCADO", "color": "#35F06B", "glyph": "$"},
}


def rgb(key_or_hex):
    return hex_color(ARCADE.get(key_or_hex, key_or_hex))


def arcade_color(name, fallback=None):
    return ARCADE.get(name, fallback or COLORS.get(name, "#FFFFFF"))


def altar_style(kind):
    return ALTAR_STYLE.get(kind, {"label": "ALTAR", "color": "#FFD447", "glyph": "A"})


def draw_background(surface, tick=0.0):
    surface.fill(rgb("bg"))
    grid = rgb("#0E2231")
    hot = rgb("#12394C")
    offset = int(tick * 18) % 64
    for x in range(-64 + offset, SCREEN_WIDTH + 64, 64):
        pygame.draw.line(surface, grid, (x, 0), (x + 190, SCREEN_HEIGHT), 1)
    for y in range(54, SCREEN_HEIGHT, 72):
        pygame.draw.line(surface, hot, (0, y), (SCREEN_WIDTH, y - 30), 1)
    horizon = SCREEN_HEIGHT - 126
    pygame.draw.line(surface, rgb("#28D7FF"), (0, horizon), (SCREEN_WIDTH, horizon), 1)
    for x in range(0, SCREEN_WIDTH, 32):
        alpha = 70 if (x // 32) % 2 == 0 else 34
        pygame.draw.line(surface, (*rgb("#28D7FF")[:3], alpha), (x, horizon), (x + 54, SCREEN_HEIGHT))
    for y in range(horizon + 20, SCREEN_HEIGHT, 20):
        pygame.draw.line(surface, rgb("#132C45"), (0, y), (SCREEN_WIDTH, y), 1)


def draw_panel(surface, rect, border="#28D7FF", fill="#0B1020", shadow=True, title_bar=False):
    rect = pygame.Rect(rect)
    if shadow:
        pygame.draw.rect(surface, rgb("shadow"), rect.move(5, 5))
    pygame.draw.rect(surface, rgb(fill), rect)
    pygame.draw.rect(surface, rgb(border), rect, width=2)
    inner = rect.inflate(-8, -8)
    pygame.draw.rect(surface, rgb("#1B2440"), inner, width=1)
    if title_bar:
        bar = pygame.Rect(rect.x + 2, rect.y + 2, rect.width - 4, 22)
        pygame.draw.rect(surface, rgb(border), bar)
        pygame.draw.rect(surface, rgb("#FFFFFF"), (bar.x + 8, bar.y + 6, 24, 2))
    return rect


def draw_title(surface, font_big, font_small, title, subtitle, y, tick=0.0):
    glow = 1.0 + math.sin(tick * 4.0) * 0.18
    rect = font_big.get_rect(title)
    x = SCREEN_WIDTH // 2 - rect.width // 2
    for dx, dy, col in [(-3, 0, "#D96CFF"), (3, 0, "#28D7FF"), (0, 3, "#02030A")]:
        font_big.render_to(surface, (x + dx, y + dy), title, rgb(col))
    font_big.render_to(surface, (x, y), title, rgb("text"))
    underline_w = int(rect.width * glow)
    pygame.draw.rect(surface, rgb("coin"), (SCREEN_WIDTH // 2 - underline_w // 2, y + rect.height + 8, underline_w, 3))
    if subtitle:
        sub_rect = font_small.get_rect(subtitle)
        font_small.render_to(surface, (SCREEN_WIDTH // 2 - sub_rect.width // 2, y + rect.height + 20), subtitle, rgb("muted"))


def draw_button(surface, font, rect, text, color, selected=False, hover=False):
    rect = pygame.Rect(rect)
    base = rgb(color)
    border = rgb("coin") if selected else (tuple(min(255, c + 34) for c in base) if hover else base)
    fill = rgb("#101827") if not selected else tuple(max(0, c // 5) for c in base)
    pygame.draw.rect(surface, rgb("shadow"), rect.move(4, 4))
    pygame.draw.rect(surface, fill, rect)
    pygame.draw.rect(surface, border, rect, width=3 if selected else 2)
    pygame.draw.rect(surface, rgb("#FFFFFF"), (rect.x + 8, rect.y + 6, 28, 2))
    if hover or selected:
        pygame.draw.rect(surface, (*border[:3], 42), rect.inflate(8, 8), width=2)
    surf, s_rect = font.render(text.upper(), rgb("text"))
    surface.blit(surf, (rect.centerx - s_rect.width // 2, rect.centery - s_rect.height // 2))
    return rect


def draw_badge(surface, font, rect, label, color="#28D7FF"):
    rect = pygame.Rect(rect)
    pygame.draw.rect(surface, rgb("#111827"), rect)
    pygame.draw.rect(surface, rgb(color), rect, width=2)
    surf, s_rect = font.render(label, rgb("text"))
    surface.blit(surf, (rect.centerx - s_rect.width // 2, rect.centery - s_rect.height // 2))


def draw_slot(surface, rect, color="#26385E", active=False):
    rect = pygame.Rect(rect)
    pygame.draw.rect(surface, rgb("#080C18"), rect)
    pygame.draw.rect(surface, rgb(color if active else "#26385E"), rect, width=2 if active else 1)


ITEM_ICON_STYLE = {
    "storm_core": ("#28D7FF", "bolt"),
    "guardian_plate": ("#FFD447", "shield"),
    "magnet_orb": ("#D96CFF", "magnet"),
    "chrono_boots": ("#35F06B", "boot"),
    "blade_relay": ("#FF5C3B", "blade"),
}


def draw_pixel_icon(surface, rect, key, color=None, label=None):
    rect = pygame.Rect(rect)
    color = rgb(color or ITEM_ICON_STYLE.get(key, ("#28D7FF", ""))[0])
    kind = ITEM_ICON_STYLE.get(key, ("", key))[1]
    pygame.draw.rect(surface, rgb("#080C18"), rect)
    pygame.draw.rect(surface, color, rect, width=2)
    cx, cy = rect.center
    unit = max(2, rect.width // 10)

    if kind == "bolt":
        pts = [
            (cx - unit, rect.y + unit * 2),
            (cx + unit * 2, rect.y + unit * 2),
            (cx, cy),
            (cx + unit * 2, cy),
            (cx - unit * 2, rect.bottom - unit * 2),
            (cx, cy + unit),
            (cx - unit * 2, cy + unit),
        ]
        pygame.draw.polygon(surface, color, pts)
    elif kind == "shield":
        pts = [(cx, rect.y + unit * 2), (rect.right - unit * 2, cy - unit), (cx + unit * 2, rect.bottom - unit * 2), (cx, rect.bottom - unit), (cx - unit * 2, rect.bottom - unit * 2), (rect.x + unit * 2, cy - unit)]
        pygame.draw.polygon(surface, color, pts)
    elif kind == "magnet":
        pygame.draw.rect(surface, color, (rect.x + unit * 2, rect.y + unit * 2, unit * 2, unit * 5))
        pygame.draw.rect(surface, color, (rect.right - unit * 4, rect.y + unit * 2, unit * 2, unit * 5))
        pygame.draw.rect(surface, color, (rect.x + unit * 2, rect.y + unit * 2, rect.width - unit * 4, unit * 2))
        pygame.draw.rect(surface, rgb("#FF3B58"), (rect.x + unit * 2, rect.bottom - unit * 3, unit * 2, unit))
        pygame.draw.rect(surface, rgb("#28D7FF"), (rect.right - unit * 4, rect.bottom - unit * 3, unit * 2, unit))
    elif kind == "boot":
        pygame.draw.rect(surface, color, (rect.x + unit * 3, rect.y + unit * 2, unit * 3, unit * 5))
        pygame.draw.rect(surface, color, (rect.x + unit * 3, rect.bottom - unit * 3, unit * 5, unit * 2))
        pygame.draw.rect(surface, rgb("#FFF7D6"), (rect.x + unit * 6, rect.bottom - unit * 4, unit, unit))
    elif kind == "blade":
        pygame.draw.polygon(surface, color, [(rect.x + unit * 3, rect.bottom - unit * 2), (rect.right - unit * 2, rect.y + unit * 2), (rect.right - unit * 3, rect.y + unit), (rect.x + unit * 2, rect.bottom - unit * 3)])
        pygame.draw.rect(surface, rgb("#FFF7D6"), (rect.x + unit * 2, rect.bottom - unit * 3, unit * 3, unit))
    else:
        pygame.draw.rect(surface, color, rect.inflate(-unit * 3, -unit * 3))

    if label:
        font = pygame.font.SysFont("Consolas", max(8, rect.width // 4), bold=True)
        text = font.render(str(label)[:3].upper(), False, rgb("text"))
        surface.blit(text, (cx - text.get_width() // 2, cy - text.get_height() // 2))


def draw_scanline_overlay(surface, alpha=14):
    overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    for y in range(1, surface.get_height(), 4):
        pygame.draw.line(overlay, (0, 0, 0, alpha), (0, y), (surface.get_width(), y))
    surface.blit(overlay, (0, 0))
