from pygame.math import Vector2
import random
import math
if __package__:
    from ...data.constants import *
    from ..entities import Drop
    from ...data.items import item_display_name, RELIC_DEFINITIONS
    from ...data.stamps import (
        ALL_DROPPABLE_STAMP_KEYS,
        FUNCTIONAL_STAMP_KEYS,
        MAX_STAMP_LEVEL,
        Stamp,
        stamp_display_name,
        stamp_sell_value,
    )
    from .buff_applicator import recalc_item_buffs, ensure_item_bonus_fields
else:
    from Sobrevivencia.data.constants import *
    from Sobrevivencia.core.entities import Drop
    from Sobrevivencia.data.items import item_display_name, RELIC_DEFINITIONS
    from Sobrevivencia.data.stamps import (
        ALL_DROPPABLE_STAMP_KEYS,
        FUNCTIONAL_STAMP_KEYS,
        MAX_STAMP_LEVEL,
        Stamp,
        stamp_display_name,
        stamp_sell_value,
    )
    from Sobrevivencia.core.managers.buff_applicator import recalc_item_buffs, ensure_item_bonus_fields

class ItemManager:
    def _update_item_system(self, dt):
        self.special_box_timer -= dt
        if self.special_box_timer <= 0:
            self.spawn_drop("item_box", self.player.pos + self.random_offset(320), 1)
            self.special_box_timer = self.random.uniform(32.0, 44.0)
            self.message = "Uma Caixa Especial surgiu por perto."

        for item in self.inventory.active_items():
            if "storm_core" in item.effect_keys():
                item.timers["storm"] = item.timers.get("storm", 1.0) - dt
                if item.timers["storm"] <= 0:
                    self._trigger_storm_item(item)

        alive_events = []
        for event in self.item_events:
            if event.get("type") == "arrow_rain":
                event["timer"] -= dt
                event["age"] = event.get("age", 0.0) + dt
                if event["timer"] > 0:
                    alive_events.append(event)
                    if self.random.random() < dt * 15:
                        for enemy in list(self.enemies):
                            if enemy.pos.distance_squared_to(event["pos"]) <= event["radius"]**2:
                                self.damage_enemy(enemy, event["damage"], source="special")
            else:
                if event.get("type") == "explosion" and event.get("age", 0) == 0 and event.get("damage", 0) > 0:
                    for enemy in list(self.enemies):
                        if enemy.pos.distance_squared_to(event["pos"]) <= event["radius"]**2:
                            self.damage_enemy(enemy, event.get("damage", 0), source="projectile")
                            enemy.knockback += (enemy.pos - event["pos"]).normalize() * 150 if enemy.pos != event["pos"] else Vector2(1, 0)

                event["age"] = event.get("age", 0.0) + dt
                if event["age"] < event.get("duration", 1.0):
                    alive_events.append(event)
        self.item_events = alive_events[-24:]

    def _trigger_storm_item(self, item):
        target = self._nearest_enemy(self.player.pos, 520 + item.level * 18)
        cooldown = max(1.8, 5.2 - item.level * 0.18 - self.hybrid_level() * 0.08)
        item.timers["storm"] = cooldown
        if target is None:
            return

        damage = 22 + item.level * 8
        self.damage_enemy(target, damage, source="storm")
        self.item_events.append(
            {
                "start": Vector2(self.player.pos),
                "end": Vector2(target.pos),
                "age": 0.0,
                "duration": 0.18,
                "color": COLORS["special"],
            }
        )

    def _update_drops(self, dt):
        if getattr(self, "magnet_timer", 0.0) > 0.0:
            self.magnet_timer -= dt
        alive = []
        for drop in self.drops:
            drop.ttl -= dt
            drop.bob += dt * 6
            # Find nearest alive player for attraction/pickup
            nearest = self.player
            nearest_dist = 999999
            for player in self.alive_players():
                d = player.pos.distance_to(drop.pos)
                if d < nearest_dist:
                    nearest = player
                    nearest_dist = d
            to_player = nearest.pos - drop.pos
            distance = to_player.length()

            magnet_radius = self.drop_magnet_radius(drop.kind)
            if getattr(self, "magnet_timer", 0.0) > 0.0 and distance > 0:
                drop.pos += to_player.normalize() * (1200.0 * dt)
            elif 0 < distance < magnet_radius:
                drop.pos += to_player.normalize() * DROP_ATTRACT_SPEED * dt

            if distance <= DROP_PICKUP_RADIUS + drop.radius:
                if self.collect_drop(drop, nearest):
                    continue
            if drop.ttl > 0:
                alive.append(drop)
        self.drops = alive

    def _update_floaters(self, dt):
        alive = []
        for floater in self.floaters:
            floater["age"] += dt
            floater["pos"].y -= 24 * dt
            if floater["age"] < floater["duration"]:
                alive.append(floater)
        self.floaters = alive[-35:]

    def _add_special_from_source(self, amount, source, player=None):
        if player is None:
            player = self.player
        if source in ("sword", "bleed", "shield", "relic"):
            player.add_special(amount, "melee")
        elif source in ("projectile", "poison", "storm"):
            player.add_special(amount, "ranged")

    def _ammo_drop_amount(self, enemy):
        chances = {
            "basic": 0.18,
            "runner": 0.16,
            "brute": 0.42,
            "chromatic": 0.70,
            "spitter": 0.26,
            "bulwark": 0.46,
            "sapper": 0.22,
            "minion": 0.08,
        }
        if self.random.random() >= chances.get(enemy.kind, 0.0):
            return 0
        if enemy.kind == "brute":
            return self.random.randint(10, 18)
        if enemy.kind == "chromatic":
            return self.random.randint(18, 30)
        if enemy.kind == "bulwark":
            return self.random.randint(14, 24)
        if enemy.kind == "sapper":
            return self.random.randint(6, 14)
        if enemy.kind == "minion":
            return self.random.randint(2, 5)
        return self.random.randint(AMMO_DROP_PICKUP_MIN, AMMO_DROP_PICKUP_MAX)

    def _apply_kill_resource_passives(self, enemy, source, player=None):
        if player is None:
            player = self.player
        salvage = player.passives.get("field_salvage", 0)
        if salvage > 0 and self.random.random() < min(0.45, 0.035 * salvage):
            gained = 2 + salvage // 2
            player.ammo_reserve += gained
            self.add_floater(player.pos, f"+{gained} mun", COLORS["projectile"])
            if player.ammo_magazine <= 0 and player.reload_timer <= 0:
                self._start_reload_for(player)

        siphon = player.passives.get("ammo_siphon", 0)
        if siphon > 0 and source != "special" and self.random.random() < min(0.40, 0.030 * siphon):
            gained = 2 + siphon // 3
            player.ammo_reserve += gained
            player.add_special(1.5 + siphon * 0.35, "ranged" if source in ("projectile", "poison", "storm") else "melee")
            self.add_floater(player.pos, f"+{gained} mun", COLORS["projectile"])
            if player.ammo_magazine <= 0 and player.reload_timer <= 0:
                self._start_reload_for(player)

    def collect_drop(self, drop, player=None):
        if player is None:
            player = self.player
        if drop.kind == "xp":
            self.add_xp(drop.value, player)
        elif drop.kind == "ammo":
            max_res = self.max_ammo_reserve_for(player)
            if player.ammo_reserve >= max_res:
                if player.full_ammo_msg_timer <= 0:
                    self.add_floater(player.pos, "Cheio!", COLORS["muted"])
                    player.full_ammo_msg_timer = 2.0
                return False
                
            amount = int(drop.value)
            added = min(amount, max_res - player.ammo_reserve)
            player.ammo_reserve += added
            self.add_floater(player.pos, f"+{added} mun", COLORS["projectile"])
            if player.ammo_magazine <= 0 and player.reload_timer <= 0:
                self._start_reload_for(player)
        elif drop.kind == "coin":
            if self.multiplayer:
                self.shared_coins += 1
            else:
                player.coins += 1
            player.score += 25
            total_coins = self.shared_coins if self.multiplayer else player.coins
            if total_coins % 5 == 0:
                self.activate_random_coin_buff(player)
        elif drop.kind == "heal":
            player.health = min(player.max_health, player.health + drop.value)
            self.add_floater(player.pos, f"+{int(drop.value)}", COLORS["health"])
        elif drop.kind == "shield":
            player.activate_shield()
            self.message = "Escudo ativo: invulneravel, rapido e repelente."
        elif drop.kind == "item_box":
            self.grant_random_item(player.player_index)
        elif drop.kind == "stamp":
            self.grant_stamp(str(drop.value), player.player_index)
        elif drop.kind == "vacuum":
            self.magnet_timer = 4.0
            self.add_floater(player.pos, "IMA GLOBAL!", "#06B6D4")
            self.message = "Ima Global ativado! Coletando tudo."
        elif drop.kind == "portal":
            self.current_dimension = "pocket"
            self.pocket_dimension_timer = 30.0
            self.message = "Dimensao de Bolso! Sobreviva ao HP Decay!"
            for p in self.alive_players():
                p.original_pos = Vector2(p.pos)
                p.pos = Vector2(20000.0, 20000.0) + self.random_offset(100.0)
                if p.body:
                    p.body.position = p.pos.x, p.pos.y
            
            # Spawn void elite guards
            if hasattr(self, "_spawn_special_enemy"):
                self._spawn_special_enemy("chromatic", 1.5)
                self._spawn_special_enemy("chromatic", 1.5)
        return True

    def grant_random_item(self, player_index=0):
        inv = self.get_inventory(player_index)
        player = self.get_player(player_index)
        # 0.5% chance of pre-defined relic drop
        if self.random.random() < 0.005:
            relic_source_key = self.random.choice(list(RELIC_DEFINITIONS.keys()))
            result, item = inv.add_relic(relic_source_key)
            if item is not None and result in ("new", "level_up"):
                name = item_display_name(item)
                self.message = f"RELIQUIA LENDARIA encontrada: {name}!"
                self.screen_shake = max(self.screen_shake, 14.0)
                # Recalc buffs pois o item pode ter ido automaticamente para slot ativo
                ensure_item_bonus_fields(player)
                recalc_item_buffs(player, inv)
                return

        result, item = inv.add_random_item(self.random)
        if item is None:
            inv.points += 1
            self.message = "Sem itens disponiveis. +1 ponto de item."
            return

        name = item_display_name(item)
        if result == "new":
            self.message = f"Novo item: {name}."
            self.add_alert(player.pos, f"ITEM: {name}", "#38BDF8")
        elif result == "level_up":
            self.message = f"{name} subiu para o nivel {item.level}."
            self.add_alert(player.pos, f"UP: {name} Nv{item.level}", "#A78BFA")
        else:
            inv.points += 1
            self.message = f"{name} ja esta no maximo. +1 ponto de item."
            self.add_alert(player.pos, f"MAX: +1 ponto", "#64748B")

        # Sempre recalcula buffs após mudança no inventário
        ensure_item_bonus_fields(player)
        recalc_item_buffs(player, inv)

    def _grant_random_reward(self, pos, strong=False, player_index=0):
        pos = Vector2(pos)
        player = self.get_player(player_index)
        inv = self.get_inventory(player_index)
        rewards = ["item", "coins", "xp", "heal", "shield", "points"]
        if strong:
            rewards.extend(["item", "coins", "points"])
        reward = self.random.choice(rewards)

        if reward == "item":
            self.grant_random_item(player_index)
        elif reward == "coins":
            amount = 10 if strong else 5
            for _ in range(amount):
                self.spawn_drop("coin", pos + self.random_offset(56), 1)
            self.message = "Recompensa: chuva de moedas."
        elif reward == "xp":
            amount = 150 if strong else 55
            self.add_xp(amount, player)
            self.message = "Recompensa: experiencia extra."
        elif reward == "heal":
            amount = player.max_health if strong else 38
            player.health = min(player.max_health, player.health + amount)
            self.add_floater(player.pos, f"+{int(amount)}", COLORS["health"])
            self.message = "Recompensa: cura imediata."
        elif reward == "shield":
            player.activate_shield()
            self.message = "Recompensa: escudo ativado."
        else:
            amount = 1600 if strong else 420
            player.score += amount
            inv.points += 2 if strong else 1
            self.message = "Recompensa: pontos e carga de itens."

    def _grant_miniboss_reward(self, pos, killer_index=0):
        self.miniboss_arena_center = None
        self.miniboss_trapped_player = None
        killer = self.get_player(killer_index)
        inv = self.get_inventory(killer_index)
        killer.health = killer.max_health
        killer.ammo_reserve += 80
        killer.score += 5200 + int(self.time_alive * 35)
        inv.points += 3
        self._grant_bonus_levels(3, killer_index)
        self.spawn_drop("portal", Vector2(pos), 1)
        for _ in range(14):
            self.spawn_drop("coin", Vector2(pos) + self.random_offset(88), 1)
        self._grant_random_reward(pos, strong=True, player_index=killer_index)
        self.message = "Mini-boss derrotado: Altar de Portal Ativo!"

    def _grant_bonus_levels(self, amount, player_index=0):
        if self.multiplayer:
            major = False
            for _ in range(amount):
                self.shared_level += 1
                for p in self.players:
                    p.level = self.shared_level
                    self._apply_level_up_stats(p)
                for inv in self.inventories:
                    inv.points += 1
                if self.shared_level % 3 == 0:
                    major = True
                    for inv in self.inventories:
                        inv.points += 2
                    for p in self.players:
                        if not p.is_down:
                            self.spawn_drop("item_box", p.pos + self.random_offset(130), 1)
            self.shared_xp = 0
            self.shared_xp_to_next = int(40 + 25 * self.shared_level)
            self.level_up_pending = True
            self.upgrade_is_major = major
            if major:
                self.level_up_player_index = 0
                self.draft_active = False
                self.upgrade_choices = self.generate_upgrade_choices(True, 0)
            else:
                self.draft_active = True
                self.draft_turn_player = self.draft_first_picker
                if len(self.players) > 1 and self.players[self.draft_turn_player].is_down:
                    other_player = 1 - self.draft_turn_player
                    if not self.players[other_player].is_down:
                        self.draft_turn_player = other_player
                self.level_up_player_index = self.draft_turn_player
                self.upgrade_choices = self.generate_upgrade_choices(False, self.draft_turn_player)
                self.draft_first_picker = 1 - self.draft_first_picker
            return

        player = self.get_player(player_index)
        inv = self.get_inventory(player_index)
        major = False
        for _ in range(amount):
            player.level += 1
            self._apply_level_up_stats(player)
            inv.points += 1
            if player.level % 3 == 0:
                major = True
                inv.points += 2
                self.spawn_drop("item_box", player.pos + self.random_offset(130), 1)
        player.xp = 0
        player.xp_to_next = int(40 + 25 * player.level)
        self.level_up_pending = True
        self.level_up_player_index = player_index
        self.upgrade_is_major = major
        self.upgrade_choices = self.generate_upgrade_choices(major, player_index)

    def stat_shop_unlocked(self):
        return any(p.level >= STAT_SHOP_UNLOCK_LEVEL for p in self.players)

    def roll_stat_shop(self):
        if not self.stat_shop_unlocked():
            self.message = f"Loja de Status libera no nivel {STAT_SHOP_UNLOCK_LEVEL}."
            return False
        inv = self.get_inventory(0)  # shared stat shop uses P1 inventory points
        if inv.points < STAT_SHOP_ROLL_COST:
            self.message = f"Roletar custa {STAT_SHOP_ROLL_COST} ponto."
            return False
        inv.points -= STAT_SHOP_ROLL_COST
        self.stat_shop_offers = [self._generate_stat_offer() for _ in range(3)]
        self.message = "Loja de Status: escolha uma melhoria ou role uma carta novamente."
        return True

    def reroll_stat_shop_offer(self, index):
        if not self.stat_shop_unlocked():
            self.message = f"Loja de Status libera no nivel {STAT_SHOP_UNLOCK_LEVEL}."
            return False
        if index < 0 or index >= len(self.stat_shop_offers):
            self.message = "Oferta invalida."
            return False
        inv = self.get_inventory(0)
        if inv.points < STAT_SHOP_REROLL_COST:
            self.message = f"Jogar novamente custa {STAT_SHOP_REROLL_COST} ponto."
            return False
        inv.points -= STAT_SHOP_REROLL_COST
        previous_power = self.stat_shop_offers[index].get("power", 1)
        self.stat_shop_offers[index] = self._generate_stat_offer(self._reroll_stat_power(previous_power))
        self.message = "Oferta rolada novamente."
        return True

    def purchase_stat_shop_offer(self, index):
        if index < 0 or index >= len(self.stat_shop_offers):
            self.message = "Oferta invalida."
            return False
        offer = self.stat_shop_offers[index]
        cost = offer.get("cost", 0)
        inv = self.get_inventory(0)
        
        is_night = getattr(self, "light_level", 1.0) < 0.15
        
        if is_night:
            for p in self.alive_players():
                hp_cost = int(p.max_health * 0.20)
                if p.health <= hp_cost + 5:
                    self.message = "Vida muito baixa para o Sacrificio Sangrento!"
                    return False
            
            for p in self.alive_players():
                hp_cost = int(p.max_health * 0.20)
                p.health -= hp_cost
                p.damage_bonus += 0.15
                self.add_floater(p.pos, f"-{hp_cost} HP PACTO!", "#EF4444")
                self.add_floater(p.pos + Vector2(0, -25), "+15% DANO NOTURNO!", "#F59E0B")
            
            for effect in offer["effects"]:
                for player in self.players:
                    self._apply_stat_shop_effect(effect["key"], effect["value"], player)
            self.stat_shop_offers = []
            self.message = f"Pacto Sangrento: {offer['title']} (+15% Dano!)."
            return True
        else:
            if inv.points < cost:
                self.message = f"Pontos insuficientes para comprar esta melhoria (custa {cost})."
                return False
            inv.points -= cost
            for effect in offer["effects"]:
                for player in self.players:
                    self._apply_stat_shop_effect(effect["key"], effect["value"], player)
            self.stat_shop_offers = []
            self.message = f"Melhoria comprada: {offer['title']}."
            return True

    def _generate_stat_offer(self, power=None):
        if power is None:
            power = 2 if self.random.random() < 0.20 else 1
        power = max(1, min(5, int(power)))
        if power >= 4:
            effect_count = self.random.choices([1, 2, 3], weights=[20, 50, 30], k=1)[0]
        elif power >= 2:
            effect_count = self.random.choices([1, 2], weights=[55, 45], k=1)[0]
        else:
            effect_count = self.random.choices([1, 2], weights=[75, 25], k=1)[0]

        definitions = self.random.sample(STAT_SHOP_STATS, min(effect_count, len(STAT_SHOP_STATS)))
        effects = []
        total_cost = 0.0
        for definition in definitions:
            value = self._roll_stat_value(definition, power)
            effects.append({
                "key": definition["key"],
                "label": definition["label"],
                "value": value,
                "display": self._stat_effect_display(definition, value),
            })
            total_cost += value * definition["cost"]

        rarity = ["", "Comum", "Refinada", "Rara", "Epica", "Lendaria"][power]
        cost = max(2, math.ceil(total_cost + power * 0.8 + max(0, len(effects) - 1) * 1.2))
        return {
            "title": f"Melhoria {rarity}",
            "power": power,
            "cost": cost,
            "effects": effects,
        }

    def _reroll_stat_power(self, previous_power):
        roll = self.random.random()
        if roll < 0.55:
            gain = 0
        elif roll < 0.87:
            gain = 1
        elif roll < 0.98:
            gain = 2
        else:
            gain = 3
        return min(5, previous_power + gain)

    def _roll_stat_value(self, definition, power):
        scale = 1.0 + (power - 1) * 0.55
        raw = definition["base"] * scale * self.random.uniform(0.84, 1.22)
        if definition["kind"] == "integer":
            return max(1, int(round(raw)))
        if definition["kind"] == "flat":
            return max(1, int(round(raw)))
        if definition["kind"] == "decimal":
            return round(max(0.1, raw), 1)
        return round(max(0.005, raw), 3)

    def _stat_effect_display(self, definition, value):
        if definition["kind"] == "percent":
            return f"+{int(round(value * 100))}% {definition['unit']}"
        if definition["kind"] == "decimal":
            return f"+{value:.1f} {definition['unit']}"
        return f"+{int(value)} {definition['unit']}"

    def _apply_stat_shop_effect(self, key, value, player=None):
        if player is None:
            player = self.player
        if key == "max_health":
            player.max_health += value
            player.health = min(player.max_health, player.health + value)
        elif key == "damage":
            player.damage_bonus += value
        elif key == "speed":
            player.speed_bonus += value
        elif key == "attack_rate":
            player.attack_rate_bonus += value
        elif key == "sword_range":
            player.sword_range_bonus += value
        elif key == "special_gain":
            player.special_gain_bonus += value
        elif key == "vampirism":
            player.vampirism += value
        elif key == "magazine":
            player.magazine_bonus += int(value)
            player.ammo_magazine = min(self.magazine_capacity(), player.ammo_magazine + int(value))
        elif key == "reload_speed":
            player.reload_speed_bonus += value

    def toggle_inventory_item(self, key):
        inv = self.get_inventory(self.menu_player_index)
        success, message = inv.toggle_active(key)
        if success:
            player = self.get_player(self.menu_player_index)
            ensure_item_bonus_fields(player)
            recalc_item_buffs(player, inv)
        self.message = message
        return success

    def upgrade_inventory_item(self, key):
        inv = self.get_inventory(self.menu_player_index)
        success, message = inv.upgrade_with_point(key)
        if success:
            player = self.get_player(self.menu_player_index)
            ensure_item_bonus_fields(player)
            recalc_item_buffs(player, inv)
        self.message = message
        return success

    def buy_shop_item(self, item_key):
        inv = self.get_inventory(self.menu_player_index)
        cost = 15
        if inv.points < cost:
            self.message = f"Pontos insuficientes para comprar (custa {cost})."
            return False
            
        inv.points -= cost
        status, item = inv.add_item(item_key)
        self.message = f"Item {item.key} adquirido no Mercado Negro!"
        # Recalc buffs
        player = self.get_player(self.menu_player_index)
        ensure_item_bonus_fields(player)
        recalc_item_buffs(player, inv)
        return True

    def skill_upgrade_cost(self, key):
        player = self.get_player(self.menu_player_index)
        data = CHARACTERS[player.char_class]["passives"].get(key, {})
        level = player.passives.get(key, 0)
        is_special = data.get("category") == "Especial"
        if level == 0:
            return SPECIAL_SKILL_UNLOCK_COST if is_special else SKILL_UNLOCK_COST
        return SPECIAL_SKILL_UPGRADE_COST if is_special else SKILL_UPGRADE_COST

    def upgrade_skill(self, key):
        player = self.get_player(self.menu_player_index)
        inv = self.get_inventory(self.menu_player_index)
        if key not in player.passives:
            self.message = "Skill nao encontrada."
            return False
        if player.passives[key] >= 10:
            self.message = "Skill ja esta no nivel maximo."
            return False
        cost = self.skill_upgrade_cost(key)
        if inv.points < cost:
            self.message = f"Pontos insuficientes para upar skill (custa {cost})."
            return False
        inv.points -= cost
        player.passives[key] += 1
        data = CHARACTERS[player.char_class]["passives"][key]
        state = "desbloqueada" if player.passives[key] == 1 else "aprimorada"
        self.message = f"Skill {state}: {data['title']}."
        return True

    def mark_or_fuse_item(self, key):
        inv = self.get_inventory(self.menu_player_index)
        success, message = inv.mark_for_fusion(key)
        self.message = message
        return success

    def fusion_preview(self):
        inv = self.get_inventory(self.menu_player_index)
        success, preview, message = inv.preview_marked_fusion()
        return success, preview, message

    def has_pending_fusion(self):
        success, _, _ = self.fusion_preview()
        return success

    def confirm_pending_fusion(self):
        inv = self.get_inventory(self.menu_player_index)
        if inv.points < FUSION_COST:
            self.message = f"Pontos insuficientes para fusao (custa {FUSION_COST})."
            return False
        success, message = inv.fuse_marked_items()
        if success:
            inv.points -= FUSION_COST
            # Recalcula buffs: a fusão substitui itens nos slots ativos
            player = self.get_player(self.menu_player_index)
            ensure_item_bonus_fields(player)
            recalc_item_buffs(player, inv)
        self.message = message
        return success

    def cancel_pending_fusion(self):
        inv = self.get_inventory(self.menu_player_index)
        inv.clear_fusion_marks()
        self.message = "Fusao cancelada."

    # Incremento fixo por nível para cada atributo do player (separado da Loja de Status)
    # Valores calibrados para dar progressão leve mas perceptível sem inflacionar demais.
    _LEVEL_UP_STAT_INCREMENTS = {
        "max_health":   8,       # flat HP por nível
        "damage":       0.008,   # +0.8% dano por nível
        "speed":        0.005,   # +0.5% velocidade por nível
        "attack_rate":  0.006,   # +0.6% cadência por nível
        "sword_range":  0.004,   # +0.4% alcance por nível
        "special_gain": 0.005,   # +0.5% carga especial por nível
        # vampirism, magazine e reload_speed NÃO crescem automaticamente por nível;
        # são adquiridos explicitamente via Loja de Status.
    }

    def _apply_level_up_stats(self, player):
        """Aplica incremento calibrado de atributos por level-up no player."""
        for key, val in self._LEVEL_UP_STAT_INCREMENTS.items():
            self._apply_stat_shop_effect(key, val, player)

    def add_xp(self, amount, player=None):
        if player is None:
            player = self.player
        
        # XP Compartilhado no Multiplayer
        if self.multiplayer:
            self.shared_xp += amount
            for p in self.players:
                p.score += int(amount * 3) # Score dividido
            
            while self.shared_xp >= self.shared_xp_to_next:
                self.shared_xp -= self.shared_xp_to_next
                self.shared_level += 1
                for p in self.players:
                    p.level = self.shared_level # Sincroniza níveis
                    self._apply_level_up_stats(p)
                
                # Pontos de inventário ainda são individuais para cada nível
                for inv in self.inventories:
                    inv.points += 1
                
                self.shared_xp_to_next = int(40 + 25 * self.shared_level)
                self.level_up_pending = True
                
                # Lógica de Draft
                major = self.shared_level % 3 == 0
                self.upgrade_is_major = major
                
                if major:
                    # Recompensas do nível especial para o time
                    for inv in self.inventories:
                        inv.points += 2
                    for p in self.players:
                        if not p.is_down:
                            self.spawn_drop("item_box", p.pos + self.random_offset(120), 1)
                    
                    # Upgrades grandes são individuais (um após o outro)
                    self.level_up_player_index = 0
                    self.draft_active = False
                    self.upgrade_choices = self.generate_upgrade_choices(True, self.level_up_player_index)
                else:
                    # Upgrades comuns são via DRAFT
                    self.draft_active = True
                    self.draft_turn_player = self.draft_first_picker
                    
                    # Se o jogador da vez estiver morto e o outro não, passa a vez pro vivo
                    if len(self.players) > 1 and self.players[self.draft_turn_player].is_down:
                        other_player = 1 - self.draft_turn_player
                        if not self.players[other_player].is_down:
                            self.draft_turn_player = other_player
                            
                    self.level_up_player_index = self.draft_turn_player
                    self.upgrade_choices = self.generate_upgrade_choices(False, self.draft_turn_player)
                    # O draft alterna quem começa a cada nível
                    self.draft_first_picker = 1 - self.draft_first_picker
                
                self.message = "DRAFT: escolha um upgrade!" if self.draft_active else "Evolução de Classe!"
                break
            return

        pi = player.player_index
        inv = self.get_inventory(pi)
        player.xp += amount
        player.score += int(amount * 6)
        while player.xp >= player.xp_to_next:
            player.xp -= player.xp_to_next
            player.level += 1
            self._apply_level_up_stats(player)
            inv.points += 1
            player.xp_to_next = int(40 + 25 * player.level)
            self.level_up_pending = True
            self.level_up_player_index = pi
            self.upgrade_is_major = player.level % 3 == 0
            if self.upgrade_is_major:
                inv.points += 2
                self.spawn_drop("item_box", player.pos + self.random_offset(120), 1)
            self.upgrade_choices = self.generate_upgrade_choices(self.upgrade_is_major, pi)
            self.message = "Escolha uma melhoria grande." if self.upgrade_is_major else "Escolha um upgrade."
            break

    def activate_random_coin_buff(self, player=None):
        if player is None:
            player = self.player
        buff = self.random.choice(["freeze", "speed", "power"])
        player.activate_buff(buff)
        labels = {
            "freeze": "Tiro congelante ativado.",
            "speed": "Aumento de velocidade ativado.",
            "power": "Dano energizado ativado.",
        }
        self.message = labels[buff]

    def generate_upgrade_choices(self, major=False, player_index=0):
        player = self.get_player(player_index)
        if major:
            passives = player.passives
            available = [k for k, v in passives.items() if v < 10]
            if not available:
                keys = list(OMNI_UPGRADES.keys())
                return self.random.sample(keys, min(3, len(keys)))
            return self.random.sample(available, min(3, len(available)))
        else:
            keys = list(UPGRADES.keys())
            return self.random.sample(keys, 3)

    def apply_upgrade(self, upgrade_key, player_index=0):
        player = self.get_player(player_index)
        if upgrade_key == "speed":
            player.speed_bonus += 0.08
        elif upgrade_key == "damage":
            player.damage_bonus += 0.13
        elif upgrade_key == "max_health":
            player.max_health += 22
            player.health = min(player.max_health, player.health + 42)
        elif upgrade_key == "fire_rate":
            player.attack_rate_bonus += 0.11
        elif upgrade_key == "sword_range":
            player.sword_range_bonus += 0.10
        elif upgrade_key == "special_gain":
            player.special_gain_bonus += 0.16
        elif upgrade_key == "vampirism":
            player.vampirism += 2.5
        elif upgrade_key in player.passives:
            player.passives[upgrade_key] += 1
        elif upgrade_key == "omni_power":
            player.damage_bonus += 0.25
            player.attack_rate_bonus += 0.25
            player.sword_range_bonus += 0.25
        elif upgrade_key == "omni_survival":
            player.max_health += 45
            player.health += 45
            player.speed_bonus += 0.45
            player.vampirism += 5.0
        elif upgrade_key == "omni_special":
            player.special_gain_bonus += 1.0
            player.sword_range_bonus += 0.35
            player.attack_rate_bonus += 0.15

        data = UPGRADES.get(upgrade_key)
        if not data:
            data = OMNI_UPGRADES.get(upgrade_key)
        if not data:
            data = CHARACTERS[player.char_class]["passives"].get(upgrade_key)

        title = data["title"] if data else upgrade_key
        self.message = f"J{player_index + 1} escolheu: {title}"

        # Lógica de Draft Multiplayer
        if self.multiplayer and self.draft_active:
            if player_index == self.draft_turn_player: # Jogador da vez
                # Remove a escolha da lista
                if upgrade_key in self.upgrade_choices:
                    self.upgrade_choices.remove(upgrade_key)
                
                # Se ainda houver um segundo turno no draft
                if len(self.upgrade_choices) > 1: # Tinha 3, sobrou 2
                    self.draft_turn_player = 1 - self.draft_turn_player
                    self.level_up_player_index = self.draft_turn_player
                    # Mantém o level_up_pending = True para o próximo jogador
                    return
                else:
                    # Fim do draft: limpa tudo
                    self.draft_active = False
                    self.level_up_pending = False
                    self.upgrade_choices = []
            return

        # Lógica de Upgrades Grandes Multiplayer (sequencial)
        if self.multiplayer and self.upgrade_is_major and player_index == 0:
            # P1 terminou, agora vez do P2
            self.level_up_player_index = 1
            self.upgrade_choices = self.generate_upgrade_choices(True, 1)
            return

        self.level_up_pending = False
        self.upgrade_is_major = False
        self.upgrade_choices = []

    def spawn_drop(self, kind, pos, value=1):
        radius = 8
        if kind == "xp":
            radius = 7
        elif kind == "ammo":
            radius = 8
        elif kind == "heal":
            radius = 10
        elif kind == "shield":
            radius = 12
        elif kind == "item_box":
            radius = 13
        elif kind == "stamp":
            radius = 10
        self.drops.append(Drop(pos=Vector2(pos), kind=kind, value=value, radius=radius))

    def _stamp_entries(self, player):
        entries = []
        for weapon_key in ("weapon_1", "weapon_2"):
            for index, stamp in enumerate(player.weapon_stamps.get(weapon_key, [])):
                entries.append((weapon_key, index, stamp))
        for index, stamp in enumerate(player.stamp_reserve):
            entries.append(("reserve", index, stamp))
        return entries

    def grant_stamp(self, stamp_key=None, player_index=0):
        player = self.get_player(player_index)
        if stamp_key is None:
            stamp_key = self.random.choice(ALL_DROPPABLE_STAMP_KEYS)
        stamp = Stamp(key=stamp_key, level=1)
        player.stamp_reserve.append(stamp)
        name = stamp_display_name(stamp)
        self.message = f"Novo selo coletado: {name}."
        self.add_alert(player.pos, f"SELO: {name}", "#F59E0B")
        return stamp

    def equip_stamp(self, weapon_key, selected):
        player = self.get_player(self.menu_player_index)
        entries = self._stamp_entries(player)
        if selected < 0 or selected >= len(entries):
            self.message = "Selo nao encontrado."
            return False
        location, index, stamp = entries[selected]
        if location != "reserve":
            self.message = "Este selo ja esta equipado."
            return False
        if stamp.key not in FUNCTIONAL_STAMP_KEYS:
            self.message = "Fragmentos nao podem ser equipados; use para fusao ou venda."
            return False
        equipped = player.weapon_stamps.setdefault(weapon_key, [])
        if len(equipped) >= 3:
            self.message = "Esta arma ja tem 3 selos equipados."
            return False
        equipped.append(player.stamp_reserve.pop(index))
        weapon_name = "distancia" if weapon_key == "weapon_1" else "corpo a corpo"
        self.message = f"{stamp_display_name(stamp)} equipado na arma de {weapon_name}."
        return True

    def unequip_stamp(self, selected):
        player = self.get_player(self.menu_player_index)
        entries = self._stamp_entries(player)
        if selected < 0 or selected >= len(entries):
            self.message = "Selo nao encontrado."
            return False
        location, index, stamp = entries[selected]
        if location == "reserve":
            self.message = "Este selo ja esta guardado."
            return False
        player.stamp_reserve.append(player.weapon_stamps[location].pop(index))
        self.message = f"{stamp_display_name(stamp)} guardado na reserva."
        return True

    def sell_stamp(self, selected):
        player = self.get_player(self.menu_player_index)
        entries = self._stamp_entries(player)
        if selected < 0 or selected >= len(entries):
            self.message = "Selo nao encontrado."
            return False
        location, index, stamp = entries[selected]
        if location != "reserve":
            self.message = "Desequipe o selo antes de vende-lo."
            return False
        value = stamp_sell_value(stamp)
        player.stamp_reserve.pop(index)
        self.get_inventory(self.menu_player_index).points += value
        self.message = f"{stamp_display_name(stamp)} vendido por {value} pontos."
        return True

    def setup_stamp_fusion(self, selected):
        player = self.get_player(self.menu_player_index)
        entries = self._stamp_entries(player)
        if selected < 0 or selected >= len(entries):
            self.stamp_fusion_target = None
            self.stamp_fusion_materials = []
            self.stamp_fusion_msg = "Selo alvo invalido."
            return False
        _, _, stamp = entries[selected]
        self.stamp_fusion_target = selected
        self.stamp_fusion_materials = []
        self.stamp_fusion_msg = f"Escolha 3 selos da reserva para aprimorar {stamp_display_name(stamp)}."
        return True

    def toggle_stamp_fusion_material(self, reserve_index):
        player = self.get_player(self.menu_player_index)
        if reserve_index < 0 or reserve_index >= len(player.stamp_reserve):
            return False
        target = getattr(self, "stamp_fusion_target", None)
        entries = self._stamp_entries(player)
        if target is not None and 0 <= target < len(entries):
            location, index, _ = entries[target]
            if location == "reserve" and index == reserve_index:
                self.stamp_fusion_msg = "O selo alvo nao pode ser sacrificado."
                return False
        materials = getattr(self, "stamp_fusion_materials", [])
        if reserve_index in materials:
            materials.remove(reserve_index)
        elif len(materials) < 3:
            materials.append(reserve_index)
        else:
            self.stamp_fusion_msg = "Limite de 3 selos para sacrificio."
            return False
        self.stamp_fusion_materials = materials
        return True

    def can_confirm_stamp_fusion(self):
        player = self.get_player(self.menu_player_index)
        entries = self._stamp_entries(player)
        target = getattr(self, "stamp_fusion_target", None)
        materials = list(getattr(self, "stamp_fusion_materials", []))
        if target is None or target < 0 or target >= len(entries):
            return False, "Escolha um selo alvo."
        location, target_index, target_stamp = entries[target]
        if target_stamp.level >= MAX_STAMP_LEVEL or target_stamp.is_junk:
            return False, "Este selo nao pode subir mais de nivel."
        if len(set(materials)) != 3:
            return False, "Sacrifique exatamente 3 selos da reserva."
        if any(idx < 0 or idx >= len(player.stamp_reserve) for idx in materials):
            return False, "Material de fusao invalido."
        if location == "reserve" and target_index in materials:
            return False, "O selo alvo nao pode ser sacrificado."
        return True, "Fusao pronta."

    def confirm_stamp_fusion(self):
        ok, message = self.can_confirm_stamp_fusion()
        if not ok:
            self.stamp_fusion_msg = message
            self.message = message
            return False
        player = self.get_player(self.menu_player_index)
        entries = self._stamp_entries(player)
        _, _, target_stamp = entries[self.stamp_fusion_target]
        target_stamp.level = min(MAX_STAMP_LEVEL, target_stamp.level + 1)
        for reserve_index in sorted(self.stamp_fusion_materials, reverse=True):
            player.stamp_reserve.pop(reserve_index)
        self.stamp_fusion_materials = []
        self.stamp_fusion_target = None
        self.stamp_fusion_msg = ""
        self.message = f"{stamp_display_name(target_stamp)} aprimorado."
        return True

    def add_floater(self, pos, text, color):
        self.floaters.append(
            {
                "pos": Vector2(pos),
                "text": text,
                "color": color,
                "age": 0.0,
                "duration": 0.55,
                "type": "damage",
            }
        )

    def add_alert(self, pos, text, color=None, flash_target=None):
        """Alerta rápido de ação bloqueada (0.5s, sobe mais, fonte maior)."""
        if color is None:
            color = COLORS["danger"]
        # Evita spam: ignora se já há alerta igual recente
        for f in self.floaters[-6:]:
            if f.get("type") == "alert" and f["text"] == text and f["age"] < 0.2:
                return
        self.floaters.append(
            {
                "pos": Vector2(pos),
                "text": text,
                "color": color,
                "age": 0.0,
                "duration": 0.65,
                "type": "alert",
                "flash_target": flash_target,
            }
        )

    def drop_magnet_radius(self, kind):
        magnet = self.item_level("magnet_orb")
        base = XP_MAGNET_RADIUS if kind == "xp" else XP_MAGNET_RADIUS * 0.72
        if kind == "item_box":
            base = XP_MAGNET_RADIUS * 1.4  # Item boxes easier to pick up
        elif kind == "stamp":
            base = XP_MAGNET_RADIUS * 1.8  # Stamps have large magnet radius
        return base + magnet * 9

