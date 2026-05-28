from pygame.math import Vector2
import math
if __package__:
    from ...data.constants import *
    from ...data.stamps import ALL_DROPPABLE_STAMP_KEYS, stamp_effect_value, stamps_equipped_for_weapon
    from ..entities import Projectile, Slash
    from ..world import circle_rect_overlap
else:
    from Sobrevivencia.data.constants import *
    from Sobrevivencia.data.stamps import ALL_DROPPABLE_STAMP_KEYS, stamp_effect_value, stamps_equipped_for_weapon
    from Sobrevivencia.core.entities import Projectile, Slash
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
        self._cast_combo_special(aim_world, player)
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
        if player is None:
            player = self.player
        if player.char_class == "vanguard":
            if channel == "ranged":
                self._cast_vanguard_radial(player=player)
            else:
                self._cast_vanguard_charge(aim_world, player=player)
        else:
            if channel == "ranged":
                self._cast_huntress_arrow_rain(aim_world, player=player)
            else:
                self._cast_huntress_dagger_dance(player=player)

    def _cast_combo_special(self, aim_world, player=None):
        if player is None:
            player = self.player
        if player.char_class == "vanguard":
            self._cast_vanguard_radial(multiplier=1.35, radius_multiplier=1.18, silent=True, player=player)
            self._cast_vanguard_charge(aim_world, multiplier=1.35, silent=True, player=player)
            self.message = "Combo: Protocolo Cerco!"
        else:
            self._cast_huntress_arrow_rain(aim_world, multiplier=1.25, radius_multiplier=1.18, silent=True, player=player)
            self._cast_huntress_dagger_dance(multiplier=1.30, radius_multiplier=1.18, silent=True, player=player)
            self.message = "Combo: Tempestade Predatoria!"
        self.screen_shake = max(self.screen_shake, 18.0)

    def _cast_vanguard_radial(self, multiplier=1.0, radius_multiplier=1.0, silent=False, player=None):
        if player is None:
            player = self.player
        inv = self.get_inventory(player.player_index)
        special_damage = self.special_damage_for(player) * multiplier
        special_radius = self.special_radius_for(player) * radius_multiplier
        self.special_blast_timer = 0.35
        self.screen_shake = max(self.screen_shake, 16.0)
        self.emit_particles(player.pos, count=34, color=COLORS["special"], speed=260, lifetime=0.44, size=6)
        if not silent:
            self.message = "Explosao radial liberada!"

        for enemy in list(self.enemies):
            distance = enemy.pos.distance_to(player.pos)
            if distance <= special_radius:
                direction = enemy.pos - player.pos
                if direction.length_squared() > 0:
                    enemy.knockback += direction.normalize() * 520
                self.damage_enemy(enemy, special_damage, source="special", killer_index=player.player_index)

        for item in list(self.world.nearby_destructibles(player.pos.x, player.pos.y, special_radius * 0.75)):
            if item.rect.center.distance_to(player.pos) <= special_radius * 0.75:
                self.destroy_destructible(item)

        reactor = player.passives.get("reactor_blast", 0)
        if reactor > 0:
            restored = min(self.magazine_capacity_for(player) - player.ammo_magazine, 2 + reactor * 2)
            if restored > 0:
                player.ammo_magazine += restored
                player.forced_reload = False
                player.reload_timer = 0
                player.mode = "weapon_1"
                if not silent:
                    self.message = "Explosao radial liberada! Pente reenergizado."

    def _cast_vanguard_charge(self, aim_world, multiplier=1.0, silent=False, player=None):
        if player is None:
            player = self.player
        direction = Vector2(aim_world) - player.pos
        if direction.length_squared() <= 0.01:
            direction = player.last_move_dir
        if direction.length_squared() <= 0.01:
            direction = Vector2(1, 0)
        direction = direction.normalize()
        start = Vector2(player.pos)
        end = start + direction * 420
        width = 78
        damage = self.special_damage_for(player) * 0.88 * multiplier
        self._apply_laser_damage(start, end, width, damage, damage_player=False, killer_index=player.player_index)
        player.pos = self.world.move_circle(player.pos, player.radius, direction * 240, include_destructibles=False)
        self.item_events.append({
            "type": "laser",
            "start": start,
            "end": end,
            "width": width,
            "age": 0.0,
            "duration": 0.26,
            "color": COLORS["sword"],
        })
        self.emit_particles(player.pos, count=18, color=COLORS["sword"], speed=210, lifetime=0.30, size=5)
        self.screen_shake = max(self.screen_shake, 12.0)
        if not silent:
            self.message = "Carga Titanica!"

    def _cast_huntress_arrow_rain(self, aim_world, multiplier=1.0, radius_multiplier=1.0, silent=False, player=None):
        if player is None:
            player = self.player
        storm_eye = player.passives.get("storm_eye", 0)
        duration = (2.0 + storm_eye * 0.12) * (1.0 + (multiplier - 1.0) * 0.5)
        self.item_events.append({
            "type": "arrow_rain",
            "pos": Vector2(aim_world),
            "timer": duration,
            "age": 0.0,
            "duration": duration,
            "damage": self.special_damage_for(player) * (0.18 + storm_eye * 0.006) * multiplier,
            "radius": self.special_radius_for(player) * 0.8 * radius_multiplier,
            "owner": player.player_index,
        })
        if not silent:
            self.message = "Chuva de Flechas!"

    def _cast_huntress_dagger_dance(self, multiplier=1.0, radius_multiplier=1.0, silent=False, player=None):
        if player is None:
            player = self.player
        radius = 260 * radius_multiplier
        damage = self.special_damage_for(player) * 0.72 * multiplier
        for enemy in list(self.enemies):
            if enemy.pos.distance_squared_to(player.pos) <= (radius + enemy.radius) ** 2:
                enemy.bleed_timer = max(enemy.bleed_timer, 4.0)
                enemy.bleed_dps = max(enemy.bleed_dps, 18.0 * multiplier)
                push = enemy.pos - player.pos
                if push.length_squared() > 0:
                    enemy.knockback += push.normalize() * 260
                self.damage_enemy(enemy, damage, source="special", killer_index=player.player_index)
        self.item_events.append({
            "type": "explosion",
            "pos": Vector2(player.pos),
            "radius": radius,
            "damage": 0,
            "age": 0.0,
            "duration": 0.32,
            "owner": player.player_index,
        })
        self.emit_particles(player.pos, count=24, color=COLORS["sword"], speed=190, lifetime=0.38, size=4)
        player.invulnerable_timer = max(player.invulnerable_timer, 0.65)
        self.screen_shake = max(self.screen_shake, 10.0)
        if not silent:
            self.message = "Danca das Adagas!"

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
        blade = self.item_level("blade_relay")
        hybrid = self.hybrid_level()
        both_bonus = self.passive_level("combat_drill") * 0.01 + self.passive_level("predator_focus") * 0.012
        return self.player.attack_rate_multiplier() * (1.0 + blade * 0.012 + hybrid * 0.01 + both_bonus)

    def ranged_damage_multiplier(self):
        return (
            1.0
            + self.passive_level("combat_drill") * 0.025
            + self.passive_level("predator_focus") * 0.020
            + self.passive_level("piercing_rounds") * 0.015
        )

    def melee_damage_multiplier(self):
        return (
            1.0
            + self.passive_level("combat_drill") * 0.025
            + self.passive_level("predator_focus") * 0.020
            + self.passive_level("fan_blades") * 0.018
        )

    def projectile_damage(self):
        storm = self.item_level("storm_core")
        return self.player.projectile_damage() * (1.0 + storm * 0.01) * self.ranged_damage_multiplier()

    def sword_damage(self):
        blade = self.item_level("blade_relay")
        return self.player.sword_damage() * (1.0 + blade * 0.012) * self.melee_damage_multiplier()

    def sword_radius(self):
        blade = self.item_level("blade_relay")
        hybrid = self.hybrid_level()
        melee_bonus = self.passive_level("wide_cleave") * 0.030 + self.passive_level("fan_blades") * 0.028
        return self.player.sword_radius() * (1.0 + blade * 0.018 + hybrid * 0.018 + melee_bonus)

    def sword_arc(self):
        return SWORD_ARC + math.radians(self.passive_level("wide_cleave") * 2.4)

    def dagger_arc(self):
        return SWORD_ARC * 0.6 + math.radians(self.passive_level("fan_blades") * 2.8)

    def special_damage(self):
        return SPECIAL_DAMAGE * (
            1.0
            + self.passive_level("reactor_blast") * 0.055
            + self.passive_level("storm_eye") * 0.040
        )

    def special_radius(self):
        return SPECIAL_RADIUS * (
            1.0
            + self.passive_level("reactor_blast") * 0.030
            + self.passive_level("storm_eye") * 0.025
        )

    def special_damage_for(self, player):
        return SPECIAL_DAMAGE * (
            1.0
            + player.passives.get("reactor_blast", 0) * 0.055
            + player.passives.get("storm_eye", 0) * 0.040
        )

    def special_radius_for(self, player):
        return SPECIAL_RADIUS * (
            1.0
            + player.passives.get("reactor_blast", 0) * 0.030
            + player.passives.get("storm_eye", 0) * 0.025
        )

    def incoming_damage_multiplier(self):
        """Multiplicador de dano recebido para self.player (single-player helper)."""
        guardian_reduction = self.player.item_guardian_reduction
        if guardian_reduction <= 0:
            return 1.0
        if self.player.health / self.player.max_health > 0.42:
            return 1.0
        return max(0.52, 1.0 - (0.10 + guardian_reduction))

    def _auto_attack(self, dt, aim_world):
        self._auto_attack_for(dt, aim_world, self.player)

    def _auto_attack_for(self, dt, aim_world, player):
        direction = Vector2(aim_world) - player.pos
        if direction.length_squared() < 0.01:
            direction = Vector2(1, 0)
        direction = direction.normalize()
        pi = player.player_index
        inv = self.get_inventory(pi)

        if player.char_class == "vanguard":
            if player.mode == "weapon_1":
                cooldown = PROJECTILE_COOLDOWN / self.effective_attack_rate_multiplier_for(player, inv)
                if player.shoot_timer <= 0 and len(self.projectiles) < MAX_PROJECTILES:
                    if not self._consume_ranged_ammo_for(player):
                        return
                    # Quest hook: fail melee_only
                    if self.quest and self.quest["goal_type"] == "survive_melee":
                        self._fail_quest()
                    count = 1 + player.passives.get("multishot", 0)
                    side = direction.rotate(90)
                    start_offset = -(count - 1) * 0.5
                    pierce = player.passives.get("piercing_rounds", 0) // 3
                    for index in range(count):
                        if len(self.projectiles) >= MAX_PROJECTILES:
                            break
                        offset = side * ((start_offset + index) * PROJECTILE_PARALLEL_SPACING)
                        self.projectiles.append(
                            Projectile(
                                pos=Vector2(player.pos) + direction * (player.radius + 8) + offset,
                                vel=direction * PROJECTILE_SPEED,
                                damage=self.projectile_damage_for(player, inv),
                                radius=self.projectile_radius_for(player),
                                freeze=player.buffs.get("freeze", 0) > 0,
                                poison=player.passives.get("poison", 0) > 0,
                                poison_dps=POISON_BASE_DPS * player.passives.get("poison", 0) * player.damage_multiplier(),
                                bounces_left=player.passives.get("ricochet", 0),
                                pierce=pierce,
                                owner=pi,
                            )
                        )
                    player.shoot_timer = cooldown
            else:
                cooldown = SWORD_COOLDOWN / self.effective_attack_rate_multiplier_for(player, inv)
                if player.sword_timer <= 0:
                    self.slashes.append(
                        Slash(
                            origin=Vector2(player.pos),
                            direction=direction,
                            radius=self.sword_radius_for(player, inv),
                            arc=self.sword_arc_for(player),
                            damage=self.sword_damage_for(player, inv),
                            execute_level=player.passives.get("execution_edge", 0),
                            shockwave_level=player.passives.get("shockwave", 0),
                            owner=pi,
                        )
                    )
                    player.sword_timer = cooldown
        else: # huntress
            if player.mode == "weapon_1":
                cooldown = (PROJECTILE_COOLDOWN * 1.3) / self.effective_attack_rate_multiplier_for(player, inv)
                if player.shoot_timer <= 0 and len(self.projectiles) < MAX_PROJECTILES:
                    if not self._consume_ranged_ammo_for(player):
                        return
                    # Quest hook: fail melee_only
                    if self.quest and self.quest["goal_type"] == "survive_melee":
                        self._fail_quest()
                    split_level = player.passives.get("splinter_arrows", 0)
                    side_pairs = 0 if split_level <= 0 else 1 + split_level // 6
                    angles = [0]
                    for pair in range(1, side_pairs + 1):
                        angles.extend((10 * pair, -10 * pair))
                    for angle in angles:
                        if len(self.projectiles) >= MAX_PROJECTILES:
                            break
                        shot_dir = direction.rotate(angle)
                        extra = angle != 0
                        self.projectiles.append(
                            Projectile(
                                pos=Vector2(player.pos) + shot_dir * (player.radius + 8),
                                vel=shot_dir * PROJECTILE_SPEED * 1.5,
                                damage=self.projectile_damage_for(player, inv) * (1.2 if not extra else 0.58 + split_level * 0.018),
                                radius=self.projectile_radius_for(player),
                                freeze=player.buffs.get("freeze", 0) > 0,
                                pierce=2 if not extra else max(0, split_level // 5),
                                explosive_level=player.passives.get("explosive", 0),
                                homing_level=player.passives.get("homing", 0),
                                owner=pi,
                            )
                        )
                    player.shoot_timer = cooldown
            else:
                cooldown = (SWORD_COOLDOWN * 0.45) / self.effective_attack_rate_multiplier_for(player, inv)
                if player.sword_timer <= 0:
                    self.slashes.append(
                        Slash(
                            origin=Vector2(player.pos),
                            direction=direction,
                            radius=self.sword_radius_for(player, inv) * 0.65,
                            arc=self.dagger_arc_for(player),
                            damage=self.sword_damage_for(player, inv) * 0.45,
                            duration=SWORD_DURATION * 0.5,
                            prey_mark_level=player.passives.get("prey_mark", 0),
                            bleed_level=player.passives.get("bleeding_blades", 0),
                            shadow_lunge_level=player.passives.get("shadow_lunge", 0),
                            owner=pi,
                        )
                    )
                    player.sword_timer = cooldown

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
                    if projectile.freeze:
                        enemy.frozen_timer = max(enemy.frozen_timer, FREEZE_DURATION)
                    if projectile.poison:
                        enemy.poison_timer = max(enemy.poison_timer, POISON_DURATION)
                        enemy.poison_dps = max(enemy.poison_dps, projectile.poison_dps)
                    self.damage_enemy(enemy, projectile.damage, source="projectile", killer_index=projectile.owner)
                    self._apply_stamp_on_hit(enemy, projectile.damage, "weapon_1", projectile.owner)

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
                enemy.knockback += to_enemy.normalize() * 330
                damage = slash.damage
                if slash.prey_mark_level > 0:
                    enemy.speed *= max(0.4, 1.0 - 0.05 * slash.prey_mark_level)
                    damage *= 1.0 + 0.1 * slash.prey_mark_level
                if slash.execute_level > 0 and enemy.health <= enemy.max_health * 0.42:
                    damage *= 1.0 + 0.08 * slash.execute_level
                if slash.bleed_level > 0:
                    enemy.bleed_timer = max(enemy.bleed_timer, 2.2 + slash.bleed_level * 0.12)
                    enemy.bleed_dps = max(enemy.bleed_dps, 4.0 + slash.bleed_level * 2.2)
                if slash.shadow_lunge_level > 0:
                    owner.dash_cooldown = max(0, owner.dash_cooldown - 0.035 * slash.shadow_lunge_level)
                    owner.invulnerable_timer = max(owner.invulnerable_timer, 0.02 * slash.shadow_lunge_level)
                self.damage_enemy(enemy, damage, source="sword", killer_index=slash.owner)
                self._apply_stamp_on_hit(enemy, damage, "weapon_2", slash.owner)
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
        mult = 1.0
        if guardian_reduction > 0 and player.health / player.max_health <= 0.42:
            mult = max(0.52, 1.0 - (0.10 + guardian_reduction))
        player.health -= amount * mult
        if amount >= 1:
            self.add_floater(player.pos, f"-{int(amount)}", COLORS["danger"])
        return True

    def _apply_area_damage(self, center, radius, damage, source, ignore_enemy=None):
        center = Vector2(center)
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

    def _apply_laser_damage(self, start, end, width, damage, ignore_enemy=None, damage_player=True, killer_index=0):
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
        self._apply_area_damage(trigger_pos, MINE_EXPLOSION_RADIUS, MINE_DAMAGE, "mine")
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
        box_chance = heat_ratio * 0.025

        if self.random.random() < coin_chance:
            self.spawn_drop("coin", enemy.pos + self.random_offset(18), 1)
        if self.random.random() < heal_chance:
            self.spawn_drop("heal", enemy.pos + self.random_offset(22), 22)
        if self.random.random() < shield_chance:
            self.spawn_drop("shield", enemy.pos + self.random_offset(22), 1)
        if self.random.random() < box_chance:
            self.spawn_drop("item_box", enemy.pos + self.random_offset(24), 1)
        stamp_chance = 0.010 + heat_ratio * 0.030
        if enemy.kind in ("brute", "chromatic", "miniboss"):
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

