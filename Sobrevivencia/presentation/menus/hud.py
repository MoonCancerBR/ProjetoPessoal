import pygame
from pygame.math import Vector2

if __package__:
    from ...data.constants import *
    from ...data.items import BASE_ITEM_KEYS, ITEM_DEFINITIONS, InventoryItem, MAX_ACTIVE_ITEMS, MAX_ITEM_LEVEL, item_display_name, item_short_description, RELIC_DEFINITIONS
    from ..ui_utils import hex_color
else:
    from Sobrevivencia.data.constants import *
    from Sobrevivencia.data.items import BASE_ITEM_KEYS, ITEM_DEFINITIONS, InventoryItem, MAX_ACTIVE_ITEMS, MAX_ITEM_LEVEL, item_display_name, item_short_description, RELIC_DEFINITIONS
    from Sobrevivencia.presentation.ui_utils import hex_color


BASE_SCREEN_W = 1100
BASE_SCREEN_H = 720

HUD_TOP_H = 148
HUD_MARGIN = 10

PANEL_W_SINGLE_MIN = 650
PANEL_W_SINGLE_MAX = 770
SIDE_PANEL_W_SINGLE = 300
PANEL_W = 350
PANEL_W_COMPACT = 330
PANEL_H = 110
PANEL_H_COMPACT = 108
PANEL_PAD = 10

BAR_H_HP = 17
BAR_H_THIN = 9
SLOT_ITEM = 22
SLOT_GAP = 4

QUEST_PANEL_W = 270
STATS_PANEL_W = 220


