import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame
import pygame.freetype
from pygame.math import Vector2

if __package__:
    from .config.config_loader import load_settings
    from .config.runtime import logger
    from .data.constants import *
    from .data.items import BASE_ITEM_KEYS
    from .data.encyclopedia import ENCYCLOPEDIA_CATEGORIES
    from .core.records import add_record, delete_record, qualifies, total_score
    from .core.meta_progress import CHARACTER_UPGRADES, character_upgrades, is_character_unlocked, purchase_upgrade_level, save_active_upgrade_levels, unlock_character
    from .core.game_logic import GameLogic
    from .presentation.bootstrap import attach_virtual_screen, init_pygame_runtime
    from .presentation.altar_routing import handle_altar_menu_transition
    from .presentation.runtime_loop import present_virtual_screen, scaled_event_pos, scaled_mouse_pos, update_aim_state
    from .presentation.state_rendering import render_state
else:
    from Sobrevivencia.config.config_loader import load_settings
    from Sobrevivencia.config.runtime import logger
    from Sobrevivencia.data.constants import *
    from Sobrevivencia.data.items import BASE_ITEM_KEYS
    from Sobrevivencia.data.encyclopedia import ENCYCLOPEDIA_CATEGORIES
    from Sobrevivencia.core.records import add_record, delete_record, qualifies, total_score
    from Sobrevivencia.core.meta_progress import CHARACTER_UPGRADES, character_upgrades, is_character_unlocked, purchase_upgrade_level, save_active_upgrade_levels, unlock_character
    from Sobrevivencia.core.game_logic import GameLogic
    from Sobrevivencia.presentation.bootstrap import attach_virtual_screen, init_pygame_runtime
    from Sobrevivencia.presentation.altar_routing import handle_altar_menu_transition
    from Sobrevivencia.presentation.runtime_loop import present_virtual_screen, scaled_event_pos, scaled_mouse_pos, update_aim_state
    from Sobrevivencia.presentation.state_rendering import render_state


if __package__:
    from .input.input_manager import InputManager
    from .controllers.menu_controller import MenuController
    from .presentation.menu_manager import MenuManager

else:
    from Sobrevivencia.input.input_manager import InputManager
    from Sobrevivencia.controllers.menu_controller import MenuController
    from Sobrevivencia.presentation.menu_manager import MenuManager


