import pygame
from itertools import combinations, combinations_with_replacement
try:
    import pygame_gui
    from pygame_gui.elements import UIWindow, UIButton, UILabel, UIPanel, UITextBox, UIScrollingContainer
    from pygame_gui.core import ObjectID
except ImportError:
    pygame_gui = None
    UIWindow = UIButton = UILabel = UIPanel = UITextBox = UIScrollingContainer = None
    class ObjectID:
        def __init__(self, class_id=None, object_id=None):
            pass

if __package__:
    from ...data.constants import *
    from ...data.items import BASE_ITEM_KEYS, ITEM_DEFINITIONS, InventoryItem, MAX_ACTIVE_ITEMS, MAX_ITEM_LEVEL, item_display_name, item_short_description, RELIC_DEFINITIONS
    from ..ui_utils import hex_color
else:
    from Sobrevivencia.data.constants import *
    from Sobrevivencia.data.items import BASE_ITEM_KEYS, ITEM_DEFINITIONS, InventoryItem, MAX_ACTIVE_ITEMS, MAX_ITEM_LEVEL, item_display_name, item_short_description, RELIC_DEFINITIONS
    from Sobrevivencia.presentation.ui_utils import hex_color

import math

class ShopMenus:
    def init_shop_menus(self):
        self.stat_shop_window = None
        self.stat_shop_buttons = {}
        self.stat_shop_reroll_buttons = {}
        self.stat_shop_back_button = None
        
        self.skills_window = None
        self.skills_buttons = {}

    def render_stat_shop(self, game, selected, mouse_pos):
        self.render_game(game, mouse_pos, flip=False, draw_gui=False)
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((5, 10, 18, 224))
        self.screen.blit(overlay, (0, 0))
        
        if pygame_gui is None or not getattr(self, "components", None) or not self.components.available:
            return []
            
        if not hasattr(self, '_last_stat_shop_selected'):
            self._last_stat_shop_selected = -1
            self._last_stat_shop_signature = None
            
        offers_signature = tuple(
            (offer['title'], offer['cost'], tuple(effect['display'] for effect in offer['effects']))
            for offer in game.stat_shop_offers
        )
        inv = game.get_inventory(game.menu_player_index)
        signature = (game.stat_shop_unlocked(), inv.points, game.menu_player_index, offers_signature)
        
        if (not self.stat_shop_window or 
            not self.stat_shop_window.alive() or 
            self._last_stat_shop_selected != selected or 
            self._last_stat_shop_signature != signature):
            
            if self.stat_shop_window:
                self.stat_shop_window.kill()
                
            self._create_stat_shop_window(game, selected)
            self._last_stat_shop_selected = selected
            self._last_stat_shop_signature = signature
            
        self.draw_gui_layer()
        return []

    def _create_stat_shop_window(self, game, selected):
        self.stat_shop_buttons = {}
        self.stat_shop_reroll_buttons = {}
        c = self.components
        
        self.stat_shop_window = c.window(
            'LOJA DE STATUS',
            (900, 580),
            '#shop_window',
            y=80,
            close_button=False
        )
        if self.stat_shop_window is None:
            return
            
        inv = game.get_inventory(game.menu_player_index)
        points_label = f'Pontos J{game.menu_player_index + 1}' if game.multiplayer else 'Pontos disponiveis'
        points_text = f"{points_label}: {inv.points}"
        c.label(
            pygame.Rect((650, 10), (200, 30)),
            points_text,
            container=self.stat_shop_window
        )
        
        if not game.stat_shop_unlocked():
            current_level = max(player.level for player in game.players)
            needed = max(0, STAT_SHOP_UNLOCK_LEVEL - current_level)
            c.label(
                pygame.Rect((200, 100), (500, 40)),
                f"Desbloqueia no nivel {STAT_SHOP_UNLOCK_LEVEL}",
                container=self.stat_shop_window
            )
            c.label(
                pygame.Rect((200, 150), (500, 30)),
                f"Maior nivel atual {current_level}. Faltam {needed} niveis.",
                container=self.stat_shop_window
            )
            self.stat_shop_back_button = c.button(
                pygame.Rect((350, 480), (200, 40)),
                'Voltar',
                container=self.stat_shop_window,
                intent='muted'
            )
            return
            
        subtitle_text = f"Roletar abre 3 ofertas por {STAT_SHOP_ROLL_COST} ponto. Jogar novamente uma oferta custa {STAT_SHOP_REROLL_COST} ponto."
        if getattr(game, "stat_shop_cooldown", 0.0) > 0:
            subtitle_text = f"Loja bloqueada por {game.stat_shop_cooldown:.0f}s apos compra recente."
        c.label(
            pygame.Rect((20, 10), (860, 30)),
            subtitle_text,
            container=self.stat_shop_window
        )
        
        if not game.stat_shop_offers:
            c.label(
                pygame.Rect((150, 200), (600, 30)),
                'Role a loja para revelar tres melhorias permanentes.',
                container=self.stat_shop_window
            )
            btn = c.button(
                pygame.Rect((320, 260), (260, 50)),
                f"Roletar ({STAT_SHOP_ROLL_COST} pt)",
                container=self.stat_shop_window,
                intent='primary' if getattr(game, "stat_shop_cooldown", 0.0) <= 0 else 'muted'
            )
            if getattr(game, "stat_shop_cooldown", 0.0) > 0:
                btn.disable()
            self.stat_shop_buttons['roll'] = btn
            
            self.stat_shop_back_button = c.button(
                pygame.Rect((350, 480), (200, 40)),
                'Voltar',
                container=self.stat_shop_window,
                intent='muted'
            )
            return
            
        card_w = 270
        card_h = 360
        start_x = 20
        gap = 20
        y = 60
        
        for index, offer in enumerate(game.stat_shop_offers):
            x = start_x + index * (card_w + gap)
            is_selected = (index == selected)
            
            panel = c.panel(
                pygame.Rect((x, y), (card_w, card_h)),
                container=self.stat_shop_window
            )
            if is_selected:
                c.panel(
                    pygame.Rect((0, 0), (card_w, card_h)),
                    container=panel,
                    object_id=ObjectID(class_id='@selected_panel', object_id='#item_button')
                )
                
            x = start_x + index * (card_w + gap)
            is_selected = (index == selected)
            
            panel = c.panel(
                pygame.Rect((x, y), (card_w, card_h)),
                container=self.stat_shop_window
            )
            if is_selected:
                c.panel(
                    pygame.Rect((0, 0), (card_w, card_h)),
                    container=panel,
                    object_id=ObjectID(class_id='@selected_panel', object_id='#item_button')
                )
                
            c.label(
                pygame.Rect((10, 10), (card_w - 20, 30)),
                offer['title'].upper(),
                container=panel
            )
            
            line_y = 60
            for effect in offer['effects']:
                c.label(
                    pygame.Rect((10, line_y), (card_w - 20, 20)),
                    effect['label'],
                    container=panel
                )
                c.label(
                    pygame.Rect((10, line_y + 20), (card_w - 20, 20)),
                    effect['display'],
                    container=panel
                )
                line_y += 50
                
            cost = offer['cost']
            altar_purchase = getattr(game, "active_altar", None) is not None and game.active_altar.kind == "stat_altar"
            on_cooldown = getattr(game, "stat_shop_cooldown", 0.0) > 0
            is_night = getattr(game, "light_level", 1.0) < 0.15
            cost_text = "Custo: 20% Max HP (SANGUE)" if is_night else f"Custo: {cost} pts"
            buy_text = "Pacto Sangrento" if is_night else (f"Comprar ({cost})" if altar_purchase else "Compra via Altar")
            
            c.label(
                pygame.Rect((10, card_h - 110), (card_w - 20, 20)),
                cost_text,
                container=panel
            )
            btn_buy = c.button(
                pygame.Rect((10, card_h - 80), (card_w - 20, 30)),
                buy_text,
                container=panel,
                intent='danger' if (altar_purchase and is_night) else ('primary' if altar_purchase and not on_cooldown else 'muted')
            )
            if not altar_purchase or on_cooldown:
                btn_buy.disable()
            self.stat_shop_buttons[index] = btn_buy
            rerolls = getattr(game, "stat_shop_offer_rerolls", {}).get(index, 0)
            reroll_label = "Sacrificar -5 HP" if rerolls >= 1 else f"Reroll ({STAT_SHOP_REROLL_COST})"
            btn_reroll = c.button(
                pygame.Rect((10, card_h - 40), (card_w - 20, 30)),
                reroll_label,
                container=panel,
                intent='secondary'
            )
            self.stat_shop_reroll_buttons[index] = btn_reroll
            
        self.stat_shop_back_button = c.button(
            pygame.Rect((350, 480), (200, 40)),
            'Voltar',
            container=self.stat_shop_window,
            intent='muted'
        )

    def handle_shop_menus_event(self, event, game):
        if pygame_gui is None:
            return None
            
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.stat_shop_back_button:
                return 'stat_shop_back'
                
            if 'roll' in self.stat_shop_buttons and event.ui_element == self.stat_shop_buttons['roll']:
                return 'stat_shop_roll'
                
            for index, btn in self.stat_shop_buttons.items():
                if event.ui_element == btn:
                    if index != 'roll':
                        return f"stat_shop_buy:{index}"
                        
            for index, btn in self.stat_shop_reroll_buttons.items():
                if event.ui_element == btn:
                    return f"stat_shop_reroll:{index}"
                    
            if hasattr(self, 'skills_back_btn') and event.ui_element == self.skills_back_btn:
                return 'skills_back'
                
            if hasattr(self, 'skills_toggle_player_btn') and self.skills_toggle_player_btn and event.ui_element == self.skills_toggle_player_btn:
                return 'skills_toggle_player'
                
            if hasattr(self, 'skills_upgrade_btn') and self.skills_upgrade_btn and event.ui_element == self.skills_upgrade_btn:
                return 'skill_upgrade'
                
            if hasattr(self, 'skills_buttons'):
                for index, btn in self.skills_buttons.items():
                    if event.ui_element == btn:
                        return f"skill_select:{index}"
                        
            if hasattr(self, 'upgrade_buttons'):
                for key, btn in self.upgrade_buttons.items():
                    if event.ui_element == btn:
                        if self.upgrade_window:
                            self.upgrade_window.kill()
                            self.upgrade_window = None
                        game.apply_upgrade(key)
                        if not game.level_up_pending:
                            return 'playing'
                        else:
                            return 'upgrade'
                            
            if hasattr(self, 'const_action_buttons') and self.const_action_buttons:
                for btn, action in self.const_action_buttons.items():
                    if event.ui_element == btn:
                        return action
                            
        return None

    def render_upgrade(self, game, selected, mouse_pos):
        self.render_game(game, mouse_pos, flip=False, draw_gui=False)
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((5, 10, 18, 205))
        self.screen.blit(overlay, (0, 0))
        
        if pygame_gui is None or not getattr(self, "components", None) or not self.components.available:
            return []
            
        if not hasattr(self, '_last_upgrade_selected') or not hasattr(self, '_last_upgrade_player_index'):
            self._last_upgrade_selected = -1
            self._last_upgrade_player_index = -1
            
        if not hasattr(self, 'upgrade_window'):
            self.upgrade_window = None
            
        if (not self.upgrade_window or 
            not self.upgrade_window.alive() or 
            self._last_upgrade_selected != selected or 
            self._last_upgrade_player_index != game.level_up_player_index):
            
            if self.upgrade_window:
                self.upgrade_window.kill()
                
            self._create_upgrade_window(game, selected)
            self._last_upgrade_selected = selected
            self._last_upgrade_player_index = game.level_up_player_index
            
        self.draw_gui_layer()
        if game.multiplayer:
            self.draw_player_window_accent(self.upgrade_window, game.level_up_player_index)
            
        return []

    def _create_upgrade_window(self, game, selected):
        self.upgrade_buttons = {}
        
        player_index = game.level_up_player_index
        player = game.get_player(player_index)
        title_prefix = f"J{player_index + 1} - " if game.multiplayer else ""
        self.upgrade_window = self.components.window(
            f"{title_prefix}NOVO NIVEL",
            (820, 580),
            "#shop_window",
            y=80,
            player_index=player_index if game.multiplayer else None,
            close_button=False,
        )
        if self.upgrade_window is None:
            return
        
        is_major = game.upgrade_is_major
        title = "MELHORIA GRANDE" if is_major else "NOVO NIVEL"
        subtitle = "Escolha um poder permanente raro!" if is_major else "Escolha um upgrade permanente para continuar"
        if game.multiplayer:
            subtitle = f"Turno do Jogador {player_index + 1} - " + subtitle
            
        UILabel(
            relative_rect=pygame.Rect((10, 8), (770, 40)),
            text=title,
            manager=self.gui_manager,
            container=self.upgrade_window,
            object_id=ObjectID(class_id="@title_text")
        )
        UILabel(
            relative_rect=pygame.Rect((10, 48), (770, 28)),
            text=subtitle,
            manager=self.gui_manager,
            container=self.upgrade_window
        )
        
        y = 95
        for index, key in enumerate(game.upgrade_choices):
            data = UPGRADES.get(key)
            if not data:
                data = OMNI_UPGRADES.get(key)
            if not data:
                data = CHARACTERS[player.char_class]["passives"].get(key)
            if not data: continue
            
            is_selected = (index == selected)
            
            panel_oid = ObjectID(
                class_id="@selected_upgrade_panel" if is_selected else "@upgrade_panel",
                object_id=f"#upgrade_{index}",
            )
            panel = UIPanel(
                relative_rect=pygame.Rect((20, y), (740, 100)),
                manager=self.gui_manager,
                container=self.upgrade_window,
                object_id=panel_oid
            )
            
            indicator = "> " if is_selected else f"  [{index + 1}] "
            label_text = f"{indicator}{data['title']}"
            UILabel(
                relative_rect=pygame.Rect((10, 8), (720, 30)),
                text=label_text,
                manager=self.gui_manager,
                container=panel,
                object_id=ObjectID(
                    class_id="@selected_upgrade_title" if is_selected else "@upgrade_title"
                )
            )
            UILabel(
                relative_rect=pygame.Rect((10, 44), (720, 50)),
                text=data.get("description", "")[:120],
                manager=self.gui_manager,
                container=panel
            )
            
            btn = UIButton(
                relative_rect=pygame.Rect((0, 0), (740, 100)),
                text="",
                manager=self.gui_manager,
                container=panel,
                object_id=ObjectID(
                    class_id="@selected_upgrade_btn" if is_selected else "@upgrade_btn",
                    object_id=f"#upgrade_btn_{index}"
                )
            )
            self.upgrade_buttons[key] = btn
            y += 116

    def render_skills(self, game, selected, mouse_pos):
        self.render_game(game, mouse_pos, flip=False, draw_gui=False)
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((5, 10, 18, 224))
        self.screen.blit(overlay, (0, 0))
        
        if pygame_gui is None or not getattr(self, "components", None) or not self.components.available:
            return []
            
        if not hasattr(self, '_last_skills_selected') or not hasattr(self, '_last_skills_player_index'):
            self._last_skills_selected = -1
            self._last_skills_player_index = -1
            self._last_skills_signature = None
            
        player = game.get_player(game.menu_player_index)
        inv = game.get_inventory(game.menu_player_index)
        signature = (inv.points, tuple(player.passives.items()))
        
        if (not self.skills_window or 
            not self.skills_window.alive() or 
            self._last_skills_selected != selected or 
            self._last_skills_player_index != game.menu_player_index or 
            self._last_skills_signature != signature):
            
            if self.skills_window:
                self.skills_window.kill()
                
            self._create_skills_window(game, selected)
            self._last_skills_selected = selected
            self._last_skills_player_index = game.menu_player_index
            self._last_skills_signature = signature
            
        self.draw_gui_layer()
        if game.multiplayer:
            self.draw_player_window_accent(self.skills_window, game.menu_player_index)
            
        return []

    def _create_skills_window(self, game, selected):
        self.skills_buttons = {}
        c = self.components
        
        player = game.get_player(game.menu_player_index)
        inv = game.get_inventory(game.menu_player_index)
        
        title_prefix = f"J{game.menu_player_index + 1} - " if game.multiplayer else ""
        self.skills_window = c.window(
            f"{title_prefix}HABILIDADES E PASSIVAS",
            (900, 600),
            "#shop_window",
            y=80,
            player_index=game.menu_player_index if game.multiplayer else None
        )
        if self.skills_window is None:
            return
            
        data = CHARACTERS[player.char_class]['passives']
        keys = list(player.passives.keys())
        
        if keys:
            selected = max(0, min(selected, len(keys) - 1))
            selected_key = keys[selected]
        else:
            selected = 0
            selected_key = None
            
        switch_hint = " | Y/P troca jogador" if game.multiplayer else ""
        subtitle_text = f"Jogador {game.menu_player_index + 1} | Pontos: {inv.points} {switch_hint}"
        
        c.label(
            pygame.Rect((20, 10), (500, 30)),
            subtitle_text,
            container=self.skills_window
        )
        
        if game.multiplayer:
            other = 2 if game.menu_player_index == 0 else 1
            self.skills_toggle_player_btn = c.button(
                pygame.Rect((650, 10), (200, 30)),
                f"Ver Jogador {other}",
                container=self.skills_window,
                intent='secondary'
            )
        else:
            self.skills_toggle_player_btn = None
            
        self.skills_list_panel = c.scroll(
            pygame.Rect((20, 50), (450, 420)),
            container=self.skills_window
        )
        
        y = 10
        for index, key in enumerate(keys):
            skill = data[key]
            level = player.passives[key]
            category = skill.get('category', 'Kit')
            state = 'ATIVA' if level > 0 else 'BLOQ.'
            btn_text = f"[{state}] NV {level}/10 - {skill['title'][:20]}"
            is_selected = (index == selected)
            
            btn = c.button(
                pygame.Rect((10, y), (410, 40)),
                btn_text,
                container=self.skills_list_panel,
                intent='selected' if is_selected else 'secondary'
            )
            self.skills_buttons[index] = btn
            y += 50
            
        self.skills_list_panel.set_scrollable_area_dimensions((430, y))
        
        self._scroll_container_to_item(self.skills_list_panel, 10 + selected * 50, 40, 420, y)
                
        # Details Panel
        self.skills_detail_panel = c.panel(
            pygame.Rect((490, 50), (390, 420)),
            container=self.skills_window
        )
        
        if selected_key:
            skill = data[selected_key]
            level = player.passives[selected_key]
            category = skill.get('category', 'Kit')
            cost = game.skill_upgrade_cost(selected_key)
            altar_upgrade = getattr(game, "active_altar", None) is not None and game.active_altar.kind == "skill_altar"
            
            c.label(
                pygame.Rect((10, 10), (360, 20)),
                category.upper(),
                container=self.skills_detail_panel
            )
            c.text_box(
                pygame.Rect((10, 40), (360, 250)),
                f"<b>{skill['title']}</b><br><br>{skill['description']}",
                container=self.skills_detail_panel
            )
            
            cost_text = f"Custo: {cost} pontos" if level < 10 else "Nível Máximo"
            c.label(
                pygame.Rect((10, 300), (360, 30)),
                cost_text,
                container=self.skills_detail_panel
            )
            
            self.skills_upgrade_btn = c.button(
                pygame.Rect((10, 340), (360, 50)),
                'Upar via Altar' if altar_upgrade else 'Upgrade via Altar',
                container=self.skills_detail_panel,
                intent='primary' if altar_upgrade else 'muted'
            )
            if not altar_upgrade or level >= 10 or inv.points < cost:
                self.skills_upgrade_btn.disable()
        else:
            self.skills_upgrade_btn = None
            
        self.skills_back_btn = c.button(
            pygame.Rect((350, 480), (200, 40)),
            'Voltar',
            container=self.skills_window,
            intent='muted'
        )
    def render_constructions(self, game, selected, mouse_pos):
        self.render_game(game, mouse_pos, flip=False, draw_gui=False)
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((5, 10, 18, 222))
        self.screen.blit(overlay, (0, 0))

        if pygame_gui is None or not getattr(self, "components", None) or not self.components.available:
            return self._render_constructions_legacy(game, selected, mouse_pos)

        c = self.components
        entries = self.construction_catalog()
        selected = max(0, min(selected, len(entries) - 1))

        inv = game.get_inventory(game.menu_player_index)
        relic_count = sum(1 for it in inv.items.values() if it.is_relic)
        selected_entry = entries[selected]
        is_relic_entry = selected_entry["tier"] == 3

        signature = (selected, relic_count, inv.points)
        if not hasattr(self, 'constructions_window') or not self.constructions_window or not self.constructions_window.alive() or getattr(self, '_last_const_signature', None) != signature:
            if hasattr(self, 'constructions_window') and self.constructions_window:
                self.constructions_window.kill()

            self.constructions_window = c.window(
                "CONSTRUCOES",
                (940, 600),
                "#constructions_window",
                y=58,
                close_button=False
            )

            c.label(pygame.Rect((20, 12), (880, 26)), "Arvore de itens, fusoes e reliquias", container=self.constructions_window)

            scroll_panel = c.scroll(pygame.Rect((20, 52), (390, 448)), container=self.constructions_window)
            detail_panel = c.panel(pygame.Rect((430, 52), (490, 448)), container=self.constructions_window)

            self.const_action_buttons = {}

            # Preenche a lista da esquerda
            inner_y = 10
            index = 0
            selected_item_top = 10
            for tier, label in ((1, "TIER 1 - BASE"), (2, "TIER 2 - HIBRIDOS"), (3, "TIER 3 - RELIQUIAS")):
                c.label(pygame.Rect((10, inner_y), (340, 22)), label, container=scroll_panel)
                inner_y += 32
                for entry in [e for e in entries if e["tier"] == tier]:
                    is_selected = index == selected
                    if is_selected:
                        selected_item_top = inner_y
                    btn = c.button(
                        pygame.Rect((10, inner_y), (340, 32)),
                        self._catalog_label(entry["item"])[:35],
                        container=scroll_panel,
                        intent="selected" if is_selected else "secondary"
                    )
                    self.const_action_buttons[btn] = f"construction_select:{index}"
                    inner_y += 38
                    index += 1
                inner_y += 10

            scroll_panel.set_scrollable_area_dimensions((360, inner_y))
            self._scroll_container_to_item(scroll_panel, selected_item_top, 32, 448, inner_y)

            # Preenche os detalhes da direita via surface customizada
            selected_item = entries[selected]["item"]
            detail_surf = pygame.Surface((490, 448), pygame.SRCALPHA)
            old_screen = self.screen
            self.screen = detail_surf

            # Desenha fundo para clarear
            pygame.draw.rect(self.screen, (13, 22, 36, 150), detail_surf.get_rect(), border_radius=6)
            self._draw_construction_detail(game, selected_item, pygame.Rect(0, 0, 490, 448))

            self.screen = old_screen

            c.image(pygame.Rect((0, 0), (490, 448)), detail_surf, container=detail_panel)

            # Botao de forja para reliquias (Tier 3)
            if is_relic_entry:
                relic_source_key = selected_entry["key"].replace("relic:", "")
                forge_unlocked = relic_count >= 3
                has_points = inv.points >= 50
                if forge_unlocked and has_points:
                    forge_label = "Forjar Reliquia (50 pts)"
                    forge_intent = "primary"
                elif forge_unlocked:
                    forge_label = "Pontos insuficientes (50 pts)"
                    forge_intent = "muted"
                else:
                    forge_label = f"Bloqueado: Requer 3 Reliquias ({relic_count}/3)"
                    forge_intent = "muted"
                btn_forge = c.button(
                    pygame.Rect((130, 518), (340, 40)),
                    forge_label,
                    container=self.constructions_window,
                    intent=forge_intent
                )
                if forge_unlocked and has_points:
                    self.const_action_buttons[btn_forge] = f"constructions_buy_relic:{relic_source_key}"

            btn_back = c.button(
                pygame.Rect((370, 518), (200, 40)),
                "Voltar ao Jogo",
                container=self.constructions_window,
                intent="muted"
            )
            self.const_action_buttons[btn_back] = "constructions_back"

            self._last_const_signature = signature

        self.draw_gui_layer()
        return []



    def _skill_category_color(self, category):
        if category == "Distância":
            return hex_color(COLORS["projectile"])
        if category == "Corpo a corpo":
            return hex_color(COLORS["sword"])
        if category == "Ambas":
            return hex_color(COLORS["xp"])
        if category == "Especial":
            return hex_color(COLORS["upgrade"])
        return hex_color(COLORS["special"])

    def construction_catalog(self):
        entries = []
        for key in BASE_ITEM_KEYS:
            entries.append({
                "tier": 1,
                "key": key,
                "item": InventoryItem(key=key),
            })

        for first, second in combinations_with_replacement(BASE_ITEM_KEYS, 2):
            sources = tuple(sorted((first, second)))
            entries.append({
                "tier": 2,
                "key": "hybrid:" + "+".join(sources),
                "item": InventoryItem(key="hybrid:" + "+".join(sources), hybrid_sources=sources),
            })

        for source_key in RELIC_DEFINITIONS:
            sources = tuple(source_key.split("+"))
            entries.append({
                "tier": 3,
                "key": "relic:" + source_key,
                "item": InventoryItem(key="relic:" + source_key, hybrid_sources=sources),
            })
        return entries

    def _render_constructions_legacy(self, game, selected, mouse_pos):
        self.render_game(game, mouse_pos, flip=False)
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((5, 10, 18, 222))
        self.screen.blit(overlay, (0, 0))

        entries = self.construction_catalog()
        selected = max(0, min(selected, len(entries) - 1))
        selected_entry = entries[selected]
        selected_item = selected_entry["item"]
        buttons = []

        panel = pygame.Rect(58, 48, SCREEN_WIDTH - 116, SCREEN_HEIGHT - 96)
        pygame.draw.rect(self.screen, (8, 14, 25), panel, border_radius=8)
        pygame.draw.rect(self.screen, (179, 147, 74), panel, width=2, border_radius=8)
        pygame.draw.line(self.screen, (64, 52, 34), (panel.left + 22, panel.top + 52), (panel.right - 22, panel.top + 52), 1)

        self.font_title.render_to(self.screen, (panel.x + 28, panel.y + 16), "CONSTRUCOES", hex_color(COLORS["text"]))
        subtitle_text = "Itens separados por tier, com arvore de fusao e resultado final."
        self.font_tiny.render_to(self.screen, (panel.x + 236, panel.y + 26), subtitle_text, hex_color(COLORS["muted"]))

        list_rect = pygame.Rect(panel.x + 26, panel.y + 76, 398, panel.h - 142)
        detail_rect = pygame.Rect(list_rect.right + 24, list_rect.y, panel.right - list_rect.right - 50, list_rect.h)
        pygame.draw.rect(self.screen, (13, 22, 36), list_rect, border_radius=6)
        pygame.draw.rect(self.screen, (39, 52, 73), list_rect, width=1, border_radius=6)
        pygame.draw.rect(self.screen, (11, 19, 31), detail_rect, border_radius=6)
        pygame.draw.rect(self.screen, (72, 86, 112), detail_rect, width=1, border_radius=6)

        y = list_rect.y + 12
        index = 0
        for tier, label in ((1, "TIER 1 - BASE"), (2, "TIER 2 - HIBRIDOS"), (3, "TIER 3 - RELIQUIAS")):
            header_color = self._tier_color(tier)
            self.font_tiny.render_to(self.screen, (list_rect.x + 14, y), label, header_color)
            y += 19
            for entry in [entry for entry in entries if entry["tier"] == tier]:
                rect = pygame.Rect(list_rect.x + 12, y, list_rect.w - 24, 18)
                hover = rect.collidepoint(mouse_pos)
                active = index == selected
                bg = (31, 44, 64) if active else (17, 28, 44)
                if hover:
                    bg = (37, 58, 78)
                pygame.draw.rect(self.screen, bg, rect, border_radius=4)
                if active:
                    pygame.draw.rect(self.screen, header_color, rect, width=1, border_radius=4)

                icon_rect = pygame.Rect(rect.x + 5, rect.y + 3, 12, 12)
                self._draw_item_icon(entry["item"], icon_rect, game, show_level=False)
                name = self._catalog_label(entry["item"])
                color = hex_color(COLORS["text"] if active or hover else COLORS["muted"])
                self.font_tiny.render_to(self.screen, (rect.x + 24, rect.y + 2), name[:45], color)
                buttons.append((f"construction_select:{index}", rect))
                y += 19
                index += 1
            y += 4

        self._draw_construction_detail(game, selected_item, detail_rect)

        # Botao de forja para reliquias (Tier 3)
        if selected_entry["tier"] == 3:
            relic_source_key = selected_entry["key"].replace("relic:", "")
            inv = game.get_inventory(game.menu_player_index)
            relic_count = sum(1 for it in inv.items.values() if it.is_relic)
            forge_unlocked = relic_count >= 3
            has_points = inv.points >= 50
            if forge_unlocked and has_points:
                forge_label = "Forjar Reliquia (50 pts)"
                forge_action = f"constructions_buy_relic:{relic_source_key}"
                forge_color = COLORS["xp"]
            elif forge_unlocked:
                forge_label = "Pontos insuficientes (50 pts)"
                forge_action = None
                forge_color = COLORS["muted_2"]
            else:
                forge_label = f"Bloqueado: Requer 3 Reliquias ({relic_count}/3)"
                forge_action = None
                forge_color = COLORS["muted_2"]
            forge_btn_rect = pygame.Rect(panel.centerx - 240, panel.bottom - 52, 260, 38)
            forge_btn = self._button(forge_btn_rect.x, forge_btn_rect.y, forge_btn_rect.w, forge_btn_rect.h, forge_label, forge_action or "noop", mouse_pos, forge_color)
            if forge_action:
                buttons.append(forge_btn)

        buttons.append(self._button(panel.centerx + 30, panel.bottom - 52, 220, 38, "Voltar", "constructions_back", mouse_pos, COLORS["muted_2"]))
        # pygame.display.flip()
        return buttons

    def _draw_construction_detail(self, game, item, rect):
        rank_label, rank_color = self._rank_title(item)
        self.font_tiny.render_to(self.screen, (rect.x + 22, rect.y + 18), rank_label, rank_color)

        y = rect.y + 42
        for line in self._wrap_text(item_display_name(item), 38)[:3]:
            self.font_title.render_to(self.screen, (rect.x + 22, y), line, hex_color(COLORS["text"]))
            y += 30

        y += 4
        for line in self._wrap_text(item_short_description(item), 58)[:3]:
            self.font_small.render_to(self.screen, (rect.x + 24, y), line, hex_color(COLORS["muted"]))
            y += 19

        tree_rect = pygame.Rect(rect.x + 20, rect.y + 172, rect.w - 40, rect.h - 194)
        self._draw_build_tree(game, item, tree_rect)

    def _draw_build_tree(self, game, item, rect):
        pygame.draw.rect(self.screen, (8, 14, 24), rect, border_radius=6)
        pygame.draw.rect(self.screen, (39, 52, 73), rect, width=1, border_radius=6)
        self.font_tiny.render_to(self.screen, (rect.x + 12, rect.y + 10), "ARVORE DE CONSTRUCAO", (179, 147, 74))

        if item.rank == 1:
            node = pygame.Rect(rect.centerx - 96, rect.y + 72, 192, 112)
            self._draw_tree_node(item, node, game, selected=True, show_level=False)
            for index, line in enumerate(self._wrap_text("Item base encontrado em caixas especiais e recompensas.", 56)[:2]):
                s_rect = self.font_tiny.get_rect(line)
                self.font_tiny.render_to(self.screen, (rect.centerx - s_rect.width // 2, node.bottom + 20 + index * 16), line, hex_color(COLORS["muted"]))
            return

        if item.rank == 2:
            top = pygame.Rect(rect.centerx - 106, rect.y + 42, 212, 90)
            left = pygame.Rect(rect.x + 54, rect.bottom - 104, 154, 82)
            right = pygame.Rect(rect.right - 208, rect.bottom - 104, 154, 82)
            self._draw_tree_node(item, top, game, selected=True, show_level=False)
            sources = list(item.hybrid_sources)
            self._draw_tree_edges((left.centerx, left.y - 10), (top.centerx, top.bottom + 8), (right.centerx, right.y - 10))
            self._draw_tree_node(InventoryItem(key=sources[0]), left, game, show_level=False)
            self._draw_tree_node(InventoryItem(key=sources[1]), right, game, show_level=False)
            return

        sources = list(item.hybrid_sources)
        first_pair = tuple(sources[:2])
        second_pair = tuple(sources[2:])
        top = pygame.Rect(rect.centerx - 112, rect.y + 36, 224, 78)
        left_hybrid = pygame.Rect(rect.x + 52, rect.y + 150, 164, 76)
        right_hybrid = pygame.Rect(rect.right - 216, rect.y + 150, 164, 76)
        self._draw_tree_node(item, top, game, selected=True, show_level=False)
        self._draw_tree_edges((left_hybrid.centerx, left_hybrid.y - 8), (top.centerx, top.bottom + 8), (right_hybrid.centerx, right_hybrid.y - 8))

        left_item = self._hybrid_preview_item(first_pair)
        right_item = self._hybrid_preview_item(second_pair)
        self._draw_tree_node(left_item, left_hybrid, game, show_level=False)
        self._draw_tree_node(right_item, right_hybrid, game, show_level=False)

        base_y = rect.bottom - 76
        base_w = 96
        gap = 16
        start_x = rect.centerx - (base_w * 4 + gap * 3) // 2
        base_rects = []
        for index, source_key in enumerate(first_pair + second_pair):
            base_rects.append(pygame.Rect(start_x + index * (base_w + gap), base_y, base_w, 62))
            self._draw_tree_node(InventoryItem(key=source_key), base_rects[-1], game, show_level=False)

        for source_rect in base_rects[:2]:
            pygame.draw.line(self.screen, (179, 147, 74), source_rect.midtop, left_hybrid.midbottom, 1)
        for source_rect in base_rects[2:]:
            pygame.draw.line(self.screen, (179, 147, 74), source_rect.midtop, right_hybrid.midbottom, 1)

    def _draw_tree_edges(self, left_point, top_point, right_point):
        pygame.draw.line(self.screen, (179, 147, 74), top_point, left_point, 2)
        pygame.draw.line(self.screen, (179, 147, 74), top_point, right_point, 2)
        pygame.draw.circle(self.screen, (179, 147, 74), top_point, 3)

    def _draw_tree_node(self, item, rect, game, selected=False, show_level=False):
        rank_label, rank_color = self._rank_title(item)
        bg = (20, 31, 47) if selected else (13, 22, 36)
        pygame.draw.rect(self.screen, bg, rect, border_radius=6)
        pygame.draw.rect(self.screen, rank_color, rect, width=2 if selected else 1, border_radius=6)

        icon_size = max(18, min(38, rect.w - 16, rect.h - 32))
        icon_rect = pygame.Rect(rect.centerx - icon_size // 2, rect.y + 7, icon_size, icon_size)
        self._draw_item_icon(item, icon_rect, game, show_level=show_level)

        label = item_display_name(item) if rect.w >= 150 else self._catalog_label(item)
        max_chars = max(10, rect.w // 8)
        lines = self._wrap_text(label, max_chars)[:2]
        y = icon_rect.bottom + 4
        for line in lines:
            s_rect = self.font_tiny.get_rect(line)
            self.font_tiny.render_to(self.screen, (rect.centerx - s_rect.width // 2, y), line, hex_color(COLORS["text"]))
            y += 14

        if rect.h >= 84:
            self.font_tiny.render_to(self.screen, (rect.x + 6, rect.bottom - 16), rank_label.split(" - ")[0], rank_color)

    def _catalog_label(self, item):
        if item.is_relic:
            relic_key = item.key[len("relic:"):]
            return RELIC_DEFINITIONS.get(relic_key, {}).get("short", item_display_name(item))
        if item.is_hybrid:
            return " + ".join(ITEM_DEFINITIONS[key]["short"] for key in item.hybrid_sources)
        return item_display_name(item)

