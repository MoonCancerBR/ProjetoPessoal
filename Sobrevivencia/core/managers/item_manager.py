from pygame.math import Vector2
import random
import math
if __package__:
    from ...data.constants import *
    from ..drops import coleta as drop_coleta
    from ..drops.spawning import spawn_drop as spawn_drop_entity
    from ..personagem import progressao as progressao_system
    from ..entities import Drop
    from ..personagem.inventario import acoes as inventario_acoes
    from ..selos.inventario.helpers import auto_equip_passive_stamp, stamp_entries
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
    from Sobrevivencia.core.drops import coleta as drop_coleta
    from Sobrevivencia.core.drops.spawning import spawn_drop as spawn_drop_entity
    from Sobrevivencia.core.personagem import progressao as progressao_system
    from Sobrevivencia.core.entities import Drop
    from Sobrevivencia.core.personagem.inventario import acoes as inventario_acoes
    from Sobrevivencia.core.selos.inventario.helpers import auto_equip_passive_stamp, stamp_entries
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
            self.special_box_timer = self.random.uniform(22.0, 32.0)
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
            elif event.get("type") == "blood_zone":
                event["timer"] -= dt
                event["age"] = event.get("age", 0.0) + dt
                event["pulse_timer"] = event.get("pulse_timer", 0.0) - dt
                if event["timer"] > 0:
                    alive_events.append(event)
                    if event["pulse_timer"] <= 0:
                        owner = self.get_player(event.get("owner", 0))
                        for enemy in list(self.enemies):
                            if enemy.pos.distance_squared_to(event["pos"]) > event["radius"] ** 2:
                                continue
                            self.damage_enemy(enemy, event["damage"], source="special", killer_index=owner.player_index)
                            enemy.frozen_timer = max(enemy.frozen_timer, 0.18)
                            if hasattr(self, "_apply_blood_mark"):
                                self._apply_blood_mark(
                                    enemy,
                                    owner,
                                    bonus_duration=0.35,
                                    level_bonus=event.get("mark_bonus", 0),
                                )
                        event["pulse_timer"] = 0.28
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
            
        original_dimension = getattr(self, "current_dimension", "main")
        drops_to_process = self.drops
        self.drops = []
        
        for drop in drops_to_process:
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

            if drop.kind in ("portal", "exit_portal"):
                interact_radius = DROP_PICKUP_RADIUS + drop.radius + 16
                if distance <= interact_radius:
                    player_still = getattr(nearest, "dash_timer", 0.0) <= 0 and not getattr(nearest, "is_moving_input", False)
                    if drop.activation_player_index != nearest.player_index:
                        drop.activation_player_index = nearest.player_index
                        drop.activation_timer = 0.0
                    if player_still:
                        drop.activation_timer += dt
                        if drop.activation_timer >= 1.6:
                            if self.collect_drop(drop, nearest):
                                continue
                    else:
                        drop.activation_timer = max(0.0, drop.activation_timer - dt * 1.5)
                    remaining = max(0.0, 1.6 - drop.activation_timer)
                    self.message = f"Portal instavel: fique parado {remaining:.1f}s para entrar."
                else:
                    drop.activation_timer = 0.0
                    drop.activation_player_index = -1
            else:
                magnet_radius = self.drop_magnet_radius(drop.kind)
                if getattr(self, "magnet_timer", 0.0) > 0.0 and distance > 0:
                    drop.pos += to_player.normalize() * (1200.0 * dt)
                elif 0 < distance < magnet_radius:
                    drop.pos += to_player.normalize() * DROP_ATTRACT_SPEED * dt

                if distance <= DROP_PICKUP_RADIUS + drop.radius:
                    if self.collect_drop(drop, nearest):
                        continue
            if drop.ttl > 0:
                if getattr(self, "current_dimension", "main") == original_dimension:
                    self.drops.append(drop)
                else:
                    state = getattr(self, "pocket_dimension_state", None)
                    if state is not None and "drops" in state:
                        state["drops"].append(drop)

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
        elif source in ("projectile", "poison", "storm", "laser"):
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
        return drop_coleta.collect_drop(self, drop, player)
    def grant_random_item(self, player_index=0):
        return progressao_system.grant_random_item(self, player_index)

    def _grant_random_reward(self, pos, strong=False, player_index=0):
        return progressao_system.grant_random_reward(self, pos, strong, player_index)

    def _grant_miniboss_reward(self, pos, killer_index=0):
        return progressao_system.grant_miniboss_reward(self, pos, killer_index)

    def _grant_bonus_levels(self, amount, player_index=0):
        return progressao_system.grant_bonus_levels(self, amount, player_index)

    def stat_shop_unlocked(self):
        if getattr(self, "multiplayer", False) and hasattr(self, "shared_level"):
            return self.shared_level >= STAT_SHOP_UNLOCK_LEVEL
        players = getattr(self, "players", None) or []
        if players:
            return max(getattr(player, "level", 0) for player in players) >= STAT_SHOP_UNLOCK_LEVEL
        return getattr(self, "level", 0) >= STAT_SHOP_UNLOCK_LEVEL

    def _max_health_shop_cost(self, base_cost):
        return max(1, int(math.ceil(base_cost)))

    def _pay_max_health_cost(self, cost, reason):
        cost = max(1, int(math.ceil(cost)))
        player = self.get_player(getattr(self, "menu_player_index", 0))
        if player.max_health - cost < 1:
            self.message = "Vida maxima insuficiente para pagar esse custo."
            return False
        player.max_health -= cost
        player.health = min(player.health, player.max_health)
        return True

    def roll_stat_shop(self):
        hp_cost = self._max_health_shop_cost(STAT_SHOP_ROLL_COST)
        if not self._pay_max_health_cost(hp_cost, "abrir o gacha"):
            return False
        self.stat_shop_offers = [self._generate_stat_offer() for _ in range(3)]
        self.message = f"Gacha de Status aberto por -{hp_cost} vida maxima."
        return True

    def reroll_stat_shop_offer(self, index):
        if index < 0 or index >= len(self.stat_shop_offers):
            self.message = "Oferta invalida."
            return False
        hp_cost = self._max_health_shop_cost(STAT_SHOP_REROLL_COST)
        if not self._pay_max_health_cost(hp_cost, "rerollar oferta"):
            return False
        previous_power = self.stat_shop_offers[index].get("power", 1)
        self.stat_shop_offers[index] = self._generate_stat_offer(self._reroll_stat_power(previous_power))
        self.message = f"Oferta rolada novamente por -{hp_cost} vida maxima."
        return True

    def purchase_stat_shop_offer(self, index):
        if index < 0 or index >= len(self.stat_shop_offers):
            self.message = "Oferta invalida."
            return False
        offer = self.stat_shop_offers[index]
        cost = offer.get("cost", 0)
        inv = self.get_inventory(getattr(self, "menu_player_index", 0))
        
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
        return inventario_acoes.toggle_inventory_item(self, key)

    def upgrade_inventory_item(self, key):
        return inventario_acoes.upgrade_inventory_item(self, key)

    def buy_shop_item(self, item_key):
        return inventario_acoes.buy_shop_item(self, item_key)

    def skill_upgrade_cost(self, key):
        return inventario_acoes.skill_upgrade_cost(self, key)

    def upgrade_skill(self, key):
        return inventario_acoes.upgrade_skill(self, key)

    def mark_or_fuse_item(self, key):
        return inventario_acoes.mark_or_fuse_item(self, key)

    def fusion_preview(self):
        return inventario_acoes.fusion_preview(self)

    def has_pending_fusion(self):
        return inventario_acoes.has_pending_fusion(self)

    def confirm_pending_fusion(self):
        return inventario_acoes.confirm_pending_fusion(self)
    def cancel_pending_fusion(self):
        return inventario_acoes.cancel_pending_fusion(self)
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
            self.level_up_player_index = pi
            self.upgrade_is_major = player.level % 3 == 0
            if self.upgrade_is_major:
                inv.points += 2
                self.spawn_drop("item_box", player.pos + self.random_offset(120), 1)
            if player.level % 10 == 0:
                self.level_up_pending = True
                self.upgrade_is_major = True
                self.upgrade_choices = self.generate_singleplayer_milestone_choices(pi)
                self.message = "Marco de nivel: escolha uma melhoria mista."
            else:
                self.level_up_pending = False
                self.upgrade_is_major = False
                self.upgrade_choices = []
                self.message = f"Nivel {player.level}: atributos aumentaram."
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
            available = [
                key for key, level in passives.items()
                if level < 10 and (level > 0 or self.passive_unlock_status(key, player)[0])
            ]
            if not available:
                keys = list(OMNI_UPGRADES.keys())
                return self.random.sample(keys, min(3, len(keys)))
            return self.random.sample(available, min(3, len(available)))
        else:
            keys = list(UPGRADES.keys())
            return self.random.sample(keys, 3)

    def generate_singleplayer_milestone_choices(self, player_index=0):
        player = self.get_player(player_index)
        choices = []
        passives = [
            key for key, level in player.passives.items()
            if level < 10 and (level > 0 or self.passive_unlock_status(key, player)[0])
        ]
        omni = list(OMNI_UPGRADES.keys())
        common = list(UPGRADES.keys())
        pools = [passives, omni, common]
        while len(choices) < 3 and any(pools):
            pool = self.random.choice([p for p in pools if p])
            key = self.random.choice(pool)
            pool.remove(key)
            if key not in choices:
                choices.append(key)
        return choices

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
            player.passives[upgrade_key] = min(10, player.passives[upgrade_key] + 1)
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
        return spawn_drop_entity(self, kind, pos, value)

    def _stamp_entries(self, player):
        return stamp_entries(player)

    def grant_stamp(self, stamp_key=None, player_index=0):
        player = self.get_player(player_index)
        if stamp_key is None:
            stamp_key = self.random.choice(ALL_DROPPABLE_STAMP_KEYS)
        stamp = Stamp(key=stamp_key, level=1)
        name = stamp_display_name(stamp)
        auto_weapon = self._auto_equip_passive_stamp(player, stamp)
        if auto_weapon is None:
            if len(player.stamp_reserve) >= STAMP_RESERVE_LIMIT:
                value = stamp_sell_value(stamp)
                self.get_inventory(player.player_index).points += value
                self.message = f"Reserva de selos cheia ({STAMP_RESERVE_LIMIT}). {name} convertido em {value} pts."
                self.add_alert(player.pos, f"SELO -> +{value} pts", COLORS["coin"])
                return None
            player.stamp_reserve.append(stamp)
            self.message = f"Novo selo coletado: {name}."
        else:
            weapon_name = CHARACTERS[player.char_class][auto_weapon]
            self.message = f"Selo coletado e equipado em {weapon_name}: {name}."
        self.add_alert(player.pos, f"SELO: {name}", "#F59E0B")
        return stamp

    def _auto_equip_passive_stamp(self, player, stamp):
        return auto_equip_passive_stamp(player, stamp)

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
        if len(player.stamp_reserve) >= STAMP_RESERVE_LIMIT:
            self.message = f"Reserva de selos cheia ({STAMP_RESERVE_LIMIT}). Venda ou funda selos antes de desequipar."
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
