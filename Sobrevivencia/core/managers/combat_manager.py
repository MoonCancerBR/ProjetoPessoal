from pygame.math import Vector2
import math
if __package__:
    from ...data.constants import *
    from ..combate import sangue
    from ...data.stamps import ALL_DROPPABLE_STAMP_KEYS, stamp_effect_value, stamps_equipped_for_weapon
    from ..personagem import atributos
    from ..personagem.cacadora import combate as cacadora_combate
    from ..personagem.ceifadora import combate as ceifadora_combate
    from ..personagem.engenheiro import combate as engenheiro_combate
    from ..personagem.vanguarda import combate as vanguarda_combate
    from ..personagem.combat_dispatch import auto_attack_for, cast_ultimate, cast_weapon_special
    from ..entities import Hazard, PlayerConstruct, Projectile, RectBody, Slash
    from ..world import circle_rect_overlap
else:
    from Sobrevivencia.data.constants import *
    from Sobrevivencia.core.combate import sangue
    from Sobrevivencia.data.stamps import ALL_DROPPABLE_STAMP_KEYS, stamp_effect_value, stamps_equipped_for_weapon
    from Sobrevivencia.core.personagem import atributos
    from Sobrevivencia.core.personagem.cacadora import combate as cacadora_combate
    from Sobrevivencia.core.personagem.ceifadora import combate as ceifadora_combate
    from Sobrevivencia.core.personagem.engenheiro import combate as engenheiro_combate
    from Sobrevivencia.core.personagem.vanguarda import combate as vanguarda_combate
    from Sobrevivencia.core.personagem.combat_dispatch import auto_attack_for, cast_ultimate, cast_weapon_special
    from Sobrevivencia.core.entities import Hazard, PlayerConstruct, Projectile, RectBody, Slash
    from Sobrevivencia.core.world import circle_rect_overlap

