import pygame
try:
    import pygame_gui
except ImportError:
    pygame_gui = None

if __package__:
    from ...data.constants import *
    from ...core.records import load_records, total_score
    from ...data.items import InventoryItem
    from ...core.meta_progress import (
        CHARACTER_UPGRADES,
        UPGRADE_LEVEL_BASE,
        UPGRADE_LEVEL_MAX,
        character_price,
        character_upgrades,
        coin_balance,
        is_character_unlocked,
        upgrade_cost,
        upgrade_effect_value,
    )
    from .. import arcade_theme
    from ..ui_utils import hex_color
else:
    from Sobrevivencia.data.constants import *
    from Sobrevivencia.core.records import load_records, total_score
    from Sobrevivencia.data.items import InventoryItem
    from Sobrevivencia.core.meta_progress import (
        CHARACTER_UPGRADES,
        UPGRADE_LEVEL_BASE,
        UPGRADE_LEVEL_MAX,
        character_price,
        character_upgrades,
        coin_balance,
        is_character_unlocked,
        upgrade_cost,
        upgrade_effect_value,
    )
    from Sobrevivencia.presentation import arcade_theme
    from Sobrevivencia.presentation.ui_utils import hex_color

ENEMY_GROUPS = (
    ("Normais", ("basic", "runner", "brute", "spitter", "bulwark", "sapper", "golem", "necromancer", "phantom", "minion", "morcego_sombra", "lobo_infectado")),
    ("Errantes Prismaticos", ("chromatic",)),
    ("Elite", ("miniboss",)),
    ("Bosses", ("harbinger", "reaper", "god")),
)

