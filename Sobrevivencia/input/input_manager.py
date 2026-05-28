import pygame
from pygame.math import Vector2
import math
if __package__:
    from ..config.config_loader import load_keybinds
    from ..data.constants import *
else:
    from Sobrevivencia.config.config_loader import load_keybinds
    from Sobrevivencia.data.constants import *

class InputManager:
    def _default_bindings(self):
        controls = {action: list(bindings) for action, bindings in DEFAULT_BINDINGS.items()}
        configured = load_keybinds()
        for action, entries in configured.items():
            if action not in controls or not isinstance(entries, list):
                continue
            parsed = [self._binding_from_config(entry) for entry in entries]
            parsed = [binding for binding in parsed if binding is not None]
            if not parsed:
                continue
            controls[action] = parsed[:BINDING_SLOT_COUNT]
            while len(controls[action]) < BINDING_SLOT_COUNT:
                controls[action].append(None)
        return controls

    def _binding_from_config(self, value):
        if not isinstance(value, str) or ":" not in value:
            return None
        source, raw_code = value.split(":", 1)
        source = source.strip().lower()
        raw_code = raw_code.strip().lower()
        if source == "keyboard":
            key_name = raw_code.upper()
            if len(raw_code) == 1 and raw_code.isalnum():
                key_name = raw_code
            key_constant = getattr(pygame, f"K_{key_name}", None)
            if key_constant is not None:
                return ("key", key_constant)
            try:
                return ("key", pygame.key.key_code(raw_code))
            except ValueError:
                return None
        if source == "mouse":
            aliases = {"left": 1, "middle": 2, "right": 3, "wheel_up": 4, "wheel_down": 5}
            if raw_code in aliases:
                return ("mouse", aliases[raw_code])
            if raw_code.isdigit():
                return ("mouse", int(raw_code))
            return None
        if source == "joy_button" and raw_code.isdigit():
            return ("joy_button", int(raw_code))
        return None

    def _poll_events(self, game):
        try:
            return pygame.event.get()
        except (KeyError, SystemError, pygame.error):
            self._recover_joystick_state()
            game.message = "Controle desconectado: entrada reinicializada."
            return []

    def _recover_joystick_state(self):
        self.joysticks = {}
        self._joystick_axis_active = {}
        self._joystick_hat_active = {}
        try:
            pygame.event.clear()
        except (KeyError, SystemError, pygame.error):
            pass
        try:
            pygame.joystick.quit()
        except pygame.error:
            pass
        try:
            pygame.joystick.init()
            self._init_joysticks()
        except pygame.error:
            self.joysticks = {}

    def _init_joysticks(self):
        self.joysticks = {}
        for index in range(pygame.joystick.get_count()):
            self._add_joystick(index)

    def _apply_default_joystick_bindings(self, controls):
        for action, binding in JOYSTICK_DEFAULT_BINDINGS.items():
            bindings = controls.setdefault(action, [])
            while len(bindings) < BINDING_SLOT_COUNT:
                bindings.append(None)
            if binding not in bindings and bindings[BINDING_SLOT_COUNT - 1] is None:
                bindings[BINDING_SLOT_COUNT - 1] = binding

    def _add_joystick(self, device_index):
        try:
            joystick = pygame.joystick.Joystick(device_index)
            joystick.init()
            instance_id = joystick.get_instance_id()
            self.joysticks[instance_id] = joystick
        except pygame.error:
            return

    def _remove_joystick(self, instance_id):
        joystick = self.joysticks.pop(instance_id, None)
        self._joystick_axis_active = {
            key: binding for key, binding in self._joystick_axis_active.items() if key[0] != instance_id
        }
        self._joystick_hat_active = {
            key: bindings for key, bindings in self._joystick_hat_active.items() if key[0] != instance_id
        }
        if joystick is not None:
            try:
                joystick.quit()
            except pygame.error:
                pass

    def _joystick_count(self):
        return len(getattr(self, "joysticks", {}))

    def _joystick_status_message(self):
        count = self._joystick_count()
        if count == 1:
            return "Controle detectado: Single-Player ou Coop Local disponiveis."
        if count > 1:
            return f"{count} controles detectados: Coop Local disponivel."
        return "Controle desconectado."

    def _prepare_input_event(self, event):
        self._event_pressed_bindings = []
        self._event_released_bindings = []

        if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN, pygame.JOYBUTTONDOWN):
            binding = self._binding_from_event(event)
            if binding is not None:
                self._event_pressed_bindings.append(binding)
            return

        if event.type in (pygame.KEYUP, pygame.MOUSEBUTTONUP, pygame.JOYBUTTONUP):
            binding = self._binding_from_event(event)
            if binding is not None:
                self._event_released_bindings.append(binding)
            return

        if event.type == pygame.JOYAXISMOTION:
            device_id = self._joystick_event_device_id(event)
            key = (device_id, event.axis)
            previous = self._joystick_axis_active.get(key)
            current = self._axis_binding(event.axis, event.value)
            if previous != current:
                if previous is not None:
                    self._event_released_bindings.append(previous)
                if current is not None:
                    self._event_pressed_bindings.append(current)
                    self._joystick_axis_active[key] = current
                else:
                    self._joystick_axis_active.pop(key, None)
            return

        if event.type == pygame.JOYHATMOTION:
            device_id = self._joystick_event_device_id(event)
            key = (device_id, event.hat)
            previous = self._joystick_hat_active.get(key, set())
            current = set(self._hat_bindings(event.hat, event.value))
            for binding in previous - current:
                self._event_released_bindings.append(binding)
            for binding in current - previous:
                self._event_pressed_bindings.append(binding)
            if current:
                self._joystick_hat_active[key] = current
            else:
                self._joystick_hat_active.pop(key, None)

    def _joystick_event_device_id(self, event):
        return getattr(event, "instance_id", getattr(event, "joy", 0))

    def _axis_binding(self, axis, value):
        if value <= -JOYSTICK_DEADZONE:
            return ("joy_axis", axis, -1)
        if value >= JOYSTICK_DEADZONE:
            return ("joy_axis", axis, 1)
        return None

    def _hat_bindings(self, hat, value):
        x, y = value
        bindings = []
        if x < 0:
            bindings.append(("joy_hat", hat, -1, 0))
        elif x > 0:
            bindings.append(("joy_hat", hat, 1, 0))
        if y < 0:
            bindings.append(("joy_hat", hat, 0, -1))
        elif y > 0:
            bindings.append(("joy_hat", hat, 0, 1))
        return bindings

    def _pressed_has(self, *bindings):
        return any(binding in self._event_pressed_bindings for binding in bindings)

    def _menu_up_pressed(self):
        return self._pressed_has(("joy_axis", 1, -1), ("joy_hat", 0, 0, 1), ("key", pygame.K_UP), ("key", pygame.K_w))

    def _menu_down_pressed(self):
        return self._pressed_has(("joy_axis", 1, 1), ("joy_hat", 0, 0, -1), ("key", pygame.K_DOWN), ("key", pygame.K_s))

    def _menu_left_pressed(self):
        return self._pressed_has(("joy_axis", 0, -1), ("joy_hat", 0, -1, 0), ("key", pygame.K_LEFT), ("key", pygame.K_a))

    def _menu_right_pressed(self):
        return self._pressed_has(("joy_axis", 0, 1), ("joy_hat", 0, 1, 0), ("key", pygame.K_RIGHT), ("key", pygame.K_d))

    def _menu_confirm_pressed(self):
        return self._pressed_has(("joy_button", 0), ("joy_button", 7), ("key", pygame.K_RETURN), ("key", pygame.K_SPACE))

    def _menu_back_pressed(self):
        return self._pressed_has(("joy_button", 1), ("key", pygame.K_ESCAPE), ("key", pygame.K_BACKSPACE))

    def _menu_x_pressed(self):
        return self._pressed_has(("joy_button", 2), ("key", pygame.K_x), ("key", pygame.K_u))

    def _menu_y_pressed(self):
        return self._pressed_has(("joy_button", 3), ("key", pygame.K_y))

    def _menu_l1_pressed(self):
        return self._pressed_has(("joy_button", 4), ("key", pygame.K_q))

    def _menu_r1_pressed(self):
        return self._pressed_has(("joy_button", 5), ("key", pygame.K_e))

    def _menu_l3_pressed(self):
        return self._pressed_has(("joy_button", 8), ("key", pygame.K_p))

    def _joystick_aim_vector(self):
        best = Vector2()
        best_strength = JOYSTICK_AIM_DEADZONE * JOYSTICK_AIM_DEADZONE
        for joystick in getattr(self, "joysticks", {}).values():
            try:
                pair = self._right_stick_axes(joystick)
                if pair is None:
                    continue
                x_axis, y_axis = pair
                vector = Vector2(joystick.get_axis(x_axis), joystick.get_axis(y_axis))
            except (KeyError, IndexError, pygame.error):
                continue
            strength = vector.length_squared()
            if strength > best_strength:
                best = vector
                best_strength = strength
        if best.length_squared() > 1:
            best = best.normalize()
        return best

    def _right_stick_axes(self, joystick):
        try:
            axis_count = joystick.get_numaxes()
        except pygame.error:
            return None
        if axis_count >= 6:
            return 2, 3
        if axis_count >= 5:
            return 3, 4
        if axis_count >= 4:
            return 2, 3
        return None

    def _aim_screen_pos(self, game, direction):
        return self._aim_screen_pos_for(game, game.player, direction)

    def _aim_screen_pos_for(self, game, player, direction):
        if direction.length_squared() <= 0:
            direction = Vector2(player.last_move_dir)
        if direction.length_squared() <= 0:
            direction = Vector2(1, 0)
        player_screen = Vector2(
            player.pos.x - game.camera.x,
            player.pos.y - game.camera.y,
        )
        aim_pos = player_screen + direction.normalize() * JOYSTICK_AIM_DISTANCE
        margin = 18
        aim_pos.x = max(margin, min(SCREEN_WIDTH - margin, aim_pos.x))
        aim_pos.y = max(margin, min(SCREEN_HEIGHT - margin, aim_pos.y))
        return int(aim_pos.x), int(aim_pos.y)

    def _binding_from_event(self, event):
        if event.type in (pygame.KEYDOWN, pygame.KEYUP):
            return ("key", event.key)
        if event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
            return ("mouse", event.button)
        if event.type in (pygame.JOYBUTTONDOWN, pygame.JOYBUTTONUP):
            return ("joy_button", event.button)
        if event.type == pygame.JOYAXISMOTION:
            return self._axis_binding(event.axis, event.value)
        if event.type == pygame.JOYHATMOTION:
            bindings = self._hat_bindings(event.hat, event.value)
            return bindings[0] if bindings else None
        return None

    def _action_pressed(self, event, controls, action):
        return any(binding in controls.get(action, []) for binding in self._event_pressed_bindings)

    def _action_released(self, event, controls, action):
        return any(binding in controls.get(action, []) for binding in self._event_released_bindings)

    def _action_currently_active(self, controls, action):
        keys = pygame.key.get_pressed()
        try:
            mouse_buttons = pygame.mouse.get_pressed(5)
        except TypeError:
            mouse_buttons = pygame.mouse.get_pressed()
        return any(self._binding_active(binding, keys, mouse_buttons) for binding in controls.get(action, []))

    def _binding_active(self, binding, keys, mouse_buttons):
        if binding is None:
            return False
        source = binding[0]
        code = binding[1] if len(binding) > 1 else None
        if source == "key":
            try:
                return bool(keys[code])
            except (IndexError, KeyError):
                return False
        if source == "mouse":
            index = code - 1
            return 0 <= index < len(mouse_buttons) and bool(mouse_buttons[index])
        if source == "joy_button":
            for joystick in getattr(self, "joysticks", {}).values():
                try:
                    if code < joystick.get_numbuttons() and joystick.get_button(code):
                        return True
                except pygame.error:
                    continue
            return False
        if source == "joy_axis":
            axis, direction = binding[1], binding[2]
            for joystick in getattr(self, "joysticks", {}).values():
                try:
                    if axis >= joystick.get_numaxes():
                        continue
                    value = joystick.get_axis(axis)
                    if direction < 0 and value <= -JOYSTICK_DEADZONE:
                        return True
                    if direction > 0 and value >= JOYSTICK_DEADZONE:
                        return True
                except pygame.error:
                    continue
            return False
        if source == "joy_hat":
            hat, x_dir, y_dir = binding[1], binding[2], binding[3]
            for joystick in getattr(self, "joysticks", {}).values():
                try:
                    if hat >= joystick.get_numhats():
                        continue
                    x, y = joystick.get_hat(hat)
                    if x_dir and x == x_dir:
                        return True
                    if y_dir and y == y_dir:
                        return True
                except pygame.error:
                    continue
            return False
        return False

    def _control_index(self, action):
        for index, (action_key, _label) in enumerate(CONTROL_ACTIONS):
            if action_key == action:
                return index
        return 0

    def _binding_label(self, binding):
        if binding is None:
            return "Nao definido"
        source = binding[0]
        code = binding[1] if len(binding) > 1 else None
        if source == "mouse":
            names = {
                1: "Mouse esquerdo",
                2: "Mouse meio",
                3: "Mouse direito",
                4: "Roda cima",
                5: "Roda baixo",
            }
            return names.get(code, f"Mouse {code}")
        if source == "joy_button":
            xbox_buttons = {
                0: "Controle A",
                1: "Controle B",
                2: "Controle X",
                3: "Controle Y",
                4: "LB",
                5: "RB",
                6: "Back",
                7: "Start",
                8: "L3",
                9: "R3",
                10: "Guide",
            }
            return xbox_buttons.get(code, f"Controle B{code}")
        if source == "joy_axis":
            axis, direction = binding[1], binding[2]
            side = "neg." if direction < 0 else "pos."
            return f"Analogico {axis} {side}"
        if source == "joy_hat":
            hat, x_dir, y_dir = binding[1], binding[2], binding[3]
            if y_dir > 0:
                side = "cima"
            elif y_dir < 0:
                side = "baixo"
            elif x_dir < 0:
                side = "esq."
            else:
                side = "dir."
            return f"D-pad {hat} {side}"

        key_names = {
            pygame.K_ESCAPE: "Esc",
            pygame.K_SPACE: "Espaco",
            pygame.K_TAB: "Tab",
            pygame.K_RETURN: "Enter",
            pygame.K_KP_ENTER: "Enter num.",
            pygame.K_UP: "Seta cima",
            pygame.K_DOWN: "Seta baixo",
            pygame.K_LEFT: "Seta esq.",
            pygame.K_RIGHT: "Seta dir.",
            pygame.K_LSHIFT: "Shift esq.",
            pygame.K_RSHIFT: "Shift dir.",
            pygame.K_BACKSPACE: "Backspace",
            pygame.K_F11: "F11",
        }
        if code in key_names:
            return key_names[code]
        name = pygame.key.name(code)
        return name.upper() if len(name) == 1 else name.title()

    def _binding_combo(self, controls, action):
        labels = [self._binding_label(binding) for binding in controls.get(action, []) if binding is not None]
        return " / ".join(labels) if labels else "Nao definido"

    def _control_rows(self, controls):
        rows = []
        for action, label in CONTROL_ACTIONS:
            bindings = list(controls.get(action, []))
            while len(bindings) < BINDING_SLOT_COUNT:
                bindings.append(None)
            rows.append({
                "action": action,
                "label": label,
                "bindings": [self._binding_label(bindings[slot]) for slot in range(BINDING_SLOT_COUNT)],
            })
        return rows

    def _command_lines(self, controls):
        return [
            f"Mover cima/baixo: {self._binding_combo(controls, 'move_up')} | {self._binding_combo(controls, 'move_down')}",
            f"Mover esquerda/direita: {self._binding_combo(controls, 'move_left')} | {self._binding_combo(controls, 'move_right')}",
            "Mouse: direcao dos tiros e golpes automaticos",
            f"{self._binding_combo(controls, 'toggle_weapon')}: alternar entre projetil e espada",
            f"{self._binding_combo(controls, 'dash')}: dash com recarga e invulnerabilidade curta",
            f"{self._binding_combo(controls, 'special')}: especial normal (toque)",
            f"{self._binding_combo(controls, 'combo_special')}: Suprema - segure com as duas barras cheias",
            f"{self._binding_combo(controls, 'inventory')}: abre inventario de itens passivos",
            f"{self._binding_combo(controls, 'skills')}: abre Gerenciamento de Skills",
            f"{self._binding_combo(controls, 'stat_shop')}: abre Loja de Status",
            f"{self._binding_combo(controls, 'settings')}: configuracoes da sessao",
            f"{self._binding_combo(controls, 'fullscreen')}: alternar tela cheia",
            "Controle Xbox: analogico esquerdo move, A confirma/dash, B volta, LB loja, RB skills, Start pausa.",
            "Joystick: remapeie botoes, eixos e D-pad em Configuracoes.",
            "Armas de distancia usam pente e reserva de municao.",
            "No Game Over, C ou T abre a troca de personagem.",
        ]

    def _movement_vector(self, controls):
        keys = pygame.key.get_pressed()
        try:
            mouse_buttons = pygame.mouse.get_pressed(5)
        except TypeError:
            mouse_buttons = pygame.mouse.get_pressed()
        x = 0
        y = 0
        if any(self._binding_active(binding, keys, mouse_buttons) for binding in controls.get("move_left", [])):
            x -= 1
        if any(self._binding_active(binding, keys, mouse_buttons) for binding in controls.get("move_right", [])):
            x += 1
        if any(self._binding_active(binding, keys, mouse_buttons) for binding in controls.get("move_up", [])):
            y -= 1
        if any(self._binding_active(binding, keys, mouse_buttons) for binding in controls.get("move_down", [])):
            y += 1
        return Vector2(x, y)

    def _player_one_controls(self, controls):
        filtered = {}
        for action, bindings in controls.items():
            filtered[action] = [binding for binding in bindings if binding is None or binding[0] in ("key", "mouse")]
        return filtered

    def _joystick_movement_vector(self):
        x = 0.0
        y = 0.0
        for joystick in getattr(self, "joysticks", {}).values():
            try:
                if joystick.get_numaxes() >= 2:
                    x = joystick.get_axis(0)
                    y = joystick.get_axis(1)
                    break
            except pygame.error:
                continue
        if abs(x) < JOYSTICK_AIM_DEADZONE:
            x = 0
        if abs(y) < JOYSTICK_AIM_DEADZONE:
            y = 0
        return Vector2(x, y)