class HudMenu:
    def _hud_scale(self):
        return max(0.82, min(1.15, min(SCREEN_WIDTH / BASE_SCREEN_W, SCREEN_HEIGHT / BASE_SCREEN_H)))

    def _s(self, value):
        return max(1, int(round(value * self._hud_scale())))

    def _top_h(self):
        return self._s(HUD_TOP_H)

    def _player_panel_size(self, compact=False):
        w = PANEL_W_COMPACT if compact else PANEL_W
        h = PANEL_H_COMPACT if compact else PANEL_H
        return self._s(w), self._s(h)

    def _fit_text(self, font, text, max_width):
        text = str(text)
        if max_width <= 0 or font.get_rect(text).width <= max_width:
            return text

        suffix = "..."
        limit = max(0, max_width - font.get_rect(suffix).width)
        if limit <= 0:
            return suffix

        trimmed = text
        while trimmed and font.get_rect(trimmed).width > limit:
            trimmed = trimmed[:-1]
        return trimmed.rstrip() + suffix

    def _render_fit(self, font, text, pos, color, max_width):
        font.render_to(self.screen, pos, self._fit_text(font, text, max_width), color)

    def _wrap_lines(self, font, text, max_width, max_lines):
        words = str(text).split()
        if not words:
            return [""]

        lines = []
        current = ""
        for word in words:
            candidate = word if not current else f"{current} {word}"
            if font.get_rect(candidate).width <= max_width:
                current = candidate
                continue
            if current:
                lines.append(current)
            current = word
            if len(lines) == max_lines:
                break

        if len(lines) < max_lines and current:
            lines.append(current)

        if len(lines) > max_lines:
            lines = lines[:max_lines]

        if words and len(lines) == max_lines:
            used_text = " ".join(lines)
            original = " ".join(words)
            if len(used_text) < len(original):
                lines[-1] = self._fit_text(font, lines[-1], max_width)

        return lines

    def _draw_panel_back(self, rect, alpha=220, border=(51, 65, 85), radius=6):
        overlay = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        pygame.draw.rect(overlay, (16, 25, 40, alpha), overlay.get_rect(), border_radius=self._s(radius))
        self.screen.blit(overlay, rect.topleft)
        pygame.draw.rect(self.screen, border, rect, width=1, border_radius=self._s(radius))

    def _draw_hud_backdrop(self, height):
        pygame.draw.rect(self.screen, hex_color(COLORS["panel"]), (0, 0, SCREEN_WIDTH, height))
        pygame.draw.line(self.screen, (30, 41, 59), (0, height), (SCREEN_WIDTH, height), self._s(2))

    def _draw_hud(self, game):
        if game.multiplayer and len(game.players) > 1:
            self._draw_coop_hud(game)
            return

        player = game.player
        inv = game.inventory
        margin = self._s(HUD_MARGIN)
        hud_h = self._top_h()

        self._draw_hud_backdrop(hud_h)

        side_w = min(self._s(SIDE_PANEL_W_SINGLE), max(self._s(238), SCREEN_WIDTH // 3))
        panel_w = min(
            self._s(PANEL_W_SINGLE_MAX),
            max(self._s(PANEL_W_SINGLE_MIN), SCREEN_WIDTH - side_w - margin * 3),
        )
        player_rect = self._draw_player_panel(
            game,
            player,
            inv,
            x=margin + self._s(4),
            y=self._s(8),
            compact=False,
            expanded=True,
            width=panel_w,
        )
        side_x = player_rect.right + self._s(14)
        side_w = max(self._s(230), SCREEN_WIDTH - side_x - margin - self._s(4))
        self._draw_metric_strip(
            side_x,
            self._s(12),
            side_w,
            [
                ("Abates", player.kills, COLORS["text"]),
                ("Moedas", player.coins, COLORS["coin"]),
                ("Pts", player.score, COLORS["upgrade"]),
            ],
        )
        self._draw_message(game.message, side_x, self._s(49), side_w)
        self._draw_quest_panel(game, x=side_x, y=self._s(72), w=side_w, compact=True)
        self._draw_status_strip(game, player, inv, side_x, self._s(120), side_w)
        self._draw_chalice_tracker(game, margin + self._s(4), hud_h + self._s(38))
        self._draw_combo_counter(game)
        self._draw_buff_list(player, SCREEN_WIDTH - margin, hud_h + self._s(8), align_right=True)
        self._draw_synergy_tags(inv, margin, hud_h + self._s(8), align_right=False)
        self._draw_escort_hud(game)
        self._draw_altar_compass(game)
        self._draw_game_clock(game)
        self._draw_heat_gauge(game)

    def _draw_coop_hud(self, game):
        margin = self._s(HUD_MARGIN)
        hud_h = self._top_h()
        panel_w, _ = self._player_panel_size(compact=True)

        self._draw_hud_backdrop(hud_h)

        left_rect = self._draw_player_panel(game, game.player, game.get_inventory(0), x=margin, y=self._s(8), compact=True)
        right_x = SCREEN_WIDTH - panel_w - margin
        right_rect = self._draw_player_panel(game, game.player2, game.get_inventory(1), x=right_x, y=self._s(8), compact=True, flip=True)

        center_x = left_rect.right + self._s(12)
        center_w = max(self._s(180), right_rect.left - center_x - self._s(12))
        kills = " / ".join(f"J{p.player_index + 1} {p.kills}" for p in game.players)
        score = sum(p.score for p in game.players)
        self._draw_metric_strip(
            center_x,
            self._s(10),
            center_w,
            [
                ("Abates", kills, COLORS["text"]),
                ("Moedas", game.shared_coins, COLORS["coin"]),
                ("Pts", score, COLORS["upgrade"]),
            ],
            compact=True,
        )

        self._draw_message(game.message, center_x, self._s(42), center_w, centered=True)

        if game.level_up_pending:
            turn = f"Turno do Jogador {game.level_up_player_index + 1}"
            surf, rect = self.font_tiny.render(self._fit_text(self.font_tiny, turn, center_w), hex_color(COLORS["upgrade"]))
            self.screen.blit(surf, (center_x + center_w // 2 - rect.width // 2, self._s(60)))

        self._draw_quest_panel(game, x=center_x, y=self._s(76), w=center_w, compact=True)
        self._draw_chalice_tracker(game, center_x, hud_h + self._s(38))
        self._draw_combo_counter(game, center_x, self._s(120), center_w)
        self._draw_buff_list(game.player, margin, hud_h + self._s(8), align_right=False)
        self._draw_synergy_tags(game.get_inventory(0), margin, hud_h + self._s(8) + self._s(90), align_right=False)
        if getattr(game, "player2", None):
            self._draw_buff_list(game.player2, SCREEN_WIDTH - margin, hud_h + self._s(8), align_right=True)
            self._draw_synergy_tags(game.get_inventory(1), SCREEN_WIDTH - margin, hud_h + self._s(8) + self._s(90), align_right=True)
        self._draw_altar_compass(game)
        self._draw_game_clock(game)
        self._draw_heat_gauge(game)

    def _draw_metric_strip(self, x, y, w, entries, compact=False):
        if w <= 0:
            return

        gap = self._s(6 if compact else 8)
        count = max(1, len(entries))
        cell_w = max(self._s(42), (w - gap * (count - 1)) // count)
        cell_h = self._s(28 if compact else 32)

        for index, (label, value, color_key) in enumerate(entries):
            rect = pygame.Rect(x + index * (cell_w + gap), y, cell_w, cell_h)
            self._draw_panel_back(rect, alpha=150, border=(39, 52, 73), radius=5)

            label_text = self._fit_text(self.font_tiny, str(label).upper(), rect.width - self._s(12))
            value_text = self._fit_text(self.font_small if not compact else self.font_tiny, str(value), rect.width - self._s(12))
            self.font_tiny.render_to(self.screen, (rect.x + self._s(6), rect.y + self._s(3)), label_text, hex_color(COLORS["muted"]))
            value_font = self.font_small if not compact else self.font_tiny
            value_y = rect.y + self._s(14 if not compact else 15)
            value_font.render_to(self.screen, (rect.x + self._s(6), value_y), value_text, hex_color(color_key))

    def _draw_message(self, message, x, y, w, centered=False):
        msg = self._fit_text(self.font_tiny, message, w)
        surf, rect = self.font_tiny.render(msg, hex_color(COLORS["muted"]))
        draw_x = x + w // 2 - rect.width // 2 if centered else x
        self.screen.blit(surf, (draw_x, y))

    def _draw_status_strip(self, game, player, inv, x, y, w):
        rect = pygame.Rect(x, y, w, self._s(22))
        self._draw_panel_back(rect, alpha=138, border=(39, 52, 73), radius=5)
        values = [
            ("Tiro", f"{game.projectile_damage_for(player, inv):.0f}"),
            ("Esp", f"{game.sword_damage_for(player, inv):.0f}"),
            ("Cad", f"{game.effective_attack_rate_multiplier_for(player, inv) / PROJECTILE_COOLDOWN:.1f}/s"),
        ]
        gap = self._s(8)
        cell_w = max(self._s(52), (w - self._s(12) - gap * (len(values) - 1)) // len(values))
        cx = x + self._s(6)
        for label, value in values:
            text = self._fit_text(self.font_tiny, f"{label} {value}", cell_w)
            self.font_tiny.render_to(self.screen, (cx, y + self._s(5)), text, hex_color(COLORS["text"]))
            cx += cell_w + gap

    def _draw_combo_counter(self, game, x=None, y=None, w=None):
        if getattr(game, "combo_count", 0) <= 0 or getattr(game, "combo_timer", 0.0) <= 0:
            return None
        w = self._s(180) if w is None else min(int(w), self._s(240))
        h = self._s(38)
        x = SCREEN_WIDTH // 2 - w // 2 if x is None else int(x + max(0, (int(w) - w) // 2))
        y = self._top_h() + self._s(104) if y is None else int(y)
        rect = pygame.Rect(x, y, w, h)
        pulse = 90 + int(50 * min(1.0, game.combo_timer / 2.2))
        self._draw_panel_back(rect, alpha=178, border=(250, 204, 21), radius=6)
        title = f"COMBO x{game.combo_count}"
        rate = f"{game.combo_kps:.1f} ab/s"
        self.font_small.render_to(self.screen, (x + self._s(10), y + self._s(5)), self._fit_text(self.font_small, title, w - self._s(20)), (250, 204, 21))
        self.font_tiny.render_to(self.screen, (x + self._s(10), y + self._s(23)), rate, (253, 230, 138))
        bar_w = int((w - self._s(20)) * min(1.0, game.combo_timer / 2.2))
        pygame.draw.rect(self.screen, (250, 204, 21, pulse), (x + self._s(10), y + h - self._s(5), bar_w, self._s(3)), border_radius=2)
        return rect

    def _draw_player_panel(self, game, player, inv, x, y, compact=False, flip=False, expanded=False, width=None):
        if expanded:
            return self._draw_player_panel_expanded(game, player, inv, x, y, width=width)

        w, h = self._player_panel_size(compact)
        pad = self._s(PANEL_PAD)
        rect = pygame.Rect(x, y, w, h)
        title_color = P2_AIM_COLOR if player.player_index == 1 else P1_AIM_COLOR

        self._draw_panel_back(rect, alpha=178, border=hex_color(title_color), radius=7)

        char_name = CHARACTERS[player.char_class]["name"]
        status = "CAIDO" if player.is_down else f"NV {player.level}"
        title = f"J{player.player_index + 1} - {char_name} [{status}]"
        self._render_fit(self.font_small, title.upper(), (x + pad, y + self._s(5)), hex_color(title_color), w - pad * 2)

        content_y = y + self._s(27)
        right_w = self._s(118 if not compact else 112)
        gap = self._s(9)
        left_w = max(self._s(160), w - pad * 2 - right_w - gap)
        right_x = x + w - pad - right_w

        h_smooth = self.animation_manager.get_tween(
            f"p{player.player_index}_hp",
            player.health / max(1, player.max_health),
        )
        h_smooth.set_target(player.health / max(1, player.max_health))
        hp_label = f"VIDA {int(player.health)}/{int(player.max_health)}"
        self._bar(x + pad, content_y, left_w, self._s(BAR_H_HP), h_smooth.current, COLORS["health"], COLORS["health_bg"], hp_label)

        cy = content_y + self._s(BAR_H_HP + 4)
        if not compact:
            xp_f = player.xp / max(1, player.xp_to_next)
            xp_lbl = f"XP NV {player.level}"
            xp_smooth = self.animation_manager.get_tween(f"p{player.player_index}_xp", xp_f)
            xp_smooth.set_target(xp_f)
            self._bar(x + pad, cy, left_w, self._s(BAR_H_THIN), xp_smooth.current, COLORS["xp"], "#15361F", xp_lbl)
            cy += self._s(BAR_H_THIN + 4)

        bar_w2 = max(self._s(44), (left_w - self._s(4)) // 2)
        sr_smooth = self.animation_manager.get_tween(
            f"p{player.player_index}_sr",
            player.special_ranged / SPECIAL_MAX,
        )
        sr_smooth.set_target(player.special_ranged / SPECIAL_MAX)
        sm_smooth = self.animation_manager.get_tween(
            f"p{player.player_index}_sm",
            player.special_melee / SPECIAL_MAX,
        )
        sm_smooth.set_target(player.special_melee / SPECIAL_MAX)
        self._bar(x + pad, cy, bar_w2, self._s(BAR_H_THIN), sr_smooth.current, COLORS["special"], "#0B2C3C", "ESP DIST")
        self._bar(x + pad + bar_w2 + self._s(4), cy, max(self._s(44), left_w - bar_w2 - self._s(4)), self._s(BAR_H_THIN), sm_smooth.current, COLORS["sword"], "#3A2A08", "ESP MELEE")

        if player.special_ranged >= SPECIAL_MAX and player.special_melee >= SPECIAL_MAX:
            pulse = (pygame.time.get_ticks() // 400) % 2 == 0
            if pulse:
                ss, sr2 = self.font_tiny.render("SUPREMA", (250, 204, 21))
                self.screen.blit(ss, (x + pad + left_w // 2 - sr2.width // 2, cy - self._s(2)))

        cy += self._s(BAR_H_THIN + 5)
        self._draw_cooldown_row(game, player, x + pad, cy, left_w)
        self._draw_equipment_summary(inv, right_x, content_y, right_w)
        self._draw_attribute_summary(player, right_x, content_y + self._s(43), right_w, rect.bottom - (content_y + self._s(43)) - self._s(5))

        return rect

    def _draw_player_panel_expanded(self, game, player, inv, x, y, width=None):
        w = int(width or self._s(PANEL_W_SINGLE_MAX))
        h = self._s(PANEL_H)
        pad = self._s(PANEL_PAD + 2)
        gap = self._s(14)
        rect = pygame.Rect(x, y, w, h)
        title_color = P2_AIM_COLOR if player.player_index == 1 else P1_AIM_COLOR

        self._draw_panel_back(rect, alpha=178, border=hex_color(title_color), radius=7)

        char_name = CHARACTERS[player.char_class]["name"]
        status = "CAIDO" if player.is_down else f"NV {player.level}"
        title = f"J{player.player_index + 1} - {char_name} [{status}]"
        self._render_fit(self.font_small, title.upper(), (x + pad, y + self._s(5)), hex_color(title_color), w - pad * 2)

        content_y = y + self._s(28)
        content_bottom = rect.bottom - self._s(7)
        equip_w = self._s(196)
        attr_w = self._s(200)
        bars_w = max(self._s(270), w - pad * 2 - gap * 2 - equip_w - attr_w)
        bars_x = x + pad
        equip_x = bars_x + bars_w + gap
        attr_x = equip_x + equip_w + gap

        if attr_x + attr_w > rect.right - pad:
            overflow = attr_x + attr_w - (rect.right - pad)
            bars_w = max(self._s(240), bars_w - overflow)
            equip_x = bars_x + bars_w + gap
            attr_x = equip_x + equip_w + gap

        h_smooth = self.animation_manager.get_tween(
            f"p{player.player_index}_hp",
            player.health / max(1, player.max_health),
        )
        h_smooth.set_target(player.health / max(1, player.max_health))
        hp_label = f"VIDA {int(player.health)}/{int(player.max_health)}"
        self._bar(bars_x, content_y, bars_w, self._s(18), h_smooth.current, COLORS["health"], COLORS["health_bg"], hp_label)

        xp_y = content_y + self._s(23)
        xp_f = player.xp / max(1, player.xp_to_next)
        xp_lbl = f"XP NV {player.level}"
        xp_smooth = self.animation_manager.get_tween(f"p{player.player_index}_xp", xp_f)
        xp_smooth.set_target(xp_f)
        self._bar(bars_x, xp_y, bars_w, self._s(11), xp_smooth.current, COLORS["xp"], "#15361F", xp_lbl)

        special_y = content_y + self._s(39)
        bar_w2 = max(self._s(96), (bars_w - self._s(8)) // 2)
        sr_smooth = self.animation_manager.get_tween(
            f"p{player.player_index}_sr",
            player.special_ranged / SPECIAL_MAX,
        )
        sr_smooth.set_target(player.special_ranged / SPECIAL_MAX)
        sm_smooth = self.animation_manager.get_tween(
            f"p{player.player_index}_sm",
            player.special_melee / SPECIAL_MAX,
        )
        sm_smooth.set_target(player.special_melee / SPECIAL_MAX)
        self._bar(bars_x, special_y, bar_w2, self._s(12), sr_smooth.current, COLORS["special"], "#0B2C3C", "ESP DIST")
        self._bar(
            bars_x + bar_w2 + self._s(8),
            special_y,
            max(self._s(96), bars_w - bar_w2 - self._s(8)),
            self._s(12),
            sm_smooth.current,
            COLORS["sword"],
            "#3A2A08",
            "ESP MELEE",
        )

        if player.special_ranged >= SPECIAL_MAX and player.special_melee >= SPECIAL_MAX:
            pulse = (pygame.time.get_ticks() // 400) % 2 == 0
            if pulse:
                ss, sr2 = self.font_tiny.render("SUPREMA", (250, 204, 21))
                self.screen.blit(ss, (bars_x + bars_w // 2 - sr2.width // 2, special_y - self._s(2)))

        cooldown_y = content_y + self._s(64)
        self._draw_cooldown_row(game, player, bars_x, cooldown_y, bars_w)
        self._draw_equipment_block(inv, equip_x, content_y, equip_w, content_bottom - content_y)
        self._draw_attribute_block(player, attr_x, content_y, attr_w, content_bottom - content_y)

        return rect

    def _draw_equipment_block(self, inv, x, y, w, h):
        header = "EQP"
        self.font_tiny.render_to(self.screen, (x, y), header, hex_color(COLORS["muted"]))
        active_items = inv.active_items()
        count = f"{len(active_items)}/{MAX_ACTIVE_ITEMS}"
        count_s, count_r = self.font_tiny.render(count, hex_color(COLORS["muted_2"]))
        self.screen.blit(count_s, (x + w - count_r.width, y))

        gap = self._s(7)
        slot = min(self._s(30), max(self._s(24), (w - gap * (MAX_ACTIVE_ITEMS - 1)) // MAX_ACTIVE_ITEMS))
        start_x = x + max(0, (w - (slot * MAX_ACTIVE_ITEMS + gap * (MAX_ACTIVE_ITEMS - 1))) // 2)
        slot_y = y + self._s(22)
        for i in range(MAX_ACTIVE_ITEMS):
            rect = pygame.Rect(start_x + i * (slot + gap), slot_y, slot, slot)
            pygame.draw.rect(self.screen, (15, 23, 42), rect, border_radius=self._s(5))
            pygame.draw.rect(self.screen, (51, 65, 85), rect, width=1, border_radius=self._s(5))
            if i >= len(active_items):
                continue

            item = active_items[i]
            if item.is_relic:
                pygame.draw.rect(self.screen, (250, 180, 50), rect, width=2, border_radius=self._s(5))
            elif item.is_hybrid:
                pygame.draw.rect(self.screen, hex_color(COLORS["upgrade"]), rect, width=1, border_radius=self._s(5))

            ik = getattr(item, "key", None)
            icon = getattr(self, "item_icons", {}).get(ik)
            if icon:
                if icon.get_width() != slot or icon.get_height() != slot:
                    icon = pygame.transform.smoothscale(icon, (slot, slot))
                self.screen.blit(icon, rect.topleft)
            elif item.is_hybrid or item.is_relic:
                pygame.draw.circle(self.screen, hex_color(COLORS["upgrade"]), rect.center, max(5, slot // 3))
            else:
                pygame.draw.circle(self.screen, hex_color(COLORS["special"]), rect.center, max(5, slot // 3))

            lvl_s, lvl_r = self.font_tiny.render(str(item.level), hex_color(COLORS["text"]))
            lvl_r.bottomright = (rect.right - self._s(1), rect.bottom + self._s(1))
            bg_s = pygame.Surface((lvl_r.width + self._s(5), lvl_r.height), pygame.SRCALPHA)
            pygame.draw.rect(bg_s, (9, 14, 24, 220), bg_s.get_rect(), border_radius=self._s(2))
            self.screen.blit(bg_s, (lvl_r.left - self._s(3), lvl_r.top))
            self.screen.blit(lvl_s, lvl_r)

        hint_y = slot_y + slot + self._s(10)
        hint = "ativos prontos" if active_items else "slots livres"
        self._render_fit(self.font_tiny, hint, (x, hint_y), hex_color(COLORS["muted_2"]), w)

    def _draw_attribute_block(self, player, x, y, w, h):
        char_passives = CHARACTERS[player.char_class]["passives"]
        upgraded = [(key, lvl) for key, lvl in player.passives.items() if lvl > 0]
        total = len(player.passives)

        self.font_tiny.render_to(self.screen, (x, y), "ATR", hex_color(COLORS["muted"]))
        counter = f"{len(upgraded)}/{total}"
        counter_s, counter_r = self.font_tiny.render(counter, hex_color(COLORS["muted_2"]))
        self.screen.blit(counter_s, (x + w - counter_r.width, y))

        start_y = y + self._s(19)
        gap = self._s(3)
        cols = 4
        chip_h = self._s(16)
        chip_w = max(self._s(34), (w - gap * (cols - 1)) // cols)
        max_rows = max(1, (h - self._s(19) + gap) // (chip_h + gap))
        max_items = max_rows * cols

        if not upgraded:
            empty_cols = 5
            empty_w = max(self._s(18), (w - gap * (empty_cols - 1)) // empty_cols)
            for i in range(min(total, 10)):
                col = i % empty_cols
                row = i // empty_cols
                rect = pygame.Rect(x + col * (empty_w + gap), start_y + row * (chip_h + gap), empty_w, chip_h)
                pygame.draw.rect(self.screen, (15, 23, 42), rect, border_radius=self._s(4))
                pygame.draw.rect(self.screen, (51, 65, 85), rect, width=1, border_radius=self._s(4))
            return

        visible = upgraded[:max_items]
        for i, (key, lvl) in enumerate(visible):
            col = i % cols
            row = i // cols
            rect = pygame.Rect(x + col * (chip_w + gap), start_y + row * (chip_h + gap), chip_w, chip_h)
            pygame.draw.rect(self.screen, (15, 23, 42), rect, border_radius=self._s(4))
            pygame.draw.rect(self.screen, hex_color(COLORS["special"]), rect, width=1, border_radius=self._s(4))
            short = char_passives.get(key, {}).get("short", key[:3].upper())
            label = self._fit_text(self.font_tiny, f"{short} {lvl}", rect.width - self._s(6))
            surf, s_rect = self.font_tiny.render(label, hex_color(COLORS["text"]))
            self.screen.blit(surf, (rect.centerx - s_rect.width // 2, rect.centery - s_rect.height // 2))

        hidden = len(upgraded) - len(visible)
        if hidden > 0:
            note = f"+{hidden}"
            self.font_tiny.render_to(self.screen, (x + w - self.font_tiny.get_rect(note).width, y + self._s(61)), note, hex_color(COLORS["upgrade"]))

    def _draw_cooldown_row(self, game, player, x, y, w):
        gap = self._s(3)
        h = self._s(22)
        cell_w = max(self._s(34), (w - gap * 4) // 5)
        w_name = CHARACTERS[player.char_class][player.mode]
        mode_col = COLORS["sword"] if player.mode == "weapon_2" else COLORS["projectile"]
        self._pill(x, y, cell_w, h, w_name[:6].upper(), mode_col)

        capacity = max(1, game.magazine_capacity_for(player))
        ammo_fill = player.ammo_magazine / capacity
        ammo_lbl = f"{player.ammo_magazine}/{capacity}"
        if player.reload_timer > 0:
            ammo_fill = 1.0 - min(1.0, player.reload_timer / max(0.01, player.reload_duration))
            ammo_lbl = f"REC {player.reload_timer:.1f}s"
        self._mini_cooldown(x + (cell_w + gap), y, cell_w, h, ammo_lbl, ammo_fill)

        max_res = max(1, game.max_ammo_reserve_for(player))
        res_fill = player.ammo_reserve / max_res
        self._mini_cooldown(x + (cell_w + gap) * 2, y, cell_w, h, f"R {player.ammo_reserve}", res_fill)

        dash_fill = 1.0 - min(1.0, player.dash_cooldown / DASH_COOLDOWN)
        dash_lbl = "DASH" if dash_fill >= 1.0 else f"{player.dash_cooldown:.1f}s"
        self._mini_cooldown(x + (cell_w + gap) * 3, y, cell_w, h, dash_lbl, dash_fill)

        omni_fill = game.omni_active_charge_ratio()
        omni_lbl = f"OMNI {game.omni_active_status()}"
        self._mini_cooldown(x + (cell_w + gap) * 4, y, cell_w, h, omni_lbl, omni_fill)

        try:
            if __package__:
                from ...data.stamps import stamp_hud_color
            else:
                from Sobrevivencia.data.stamps import stamp_hud_color
                
            def draw_stamp_tags(w_key, cx, cy):
                stamps = getattr(player, "weapon_stamps", {}).get(w_key, [])
                tag_w = self._s(11)
                tag_h = self._s(8)
                tag_gap = self._s(2)
                start_x = cx + (cell_w - (3 * tag_w + 2 * tag_gap)) // 2
                
                stamp_abbreviations = {
                    "impact": "IMP",
                    "haste": "RAP",
                    "lifesteal": "VAM",
                    "blast": "EXP",
                    "frost": "CON",
                    "toxic": "VEN",
                    "caliber": "CAL",
                    "repulse": "REP",
                    "junk_grey": "CIN",
                    "junk_rust": "FER",
                    "junk_cracked": "QUE"
                }
                
                for i in range(3):
                    rx = start_x + i * (tag_w + tag_gap)
                    ry = cy + h + self._s(2)
                    rect = pygame.Rect(rx, ry, tag_w, tag_h)
                    
                    pygame.draw.rect(self.screen, (15, 23, 42), rect, border_radius=1)
                    pygame.draw.rect(self.screen, (51, 65, 85), rect, width=1, border_radius=1)
                    
                    if i < len(stamps):
                        color_hex = stamp_hud_color(stamps[i])
                        from Sobrevivencia.presentation.ui_utils import hex_color
                        color = hex_color(color_hex)
                        
                        pygame.draw.rect(self.screen, color, rect, border_radius=1)
                        
                        abb = stamp_abbreviations.get(stamps[i].key, stamps[i].key[:3].upper())
                        
                        text_color = (255, 255, 255)
                        if stamps[i].level == 2:
                            pygame.draw.rect(self.screen, (255, 255, 255), rect, width=1, border_radius=1)
                        elif stamps[i].level >= 3:
                            import time, math
                            pulse = int(170 + 85 * math.sin(time.time() * 8))
                            pygame.draw.rect(self.screen, (255, pulse, 0), rect, width=1, border_radius=1)
                            text_color = (255, 244, 0)
                        
                        font = self.font_tiny
                        text_rect = font.get_rect(abb, size=self._s(6))
                        font.render_to(self.screen, (rx + (tag_w - text_rect.width)//2, ry + (tag_h - text_rect.height)//2), abb, text_color, size=self._s(6))
                    else:
                        font = self.font_tiny
                        text_rect = font.get_rect("-", size=self._s(5))
                        font.render_to(self.screen, (rx + (tag_w - text_rect.width)//2, ry + (tag_h - text_rect.height)//2), "-", (70, 85, 105), size=self._s(5))

            draw_stamp_tags("weapon_2", x, y)
            draw_stamp_tags("weapon_1", x + (cell_w + gap), y)
        except Exception:
            pass


    def _draw_equipment_summary(self, inv, x, y, w):
        label_w = self.font_tiny.get_rect("EQP").width
        self.font_tiny.render_to(self.screen, (x, y - self._s(1)), "EQP", hex_color(COLORS["muted"]))

        gap = self._s(SLOT_GAP)
        slot = min(self._s(SLOT_ITEM), max(self._s(16), (w - label_w - self._s(6) - gap * (MAX_ACTIVE_ITEMS - 1)) // MAX_ACTIVE_ITEMS))
        start_x = x + label_w + self._s(6)
        active_items = inv.active_items()
        for i in range(MAX_ACTIVE_ITEMS):
            item_x = start_x + i * (slot + gap)
            rect = pygame.Rect(item_x, y, slot, slot)
            pygame.draw.rect(self.screen, (15, 23, 42), rect, border_radius=self._s(4))
            pygame.draw.rect(self.screen, (51, 65, 85), rect, width=1, border_radius=self._s(4))
            if i >= len(active_items):
                continue

            item = active_items[i]
            if item.is_relic:
                pygame.draw.rect(self.screen, (250, 180, 50), rect, width=2, border_radius=self._s(4))
            elif item.is_hybrid:
                pygame.draw.rect(self.screen, hex_color(COLORS["upgrade"]), rect, width=1, border_radius=self._s(4))

            ik = getattr(item, "key", None)
            icon = getattr(self, "item_icons", {}).get(ik)
            if icon:
                if icon.get_width() != slot or icon.get_height() != slot:
                    icon = pygame.transform.smoothscale(icon, (slot, slot))
                self.screen.blit(icon, rect.topleft)
            elif item.is_hybrid or item.is_relic:
                pygame.draw.circle(self.screen, hex_color(COLORS["upgrade"]), rect.center, max(4, slot // 3))
            else:
                pygame.draw.circle(self.screen, hex_color(COLORS["special"]), rect.center, max(4, slot // 3))

            lvl_s, lvl_r = self.font_tiny.render(str(item.level), hex_color(COLORS["text"]))
            lvl_r.bottomright = (rect.right, rect.bottom + self._s(2))
            bg_s = pygame.Surface((lvl_r.width + self._s(4), lvl_r.height), pygame.SRCALPHA)
            pygame.draw.rect(bg_s, (9, 14, 24, 210), bg_s.get_rect(), border_radius=self._s(2))
            self.screen.blit(bg_s, (lvl_r.left - self._s(2), lvl_r.top))
            self.screen.blit(lvl_s, lvl_r)

    def _draw_attribute_summary(self, player, x, y, w, h):
        self.font_tiny.render_to(self.screen, (x, y), "ATR", hex_color(COLORS["muted"]))
        char_passives = CHARACTERS[player.char_class]["passives"]
        upgraded = [(key, lvl) for key, lvl in player.passives.items() if lvl > 0]
        if not upgraded:
            text = f"0/{len(player.passives)}"
            self.font_tiny.render_to(self.screen, (x + self._s(32), y), text, hex_color(COLORS["muted_2"]))
            return

        start_y = y + self._s(16)
        chip_h = self._s(17)
        gap = self._s(4)
        cols = 3
        chip_w = max(self._s(30), (w - gap * (cols - 1)) // cols)
        max_rows = max(1, h // (chip_h + gap))
        max_items = max_rows * cols
        visible = upgraded[:max_items]
        for i, (key, lvl) in enumerate(visible):
            col = i % cols
            row = i // cols
            rect = pygame.Rect(x + col * (chip_w + gap), start_y + row * (chip_h + gap), chip_w, chip_h)
            pygame.draw.rect(self.screen, (15, 23, 42), rect, border_radius=self._s(4))
            pygame.draw.rect(self.screen, hex_color(COLORS["special"]), rect, width=1, border_radius=self._s(4))
            short = char_passives.get(key, {}).get("short", key[:3].upper())
            label = self._fit_text(self.font_tiny, f"{short}{lvl}", rect.width - self._s(6))
            surf, s_rect = self.font_tiny.render(label, hex_color(COLORS["text"]))
            self.screen.blit(surf, (rect.centerx - s_rect.width // 2, rect.centery - s_rect.height // 2))

        hidden = len(upgraded) - len(visible)
        if hidden > 0:
            note = f"+{hidden}"
            self.font_tiny.render_to(self.screen, (x + w - self.font_tiny.get_rect(note).width, y), note, hex_color(COLORS["upgrade"]))

    def _bar(self, x, y, w, h, fill, color, bg, label):
        fill = max(0, min(1, fill))
        rect = pygame.Rect(x, y, w, h)
        pygame.draw.rect(self.screen, hex_color(bg), rect, border_radius=self._s(5))
        if fill > 0:
            fill_rect = pygame.Rect(x, y, max(1, int(w * fill)), h)
            pygame.draw.rect(self.screen, hex_color(color), fill_rect, border_radius=self._s(5))
        pygame.draw.rect(self.screen, (15, 23, 42), rect, width=1, border_radius=self._s(5))

        label = self._fit_text(self.font_tiny, label, w - self._s(10))
        text_y = y + h // 2 - self.font_tiny.get_rect(label).height // 2 - self._s(1)
        self.font_tiny.render_to(self.screen, (x + self._s(6), text_y + self._s(1)), label, (0, 0, 0))
        self.font_tiny.render_to(self.screen, (x + self._s(5), text_y), label, hex_color(COLORS["text"]))

    def _pill(self, x, y, w, h, text, color):
        rect = pygame.Rect(x, y, w, h)
        pygame.draw.rect(self.screen, hex_color(color), rect, border_radius=self._s(6))
        pygame.draw.rect(self.screen, (255, 255, 255, 50), rect, width=1, border_radius=self._s(6))
        text = self._fit_text(self.font_tiny, text, w - self._s(8))
        surf, s_rect = self.font_tiny.render(text, (9, 14, 24))
        self.screen.blit(surf, (x + w // 2 - s_rect.width // 2, y + h // 2 - s_rect.height // 2))

    def _mini_cooldown(self, x, y, w, h, text, fill):
        rect = pygame.Rect(x, y, w, h)
        pygame.draw.rect(self.screen, (30, 41, 59), rect, border_radius=self._s(6))
        if fill > 0:
            fw = max(0, min(w, int(w * fill)))
            pygame.draw.rect(self.screen, (34, 197, 94), (x, y, fw, h), border_radius=self._s(6))
        pygame.draw.rect(self.screen, (15, 23, 42), rect, width=1, border_radius=self._s(6))
        text = self._fit_text(self.font_tiny, text, w - self._s(8))
        surf, s_rect = self.font_tiny.render(text, hex_color(COLORS["text"]))
        self.screen.blit(surf, (x + w // 2 - s_rect.width // 2, y + h // 2 - s_rect.height // 2))

    def _draw_buff_list(self, player, start_x, start_y, align_right=False):
        labels = {"freeze": "Gelo", "speed": "Veloc.", "power": "Forca"}
        y = start_y
        active_buffs = []
        if player.shield_timer > 0:
            active_buffs.append(("Escudo", player.shield_timer, COLORS["shield"]))
        for name, timer in player.buffs.items():
            active_buffs.append((labels.get(name, name), timer, COLORS["upgrade"]))
        for name, timer, color in active_buffs:
            text = f"{name} {timer:.0f}s"
            width = max(self._s(72), self.font_tiny.get_rect(text).width + self._s(16))
            bx = start_x - width if align_right else start_x
            self._pill(bx, y, width, self._s(20), text, color)
            y += self._s(26)

    def _draw_synergy_tags(self, inv, start_x, start_y, align_right=False):
        synergies = inv.get_active_synergies()
        if not synergies:
            return
            
        labels = {
            "elemental": "♨ Elemental",
            "defensiva": "⛨ Defensiva",
            "utilitaria": "⧖ Utilitaria",
            "cinetica": "⚡ Cinetica",
            "ofensiva": "⚔ Ofensiva"
        }
        
        y = start_y
        for syn in synergies:
            text = labels.get(syn, syn.title())
            width = max(self._s(80), self.font_tiny.get_rect(text).width + self._s(16))
            bx = start_x - width if align_right else start_x
            self._pill(bx, y, width, self._s(22), text, COLORS["special"])
            y += self._s(26)

    def _draw_coop_stats_panels(self, game):
        if game.player2 is None:
            empty = pygame.Rect(0, self._top_h(), 0, 0)
            return empty, empty
        y = self._top_h() + self._s(8)
        left = self._draw_stats_panel_for(game, game.player, game.get_inventory(0), self._s(14), y, "Status J1", compact=True)
        right = self._draw_stats_panel_for(
            game,
            game.player2,
            game.get_inventory(1),
            SCREEN_WIDTH - self._s(STATS_PANEL_W) - self._s(14),
            y,
            "Status J2",
            compact=True,
        )
        return left, right

    def _draw_stats_panel(self, game, y=None, compact=False):
        y = self._top_h() + self._s(8) if y is None else y
        return self._draw_stats_panel_for(
            game,
            game.player,
            game.inventory,
            SCREEN_WIDTH - self._s(STATS_PANEL_W) - self._s(14),
            y,
            "Status",
            compact=compact,
        )

    def _draw_stats_panel_for(self, game, player, inv, x, y, title, compact=False):
        terrain_key = game.world.terrain_at(player.pos.x, player.pos.y)
        terrain = TERRAIN_TYPES[terrain_key]
        max_speed = player.base_speed * game.effective_speed_multiplier_for(player)
        terrain_speed = max_speed * terrain["speed"]
        fire_rate = game.effective_attack_rate_multiplier_for(player, inv) / PROJECTILE_COOLDOWN
        w, h = self._s(STATS_PANEL_W), self._s(204 if compact else 214)
        rect = pygame.Rect(x, y, w, h)

        self._draw_panel_back(rect, alpha=210, border=(51, 65, 85), radius=6)
        self.font_tiny.render_to(self.screen, (x + self._s(10), y + self._s(8)), title.upper(), hex_color(COLORS["muted"]))

        stats = [
            ("Vel. max", f"{max_speed:.0f}"),
            (f"Terreno {terrain['name']}", f"{terrain_speed:.0f}"),
            ("Dano tiro", f"{game.projectile_damage_for(player, inv):.0f}"),
            ("Dano espada", f"{game.sword_damage_for(player, inv):.0f}"),
            ("Alcance espada", f"{game.sword_radius_for(player, inv):.0f}"),
            ("Ritmo tiro", f"{fire_rate:.1f}/s"),
            ("Balas/salva", str(game.ranged_projectiles_per_salvo(player))),
            ("Vampirismo", f"{player.passives.get('vampirism', 0) * 10}%"),
            ("Pente Extra", f"+{player.passives.get('magazine', 0)}"),
            ("Recarga Rapida", f"-{player.passives.get('reload_speed', 0)}s"),
        ]

        label_w = self._s(128)
        value_w = w - label_w - self._s(24)
        line_y = y + self._s(28)
        line_gap = self._s(16)
        for label, value in stats:
            self._render_fit(self.font_tiny, label, (x + self._s(10), line_y), hex_color(COLORS["muted"]), label_w)
            value = self._fit_text(self.font_tiny, value, value_w)
            vs, vr = self.font_tiny.render(value, hex_color(COLORS["text"]))
            self.screen.blit(vs, (x + w - self._s(10) - vr.width, line_y))
            line_y += line_gap

        passive = f"Pts item {inv.points}"
        self._render_fit(self.font_tiny, passive, (x + self._s(10), y + h - self._s(20)), hex_color(COLORS["poison"]), w - self._s(20))
        return rect

    def _draw_chalice_tracker(self, game, x, y):
        fragments = getattr(game, "chalice_fragments", None)
        if not fragments:
            return None
        entries = CHALICE_FRAGMENTS
        collected = sum(1 for entry in entries if fragments.get(entry["key"], False))
        icon = self._s(26)
        gap = self._s(4)
        title_w = self._s(88)
        w = title_w + len(entries) * icon + (len(entries) - 1) * gap + self._s(8)
        h = self._s(42)
        rect = pygame.Rect(x, y, w, h)
        complete = collected >= len(entries)
        border = (255, 212, 71) if complete else (180, 136, 36)
        self._draw_panel_back(rect, alpha=208, border=border, radius=3)
        title_color = (255, 212, 71) if not complete else (53, 240, 107)
        self.font_tiny.render_to(self.screen, (x + self._s(8), y + self._s(5)), "CALICE", title_color)
        self.font_tiny.render_to(self.screen, (x + self._s(8), y + self._s(22)), f"{collected}/{len(entries)} FRAG", hex_color(COLORS["text"]))
        ix = x + title_w
        for entry in entries:
            active = fragments.get(entry["key"], False)
            color = (255, 212, 71) if active else (43, 52, 76)
            border_color = (255, 247, 214) if active else (94, 105, 134)
            text_color = (5, 5, 10) if active else (167, 176, 199)
            slot = pygame.Rect(ix, y + self._s(8), icon, icon)
            pygame.draw.rect(self.screen, color, slot, border_radius=1)
            pygame.draw.rect(self.screen, border_color, slot, width=2, border_radius=1)
            if active:
                pygame.draw.rect(self.screen, (255, 255, 255, 55), slot.inflate(-6, -6), width=1)
            label = entry["label"]
            label = self._fit_text(self.font_tiny, label, icon - self._s(3))
            surf, sr = self.font_tiny.render(label, text_color)
            self.screen.blit(surf, (slot.centerx - sr.width // 2, slot.centery - sr.height // 2))
            ix += icon + gap
        return rect

    def _draw_quest_panel(self, game, x=None, y=None, w=None, compact=False):
        q = game.quest
        margin = self._s(HUD_MARGIN)
        x = margin + self._s(4) if x is None else x
        y = self._top_h() + self._s(8) if y is None else y
        w = self._s(QUEST_PANEL_W) if w is None else int(w)
        panel_h = self._s(44 if compact else 46) if q is None else self._s(44 if compact else 82)
        rect = pygame.Rect(x, y, w, panel_h)

        border = hex_color(COLORS["upgrade"]) if q else (30, 41, 59)
        self._draw_panel_back(rect, alpha=200 if q else 178, border=border, radius=6)

        if q is None:
            wait = max(0, game.next_quest_timer)
            self.font_tiny.render_to(self.screen, (x + self._s(10), y + self._s(5)), "MISSAO", hex_color(COLORS["muted"]))
            self._render_fit(self.font_tiny, f"Proxima em {wait:.0f}s", (x + self._s(10), y + self._s(22)), hex_color(COLORS["muted_2"]), w - self._s(20))
            return rect

        self.font_tiny.render_to(self.screen, (x + self._s(10), y + self._s(5)), "MISSAO ATIVA", hex_color(COLORS["upgrade"]))

        max_lines = 1 if compact else 2
        desc_y = y + self._s(20)
        line_w = w - self._s(20)
        for i, line in enumerate(self._wrap_lines(self.font_tiny, q["description"], line_w, max_lines)):
            self.font_tiny.render_to(self.screen, (x + self._s(10), desc_y + i * self._s(13)), self._fit_text(self.font_tiny, line, line_w), hex_color(COLORS["text"]))

        target = q["target"]
        prog_f = min(1.0, game.quest_progress / target) if target > 0 else 0
        bar_y = y + self._s(31 if compact else 54)
        bar_h = self._s(7 if compact else 8)
        pygame.draw.rect(self.screen, (30, 41, 59), (x + self._s(10), bar_y, w - self._s(20), bar_h), border_radius=self._s(4))
        if prog_f > 0:
            pygame.draw.rect(
                self.screen,
                hex_color(COLORS["xp"]),
                (x + self._s(10), bar_y, int((w - self._s(20)) * prog_f), bar_h),
                border_radius=self._s(4),
            )

        if not compact:
            timer_left = max(0, q["timer"])
            tcol = COLORS["danger"] if timer_left < 10 else COLORS["muted"]
            self.font_tiny.render_to(self.screen, (x + self._s(10), y + self._s(66)), f"{timer_left:.0f}s  +3 niveis", hex_color(tcol))

        return rect

    def _draw_escort_hud(self, game):
        if not getattr(game, 'escort_event_active', False):
            return
            
        import pygame.freetype
        from pygame.math import Vector2
        font = pygame.freetype.SysFont('Verdana', self._s(15), bold=True)
        
        state = getattr(game, 'escort_state', '')
        text = 'MISSAO DE ESCOLTA: '
        border_col = (59, 130, 246, 255)
        
        if state == 'seeking_spawn':
            text += 'Encontre os aliados'
        elif state == 'escorting':
            text += 'Leve-os ate a extracao'
        elif state == 'completed':
            text = 'MISSAO CUMPRIDA! ' + getattr(game, 'escort_reward_msg', 'Aliados salvos!')
            border_col = (16, 185, 129, 255)
        elif state == 'failed':
            text = 'MISSAO FALHOU! Aliados foram eliminados.'
            border_col = (239, 68, 68, 255)
            
        rect = font.get_rect(text)
        x = (SCREEN_WIDTH - rect.width) // 2
        y = self._top_h() + self._s(20)
        
        bg_rect = pygame.Rect(x - 20, y - 5, rect.width + 40, rect.height + 10)
        
        surface = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(surface, (20, 20, 40, 210), surface.get_rect(), border_radius=4)
        pygame.draw.rect(surface, border_col, surface.get_rect(), 2, border_radius=4)
        self.screen.blit(surface, bg_rect.topleft)
        
        font.render_to(self.screen, (x, y), text, (255, 255, 255))
        
        if state in ('completed', 'failed'):
            return
            
        center_x = SCREEN_WIDTH // 2
        center_y = SCREEN_HEIGHT // 2
        player = game.player
        if player.is_down and getattr(game, 'multiplayer', False) and getattr(game, 'player2', None):
            player = game.player2
            
        target_pos = None
        if state == 'seeking_spawn':
            target_pos = game.escort_spawn_pos
            color = (59, 130, 246)
        elif state == 'escorting':
            target_pos = game.escort_extract_pos
            color = (16, 185, 129)
            
        if target_pos:
            diff = target_pos - player.pos
            dist = diff.length()
            if dist > 350:
                if dist > 0: diff = diff.normalize()
                else: diff = Vector2(1, 0)
                arrow_dist = 180
                arrow_pos = Vector2(center_x, center_y) + diff * arrow_dist
                
                p1 = arrow_pos + diff * 15
                p2 = arrow_pos + diff.rotate(135) * 12
                p3 = arrow_pos + diff.rotate(-135) * 12
                pygame.draw.polygon(self.screen, color, [p1, p2, p3])
                
                dist_font = pygame.freetype.SysFont('Verdana', self._s(11), bold=True)
                dist_text = f'{int(dist//10)}m'
                dist_rect = dist_font.get_rect(dist_text)
                dist_font.render_to(self.screen, (int(arrow_pos.x - dist_rect.width//2), int(arrow_pos.y + 15)), dist_text, color)

    def _draw_altar_compass(self, game):
        if not getattr(game, 'altars', None):
            return
        player = game.player
        if player.is_down and getattr(game, 'multiplayer', False) and getattr(game, 'player2', None):
            player = game.player2
            
        # Find closest active altar
        active_altars = [a for a in game.altars if a.active]
        if not active_altars:
            return
            
        closest = min(active_altars, key=lambda a: player.pos.distance_to(a.pos))
        diff = closest.pos - player.pos
        dist = diff.length()
        
        # Don't draw if the altar is already on the screen (close to the player)
        if dist < 220:
            return
            
        # Calculate angle
        angle = math.atan2(diff.y, diff.x)
        
        # Center of screen for arrow radius
        center_x = SCREEN_WIDTH // 2
        center_y = SCREEN_HEIGHT // 2 + self._s(70)
        arrow_dist = self._s(130)
        arrow_pos = Vector2(center_x, center_y) + Vector2(math.cos(angle), math.sin(angle)) * arrow_dist
        
        # Altar type colors
        if closest.kind == "weapon_altar":
            color = (239, 68, 68) # Red
        elif closest.kind == "skill_altar":
            color = (139, 92, 246) # Purple
        else:
            color = (245, 158, 11) # Gold
            
        diff_norm = diff.normalize() if dist > 0 else Vector2(1, 0)
        p1 = arrow_pos + diff_norm * self._s(16)
        p2 = arrow_pos + diff_norm.rotate(135) * self._s(10)
        p3 = arrow_pos + diff_norm.rotate(-135) * self._s(10)
        
        # Draw nice shadow and polygon
        pygame.draw.polygon(self.screen, (15, 23, 42, 100), [p1 + (1, 1), p2 + (1, 1), p3 + (1, 1)])
        pygame.draw.polygon(self.screen, color, [p1, p2, p3])
        pygame.draw.polygon(self.screen, (255, 255, 255), [p1, p2, p3], 1)
        
        # Text distance
        dist_text = f"{int(dist//10)}m"
        rect = self.font_tiny.get_rect(dist_text)
        self.font_tiny.render_to(self.screen, (int(arrow_pos.x - rect.width // 2), int(arrow_pos.y + self._s(12))), dist_text, color)

    def _draw_game_clock(self, game):
        import math
        total_seconds = int(game.time_alive)
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        
        phase, rem = game.phase_info
        rem_sec = int(math.ceil(rem))
        
        phase_labels = {
            "dia": f"DIA: {rem_sec}s",
            "entardecer": f"TARDE: {rem_sec}s",
            "noite": f"NOITE: {rem_sec}s",
            "amanhecer": f"ALVORADA: {rem_sec}s"
        }
        phase_str = phase_labels.get(phase, "")
        
        phase_colors = {
            "dia": "#F59E0B",
            "entardecer": "#F97316",
            "noite": "#818CF8",
            "amanhecer": "#22D3EE"
        }
        p_color = phase_colors.get(phase, "#38BDF8")
        
        w = self._s(120)
        h = self._s(34)
        x = SCREEN_WIDTH // 2 - w // 2
        y = self._top_h() + self._s(8)
        
        rect = pygame.Rect(x, y, w, h)
        border_rgb = hex_color(p_color)
        self._draw_panel_back(rect, alpha=210, border=border_rgb, radius=5)
        
        rect_time = self.font_tiny.get_rect(time_str, size=self._s(11))
        tx = x + (w - rect_time.width) // 2
        ty = y + self._s(3)
        self.font_tiny.render_to(self.screen, (tx, ty), time_str, hex_color("#F8FAFC"), size=self._s(11))
        
        rect_phase = self.font_tiny.get_rect(phase_str, size=self._s(9))
        px = x + (w - rect_phase.width) // 2
        py = y + self._s(18)
        self.font_tiny.render_to(self.screen, (px, py), phase_str, border_rgb, size=self._s(9))

    def _draw_heat_gauge(self, game):
        import math
        heat = getattr(game, "heat_level", 0.0)
        reaper_alive = any(enemy.kind == "reaper" for enemy in getattr(game, "enemies", []))
        
        w = self._s(160)
        h = self._s(10)
        x = SCREEN_WIDTH // 2 - w // 2
        y = self._top_h() + self._s(66)
        
        bg_rect = pygame.Rect(x - self._s(8), y - self._s(18), w + self._s(16), h + self._s(24))
        self._draw_panel_back(bg_rect, alpha=160, border=(30, 41, 59), radius=4)
        
        label_text = f"AMEACA: {heat:.0f}%"
        if reaper_alive:
            pulse = 127 + int(128 * math.sin(game.time_alive * 14.0))
            label_color = (248, 113, 113) if pulse > 127 else (254, 226, 226)
            label_text = f"CEIFADOR {getattr(game, 'reaper_defeats', 0) + 1} NA AREA"
        elif heat >= 75.0:
            pulse = 127 + int(128 * math.sin(game.time_alive * 12.0))
            label_color = (239, 68, 68) if pulse > 127 else (251, 191, 36)
            label_text = "AMEACA MAXIMA!"
        else:
            label_color = (244, 63, 94)
            
        rect_lbl = self.font_tiny.get_rect(label_text, size=self._s(8))
        lx = x + (w - rect_lbl.width) // 2
        ly = y - self._s(14)
        self.font_tiny.render_to(self.screen, (lx, ly), label_text, label_color, size=self._s(8))
        
        pygame.draw.rect(self.screen, (15, 23, 42), (x, y, w, h), border_radius=3)
        
        if heat > 0:
            fill_w = int((heat / 100.0) * w)
            if heat < 50.0:
                r = int(251 + (249 - 251) * (heat / 50.0))
                g = int(191 + (115 - 191) * (heat / 50.0))
                b = int(36 + (22 - 36) * (heat / 50.0))
            else:
                r = int(249 + (239 - 249) * ((heat - 50.0) / 50.0))
                g = int(115 + (68 - 115) * ((heat - 50.0) / 50.0))
                b = int(22 + (68 - 22) * ((heat - 50.0) / 50.0))
            
            fill_rect = pygame.Rect(x, y, fill_w, h)
            pygame.draw.rect(self.screen, (r, g, b), fill_rect, border_radius=3)
            
            if heat > 75.0:
                glow_surf = pygame.Surface((fill_w + 6, h + 6), pygame.SRCALPHA)
                pygame.draw.rect(glow_surf, (239, 68, 68, 80), (0, 0, fill_w + 6, h + 6), border_radius=4)
                self.screen.blit(glow_surf, (x - 3, y - 3))
