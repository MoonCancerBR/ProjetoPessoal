import pygame
try:
    import pygame_gui
except ImportError:
    pygame_gui = None

if __package__:
    from ...data.constants import *
    from ..ui_utils import hex_color
else:
    from Sobrevivencia.data.constants import *
    from Sobrevivencia.presentation.ui_utils import hex_color

class SystemMenus:
    def render_start(self, mouse_pos, selected=0):
        self.screen.fill(hex_color(COLORS["bg"]))
        self._draw_menu_background()
        self._center_text("SOBREVIVENCIA", self.font_big, 142, COLORS["text"])
        self._center_text("Top-down shooter/slasher infinito", self.font, 190, COLORS["muted"])
        self._center_text("WASD/analogico move  |  Mouse mira  |  A confirma/dash  |  B volta  |  Start pausa", self.font_small, 232, COLORS["muted"])
        buttons = []
        buttons.append(self._button(410, 286, 280, 46, "Iniciar Jogo", "character_select", mouse_pos, COLORS["xp"], selected == 0))
        buttons.append(self._button(410, 344, 280, 46, "Enciclopedia", "encyclopedia", mouse_pos, COLORS["special"], selected == 1))
        buttons.append(self._button(410, 402, 280, 46, "Comandos", "commands", mouse_pos, COLORS["special"], selected == 2))
        buttons.append(self._button(410, 460, 280, 46, "Configuracoes", "settings", mouse_pos, COLORS["upgrade"], selected == 3))
        buttons.append(self._button(410, 518, 280, 46, "Voltar ao Menu", "menu", mouse_pos, COLORS["muted_2"], selected == 4))
        # pygame.display.flip()
        return buttons

    def render_mode_select(self, mouse_pos, selected=0, joystick_count=0):
        self.screen.fill(hex_color(COLORS["bg"]))
        self._draw_menu_background()
        
        c = self.components
        signature = (selected, joystick_count)
        if not hasattr(self, 'mode_select_window') or not self.mode_select_window or not self.mode_select_window.alive() or getattr(self, '_last_mode_signature', None) != signature:
            if hasattr(self, 'mode_select_window') and self.mode_select_window:
                self.mode_select_window.kill()
                
            self.mode_select_window = c.window(
                "MODO DE JOGO",
                (600, 450),
                "#mode_select_window",
                y=120,
                close_button=False
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
        
        c = self.components
        signature = (char_class, multiplayer, char_class_2, active_player)
        if not hasattr(self, 'character_select_window') or not self.character_select_window or not self.character_select_window.alive() or getattr(self, '_last_char_signature', None) != signature:
            if hasattr(self, 'character_select_window') and self.character_select_window:
                self.character_select_window.kill()
                
            title = "SELECAO COOP" if multiplayer else "SELECIONE SEU PERSONAGEM"
            self.character_select_window = c.window(
                title,
                (900, 600),
                "#character_select_window",
                y=50,
                close_button=False
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
            
            btn_confirm = c.button(pygame.Rect((350, 520), (200, 50)), "Confirmar", container=self.character_select_window, intent="primary")
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
            
            self.commands_window = c.window(
                "COMANDOS E CONTROLES",
                (700, 500),
                "#commands",
                y=100,
                close_button=False
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
            
            self.settings_window = c.window(
                "CONFIGURACOES",
                (800, 600),
                "#settings",
                y=50,
                close_button=False
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
        for x in range(-160, SCREEN_WIDTH + 180, 80):
            pygame.draw.line(self.screen, (15, 36, 52), (x, 0), (x + 250, SCREEN_HEIGHT), 1)
        for y in range(70, SCREEN_HEIGHT, 96):
            pygame.draw.line(self.screen, (21, 48, 57), (0, y), (SCREEN_WIDTH, y - 44), 1)
        for index in range(9):
            x = 110 + index * 110
            y = 510 + (index % 3) * 18
            pygame.draw.rect(self.screen, (31, 41, 55), (x, y, 58, 34), 1, border_radius=4)

    def _center_text(self, text, font, y, color):
        f_rect = font.get_rect(text)
        font.render_to(self.screen, (SCREEN_WIDTH // 2 - f_rect.width // 2, y), text, hex_color(color))

    def _button(self, x, y, w, h, text, action, mouse_pos, color, selected=False):
        rect = pygame.Rect(x, y, w, h)
        hover = rect.collidepoint(mouse_pos)
        base = hex_color(color)
        if hover or selected:
            base = tuple(min(255, channel + 24) for channel in base)
        pygame.draw.rect(self.screen, base, rect, border_radius=7)
        pygame.draw.rect(self.screen, (226, 232, 240), rect, width=3 if selected else 1, border_radius=7)
        txt_color = (7, 17, 30) if color not in (COLORS["panel_2"], COLORS["muted_2"]) else hex_color(COLORS["text"])
        surf, s_rect = self.font.render(text, txt_color)
        self.screen.blit(surf, (x + w // 2 - s_rect.width // 2, y + h // 2 - s_rect.height // 2))
        return action, rect

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
        
