import pygame
if __package__:
    from ..data.constants import *
    from ..data.items import MAX_ITEM_LEVEL
else:
    from Sobrevivencia.data.constants import *
    from Sobrevivencia.data.items import MAX_ITEM_LEVEL

class MenuController:
    def _refresh_point_confirm_quantity(self, game):
        action = getattr(self, "point_confirm_action", None)
        marker = repr(action)
        if getattr(self, "_point_confirm_action_marker", None) != marker:
            self.point_confirm_quantity = 1
            self._point_confirm_action_marker = marker

        max_quantity = self._point_confirm_max_quantity(action, game)
        self.point_confirm_max_quantity = max(1, max_quantity)
        self.point_confirm_quantity = max(
            1,
            min(getattr(self, "point_confirm_quantity", 1), self.point_confirm_max_quantity),
        )
        self.point_confirm_total_cost = self._point_confirm_total_cost(
            action,
            game,
            self.point_confirm_quantity,
        )

    def _point_confirm_max_quantity(self, action, game):
        if not action:
            return 1

        act = action[0]
        if act == "buy_shop_item":
            return 1

        if act == "upgrade_inventory":
            if not self._altar_allows_action(game, act):
                return 1
            inv = game.get_inventory(game.menu_player_index)
            item = inv.get(action[1])
            if item is None or item.level >= MAX_ITEM_LEVEL:
                return 1
            cost = 7 if item.is_relic else (3 if item.is_hybrid else 1)
            return max(1, min(MAX_ITEM_LEVEL - item.level, inv.points // cost))

        if act == "upgrade_skill":
            if not self._altar_allows_action(game, act):
                return 1
            player = game.get_player(game.menu_player_index)
            inv = game.get_inventory(game.menu_player_index)
            key = action[1]
            level = player.passives.get(key, 0)
            if level >= 10:
                return 1

            points = inv.points
            quantity = 0
            while level + quantity < 10:
                step_cost = self._skill_step_cost(game, key, level + quantity)
                if points < step_cost:
                    break
                points -= step_cost
                quantity += 1
            return max(1, quantity)

        return 1

    def _point_confirm_total_cost(self, action, game, quantity):
        if not action:
            return getattr(self, "point_confirm_cost", 0)

        act = action[0]
        if act in ("buy_shop_item", "upgrade_inventory"):
            return getattr(self, "point_confirm_cost", 0) * quantity

        if act == "upgrade_skill":
            player = game.get_player(game.menu_player_index)
            key = action[1]
            level = player.passives.get(key, 0)
            return sum(self._skill_step_cost(game, key, level + step) for step in range(quantity))

        return getattr(self, "point_confirm_cost", 0)

    def _skill_step_cost(self, game, key, level):
        player = game.get_player(game.menu_player_index)
        data = CHARACTERS[player.char_class]["passives"].get(key, {})
        is_special = data.get("category") == "Especial"
        if level <= 0:
            return SPECIAL_SKILL_UNLOCK_COST if is_special else SKILL_UNLOCK_COST
        return SPECIAL_SKILL_UPGRADE_COST if is_special else SKILL_UPGRADE_COST

    def _altar_allows_action(self, game, act):
        altar = getattr(game, "active_altar", None)
        if altar is None:
            return False
        return (
            (act == "upgrade_inventory" and altar.kind == "weapon_altar")
            or (act == "upgrade_skill" and altar.kind == "skill_altar")
            or (act == "purchase_stat_shop" and altar.kind == "stat_altar")
        )

    def _blocked_static_upgrade(self, game, act):
        if self._altar_allows_action(game, act):
            return False
        names = {
            "upgrade_inventory": "Altar de Armas",
            "upgrade_skill": "Altar de Habilidades",
            "purchase_stat_shop": "Altar de Status",
        }
        game.message = f"Upgrade bloqueado no menu nativo. Encontre um {names.get(act, 'Altar')}."
        return True

    def _inventory_step_cost(self, item):
        return 7 if item.is_relic else (3 if item.is_hybrid else 1)

    def _inventory_total_cost(self, item, levels):
        return self._inventory_step_cost(item) * max(0, levels)

    def _skill_total_cost(self, game, key, levels):
        player = game.get_player(game.menu_player_index)
        start_level = player.passives.get(key, 0)
        return sum(self._skill_step_cost(game, key, start_level + step) for step in range(max(0, levels)))

    def _apply_inventory_upgrade_levels(self, game, key, levels, spend):
        inv = game.get_inventory(game.menu_player_index)
        item = inv.get(key)
        if item is None or levels <= 0:
            return 0
        original_points = inv.points
        inv.points = 999999
        applied = 0
        for _ in range(levels):
            if not game.upgrade_inventory_item(key):
                break
            applied += 1
        inv.points = max(0, original_points - spend)
        return applied

    def _apply_skill_upgrade_levels(self, game, key, levels, spend):
        inv = game.get_inventory(game.menu_player_index)
        original_points = inv.points
        inv.points = 999999
        applied = 0
        for _ in range(levels):
            if not game.upgrade_skill(key):
                break
            applied += 1
        inv.points = max(0, original_points - spend)
        return applied

    def _apply_altar_mass_upgrade(self, game, action, quantity, result):
        import math
        act = action[0]
        inv = game.get_inventory(game.menu_player_index)
        player = game.get_player(game.menu_player_index)
        requested_levels = max(1, quantity)

        if act == "upgrade_inventory":
            item = inv.get(action[1])
            if item is None:
                game.message = "Item nao encontrado."
                return False
            available = max(0, MAX_ITEM_LEVEL - item.level)
            requested_levels = min(requested_levels, available)
            if requested_levels <= 0:
                game.message = "Item ja esta no nivel maximo."
                return False
            requested_cost = self._inventory_total_cost(item, requested_levels)
            if result == "super":
                levels = min(available, requested_levels + 1)
                spend = math.ceil(requested_cost * 0.75)
            elif result == "sucesso":
                levels = requested_levels
                spend = requested_cost
            elif result == "parcial":
                levels = self._partial_levels(game, requested_levels)
                spend = self._inventory_total_cost(item, levels)
            else:
                levels = 0
                spend = 0
            applied = self._apply_inventory_upgrade_levels(game, action[1], levels, spend)
            if applied > 0 and result == "super":
                item.timers["altar_glow"] = 18.0
            return self._finish_rng_message(game, result, "Item", applied, spend, requested_cost)

        if act == "upgrade_skill":
            key = action[1]
            current = player.passives.get(key, 0)
            available = max(0, 10 - current)
            requested_levels = min(requested_levels, available)
            if requested_levels <= 0:
                game.message = "Skill ja esta no nivel maximo."
                return False
            requested_cost = self._skill_total_cost(game, key, requested_levels)
            if result == "super":
                levels = min(available, requested_levels + 1)
                spend = math.ceil(requested_cost * 0.75)
            elif result == "sucesso":
                levels = requested_levels
                spend = requested_cost
            elif result == "parcial":
                levels = self._partial_levels(game, requested_levels)
                spend = self._skill_total_cost(game, key, levels)
            else:
                levels = 0
                spend = 0
            applied = self._apply_skill_upgrade_levels(game, key, levels, spend)
            return self._finish_rng_message(game, result, "Skill", applied, spend, requested_cost)

        if act == "purchase_stat_shop":
            if result == "falha":
                game.message = "FALHA INSTAVEL! Status nao mudou e nenhum ponto foi gasto."
                game.last_rng_result = {
                    "result": "falha",
                    "label": "Status",
                    "applied": 0,
                    "spend": 0,
                    "requested_cost": self.point_confirm_cost,
                    "refund": 0,
                    "message": game.message
                }
                return True
            if result == "super":
                offer = game.stat_shop_offers[action[1]]
                original = [effect["value"] for effect in offer["effects"]]
                for effect in offer["effects"]:
                    effect["value"] *= 1.25
                ok = game.purchase_stat_shop_offer(action[1])
                for effect, value in zip(offer["effects"], original):
                    effect["value"] = value
                if ok:
                    game.stat_shop_cooldown = 30.0
                    game.message = "SUPER SUCESSO! Status aprimorado com bonus de 25%."
                    game.last_rng_result = {
                        "result": "super",
                        "label": "Status",
                        "applied": 1,
                        "spend": self.point_confirm_cost,
                        "requested_cost": self.point_confirm_cost,
                        "refund": 0,
                        "message": game.message
                    }
                return ok
            ok = game.purchase_stat_shop_offer(action[1])
            if ok:
                game.stat_shop_cooldown = 30.0
            if ok and result == "parcial":
                game.message = "SUCESSO PARCIAL! Status aplicado sem bonus adicional."
                game.last_rng_result = {
                    "result": "parcial",
                    "label": "Status",
                    "applied": 1,
                    "spend": self.point_confirm_cost,
                    "requested_cost": self.point_confirm_cost,
                    "refund": 0,
                    "message": game.message
                }
            elif ok:
                game.message = "SUCESSO! Status aprimorado."
                game.last_rng_result = {
                    "result": "sucesso",
                    "label": "Status",
                    "applied": 1,
                    "spend": self.point_confirm_cost,
                    "requested_cost": self.point_confirm_cost,
                    "refund": 0,
                    "message": game.message
                }
            return ok

        return False

    def _partial_levels(self, game, requested_levels):
        if requested_levels <= 1:
            return 1
        return game.random.randint(1, requested_levels - 1)

    def _finish_rng_message(self, game, result, label, applied, spend, requested_cost):
        refund = max(0, requested_cost - spend) if result != "falha" else 0
        if result == "falha":
            game.message = f"FALHA INSTAVEL! {label} nao mudou; pontos preservados; -10% velocidade por 20s."
            game.last_rng_result = {
                "result": result,
                "label": label,
                "applied": 0,
                "spend": spend,
                "requested_cost": requested_cost,
                "refund": 0,
                "message": game.message
            }
            return True
        if applied <= 0:
            return False
        if result == "super":
            game.message = f"SUPER SUCESSO! {label} +{applied} nivel(is), desconto de 25%."
        elif result == "parcial":
            game.message = f"SUCESSO PARCIAL! {label} +{applied}; troco: {refund} pts."
        else:
            game.message = f"SUCESSO! {label} +{applied} nivel(is)."

        game.last_rng_result = {
            "result": result,
            "label": label,
            "applied": applied,
            "spend": spend,
            "requested_cost": requested_cost,
            "refund": refund,
            "message": game.message
        }
        return True

    def _point_confirm_has_quantity(self):
        return getattr(self, "point_confirm_max_quantity", 1) > 1

    def _clear_point_confirm_quantity(self):
        self.point_confirm_quantity = 1
        self.point_confirm_max_quantity = 1
        self.point_confirm_total_cost = getattr(self, "point_confirm_cost", 0)
        self._point_confirm_action_marker = None

    def _adjust_point_confirm_quantity(self, delta, game):
        self._refresh_point_confirm_quantity(game)
        if not self._point_confirm_has_quantity():
            return
        self.point_confirm_quantity = max(
            1,
            min(self.point_confirm_quantity + delta, self.point_confirm_max_quantity),
        )
        self.point_confirm_total_cost = self._point_confirm_total_cost(
            self.point_confirm_action,
            game,
            self.point_confirm_quantity,
        )

    def _handle_point_confirm_choice(self, action, game):
        self._refresh_point_confirm_quantity(game)
        if action == "point_confirm_decrease":
            self._adjust_point_confirm_quantity(-1, game)
            return "point_confirm"
        if action == "point_confirm_increase":
            self._adjust_point_confirm_quantity(1, game)
            return "point_confirm"
        if action == "point_confirm_yes":
            return self._handle_point_confirm_action(self.point_confirm_action, game, self.point_confirm_return)
        if action == "point_confirm_no":
            self._clear_point_confirm_quantity()
            return self.point_confirm_return
        return "point_confirm"

    def _set_display_mode(self, fullscreen, ui):
        attempts = []
        if fullscreen:
            scaled_flag = getattr(pygame, "SCALED", 0)
            if scaled_flag:
                attempts.append((pygame.FULLSCREEN | scaled_flag, True))
            attempts.append((pygame.FULLSCREEN, True))
        else:
            attempts.append((0, False))

        attempts.append((0, False))
        seen = set()
        for flags, applied_fullscreen in attempts:
            if flags in seen:
                continue
            seen.add(flags)
            try:
                if (flags & pygame.FULLSCREEN) and not (flags & getattr(pygame, "SCALED", 0)):
                    screen = pygame.display.set_mode((0, 0), flags)
                else:
                    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), flags)
                return screen, applied_fullscreen
            except pygame.error:
                continue

        return pygame.display.get_surface(), False

    def _handle_point_confirm_action(self, action, game, return_state):
        if not action:
            return return_state
        import math
        act = action[0]
        quantity = getattr(self, "point_confirm_quantity", 1)

        if act in ("upgrade_skill", "upgrade_inventory", "purchase_stat_shop"):
            if self._blocked_static_upgrade(game, act):
                self._clear_point_confirm_quantity()
                return return_state
            p_idx = game.menu_player_index
            rng_res = game.roll_upgrade_rng(p_idx, quantity)
            is_altar = game.active_altar is not None
            ok = self._apply_altar_mass_upgrade(game, action, quantity, rng_res)
            if rng_res == "falha":
                debuffs = getattr(game, "player_debuffs", {})
                debuffs[p_idx] = {"movement_slow_timer": 20.0}
                game.player_debuffs = debuffs
                game.screen_shake = max(game.screen_shake, 12.0)
            elif ok:
                game.screen_shake = max(game.screen_shake, 18.0 if rng_res == "super" else 10.0)
                game.emit_particles(game.get_player(p_idx).pos, count=40 if rng_res == "super" else 22, color="#F59E0B", speed=250)
            game.finish_altar_interaction(destroy=True)
            self._clear_point_confirm_quantity()
            return "rng_result" if is_altar else "playing"
        
        # --- Altar (RNG) Upgrades ---
        if game.active_altar is not None and act in ("upgrade_skill", "upgrade_inventory", "purchase_stat_shop"):
            p_idx = game.menu_player_index
            inv = game.get_inventory(p_idx)
            cost = self.point_confirm_cost
            
            # Roll RNG!
            rng_res = game.roll_upgrade_rng(p_idx)
            
            if rng_res == "super":
                # SUPER SUCCESS: +2 levels/upgrades at the cost of 1!
                if act == "upgrade_skill":
                    orig_points = inv.points
                    inv.points = orig_points - cost
                    inv.points = max(inv.points, 9999)
                    
                    s1 = game.upgrade_skill(action[1])
                    s2 = game.upgrade_skill(action[1])
                    
                    inv.points = orig_points - cost
                    game.message = "SUPER SUCESSO! Habilidade aprimorada 2 níveis!"
                    
                elif act == "upgrade_inventory":
                    orig_points = inv.points
                    inv.points = orig_points - cost
                    inv.points = max(inv.points, 9999)
                    
                    s1 = game.upgrade_inventory_item(action[1])
                    s2 = game.upgrade_inventory_item(action[1])
                    
                    inv.points = orig_points - cost
                    game.message = "SUPER SUCESSO! Item aprimorado 2 níveis!"
                    
                elif act == "purchase_stat_shop":
                    offer = game.stat_shop_offers[action[1]]
                    for effect in offer["effects"]:
                        effect["value"] *= 2.0
                    
                    game.purchase_stat_shop_offer(action[1])
                    game.message = "SUPER SUCESSO! Efeitos de status duplicados!"
                
                game.screen_shake = max(game.screen_shake, 18.0)
                game.emit_particles(game.player.pos, count=40, color="#F59E0B", speed=250)
                
            elif rng_res == "sucesso":
                if act == "upgrade_skill":
                    game.upgrade_skill(action[1])
                    game.message = "SUCESSO! Habilidade aprimorada."
                elif act == "upgrade_inventory":
                    game.upgrade_inventory_item(action[1])
                    game.message = "SUCESSO! Item aprimorado."
                elif act == "purchase_stat_shop":
                    game.purchase_stat_shop_offer(action[1])
                    game.message = "SUCESSO! Status aprimorado."
                    
            elif rng_res == "parcial":
                refund = math.ceil(cost * 0.5)
                if act == "upgrade_skill":
                    game.upgrade_skill(action[1])
                elif act == "upgrade_inventory":
                    game.upgrade_inventory_item(action[1])
                elif act == "purchase_stat_shop":
                    game.purchase_stat_shop_offer(action[1])
                
                inv.points += refund
                game.message = f"SUCESSO PARCIAL! Upgrade aplicado e {refund} pontos devolvidos!"
                
            elif rng_res == "falha":
                # Instable Failure: No level, suffered temporary damage, Altar explodes, debuff applied
                debuffs = getattr(game, 'player_debuffs', {})
                debuffs[p_idx] = {"movement_slow_timer": 20.0}
                game.player_debuffs = debuffs
                
                inv.points = max(0, inv.points - cost)
                game.message = "FALHA INSTAVEL! Upgrade falhou, Altar destruído e debuff aplicado!"
                game.screen_shake = max(game.screen_shake, 12.0)
                
                if game.active_altar is not None:
                    game.active_altar.active = False
            
            # Post Altar Action: Destroy Altar and restore time scale
            if game.active_altar is not None:
                game.active_altar.active = False
                game.active_altar = None
            game.time_scale = 1.0
            
            self._clear_point_confirm_quantity()
            return "playing"
            
        # --- Native / Default Upgrades ---
        if act == "roll_stat_shop":
            game.roll_stat_shop()
        elif act == "purchase_stat_shop":
            game.purchase_stat_shop_offer(action[1])
            game.stat_shop_cooldown = 30.0
        elif act == "reroll_stat_shop":
            if game.reroll_stat_shop_offer(action[1]):
                game.stat_shop_rerolls += 1
        elif act == "reroll_stat_shop_sacrifice":
            player = game.get_player(game.menu_player_index)
            if game.reroll_stat_shop_offer(action[1], free=True, allow_second=True):
                player.max_health = max(10, player.max_health - 5)
                player.health = min(player.health, player.max_health)
                game.stat_shop_rerolls += 1
                game.message = "Reroll com Sacrificio de -5 Max HP concluido."
        elif act == "upgrade_skill":
            done = 0
            for _ in range(quantity):
                if not game.upgrade_skill(action[1]):
                    break
                done += 1
            if done > 1:
                game.message = f"Skill aprimorada {done} vezes."
        elif act == "upgrade_inventory":
            done = 0
            for _ in range(quantity):
                if not game.upgrade_inventory_item(action[1]):
                    break
                done += 1
            if done > 1:
                game.message = f"Item aprimorado {done} vezes."
        elif act == "buy_shop_item":
            done = 0
            for _ in range(quantity):
                if not game.buy_shop_item(action[1]):
                    break
                done += 1
            if done > 0:
                game.black_market_cooldown = 60.0
            if done > 1:
                game.message = f"Compra realizada {done} vezes."
        elif act == "transform_inventory":
            inv = game.get_inventory(game.menu_player_index)
            success, msg = inv.attempt_transformation(action[1], game.random)
            game.message = msg
        elif act == "sell_inventory":
            inv = game.get_inventory(game.menu_player_index)
            success, msg = inv.sell_item(action[1])
            game.message = msg
        elif act == "sell_stamp":
            game.sell_stamp(action[1])
        elif act == "buy_relic":
            inv = game.get_inventory(game.menu_player_index)
            relic_source_key = action[1]
            if inv.points >= 50:
                inv.points -= 50
                status, new_item = inv.add_relic(relic_source_key)
                if new_item:
                    game.message = "Reliquia forjada com sucesso!"
                else:
                    game.message = "Erro ao forjar reliquia."
            else:
                game.message = "Pontos insuficientes para forjar reliquia."
        self._clear_point_confirm_quantity()
        return return_state

    def _current_character_index(self, game, player_index=0):
        keys = list(CHARACTERS.keys())
        player = game.get_player(player_index)
        if player.char_class in keys:
            return keys.index(player.char_class)
        return 0

    def _handle_action(self, action, state, game, running, return_action, pause_selected, upgrade_selected):
        if action == "start":
            game.restart()
            state = "playing"
        elif action == "commands":
            state = "commands"
        elif action == "settings":
            state = "settings"
        elif action == "constructions":
            state = "constructions"
        elif action == "skills":
            state = "skills"
        elif action == "stat_shop":
            state = "stat_shop"
        elif action == "change_character":
            state = "character_select"
        elif action == "inventory":
            state = "inventory"
            game.menu_player_index = 0
        elif action == "resume":
            state = "playing"
        elif action == "restart":
            game.restart()
            state = "playing"
        elif action == "menu":
            # "Voltar ao Menu" dentro da partida: retorna ao menu inicial do jogo sem encerrar
            state = "start"
        elif action == "quit":
            # "Fechar": encerra a sessao e retorna ao Arcade
            return_action = "quit"
            running = False
        elif action in game.upgrade_choices:
            game.apply_upgrade(action, game.level_up_player_index)
            upgrade_selected = 0
            state = "playing"
        return state, running, return_action, pause_selected, upgrade_selected

    def _handle_inventory_action(self, action, state, game, selected):
        inv = game.get_inventory(game.menu_player_index)
        raw_items = inv.item_list()
        active_items = [item for item in raw_items if inv.is_active(item.slot_key)]
        reserve_items = [item for item in raw_items if not inv.is_active(item.slot_key)]
        items = active_items + reserve_items
        if action == "resume":
            if game.active_altar is not None:
                game.finish_altar_interaction(destroy=True)
            return "playing", selected

        # -- Ações de Selos (Stamps) --
        if action.startswith("stamp_select:"):
            return state, int(action.split(":", 1)[1])
        if action == "stamp_equip_w1":
            game.equip_stamp("weapon_1", selected)
            return state, selected
        elif action == "stamp_equip_w2":
            game.equip_stamp("weapon_2", selected)
            return state, selected
        elif action == "stamp_unequip":
            game.unequip_stamp(selected)
            return state, 0
        elif action == "stamp_fuse":
            game.setup_stamp_fusion(selected)
            return "stamp_fusion_confirm", selected
        elif action == "stamp_sell":
            player = game.get_player(game.menu_player_index)
            w1 = player.weapon_stamps.get("weapon_1", [])
            w2 = player.weapon_stamps.get("weapon_2", [])
            res_idx = selected - len(w1) - len(w2)
            if res_idx >= 0 and res_idx < len(player.stamp_reserve):
                stamp = player.stamp_reserve[res_idx]
                try:
                    from ...data.stamps import stamp_sell_value
                except:
                    from Sobrevivencia.data.stamps import stamp_sell_value
                val = stamp_sell_value(stamp)
                self.point_confirm_action = ("sell_stamp", selected)
                self.point_confirm_cost = 0
                self.point_confirm_msg = f"Deseja vender este selo por {val} pts?"
                self.point_confirm_return = "inventory"
                self.point_confirm_selected = 1
                return "point_confirm", selected

        # -- Ações de Itens Regulares --
        if action.startswith("item_select:"):
            return state, int(action.split(":", 1)[1])
            
        if not items:
            return state, selected

        selected = min(selected, len(items) - 1)
        slot_key = items[selected].slot_key

        if action == "item_toggle":
            game.toggle_inventory_item(slot_key)
        elif action == "item_upgrade":
            if self._blocked_static_upgrade(game, "upgrade_inventory"):
                return state, selected
            cost = 7 if items[selected].is_relic else (3 if items[selected].is_hybrid else 1)
            if inv.points >= cost:
                self.point_confirm_action = ("upgrade_inventory", slot_key)
                self.point_confirm_cost = cost
                self.point_confirm_msg = f"Deseja gastar {cost} ponto(s) para aprimorar este item?"
                self.point_confirm_return = "inventory"
                self.point_confirm_selected = 1
                return "point_confirm", selected
            else:
                game.message = f"Pontos insuficientes (custa {cost})."
        elif action == "item_fuse":
            game.mark_or_fuse_item(slot_key)
            if game.has_pending_fusion():
                return "fusion_confirm", selected
            selected = min(selected, max(0, len(inv.item_list()) - 1))
        elif action == "item_sell":
            if not inv.is_active(items[selected].slot_key):
                value = inv.get_sell_value(items[selected].slot_key)
                self.point_confirm_action = ("sell_inventory", items[selected].slot_key)
                self.point_confirm_cost = 0  # No cost, we gain points
                self.point_confirm_msg = f"Deseja vender este item por {value} ponto(s)?"
                self.point_confirm_return = "inventory"
                self.point_confirm_selected = 1
                return "point_confirm", selected
            else:
                game.message = "Desequipe o item antes de vende-lo."
        return state, selected

    def _handle_stat_shop_action(self, action, game, return_state):
        inv = game.get_inventory(game.menu_player_index)
        if action == "stat_shop_back":
            if game.active_altar is not None:
                game.finish_altar_interaction(destroy=True)
            return return_state
        if action == "stat_shop_roll":
            if getattr(game, "stat_shop_cooldown", 0.0) > 0:
                game.message = f"Loja de Status bloqueada por {game.stat_shop_cooldown:.0f}s."
                return "stat_shop"
            if inv.points >= STAT_SHOP_ROLL_COST:
                self.point_confirm_action = ("roll_stat_shop",)
                self.point_confirm_cost = STAT_SHOP_ROLL_COST
                self.point_confirm_msg = f"Deseja gastar {STAT_SHOP_ROLL_COST} ponto(s) para abrir a loja?"
                self.point_confirm_return = "stat_shop"
                self.point_confirm_selected = 1
                return "point_confirm"
            else:
                game.message = f"Pontos insuficientes (custa {STAT_SHOP_ROLL_COST})."
                return "stat_shop"
        if action.startswith("stat_shop_buy:"):
            if self._blocked_static_upgrade(game, "purchase_stat_shop"):
                return "stat_shop"
            idx = int(action.split(":", 1)[1])
            cost = game.stat_shop_offers[idx]["cost"]
            if inv.points >= cost:
                self.point_confirm_action = ("purchase_stat_shop", idx)
                self.point_confirm_cost = cost
                self.point_confirm_msg = f"Deseja gastar {cost} ponto(s) para comprar esta melhoria?"
                self.point_confirm_return = "stat_shop"
                self.point_confirm_selected = 1
                return "point_confirm"
            else:
                game.message = f"Pontos insuficientes (custa {cost})."
                return "stat_shop"
        if action.startswith("stat_shop_reroll:"):
            idx = int(action.split(":", 1)[1])
            used = getattr(game, "stat_shop_offer_rerolls", {}).get(idx, 0)
            if used >= 1:
                self.point_confirm_action = ("reroll_stat_shop_sacrifice", idx)
                self.point_confirm_cost = 0
                self.point_confirm_msg = "AVISO: sacrificar permanentemente -5 Max HP para novo reroll desta oferta?"
                self.point_confirm_return = "stat_shop"
                self.point_confirm_selected = 1
                return "point_confirm"
            if inv.points >= STAT_SHOP_REROLL_COST:
                self.point_confirm_action = ("reroll_stat_shop", idx)
                self.point_confirm_cost = STAT_SHOP_REROLL_COST
                self.point_confirm_msg = f"Deseja gastar {STAT_SHOP_REROLL_COST} ponto(s) para trocar esta oferta?"
                self.point_confirm_return = "stat_shop"
                self.point_confirm_selected = 1
                return "point_confirm"
            else:
                game.message = f"Pontos insuficientes (custa {STAT_SHOP_REROLL_COST})."
                return "stat_shop"
        return "stat_shop"

    def _handle_construction_action(self, action, selected, game=None):
        if action == "constructions_back":
            return "paused", selected
        if action.startswith("construction_select:"):
            return "constructions", int(action.split(":", 1)[1])
        if action.startswith("constructions_buy_relic:") and game is not None:
            relic_source_key = action.split(":", 1)[1]
            inv = game.get_inventory(game.menu_player_index)
            relic_count = sum(1 for it in inv.items.values() if it.is_relic)
            if relic_count < 3:
                game.message = f"Bloqueado: Requer 3 Reliquias ({relic_count}/3)."
                return "constructions", selected
            if inv.points < 50:
                game.message = "Pontos insuficientes (custa 50)."
                return "constructions", selected
            self.point_confirm_action = ("buy_relic", relic_source_key)
            self.point_confirm_cost = 50
            self.point_confirm_msg = "Deseja gastar 50 ponto(s) para forjar esta Reliquia?"
            self.point_confirm_return = "constructions"
            self.point_confirm_selected = 1
            return "point_confirm", selected
        return "constructions", selected

    def _handle_skill_action(self, action, state, game, selected, return_state):
        keys = list(game.get_player(game.menu_player_index).passives.keys())
        if action == "skills_back":
            if game.active_altar is not None:
                game.finish_altar_interaction(destroy=True)
            return return_state, selected
        if action.startswith("skill_select:"):
            return state, int(action.split(":", 1)[1])
        if action == "skill_upgrade" and keys:
            if self._blocked_static_upgrade(game, "upgrade_skill"):
                return state, selected
            selected = min(selected, len(keys) - 1)
            key = keys[selected]
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
                return "point_confirm", selected
            else:
                game.message = f"Pontos insuficientes (custa {cost})."
        return state, selected

    def _handle_fusion_confirm_action(self, action, game, selected):
        inv = game.get_inventory(game.menu_player_index)
        if action == "fusion_confirm_yes":
            game.confirm_pending_fusion()
        elif action == "fusion_confirm_no":
            game.cancel_pending_fusion()
        selected = min(selected, max(0, len(inv.item_list()) - 1))
        return "inventory", selected

    def _handle_stamp_fusion_confirm_action(self, action, game, selected):
        if action == "stamp_fusion_confirm_yes":
            can_conf, msg = game.can_confirm_stamp_fusion()
            if can_conf:
                game.confirm_stamp_fusion()
                return "inventory", selected
            else:
                game.stamp_fusion_msg = msg
                return "stamp_fusion_confirm", selected
        elif action == "stamp_fusion_confirm_no":
            game.stamp_fusion_materials = []
            return "inventory", selected
        elif action.startswith("stamp_fusion_mat:"):
            mat_idx = int(action.split(":", 1)[1])
            game.toggle_stamp_fusion_material(mat_idx)
            return "stamp_fusion_confirm", selected
        elif action.startswith("stamp_fusion_res:"):
            res_idx = int(action.split(":", 1)[1])
            game.toggle_stamp_fusion_material(res_idx)
            return "stamp_fusion_confirm", selected
        return "stamp_fusion_confirm", selected
