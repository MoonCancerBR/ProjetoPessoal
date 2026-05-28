from pygame.math import Vector2
import random
import math
if __package__:
    from ...data.constants import *
    from ..entities import Enemy, Hazard
else:
    from Sobrevivencia.data.constants import *
    from Sobrevivencia.core.entities import Enemy, Hazard

class EnemyManager:
    def _spawn_enemies(self, dt):
        heat_multiplier = 1.0 + getattr(self, "heat_level", 0.0) / 100.0 * 0.75
        difficulty = (1.0 + self.time_alive / 85.0 + (self.player.level - 1) * 0.09) * heat_multiplier
        self._update_special_spawns(dt, difficulty)

        if len(self.enemies) >= MAX_ENEMIES:
            return

        delay = max(SPAWN_MIN_DELAY, SPAWN_START_DELAY / difficulty)
        self.spawn_timer -= dt
        if self.spawn_timer > 0:
            return

        self.spawn_timer = delay
        amount = 1
        if self.time_alive > 80 and self.random.random() < 0.28:
            amount += 1
        if self.time_alive > 170 and self.random.random() < 0.18:
            amount += 1
        for _ in range(amount):
            self._spawn_one_enemy(difficulty)

    def _update_special_spawns(self, dt, difficulty):
        heat_factor = 1.0 + getattr(self, "heat_level", 0.0) / 100.0 * 1.5
        self.chromatic_spawn_timer -= dt * heat_factor
        if self.chromatic_spawn_timer <= 0:
            if len(self.enemies) < MAX_ENEMIES:
                self._spawn_special_enemy("chromatic", difficulty)
            self.chromatic_spawn_timer = self.random.uniform(CHROMATIC_SPAWN_MIN, CHROMATIC_SPAWN_MAX)

        self.miniboss_spawn_timer -= dt * (1.0 + getattr(self, "heat_level", 0.0) / 100.0 * 0.5)
        has_miniboss = any(enemy.kind == "miniboss" for enemy in self.enemies)
        if self.miniboss_spawn_timer <= 0:
            if self.time_alive > 45 and not has_miniboss and len(self.enemies) < MAX_ENEMIES:
                self._spawn_special_enemy("miniboss", difficulty)
            self.miniboss_spawn_timer = self.random.uniform(MINIBOSS_SPAWN_MIN, MINIBOSS_SPAWN_MAX)

    def _spawn_special_enemy(self, kind, difficulty):
        angle = self.random.random() * math.tau
        if kind == "chromatic":
            distance = self.random.uniform(420, 610)
            health_scale = min(2.2, 1.0 + (difficulty - 1.0) * 0.16)
            speed_scale = min(1.45, 1.0 + (difficulty - 1.0) * 0.06)
            lifetime = CHROMATIC_LIFETIME
            message = "Um Erratico Cromatico apareceu perto da tela."
        else:
            distance = self.random.uniform(650, 820)
            health_scale = min(2.4, 1.0 + (difficulty - 1.0) * 0.20)
            speed_scale = 1.0
            lifetime = -1
            message = "Mini-boss avistado: fique longe dos avisos vermelhos."

        pos = self.player.pos + Vector2(math.cos(angle), math.sin(angle)) * distance
        data = ENEMY_TYPES[kind]
        enemy = Enemy(
            id=self.enemy_id,
            pos=pos,
            kind=kind,
            radius=data["radius"],
            speed=data["speed"] * speed_scale * self.director_speed,
            max_health=data["health"] * health_scale * self.director_health,
            health=data["health"] * health_scale * self.director_health,
            damage=data["damage"] * self.director_damage,
            xp_value=data["xp"],
            color=data["color"],
            special_value=data["special"],
            coin_chance=data["coin_chance"],
            lifetime=lifetime,
            phase=self.random.random() * math.tau,
            special_timer=self.random.uniform(2.2, 4.0),
        )
        self.enemy_id += 1
        self._setup_physics_entity(enemy)

        if not self.world.circle_hits_wall(enemy.pos, enemy.radius):
            self.enemies.append(enemy)
            self.message = message
            if kind == "miniboss":
                self.miniboss_arena_center = Vector2(enemy.pos)
                self.miniboss_arena_radius = 520.0
                trapped = min(self.alive_players(), key=lambda p: p.pos.distance_to(enemy.pos), default=self.player)
                self.miniboss_trapped_player = trapped

    def _spawn_one_enemy(self, difficulty):
        angle = self.random.random() * math.tau
        distance = self.random.uniform(SPAWN_DISTANCE_MIN, SPAWN_DISTANCE_MAX)
        pos = self.player.pos + Vector2(math.cos(angle), math.sin(angle)) * distance

        is_night = getattr(self, "light_level", 1.0) < 0.15
        roll = self.random.random()
        
        if is_night:
            if roll < 0.22:
                kind = "morcego_sombra"
            elif roll < 0.44:
                kind = "lobo_infectado"
            elif roll < 0.62:
                kind = "phantom"
            elif roll < 0.80:
                kind = "runner"
            else:
                kind = "basic"
        else:
            if roll < 0.08:
                kind = "phantom"
            elif roll < 0.16:
                kind = "golem"
            elif roll < 0.24:
                kind = "necromancer"
            elif self.time_alive > 190 and roll < 0.32:
                kind = "sapper"
            elif self.time_alive > 150 and roll < 0.42:
                kind = "bulwark"
            elif self.time_alive > 95 and roll < 0.50:
                kind = "spitter"
            elif self.time_alive > 75 and roll < 0.65:
                kind = "brute"
            elif self.time_alive > 25 and roll < 0.82:
                kind = "runner"
            else:
                kind = "basic"

        data = ENEMY_TYPES[kind]
        enemy = Enemy(
            id=self.enemy_id,
            pos=pos,
            kind=kind,
            radius=data["radius"],
            speed=data["speed"] * min(1.75, 1.0 + (difficulty - 1.0) * 0.08) * self.director_speed,
            max_health=data["health"] * min(2.6, 1.0 + (difficulty - 1.0) * 0.18) * self.director_health,
            health=data["health"] * min(2.6, 1.0 + (difficulty - 1.0) * 0.18) * self.director_health,
            damage=data["damage"] * self.director_damage,
            xp_value=data["xp"],
            color=data["color"],
            special_value=data["special"],
            coin_chance=data["coin_chance"],
        )
        self.enemy_id += 1
        self._setup_physics_entity(enemy)

        if not self.world.circle_hits_wall(enemy.pos, enemy.radius):
            self.enemies.append(enemy)

    def _nearest_alive_player(self, pos):
        best_target = None
        best_dist = 999999999
        
        if getattr(self, 'escort_event_active', False) and getattr(self, 'escort_state', '') == 'escorting':
            for npc in getattr(self, 'escort_npcs', []):
                if npc.hp <= 0: continue
                d2 = pos.distance_squared_to(npc.pos)
                if d2 < best_dist:
                    best_target = npc
                    best_dist = d2
            if best_target and best_dist < 2250000:
                return best_target
                
        best_target = self.player
        best_dist = pos.distance_squared_to(self.player.pos) if not self.player.is_down else 999999999
        if self.multiplayer and self.player2 is not None and not self.player2.is_down:
            d2 = pos.distance_squared_to(self.player2.pos)
            if d2 < best_dist:
                best_target = self.player2
        return best_target

    def _update_enemies(self, dt):
        alive_list = []
        for enemy in list(self.enemies):
            enemy.phase += dt
            enemy.frozen_timer = max(0, enemy.frozen_timer - dt)
            enemy.hit_flash = max(0, enemy.hit_flash - dt)
            if enemy.lifetime > 0:
                enemy.lifetime -= dt
                if enemy.lifetime <= 0 and enemy.kind == "chromatic":
                    self.add_floater(enemy.pos, "escapou", COLORS["muted"])
                    self._cleanup_physics_entity(enemy)
                    continue
            if enemy.poison_timer > 0:
                enemy.poison_timer = max(0, enemy.poison_timer - dt)
                self.damage_enemy(enemy, enemy.poison_dps * dt, source="poison")
                if enemy.health <= 0:
                    self._cleanup_physics_entity(enemy)
                    continue
            if enemy.bleed_timer > 0:
                enemy.bleed_timer = max(0, enemy.bleed_timer - dt)
                self.damage_enemy(enemy, enemy.bleed_dps * dt, source="bleed")
                if enemy.health <= 0:
                    self._cleanup_physics_entity(enemy)
                    continue

            if enemy.kind == "phantom":
                enemy.special_timer -= dt
                if enemy.special_timer <= 0:
                    enemy.intangible = not getattr(enemy, "intangible", False)
                    enemy.special_timer = 4.0 if enemy.intangible else 6.0
                    enemy.color = "#F3E8FF" if enemy.intangible else "#D8B4FE"
                    if enemy.intangible:
                        self.emit_particles(enemy.pos, count=16, color="#D8B4FE", speed=80)
                        self.add_alert(enemy.pos, "INTANGIVEL", "#D8B4FE")
                    else:
                        self.emit_particles(enemy.pos, count=12, color="#9333EA", speed=100)
                        self.add_alert(enemy.pos, "VULNERAVEL!", "#9333EA")
                    if enemy.intangible:
                        self.emit_particles(enemy.pos, count=16, color="#D8B4FE", speed=80)
                        self.add_alert(enemy.pos, "INTANGIVEL", "#D8B4FE")
                    else:
                        self.emit_particles(enemy.pos, count=12, color="#9333EA", speed=100)
                        self.add_alert(enemy.pos, "VULNERAVEL!", "#9333EA")
                    if enemy.intangible:
                        self.emit_particles(enemy.pos, count=16, color="#D8B4FE", speed=80)
                        self.add_alert(enemy.pos, "INTANGIVEL", "#D8B4FE")
                    else:
                        self.emit_particles(enemy.pos, count=12, color="#9333EA", speed=100)
                        self.add_alert(enemy.pos, "VULNERAVEL!", "#9333EA")
            elif enemy.kind == "golem":
                enemy.knockback = Vector2(0, 0)
            elif enemy.kind == "necromancer":
                enemy.summon_cooldown -= dt
                if enemy.summon_cooldown <= 0 and len(self.enemies) < MAX_ENEMIES:
                    enemy.summon_cooldown = 12.0
                    for _ in range(2):
                        if len(self.enemies) < MAX_ENEMIES:
                            minion_data = ENEMY_TYPES["minion"]
                            minion = Enemy(
                                id=self.enemy_id,
                                pos=enemy.pos + self.random_offset(25),
                                kind="minion",
                                radius=minion_data["radius"],
                                speed=minion_data["speed"] * self.director_speed,
                                max_health=minion_data["health"] * self.director_health,
                                health=minion_data["health"] * self.director_health,
                                damage=minion_data["damage"] * self.director_damage,
                                xp_value=minion_data["xp"],
                                color=minion_data["color"],
                                special_value=minion_data["special"],
                                coin_chance=minion_data["coin_chance"],
                            )
                            self.enemy_id += 1
                            self._setup_physics_entity(minion)
                            self.enemies.append(minion)
                    self.emit_particles(enemy.pos, count=28, color="#C084FC", speed=120)
                    self.add_alert(enemy.pos, "INVOCANDO!", "#C084FC")

            target = self._nearest_alive_player(enemy.pos)
            to_player = target.pos - enemy.pos
            if to_player.length_squared() > 0:
                direction = to_player.normalize()
            else:
                direction = Vector2(1, 0)

            # Crowd and Miniboss Arena physics:
            center = getattr(self, "miniboss_arena_center", None)
            if center is not None and enemy.kind != "miniboss":
                radius = getattr(self, "miniboss_arena_radius", 520.0)
                dist = enemy.pos.distance_to(center)
                to_center = (center - enemy.pos)
                dist_to_center = to_center.length()
                if dist_to_center > 0:
                    dir_to_center = to_center.normalize()
                else:
                    dir_to_center = Vector2(1, 0)
                
                # Check how many enemies are inside
                inside_count = sum(1 for e in self.enemies if e.kind != "miniboss" and e.pos.distance_to(center) < radius)
                
                # If enemy is inside
                if dist < radius:
                    if inside_count > 5:
                        # Exceeded limits: push outside!
                        enemy.pos = center - dir_to_center * radius
                        dist = radius
                
                # If enemy is outside or was pushed outside
                if dist >= radius:
                    # Keep outside the arena!
                    if dist < radius + 10:
                        enemy.pos = center - dir_to_center * (radius + 12)
                        dist = radius + 12
                    
                    # Crowd / Gladiator Audience behavior:
                    # Orbit between radius+30 (550px) and radius+160 (680px)
                    min_orb = radius + 30
                    max_orb = radius + 160
                    if dist > max_orb:
                        # Move towards the arena
                        direction = dir_to_center
                    elif dist < min_orb:
                        # Move away from the arena
                        direction = -dir_to_center
                    else:
                        # Orbit! Perpendicular direction
                        orbit_dir = Vector2(-dir_to_center.y, dir_to_center.x)
                        # Alternate orbit direction based on enemy ID to look natural!
                        if enemy.id % 2 == 0:
                            orbit_dir = -orbit_dir
                        # Slight pull towards middle orbit
                        mid_orb = (min_orb + max_orb) / 2.0
                        pull = (mid_orb - dist) / 100.0
                        direction = (orbit_dir + dir_to_center * pull).normalize()

            slow = 0.28 if enemy.frozen_timer > 0 else 1.0
            chase_speed = enemy.speed * slow * self.world.hazard_speed_multiplier_at(enemy.pos.x, enemy.pos.y)
            if getattr(self, "light_level", 1.0) < 0.1:
                chase_speed *= 1.05
            if enemy.kind == "chromatic":
                velocity = self._chromatic_velocity(enemy, chase_speed)
            elif enemy.kind == "miniboss":
                velocity = self._miniboss_velocity(enemy, direction, chase_speed, dt)
            elif enemy.kind == "spitter":
                velocity = self._spitter_velocity(enemy, direction, chase_speed, dt)
            else:
                velocity = direction * chase_speed
            if enemy.knockback.length_squared() > 1:
                velocity += enemy.knockback
                enemy.knockback *= max(0, 1.0 - 7.0 * dt)

            if enemy.body:
                enemy.body.velocity = velocity.x, velocity.y
            else:
                enemy.pos = self._move_enemy(enemy, direction, chase_speed, velocity, dt)

            # Contact damage: check all alive players and NPCs
            sapper_detonated = False
            
            if getattr(self, 'escort_event_active', False) and getattr(self, 'escort_state', '') == 'escorting':
                for npc in getattr(self, 'escort_npcs', []):
                    if npc.hp <= 0: continue
                    distance_sq = enemy.pos.distance_squared_to(npc.pos)
                    contact_radius = enemy.radius + npc.radius
                    if distance_sq <= contact_radius * contact_radius:
                        npc.hp -= enemy.damage * dt
                        npc.hit_flash = 0.1
                        if enemy.kind == 'sapper' and distance_sq <= (enemy.radius + npc.radius + 38) ** 2:
                            self._detonate_sapper(enemy)
                            sapper_detonated = True
                            break
                            
            if sapper_detonated:
                self._cleanup_physics_entity(enemy)
                continue
                
            for player in self.alive_players():
                distance_sq = enemy.pos.distance_squared_to(player.pos)
                if enemy.kind == "sapper" and distance_sq <= (enemy.radius + player.radius + 38) ** 2:
                    self._detonate_sapper(enemy)
                    sapper_detonated = True
                    break
                contact_radius = enemy.radius + player.radius
                if distance_sq <= contact_radius * contact_radius:
                    if player.shield_timer > 0:
                        push = enemy.pos - player.pos
                        if push.length_squared() > 0:
                            enemy.knockback += push.normalize() * 460
                        self.damage_enemy(enemy, 22 * dt, source="shield")
                    elif player.invulnerable_timer <= 0:
                        self._damage_player_direct(player, enemy.damage * dt)
                        if enemy.kind == "phantom":
                            player.buffs["freeze"] = max(player.buffs.get("freeze", 0), 2.0)
            if sapper_detonated:
                self._cleanup_physics_entity(enemy)
                continue

            if enemy.health > 0:
                alive_list.append(enemy)
        self.enemies = alive_list

    def _chromatic_velocity(self, enemy, chase_speed):
        target = self._nearest_alive_player(enemy.pos)
        offset = enemy.pos - target.pos
        if offset.length_squared() <= 0.001:
            offset = Vector2(1, 0)
        distance = offset.length()
        away = offset.normalize()
        tangent = away.rotate(90 if math.sin(enemy.phase * 2.7 + enemy.id) >= 0 else -90)
        jitter = Vector2(math.cos(enemy.phase * 5.3 + enemy.id), math.sin(enemy.phase * 4.7))

        if distance < 330:
            desired = away * 1.55 + tangent * 0.9 + jitter * 0.35
        elif distance > 620:
            desired = away * -1.15 + tangent * 0.75 + jitter * 0.25
        else:
            desired = away * 0.45 + tangent * 1.15 + jitter * 0.35

        if desired.length_squared() <= 0.001:
            desired = away
        return desired.normalize() * chase_speed

    def _spitter_velocity(self, enemy, direction, chase_speed, dt):
        target = self._nearest_alive_player(enemy.pos)
        if enemy.action:
            enemy.action_timer -= dt
            if enemy.action_timer <= 0:
                if enemy.action == "spit_warn":
                    start = Vector2(enemy.pos)
                    end = Vector2(enemy.target_pos)
                    self._apply_laser_damage(start, end, 32, 26, ignore_enemy=enemy)
                    self.item_events.append({
                        "type": "laser",
                        "start": start,
                        "end": end,
                        "width": 32,
                        "age": 0.0,
                        "duration": 0.18,
                        "color": "#84CC16",
                    })
                enemy.action = ""
                enemy.special_timer = self.random.uniform(2.8, 4.2)
            return Vector2(0, 0)

        enemy.special_timer -= dt
        offset = enemy.pos - target.pos
        distance = offset.length() if offset.length_squared() > 0 else 1.0
        
        # Menor frequência de disparos
        if enemy.special_timer <= 0 and 280 < distance < 650:
            self._start_spitter_shot(enemy)
            return Vector2(0, 0)

        away = offset.normalize() if offset.length_squared() > 0 else Vector2(1, 0)
        tangent = away.rotate(90 if math.sin(enemy.phase * 2.0 + enemy.id) > 0 else -90)
        
        # Ajuste de distâncias de fuga e perseguição
        if distance < 380: # Aumentado de 340
            desired = away * 1.1 + tangent * 0.3 # Velocidade de fuga levemente reduzida
        elif distance > 550: # Reduzido de 590
            desired = -away + tangent * 0.25
        else:
            desired = tangent * 0.65
        return desired.normalize() * chase_speed

    def _start_spitter_shot(self, enemy):
        target = self._nearest_alive_player(enemy.pos)
        direction = target.pos - enemy.pos
        if direction.length_squared() <= 0.001:
            direction = Vector2(1, 0)
        direction = direction.normalize()
        start = Vector2(enemy.pos)
        end = start + direction * 620
        enemy.target_pos = end
        enemy.action = "spit_warn"
        enemy.action_timer = 0.62
        self.item_events.append({
            "type": "danger_line",
            "start": start,
            "end": end,
            "width": 32,
            "age": 0.0,
            "duration": 0.62,
            "color": "#84CC16",
        })

    def _detonate_sapper(self, enemy):
        center = Vector2(enemy.pos)
        self._apply_area_damage(center, 118, 42, "sapper", ignore_enemy=enemy)
        self.item_events.append({
            "type": "explosion",
            "pos": center,
            "radius": 118,
            "damage": 0,
            "age": 0.0,
            "duration": 0.28,
        })
        self.emit_particles(center, count=20, color=COLORS["coin"], speed=210, lifetime=0.34, size=5)
        self.screen_shake = max(self.screen_shake, 9.0)
        self.add_floater(center, "BOOM", COLORS["coin"])

    def _miniboss_velocity(self, enemy, direction, chase_speed, dt):
        enemy.summon_cooldown = max(0.0, enemy.summon_cooldown - dt)
        if enemy.action:
            enemy.action_timer -= dt
            if enemy.action_timer <= 0:
                if enemy.action == "leap_warn":
                    landing = Vector2(enemy.target_pos)
                    enemy.pos = self.world.move_circle(landing, enemy.radius, Vector2(0, 0), include_destructibles=False)
                    self._apply_area_damage(landing, MINIBOSS_LEAP_RADIUS, MINIBOSS_LEAP_DAMAGE, "miniboss", ignore_enemy=enemy)
                    self.item_events.append({
                        "type": "explosion",
                        "pos": landing,
                        "radius": MINIBOSS_LEAP_RADIUS,
                        "damage": 0,
                        "age": 0.0,
                        "duration": 0.28,
                    })
                    self.emit_particles(landing, count=28, color=COLORS["danger"], speed=230, lifetime=0.38, size=6)
                    self.screen_shake = max(self.screen_shake, 13.0)
                elif enemy.action == "laser_warn":
                    start = Vector2(enemy.pos)
                    end = Vector2(enemy.target_pos)
                    self._apply_laser_damage(start, end, MINIBOSS_LASER_WIDTH, MINIBOSS_LASER_DAMAGE, ignore_enemy=enemy)
                    self.item_events.append({
                        "type": "laser",
                        "start": start,
                        "end": end,
                        "width": MINIBOSS_LASER_WIDTH,
                        "age": 0.0,
                        "duration": 0.22,
                        "color": "#F97316",
                    })
                    self.screen_shake = max(self.screen_shake, 8.0)
                elif enemy.action == "shockwave_warn":
                    center = Vector2(enemy.pos)
                    self._apply_area_damage(center, 220, 36, "miniboss", ignore_enemy=enemy)
                    self.item_events.append({
                        "type": "explosion",
                        "pos": center,
                        "radius": 220,
                        "damage": 0,
                        "age": 0.0,
                        "duration": 0.34,
                    })
                    self.emit_particles(center, count=30, color="#C4B5FD", speed=220, lifetime=0.42, size=5)
                    self.screen_shake = max(self.screen_shake, 12.0)
                # summon action ends silently — minions were spawned at start

                enemy.action = ""
                enemy.special_timer = self.random.uniform(3.2, 5.2)
            return Vector2(0, 0)

        enemy.special_timer -= dt
        target_mb = self._nearest_alive_player(enemy.pos)
        if enemy.special_timer <= 0 and enemy.pos.distance_squared_to(target_mb.pos) < (900 * 900):
            roll = self.random.random()
            if not enemy.enraged and enemy.health <= enemy.max_health * 0.45:
                enemy.enraged = True
                enemy.speed *= 1.22
                enemy.damage *= 1.18
                self.message = "Mini-boss enfurecido!"
            if roll < 0.26 and enemy.summon_cooldown <= 0:
                self._start_miniboss_summon(enemy)
            elif roll < 0.52:
                self._start_miniboss_leap(enemy)
            elif roll < 0.78:
                self._start_miniboss_laser(enemy)
            else:
                self._start_miniboss_shockwave(enemy)
            return Vector2(0, 0)

        return direction * chase_speed

    def _start_miniboss_leap(self, enemy):
        leap_target = self._nearest_alive_player(enemy.pos)
        target = Vector2(leap_target.pos) + self.random_offset(70)
        enemy.target_pos = target
        enemy.action = "leap_warn"
        enemy.action_timer = MINIBOSS_LEAP_WARNING
        self.item_events.append({
            "type": "danger_circle",
            "pos": target,
            "radius": MINIBOSS_LEAP_RADIUS,
            "age": 0.0,
            "duration": MINIBOSS_LEAP_WARNING,
            "color": COLORS["danger"],
        })
        self.message = "Salto do mini-boss: saia do circulo vermelho."

    def _start_miniboss_laser(self, enemy):
        laser_target = self._nearest_alive_player(enemy.pos)
        direction = laser_target.pos - enemy.pos
        if direction.length_squared() <= 0.001:
            direction = Vector2(1, 0)
        direction = direction.normalize()
        start = Vector2(enemy.pos)
        end = start + direction * MINIBOSS_LASER_RANGE
        enemy.target_pos = end
        enemy.action = "laser_warn"
        enemy.action_timer = MINIBOSS_LASER_WARNING
        self.item_events.append({
            "type": "danger_line",
            "start": start,
            "end": end,
            "width": MINIBOSS_LASER_WIDTH,
            "age": 0.0,
            "duration": MINIBOSS_LASER_WARNING,
            "color": COLORS["danger"],
        })
        self.message = "Laser do mini-boss: fuja da faixa vermelha."

    def _start_miniboss_shockwave(self, enemy):
        enemy.action = "shockwave_warn"
        enemy.action_timer = 0.78
        self.item_events.append({
            "type": "danger_circle",
            "pos": Vector2(enemy.pos),
            "radius": 220,
            "age": 0.0,
            "duration": 0.78,
            "color": COLORS["danger"],
        })
        self.message = "Pulso do mini-boss: afaste-se."

    def _move_enemy(self, enemy, direction, chase_speed, velocity, dt):
        old_pos = Vector2(enemy.pos)
        intended = velocity * dt
        candidate = self.world.move_circle(old_pos, enemy.radius, intended, include_destructibles=False)
        if intended.length_squared() <= 1:
            return candidate

        moved_sq = candidate.distance_squared_to(old_pos)
        blocked = moved_sq < intended.length_squared() * 0.08
        if not blocked:
            return candidate

        best_pos = candidate
        best_score = -999999.0
        for angle in (90, -90, 45, -45, 135, -135):
            detour = direction.rotate(angle)
            test_pos = self.world.move_circle(
                old_pos,
                enemy.radius,
                detour * chase_speed * dt,
                include_destructibles=False,
            )
            progress = old_pos.distance_to(self.player.pos) - test_pos.distance_to(self.player.pos)
            movement = test_pos.distance_squared_to(old_pos)
            score = progress * 12 + movement
            if score > best_score:
                best_score = score
                best_pos = test_pos
        return best_pos

    def _start_miniboss_summon(self, enemy):
        enemy.action = "summon"
        enemy.action_timer = MINIBOSS_SUMMON_DURATION
        enemy.summon_cooldown = self.random.uniform(MINIBOSS_SUMMON_COOLDOWN_MIN, MINIBOSS_SUMMON_COOLDOWN_MAX)
        count = self.random.randint(MINIBOSS_SUMMON_COUNT_MIN, MINIBOSS_SUMMON_COUNT_MAX)
        spawned = 0
        for _ in range(count * 4):
            if spawned >= count:
                break
            angle = self.random.random() * math.tau
            dist = self.random.uniform(60, 130)
            pos = enemy.pos + Vector2(math.cos(angle), math.sin(angle)) * dist
            if not self.world.circle_hits_wall(pos, 11):
                self._spawn_minion(pos)
                spawned += 1
        self.item_events.append({
            "type": "summon_pulse",
            "pos": Vector2(enemy.pos),
            "radius": 140,
            "age": 0.0,
            "duration": MINIBOSS_SUMMON_DURATION,
        })
        self.message = "Mini-boss invocou reforcos!"

    def _spawn_minion(self, pos):
        data = ENEMY_TYPES["minion"]
        minion = Enemy(
            id=self.enemy_id,
            pos=Vector2(pos),
            kind="minion",
            radius=data["radius"],
            speed=data["speed"] * self.director_speed,
            max_health=data["health"] * self.director_health,
            health=data["health"] * self.director_health,
            damage=data["damage"] * self.director_damage,
            xp_value=data["xp"],
            color=data["color"],
            special_value=data["special"],
            coin_chance=data["coin_chance"],
        )
        self.enemy_id += 1
        self._setup_physics_entity(minion)
        self.enemies.append(minion)

    def _update_director(self, dt):
        self.director_tick += dt
        if self.director_tick >= 60.0:
            self.director_tick -= 60.0
            self.director_minute += 1
            self.director_health = 1.0 + min(1.0, self.director_minute * 0.05)
            self.director_damage = 1.0 + min(0.40, self.director_minute * 0.02)
            self.director_speed = 1.0 + min(0.30, self.director_minute * 0.02)
            bonus_enemies = min(45, self.director_minute * 5)
            self.message = (
                f"Minuto {self.director_minute}: inimigos mais fortes!"
            )
            # Dynamically raise the enemy cap
            global MAX_ENEMIES
            MAX_ENEMIES = 95 + bonus_enemies