class SystemMenus:
    def render_start(self, mouse_pos, selected=0):
        arcade_theme.draw_background(self.screen, pygame.time.get_ticks() / 1000.0)
        arcade_theme.draw_title(
            self.screen,
            self.font_big,
            self.font_small,
            "SOBREVIVENCIA",
            "ARCADE SURVIVAL PROTOCOL",
            92,
            pygame.time.get_ticks() / 1000.0,
        )

        frame = pygame.Rect(326, 230, 448, 390)
        arcade_theme.draw_panel(self.screen, frame, border="#28D7FF", title_bar=True)
        self.font_tiny.render_to(self.screen, (frame.x + 18, frame.y + 12), "INSERT COIN // SELECT MODE", hex_color(COLORS["bg"]))
        self._draw_start_side_modules(frame)

        buttons = []
        options = [
            ("Iniciar Jogo", "character_select", COLORS["xp"]),
            ("Records", "records", COLORS["coin"]),
            ("Loja de moedas", "coin_shop", COLORS["health"]),
            ("Enciclopedia", "encyclopedia", COLORS["special"]),
            ("Comandos", "commands", COLORS["coin"]),
            ("Configuracoes", "settings", COLORS["upgrade"]),
            ("Voltar ao Menu", "menu", COLORS["muted_2"]),
        ]
        for index, (label, action, color) in enumerate(options):
            buttons.append(self._button(410, 250 + index * 50, 280, 40, label, action, mouse_pos, color, selected == index))

        hint = "WASD/ANALOGICO MOVE  |  MOUSE MIRA  |  A CONFIRMA/DASH  |  START PAUSA"
        self._render_fit(self.font_tiny, hint, (SCREEN_WIDTH // 2 - 320, 650), hex_color(COLORS["muted"]), 640)
        # pygame.display.flip()
        return buttons

    def render_coin_shop(self, mouse_pos, selected=0):
        arcade_theme.draw_background(self.screen, pygame.time.get_ticks() / 1000.0)
        panel = pygame.Rect(220, 92, SCREEN_WIDTH - 440, SCREEN_HEIGHT - 170)
        arcade_theme.draw_panel(self.screen, panel, border=COLORS["coin"], title_bar=True)
        self._center_text("LOJA DE MOEDAS", self.font_title, panel.y + 38, COLORS["coin"])
        balance = coin_balance()
        wallet = pygame.Rect(panel.right - 210, panel.y + 18, 170, 36)
        pygame.draw.rect(self.screen, hex_color("#101827"), wallet)
        pygame.draw.rect(self.screen, hex_color(COLORS["coin"]), wallet, 2)
        self.font_tiny.render_to(self.screen, (wallet.x + 12, wallet.y + 9), f"MOEDAS {balance}", hex_color(COLORS["coin"]))

        options = [
            ("Skins", "coin_shop_skins", COLORS["special"]),
            ("Desbloquear Personagens", "coin_shop_characters", COLORS["xp"]),
            ("Melhorias de personagens", "coin_shop_upgrades", COLORS["upgrade"]),
        ]
        buttons = []
        y = panel.y + 128
        for index, (label, action, color) in enumerate(options):
            buttons.append(self._button(panel.centerx - 190, y, 380, 54, label, action, mouse_pos, color, selected == index))
            y += 78
        self._center_text("Sistema preparado para upgrades permanentes futuros.", self.font_tiny, panel.bottom - 96, COLORS["muted"])
        buttons.append(self._button(panel.centerx - 100, panel.bottom - 54, 200, 38, "Voltar", "coin_shop_back", mouse_pos, COLORS["muted_2"]))
        return buttons

    def render_character_unlock(self, selected, mouse_pos):
        arcade_theme.draw_background(self.screen, pygame.time.get_ticks() / 1000.0)
        panel = pygame.Rect(110, 62, SCREEN_WIDTH - 220, SCREEN_HEIGHT - 112)
        arcade_theme.draw_panel(self.screen, panel, border=COLORS["xp"], title_bar=True)
        self._center_text("DESBLOQUEAR PERSONAGENS", self.font_title, panel.y + 34, COLORS["xp"])
        balance = coin_balance()
        self.font_tiny.render_to(self.screen, (panel.right - 176, panel.y + 20), f"MOEDAS {balance}", hex_color(COLORS["coin"]))

        buttons = []
        keys = list(CHARACTERS.keys())
        cols = 2
        slot_w = 390
        slot_h = 112
        start_x = panel.x + 48
        start_y = panel.y + 104
        for index, key in enumerate(keys):
            data = CHARACTERS[key]
            row = index // cols
            col = index % cols
            rect = pygame.Rect(start_x + col * (slot_w + 38), start_y + row * (slot_h + 24), slot_w, slot_h)
            unlocked = is_character_unlocked(key)
            color = data.get("core_color", COLORS["xp"]) if unlocked else COLORS["muted_2"]
            fill = "#101827" if selected == index else "#0B1220"
            pygame.draw.rect(self.screen, hex_color(fill), rect)
            pygame.draw.rect(self.screen, hex_color(color), rect, 3 if selected == index else 2)
            arcade_theme.draw_pixel_icon(self.screen, (rect.x + 16, rect.y + 18, 74, 74), key, color=data.get("core_color", COLORS["xp"]), label=data["name"][:2])
            self.font.render_to(self.screen, (rect.x + 108, rect.y + 20), data["name"].upper(), hex_color(COLORS["text"]))
            status = "LIBERADO" if unlocked else f"BLOQUEADO  {character_price(key)} moedas"
            status_color = COLORS["xp"] if unlocked else COLORS["coin"]
            self.font_tiny.render_to(self.screen, (rect.x + 108, rect.y + 52), status, hex_color(status_color))
            self.font_tiny.render_to(self.screen, (rect.x + 108, rect.y + 78), f"{data['weapon_1']} / {data['weapon_2']}", hex_color(COLORS["muted"]))
            buttons.append(("character_unlock_select:" + str(index), rect))

        self._center_text("Selecione um slot para ver detalhes e comprar.", self.font_tiny, panel.bottom - 82, COLORS["muted"])
        buttons.append(self._button(panel.centerx - 100, panel.bottom - 50, 200, 36, "Voltar", "character_unlock_back", mouse_pos, COLORS["muted_2"]))
        return buttons

    def render_character_unlock_detail(self, selected, mouse_pos):
        arcade_theme.draw_background(self.screen, pygame.time.get_ticks() / 1000.0)
        keys = list(CHARACTERS.keys())
        selected = max(0, min(selected, len(keys) - 1))
        key = keys[selected]
        data = CHARACTERS[key]
        unlocked = is_character_unlocked(key)
        price = character_price(key)
        panel = pygame.Rect(146, 62, SCREEN_WIDTH - 292, SCREEN_HEIGHT - 112)
        arcade_theme.draw_panel(self.screen, panel, border=data.get("core_color", COLORS["xp"]), title_bar=True)
        self._center_text(data["name"].upper(), self.font_title, panel.y + 34, data.get("core_color", COLORS["xp"]))
        self.font_tiny.render_to(self.screen, (panel.right - 176, panel.y + 20), f"MOEDAS {coin_balance()}", hex_color(COLORS["coin"]))
        arcade_theme.draw_pixel_icon(self.screen, (panel.x + 56, panel.y + 92, 150, 150), key, color=data.get("core_color", COLORS["xp"]), label=data["name"][:2])
        self.font.render_to(self.screen, (panel.x + 240, panel.y + 104), f"Armas: {data['weapon_1']} / {data['weapon_2']}", hex_color(COLORS["text"]))
        specials = data.get("specials", {})
        lines = [
            f"Especial: {specials.get('weapon_1', data['special'])}",
            f"Corpo a corpo: {specials.get('weapon_2', data['special'])}",
            f"Combo: {specials.get('combo', 'Ultimate combinada')}",
        ]
        for index, text in enumerate(lines):
            self.font_tiny.render_to(self.screen, (panel.x + 240, panel.y + 144 + index * 28), text, hex_color(COLORS["muted"]))
        status = "LIBERADO PARA USO" if unlocked else f"PRECO: {price} MOEDAS"
        self.font.render_to(self.screen, (panel.x + 240, panel.y + 238), status, hex_color(COLORS["xp"] if unlocked else COLORS["coin"]))

        self.font_tiny.render_to(self.screen, (panel.x + 56, panel.y + 300), "ESTILO DE JOGABILIDADE", hex_color(COLORS["special"]))
        descriptions = self._character_playstyle_lines(data)
        for index, line in enumerate(descriptions[:5]):
            self.font_tiny.render_to(self.screen, (panel.x + 56, panel.y + 334 + index * 24), line, hex_color(COLORS["text"]))

        buttons = []
        if not unlocked:
            buttons.append(self._button(panel.centerx - 240, panel.bottom - 58, 220, 42, "Comprar", "character_unlock_buy", mouse_pos, COLORS["coin"]))
        buttons.append(self._button(panel.centerx + 20, panel.bottom - 58, 220, 42, "Voltar", "character_unlock_back", mouse_pos, COLORS["muted_2"]))
        return buttons

    def render_character_unlock_confirm(self, selected, mouse_pos):
        buttons = self.render_character_unlock_detail(selected, mouse_pos)
        keys = list(CHARACTERS.keys())
        key = keys[max(0, min(selected, len(keys) - 1))]
        data = CHARACTERS[key]
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((5, 10, 18, 176))
        self.screen.blit(overlay, (0, 0))
        box = pygame.Rect(322, 238, 456, 210)
        arcade_theme.draw_panel(self.screen, box, border=COLORS["coin"], fill="#101827", shadow=True)
        self._center_text("CONFIRMAR COMPRA", self.font, box.y + 28, COLORS["coin"])
        self._center_text(f"{data['name']} por {character_price(key)} moedas?", self.font_tiny, box.y + 80, COLORS["text"])
        return [
            self._button(box.x + 58, box.bottom - 70, 150, 42, "Comprar", "character_unlock_confirm_yes", mouse_pos, COLORS["coin"]),
            self._button(box.right - 208, box.bottom - 70, 150, 42, "Cancelar", "character_unlock_confirm_no", mouse_pos, COLORS["muted_2"]),
        ]

    def render_character_upgrades(self, draft_levels, mouse_pos, selected=0):
        arcade_theme.draw_background(self.screen, pygame.time.get_ticks() / 1000.0)
        panel = pygame.Rect(80, 54, SCREEN_WIDTH - 160, SCREEN_HEIGHT - 96)
        arcade_theme.draw_panel(self.screen, panel, border=COLORS["upgrade"], title_bar=True)
        self._center_text("MELHORIAS DE PERSONAGENS", self.font_title, panel.y + 32, COLORS["upgrade"])
        self.font_tiny.render_to(self.screen, (panel.right - 176, panel.y + 20), f"MOEDAS {coin_balance()}", hex_color(COLORS["coin"]))
        saved = character_upgrades()
        buttons = []
        y = panel.y + 92
        keys = list(CHARACTER_UPGRADES.keys())
        for index, key in enumerate(keys):
            info = CHARACTER_UPGRADES[key]
            state = saved[key]
            purchased = state["purchased_level"]
            active = int(draft_levels.get(key, state["active_level"]))
            row = pygame.Rect(panel.x + 34, y, panel.width - 68, 48)
            pygame.draw.rect(self.screen, hex_color("#101827" if index == selected else "#0B1220"), row)
            pygame.draw.rect(self.screen, hex_color(COLORS["upgrade"] if index == selected else COLORS["panel_2"]), row, 2)
            self.font_tiny.render_to(self.screen, (row.x + 16, row.y + 7), info["label"].upper(), hex_color(COLORS["text"]))
            effect = upgrade_effect_value(key, active)
            if info["kind"] == "percent":
                effect_text = f"{effect * 100:+.1f}%"
            elif info["kind"] == "integer":
                effect_text = f"{int(round(effect)):+d}{info['unit']}"
            else:
                effect_text = f"{effect:+.1f}{info['unit']}"
            self.font_tiny.render_to(self.screen, (row.x + 16, row.y + 27), f"ativo {active}  | comprado {purchased}  | efeito {effect_text}", hex_color(COLORS["muted"]))
            buttons.append(self._button(row.right - 44, row.y + 8, 30, 30, "+", f"char_upgrade_plus:{key}", mouse_pos, COLORS["xp"]))
            buttons.append(self._button(row.x + 270, row.y + 8, 30, 30, "-", f"char_upgrade_minus:{key}", mouse_pos, COLORS["muted_2"]))
            bar = pygame.Rect(row.x + 314, row.y + 16, row.width - 380, 14)
            pygame.draw.rect(self.screen, hex_color("#050812"), bar)
            seg_w = max(8, (bar.width - 18) // UPGRADE_LEVEL_MAX)
            for level in range(1, UPGRADE_LEVEL_MAX + 1):
                seg = pygame.Rect(bar.x + (level - 1) * (seg_w + 2), bar.y, seg_w, bar.height)
                if level <= active:
                    color = COLORS["xp"]
                elif level <= purchased:
                    color = COLORS["coin"]
                else:
                    color = COLORS["panel_2"]
                pygame.draw.rect(self.screen, hex_color(color), seg)
            if active == 0:
                self.font_tiny.render_to(self.screen, (bar.x, bar.y + 18), "DESAFIO", hex_color(COLORS["danger"]))
            if purchased < UPGRADE_LEVEL_MAX:
                cost = upgrade_cost(key, purchased + 1)
                self.font_tiny.render_to(self.screen, (row.right - 190, row.y + 27), f"prox {cost}", hex_color(COLORS["coin"]))
            else:
                self.font_tiny.render_to(self.screen, (row.right - 190, row.y + 27), "MAX", hex_color(COLORS["xp"]))
            y += 58
        buttons.append(self._button(panel.centerx - 230, panel.bottom - 52, 210, 38, "Salvar mudancas", "char_upgrades_save", mouse_pos, COLORS["xp"]))
        buttons.append(self._button(panel.centerx + 20, panel.bottom - 52, 210, 38, "Voltar", "char_upgrades_back", mouse_pos, COLORS["muted_2"]))
        return buttons

    def render_character_upgrade_confirm(self, key, mouse_pos):
        draft = {k: v["active_level"] for k, v in character_upgrades().items()}
        self.render_character_upgrades(draft, mouse_pos, list(CHARACTER_UPGRADES.keys()).index(key) if key in CHARACTER_UPGRADES else 0)
        state = character_upgrades().get(key)
        if not state:
            return []
        next_level = min(UPGRADE_LEVEL_MAX, state["purchased_level"] + 1)
        box = pygame.Rect(322, 238, 456, 220)
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((5, 10, 18, 178))
        self.screen.blit(overlay, (0, 0))
        arcade_theme.draw_panel(self.screen, box, border=COLORS["coin"], fill="#101827", shadow=True)
        label = CHARACTER_UPGRADES[key]["label"]
        cost = upgrade_cost(key, next_level)
        self._center_text("CONFIRMAR MELHORIA", self.font, box.y + 28, COLORS["coin"])
        self._center_text(f"{label} para nivel {next_level}", self.font_tiny, box.y + 80, COLORS["text"])
        self._center_text(f"Custo: {cost} moedas", self.font_tiny, box.y + 112, COLORS["coin"])
        return [
            self._button(box.x + 58, box.bottom - 70, 150, 42, "Comprar", "char_upgrade_confirm_yes", mouse_pos, COLORS["coin"]),
            self._button(box.right - 208, box.bottom - 70, 150, 42, "Cancelar", "char_upgrade_confirm_no", mouse_pos, COLORS["muted_2"]),
        ]

    def render_records(self, mouse_pos):
        arcade_theme.draw_background(self.screen, pygame.time.get_ticks() / 1000.0)
        panel = pygame.Rect(90, 64, SCREEN_WIDTH - 180, SCREEN_HEIGHT - 118)
        arcade_theme.draw_panel(self.screen, panel, border=COLORS["coin"], title_bar=True)
        self._center_text("RECORDS", self.font_title, panel.y + 34, COLORS["coin"])
        self._center_text("TOP 10 MAIORES PONTUACOES", self.font_small, panel.y + 72, COLORS["muted"])

        records = load_records()
        buttons = []
        y = panel.y + 112
        headers = [("#", panel.x + 28), ("Nome", panel.x + 78), ("Pts", panel.x + 238), ("Tempo", panel.x + 350), ("Run", panel.x + 462), ("", panel.right - 178)]
        for label, x in headers:
            self.font_tiny.render_to(self.screen, (x, y), label.upper(), hex_color(COLORS["muted_2"]))
        y += 28

        if not records:
            self._center_text("Nenhum record salvo ainda.", self.font, panel.centery, COLORS["muted"])
        for index, record in enumerate(records[:10]):
            row = pygame.Rect(panel.x + 22, y - 6, panel.width - 44, 44)
            fill = "#101827" if index % 2 == 0 else "#0B1220"
            pygame.draw.rect(self.screen, hex_color(fill), row)
            pygame.draw.rect(self.screen, hex_color(COLORS["panel_2"]), row, 1)
            mins = int(record["time"] // 60)
            secs = int(record["time"] % 60)
            details = record.get("details", {})
            players = details.get("players", []) if isinstance(details, dict) else []
            run_bits = []
            for player in players[:2]:
                run_bits.append(f"J{player.get('player', '?')} {player.get('class_name', '?')} Nv{player.get('level', 1)}")
            if not run_bits:
                run_bits = [record.get("build", "Legacy")[:34]]
            values = [
                (f"{index + 1:02d}", panel.x + 28, COLORS["coin"]),
                (record["name"], panel.x + 78, COLORS["text"]),
                (str(record["score"]), panel.x + 238, COLORS["xp"]),
                (f"{mins:02d}:{secs:02d}", panel.x + 350, COLORS["special"]),
            ]
            for text, x, color in values:
                self.font_tiny.render_to(self.screen, (x, y), text, hex_color(color))
            self._render_fit(self.font_tiny, " | ".join(run_bits), (panel.x + 462, y), hex_color(COLORS["muted"]), panel.width - 680)
            buttons.append(self._button(panel.right - 182, y - 8, 74, 30, "Info", f"record_details:{index}", mouse_pos, COLORS["coin"]))
            buttons.append(self._button(panel.right - 100, y - 8, 60, 30, "Del", f"record_delete:{index}", mouse_pos, COLORS["danger"]))
            y += 46

        buttons.append(self._button(panel.centerx - 100, panel.bottom - 54, 200, 38, "Voltar", "records_back", mouse_pos, COLORS["muted_2"]))
        return buttons

    def render_record_details(self, record_index, mouse_pos):
        arcade_theme.draw_background(self.screen, pygame.time.get_ticks() / 1000.0)
        self._record_tooltip = None
        records = load_records()
        record = records[record_index] if 0 <= record_index < len(records) else None
        panel = pygame.Rect(76, 40, SCREEN_WIDTH - 152, SCREEN_HEIGHT - 84)
        arcade_theme.draw_panel(self.screen, panel, border=COLORS["coin"], title_bar=True)
        if not record:
            self._center_text("RECORD NAO ENCONTRADO", self.font_title, panel.centery, COLORS["danger"])
            return [self._button(panel.centerx - 100, panel.bottom - 52, 200, 38, "Voltar", "records_back", mouse_pos, COLORS["muted_2"])]

        mins = int(record["time"] // 60)
        secs = int(record["time"] % 60)
        self._center_text(f"#{record_index + 1:02d} {record['name']}  |  {record['score']} PTS  |  {mins:02d}:{secs:02d}", self.font_title, panel.y + 34, COLORS["coin"])
        details = record.get("details", {}) if isinstance(record.get("details", {}), dict) else {}
        players = details.get("players", [])
        if not players:
            self._render_fit(self.font_small, record.get("build", "Record antigo sem dados detalhados."), (panel.x + 34, panel.y + 110), hex_color(COLORS["text"]), panel.width - 68)
            return [self._button(panel.centerx - 100, panel.bottom - 52, 200, 38, "Voltar", "records_back", mouse_pos, COLORS["muted_2"])]

        card_w = (panel.width - 92) // max(1, min(2, len(players)))
        for idx, player in enumerate(players[:2]):
            x = panel.x + 28 + idx * (card_w + 36)
            card = pygame.Rect(x, panel.y + 84, card_w, panel.height - 156)
            arcade_theme.draw_panel(self.screen, card, border=COLORS["special"] if idx else COLORS["xp"], fill="#080C18", shadow=False)
            icon = pygame.Surface((52, 52), pygame.SRCALPHA)
            class_key = player.get("class", "vanguard")
            class_color = CHARACTERS.get(class_key, {}).get("core_color", COLORS["xp"])
            arcade_theme.draw_pixel_icon(icon, (4, 4, 44, 44), class_key, color=class_color, label=str(player.get("player", "?")))
            self.screen.blit(icon, (card.x + 16, card.y + 18))
            self.font_small.render_to(self.screen, (card.x + 78, card.y + 18), f"J{player.get('player', '?')} {player.get('class_name', '?')}", hex_color(COLORS["text"]))
            self.font_tiny.render_to(self.screen, (card.x + 78, card.y + 48), f"Nivel {player.get('level', 1)}  |", hex_color(COLORS["muted"]))
            kill_rect = pygame.Rect(card.x + 182, card.y + 44, 96, 22)
            pygame.draw.rect(self.screen, hex_color("#101827"), kill_rect)
            pygame.draw.rect(self.screen, hex_color(COLORS["coin"]), kill_rect, 1)
            self.font_tiny.render_to(self.screen, (kill_rect.x + 6, kill_rect.y + 4), f"Kills {player.get('kills', 0)}", hex_color(COLORS["coin"]))
            self.font_tiny.render_to(self.screen, (kill_rect.right + 14, card.y + 48), f"|  Pts {player.get('score', 0)}", hex_color(COLORS["muted"]))
            if kill_rect.collidepoint(mouse_pos):
                self._record_tooltip = "Abrir lista de inimigos derrotados"

            y = card.y + 92
            y = self._draw_record_items(card, player.get("items", []), y, mouse_pos)
            y = self._draw_record_stamp_icons(card, player.get("stamps", {}), y, mouse_pos)
            y = self._draw_record_badges(card, "SY", player.get("synergies", []), y, COLORS["coin"], mouse_pos=mouse_pos)
            passives = [{"key": p.get("key", "?"), "level": p.get("level", 0)} for p in player.get("passives", [])]
            y = self._draw_record_badges(card, "SK", passives, y, COLORS["upgrade"], max_items=12, mouse_pos=mouse_pos)
            y = self._draw_record_stats(card, player.get("stats", {}), y, mouse_pos)
            self._draw_record_omni(card, details.get("omni", {}), y, mouse_pos)

        if self._record_tooltip:
            self._draw_record_tooltip(mouse_pos, self._record_tooltip)
        buttons = [self._button(panel.centerx - 100, panel.bottom - 52, 200, 38, "Voltar", "records_back", mouse_pos, COLORS["muted_2"])]
        for idx, player in enumerate(players[:2]):
            card_w = (panel.width - 92) // max(1, min(2, len(players)))
            x = panel.x + 28 + idx * (card_w + 36)
            buttons.append(("record_kills", pygame.Rect(x + 182, panel.y + 128, 96, 22)))
        return buttons

    def _draw_record_items(self, card, items, y, mouse_pos):
        self._section_icon(card.x + 16, y, "IT", COLORS["xp"])
        for index, item in enumerate(items[:5]):
            rect = pygame.Rect(card.x + 58 + index * 54, y, 44, 44)
            pygame.draw.rect(self.screen, hex_color(COLORS["panel_2"]), rect)
            pygame.draw.rect(self.screen, hex_color(COLORS["xp"] if item.get("rank", 1) == 1 else COLORS["coin"]), rect, 2)
            icon_item = InventoryItem(
                key=item.get("key", "?"),
                level=item.get("level", 1),
                hybrid_sources=tuple(item.get("sources", ())),
            )
            try:
                self._draw_item_icon(icon_item, rect.inflate(-6, -6), None, show_level=False)
            except Exception:
                key = self._record_code(item.get("key", "?"))
                surf, text_rect = self.font_tiny.render(key, hex_color(COLORS["text"]))
                self.screen.blit(surf, (rect.centerx - text_rect.width // 2, rect.y + 10))
            self.font_tiny.render_to(self.screen, (rect.x + 27, rect.y + 27), str(item.get("level", 1)), hex_color(COLORS["coin"]))
            if rect.collidepoint(mouse_pos):
                self._record_tooltip = f"{item.get('name', item.get('key', '?'))} Nv{item.get('level', 1)}"
        return y + 58

    def _draw_record_stamp_icons(self, card, stamps, y, mouse_pos):
        self._section_icon(card.x + 16, y, "SE", COLORS["special"])
        x = card.x + 58
        for weapon_key, border in (("weapon_1", COLORS["special"]), ("weapon_2", COLORS["sword"])):
            for stamp in stamps.get(weapon_key, [])[:3]:
                rect = pygame.Rect(x, y, 38, 38)
                pygame.draw.rect(self.screen, hex_color(COLORS["panel_2"]), rect)
                pygame.draw.rect(self.screen, hex_color(border), rect, 2)
                code = self._record_code(stamp.get("key", "?"))
                surf, text_rect = self.font_tiny.render(code, hex_color(COLORS["text"]))
                self.screen.blit(surf, (rect.centerx - text_rect.width // 2, rect.y + 8))
                self.font_tiny.render_to(self.screen, (rect.x + 23, rect.y + 23), str(stamp.get("level", 1)), hex_color(COLORS["coin"]))
                if rect.collidepoint(mouse_pos):
                    self._record_tooltip = f"{stamp.get('name', stamp.get('key', '?'))} Nv{stamp.get('level', 1)}"
                x += 44
            x += 8
        return y + 50

    def _draw_record_badges(self, card, section_code, values, y, color, max_items=8, mouse_pos=(0, 0)):
        self._section_icon(card.x + 16, y, section_code, color)
        x = card.x + 58
        row_y = y
        if not values:
            values = [{"key": "--", "level": 0}]
        for index, value in enumerate(values[:max_items]):
            if x + 42 > card.right - 14:
                x = card.x + 58
                row_y += 42
            key = value.get("key", value) if isinstance(value, dict) else str(value)
            level = value.get("level", "") if isinstance(value, dict) else ""
            rect = pygame.Rect(x, row_y, 36, 34)
            pygame.draw.rect(self.screen, hex_color(COLORS["panel_2"]), rect)
            pygame.draw.rect(self.screen, hex_color(color), rect, 2)
            code = self._record_code(key)
            surf, text_rect = self.font_tiny.render(code, hex_color(COLORS["text"]))
            self.screen.blit(surf, (rect.centerx - text_rect.width // 2, rect.y + 6))
            if level:
                self.font_tiny.render_to(self.screen, (rect.x + 21, rect.y + 20), str(level), hex_color(COLORS["coin"]))
            if rect.collidepoint(mouse_pos):
                label = value.get("title", key) if isinstance(value, dict) else str(value)
                self._record_tooltip = f"{label}" + (f" Nv{level}" if level else "")
            x += 42
        return row_y + 46

    def _draw_record_stats(self, card, stats, y, mouse_pos):
        self._section_icon(card.x + 16, y, "ST", COLORS["coin"])
        entries = [
            ("HP", "Vida maxima", stats.get("max_health", "?")),
            ("SPD", "Velocidade maxima", stats.get("speed", "?")),
            ("CAD", "Cadencia", stats.get("attack_rate", "?")),
            ("DEF", "Defesa", f"{stats.get('defense', '?')}%"),
            ("DMG", "Dano ranged", stats.get("projectile_damage", "?")),
            ("SWD", "Dano melee", stats.get("sword_damage", "?")),
            ("VMP", "Vampirismo", stats.get("vampirism", "?")),
        ]
        x = card.x + 58
        for label, full_name, value in entries:
            box = pygame.Rect(x, y, 68, 34)
            pygame.draw.rect(self.screen, hex_color("#101827"), box)
            pygame.draw.rect(self.screen, hex_color(COLORS["coin"]), box, 1)
            self.font_tiny.render_to(self.screen, (box.x + 5, box.y + 4), label, hex_color(COLORS["muted_2"]))
            self.font_tiny.render_to(self.screen, (box.x + 5, box.y + 18), str(value), hex_color(COLORS["text"]))
            if box.collidepoint(mouse_pos):
                self._record_tooltip = f"{full_name}: {value}"
            x += 74
        return y + 46

    def _draw_record_omni(self, card, omni, y, mouse_pos):
        self._section_icon(card.x + 16, y, "OM", COLORS["special"])
        fragments = omni.get("fragments", {}) if isinstance(omni, dict) else {}
        done = sum(1 for value in fragments.values() if value)
        total = max(7, len(fragments) or 7)
        entries = [
            ("FR", f"Fragmentos Omni-Kernel: {done}/{total}", f"{done}/{total}"),
            ("ES", f"Missoes de escolta concluidas: {omni.get('escorts', '?')}", omni.get("escorts", "?")),
            ("MQ", f"Missoes rapidas concluidas: {omni.get('quests', '?')}", omni.get("quests", "?")),
            ("MB", f"Mini-bosses derrotados: {omni.get('miniboss_kills', '?')}", omni.get("miniboss_kills", "?")),
        ]
        x = card.x + 58
        for label, tip, value in entries:
            rect = pygame.Rect(x, y, 52, 34)
            pygame.draw.rect(self.screen, hex_color(COLORS["panel_2"]), rect)
            pygame.draw.rect(self.screen, hex_color(COLORS["special"]), rect, 1)
            self.font_tiny.render_to(self.screen, (rect.x + 5, rect.y + 4), label, hex_color(COLORS["muted_2"]))
            self.font_tiny.render_to(self.screen, (rect.x + 5, rect.y + 18), str(value), hex_color(COLORS["text"]))
            if rect.collidepoint(mouse_pos):
                self._record_tooltip = tip
            x += 58

    def _draw_record_text_lines(self, card, lines, y, color, max_lines=4):
        for line in lines[:max_lines]:
            self._render_fit(self.font_tiny, str(line), (card.x + 16, y), hex_color(color), card.width - 32)
            y += 20
        return y + 10

    def _section_icon(self, x, y, code, color):
        rect = pygame.Rect(x, y, 34, 34)
        pygame.draw.rect(self.screen, hex_color(COLORS["panel_2"]), rect)
        pygame.draw.rect(self.screen, hex_color(color), rect, 2)
        surf, text_rect = self.font_tiny.render(code, hex_color(COLORS["text"]))
        self.screen.blit(surf, (rect.centerx - text_rect.width // 2, rect.centery - text_rect.height // 2))

    def _record_code(self, key):
        clean = str(key).replace("hybrid:", "").replace("relic:", "").replace("_", " ")
        parts = [part for part in clean.replace("+", " ").split() if part]
        if not parts:
            return "??"
        if len(parts) == 1:
            return parts[0][:2].upper()
        return "".join(part[0] for part in parts[:2]).upper()

    def _draw_record_tooltip(self, mouse_pos, text):
        lines = self._wrap_text(str(text), 44)[:3]
        width = max(180, min(360, max(self.font_tiny.get_rect(line).width for line in lines) + 24))
        height = 18 * len(lines) + 16
        rect = pygame.Rect(mouse_pos[0] + 16, mouse_pos[1] + 16, width, height)
        rect.clamp_ip(pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.draw.rect(self.screen, hex_color("#050814"), rect)
        pygame.draw.rect(self.screen, hex_color(COLORS["coin"]), rect, 2)
        y = rect.y + 8
        for line in lines:
            self.font_tiny.render_to(self.screen, (rect.x + 10, y), line, hex_color(COLORS["text"]))
            y += 18

    def render_record_kills(self, record_index, mouse_pos):
        arcade_theme.draw_background(self.screen, pygame.time.get_ticks() / 1000.0)
        records = load_records()
        record = records[record_index] if 0 <= record_index < len(records) else None
        panel = pygame.Rect(180, 76, SCREEN_WIDTH - 360, SCREEN_HEIGHT - 142)
        arcade_theme.draw_panel(self.screen, panel, border=COLORS["danger"], title_bar=True)
        self._center_text("INIMIGOS DERROTADOS", self.font_title, panel.y + 36, COLORS["danger"])
        details = record.get("details", {}) if record else {}
        counts = details.get("kill_counts", {}) if isinstance(details, dict) else {}
        y = panel.y + 92
        if not counts:
            self._center_text("Este record nao possui contagem detalhada de inimigos.", self.font, panel.centery, COLORS["muted"])
        for group_name, kinds in ENEMY_GROUPS:
            self.font_small.render_to(self.screen, (panel.x + 32, y), group_name.upper(), hex_color(COLORS["coin"]))
            y += 30
            x = panel.x + 34
            for kind in kinds:
                amount = counts.get(kind, 0)
                if amount <= 0:
                    continue
                data = ENEMY_TYPES.get(kind, {})
                rect = pygame.Rect(x, y, 170, 42)
                pygame.draw.rect(self.screen, hex_color("#101827"), rect)
                pygame.draw.rect(self.screen, hex_color(data.get("color", COLORS["muted_2"])), rect, 2)
                pygame.draw.circle(self.screen, hex_color(data.get("color", COLORS["danger"])), (rect.x + 22, rect.centery), 12)
                name = kind.replace("_", " ").title()
                self.font_tiny.render_to(self.screen, (rect.x + 44, rect.y + 6), name, hex_color(COLORS["text"]))
                self.font_tiny.render_to(self.screen, (rect.x + 44, rect.y + 23), f"x{amount}", hex_color(COLORS["coin"]))
                x += 182
                if x + 170 > panel.right - 24:
                    x = panel.x + 34
                    y += 50
            y += 56
        return [self._button(panel.centerx - 100, panel.bottom - 52, 200, 38, "Voltar", "records_back", mouse_pos, COLORS["muted_2"])]

    def render_record_delete_confirm(self, record_index, mouse_pos):
        self.render_records(mouse_pos)
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((5, 10, 18, 190))
        self.screen.blit(overlay, (0, 0))
        records = load_records()
        name = records[record_index]["name"] if 0 <= record_index < len(records) else "record"
        panel = pygame.Rect(330, 220, 440, 220)
        arcade_theme.draw_panel(self.screen, panel, border=COLORS["danger"], title_bar=True)
        self._center_text("DELETAR RECORD?", self.font_title, panel.y + 44, COLORS["danger"])
        self._center_text(name, self.font, panel.y + 94, COLORS["text"])
        return [
            self._button(panel.x + 70, panel.bottom - 68, 130, 38, "Deletar", "record_delete_yes", mouse_pos, COLORS["danger"]),
            self._button(panel.right - 200, panel.bottom - 68, 130, 38, "Cancelar", "record_delete_no", mouse_pos, COLORS["muted_2"]),
        ]

    def render_record_name(self, game, name_text, mouse_pos):
        self.render_game(game, mouse_pos, flip=False)
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((5, 10, 18, 225))
        self.screen.blit(overlay, (0, 0))
        panel = pygame.Rect(250, 150, 600, 360)
        arcade_theme.draw_panel(self.screen, panel, border=COLORS["coin"], title_bar=True)
        self._center_text("NOVO RECORD!", self.font_title, panel.y + 46, COLORS["coin"])
        score = total_score(game)
        mins = int(game.time_alive // 60)
        secs = int(game.time_alive % 60)
        self._center_text(f"Pontos {score}  |  Tempo {mins:02d}:{secs:02d}", self.font, panel.y + 98, COLORS["text"])
        self._center_text("Digite seu nome:", self.font_small, panel.y + 148, COLORS["muted"])
        input_rect = pygame.Rect(panel.x + 110, panel.y + 178, panel.width - 220, 48)
        pygame.draw.rect(self.screen, hex_color("#050814"), input_rect)
        pygame.draw.rect(self.screen, hex_color(COLORS["coin"]), input_rect, 2)
        shown_name = name_text or "_"
        self._center_text(shown_name.upper(), self.font, input_rect.y + 12, COLORS["text"])
        return [
            self._button(panel.x + 110, panel.bottom - 72, 170, 42, "Salvar", "record_save", mouse_pos, COLORS["xp"], True),
            self._button(panel.right - 280, panel.bottom - 72, 170, 42, "Pular", "record_skip", mouse_pos, COLORS["muted_2"]),
        ]

    def render_mode_select(self, mouse_pos, selected=0, joystick_count=0):
        self.screen.fill(hex_color(COLORS["bg"]))
        self._draw_menu_background()
        
        c = self.components
        if pygame_gui is None or not getattr(c, "available", False):
            panel = pygame.Rect(290, 132, 520, 430)
            arcade_theme.draw_panel(self.screen, panel, border=COLORS["special"], title_bar=True)
            self._center_text("MODO DE JOGO", self.font_title, panel.y + 42, COLORS["text"])
            self._center_text(f"{joystick_count} controle(s) detectado(s)", self.font_small, panel.y + 84, COLORS["muted"])
            buttons = [
                self._button(panel.x + 100, panel.y + 150, 320, 54, "Single-Player", "single_player", mouse_pos, COLORS["xp"], selected == 0),
                self._button(panel.x + 100, panel.y + 226, 320, 54, "Multiplayer", "multiplayer", mouse_pos, COLORS["special"], selected == 1),
                self._button(panel.x + 150, panel.y + 330, 220, 42, "Voltar", "back", mouse_pos, COLORS["muted_2"], selected == 2),
            ]
            return buttons
        signature = (selected, joystick_count)
        if not hasattr(self, 'mode_select_window') or not self.mode_select_window or not self.mode_select_window.alive() or getattr(self, '_last_mode_signature', None) != signature:
            if hasattr(self, 'mode_select_window') and self.mode_select_window:
                self.mode_select_window.kill()
                
            self.mode_select_window = c.arcade_window(
                "MODO DE JOGO",
                (600, 450),
                "#mode_select_window",
                y=120,
            )
            
            c.label(pygame.Rect((20, 20), (560, 30)), f"{joystick_count} controle(s) detectado(s)", container=self.mode_select_window)
            c.label(pygame.Rect((20, 60), (560, 30)), "P1 usa teclado e mouse. P2 usa joystick no cooperativo local.", container=self.mode_select_window)
            
            self.mode_action_buttons = {}
            
            btn_sp = c.button(pygame.Rect((100, 140), (400, 60)), "Single-Player", container=self.mode_select_window, intent="primary" if selected == 0 else "secondary")
            self.mode_action_buttons[btn_sp] = "single_player"
            
            btn_mp = c.button(pygame.Rect((100, 220), (400, 60)), "Multiplayer", container=self.mode_select_window, intent="primary" if selected == 1 else "secondary")
            self.mode_action_buttons[btn_mp] = "multiplayer"
            
            btn_back = c.button(pygame.Rect((150, 320), (300, 50)), "Voltar", container=self.mode_select_window, intent="primary" if selected == 2 else "muted")
            self.mode_action_buttons[btn_back] = "back"
            
            self._last_mode_signature = signature
            
        self.draw_gui_layer()
        return []

    def render_character_select(self, char_class, mouse_pos, multiplayer=False, char_class_2=None, active_player=0):
        self.screen.fill(hex_color(COLORS["bg"]))
        self._draw_menu_background()
        unlocked = is_character_unlocked(char_class)
        
        c = self.components
        if pygame_gui is None or not getattr(c, "available", False):
            data = CHARACTERS[char_class]
            panel = pygame.Rect(110, 52, SCREEN_WIDTH - 220, SCREEN_HEIGHT - 92)
            arcade_theme.draw_panel(self.screen, panel, border=data["core_color"], title_bar=True)
            title = "SELECAO COOP" if multiplayer else "SELECIONE SEU PERSONAGEM"
            self._center_text(title, self.font_title, panel.y + 30, COLORS["text"])
            self._center_text(data["name"].upper(), self.font_big, panel.y + 88, data["core_color"])
            shape = pygame.Surface((140, 140), pygame.SRCALPHA)
            arcade_theme.draw_pixel_icon(shape, (10, 10, 120, 120), char_class, color=data["core_color"], label=data["name"][:2])
            self.screen.blit(shape, (panel.centerx - 70, panel.y + 150))
            if not unlocked:
                self._center_text(f"BLOQUEADO - {character_price(char_class)} MOEDAS", self.font, panel.y + 292, COLORS["coin"])
            y = panel.y + 315
            self._center_text(f"ARMAS: {data['weapon_1']} / {data['weapon_2']}", self.font, y, COLORS["text"])
            y += 36
            specials = data.get("specials", {})
            self._center_text(f"ESPECIAIS: {specials.get('weapon_1', data['special'])} / {specials.get('weapon_2', data['special'])}", self.font_small, y, COLORS["muted"])
            y += 34
            self._center_text(f"COMBO: {specials.get('combo', 'Ultimate combinada')}", self.font_small, y, COLORS["muted"])
            buttons = [
                self._button(panel.x + 36, panel.bottom - 74, 180, 44, "< Anterior", "prev_char", mouse_pos, COLORS["special"]),
                self._button(panel.right - 216, panel.bottom - 74, 180, 44, "Proximo >", "next_char", mouse_pos, COLORS["special"]),
                self._button(panel.centerx - 110, panel.bottom - 82, 220, 56, "Confirmar", "confirm", mouse_pos, COLORS["xp"] if unlocked else COLORS["muted_2"], True),
            ]
            return buttons
        signature = (char_class, multiplayer, char_class_2, active_player, unlocked)
        if not hasattr(self, 'character_select_window') or not self.character_select_window or not self.character_select_window.alive() or getattr(self, '_last_char_signature', None) != signature:
            if hasattr(self, 'character_select_window') and self.character_select_window:
                self.character_select_window.kill()
                
            title = "SELECAO COOP" if multiplayer else "SELECIONE SEU PERSONAGEM"
            self.character_select_window = c.arcade_window(
                title,
                (900, 600),
                "#character_select_window",
                y=50,
            )
            
            if multiplayer:
                c.label(pygame.Rect((20, 10), (860, 20)), f"Turno do Jogador {active_player + 1}. Ambos podem escolher o mesmo personagem.", container=self.character_select_window)

            data = CHARACTERS[char_class]
            
            # Create a surface to draw the shape manually
            shape_surf = pygame.Surface((120, 120), pygame.SRCALPHA)
            color = hex_color(data["color"])
            core = hex_color(data["core_color"])
            center = (60, 60)
            pygame.draw.circle(shape_surf, color, center, 45)
            if data["shape"] == "circle_triangle":
                pts = [(center[0] + 25, center[1]), (center[0] - 15, center[1] - 20), (center[0] - 15, center[1] + 20)]
                pygame.draw.polygon(shape_surf, core, pts)
            elif data["shape"] == "circle_square":
                pygame.draw.rect(shape_surf, core, pygame.Rect(38, 38, 44, 44), border_radius=4)
            elif data["shape"] == "circle_diamond":
                pts = [(60, 24), (92, 60), (60, 96), (28, 60)]
                pygame.draw.polygon(shape_surf, core, pts)
            else:
                pygame.draw.circle(shape_surf, core, center, 15)
                
            c.image(pygame.Rect((390, 40), (120, 120)), shape_surf, container=self.character_select_window)
            
            c.label(pygame.Rect((20, 160), (860, 40)), data["name"].upper(), container=self.character_select_window)
            if not unlocked:
                c.label(pygame.Rect((20, 188), (860, 24)), f"BLOQUEADO - compre na Loja de Moedas por {character_price(char_class)} moedas.", container=self.character_select_window)
            c.label(pygame.Rect((20, 210), (860, 30)), f"Armas: {data['weapon_1']} / {data['weapon_2']}", container=self.character_select_window)
            
            specials = data.get("specials", {})
            special_text = f"Especiais: {specials.get('weapon_1', data['special'])} / {specials.get('weapon_2', data['special'])}"
            c.label(pygame.Rect((20, 240), (860, 30)), special_text, container=self.character_select_window)
            c.label(pygame.Rect((20, 270), (860, 30)), f"Combo: {specials.get('combo', 'Ultimate combinada')}", container=self.character_select_window)
            
            passives = list(data["passives"].values())
            passives_panel = c.panel(pygame.Rect((20, 320), (860, 160)), container=self.character_select_window)
            
            start_y = 10
            columns = (20, 440)
            for index, p_data in enumerate(passives):
                col = index % 2
                row = index // 2
                x = columns[col]
                y = start_y + row * 40
                category = p_data.get("category", "Kit")
                c.label(pygame.Rect((x, y), (400, 20)), f"{category.upper()} | {p_data['title']}", container=passives_panel)
                c.label(pygame.Rect((x, y+20), (400, 20)), p_data["description"][:58], container=passives_panel)

            if multiplayer and char_class_2:
                p1 = CHARACTERS[char_class]["name"]
                p2 = CHARACTERS[char_class_2]["name"]
                c.label(pygame.Rect((20, 490), (860, 30)), f"P1: {p1}    |    P2: {p2}", container=self.character_select_window)
                
            self.char_action_buttons = {}
            btn_prev = c.button(pygame.Rect((20, 530), (150, 40)), "< Anterior", container=self.character_select_window, intent="secondary")
            self.char_action_buttons[btn_prev] = "prev_char"
            
            btn_next = c.button(pygame.Rect((730, 530), (150, 40)), "Proximo >", container=self.character_select_window, intent="secondary")
            self.char_action_buttons[btn_next] = "next_char"
            
            btn_confirm = c.button(pygame.Rect((350, 520), (200, 50)), "Confirmar", container=self.character_select_window, intent="primary" if unlocked else "muted")
            self.char_action_buttons[btn_confirm] = "confirm"

            self._last_char_signature = signature

        self.draw_gui_layer()
        return []

    def render_pause(self, game, options, selected, mouse_pos):
        self.render_game(game, mouse_pos, flip=False)
        return self._overlay_menu("PAUSADO", options, selected, mouse_pos)

    def render_progression(self, game, mouse_pos):
        self.render_game(game, mouse_pos, flip=False)
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((5, 10, 18, 218))
        self.screen.blit(overlay, (0, 0))

        panel = pygame.Rect(120, 70, SCREEN_WIDTH - 240, SCREEN_HEIGHT - 120)
        pygame.draw.rect(self.screen, hex_color(COLORS["panel"]), panel, border_radius=8)
        pygame.draw.rect(self.screen, (250, 204, 21), panel, width=2, border_radius=8)

        self._center_text("PROGRESSAO", self.font_title, panel.y + 22, COLORS["coin"])
        self._center_text("Calice da Singularidade / Omni-Kernel", self.font, panel.y + 58, COLORS["text"])

        x = panel.x + 34
        y = panel.y + 104
        max_w = panel.width - 68
        info_lines = [
            "O Calice da Singularidade e um artefato dividido em 7 fragmentos. Cada fragmento vem de um objetivo longo da run.",
            "Ao completar os 7, o Omni-Kernel desperta: concede bonus permanentes massivos, ativa lasers orbitais automaticos e libera uma habilidade ativa de parada temporal sobre os inimigos.",
            "Botao reservado para ativar o Omni-Kernel: acao Omni-Kernel. Padrao teclado: H. Padrao controle: botao 10.",
        ]
        for text in info_lines:
            for line in self._wrap_text(text, 92):
                self.font_tiny.render_to(self.screen, (x, y), line, hex_color(COLORS["muted"]))
                y += 18
            y += 4

        y += 8
        self.font_small.render_to(self.screen, (x, y), "Objetivos do Calice", hex_color(COLORS["coin"]))
        y += 30

        fragments = getattr(game, "chalice_fragments", {})
        descriptions = {
            "miniboss_3": "Derrote o 3o Miniboss da run.",
            "world_hidden": "Encontre o fragmento escondido aleatoriamente no mapa principal.",
            "pocket_hidden": "Entre na Dimensao de Bolso e colete o fragmento fixo antes do tempo acabar.",
            "escort_4": "Conclua 4 missoes de escolta/resgate com sucesso.",
            "quest_5": "Conclua 5 missoes rapidas de objetivo.",
            "combat_mark": f"Alcance {CHALICE_KILL_TARGET} abates totais ou combo x{CHALICE_COMBO_TARGET}.",
            "time_mark": f"Sobreviva por {int(CHALICE_TIME_TARGET // 60)} minutos.",
        }
        for entry in CHALICE_FRAGMENTS:
            done = fragments.get(entry["key"], False)
            marker = "[OK]" if done else "[  ]"
            color = COLORS["xp"] if done else COLORS["muted_2"]
            title = f"{marker} {entry['name']} ({entry['label']})"
            self.font_tiny.render_to(self.screen, (x, y), title, hex_color(color))
            self.font_tiny.render_to(self.screen, (x + 260, y), descriptions.get(entry["key"], ""), hex_color(COLORS["text"] if done else COLORS["muted"]))
            y += 26

        status = "OMNI-KERNEL ATIVO" if getattr(game, "omni_kernel_active", False) else "OMNI-KERNEL INATIVO"
        status_color = COLORS["coin"] if getattr(game, "omni_kernel_active", False) else COLORS["muted_2"]
        self._center_text(status, self.font, panel.bottom - 88, status_color)
        buttons = [self._button(panel.centerx - 110, panel.bottom - 54, 220, 38, "Voltar", "progression_back", mouse_pos, COLORS["panel_2"])]
        return buttons

    def render_game_over(self, game, mouse_pos, selected=0):
        self.render_game(game, mouse_pos, flip=False)
        title = "FIM DA SOBREVIVENCIA"
        options = [("Reiniciar", "restart"), ("Trocar Personagem", "change_character"), ("Voltar ao Menu", "menu"), ("Fechar", "quit")]
        buttons = self._overlay_menu(title, options, selected, mouse_pos, extra=f"Tempo {int(game.time_alive)}s  |  Abates {game.player.kills}  |  Pontos {game.player.score}")

        def draw_build_for_player(p, x_start, y_start, label):
            self._center_text(label, self.font_small, y_start, COLORS["muted_2"])
            inv = game.get_inventory(p.player_index)
            active_items = [item for item in inv.item_list() if inv.is_active(item.key)]
            # Itens
            for i in range(5):
                slot_rect = pygame.Rect(x_start + i * 44 - (5 * 44) // 2 + 22, y_start + 24, 38, 38)
                pygame.draw.rect(self.screen, (30, 41, 59), slot_rect, width=1, border_radius=4)
                if i < len(active_items):
                    self._draw_item_icon(active_items[i], slot_rect, game, show_level=True)
            # Passivas
            passives = [(k, v) for k, v in p.passives.items() if v > 0]
            for i in range(10):
                slot_rect = pygame.Rect(x_start + i * 26 - (10 * 26) // 2 + 13, y_start + 70, 22, 22)
                pygame.draw.rect(self.screen, (30, 41, 59), slot_rect, width=1, border_radius=2)
                if i < len(passives):
                    pygame.draw.rect(self.screen, hex_color(COLORS["text"]), slot_rect, border_radius=2)
                    lvl_surf, l_rect = self.font_tiny.render(str(passives[i][1]), hex_color(COLORS["bg"]))
                    self.screen.blit(lvl_surf, (slot_rect.centerx - l_rect.width // 2, slot_rect.centery - l_rect.height // 2))

        if game.multiplayer:
            draw_build_for_player(game.player, SCREEN_WIDTH // 4, 520, f"BUILD J1 ({CHARACTERS[game.player.char_class]['name']})")
            draw_build_for_player(game.player2, (SCREEN_WIDTH // 4) * 3, 520, f"BUILD J2 ({CHARACTERS[game.player2.char_class]['name']})")
        else:
            draw_build_for_player(game.player, SCREEN_WIDTH // 2, 520, f"BUILD FINAL ({CHARACTERS[game.player.char_class]['name']})")

        return buttons

    def render_commands(self, mouse_pos, lines=None):
        self.screen.fill(hex_color(COLORS["bg"]))
        self._draw_menu_background()
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((5, 10, 18, 220))
        self.screen.blit(overlay, (0, 0))

        if pygame_gui is None or not getattr(self, "components", None) or not self.components.available:
            pass # fallback if needed, omitted for brevity

        c = self.components
        if not hasattr(self, 'commands_window') or not self.commands_window or not self.commands_window.alive():
            if hasattr(self, 'commands_window') and self.commands_window:
                self.commands_window.kill()
            
            self.commands_window = c.arcade_window(
                "COMANDOS E CONTROLES",
                (700, 500),
                "#commands",
                y=100,
            )
            
            if not lines:
                lines = [
                    "Teclado (Single Player / J1):",
                    "  W, A, S, D - Movimento",
                    "  Espaco - Dash (Esquiva)",
                    "  Click Esquerdo / J - Ataque / Tiro Primario",
                    "  Click Direito / K - Especial",
                    "  Q / R - Alternar Arma",
                    "  E / Tab - Inventario / Pausa",
                    "  R - Habilidade Suprema / Combo",
                    "  H - Omni-Kernel (quando desbloqueado)",
                    "",
                    "Controle (Xbox/PlayStation) (J1/J2):",
                    "  Analogico Esquerdo / D-Pad - Movimento",
                    "  Analogico Direito - Mirar",
                    "  Gatilho Direito (R2/RT) - Ataque / Tiro",
                    "  Gatilho Esquerdo (L2/LT) - Especial",
                    "  A / Cruz - Dash",
                    "  Y / Triangulo - Habilidade Suprema",
                    "  Botao 10 - Omni-Kernel (quando desbloqueado)",
                    "  L1 / R1 - Alternar Arma",
                    "  Start / Options - Pausa / Inventario"
                ]
            
            text = "<br>".join(lines)
            c.text_box(pygame.Rect((20, 10), (660, 360)), text, container=self.commands_window)
            
            self.commands_action_buttons = {}
            btn_back = c.button(
                pygame.Rect((200, 390), (300, 40)),
                "Voltar",
                container=self.commands_window,
                intent="secondary"
            )
            self.commands_action_buttons[btn_back] = "back"

        self.draw_gui_layer()
        return []

    def render_settings(self, rows, selected, selected_slot, capture_binding, fullscreen, control_pref, joystick_count, mouse_pos):
        self.screen.fill(hex_color(COLORS["bg"]))
        self._draw_menu_background()
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((5, 10, 18, 220))
        self.screen.blit(overlay, (0, 0))
        
        if pygame_gui is None or not getattr(self, "components", None) or not self.components.available:
            pass # fallback

        c = self.components
        signature = (selected, selected_slot, capture_binding, fullscreen, control_pref)
        if not hasattr(self, 'settings_window') or not self.settings_window or not self.settings_window.alive() or getattr(self, '_last_settings_signature', None) != signature:
            if hasattr(self, 'settings_window') and self.settings_window:
                self.settings_window.kill()
            
            self.settings_window = c.arcade_window(
                "CONFIGURACOES",
                (800, 600),
                "#settings",
                y=50,
            )
            
            self.settings_action_buttons = {}
            self.settings_rows = {}
            
            # Global Options
            y_offset = 10
            c.label(pygame.Rect((20, y_offset), (300, 30)), f"Tela Cheia: {'Ativada' if fullscreen else 'Desativada'}", container=self.settings_window)
            btn_fs = c.button(pygame.Rect((330, y_offset), (150, 30)), "Alternar", container=self.settings_window, intent="primary" if selected == len(rows) else "secondary")
            self.settings_action_buttons[btn_fs] = "toggle_fullscreen"
            
            y_offset += 40
            c.label(pygame.Rect((20, y_offset), (300, 30)), f"Preferencia de Controle: {control_pref.capitalize()}", container=self.settings_window)
            btn_cp = c.button(pygame.Rect((330, y_offset), (150, 30)), "Alternar", container=self.settings_window, intent="primary" if selected == len(rows)+1 else "secondary")
            self.settings_action_buttons[btn_cp] = "toggle_control_pref"
            
            y_offset += 50
            scroll_panel = c.scroll(pygame.Rect((20, y_offset), (760, 340)), container=self.settings_window)
            
            inner_y = 10
            for index, row in enumerate(rows):
                is_row_selected = index == selected
                c.label(pygame.Rect((10, inner_y), (250, 30)), row['label'], container=scroll_panel)
                
                # Slot 0
                btn_slot0 = c.button(
                    pygame.Rect((270, inner_y), (150, 30)),
                    "Capturando..." if is_row_selected and selected_slot == 0 and capture_binding else row['bindings'][0],
                    container=scroll_panel,
                    intent="selected" if is_row_selected and selected_slot == 0 else "secondary"
                )
                self.settings_rows[btn_slot0] = f"bind:{index}:0"
                
                # Slot 1
                btn_slot1 = c.button(
                    pygame.Rect((430, inner_y), (150, 30)),
                    "Capturando..." if is_row_selected and selected_slot == 1 and capture_binding else row['bindings'][1],
                    container=scroll_panel,
                    intent="selected" if is_row_selected and selected_slot == 1 else "secondary"
                )
                self.settings_rows[btn_slot1] = f"bind:{index}:1"
                
                inner_y += 40
                
            scroll_panel.set_scrollable_area_dimensions((740, inner_y))
            if selected < len(rows):
                self._scroll_container_to_item(scroll_panel, 10 + selected * 40, 30, 340, inner_y)
            
            btn_back = c.button(
                pygame.Rect((250, 500), (300, 40)),
                "Voltar ao Menu",
                container=self.settings_window,
                intent="secondary" if selected < len(rows)+2 else "primary"
            )
            self.settings_action_buttons[btn_back] = "back"
            
            self._last_settings_signature = signature

        self.draw_gui_layer()
        return []

    def _overlay_menu(self, title, options, selected, mouse_pos, extra=None):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((5, 10, 18, 192))
        self.screen.blit(overlay, (0, 0))
        self._center_text(title, self.font_big, 145, COLORS["text"])
        if extra:
            self._center_text(extra, self.font, 198, COLORS["muted"])
        buttons = []
        compact = len(options) > 7
        button_h = 42 if compact else 48
        spacing = 50 if compact else 62
        start_y = 238 if extra else (220 if compact else 235)
        for index, (label, action) in enumerate(options):
            color = COLORS["upgrade"] if index == selected else COLORS["panel_2"]
            buttons.append(self._button(410, start_y + index * spacing, 280, button_h, label, action, mouse_pos, color))
        # pygame.display.flip()
        return buttons

    def _draw_menu_background(self):
        arcade_theme.draw_background(self.screen, pygame.time.get_ticks() / 1000.0)

    def _center_text(self, text, font, y, color):
        f_rect = font.get_rect(text)
        font.render_to(self.screen, (SCREEN_WIDTH // 2 - f_rect.width // 2, y), text, hex_color(color))

    def _button(self, x, y, w, h, text, action, mouse_pos, color, selected=False):
        rect = pygame.Rect(x, y, w, h)
        hover = rect.collidepoint(mouse_pos)
        arcade_theme.draw_button(self.screen, self.font, rect, text, color, selected=selected, hover=hover)
        return action, rect

    def _draw_start_side_modules(self, frame):
        left = pygame.Rect(82, 292, 190, 220)
        right = pygame.Rect(SCREEN_WIDTH - 272, 292, 190, 220)
        arcade_theme.draw_panel(self.screen, left, border="#FFD447", fill="#090D18", shadow=True)
        arcade_theme.draw_panel(self.screen, right, border="#D96CFF", fill="#090D18", shadow=True)
        self.font_tiny.render_to(self.screen, (left.x + 14, left.y + 14), "SYSTEM STATUS", hex_color(COLORS["coin"]))
        for index, label in enumerate(("PIXEL MODE", "NEON HUD", "LOCAL COOP", "OMNI LOCK")):
            y = left.y + 48 + index * 38
            arcade_theme.draw_badge(self.screen, self.font_tiny, (left.x + 14, y, 116, 24), label, "#28D7FF" if index < 3 else "#5E6A86")
            arcade_theme.draw_slot(self.screen, (left.x + 144, y + 3, 18, 18), "#35F06B" if index < 3 else "#FF3B58", active=True)

        self.font_tiny.render_to(self.screen, (right.x + 14, right.y + 14), "ALTAR SIGNALS", hex_color(COLORS["upgrade"]))
        for index, style in enumerate(arcade_theme.ALTAR_STYLE.values()):
            y = right.y + 48 + index * 31
            arcade_theme.draw_badge(self.screen, self.font_tiny, (right.x + 14, y, 28, 24), style["glyph"], style["color"])
            self.font_tiny.render_to(self.screen, (right.x + 52, y + 5), style["label"], arcade_theme.rgb(style["color"]))

        pygame.draw.rect(self.screen, hex_color(COLORS["special"]), (frame.x + 20, frame.bottom - 38, frame.width - 40, 2))
        self.font_tiny.render_to(self.screen, (frame.x + 22, frame.bottom - 28), "BUILD: ARCADE/RETRO PIXEL-LITE", hex_color(COLORS["muted"]))

    def _wrap_text(self, text, max_chars):
        words = text.split()
        if not words:
            return [""]
        lines = []
        current = words[0]
        for word in words[1:]:
            if len(current) + len(word) + 1 <= max_chars:
                current += " " + word
            else:
                lines.append(current[:max_chars])
                current = word
        lines.append(current[:max_chars])
        return lines

    def _character_playstyle_lines(self, data):
        passives = list(data.get("passives", {}).values())
        categories = []
        for passive in passives:
            category = passive.get("category", "Kit")
            if category not in categories:
                categories.append(category)
        text = (
            f"Kit focado em {', '.join(categories[:4]).lower()}. "
            f"Usa {data.get('weapon_1', 'arma primaria')} para controlar distancia "
            f"e {data.get('weapon_2', 'arma secundaria')} para finalizar lutas. "
            f"Especial principal: {data.get('special', 'especial')}."
        )
        return self._wrap_text(text, 78)

    def handle_system_menus_event(self, event, game):
        if pygame_gui is None:
            return None

        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if hasattr(self, 'start_buttons'):
                for action, btn in self.start_buttons.items():
                    if event.ui_element == btn:
                        if self.start_window: self.start_window.kill(); self.start_window = None
                        return action

            if hasattr(self, 'pause_buttons'):
                for action, btn in self.pause_buttons.items():
                    if event.ui_element == btn:
                        if self.pause_window: self.pause_window.kill(); self.pause_window = None
                        return action

            if hasattr(self, 'game_over_buttons'):
                for action, btn in self.game_over_buttons.items():
                    if event.ui_element == btn:
                        if self.game_over_window: self.game_over_window.kill(); self.game_over_window = None
                        return action
                        
            if hasattr(self, 'commands_action_buttons'):
                for btn, action in self.commands_action_buttons.items():
                    if event.ui_element == btn:
                        return action

            if hasattr(self, 'settings_action_buttons'):
                for btn, action in self.settings_action_buttons.items():
                    if event.ui_element == btn:
                        return action
            if hasattr(self, 'settings_rows'):
                for btn, action in self.settings_rows.items():
                    if event.ui_element == btn:
                        return action

            if hasattr(self, 'mode_action_buttons'):
                for btn, action in self.mode_action_buttons.items():
                    if event.ui_element == btn:
                        return action
                        
            if hasattr(self, 'char_action_buttons'):
                for btn, action in self.char_action_buttons.items():
                    if event.ui_element == btn:
                        return action

        if event.type == pygame_gui.UI_WINDOW_CLOSE:
            if hasattr(self, 'pause_window') and event.ui_element == self.pause_window:
                self.pause_window = None
                return "resume"
            if hasattr(self, 'game_over_window') and event.ui_element == self.game_over_window:
                self.game_over_window = None
                return "menu"

        return None
        