class CombatManager:
    def try_dash(self, aim_world, player_index=0):
        player = self.get_player(player_index)
        if player.is_down:
            return
        if self.game_over:
            return
        if player.dash_cooldown > 0 or player.dash_timer > 0:
            remaining = round(player.dash_cooldown, 1)
            self.add_alert(player.pos, f"Dash: {remaining}s", COLORS["muted"], flash_target="dash")
            return
        # Quest hook: fail survive_no_dash
        if self.quest and self.quest["goal_type"] == "survive_no_dash":
            self._fail_quest()
        direction = Vector2(player.last_move_dir)
        if direction.length_squared() < 0.01:
            direction = Vector2(aim_world) - player.pos
        if direction.length_squared() < 0.01:
            direction = Vector2(1, 0)
        player.dash_dir = direction.normalize()
        player.dash_timer = DASH_DURATION
        player.dash_cooldown = self.current_dash_cooldown_for(player)
        player.invulnerable_timer = max(player.invulnerable_timer, DASH_DURATION + 0.08)
        self.emit_particles(player.pos, count=10, color=P1_AIM_COLOR if player.player_index == 0 else P2_AIM_COLOR, speed=150, lifetime=0.24, size=4)
        self._apply_character_dash_effect(player)

    def _apply_character_dash_effect(self, player):
        if player.char_class == "engineer":
            self._plant_dash_mine(player)
        elif player.char_class == "reaper":
            self._spawn_reaper_dash_slash(player)
            player.invulnerable_timer = max(player.invulnerable_timer, DASH_DURATION + 0.14)
            self.emit_particles(player.pos, count=14, color="#991B1B", speed=200, lifetime=0.28, size=3)
            self.message = "Dash da Ceifadora: rastro de morte."
        elif player.char_class == "huntress":
            player.dash_timer = max(player.dash_timer, DASH_DURATION * 1.18)
            player.invulnerable_timer = max(player.invulnerable_timer, player.dash_timer + 0.12)
            self.emit_particles(player.pos, count=18, color="#F97316", speed=230, lifetime=0.30, size=3)
            self.message = "Dash da Cacadora: investida longa."
        elif player.char_class == "vanguard":
            player.activate_shield()
            player.shield_timer = max(player.shield_timer, 1.25)
            self.message = "Dash da Vanguarda: escudo de impacto."

    def _plant_dash_mine(self, player):
        size = 32
        mine_pos = Vector2(player.pos) - player.dash_dir * 92
        cx, cy = self.world.chunk_coords(mine_pos.x, mine_pos.y)
        chunk = self.world.ensure_chunk(cx, cy)
        rect = RectBody(mine_pos.x - size * 0.5, mine_pos.y - size * 0.5, size, size)
        mine_id = f"dash_mine:{player.player_index}:{int(self.time_alive * 1000)}:{len(chunk['hazards'])}"
        chunk["hazards"].append(Hazard(id=mine_id, rect=rect, kind="mine", chunk=(cx, cy)))
        self.emit_particles(mine_pos, count=12, color="#22D3EE", speed=90, lifetime=0.35, size=4)
        self.emit_particles(mine_pos + Vector2(0, -4), count=5, color="#FACC15", speed=45, lifetime=0.2, size=2)
        self.message = "Dash do Engenheiro: mina de pulso armada."

    def _spawn_reaper_dash_slash(self, player):
        inv = self.get_inventory(player.player_index)
        self.slashes.append(
            Slash(
                origin=Vector2(player.pos),
                direction=Vector2(player.dash_dir),
                radius=self.sword_radius_for(player, inv) * 0.58,
                arc=self.sword_arc_for(player) * 0.65,
                damage=self.sword_damage_for(player, inv) * 0.34,
                duration=SWORD_DURATION * 0.55,
                bleed_level=max(0, player.passives.get("hemorrhage", 0) // 2),
                owner=player.player_index,
                style="reaper_dash",
                color="#7F1D1D",
                edge_color="#FCA5A5",
                knockback=110,
                mark_level=1,
            )
        )

    def try_special(self, aim_world, player_index=0):
        if self.game_over:
            return False
        player = self.get_player(player_index)
        if player.is_down:
            return False
        channel = "ranged" if player.mode == "weapon_1" else "melee"
        if self.special_charge(channel, player_index) < SPECIAL_MAX:
            charge = int(self.special_charge(channel, player_index))
            self.message = f"J{player_index + 1}: especial da arma atual ainda nao carregou."
            self.add_alert(player.pos, f"Especial: {charge}/{SPECIAL_MAX}", COLORS["special"], flash_target="special")
            return False
        self._consume_special(channel, player)
        self._cast_weapon_special(channel, aim_world, player)
        return True

    def try_combo_special(self, aim_world, player_index=0):
        if self.game_over:
            return False
        player = self.get_player(player_index)
        if player.is_down:
            return False
        if player.special_ranged < SPECIAL_MAX or player.special_melee < SPECIAL_MAX:
            self.message = f"J{player_index + 1}: combo exige os dois especiais carregados."
            self.add_alert(player.pos, "Combo: carregue os dois especiais!", COLORS["special"], flash_target="special")
            return False
        player.special_ranged = 0
        player.special_melee = 0
        player.special = 0
        self._cast_ultimate(aim_world, player)
        return True

    def special_charge(self, channel, player_index=0):
        player = self.get_player(player_index)
        return player.special_melee if channel == "melee" else player.special_ranged

    def _consume_special(self, channel, player=None):
        if player is None:
            player = self.player
        if channel == "melee":
            player.special_melee = 0
        else:
            player.special_ranged = 0
        player.special = max(player.special_ranged, player.special_melee)

    def _cast_weapon_special(self, channel, aim_world, player=None):
        return cast_weapon_special(self, channel, aim_world, player)

    def _cast_ultimate(self, aim_world, player=None):
        return cast_ultimate(self, aim_world, player)

    def _cast_vanguard_ultimate(self, aim_world, player):
        return vanguarda_combate.cast_ultimate(self, aim_world, player)

    def _cast_huntress_ultimate(self, aim_world, player):
        return cacadora_combate.cast_ultimate(self, aim_world, player)

    def _cast_engineer_ultimate(self, aim_world, player):
        return engenheiro_combate.cast_ultimate(self, aim_world, player)

    def _spawn_engineer_construct(self, pos, kind, owner, level=1, duration=12.0):
        return engenheiro_combate.spawn_construct(self, pos, kind, owner, level, duration)

    def _cast_engineer_turret_grid(self, aim_world, player=None):
        return engenheiro_combate.cast_turret_grid(self, aim_world, player)

    def _cast_engineer_magnetic_implosion(self, aim_world, multiplier=1.0, player=None, silent=False):
        return engenheiro_combate.cast_magnetic_implosion(self, aim_world, multiplier, player, silent)

    def _cast_vanguard_radial(self, multiplier=1.0, radius_multiplier=1.0, silent=False, player=None):
        return vanguarda_combate.cast_radial(self, multiplier, radius_multiplier, silent, player)

    def _cast_vanguard_charge(self, aim_world, multiplier=1.0, silent=False, player=None):
        return vanguarda_combate.cast_charge(self, aim_world, multiplier, silent, player)

    def _cast_huntress_arrow_rain(self, aim_world, multiplier=1.0, radius_multiplier=1.0, silent=False, player=None):
        return cacadora_combate.cast_arrow_rain(self, aim_world, multiplier, radius_multiplier, silent, player)

    def _cast_huntress_dagger_dance(self, multiplier=1.0, radius_multiplier=1.0, silent=False, player=None):
        return cacadora_combate.cast_dagger_dance(self, multiplier, radius_multiplier, silent, player)

    def _cast_reaper_rosary(self, aim_world, multiplier=1.0, radius_multiplier=1.0, silent=False, player=None):
        return ceifadora_combate.cast_rosary(self, aim_world, multiplier, radius_multiplier, silent, player)

    def _cast_reaper_harvest(self, aim_world, multiplier=1.0, silent=False, player=None):
        return ceifadora_combate.cast_harvest(self, aim_world, multiplier, silent, player)

    def _cast_reaper_ultimate(self, aim_world, player):
        return ceifadora_combate.cast_ultimate(self, aim_world, player)

    def _ranged_weapon_ready(self, show_message=False):
        return self._ranged_weapon_ready_for(self.player, show_message=show_message)

    def _ranged_weapon_ready_for(self, player, show_message=False):
        if player.reload_timer > 0:
            if show_message:
                self.message = f"J{player.player_index + 1} recarregando: {player.reload_timer:.1f}s."
                self.add_alert(player.pos, f"Recarregando! ({player.reload_timer:.1f}s)", COLORS["muted"], flash_target="ammo")
            return False
        if player.ammo_magazine > 0:
            return True
        started = self._start_reload_for(player)
        if show_message and not started:
            self.message = f"J{player.player_index + 1} sem municao: lute corpo a corpo e colete cartuchos."
            self.add_alert(player.pos, "Sem balas! Colete cartuchos.", COLORS["danger"], flash_target="ammo")
        elif show_message:
            self.message = f"J{player.player_index + 1}: pente vazio, recarregando."
            self.add_alert(player.pos, "Pente vazio! Recarregando...", COLORS["coin"], flash_target="ammo")
        return False


    def _start_forced_reload(self, show_message=True):
        player = self.player
        player.mode = "weapon_2"
        player.forced_reload = True
        if player.ammo_reserve <= 0:
            if show_message:
                self.message = "Sem municao: lute corpo a corpo e colete cartuchos."
            return False
        player.reload_duration = self.current_reload_duration()
        player.reload_timer = player.reload_duration
        if show_message:
            self.message = "Pente vazio: arma corpo a corpo ativa enquanto recarrega."
        return True

    def _finish_reload(self):
        player = self.player
        capacity = self.magazine_capacity()
        needed = max(0, capacity - player.ammo_magazine)
        loaded = min(needed, player.ammo_reserve)
        if loaded <= 0:
            player.reload_timer = 0
            player.reload_duration = 0
            player.forced_reload = True
            self.message = "Sem municao na reserva."
            return

        player.ammo_magazine += loaded
        player.ammo_reserve -= loaded
        player.reload_timer = 0
        player.reload_duration = 0
        was_forced = player.forced_reload
        player.forced_reload = False
        if was_forced:
            player.mode = "weapon_1"
            self.message = "Recarga completa: arma de distancia pronta."

    def _consume_ranged_ammo(self):
        player = self.player
        if not self._ranged_weapon_ready(show_message=True):
            return False
        player.ammo_magazine = max(0, player.ammo_magazine - 1)
        if player.ammo_magazine <= 0:
            self._start_forced_reload(show_message=True)
        return True

    def _consume_ranged_ammo_for(self, player):
        if player.reload_timer > 0:
            return False
        if player.ammo_magazine > 0:
            player.ammo_magazine = max(0, player.ammo_magazine - 1)
            if player.ammo_magazine <= 0:
                self._start_reload_for(player)
            return True
        self._start_reload_for(player)
        return False

    def _start_reload_for(self, player, forced=True, show_message=True):
        player.mode = "weapon_2"
        if forced:
            player.forced_reload = True
        
        capacity = self.magazine_capacity_for(player)
        if player.ammo_magazine >= capacity or player.ammo_reserve <= 0:
            if forced and show_message:
                self.message = f"J{player.player_index + 1} sem municao: lute corpo a corpo e colete cartuchos."
            return False

        reload_bonus = (
            player.passives.get("combat_drill", 0) * 0.015
            + player.passives.get("predator_focus", 0) * 0.015
            + player.reload_speed_bonus
        )
        player.reload_duration = max(0.75, RELOAD_DURATION * (1.0 - min(0.35, reload_bonus)))
        
        needed = capacity - player.ammo_magazine
        loaded = min(needed, player.ammo_reserve)
        time_per_bullet = player.reload_duration / capacity
        
        player.reload_timer = time_per_bullet * loaded
        player.reload_step_timer = time_per_bullet
        
        if forced and show_message:
            self.message = f"J{player.player_index + 1}: pente vazio: arma corpo a corpo ativa enquanto recarrega."
        return True

    def effective_speed_multiplier(self):
        chrono = self.item_level("chrono_boots")
        return self.player.speed_multiplier() * (1.0 + chrono * 0.015)

    def current_dash_cooldown(self):
        chrono = self.item_level("chrono_boots")
        hybrid = self.hybrid_level()
        reduction = min(0.45, chrono * 0.025 + hybrid * 0.015)
        return max(0.55, DASH_COOLDOWN * (1.0 - reduction))

    def current_dash_cooldown_for(self, player):
        inv = self.get_inventory(player.player_index)
        chrono = inv.active_effect_level("chrono_boots")
        hybrid = inv.active_hybrid_level()
        reduction = min(0.45, chrono * 0.025 + hybrid * 0.015)
        return max(0.55, DASH_COOLDOWN * (1.0 - reduction))

    def effective_attack_rate_multiplier(self):
        return self.effective_attack_rate_multiplier_for(self.player, self.inventory)

    def ranged_damage_multiplier(self):
        return (
            1.0
            + self.passive_level("combat_drill") * 0.025
            + self.passive_level("predator_focus") * 0.020
            + self.passive_level("piercing_rounds") * 0.015
            + self.passive_level("mourning_pierce") * 0.012
        )

    def melee_damage_multiplier(self):
        return (
            1.0
            + self.passive_level("combat_drill") * 0.025
            + self.passive_level("predator_focus") * 0.020
            + self.passive_level("fan_blades") * 0.018
            + self.passive_level("harvest_heal") * 0.010
        )

    def projectile_damage(self):
        return self.projectile_damage_for(self.player, self.inventory)

    def sword_damage(self):
        return self.sword_damage_for(self.player, self.inventory)

    def sword_radius(self):
        return self.sword_radius_for(self.player, self.inventory)

    def sword_arc(self):
        return self.sword_arc_for(self.player)

    def dagger_arc(self):
        return self.dagger_arc_for(self.player)

    def special_damage(self):
        return self.special_damage_for(self.player)

    def special_radius(self):
        return self.special_radius_for(self.player)

    def special_damage_for(self, player):
        return atributos.special_damage_for(player)

    def special_radius_for(self, player):
        return atributos.special_radius_for(player)

    def incoming_damage_multiplier(self):
        """Multiplicador de dano recebido para self.player (single-player helper)."""
        guardian_reduction = self.player.item_guardian_reduction
        defense_reduction = getattr(self.player, "defense_bonus", 0.0)
        if guardian_reduction <= 0 and defense_reduction <= 0:
            return 1.0
        low_health_bonus = 0.10 + guardian_reduction if guardian_reduction > 0 and self.player.health / self.player.max_health <= 0.42 else 0.0
        return max(0.45, 1.0 - defense_reduction - low_health_bonus)

    def effective_attack_rate_multiplier_for(self, player, inv):
        return atributos.effective_attack_rate_multiplier_for(self, player, inv)

    def projectile_damage_for(self, player, inv):
        return atributos.projectile_damage_for(self, player, inv)

    def sword_damage_for(self, player, inv):
        return atributos.sword_damage_for(self, player, inv)

    def projectile_radius_for(self, player, base_radius=PROJECTILE_RADIUS):
        return atributos.projectile_radius_for(self, player, base_radius)

    def sword_radius_for(self, player, inv):
        return atributos.sword_radius_for(self, player, inv)

    def sword_arc_for(self, player):
        return atributos.sword_arc_for(player)

    def dagger_arc_for(self, player):
        return atributos.dagger_arc_for(player)

    def ranged_projectiles_per_salvo(self, player):
        if player.char_class == "vanguard":
            return 3 + max(0, player.passives.get("multishot", 0))
        if player.char_class == "reaper":
            volley = player.passives.get("funeral_volley", 0)
            extra = 1 if volley > 0 else 0
            if volley >= 6:
                extra += 1
            return 2 + extra
        if player.char_class == "huntress":
            split_level = player.passives.get("splinter_arrows", 0)
            side_pairs = 0 if split_level <= 0 else 1 + split_level // 6
            return 3 + side_pairs * 2
        return 1

    def _flag_ranged_attack_for_quest(self):
        if self.quest and self.quest["goal_type"] == "survive_melee":
            self._fail_quest()

    def _append_projectile_if_room(self, projectile):
        if len(self.projectiles) >= MAX_PROJECTILES:
            return False
        self.projectiles.append(projectile)
        return True

    def _is_blood_marked(self, enemy):
        return sangue.is_blood_marked(enemy)

    def _apply_blood_mark(self, enemy, player, bonus_duration=0.0, level_bonus=0):
        return sangue.apply_blood_mark(enemy, player, bonus_duration, level_bonus)

    def _consume_blood_mark(self, enemy, player, special_gain_scale=1.0):
        return sangue.consume_blood_mark(self, enemy, player, special_gain_scale)

    def _spread_blood_mark(self, center, player, radius, max_targets=2):
        return sangue.spread_blood_mark(self, center, player, radius, max_targets)

    def _reward_reaper_mark_kill(self, enemy, killer):
        if killer.char_class != "reaper":
            return
        marked_value = max(getattr(enemy, "blood_mark_level", 0), getattr(enemy, "blood_harvest_value", 0))
        if marked_value <= 0:
            return

        heal_level = killer.passives.get("harvest_heal", 0)
        if heal_level > 0 and killer.health < killer.max_health:
            heal = min(killer.max_health - killer.health, 2.0 + heal_level * 1.15 + marked_value * 0.6)
            if heal > 0:
                killer.health += heal
                self.add_floater(killer.pos, f"+{heal:.0f}", COLORS["health"])

        reload_level = killer.passives.get("scarlet_reload", 0)
        if reload_level > 0:
            capacity = self.magazine_capacity_for(killer)
            restored = min(capacity - killer.ammo_magazine, 1 + reload_level // 4 + (1 if marked_value >= 2 else 0))
            if restored > 0:
                killer.ammo_magazine += restored
                killer.forced_reload = False
                if killer.reload_timer > 0:
                    killer.reload_timer = max(0.0, killer.reload_timer - 0.24 * restored)
                if killer.mode == "weapon_2":
                    killer.mode = "weapon_1"
                self.add_floater(killer.pos, f"+{restored} pente", "#FCA5A5")

        chain_level = killer.passives.get("funeral_chain", 0)
        if chain_level > 0:
            self._spread_blood_mark(enemy.pos, killer, 110 + chain_level * 10, max_targets=1 + chain_level // 5)

    def _fire_vanguard_primary(self, player, direction, inv):
        return vanguarda_combate.fire_primary(self, player, direction, inv)

    def _fire_huntress_primary(self, player, direction, inv):
        return cacadora_combate.fire_primary(self, player, direction, inv)

    def _fire_reaper_primary(self, player, direction, inv):
        return ceifadora_combate.fire_primary(self, player, direction, inv)

    def _segment_enemies(self, start, end, width):
        hits = []
        segment = end - start
        length_sq = max(0.001, segment.length_squared())
        for enemy in list(self.enemies):
            radius_sq = (width * 0.5 + enemy.radius) ** 2
            if self._point_segment_distance_sq(enemy.pos, start, end) > radius_sq:
                continue
            progress = max(0.0, min(1.0, (enemy.pos - start).dot(segment) / length_sq))
            hits.append((progress, enemy))
        hits.sort(key=lambda entry: entry[0])
        return hits

    def _fire_engineer_primary(self, player, direction, inv):
        return engenheiro_combate.fire_primary(self, player, direction, inv)

    def _swing_vanguard_melee(self, player, direction, inv):
        return vanguarda_combate.swing_melee(self, player, direction, inv)

    def _swing_huntress_melee(self, player, direction, inv):
        return cacadora_combate.swing_melee(self, player, direction, inv)

    def _swing_engineer_melee(self, player, direction, inv):
        return engenheiro_combate.swing_melee(self, player, direction, inv)

    def _swing_reaper_melee(self, player, direction, inv):
        return ceifadora_combate.swing_melee(self, player, direction, inv)

    def _auto_attack(self, dt, aim_world):
        self._auto_attack_for(dt, aim_world, self.player)

    def _auto_attack_for(self, dt, aim_world, player):
        return auto_attack_for(self, dt, Vector2(aim_world), player)

    def _update_projectiles(self, dt):
        alive = []
        for projectile in self.projectiles:
            if projectile.homing_level > 0 and projectile.life > 0:
                best_target = None
                best_dist = 400**2
                for enemy in self.enemies:
                    if enemy.id in projectile.hit_ids: continue
                    d = projectile.pos.distance_squared_to(enemy.pos)
                    if d < best_dist:
                        best_dist = d
                        best_target = enemy
                if best_target:
                    direction = (best_target.pos - projectile.pos).normalize()
                    speed = projectile.vel.length()
                    new_dir = (projectile.vel.normalize() * 0.9 + direction * 0.1 * projectile.homing_level).normalize()
                    projectile.vel = new_dir * speed

            projectile.life -= dt
            projectile.pos += projectile.vel * dt
            if projectile.life <= 0 or self.world.circle_hits_wall(projectile.pos, projectile.radius, include_destructibles=False):
                if projectile.explosive_level > 0:
                    self.item_events.append({
                        "type": "explosion",
                        "pos": Vector2(projectile.pos),
                        "radius": 40 + projectile.explosive_level * 12,
                        "damage": projectile.damage * (0.5 + projectile.explosive_level * 0.15),
                        "age": 0,
                        "duration": 0.2
                    })
                continue

            hit = False
            min_damage_required = (SWORD_DAMAGE // 10) * 10 - 5
            for item in self.world.nearby_destructibles(projectile.pos.x, projectile.pos.y, projectile.radius + 24):
                if item.id in projectile.hit_ids:
                    continue
                if circle_rect_overlap(projectile.pos.x, projectile.pos.y, projectile.radius, item.rect):
                    projectile.hit_ids.add(item.id)
                    hit = True
                    if projectile.damage >= min_damage_required:
                        self.damage_destructible(item, projectile.damage)
                    break
            if hit:
                if projectile.explosive_level > 0:
                    self.item_events.append({
                        "type": "explosion",
                        "pos": Vector2(projectile.pos),
                        "radius": 40 + projectile.explosive_level * 12,
                        "damage": projectile.damage * (0.5 + projectile.explosive_level * 0.15),
                        "age": 0,
                        "duration": 0.2
                    })
                if projectile.pierce > 0:
                    projectile.pierce -= 1
                    alive.append(projectile)
                elif self._try_ricochet(projectile):
                    alive.append(projectile)
                continue

            for enemy in list(self.enemies):
                if enemy.id in projectile.hit_ids:
                    continue
                if projectile.pos.distance_squared_to(enemy.pos) <= (projectile.radius + enemy.radius) ** 2:
                    projectile.hit_ids.add(enemy.id)
                    owner_player = self.get_player(projectile.owner)
                    damage = projectile.damage
                    if owner_player.char_class == "reaper" and projectile.style == "reaper_needle" and self._is_blood_marked(enemy):
                        damage *= 1.0 + owner_player.passives.get("mourning_pierce", 0) * 0.05 + getattr(enemy, "blood_mark_level", 0) * 0.06
                    if projectile.freeze:
                        enemy.frozen_timer = max(enemy.frozen_timer, FREEZE_DURATION)
                    if projectile.poison:
                        enemy.poison_timer = max(enemy.poison_timer, POISON_DURATION)
                        enemy.poison_dps = max(enemy.poison_dps, projectile.poison_dps)
                    if projectile.mark_level > 0 and owner_player.char_class == "reaper":
                        self._apply_blood_mark(enemy, owner_player, bonus_duration=projectile.mark_duration, level_bonus=projectile.mark_level - 1)
                    if projectile.knockback > 0 and not getattr(enemy, "immune_to_knockback", False):
                        push = enemy.pos - projectile.pos
                        if push.length_squared() > 0:
                            enemy.knockback += push.normalize() * projectile.knockback
                    self.damage_enemy(enemy, damage, source="projectile", killer_index=projectile.owner)
                    self._apply_stamp_on_hit(enemy, damage, "weapon_1", projectile.owner)

                    if projectile.pierce > 0:
                        projectile.pierce -= 1
                        alive.append(projectile)
                    elif self._try_ricochet(projectile):
                        alive.append(projectile)
                    else:
                        if projectile.explosive_level > 0:
                            self.item_events.append({
                                "type": "explosion",
                                "pos": Vector2(projectile.pos),
                                "radius": 40 + projectile.explosive_level * 12,
                                "damage": projectile.damage * (0.5 + projectile.explosive_level * 0.15),
                                "age": 0,
                                "duration": 0.2
                            })
                    hit = True
                    break

            if not hit:
                alive.append(projectile)

        self.projectiles = alive

    def _try_ricochet(self, projectile):
        if projectile.bounces_left <= 0:
            return False

        target = None
        target_distance = RICOCHET_RANGE * RICOCHET_RANGE
        for enemy in self.enemies:
            if enemy.id in projectile.hit_ids:
                continue
            distance_sq = projectile.pos.distance_squared_to(enemy.pos)
            if distance_sq < target_distance:
                target = enemy
                target_distance = distance_sq

        if target is None:
            return False

        direction = target.pos - projectile.pos
        if direction.length_squared() <= 0:
            return False

        direction = direction.normalize()
        projectile.vel = direction * PROJECTILE_SPEED
        projectile.pos += direction * (projectile.radius + 8)
        projectile.damage *= RICOCHET_DAMAGE_MULTIPLIER
        projectile.bounces_left -= 1
        projectile.life = max(projectile.life, 0.28)
        return True

    def _update_slashes(self, dt):
        alive = []
        for slash in self.slashes:
            slash.age += dt
            self._apply_slash_hits(slash)
            if slash.age < slash.duration:
                alive.append(slash)
        self.slashes = alive

    def _apply_slash_hits(self, slash):
        owner = self.get_player(slash.owner)
        origin = owner.pos
        slash.origin = Vector2(origin)
        for enemy in list(self.enemies):
            if enemy.id in slash.hit_ids:
                continue
            to_enemy = enemy.pos - origin
            distance_sq = to_enemy.length_squared()
            if distance_sq > (slash.radius + enemy.radius) ** 2 or distance_sq <= 0:
                continue
            if slash.direction.angle_to(to_enemy) ** 2 <= math.degrees(slash.arc * 0.5) ** 2:
                slash.hit_ids.add(enemy.id)
                hit_pos = Vector2(enemy.pos)
                hit_dir = to_enemy.normalize()
                consumed_mark = 0
                if slash.knockback > 0 and not getattr(enemy, "immune_to_knockback", False):
                    enemy.knockback += hit_dir * slash.knockback
                if slash.pull_strength > 0 and not getattr(enemy, "immune_to_knockback", False):
                    pull = origin - enemy.pos
                    if pull.length_squared() > 0:
                        enemy.knockback += pull.normalize() * slash.pull_strength
                damage = slash.damage
                if slash.consume_mark:
                    consumed_mark = self._consume_blood_mark(enemy, owner)
                    if consumed_mark > 0:
                        damage *= 1.0 + consumed_mark * 0.18 + owner.passives.get("blood_mark", 0) * 0.015
                if slash.prey_mark_level > 0:
                    enemy.speed *= max(0.4, 1.0 - 0.05 * slash.prey_mark_level)
                    damage *= 1.0 + 0.1 * slash.prey_mark_level
                if slash.execute_level > 0 and enemy.health <= enemy.max_health * 0.42:
                    damage *= 1.0 + 0.08 * slash.execute_level
                if slash.bleed_level > 0:
                    enemy.bleed_timer = max(enemy.bleed_timer, 2.2 + slash.bleed_level * 0.12)
                    enemy.bleed_dps = max(enemy.bleed_dps, 4.0 + slash.bleed_level * 2.2)
                if slash.heavy_alloy_level > 0:
                    damage *= 1.0 + 0.05 * slash.heavy_alloy_level
                if slash.magnetic_pull_level > 0 and not getattr(enemy, "immune_to_knockback", False):
                    extra_pull = origin - enemy.pos
                    if extra_pull.length_squared() > 0:
                        enemy.knockback += extra_pull.normalize() * (28 + slash.magnetic_pull_level * 18)
                if slash.shadow_lunge_level > 0:
                    owner.dash_cooldown = max(0, owner.dash_cooldown - 0.035 * slash.shadow_lunge_level)
                    owner.invulnerable_timer = max(owner.invulnerable_timer, 0.02 * slash.shadow_lunge_level)
                self.damage_enemy(enemy, damage, source="sword", killer_index=slash.owner)
                self._apply_stamp_on_hit(enemy, damage, "weapon_2", slash.owner)
                if slash.mark_level > 0 and owner.char_class == "reaper":
                    self._apply_blood_mark(enemy, owner, level_bonus=slash.mark_level - 1)
                if slash.shockwave_level > 0:
                    self._apply_slash_shockwave(hit_pos, slash.shockwave_level, slash.damage, slash.hit_ids)

        for item in list(self.world.nearby_destructibles(origin.x, origin.y, slash.radius + 64)):
            marker = f"item:{item.id}"
            if marker in slash.hit_ids:
                continue
            center = item.rect.center
            to_item = center - origin
            if to_item.length_squared() > (slash.radius + 36) ** 2 or to_item.length_squared() <= 0:
                continue
            if slash.direction.angle_to(to_item) ** 2 <= math.degrees(slash.arc * 0.5) ** 2:
                slash.hit_ids.add(marker)
                self.damage_destructible(item, slash.damage)

    def _apply_slash_shockwave(self, center, level, base_damage, hit_ids):
        radius = 52 + level * 7
        damage = base_damage * (0.14 + level * 0.035)
        for other in list(self.enemies):
            if other.id in hit_ids:
                continue
            if other.pos.distance_squared_to(center) > (radius + other.radius) ** 2:
                continue
            hit_ids.add(other.id)
            push = other.pos - center
            if push.length_squared() > 0:
                other.knockback += push.normalize() * (95 + level * 8)
            self.damage_enemy(other, damage, source="sword")

    def _apply_stamp_on_hit(self, enemy, damage, weapon_key, owner_index=0):
        player = self.get_player(owner_index)
        for stamp in stamps_equipped_for_weapon(player, weapon_key):
            value = stamp_effect_value(stamp)
            if stamp.key == "lifesteal" and player.health < player.max_health:
                heal = min(player.max_health - player.health, damage * value)
                if heal > 0:
                    player.health += heal
                    self.add_floater(player.pos, f"+{heal:.0f}", COLORS["health"])
            elif stamp.key == "blast" and self.random.random() < value:
                self.item_events.append({
                    "type": "explosion",
                    "pos": Vector2(enemy.pos),
                    "radius": 54 + stamp.level * 12,
                    "damage": damage * 0.30,
                    "age": 0,
                    "duration": 0.22,
                    "owner": owner_index,
                })
                self.emit_particles(enemy.pos, count=12, color="#F97316", speed=130, size=4)
            elif stamp.key == "frost" and self.random.random() < value:
                enemy.frozen_timer = max(enemy.frozen_timer, 3.0)
            elif stamp.key == "toxic" and self.random.random() < value:
                enemy.poison_timer = max(enemy.poison_timer, 4.0)
                enemy.poison_dps = max(enemy.poison_dps, 12.0 + stamp.level * 3.0)
            elif stamp.key == "repulse":
                push = enemy.pos - player.pos
                if push.length_squared() > 0:
                    enemy.knockback += push.normalize() * value

    def _damage_player(self, amount, source="hit"):
        if amount <= 0 or self.player.shield_timer > 0 or self.player.invulnerable_timer > 0:
            return False
        self.player.health -= amount * self.incoming_damage_multiplier()
        if amount >= 1:
            self.add_floater(self.player.pos, f"-{int(amount)}", COLORS["danger"])
        return True

    def _damage_player_direct(self, player, amount, source="hit"):
        if amount <= 0 or player.shield_timer > 0 or player.invulnerable_timer > 0:
            return False
        # Usa o bônus de guardian_plate pré-calculado pelo buff_applicator
        guardian_reduction = getattr(player, "item_guardian_reduction", 0.0)
        defense_reduction = getattr(player, "defense_bonus", 0.0)
        mult = max(0.45, 1.0 - defense_reduction)
        if guardian_reduction > 0 and player.health / player.max_health <= 0.42:
            mult = max(0.45, mult - (0.10 + guardian_reduction))
        final_amount = amount * mult
        player.health -= final_amount
        self.director_recent_damage_taken = getattr(self, "director_recent_damage_taken", 0.0) + final_amount
        if amount >= 1:
            self.add_floater(player.pos, f"-{int(amount)}", COLORS["danger"])
        return True

    def _apply_area_damage(self, center, radius, damage, source, ignore_enemy=None, damage_players=True):
        center = Vector2(center)
        if damage_players:
            for player in self.alive_players():
                if player.pos.distance_squared_to(center) <= (radius + player.radius) ** 2:
                    self._damage_player_direct(player, damage, source=source)

        for enemy in list(self.enemies):
            if enemy is ignore_enemy:
                continue
            if enemy.pos.distance_squared_to(center) <= (radius + enemy.radius) ** 2:
                push = enemy.pos - center
                if push.length_squared() > 0:
                    enemy.knockback += push.normalize() * 360
                self.damage_enemy(enemy, damage, source=source)

    def _apply_laser_damage(self, start, end, width, damage, ignore_enemy=None, damage_player=True, killer_index=0, knockback=0):
        if damage_player:
            for player in self.alive_players():
                radius_sq = (width * 0.5 + player.radius) ** 2
                if self._point_segment_distance_sq(player.pos, start, end) <= radius_sq:
                    self._damage_player_direct(player, damage, source="laser")

        for enemy in list(self.enemies):
            if enemy is ignore_enemy:
                continue
            enemy_radius_sq = (width * 0.5 + enemy.radius) ** 2
            if self._point_segment_distance_sq(enemy.pos, start, end) <= enemy_radius_sq:
                if knockback > 0 and not getattr(enemy, "immune_to_knockback", False):
                    direction = enemy.pos - start
                    if direction.length_squared() > 0:
                        enemy.knockback += direction.normalize() * knockback
                self.damage_enemy(enemy, damage, source="laser", killer_index=killer_index)

    def _repel_enemies(self, dt, player=None):
        if player is None:
            player = self.player
        for enemy in self.enemies:
            distance = enemy.pos.distance_to(player.pos)
            if 0 < distance < 130:
                direction = (enemy.pos - player.pos).normalize()
                enemy.pos = self.world.move_circle(
                    enemy.pos,
                    enemy.radius,
                    direction * 280 * dt,
                    include_destructibles=False,
                )
                enemy.knockback += direction * 180 * dt

    def _detonate_mine(self, hazard, trigger_pos):
        self.world.remove_hazard(hazard)
        damage_players = not str(getattr(hazard, "id", "")).startswith("dash_mine:")
        self._apply_area_damage(trigger_pos, MINE_EXPLOSION_RADIUS, MINE_DAMAGE, "mine", damage_players=damage_players)
        self.item_events.append({
            "type": "explosion",
            "pos": Vector2(trigger_pos),
            "radius": MINE_EXPLOSION_RADIUS,
            "damage": 0,
            "age": 0.0,
            "duration": 0.32,
        })
        self.emit_particles(trigger_pos, count=26, color=COLORS["coin"], speed=240, lifetime=0.42, size=5)
        self.screen_shake = max(self.screen_shake, 12.0)
        self.message = "Mina terrestre detonada."

    def damage_enemy(self, enemy, amount, source="hit", killer_index=0):
        if enemy.kind != "bulwark" and source not in ("fire", "mine", "special"):
            for protector in self.enemies:
                if protector.kind == "bulwark" and protector.health > 0:
                    if protector.pos.distance_squared_to(enemy.pos) <= 220 * 220:
                        amount *= 0.72
                        break

        # Reações Elementares e Combos
        # 1. Choque Térmico: Dano físico/corte/tiro em inimigo Congelado
        if getattr(enemy, "frozen_timer", 0.0) > 0.0:
            enemy.frozen_timer = 0.0
            shock_damage = amount * 1.5 + 60.0
            amount += shock_damage
            self.add_floater(enemy.pos, "CHOQUE TERMICO!", "#38BDF8")
            self.emit_particles(enemy.pos, count=16, color="#06B6D4", speed=150, size=4)
            self.screen_shake = max(self.screen_shake, 3.5)

        # 2. Hemotoxina: Veneno + Sangramento ativos simultaneamente
        if getattr(enemy, "poison_timer", 0.0) > 0.0 and getattr(enemy, "bleed_timer", 0.0) > 0.0:
            p_dps = getattr(enemy, "poison_dps", 0.0)
            b_dps = getattr(enemy, "bleed_dps", 0.0)
            enemy.poison_timer = 0.0
            enemy.bleed_timer = 0.0
            toxin_damage = (p_dps + b_dps) * 4.0
            if toxin_damage <= 0:
                toxin_damage = 50.0
            amount += toxin_damage
            self.add_floater(enemy.pos, "HEMOTOXINA!", "#A855F7")
            self.emit_particles(enemy.pos, count=18, color="#10B981", speed=160, size=4)
            self.emit_particles(enemy.pos, count=18, color="#8B5CF6", speed=160, size=4)
            self.screen_shake = max(self.screen_shake, 4.0)

        resistance = getattr(enemy, "damage_resistance", 0.0)
        if resistance > 0 and source in ("projectile", "sword", "special", "laser", "storm"):
            amount *= max(0.0, 1.0 - resistance)
        enemy.health -= amount
        enemy.hit_flash = 0.08
        self.emit_particles(enemy.pos, count=3, color="#DC2626", speed=80, size=3)
        if amount >= 1:
            self.add_floater(enemy.pos, str(int(amount)), "#FDE68A" if source == "sword" else "#BAE6FD")
        if enemy.health <= 0 and enemy in self.enemies:
            self.kill_enemy(enemy, source=source, killer_index=killer_index)

    def kill_enemy(self, enemy, source="hit", killer_index=0):
        self.enemies.remove(enemy)
        killer = self.get_player(killer_index)
        killer.kills += 1
        self.kill_counts[enemy.kind] = self.kill_counts.get(enemy.kind, 0) + 1
        self.director_recent_kills = getattr(self, "director_recent_kills", 0) + 1
        self.register_kill_combo()
        self.emit_particles(enemy.pos, count=15, color="#991B1B", speed=120, size=5)
        killer.score += int(enemy.xp_value * 10 + self.time_alive)

        # Increase dynamic heat level on kill!
        gain = 3.5
        ekind = getattr(enemy, "kind", "")
        if ekind == "brute":
            gain = 12.0
        elif ekind == "sapper":
            gain = 7.0
        elif ekind == "phantom":
            gain = 6.0
        elif ekind == "miniboss":
            gain = 35.0
        elif ekind == "reaper":
            gain = 45.0
        elif ekind in ("morcego_sombra", "lobo_infectado"):
            gain = 8.0
            
        self.heat_level = min(100.0, getattr(self, "heat_level", 0.0) + gain)

        # Quest hooks (team-based)
        if self.quest:
            gt = self.quest["goal_type"]
            if gt == "kill_count":
                self.quest_progress += 1
            elif gt == "kill_brutes" and enemy.kind == "brute":
                self.quest_progress += 1

        if source != "special":
            self._add_special_from_source(enemy.special_value, source, killer)
        if killer.vampirism > 0 and killer.health < killer.max_health:
            heal = min(killer.vampirism, killer.max_health - killer.health)
            killer.health += heal
            if heal > 0:
                self.add_floater(killer.pos, f"+{heal:.0f}", COLORS["health"])
        self._apply_kill_resource_passives(enemy, source, killer)
        if killer.char_class == "engineer":
            necro = killer.passives.get("robotic_necromancy", 0)
            if necro > 0 and self.random.random() < min(0.72, 0.18 + necro * 0.055):
                level = max(1, necro)
                self._spawn_engineer_construct(enemy.pos + self.random_offset(36), "robo_minion", killer.player_index, level=level, duration=9.0 + level * 0.85)
                self.add_floater(enemy.pos, "ROBO-ALIADO", "#EAB308")
        elif killer.char_class == "reaper":
            self._reward_reaper_mark_kill(enemy, killer)

        if enemy.kind == "harbinger":
            self.harbinger_defeats = getattr(self, "harbinger_defeats", 0) + 1
            if getattr(self, "current_dimension", "main") == "pocket":
                self.spawn_drop("exit_portal", enemy.pos)
                self.message = "O Arauto Sombrio caiu. O caminho esta livre."
                self.screen_shake = max(self.screen_shake, 22.0)
                self._grant_random_reward(enemy.pos, strong=True, player_index=killer_index)
            else:
                self.harbinger_spawn_timer = HARBINGER_SPAWN_INTERVAL
                self.screen_shake = max(self.screen_shake, 22.0)
                self.message = "Arauto do Fim derrotado. Ele voltara mais forte."
                self._grant_random_reward(enemy.pos, strong=True, player_index=killer_index)

        if enemy.kind == "reaper":
            self.reaper_defeats = getattr(self, "reaper_defeats", 0) + 1
            self.reaper_spawn_timer = REAPER_SPAWN_INTERVAL
            self.reaper_area_anchor = Vector2(self.camera_focus)
            self.reaper_area_linger = 0.0
            self.reaper_pressure_level = 0.0
            self.screen_shake = max(self.screen_shake, 28.0)
            self.message = "Ceifador da Margem derrotado. Ele retornara ainda mais forte."
            self._grant_random_reward(enemy.pos, strong=True, player_index=killer_index)

        if enemy.kind == "god":
            self.message = "Deus derrotado! Retornando ao mundo mortal..."
            self.screen_shake = max(self.screen_shake, 40.0)
            self._grant_random_reward(enemy.pos, strong=True, player_index=killer_index)
            self.exit_olympus_dimension()
            self.spawn_drop("item_box", enemy.pos + self.random_offset(18), 1)
            self.spawn_drop("stamp", enemy.pos + self.random_offset(28), self.random.choice(ALL_DROPPABLE_STAMP_KEYS))

        if enemy.kind == "miniboss":
            self._grant_miniboss_reward(enemy.pos, killer_index)
            return

        self.spawn_drop("xp", enemy.pos, enemy.xp_value)
        ammo_amount = self._ammo_drop_amount(enemy)
        if ammo_amount > 0:
            self.spawn_drop("ammo", enemy.pos + self.random_offset(20), ammo_amount)
        heat_ratio = getattr(self, "heat_level", 0.0) / 100.0
        coin_chance = enemy.coin_chance + heat_ratio * 0.15
        heal_chance = 0.035 + heat_ratio * 0.02
        shield_chance = 0.018 + heat_ratio * 0.015
        box_chance = 0.006 + heat_ratio * 0.045
        if enemy.kind in ("brute", "chromatic", "bulwark", "golem", "necromancer"):
            box_chance += 0.010
        tier_rank = getattr(enemy, "tier_rank", 0)
        if tier_rank > 0:
            coin_chance += tier_rank * 0.025
            box_chance += tier_rank * 0.010
            stamp_chance_bonus = tier_rank * 0.010
        else:
            stamp_chance_bonus = 0.0

        if self.random.random() < coin_chance:
            self.spawn_drop("coin", enemy.pos + self.random_offset(18), 1)
        if self.random.random() < heal_chance:
            self.spawn_drop("heal", enemy.pos + self.random_offset(22), 22)
        if self.random.random() < shield_chance:
            self.spawn_drop("shield", enemy.pos + self.random_offset(22), 1)
        if self.random.random() < box_chance:
            self.spawn_drop("item_box", enemy.pos + self.random_offset(24), 1)
        stamp_chance = 0.010 + heat_ratio * 0.030 + stamp_chance_bonus
        if enemy.kind in ("brute", "chromatic", "miniboss", "reaper"):
            stamp_chance += 0.020
        if self.random.random() < stamp_chance:
            self.spawn_drop("stamp", enemy.pos + self.random_offset(28), self.random.choice(ALL_DROPPABLE_STAMP_KEYS))
        if enemy.kind == "chromatic":
            self._grant_random_reward(enemy.pos, strong=False, player_index=killer_index)

    def damage_destructible(self, item, amount):
        item.hp -= amount
        item.hit_flash = 0.08
        if item.hp <= 0:
            self.destroy_destructible(item)

    def destroy_destructible(self, item):
        center = item.rect.center
        self.world.remove_destructible(item)
        if item.kind == "special":
            self.spawn_drop("item_box", center + self.random_offset(16), 1)
            self.spawn_drop("coin", center + self.random_offset(20), 1)
            return

        self.spawn_drop("coin", center + self.random_offset(18), 1)
        
        # Rare chance of global magnet (vacuum)
        if self.random.random() < 0.025:
            self.spawn_drop("vacuum", center + self.random_offset(20), 1)
            
        roll = self.random.random()
        if roll < 0.18:
            self.spawn_drop("heal", center + self.random_offset(22), 20)
        elif roll < 0.28:
            self.spawn_drop("shield", center + self.random_offset(22), 1)
        elif roll < 0.45:
            self.spawn_drop("xp", center + self.random_offset(22), 8)
        elif item.kind == "cache" and roll < 0.58:
            self.spawn_drop("item_box", center + self.random_offset(22), 1)

    def _point_segment_distance_sq(self, point, start, end):
        segment = end - start
        length_sq = segment.length_squared()
        if length_sq <= 0.001:
            return point.distance_squared_to(start)
        t = max(0.0, min(1.0, (point - start).dot(segment) / length_sq))
        closest = start + segment * t
        return point.distance_squared_to(closest)