class SobrevivenciaGame(InputManager, MenuController):
    def run(self):
        settings = load_settings()
        screen, fullscreen, clock, ui, menu_manager = init_pygame_runtime(settings, self._set_display_mode)

        # Menu Callbacks
        def on_start_click():
            nonlocal state, character_selected, character_selected_2, character_select_player, multiplayer_selected, character_cancel_state
            state = "mode_select" if self._joystick_count() else "character_select"
            character_selected = 0
            character_selected_2 = 0
            character_select_player = 0
            multiplayer_selected = False
            character_cancel_state = "start"

        def on_commands_click():
            nonlocal state, commands_return_state
            commands_return_state = "start"
            state = "commands"

        def on_encyclopedia_click():
            nonlocal state, encyclopedia_return_state, encyclopedia_selected
            encyclopedia_return_state = "start"
            encyclopedia_selected = 0
            state = "encyclopedia"

        def on_records_click():
            nonlocal state
            state = "records"

        def on_coin_shop_click():
            nonlocal state
            state = "coin_shop"

        def on_settings_click():
            nonlocal state, settings_return_state, capture_binding
            settings_return_state = "start"
            state = "settings"
            capture_binding = None

        def on_quit_click():
            nonlocal running
            running = False

        menu_manager.create_start_menu(on_start_click, on_commands_click, on_settings_click, on_quit_click, on_encyclopedia_click, on_records_click, on_coin_shop_click)

        def on_resume_click():
            nonlocal state
            state = "playing"

        def on_inventory_click():
            nonlocal state, inventory_selected, game
            game.menu_player_index = 0
            state = "inventory"
            inventory_selected = min(inventory_selected, max(0, len(game.get_inventory(0).item_list()) - 1))

        def on_skills_click():
            nonlocal state, skill_selected, game, skills_return_state
            game.menu_player_index = 0
            skills_return_state = "paused"
            state = "skills"
            skill_selected = min(skill_selected, max(0, len(game.get_player(0).passives) - 1))

        def on_pause_encyclopedia_click():
            nonlocal state, encyclopedia_return_state, encyclopedia_selected
            encyclopedia_return_state = "paused"
            encyclopedia_selected = 0
            state = "encyclopedia"

        menu_manager.create_pause_menu(on_resume_click, on_inventory_click, on_skills_click, on_settings_click, on_quit_click, on_pause_encyclopedia_click)

        game = GameLogic()
        controls = self._default_bindings()
        self._event_pressed_bindings = []
        self._event_released_bindings = []
        self._joystick_axis_active = {}
        self._joystick_hat_active = {}
        self._init_joysticks()
        if self._joystick_count():
            self._apply_default_joystick_bindings(controls)

        state = "start"
        return_action = "menu"
        button_rects = []
        start_selected = 0
        pause_selected = 0
        upgrade_selected = 0
        inventory_selected = 0
        construction_selected = 0
        skill_selected = 0
        settings_selected = 0
        settings_slot = 0
        fusion_confirm_selected = 0
        self.point_confirm_action = None
        self.point_confirm_cost = 0
        self.point_confirm_msg = ""
        self.point_confirm_return = ""
        self.point_confirm_selected = 1
        self.point_confirm_quantity = 1
        self.point_confirm_max_quantity = 1
        self.point_confirm_total_cost = 0
        self._point_confirm_action_marker = None
        self.record_name_text = ""
        self.record_details_index = 0
        self.record_delete_index = 0
        record_pending_game_over = False
        game_over_selected = 0
        stat_shop_selected = 0
        coin_shop_selected = 0
        character_unlock_selected = 0
        character_upgrade_selected = 0
        inventory_tab = "items"
        mode_selected = 0
        multiplayer_selected = False
        character_selected = 0
        character_selected_2 = 0
        character_select_player = 0
        character_cancel_state = "start"
        commands_return_state = "start"
        encyclopedia_return_state = "start"
        encyclopedia_selected = 0
        encyclopedia_category = "Todos"
        encyclopedia_query = ""
        skills_return_state = "paused"
        stat_shop_return_state = "paused"
        settings_return_state = "start"
        capture_binding = None
        self.character_unlock_message = ""
        self.character_upgrade_draft = {key: value["active_level"] for key, value in character_upgrades().items()}
        self.character_upgrade_pending_key = ""

        def selected_character_key(player_index=0):
            keys = list(CHARACTERS.keys())
            index = character_selected_2 if player_index == 1 else character_selected
            return keys[index]

        def selected_party_unlocked():
            if not is_character_unlocked(selected_character_key(0)):
                return False
            if multiplayer_selected and not is_character_unlocked(selected_character_key(1)):
                return False
            return True

        def locked_character_message():
            key = selected_character_key(1 if multiplayer_selected and character_select_player == 1 else 0)
            name = CHARACTERS[key]["name"]
            return f"{name} bloqueado. Desbloqueie na Loja de Moedas."

        def refresh_character_upgrade_draft():
            self.character_upgrade_draft = {key: value["active_level"] for key, value in character_upgrades().items()}

        def change_character_upgrade_level(key, delta):
            saved = character_upgrades()
            if key not in saved:
                return
            purchased = saved[key]["purchased_level"]
            current = int(self.character_upgrade_draft.get(key, saved[key]["active_level"]))
            if delta > 0 and current >= purchased:
                self.character_upgrade_pending_key = key
                return "confirm"
            self.character_upgrade_draft[key] = max(0, min(purchased, current + delta))
            return "changed"
        special_holding = {0: False, 1: False}
        special_hold_time = {0: 0.0, 1: 0.0}
        special_hold_triggered = {0: False, 1: False}
        special_combo_checked = {0: False, 1: False}
        combo_holding = {0: False, 1: False}
        combo_hold_time = {0: 0.0, 1: 0.0}
        combo_hold_triggered = {0: False, 1: False}
        joystick_aim_dir = Vector2(1, 0)
        aim_mode = "mouse"
        running = True
        
        attach_virtual_screen(self, ui, menu_manager)
        self.active_device = "keyboard" # "keyboard" ou "joystick"
        self.control_preference = "auto" # "auto", "keyboard", "joystick"

        while running:
            dt = clock.tick(FPS) / 1000.0
            if state == "start" and pygame.time.get_ticks() < 5000:
                # Print once every second for 5 seconds
                if pygame.time.get_ticks() % 1000 < 20:
                    logger.info(f"Loop running... State: {state}")
            
            final_screen = pygame.display.get_surface()
            mouse_pos = scaled_mouse_pos(final_screen, self.virtual_screen)
            joystick_aim_dir, aim_mode, aim_pos, aim_world, p2_aim_screen, p2_aim_world = update_aim_state(
                self, game, ui, mouse_pos, joystick_aim_dir, aim_mode
            )

            ui.sync_menu_windows(state)
            for event in self._poll_events(game):
                self._prepare_input_event(event)
                ui.gui_manager.process_events(event)
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE and state == "records":
                    state = "start"
                    continue
                if state == "inventory":
                    action = ui.handle_inventory_event(event)
                    if action:
                        if action.startswith("inventory_tab:"):
                            inventory_tab = action.split(":", 1)[1]
                            inventory_selected = 0
                        elif action == "toggle_menu_player":
                            game.menu_player_index = 1 - game.menu_player_index
                            inventory_selected = 0
                        elif action.startswith("stamp_select:"):
                            inventory_selected = int(action.split(":", 1)[1])
                            altar_kind = getattr(getattr(game, "active_altar", None), "kind", None)
                            if altar_kind == "black_market_altar":
                                player = game.get_player(game.menu_player_index)
                                reserve_start = len(player.weapon_stamps.get("weapon_1", [])) + len(player.weapon_stamps.get("weapon_2", []))
                                if inventory_selected >= reserve_start:
                                    self._toggle_stamp_sale_mark(game, inventory_selected)
                        elif action.startswith("shop_select:"):
                            inventory_selected = int(action.split(":", 1)[1])
                        elif action.startswith("item_select:"):
                            inventory_selected = int(action.split(":", 1)[1])
                            altar_kind = getattr(getattr(game, "active_altar", None), "kind", None)
                            if altar_kind == "black_market_altar":
                                inv = game.get_inventory(game.menu_player_index)
                                raw_items = inv.item_list()
                                active_items = [item for item in raw_items if inv.is_active(item.slot_key)]
                                if inventory_selected >= len(active_items) and inventory_selected < len(raw_items):
                                    self._toggle_inventory_sale_mark(game, raw_items[inventory_selected].slot_key)
                        elif action == "shop_buy":
                            shop_keys = list(BASE_ITEM_KEYS)
                            if inventory_selected < len(shop_keys):
                                cost = 15
                                if game.get_inventory(game.menu_player_index).points >= cost:
                                    self.point_confirm_action = ("buy_shop_item", shop_keys[inventory_selected])
                                    self.point_confirm_cost = cost
                                    self.point_confirm_msg = f"Deseja gastar {cost} moedas para comprar este item?"
                                    self.point_confirm_return = "inventory"
                                    self.point_confirm_selected = 1
                                    state = "point_confirm"
                                else:
                                    game.message = f"Pontos insuficientes (custa {cost})."
                        elif action == "item_transform":
                            inv = game.get_inventory(game.menu_player_index)
                            raw_items = inv.item_list()
                            active_items = [item for item in raw_items if inv.is_active(item.slot_key)]
                            reserve_items = [item for item in raw_items if not inv.is_active(item.slot_key)]
                            items = active_items + reserve_items
                            if inventory_selected < len(items):
                                item = items[inventory_selected]
                                cost = 15
                                if item.rank == 1 and item.level >= 10 and inv.black_market_unlocked:
                                    if inv.points >= cost:
                                        self.point_confirm_action = ("transform_inventory", item.slot_key)
                                        self.point_confirm_cost = cost
                                        self.point_confirm_msg = "Deseja gastar 15 moedas para tentar a Transformacao (Risco de Degradacao)?"
                                        self.point_confirm_return = "inventory"
                                        self.point_confirm_selected = 1
                                        state = "point_confirm"
                                    else:
                                        game.message = f"Pontos insuficientes (custa {cost})."
                                else:
                                    game.message = "Transformacao bloqueada ou requisitos nao atendidos."
                        else:
                            state, inventory_selected = self._handle_inventory_action(action, state, game, inventory_selected)
                            if state == "fusion_confirm":
                                fusion_confirm_selected = 1
                            elif state == "stamp_fusion_confirm":
                                fusion_confirm_selected = 1
                        continue
                elif state == "stamp_fusion_confirm":
                    action = ui.handle_inventory_event(event)
                    if action:
                        state, inventory_selected = self._handle_stamp_fusion_confirm_action(action, game, inventory_selected)
                        continue
                elif state == "point_confirm":
                    action = ui.handle_inventory_event(event)
                    if action:
                        state = self._handle_point_confirm_choice(action, game)
                        continue
                elif state == "encyclopedia":
                    action = ui.handle_encyclopedia_event(event)
                    if action:
                        if action == "encyclopedia_back":
                            state = encyclopedia_return_state
                        elif action == "encyclopedia_clear_search":
                            encyclopedia_query = ""
                            encyclopedia_selected = 0
                        elif action.startswith("encyclopedia_search:"):
                            encyclopedia_query = action.split(":", 1)[1]
                            encyclopedia_selected = 0
                        elif action.startswith("encyclopedia_category:"):
                            encyclopedia_category = action.split(":", 1)[1]
                            encyclopedia_selected = 0
                        elif action.startswith("encyclopedia_select:"):
                            encyclopedia_selected = int(action.split(":", 1)[1])
                        continue
                elif state in ("stat_shop", "skills", "upgrade"):
                    new_state = ui.handle_shop_menus_event(event, game)
                    if new_state:
                        if state == "skills":
                            if new_state == "skills_toggle_player":
                                game.menu_player_index = 1 - game.menu_player_index
                                skill_selected = 0
                            else:
                                state, skill_selected = self._handle_skill_action(
                                    new_state,
                                    state,
                                    game,
                                    skill_selected,
                                    skills_return_state,
                                )
                        elif state == "stat_shop":
                            state = self._handle_stat_shop_action(new_state, game, stat_shop_return_state)
                        else:
                            state = new_state
                elif state == "paused":
                    action = ui.handle_system_menus_event(event, game)
                    if action:
                        if action == "commands":
                            commands_return_state = "paused"
                            state = "commands"
                        elif action == "encyclopedia":
                            encyclopedia_return_state = "paused"
                            encyclopedia_selected = 0
                            state = "encyclopedia"
                        elif action == "settings":
                            settings_return_state = "paused"
                            state = "settings"
                            capture_binding = None
                        elif action == "skills":
                            skills_return_state = "paused"
                            state = "skills"
                            game.menu_player_index = 0
                            skill_selected = min(skill_selected, max(0, len(game.get_player(0).passives) - 1))
                        elif action == "stat_shop":
                            game.message = "Loja de Status disponivel apenas no Altar de Status."
                        elif action == "change_character":
                            character_selected = self._current_character_index(game)
                            character_selected_2 = self._current_character_index(game, 1)
                            multiplayer_selected = game.multiplayer
                            character_select_player = 0
                            character_cancel_state = "paused"
                            state = "character_select"
                        else:
                            state, running, return_action, pause_selected, upgrade_selected = self._handle_action(
                                action,
                                state,
                                game,
                                running,
                                return_action,
                                pause_selected,
                                upgrade_selected,
                            )
                        continue
                elif state == "start":
                    action = ui.handle_system_menus_event(event, game)
                    if action:
                        if action == "character_select":
                            state = "mode_select" if self._joystick_count() else "character_select"
                            character_selected = 0
                            character_selected_2 = 0
                            character_select_player = 0
                            multiplayer_selected = False
                            character_cancel_state = "start"
                        elif action == "commands":
                            commands_return_state = "start"
                            state = "commands"
                        elif action == "records":
                            state = "records"
                        elif action == "coin_shop":
                            state = "coin_shop"
                        elif action == "encyclopedia":
                            encyclopedia_return_state = "start"
                            encyclopedia_selected = 0
                            state = "encyclopedia"
                        elif action == "settings":
                            settings_return_state = "start"
                            state = "settings"
                            capture_binding = None
                        elif action == "menu":
                            return_action = "menu"
                            running = False
                        elif action == "quit":
                            return_action = "quit"
                            running = False
                        continue
                elif state == "game_over":
                    action = ui.handle_system_menus_event(event, game)
                    if action == "restart":
                        game.restart()
                        record_pending_game_over = False
                        self.record_name_text = ""
                        state = "playing"
                    elif action == "change_character":
                        character_selected = self._current_character_index(game)
                        character_selected_2 = self._current_character_index(game, 1)
                        multiplayer_selected = game.multiplayer
                        character_select_player = 0
                        character_cancel_state = "game_over"
                        state = "character_select"
                    elif action == "menu":
                        running = False
                        return_action = "menu"
                    elif action == "quit":
                        running = False
                        return_action = "quit"
                elif state == "records":
                    action = ui.handle_system_menus_event(event, game)
                    if action == "records_back":
                        state = "start"
                    elif action and action.startswith("record_details:"):
                        self.record_details_index = int(action.split(":", 1)[1])
                        state = "record_details"
                    elif action and action.startswith("record_delete:"):
                        self.record_delete_index = int(action.split(":", 1)[1])
                        state = "record_delete_confirm"
                elif state == "record_details":
                    action = ui.handle_system_menus_event(event, game)
                    if action == "records_back":
                        state = "records"
                    elif action == "record_kills":
                        state = "record_kills"
                elif state == "record_kills":
                    action = ui.handle_system_menus_event(event, game)
                    if action == "records_back":
                        state = "record_details"
                elif state == "record_delete_confirm":
                    action = ui.handle_system_menus_event(event, game)
                    if action == "record_delete_yes":
                        delete_record(self.record_delete_index)
                        state = "records"
                    elif action in ("record_delete_no", "records_back"):
                        state = "records"
                elif state == "coin_shop":
                    action = ui.handle_system_menus_event(event, game)
                    if action == "coin_shop_back":
                        state = "start"
                    elif action == "coin_shop_characters":
                        character_unlock_selected = 0
                        state = "character_unlock"
                    elif action == "coin_shop_upgrades":
                        refresh_character_upgrade_draft()
                        character_upgrade_selected = 0
                        state = "character_upgrades"
                elif state == "character_select":
                    action = ui.handle_system_menus_event(event, game)
                    if action == "prev_char":
                        if multiplayer_selected and character_select_player == 1:
                            character_selected_2 = (character_selected_2 - 1) % len(CHARACTERS)
                        else:
                            character_selected = (character_selected - 1) % len(CHARACTERS)
                    elif action == "next_char":
                        if multiplayer_selected and character_select_player == 1:
                            character_selected_2 = (character_selected_2 + 1) % len(CHARACTERS)
                        else:
                            character_selected = (character_selected + 1) % len(CHARACTERS)
                    elif action == "confirm":
                        if not is_character_unlocked(selected_character_key(0)):
                            game.message = locked_character_message()
                        elif multiplayer_selected and character_select_player == 0:
                            character_select_player = 1
                        elif not selected_party_unlocked():
                            game.message = locked_character_message()
                        else:
                            char_class = list(CHARACTERS.keys())[character_selected]
                            char_class_2 = list(CHARACTERS.keys())[character_selected_2]
                            game = GameLogic(char_class, char_class_2, multiplayer_selected)
                            record_pending_game_over = False
                            self.record_name_text = ""
                            state = "playing"

                if event.type == pygame.QUIT:
                    return_action = "menu"
                    running = False
                    break

                if event.type == pygame.JOYDEVICEADDED:
                    self._add_joystick(event.device_index)
                    self._apply_default_joystick_bindings(controls)
                    aim_mode = "joystick"
                    game.message = self._joystick_status_message()

                elif event.type == pygame.JOYDEVICEREMOVED:
                    self._remove_joystick(event.instance_id)
                    if not self._joystick_count():
                        aim_mode = "mouse"
                        self.active_device = "keyboard"
                    game.message = self._joystick_status_message()

                # Detecção de Dispositivo Ativo (Apenas se estiver em "auto")
                if self.control_preference == "auto":
                    if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN, pygame.MOUSEMOTION):
                        self.active_device = "keyboard"
                        aim_mode = "mouse"
                    elif event.type in (pygame.JOYBUTTONDOWN, pygame.JOYAXISMOTION, pygame.JOYHATMOTION):
                        self.active_device = "joystick"
                        aim_mode = "joystick"
                else:
                    self.active_device = self.control_preference
                    aim_mode = "joystick" if self.active_device == "joystick" else "mouse"

                # Input Lock Multiplayer no Draft / Level Up
                if game.multiplayer and game.level_up_pending:
                    is_joystick_event = event.type in (pygame.JOYBUTTONDOWN, pygame.JOYAXISMOTION, pygame.JOYHATMOTION)
                    is_keyboard_event = event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN)
                    
                    if game.level_up_player_index == 0: # Turno do P1 (Teclado)
                        if is_joystick_event: continue
                    else: # Turno do P2 (Joystick)
                        if is_keyboard_event: continue
                
                # Trava de Dispositivo Singleplayer (Gameplay)
                if not game.multiplayer and state == "playing":
                    if self.active_device == "joystick" and event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                        continue
                    if self.active_device == "keyboard" and event.type in (pygame.JOYBUTTONDOWN, pygame.JOYAXISMOTION):
                        continue

                if state == "settings" and capture_binding:
                    binding = self._binding_from_event(event)
                    if binding is not None:
                        action_key, slot = capture_binding
                        controls[action_key][slot] = binding
                        capture_binding = None
                    continue

                elif event.type == pygame.MOUSEMOTION:
                    aim_mode = "mouse"

                elif event.type == pygame.MOUSEWHEEL:
                    aim_mode = "mouse"
                    if state == "skills":
                        keys = list(game.get_player(game.menu_player_index).passives.keys())
                        if keys:
                            if event.y > 0:
                                skill_selected = max(0, skill_selected - 1)
                            elif event.y < 0:
                                skill_selected = min(len(keys) - 1, skill_selected + 1)

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    aim_mode = "mouse"
                    if state == "settings" and capture_binding:
                        action_key, slot = capture_binding
                        controls[action_key][slot] = self._binding_from_event(event)
                        capture_binding = None
                        continue

                    clicked_button = False
                    if state == "skills" and event.button in (4, 5):
                        keys = list(game.get_player(game.menu_player_index).passives.keys())
                        if keys:
                            if event.button == 4:
                                skill_selected = max(0, skill_selected - 1)
                            else:
                                skill_selected = min(len(keys) - 1, skill_selected + 1)
                        continue

                    if event.button == 1:
                        final_screen = pygame.display.get_surface()
                        ev_pos = scaled_event_pos(event.pos, final_screen, self.virtual_screen)
                        for action, rect in button_rects:
                            if rect.collidepoint(ev_pos):
                                clicked_button = True
                                if state == "settings":
                                    if action == "settings_back":
                                        state = settings_return_state
                                        capture_binding = None
                                    elif action == "settings_reset":
                                        controls = self._default_bindings()
                                        if self._joystick_count():
                                            self._apply_default_joystick_bindings(controls)
                                        capture_binding = None
                                    elif action == "settings_fullscreen":
                                        fullscreen = not fullscreen
                                        screen, fullscreen = self._set_display_mode(fullscreen, ui)
                                    elif action == "settings_control":
                                        prefs = ["auto", "keyboard", "joystick"]
                                        curr = prefs.index(self.control_preference)
                                        self.control_preference = prefs[(curr + 1) % len(prefs)]
                                        if self.control_preference != "auto":
                                            self.active_device = self.control_preference
                                            aim_mode = "joystick" if self.active_device == "joystick" else "mouse"
                                    elif action.startswith("bind:"):
                                        _, action_key, slot = action.split(":", 2)
                                        settings_selected = self._control_index(action_key)
                                        settings_slot = int(slot)
                                        capture_binding = (action_key, settings_slot)
                                    break
                                if state == "encyclopedia":
                                    if action == "encyclopedia_back":
                                        state = encyclopedia_return_state
                                    elif action.startswith("encyclopedia_select:"):
                                        encyclopedia_selected = int(action.split(":", 1)[1])
                                    break
                                if state == "progression":
                                    if action == "progression_back":
                                        state = "paused"
                                    break
                                if action == "character_select":
                                    state = "mode_select" if self._joystick_count() else "character_select"
                                    character_selected = 0
                                    character_selected_2 = 0
                                    character_select_player = 0
                                    multiplayer_selected = False
                                    character_cancel_state = "start"
                                    break
                                if action in ("single_player", "multiplayer"):
                                    multiplayer_selected = action == "multiplayer"
                                    state = "character_select"
                                    character_selected = 0
                                    character_selected_2 = 0
                                    character_select_player = 0
                                    character_cancel_state = "mode_select"
                                    break
                                if action == "start_game":
                                    if not is_character_unlocked(selected_character_key(0)):
                                        game.message = locked_character_message()
                                    elif multiplayer_selected and character_select_player == 0:
                                        character_select_player = 1
                                    elif not selected_party_unlocked():
                                        game.message = locked_character_message()
                                    else:
                                        char_class = list(CHARACTERS.keys())[character_selected]
                                        char_class_2 = list(CHARACTERS.keys())[character_selected_2]
                                        game = GameLogic(char_class, char_class_2, multiplayer_selected)
                                        record_pending_game_over = False
                                        self.record_name_text = ""
                                        state = "playing"
                                    break
                                if action == "change_character":
                                    character_selected = self._current_character_index(game)
                                    character_selected_2 = self._current_character_index(game, 1)
                                    character_cancel_state = state
                                    multiplayer_selected = game.multiplayer
                                    character_select_player = 0
                                    state = "character_select"
                                    break
                                if action == "encyclopedia":
                                    encyclopedia_return_state = "paused" if state == "paused" else "start"
                                    encyclopedia_selected = 0
                                    state = "encyclopedia"
                                    break
                                if state == "fusion_confirm":
                                    state, inventory_selected = self._handle_fusion_confirm_action(action, game, inventory_selected)
                                    break
                                if state == "stamp_fusion_confirm":
                                    state, inventory_selected = self._handle_stamp_fusion_confirm_action(action, game, inventory_selected)
                                    break
                                if state == "point_confirm":
                                    state = self._handle_point_confirm_choice(action, game)
                                    break
                                if state == "records":
                                    if action.startswith("record_details:"):
                                        self.record_details_index = int(action.split(":", 1)[1])
                                        state = "record_details"
                                    elif action.startswith("record_delete:"):
                                        self.record_delete_index = int(action.split(":", 1)[1])
                                        state = "record_delete_confirm"
                                    elif action == "records_back":
                                        state = "start"
                                    break
                                if state == "record_details":
                                    if action == "records_back":
                                        state = "records"
                                    elif action == "record_kills":
                                        state = "record_kills"
                                    break
                                if state == "record_kills":
                                    if action == "records_back":
                                        state = "record_details"
                                    break
                                if state == "record_delete_confirm":
                                    if action == "record_delete_yes":
                                        delete_record(self.record_delete_index)
                                        state = "records"
                                    elif action in ("record_delete_no", "records_back"):
                                        state = "records"
                                    break
                                if state == "coin_shop":
                                    if action == "coin_shop_back":
                                        state = "start"
                                    elif action == "coin_shop_characters":
                                        character_unlock_selected = 0
                                        state = "character_unlock"
                                    elif action == "coin_shop_upgrades":
                                        refresh_character_upgrade_draft()
                                        character_upgrade_selected = 0
                                        state = "character_upgrades"
                                    elif action.startswith("coin_shop_"):
                                        game.message = "Loja de moedas: categoria em desenvolvimento."
                                    break
                                if state == "character_upgrades":
                                    if action == "char_upgrades_back":
                                        state = "coin_shop"
                                    elif action == "char_upgrades_save":
                                        save_active_upgrade_levels(self.character_upgrade_draft)
                                        game.message = "Melhorias salvas."
                                        state = "coin_shop"
                                    elif action.startswith("char_upgrade_minus:"):
                                        key = action.split(":", 1)[1]
                                        character_upgrade_selected = list(CHARACTER_UPGRADES.keys()).index(key)
                                        change_character_upgrade_level(key, -1)
                                    elif action.startswith("char_upgrade_plus:"):
                                        key = action.split(":", 1)[1]
                                        character_upgrade_selected = list(CHARACTER_UPGRADES.keys()).index(key)
                                        result = change_character_upgrade_level(key, 1)
                                        if result == "confirm":
                                            state = "character_upgrade_confirm"
                                    break
                                if state == "character_upgrade_confirm":
                                    if action == "char_upgrade_confirm_yes":
                                        ok, msg, _ = purchase_upgrade_level(self.character_upgrade_pending_key)
                                        refresh_character_upgrade_draft()
                                        game.message = msg
                                        state = "character_upgrades"
                                    elif action in ("char_upgrade_confirm_no", "char_upgrades_back"):
                                        state = "character_upgrades"
                                    break
                                if state == "character_unlock":
                                    if action == "character_unlock_back":
                                        state = "coin_shop"
                                    elif action.startswith("character_unlock_select:"):
                                        character_unlock_selected = int(action.split(":", 1)[1])
                                        state = "character_unlock_detail"
                                    break
                                if state == "character_unlock_detail":
                                    if action == "character_unlock_back":
                                        state = "character_unlock"
                                    elif action == "character_unlock_buy":
                                        state = "character_unlock_confirm"
                                    break
                                if state == "character_unlock_confirm":
                                    if action == "character_unlock_confirm_yes":
                                        key = list(CHARACTERS.keys())[character_unlock_selected]
                                        _, msg, _ = unlock_character(key)
                                        game.message = msg
                                        state = "character_unlock_detail"
                                    elif action in ("character_unlock_confirm_no", "character_unlock_back"):
                                        state = "character_unlock_detail"
                                    break
                                if state == "record_name":
                                    if action == "record_save":
                                        add_record(self.record_name_text, game)
                                        self.record_name_text = ""
                                        record_pending_game_over = False
                                        state = "game_over"
                                    elif action == "record_skip":
                                        self.record_name_text = ""
                                        record_pending_game_over = False
                                        state = "game_over"
                                    break
                                if state == "rng_result":
                                    if action == "rng_result_ok":
                                        state = "playing"
                                    break
                                if action == "toggle_menu_player" and state in ("inventory", "skills"):
                                    game.menu_player_index = 1 - game.menu_player_index
                                    inventory_selected = 0
                                    skill_selected = 0
                                    break
                                elif action.startswith("shop_select:"):
                                    inventory_selected = int(action.split(":")[1])
                                    break
                                elif action == "shop_buy":
                                    shop_keys = list(BASE_ITEM_KEYS)
                                    if inventory_selected < len(shop_keys):
                                        cost = 15
                                        if game.get_inventory(game.menu_player_index).points >= cost:
                                            self.point_confirm_action = ("buy_shop_item", shop_keys[inventory_selected])
                                            self.point_confirm_cost = cost
                                            self.point_confirm_msg = f"Deseja gastar {cost} moedas para comprar este item?"
                                            self.point_confirm_return = "inventory"
                                            self.point_confirm_selected = 1
                                            state = "point_confirm"
                                        else:
                                            game.message = f"Pontos insuficientes (custa {cost})."
                                    break
                                elif action == "item_transform":
                                    inv = game.get_inventory(game.menu_player_index)
                                    raw_items = inv.item_list()
                                    active_items = [item for item in raw_items if inv.is_active(item.slot_key)]
                                    reserve_items = [item for item in raw_items if not inv.is_active(item.slot_key)]
                                    items = active_items + reserve_items
                                    if inventory_selected < len(items):
                                        item = items[inventory_selected]
                                        cost = 15
                                        if item.rank == 1 and item.level >= 10 and inv.black_market_unlocked:
                                            if inv.points >= cost:
                                                self.point_confirm_action = ("transform_inventory", item.slot_key)
                                                self.point_confirm_cost = cost
                                                self.point_confirm_msg = "Deseja gastar 15 moedas para tentar a Transformacao (Risco de Degradacao)?"
                                                self.point_confirm_return = "inventory"
                                                self.point_confirm_selected = 1
                                                state = "point_confirm"
                                            else:
                                                game.message = f"Pontos insuficientes (custa {cost})."
                                        else:
                                            game.message = "Transformacao bloqueada ou requisitos nao atendidos."
                                    break
                                if state == "inventory":
                                    state, inventory_selected = self._handle_inventory_action(action, state, game, inventory_selected)
                                    if state == "fusion_confirm":
                                        fusion_confirm_selected = 1
                                    elif state == "stamp_fusion_confirm":
                                        fusion_confirm_selected = 1
                                    break
                                if state == "stat_shop":
                                    state = self._handle_stat_shop_action(action, game, stat_shop_return_state)
                                    break
                                if state == "constructions":
                                    state, construction_selected = self._handle_construction_action(action, construction_selected)
                                    break
                                if state == "skills":
                                    state, skill_selected = self._handle_skill_action(action, state, game, skill_selected, skills_return_state)
                                    break
                                if action == "commands":
                                    commands_return_state = "paused" if state == "paused" else "start"
                                elif action == "encyclopedia":
                                    encyclopedia_return_state = "paused" if state == "paused" else "start"
                                    state = "encyclopedia"
                                    break
                                elif action == "settings":
                                    settings_return_state = "paused" if state == "paused" else "start"
                                    state = "settings"
                                    capture_binding = None
                                    break
                                elif action == "progression":
                                    state = "progression"
                                    break
                                elif action == "skills":
                                    skills_return_state = "paused"
                                elif action == "stat_shop":
                                    stat_shop_return_state = "paused" if state == "paused" else "playing"
                                elif action == "back":
                                    if state == "mode_select":
                                        state = "start"
                                        break
                                    state = commands_return_state
                                    break
                                state, running, return_action, pause_selected, upgrade_selected = self._handle_action(
                                    action,
                                    state,
                                    game,
                                    running,
                                    return_action,
                                    pause_selected,
                                    upgrade_selected,
                                )
                                break

                    if clicked_button:
                        continue

                    if self._action_pressed(event, controls, "fullscreen"):
                        fullscreen = not fullscreen
                        screen, fullscreen = self._set_display_mode(fullscreen, ui)
                        continue

                    if state == "playing":
                        if self._action_pressed(event, controls, "pause"):
                            state = "paused"
                            pause_selected = 0
                        elif self._action_pressed(event, controls, "settings"):
                            settings_return_state = "playing"
                            state = "settings"
                            special_holding[0] = False
                            special_combo_checked[0] = False
                        elif self._action_pressed(event, controls, "toggle_weapon"):
                            game.toggle_mode()
                        elif self._action_pressed(event, controls, "dash"):
                            game.try_dash(aim_world)
                        elif self._action_pressed(event, controls, "special"):
                            special_holding[0] = True
                            special_hold_time[0] = 0.0
                            special_hold_triggered[0] = False
                            special_combo_checked[0] = False
                        elif self._action_pressed(event, controls, "combo_special"):
                            game.try_combo_special(aim_world, 0)
                        elif self._action_pressed(event, controls, "omni_active"):
                            game.try_omni_active()
                        elif self._action_pressed(event, controls, "inventory"):
                            game.menu_player_index = 0
                            state = "inventory"
                            inventory_selected = min(inventory_selected, max(0, len(game.get_inventory(0).item_list()) - 1))
                            special_holding[0] = False
                            special_combo_checked[0] = False
                        elif self._action_pressed(event, controls, "skills"):
                            game.menu_player_index = 0
                            skills_return_state = "playing"
                            state = "skills"
                            skill_selected = min(skill_selected, max(0, len(game.get_player(0).passives) - 1))
                            special_holding[0] = False
                            special_combo_checked[0] = False
                        elif self._action_pressed(event, controls, "stat_shop"):
                            game.message = "Loja de Status disponivel apenas no Altar de Status."
                            special_holding[0] = False
                            special_combo_checked[0] = False

                elif event.type in (pygame.JOYBUTTONDOWN, pygame.JOYAXISMOTION, pygame.JOYHATMOTION):
                    if not self._event_pressed_bindings:
                        continue
                    if self._action_pressed(event, controls, "fullscreen"):
                        fullscreen = not fullscreen
                        screen, fullscreen = self._set_display_mode(fullscreen, ui)
                        continue

                    if state == "start":
                        if self._menu_up_pressed():
                            start_selected = (start_selected - 1) % len(START_OPTIONS)
                        elif self._menu_down_pressed():
                            start_selected = (start_selected + 1) % len(START_OPTIONS)
                        elif self._menu_confirm_pressed():
                            action = START_OPTIONS[start_selected][1]
                            if action == "character_select":
                                state = "mode_select" if self._joystick_count() else "character_select"
                                character_selected = 0
                                character_selected_2 = 0
                                character_select_player = 0
                                multiplayer_selected = False
                                character_cancel_state = "start"
                            elif action == "commands":
                                commands_return_state = "start"
                                state = "commands"
                            elif action == "records":
                                state = "records"
                            elif action == "coin_shop":
                                state = "coin_shop"
                            elif action == "encyclopedia":
                                encyclopedia_return_state = "start"
                                encyclopedia_selected = 0
                                state = "encyclopedia"
                            elif action == "settings":
                                settings_return_state = "start"
                                state = "settings"
                            elif action == "menu":
                                running = False
                                return_action = "menu"
                        elif self._menu_back_pressed():
                            running = False
                            return_action = "menu"
                    elif state == "records":
                        if self._menu_back_pressed() or self._menu_confirm_pressed():
                            state = "start"
                    elif state == "record_details":
                        if self._menu_back_pressed() or self._menu_confirm_pressed():
                            state = "records"
                    elif state == "record_kills":
                        if self._menu_back_pressed() or self._menu_confirm_pressed():
                            state = "record_details"
                    elif state == "record_delete_confirm":
                        if self._menu_confirm_pressed():
                            delete_record(self.record_delete_index)
                            state = "records"
                        elif self._menu_back_pressed():
                            state = "records"
                    elif state == "coin_shop":
                        if self._menu_up_pressed():
                            coin_shop_selected = (coin_shop_selected - 1) % 4
                        elif self._menu_down_pressed():
                            coin_shop_selected = (coin_shop_selected + 1) % 4
                        elif self._menu_confirm_pressed():
                            if coin_shop_selected == 3:
                                state = "start"
                            elif coin_shop_selected == 1:
                                character_unlock_selected = 0
                                state = "character_unlock"
                            elif coin_shop_selected == 2:
                                refresh_character_upgrade_draft()
                                character_upgrade_selected = 0
                                state = "character_upgrades"
                            else:
                                game.message = "Loja de moedas: categoria em desenvolvimento."
                        elif self._menu_back_pressed():
                            state = "start"
                    elif state == "character_upgrades":
                        keys = list(CHARACTER_UPGRADES.keys())
                        if self._menu_up_pressed():
                            character_upgrade_selected = (character_upgrade_selected - 1) % len(keys)
                        elif self._menu_down_pressed():
                            character_upgrade_selected = (character_upgrade_selected + 1) % len(keys)
                        elif self._menu_left_pressed():
                            change_character_upgrade_level(keys[character_upgrade_selected], -1)
                        elif self._menu_right_pressed() or self._menu_confirm_pressed():
                            result = change_character_upgrade_level(keys[character_upgrade_selected], 1)
                            if result == "confirm":
                                state = "character_upgrade_confirm"
                        elif self._menu_back_pressed():
                            save_active_upgrade_levels(self.character_upgrade_draft)
                            game.message = "Melhorias salvas."
                            state = "coin_shop"
                    elif state == "character_upgrade_confirm":
                        if self._menu_confirm_pressed():
                            _, msg, _ = purchase_upgrade_level(self.character_upgrade_pending_key)
                            refresh_character_upgrade_draft()
                            game.message = msg
                            state = "character_upgrades"
                        elif self._menu_back_pressed():
                            state = "character_upgrades"
                    elif state == "character_unlock":
                        if self._menu_left_pressed():
                            character_unlock_selected = max(0, character_unlock_selected - 1)
                        elif self._menu_right_pressed():
                            character_unlock_selected = min(len(CHARACTERS) - 1, character_unlock_selected + 1)
                        elif self._menu_up_pressed():
                            character_unlock_selected = max(0, character_unlock_selected - 2)
                        elif self._menu_down_pressed():
                            character_unlock_selected = min(len(CHARACTERS) - 1, character_unlock_selected + 2)
                        elif self._menu_confirm_pressed():
                            state = "character_unlock_detail"
                        elif self._menu_back_pressed():
                            state = "coin_shop"
                    elif state == "character_unlock_detail":
                        if self._menu_confirm_pressed():
                            key = list(CHARACTERS.keys())[character_unlock_selected]
                            if is_character_unlocked(key):
                                game.message = "Personagem ja desbloqueado."
                            else:
                                state = "character_unlock_confirm"
                        elif self._menu_back_pressed():
                            state = "character_unlock"
                    elif state == "character_unlock_confirm":
                        if self._menu_confirm_pressed():
                            key = list(CHARACTERS.keys())[character_unlock_selected]
                            _, msg, _ = unlock_character(key)
                            game.message = msg
                            state = "character_unlock_detail"
                        elif self._menu_back_pressed():
                            state = "character_unlock_detail"
                    elif state == "mode_select":
                        if self._menu_up_pressed():
                            mode_selected = (mode_selected - 1) % 3
                        elif self._menu_down_pressed():
                            mode_selected = (mode_selected + 1) % 3
                        elif self._menu_confirm_pressed():
                            if mode_selected == 2:
                                state = "start"
                            else:
                                multiplayer_selected = mode_selected == 1
                                character_selected = 0
                                character_selected_2 = 0
                                character_select_player = 0
                                character_cancel_state = "mode_select"
                                state = "character_select"
                        elif self._menu_back_pressed():
                            state = "start"
                    elif state == "character_select":
                        if self._menu_left_pressed():
                            if multiplayer_selected and character_select_player == 1:
                                character_selected_2 = (character_selected_2 - 1) % len(CHARACTERS)
                            else:
                                character_selected = (character_selected - 1) % len(CHARACTERS)
                        elif self._menu_right_pressed():
                            if multiplayer_selected and character_select_player == 1:
                                character_selected_2 = (character_selected_2 + 1) % len(CHARACTERS)
                            else:
                                character_selected = (character_selected + 1) % len(CHARACTERS)
                        elif self._menu_confirm_pressed():
                            if not is_character_unlocked(selected_character_key(0)):
                                game.message = locked_character_message()
                            elif multiplayer_selected and character_select_player == 0:
                                character_select_player = 1
                            elif not selected_party_unlocked():
                                game.message = locked_character_message()
                            else:
                                char_class = list(CHARACTERS.keys())[character_selected]
                                char_class_2 = list(CHARACTERS.keys())[character_selected_2]
                                game = GameLogic(char_class, char_class_2, multiplayer_selected)
                                record_pending_game_over = False
                                self.record_name_text = ""
                                state = "playing"
                        elif self._menu_back_pressed():
                            if multiplayer_selected and character_select_player == 1:
                                character_select_player = 0
                            else:
                                state = character_cancel_state
                    elif state == "commands":
                        if self._menu_confirm_pressed() or self._menu_back_pressed():
                            state = commands_return_state
                    elif state == "progression":
                        if self._menu_confirm_pressed() or self._menu_back_pressed():
                            state = "paused"
                    elif state == "encyclopedia":
                        entries = ui.filtered_encyclopedia_entries(encyclopedia_category, encyclopedia_query)
                        categories = ("Todos",) + ENCYCLOPEDIA_CATEGORIES
                        if self._menu_back_pressed():
                            state = encyclopedia_return_state
                        elif self._menu_up_pressed() and entries:
                            encyclopedia_selected = (encyclopedia_selected - 1) % len(entries)
                        elif self._menu_down_pressed() and entries:
                            encyclopedia_selected = (encyclopedia_selected + 1) % len(entries)
                        elif self._menu_left_pressed() or self._menu_l1_pressed():
                            encyclopedia_category = categories[(categories.index(encyclopedia_category) - 1) % len(categories)] if encyclopedia_category in categories else "Todos"
                            encyclopedia_selected = 0
                        elif self._menu_right_pressed() or self._menu_r1_pressed():
                            encyclopedia_category = categories[(categories.index(encyclopedia_category) + 1) % len(categories)] if encyclopedia_category in categories else "Todos"
                            encyclopedia_selected = 0
                        elif self._menu_y_pressed():
                            encyclopedia_query = ""
                            encyclopedia_selected = 0
                    elif state == "settings":
                        if self._menu_back_pressed():
                            state = settings_return_state
                            capture_binding = None
                        elif self._menu_up_pressed():
                            settings_selected = (settings_selected - 1) % len(CONTROL_ACTIONS)
                        elif self._menu_down_pressed():
                            settings_selected = (settings_selected + 1) % len(CONTROL_ACTIONS)
                        elif self._menu_left_pressed():
                            settings_slot = (settings_slot - 1) % BINDING_SLOT_COUNT
                        elif self._menu_right_pressed():
                            settings_slot = (settings_slot + 1) % BINDING_SLOT_COUNT
                        elif self._menu_confirm_pressed():
                            action_key = CONTROL_ACTIONS[settings_selected][0]
                            capture_binding = (action_key, settings_slot)
                    elif state == "paused":
                        if self._menu_back_pressed():
                            state = "playing"
                        elif self._menu_up_pressed():
                            pause_selected = (pause_selected - 1) % len(PAUSE_OPTIONS)
                        elif self._menu_down_pressed():
                            pause_selected = (pause_selected + 1) % len(PAUSE_OPTIONS)
                        elif self._menu_confirm_pressed():
                            action = PAUSE_OPTIONS[pause_selected][1]
                            if action == "commands":
                                commands_return_state = "paused"
                            if action == "encyclopedia":
                                encyclopedia_return_state = "paused"
                                encyclopedia_selected = 0
                                state = "encyclopedia"
                                continue
                            if action == "settings":
                                settings_return_state = "paused"
                                state = "settings"
                                capture_binding = None
                                continue
                            if action == "skills":
                                skills_return_state = "paused"
                                state = "skills"
                                skill_selected = min(skill_selected, max(0, len(game.get_player(game.menu_player_index).passives) - 1))
                                continue
                            if action == "stat_shop":
                                game.message = "Loja de Status disponivel apenas no Altar de Status."
                                continue
                            if action == "change_character":
                                character_selected = self._current_character_index(game)
                                character_selected_2 = self._current_character_index(game, 1)
                                multiplayer_selected = game.multiplayer
                                character_select_player = 0
                                character_cancel_state = "paused"
                                state = "character_select"
                                continue
                            state, running, return_action, pause_selected, upgrade_selected = self._handle_action(
                                action,
                                state,
                                game,
                                running,
                                return_action,
                                pause_selected,
                                upgrade_selected,
                            )
                    elif state == "playing":
                        if game.multiplayer:
                            if self._action_pressed(event, controls, "pause"):
                                state = "paused"
                                pause_selected = 0
                            elif self._action_pressed(event, controls, "toggle_weapon"):
                                game.toggle_mode(1)
                            elif self._action_pressed(event, controls, "dash"):
                                game.try_dash(p2_aim_world or aim_world, 1)
                            elif self._action_pressed(event, controls, "special"):
                                game.try_special(p2_aim_world or aim_world, 1)
                            elif self._action_pressed(event, controls, "combo_special"):
                                game.try_combo_special(p2_aim_world or aim_world, 1)
                            elif self._action_pressed(event, controls, "omni_active"):
                                game.try_omni_active()
                            elif self._action_pressed(event, controls, "inventory"):
                                game.menu_player_index = 1
                                state = "inventory"
                                inventory_selected = min(inventory_selected, max(0, len(game.get_inventory(1).item_list()) - 1))
                            elif self._action_pressed(event, controls, "skills"):
                                game.menu_player_index = 1
                                skills_return_state = "playing"
                                state = "skills"
                                skill_selected = min(skill_selected, max(0, len(game.get_player(1).passives) - 1))
                            elif self._action_pressed(event, controls, "stat_shop"):
                                game.message = "Loja de Status disponivel apenas no Altar de Status."
                            continue
                        if self._action_pressed(event, controls, "pause"):
                            state = "paused"
                            pause_selected = 0
                        elif self._action_pressed(event, controls, "settings"):
                            settings_return_state = "playing"
                            state = "settings"
                            special_holding[0] = False
                            special_combo_checked[0] = False
                        elif self._action_pressed(event, controls, "toggle_weapon"):
                            game.toggle_mode()
                        elif self._action_pressed(event, controls, "dash"):
                            game.try_dash(aim_world)
                        elif self._action_pressed(event, controls, "special"):
                            special_holding[0] = True
                            special_hold_time[0] = 0.0
                            special_hold_triggered[0] = False
                            special_combo_checked[0] = False
                        elif self._action_pressed(event, controls, "inventory"):
                            game.menu_player_index = 0
                            state = "inventory"
                            inventory_selected = min(inventory_selected, max(0, len(game.get_inventory(0).item_list()) - 1))
                            special_holding[0] = False
                            special_combo_checked[0] = False
                        elif self._action_pressed(event, controls, "skills"):
                            game.menu_player_index = 0
                            skills_return_state = "playing"
                            state = "skills"
                            skill_selected = min(skill_selected, max(0, len(game.get_player(0).passives) - 1))
                            special_holding[0] = False
                            special_combo_checked[0] = False
                        elif self._action_pressed(event, controls, "stat_shop"):
                            game.message = "Loja de Status disponivel apenas no Altar de Status."
                            special_holding[0] = False
                            special_combo_checked[0] = False

                    elif state == "upgrade":
                        if self._menu_up_pressed():
                            upgrade_selected = (upgrade_selected - 1) % len(game.upgrade_choices)
                        elif self._menu_down_pressed():
                            upgrade_selected = (upgrade_selected + 1) % len(game.upgrade_choices)
                        elif self._menu_confirm_pressed():
                            game.apply_upgrade(game.upgrade_choices[upgrade_selected], game.level_up_player_index)
                            upgrade_selected = 0
                            state = "playing"

                    elif state == "inventory":
                        inv = game.get_inventory(game.menu_player_index)
                        raw_items = inv.item_list()
                        active_items = [item for item in raw_items if inv.is_active(item.slot_key)]
                        reserve_items = [item for item in raw_items if not inv.is_active(item.slot_key)]
                        items = active_items + reserve_items
                        
                        if self._menu_back_pressed() or self._action_pressed(event, controls, "inventory"):
                            if game.active_altar is not None:
                                game.finish_altar_interaction(destroy=True)
                            state = "playing"
                        elif self._menu_r1_pressed() or self._menu_l1_pressed() or (event.type == pygame.KEYDOWN and event.key == pygame.K_t):
                            altar_kind = getattr(getattr(game, "active_altar", None), "kind", None)
                            if altar_kind == "weapon_altar":
                                tabs = ["items"]
                            elif altar_kind == "stamps_altar":
                                tabs = ["stamps"]
                            elif altar_kind == "black_market_altar":
                                tabs = ["shop", "items", "stamps"]
                            else:
                                tabs = ["items", "stamps"]
                            inventory_tab = tabs[(tabs.index(inventory_tab) + 1) % len(tabs)] if inventory_tab in tabs else "items"
                            inventory_selected = 0
                        elif game.multiplayer and self._menu_l3_pressed():
                            game.menu_player_index = 1 - game.menu_player_index
                            inventory_selected = 0
                            
                        elif inventory_tab == "shop":
                            shop_items = list(BASE_ITEM_KEYS)
                            if self._menu_up_pressed():
                                inventory_selected -= 5
                            elif self._menu_down_pressed():
                                inventory_selected += 5
                            elif self._menu_left_pressed():
                                inventory_selected -= 1
                            elif self._menu_right_pressed():
                                inventory_selected += 1
                            elif self._menu_confirm_pressed():
                                cost = 15
                                if inv.points >= cost:
                                    self.point_confirm_action = ("buy_shop_item", shop_items[inventory_selected])
                                    self.point_confirm_cost = cost
                                    self.point_confirm_msg = f"Deseja gastar {cost} moedas para comprar este item?"
                                    self.point_confirm_return = "inventory"
                                    self.point_confirm_selected = 1
                                    state = "point_confirm"
                                else:
                                    game.message = f"Pontos insuficientes (custa {cost})."
                            inventory_selected = max(0, min(inventory_selected, len(shop_items) - 1))
                            
                        elif items:
                            if self._menu_up_pressed():
                                inventory_selected -= 5
                            elif self._menu_down_pressed():
                                inventory_selected += 5
                            elif self._menu_left_pressed():
                                inventory_selected -= 1
                            elif self._menu_right_pressed():
                                inventory_selected += 1
                            elif self._menu_confirm_pressed():
                                game.toggle_inventory_item(items[inventory_selected].slot_key)
                            elif self._menu_x_pressed():
                                item = items[inventory_selected]
                                if item.rank == 1 and item.level >= 10 and inv.black_market_unlocked:
                                    if inv.points >= 15:
                                        self.point_confirm_action = ("transform_inventory", item.slot_key)
                                        self.point_confirm_cost = 15
                                        self.point_confirm_msg = "Deseja gastar 15 moedas para tentar a Transformacao (Risco de Degradacao)?"
                                        self.point_confirm_return = "inventory"
                                        self.point_confirm_selected = 1
                                        state = "point_confirm"
                                    else:
                                        game.message = "Pontos insuficientes para Transformar (custa 15)."
                                else:
                                    cost = 7 if item.is_relic else (3 if item.is_hybrid else 1)
                                    if inv.points >= cost:
                                        self.point_confirm_action = ("upgrade_inventory", item.slot_key)
                                        self.point_confirm_cost = cost
                                        self.point_confirm_msg = f"Deseja gastar {cost} ponto(s) para aprimorar este item?"
                                        self.point_confirm_return = "inventory"
                                        self.point_confirm_selected = 1
                                        state = "point_confirm"
                                    else:
                                        game.message = f"Pontos insuficientes (custa {cost})."
                            elif self._menu_y_pressed():
                                game.mark_or_fuse_item(items[inventory_selected].slot_key)
                                if game.has_pending_fusion():
                                    state = "fusion_confirm"
                                    fusion_confirm_selected = 1
                            inventory_selected = max(0, min(inventory_selected, len(items) - 1))

                    elif state == "point_confirm":
                        self._refresh_point_confirm_quantity(game)
                        if self._menu_back_pressed():
                            self._clear_point_confirm_quantity()
                            state = self.point_confirm_return
                        elif self._point_confirm_has_quantity() and self._menu_left_pressed():
                            self._adjust_point_confirm_quantity(-1, game)
                        elif self._point_confirm_has_quantity() and self._menu_right_pressed():
                            self._adjust_point_confirm_quantity(1, game)
                        elif self._menu_left_pressed() or self._menu_right_pressed() or self._menu_up_pressed() or self._menu_down_pressed():
                            self.point_confirm_selected = 1 - self.point_confirm_selected
                        elif self._menu_confirm_pressed():
                            if self.point_confirm_selected == 0:
                                state = self._handle_point_confirm_action(self.point_confirm_action, game, self.point_confirm_return)
                            else:
                                self._clear_point_confirm_quantity()
                                state = self.point_confirm_return

                    elif state == "fusion_confirm":
                        if self._menu_back_pressed():
                            state, inventory_selected = self._handle_fusion_confirm_action("fusion_confirm_no", game, inventory_selected)
                        elif self._menu_left_pressed() or self._menu_right_pressed() or self._menu_up_pressed() or self._menu_down_pressed():
                            fusion_confirm_selected = 1 - fusion_confirm_selected
                        elif self._menu_confirm_pressed():
                            action = "fusion_confirm_yes" if fusion_confirm_selected == 0 else "fusion_confirm_no"
                            state, inventory_selected = self._handle_fusion_confirm_action(action, game, inventory_selected)

                    elif state == "rng_result":
                        if self._menu_confirm_pressed() or self._menu_back_pressed():
                            state = "playing"

                    elif state == "stat_shop":
                        if self._menu_back_pressed() or self._action_pressed(event, controls, "stat_shop"):
                            if game.active_altar is not None:
                                game.finish_altar_interaction(destroy=True)
                            state = stat_shop_return_state
                        elif not game.stat_shop_offers:
                            if (self._menu_confirm_pressed() or self._menu_y_pressed()) and game.stat_shop_unlocked():
                                hp_cost = game._max_health_shop_cost(STAT_SHOP_ROLL_COST)
                                self.point_confirm_action = ("roll_stat_shop",)
                                self.point_confirm_cost = hp_cost
                                self.point_confirm_msg = f"Sacrificar {hp_cost} de vida maxima para abrir o gacha?"
                                self.point_confirm_return = "stat_shop"
                                self.point_confirm_selected = 1
                                state = "point_confirm"
                        else:
                            stat_shop_selected = min(stat_shop_selected, len(game.stat_shop_offers) - 1)
                            if self._menu_left_pressed() or self._menu_up_pressed():
                                stat_shop_selected = (stat_shop_selected - 1) % len(game.stat_shop_offers)
                            elif self._menu_right_pressed() or self._menu_down_pressed():
                                stat_shop_selected = (stat_shop_selected + 1) % len(game.stat_shop_offers)
                            elif self._menu_confirm_pressed():
                                cost = game.stat_shop_offers[stat_shop_selected]["cost"]
                                if game.inventory.points >= cost:
                                    self.point_confirm_action = ("purchase_stat_shop", stat_shop_selected)
                                    self.point_confirm_cost = cost
                                    self.point_confirm_msg = f"Deseja gastar {cost} ponto(s) para comprar esta melhoria?"
                                    self.point_confirm_return = "stat_shop"
                                    self.point_confirm_selected = 1
                                    state = "point_confirm"
                                else:
                                    game.message = f"Pontos insuficientes (custa {cost})."
                            elif self._menu_x_pressed():
                                hp_cost = game._max_health_shop_cost(STAT_SHOP_REROLL_COST)
                                self.point_confirm_action = ("reroll_stat_shop", stat_shop_selected)
                                self.point_confirm_cost = hp_cost
                                self.point_confirm_msg = f"Sacrificar {hp_cost} de vida maxima para trocar esta oferta?"
                                self.point_confirm_return = "stat_shop"
                                self.point_confirm_selected = 1
                                state = "point_confirm"

                    elif state == "constructions":
                        entry_count = len(ui.construction_catalog())
                        if self._menu_back_pressed():
                            state = "paused"
                        elif self._menu_up_pressed():
                            construction_selected = (construction_selected - 1) % entry_count
                        elif self._menu_down_pressed():
                            construction_selected = (construction_selected + 1) % entry_count

                    elif state == "skills":
                        keys = list(game.get_player(game.menu_player_index).passives.keys())
                        if self._menu_back_pressed() or self._action_pressed(event, controls, "skills"):
                            if game.active_altar is not None:
                                game.finish_altar_interaction(destroy=True)
                            state = skills_return_state
                        elif game.multiplayer and self._menu_y_pressed():
                            game.menu_player_index = 1 - game.menu_player_index
                            skill_selected = 0
                        elif keys:
                            if self._menu_up_pressed():
                                skill_selected = (skill_selected - 1) % len(keys)
                            elif self._menu_down_pressed():
                                skill_selected = (skill_selected + 1) % len(keys)
                            elif self._menu_confirm_pressed() or self._menu_x_pressed():
                                skill_selected = min(skill_selected, len(keys) - 1)
                                key = keys[skill_selected]
                                cost = game.skill_upgrade_cost(key)
                                level = game.get_player(game.menu_player_index).passives.get(key, 0)
                                if level >= 10:
                                    game.message = "Skill ja esta no nivel maximo."
                                elif game.get_inventory(game.menu_player_index).points >= cost:
                                    self.point_confirm_action = ("upgrade_skill", key)
                                    self.point_confirm_cost = cost
                                    self.point_confirm_msg = f"Deseja gastar {cost} ponto(s) para aprimorar esta skill?"
                                    self.point_confirm_return = "skills"
                                    self.point_confirm_selected = 1
                                    state = "point_confirm"
                                else:
                                    game.message = f"Pontos insuficientes (custa {cost})."

                    elif state == "game_over":
                        go_options = [("Reiniciar", "restart"), ("Trocar Personagem", "change_character"), ("Voltar ao Menu", "menu"), ("Fechar", "quit")]
                        if self._menu_up_pressed():
                            game_over_selected = (game_over_selected - 1) % len(go_options)
                        elif self._menu_down_pressed():
                            game_over_selected = (game_over_selected + 1) % len(go_options)
                        elif self._menu_confirm_pressed():
                            go_action = go_options[game_over_selected][1]
                            if go_action == "restart":
                                game.restart()
                                record_pending_game_over = False
                                self.record_name_text = ""
                                state = "playing"
                            elif go_action == "change_character":
                                character_selected = self._current_character_index(game)
                                character_selected_2 = self._current_character_index(game, 1)
                                multiplayer_selected = game.multiplayer
                                character_select_player = 0
                                character_cancel_state = "game_over"
                                state = "character_select"
                            elif go_action == "menu":
                                running = False
                                return_action = "menu"
                            elif go_action == "quit":
                                running = False
                                return_action = "quit"
                        elif self._menu_back_pressed():
                            running = False
                            return_action = "menu"

                elif event.type in (pygame.KEYUP, pygame.MOUSEBUTTONUP, pygame.JOYBUTTONUP):
                    if self._action_released(event, controls, "special") and special_holding[0]:
                        if state == "playing" and not special_hold_triggered[0]:
                            game.try_special(aim_world)
                        special_holding[0] = False
                        special_hold_time[0] = 0.0
                        special_hold_triggered[0] = False
                        special_combo_checked[0] = False

                elif event.type == pygame.KEYDOWN:
                    if state == "record_name":
                        if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                            add_record(self.record_name_text, game)
                            self.record_name_text = ""
                            record_pending_game_over = False
                            state = "game_over"
                        elif event.key == pygame.K_ESCAPE:
                            self.record_name_text = ""
                            record_pending_game_over = False
                            state = "game_over"
                        elif event.key == pygame.K_BACKSPACE:
                            self.record_name_text = self.record_name_text[:-1]
                        elif len(self.record_name_text) < 16 and event.unicode and (event.unicode.isalnum() or event.unicode in " _-"):
                            self.record_name_text += event.unicode
                    elif state == "records":
                        if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE, pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                            state = "start"
                    elif state == "record_details":
                        if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE, pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                            state = "records"
                    elif state == "record_kills":
                        if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE, pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                            state = "record_details"
                    elif state == "record_delete_confirm":
                        if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE, pygame.K_n):
                            state = "records"
                        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE, pygame.K_y):
                            delete_record(self.record_delete_index)
                            state = "records"
                    elif state == "coin_shop":
                        if event.key == pygame.K_UP:
                            coin_shop_selected = (coin_shop_selected - 1) % 4
                        elif event.key == pygame.K_DOWN:
                            coin_shop_selected = (coin_shop_selected + 1) % 4
                        elif event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                            state = "start"
                        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                            if coin_shop_selected == 3:
                                state = "start"
                            elif coin_shop_selected == 1:
                                character_unlock_selected = 0
                                state = "character_unlock"
                            elif coin_shop_selected == 2:
                                refresh_character_upgrade_draft()
                                character_upgrade_selected = 0
                                state = "character_upgrades"
                            else:
                                game.message = "Loja de moedas: categoria em desenvolvimento."
                    elif state == "character_upgrades":
                        keys = list(CHARACTER_UPGRADES.keys())
                        if event.key == pygame.K_UP:
                            character_upgrade_selected = (character_upgrade_selected - 1) % len(keys)
                        elif event.key == pygame.K_DOWN:
                            character_upgrade_selected = (character_upgrade_selected + 1) % len(keys)
                        elif event.key == pygame.K_LEFT:
                            change_character_upgrade_level(keys[character_upgrade_selected], -1)
                        elif event.key in (pygame.K_RIGHT, pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                            result = change_character_upgrade_level(keys[character_upgrade_selected], 1)
                            if result == "confirm":
                                state = "character_upgrade_confirm"
                        elif event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                            save_active_upgrade_levels(self.character_upgrade_draft)
                            game.message = "Melhorias salvas."
                            state = "coin_shop"
                        elif event.key == pygame.K_s:
                            save_active_upgrade_levels(self.character_upgrade_draft)
                            game.message = "Melhorias salvas."
                            state = "coin_shop"
                    elif state == "character_upgrade_confirm":
                        if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE, pygame.K_n):
                            state = "character_upgrades"
                        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE, pygame.K_y):
                            _, msg, _ = purchase_upgrade_level(self.character_upgrade_pending_key)
                            refresh_character_upgrade_draft()
                            game.message = msg
                            state = "character_upgrades"
                    elif state == "character_unlock":
                        if event.key == pygame.K_LEFT:
                            character_unlock_selected = max(0, character_unlock_selected - 1)
                        elif event.key == pygame.K_RIGHT:
                            character_unlock_selected = min(len(CHARACTERS) - 1, character_unlock_selected + 1)
                        elif event.key == pygame.K_UP:
                            character_unlock_selected = max(0, character_unlock_selected - 2)
                        elif event.key == pygame.K_DOWN:
                            character_unlock_selected = min(len(CHARACTERS) - 1, character_unlock_selected + 2)
                        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                            state = "character_unlock_detail"
                        elif event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                            state = "coin_shop"
                    elif state == "character_unlock_detail":
                        if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                            state = "character_unlock"
                        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                            key = list(CHARACTERS.keys())[character_unlock_selected]
                            if is_character_unlocked(key):
                                game.message = "Personagem ja desbloqueado."
                            else:
                                state = "character_unlock_confirm"
                    elif state == "character_unlock_confirm":
                        if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE, pygame.K_n):
                            state = "character_unlock_detail"
                        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE, pygame.K_y):
                            key = list(CHARACTERS.keys())[character_unlock_selected]
                            _, msg, _ = unlock_character(key)
                            game.message = msg
                            state = "character_unlock_detail"
                    elif state == "settings":
                        if capture_binding:
                            action_key, slot = capture_binding
                            controls[action_key][slot] = self._binding_from_event(event)
                            capture_binding = None
                            continue
                        if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                            state = settings_return_state
                        elif event.key == pygame.K_UP:
                            settings_selected = (settings_selected - 1) % len(CONTROL_ACTIONS)
                        elif event.key == pygame.K_DOWN:
                            settings_selected = (settings_selected + 1) % len(CONTROL_ACTIONS)
                        elif event.key == pygame.K_LEFT:
                            settings_slot = (settings_slot - 1) % BINDING_SLOT_COUNT
                        elif event.key in (pygame.K_RIGHT, pygame.K_TAB):
                            settings_slot = (settings_slot + 1) % BINDING_SLOT_COUNT
                        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                            action_key = CONTROL_ACTIONS[settings_selected][0]
                            capture_binding = (action_key, settings_slot)
                        elif event.key == pygame.K_r:
                            controls = self._default_bindings()
                            if self._joystick_count():
                                self._apply_default_joystick_bindings(controls)
                            capture_binding = None
                        elif self._action_pressed(event, controls, "fullscreen"):
                            fullscreen = not fullscreen
                            screen, fullscreen = self._set_display_mode(fullscreen, ui)
                        continue

                    if self._action_pressed(event, controls, "fullscreen"):
                        fullscreen = not fullscreen
                        screen, fullscreen = self._set_display_mode(fullscreen, ui)
                        continue

                    if state == "start":
                        if event.key == pygame.K_UP:
                            start_selected = (start_selected - 1) % len(START_OPTIONS)
                        elif event.key == pygame.K_DOWN:
                            start_selected = (start_selected + 1) % len(START_OPTIONS)
                        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                            action = START_OPTIONS[start_selected][1]
                            if action == "character_select":
                                state = "mode_select" if self._joystick_count() else "character_select"
                                character_selected = 0
                                character_selected_2 = 0
                                character_select_player = 0
                                multiplayer_selected = False
                                character_cancel_state = "start"
                            elif action == "commands":
                                commands_return_state = "start"
                                state = "commands"
                            elif action == "records":
                                state = "records"
                            elif action == "coin_shop":
                                state = "coin_shop"
                            elif action == "encyclopedia":
                                encyclopedia_return_state = "start"
                                encyclopedia_selected = 0
                                state = "encyclopedia"
                            elif action == "settings":
                                settings_return_state = "start"
                                state = "settings"
                            elif action == "menu":
                                running = False
                                return_action = "menu"
                        elif event.key == pygame.K_ESCAPE:
                            running = False
                            return_action = "menu"
                        elif event.key == pygame.K_c:
                            commands_return_state = "start"
                            state = "commands"
                        elif self._action_pressed(event, controls, "settings"):
                            settings_return_state = "start"
                            state = "settings"

                    elif state == "mode_select":
                        if event.key == pygame.K_UP:
                            mode_selected = (mode_selected - 1) % 3
                        elif event.key == pygame.K_DOWN:
                            mode_selected = (mode_selected + 1) % 3
                        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                            if mode_selected == 2:
                                state = "start"
                            else:
                                multiplayer_selected = mode_selected == 1
                                character_selected = 0
                                character_selected_2 = 0
                                character_select_player = 0
                                character_cancel_state = "mode_select"
                                state = "character_select"
                        elif event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                            state = "start"

                    elif state == "character_select":
                        if event.key == pygame.K_LEFT:
                            if multiplayer_selected and character_select_player == 1:
                                character_selected_2 = (character_selected_2 - 1) % len(CHARACTERS)
                            else:
                                character_selected = (character_selected - 1) % len(CHARACTERS)
                        elif event.key == pygame.K_RIGHT:
                            if multiplayer_selected and character_select_player == 1:
                                character_selected_2 = (character_selected_2 + 1) % len(CHARACTERS)
                            else:
                                character_selected = (character_selected + 1) % len(CHARACTERS)
                        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                            if not is_character_unlocked(selected_character_key(0)):
                                game.message = locked_character_message()
                            elif multiplayer_selected and character_select_player == 0:
                                character_select_player = 1
                            elif not selected_party_unlocked():
                                game.message = locked_character_message()
                            else:
                                char_class = list(CHARACTERS.keys())[character_selected]
                                char_class_2 = list(CHARACTERS.keys())[character_selected_2]
                                game = GameLogic(char_class, char_class_2, multiplayer_selected)
                                record_pending_game_over = False
                                self.record_name_text = ""
                                state = "playing"
                        elif event.key == pygame.K_ESCAPE:
                            if multiplayer_selected and character_select_player == 1:
                                character_select_player = 0
                            else:
                                state = character_cancel_state

                    elif state == "playing":
                        if self._action_pressed(event, controls, "pause"):
                            state = "paused"
                            pause_selected = 0
                        elif self._action_pressed(event, controls, "settings"):
                            settings_return_state = "playing"
                            state = "settings"
                            special_holding[0] = False
                            special_combo_checked[0] = False
                            combo_holding[0] = False
                        elif self._action_pressed(event, controls, "toggle_weapon"):
                            game.toggle_mode()
                        elif self._action_pressed(event, controls, "dash"):
                            game.try_dash(aim_world)
                        elif self._action_pressed(event, controls, "special"):
                            # Especial normal: disparo imediato, sem hold
                            game.try_special(aim_world, 0)
                        elif self._action_pressed(event, controls, "combo_special"):
                            game.try_combo_special(aim_world, 0)
                        elif self._action_pressed(event, controls, "omni_active"):
                            game.try_omni_active()
                        elif self._action_pressed(event, controls, "inventory"):
                            state = "inventory"
                            game.menu_player_index = 0
                            inventory_selected = min(inventory_selected, max(0, len(game.get_inventory(0).item_list()) - 1))
                            special_holding[0] = False
                            special_combo_checked[0] = False
                            combo_holding[0] = False
                        elif self._action_pressed(event, controls, "skills"):
                            skills_return_state = "playing"
                            state = "skills"
                            game.menu_player_index = 0
                            skill_selected = min(skill_selected, max(0, len(game.get_player(0).passives) - 1))
                            special_holding[0] = False
                            special_combo_checked[0] = False
                            combo_holding[0] = False
                        elif self._action_pressed(event, controls, "stat_shop"):
                            game.message = "Loja de Status disponivel apenas no Altar de Status."
                            special_holding[0] = False
                            special_combo_checked[0] = False
                            combo_holding[0] = False

                    elif state == "paused":
                        if event.key == pygame.K_ESCAPE:
                            state = "playing"
                        elif event.key == pygame.K_UP:
                            pause_selected = (pause_selected - 1) % len(PAUSE_OPTIONS)
                        elif event.key == pygame.K_DOWN:
                            pause_selected = (pause_selected + 1) % len(PAUSE_OPTIONS)
                        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                            action = PAUSE_OPTIONS[pause_selected][1]
                            if action == "commands":
                                commands_return_state = "paused"
                            if action == "encyclopedia":
                                encyclopedia_return_state = "paused"
                                encyclopedia_selected = 0
                                state = "encyclopedia"
                                continue
                            if action == "settings":
                                settings_return_state = "paused"
                                state = "settings"
                                capture_binding = None
                                continue
                            if action == "skills":
                                skills_return_state = "paused"
                                state = "skills"
                                skill_selected = min(skill_selected, max(0, len(game.get_player(game.menu_player_index).passives) - 1))
                                continue
                            if action == "stat_shop":
                                game.message = "Loja de Status disponivel apenas no Altar de Status."
                                continue
                            if action == "change_character":
                                character_selected = self._current_character_index(game)
                                character_selected_2 = self._current_character_index(game, 1)
                                multiplayer_selected = game.multiplayer
                                character_select_player = 0
                                character_cancel_state = "paused"
                                state = "character_select"
                                continue
                            state, running, return_action, pause_selected, upgrade_selected = self._handle_action(
                                action,
                                state,
                                game,
                                running,
                                return_action,
                                pause_selected,
                                upgrade_selected,
                            )

                    elif state == "commands":
                        if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE, pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                            state = commands_return_state
                    elif state == "progression":
                        if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE, pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                            state = "paused"

                    elif state == "encyclopedia":
                        entries = ui.filtered_encyclopedia_entries(encyclopedia_category, encyclopedia_query)
                        categories = ("Todos",) + ENCYCLOPEDIA_CATEGORIES
                        if event.key == pygame.K_ESCAPE:
                            state = encyclopedia_return_state
                        elif event.key == pygame.K_BACKSPACE:
                            if encyclopedia_query:
                                encyclopedia_query = encyclopedia_query[:-1]
                                encyclopedia_selected = 0
                            else:
                                state = encyclopedia_return_state
                        elif event.key == pygame.K_UP and entries:
                            encyclopedia_selected = (encyclopedia_selected - 1) % len(entries)
                        elif event.key == pygame.K_DOWN and entries:
                            encyclopedia_selected = (encyclopedia_selected + 1) % len(entries)
                        elif event.key in (pygame.K_LEFT, pygame.K_q):
                            encyclopedia_category = categories[(categories.index(encyclopedia_category) - 1) % len(categories)] if encyclopedia_category in categories else "Todos"
                            encyclopedia_selected = 0
                        elif event.key in (pygame.K_RIGHT, pygame.K_e):
                            encyclopedia_category = categories[(categories.index(encyclopedia_category) + 1) % len(categories)] if encyclopedia_category in categories else "Todos"
                            encyclopedia_selected = 0
                        elif event.key == pygame.K_DELETE:
                            encyclopedia_query = ""
                            encyclopedia_selected = 0
                        elif getattr(event, "unicode", "") and event.unicode.isprintable():
                            encyclopedia_query += event.unicode
                            encyclopedia_selected = 0

                    elif state == "stat_shop":
                        if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE) or self._action_pressed(event, controls, "stat_shop"):
                            if game.active_altar is not None:
                                game.finish_altar_interaction(destroy=True)
                            state = stat_shop_return_state
                        elif event.key == pygame.K_r and game.stat_shop_unlocked() and not game.stat_shop_offers:
                            hp_cost = game._max_health_shop_cost(STAT_SHOP_ROLL_COST)
                            self.point_confirm_action = ("roll_stat_shop",)
                            self.point_confirm_cost = hp_cost
                            self.point_confirm_msg = f"Sacrificar {hp_cost} de vida maxima para abrir o gacha?"
                            self.point_confirm_return = "stat_shop"
                            self.point_confirm_selected = 1
                            state = "point_confirm"
                        elif game.stat_shop_offers:
                            if event.key in (pygame.K_LEFT, pygame.K_a):
                                stat_shop_selected = (stat_shop_selected - 1) % len(game.stat_shop_offers)
                            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                                stat_shop_selected = (stat_shop_selected + 1) % len(game.stat_shop_offers)
                            elif event.key in (pygame.K_UP, pygame.K_w):
                                stat_shop_selected = (stat_shop_selected - 1) % len(game.stat_shop_offers)
                            elif event.key in (pygame.K_DOWN, pygame.K_s):
                                stat_shop_selected = (stat_shop_selected + 1) % len(game.stat_shop_offers)
                            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                                idx = stat_shop_selected
                                cost = game.stat_shop_offers[idx]["cost"]
                                if game.inventory.points >= cost:
                                    self.point_confirm_action = ("purchase_stat_shop", idx)
                                    self.point_confirm_cost = cost
                                    self.point_confirm_msg = f"Deseja gastar {cost} ponto(s) para comprar esta melhoria?"
                                    self.point_confirm_return = "stat_shop"
                                    self.point_confirm_selected = 1
                                    state = "point_confirm"
                                else:
                                    game.message = f"Pontos insuficientes (custa {cost})."
                            elif event.key == pygame.K_x:
                                idx = stat_shop_selected
                                hp_cost = game._max_health_shop_cost(STAT_SHOP_REROLL_COST)
                                self.point_confirm_action = ("reroll_stat_shop", idx)
                                self.point_confirm_cost = hp_cost
                                self.point_confirm_msg = f"Sacrificar {hp_cost} de vida maxima para trocar esta oferta?"
                                self.point_confirm_return = "stat_shop"
                                self.point_confirm_selected = 1
                                state = "point_confirm"
                            else:
                                idx = None
                                if event.key in (pygame.K_1, pygame.K_KP1): idx = 0
                                elif event.key in (pygame.K_2, pygame.K_KP2) and len(game.stat_shop_offers) > 1: idx = 1
                                elif event.key in (pygame.K_3, pygame.K_KP3) and len(game.stat_shop_offers) > 2: idx = 2
                                if idx is not None:
                                    stat_shop_selected = idx
                                    cost = game.stat_shop_offers[idx]["cost"]
                                    if game.inventory.points >= cost:
                                        self.point_confirm_action = ("purchase_stat_shop", idx)
                                        self.point_confirm_cost = cost
                                        self.point_confirm_msg = f"Deseja gastar {cost} ponto(s) para comprar esta melhoria?"
                                        self.point_confirm_return = "stat_shop"
                                        self.point_confirm_selected = 1
                                        state = "point_confirm"
                                    else:
                                        game.message = f"Pontos insuficientes (custa {cost})."

                    elif state == "constructions":
                        entry_count = len(ui.construction_catalog())
                        if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                            state = "paused"
                        elif event.key == pygame.K_UP:
                            construction_selected = (construction_selected - 1) % entry_count
                        elif event.key == pygame.K_DOWN:
                            construction_selected = (construction_selected + 1) % entry_count
                        elif event.key == pygame.K_PAGEUP:
                            construction_selected = max(0, construction_selected - 5)
                        elif event.key == pygame.K_PAGEDOWN:
                            construction_selected = min(entry_count - 1, construction_selected + 5)
                        elif event.key == pygame.K_HOME:
                            construction_selected = 0
                        elif event.key == pygame.K_END:
                            construction_selected = entry_count - 1

                    elif state == "skills":
                        keys = list(game.get_player(game.menu_player_index).passives.keys())
                        if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE, pygame.K_k):
                            if game.active_altar is not None:
                                game.finish_altar_interaction(destroy=True)
                            state = skills_return_state
                        elif game.multiplayer and event.key == pygame.K_p:
                            game.menu_player_index = 1 - game.menu_player_index
                            skill_selected = 0
                        elif keys:
                            if event.key == pygame.K_UP:
                                skill_selected = (skill_selected - 1) % len(keys)
                            elif event.key == pygame.K_DOWN:
                                skill_selected = (skill_selected + 1) % len(keys)
                            elif event.key == pygame.K_PAGEUP:
                                skill_selected = max(0, skill_selected - 5)
                            elif event.key == pygame.K_PAGEDOWN:
                                skill_selected = min(len(keys) - 1, skill_selected + 5)
                            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE, pygame.K_u):
                                key = keys[skill_selected]
                                cost = game.skill_upgrade_cost(key)
                                level = game.get_player(game.menu_player_index).passives.get(key, 0)
                                if level >= 10:
                                    game.message = "Skill ja esta no nivel maximo."
                                elif game.get_inventory(game.menu_player_index).points >= cost:
                                    self.point_confirm_action = ("upgrade_skill", key)
                                    self.point_confirm_cost = cost
                                    self.point_confirm_msg = f"Deseja gastar {cost} ponto(s) para aprimorar esta skill?"
                                    self.point_confirm_return = "skills"
                                    self.point_confirm_selected = 1
                                    state = "point_confirm"
                                else:
                                    game.message = f"Pontos insuficientes (custa {cost})."

                    elif state == "upgrade":
                        if event.key == pygame.K_UP:
                            upgrade_selected = (upgrade_selected - 1) % len(game.upgrade_choices)
                        elif event.key == pygame.K_DOWN:
                            upgrade_selected = (upgrade_selected + 1) % len(game.upgrade_choices)
                        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                            game.apply_upgrade(game.upgrade_choices[upgrade_selected], game.level_up_player_index)
                            upgrade_selected = 0
                            state = "playing"

                    elif state == "inventory":
                        inv = game.get_inventory(game.menu_player_index)
                        raw_items = inv.item_list()
                        active_items = [item for item in raw_items if inv.is_active(item.slot_key)]
                        reserve_items = [item for item in raw_items if not inv.is_active(item.slot_key)]
                        items = active_items + reserve_items

                        if event.key in (pygame.K_ESCAPE, pygame.K_i):
                            if game.active_altar is not None:
                                game.finish_altar_interaction(destroy=True)
                            state = "playing"
                            inventory_tab = "items"
                        elif event.key in (pygame.K_TAB, pygame.K_q):
                            altar_kind = getattr(getattr(game, "active_altar", None), "kind", None)
                            if altar_kind == "weapon_altar":
                                tabs = ["items"]
                            elif altar_kind == "stamps_altar":
                                tabs = ["stamps"]
                            elif altar_kind == "black_market_altar":
                                tabs = ["shop", "items", "stamps"]
                            else:
                                tabs = ["items", "stamps"]
                            inventory_tab = tabs[(tabs.index(inventory_tab) + 1) % len(tabs)] if inventory_tab in tabs else "items"
                            inventory_selected = 0
                        elif game.multiplayer and event.key == pygame.K_p:
                            game.menu_player_index = 1 - game.menu_player_index
                            inventory_selected = 0
                        elif inventory_tab == "shop":
                            shop_keys = list(BASE_ITEM_KEYS)
                            if event.key == pygame.K_LEFT:
                                inventory_selected = max(0, inventory_selected - 1)
                            elif event.key == pygame.K_RIGHT:
                                inventory_selected = min(len(shop_keys) - 1, inventory_selected + 1)
                            elif event.key == pygame.K_UP:
                                inventory_selected = max(0, inventory_selected - 5)
                            elif event.key == pygame.K_DOWN:
                                inventory_selected = min(len(shop_keys) - 1, inventory_selected + 5)
                            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_e, pygame.K_u):
                                cost = 15
                                if inv.points >= cost:
                                    self.point_confirm_action = ("buy_shop_item", shop_keys[inventory_selected])
                                    self.point_confirm_cost = cost
                                    self.point_confirm_msg = f"Deseja gastar {cost} moedas para comprar este item?"
                                    self.point_confirm_return = "inventory"
                                    self.point_confirm_selected = 1
                                    state = "point_confirm"
                                else:
                                    game.message = f"Pontos insuficientes (custa {cost})."
                        elif inventory_tab == "stamps":
                            player = game.get_player(game.menu_player_index)
                            stamp_count = len(player.weapon_stamps.get("weapon_1", [])) + len(player.weapon_stamps.get("weapon_2", [])) + len(player.stamp_reserve)
                            if stamp_count:
                                if event.key == pygame.K_UP:
                                    inventory_selected -= 5
                                elif event.key == pygame.K_DOWN:
                                    inventory_selected += 5
                                elif event.key == pygame.K_LEFT:
                                    inventory_selected -= 1
                                elif event.key == pygame.K_RIGHT:
                                    inventory_selected += 1
                                elif event.key == pygame.K_1:
                                    game.equip_stamp("weapon_1", inventory_selected)
                                elif event.key == pygame.K_2:
                                    game.equip_stamp("weapon_2", inventory_selected)
                                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_e):
                                    game.unequip_stamp(inventory_selected)
                                elif event.key == pygame.K_f:
                                    if not self._blocked_static_upgrade(game, "stamp_fuse"):
                                        game.setup_stamp_fusion(inventory_selected)
                                        state = "stamp_fusion_confirm"
                                        fusion_confirm_selected = 1
                                elif event.key == pygame.K_s:
                                    if self._blocked_static_upgrade(game, "sell_stamp"):
                                        continue
                                    self._toggle_stamp_sale_mark(game, inventory_selected)
                                elif event.key == pygame.K_v:
                                    if self._blocked_static_upgrade(game, "sell_stamp"):
                                        continue
                                    next_state = self._confirm_stamp_sale_marks(game)
                                    if next_state:
                                        state = next_state
                                inventory_selected = max(0, min(inventory_selected, stamp_count - 1))
                        elif inventory_tab == "stamps":
                            player = game.get_player(game.menu_player_index)
                            stamp_count = len(player.weapon_stamps.get("weapon_1", [])) + len(player.weapon_stamps.get("weapon_2", [])) + len(player.stamp_reserve)
                            if stamp_count:
                                if self._menu_up_pressed():
                                    inventory_selected -= 5
                                elif self._menu_down_pressed():
                                    inventory_selected += 5
                                elif self._menu_left_pressed():
                                    inventory_selected -= 1
                                elif self._menu_right_pressed():
                                    inventory_selected += 1
                                elif self._menu_confirm_pressed():
                                    game.unequip_stamp(inventory_selected)
                                elif self._menu_x_pressed():
                                    game.equip_stamp("weapon_1", inventory_selected)
                                elif self._menu_y_pressed():
                                    game.equip_stamp("weapon_2", inventory_selected)
                                elif event.type == pygame.KEYDOWN and event.key == pygame.K_f:
                                    if not self._blocked_static_upgrade(game, "stamp_fuse"):
                                        game.setup_stamp_fusion(inventory_selected)
                                        state = "stamp_fusion_confirm"
                                        fusion_confirm_selected = 1
                                inventory_selected = max(0, min(inventory_selected, stamp_count - 1))

                        elif items:
                            if event.key == pygame.K_UP:
                                inventory_selected -= 5
                            elif event.key == pygame.K_DOWN:
                                inventory_selected += 5
                            elif event.key == pygame.K_LEFT:
                                inventory_selected -= 1
                            elif event.key == pygame.K_RIGHT:
                                inventory_selected += 1
                            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_e):
                                game.toggle_inventory_item(items[inventory_selected].slot_key)
                            elif event.key == pygame.K_u:
                                item = items[inventory_selected]
                                if item.rank == 1 and item.level >= 10 and inv.black_market_unlocked:
                                    if self._blocked_static_upgrade(game, "transform_inventory"):
                                        continue
                                    cost = 15
                                    if inv.points >= cost:
                                        self.point_confirm_action = ("transform_inventory", item.slot_key)
                                        self.point_confirm_cost = cost
                                        self.point_confirm_msg = "Deseja gastar 15 moedas para tentar a Transformacao (Risco de Degradacao)?"
                                        self.point_confirm_return = "inventory"
                                        self.point_confirm_selected = 1
                                        state = "point_confirm"
                                    else:
                                        game.message = "Pontos insuficientes para Transformar (custa 15)."
                                else:
                                    if self._blocked_static_upgrade(game, "upgrade_inventory"):
                                        continue
                                    cost = 7 if item.is_relic else (3 if item.is_hybrid else 1)
                                    if inv.points >= cost:
                                        self.point_confirm_action = ("upgrade_inventory", item.slot_key)
                                        self.point_confirm_cost = cost
                                        self.point_confirm_msg = f"Deseja gastar {cost} ponto(s) para aprimorar este item?"
                                        self.point_confirm_return = "inventory"
                                        self.point_confirm_selected = 1
                                        state = "point_confirm"
                                    else:
                                        game.message = f"Pontos insuficientes (custa {cost})."
                            elif event.key == pygame.K_f:
                                if self._blocked_static_upgrade(game, "item_fuse"):
                                    continue
                                game.mark_or_fuse_item(items[inventory_selected].slot_key)
                                if game.has_pending_fusion():
                                    state = "fusion_confirm"
                                    fusion_confirm_selected = 1
                            elif event.key == pygame.K_s:
                                if self._blocked_static_upgrade(game, "sell_inventory"):
                                    continue
                                if not inv.is_active(items[inventory_selected].slot_key):
                                    self._toggle_inventory_sale_mark(game, items[inventory_selected].slot_key)
                                else:
                                    game.message = "Desequipe o item antes de vende-lo."
                            elif event.key == pygame.K_v:
                                if self._blocked_static_upgrade(game, "sell_inventory"):
                                    continue
                                next_state = self._confirm_inventory_sale_marks(game)
                                if next_state:
                                    state = next_state

                            inventory_selected = max(0, min(inventory_selected, len(items) - 1))

                    elif state == "fusion_confirm":
                        if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE, pygame.K_n):
                            state, inventory_selected = self._handle_fusion_confirm_action("fusion_confirm_no", game, inventory_selected)
                        elif event.key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN):
                            fusion_confirm_selected = 1 - fusion_confirm_selected
                        elif event.key in (pygame.K_y,):
                            state, inventory_selected = self._handle_fusion_confirm_action("fusion_confirm_yes", game, inventory_selected)
                        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                            action = "fusion_confirm_yes" if fusion_confirm_selected == 0 else "fusion_confirm_no"
                            state, inventory_selected = self._handle_fusion_confirm_action(action, game, inventory_selected)

                    elif state == "stamp_fusion_confirm":
                        if self._menu_back_pressed():
                            state, inventory_selected = self._handle_stamp_fusion_confirm_action("stamp_fusion_confirm_no", game, inventory_selected)
                        elif self._menu_left_pressed() or self._menu_right_pressed() or self._menu_up_pressed() or self._menu_down_pressed():
                            fusion_confirm_selected = 1 - fusion_confirm_selected
                        elif self._menu_confirm_pressed():
                            action = "stamp_fusion_confirm_yes" if fusion_confirm_selected == 0 else "stamp_fusion_confirm_no"
                            state, inventory_selected = self._handle_stamp_fusion_confirm_action(action, game, inventory_selected)

                    elif state == "stamp_fusion_confirm":
                        if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE, pygame.K_n):
                            state, inventory_selected = self._handle_stamp_fusion_confirm_action("stamp_fusion_confirm_no", game, inventory_selected)
                        elif event.key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN):
                            fusion_confirm_selected = 1 - fusion_confirm_selected
                        elif event.key in (pygame.K_y,):
                            state, inventory_selected = self._handle_stamp_fusion_confirm_action("stamp_fusion_confirm_yes", game, inventory_selected)
                        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                            action = "stamp_fusion_confirm_yes" if fusion_confirm_selected == 0 else "stamp_fusion_confirm_no"
                            state, inventory_selected = self._handle_stamp_fusion_confirm_action(action, game, inventory_selected)

                    elif state == "point_confirm":
                        self._refresh_point_confirm_quantity(game)
                        if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE, pygame.K_n):
                            self._clear_point_confirm_quantity()
                            state = self.point_confirm_return
                        elif self._point_confirm_has_quantity() and event.key == pygame.K_LEFT:
                            self._adjust_point_confirm_quantity(-1, game)
                        elif self._point_confirm_has_quantity() and event.key == pygame.K_RIGHT:
                            self._adjust_point_confirm_quantity(1, game)
                        elif event.key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN):
                            self.point_confirm_selected = 1 - self.point_confirm_selected
                        elif event.key in (pygame.K_y,):
                            state = self._handle_point_confirm_action(self.point_confirm_action, game, self.point_confirm_return)
                        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                            if self.point_confirm_selected == 0:
                                state = self._handle_point_confirm_action(self.point_confirm_action, game, self.point_confirm_return)
                            else:
                                self._clear_point_confirm_quantity()
                                state = self.point_confirm_return

                    elif state == "rng_result":
                        if event.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE, pygame.K_e, pygame.K_y):
                            state = "playing"

                    elif state == "game_over":
                        if event.key == pygame.K_r:
                            game.restart()
                            record_pending_game_over = False
                            self.record_name_text = ""
                            state = "playing"
                        elif event.key in (pygame.K_c, pygame.K_t):
                            character_selected = self._current_character_index(game)
                            character_selected_2 = self._current_character_index(game, 1)
                            multiplayer_selected = game.multiplayer
                            character_select_player = 0
                            character_cancel_state = "game_over"
                            state = "character_select"
                        elif event.key == pygame.K_ESCAPE:
                            running = False
                            return_action = "menu"

            ui.sync_menu_windows(state)
            if state == "playing":
                p1_controls = self._player_one_controls(controls) if game.multiplayer else controls
                move = self._movement_vector(p1_controls)
                move_2 = self._joystick_movement_vector() if game.multiplayer else None
                
                distortion = getattr(game, "olympus_distortion_type", "")
                if distortion == "invert_keyboard":
                    move = move * -1
                    if move_2: move_2 = move_2 * -1
                elif distortion == "invert_mouse":
                    if game.players and not game.players[0].is_down:
                        aim_dir = (aim_world - game.players[0].pos)
                        aim_world = game.players[0].pos - aim_dir
                    if game.multiplayer and game.player2 and not game.player2.is_down and p2_aim_world:
                        aim_dir2 = (p2_aim_world - game.player2.pos)
                        p2_aim_world = game.player2.pos - aim_dir2

                game.update(dt, move, aim_world, move_2, p2_aim_world)
                state, inventory_tab, inventory_selected, skill_selected, stat_shop_selected, skills_return_state, stat_shop_return_state = handle_altar_menu_transition(
                    game,
                    state,
                    inventory_tab,
                    inventory_selected,
                    skill_selected,
                    stat_shop_selected,
                    skills_return_state,
                    stat_shop_return_state,
                    special_holding,
                    special_hold_triggered,
                    special_combo_checked,
                    combo_holding,
                    combo_hold_triggered,
                )
                if game.level_up_pending:
                    state = "upgrade"
                    upgrade_selected = 0
                elif game.game_over:
                    if not record_pending_game_over and qualifies(total_score(game)):
                        record_pending_game_over = True
                        self.record_name_text = ""
                        state = "record_name"
                    else:
                        state = "game_over"
                    game_over_selected = 0
                selections = {
                    "start": start_selected,
                    "pause": pause_selected,
                    "upgrade": upgrade_selected,
                    "inventory": inventory_selected,
                    "construction": construction_selected,
                    "skill": skill_selected,
                    "settings": settings_selected,
                    "settings_slot": settings_slot,
                    "fusion_confirm": fusion_confirm_selected,
                    "game_over": game_over_selected,
                    "stat_shop": stat_shop_selected,
                    "coin_shop": coin_shop_selected,
                    "character_unlock": character_unlock_selected,
                    "character_upgrade": character_upgrade_selected,
                    "mode": mode_selected,
                    "multiplayer": multiplayer_selected,
                    "character": character_selected,
                    "character_2": character_selected_2,
                    "character_player": character_select_player,
                    "encyclopedia": encyclopedia_selected,
                    "encyclopedia_category": encyclopedia_category,
                    "encyclopedia_query": encyclopedia_query,
                }
                button_rects, selections, inventory_tab = render_state(
                    self, ui, game, state, mouse_pos, aim_pos, aim_mode, p2_aim_screen, dt,
                    controls, selections, fullscreen, capture_binding, inventory_tab
                )
                start_selected = selections["start"]
                pause_selected = selections["pause"]
                upgrade_selected = selections["upgrade"]
                inventory_selected = selections["inventory"]
                construction_selected = selections["construction"]
                skill_selected = selections["skill"]
                settings_selected = selections["settings"]
                game_over_selected = selections["game_over"]
                stat_shop_selected = selections["stat_shop"]
                coin_shop_selected = selections["coin_shop"]
                character_unlock_selected = selections["character_unlock"]
                character_upgrade_selected = selections["character_upgrade"]
                encyclopedia_selected = selections["encyclopedia"]
                present_virtual_screen(self.virtual_screen)
                continue

            else:
                selections = {
                    "start": start_selected,
                    "pause": pause_selected,
                    "upgrade": upgrade_selected,
                    "inventory": inventory_selected,
                    "construction": construction_selected,
                    "skill": skill_selected,
                    "settings": settings_selected,
                    "settings_slot": settings_slot,
                    "fusion_confirm": fusion_confirm_selected,
                    "game_over": game_over_selected,
                    "stat_shop": stat_shop_selected,
                    "coin_shop": coin_shop_selected,
                    "character_unlock": character_unlock_selected,
                    "character_upgrade": character_upgrade_selected,
                    "mode": mode_selected,
                    "multiplayer": multiplayer_selected,
                    "character": character_selected,
                    "character_2": character_selected_2,
                    "character_player": character_select_player,
                    "encyclopedia": encyclopedia_selected,
                    "encyclopedia_category": encyclopedia_category,
                    "encyclopedia_query": encyclopedia_query,
                }
                button_rects, selections, inventory_tab = render_state(
                    self, ui, game, state, mouse_pos, aim_pos, aim_mode, p2_aim_screen, dt,
                    controls, selections, fullscreen, capture_binding, inventory_tab
                )
                start_selected = selections["start"]
                pause_selected = selections["pause"]
                upgrade_selected = selections["upgrade"]
                inventory_selected = selections["inventory"]
                construction_selected = selections["construction"]
                skill_selected = selections["skill"]
                settings_selected = selections["settings"]
                game_over_selected = selections["game_over"]
                stat_shop_selected = selections["stat_shop"]
                coin_shop_selected = selections["coin_shop"]
                character_unlock_selected = selections["character_unlock"]
                character_upgrade_selected = selections["character_upgrade"]
                encyclopedia_selected = selections["encyclopedia"]
                present_virtual_screen(self.virtual_screen)

        pygame.display.quit()
        pygame.joystick.quit()
        return return_action























        
        




























def main():
    app = SobrevivenciaGame()
    app.run()


if __name__ == "__main__":
    main()

