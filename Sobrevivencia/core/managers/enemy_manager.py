from pygame.math import Vector2
import random
import math
if __package__:
    from ...data.constants import *
    from ..inimigos.elites.arauto.ai import harbinger_velocity
    from ..inimigos.elites.ceifador.ai import apply_reaper_presence, reaper_velocity, start_reaper_blink, start_reaper_dash, start_reaper_doom
    from ..inimigos.elites.miniboss.ai import miniboss_velocity, start_miniboss_charge, start_miniboss_laser, start_miniboss_leap, start_miniboss_shockwave, start_miniboss_summon
    from ..inimigos.scaling import active_spitter_cap, apply_enemy_tier, choose_enemy_tier, enemy_difficulty_rating, enemy_spawn_scales, highest_player_level, player_power_rating, player_power_rating_for
    from ..inimigos.spawning import spawn_enemies, spawn_one_enemy, spawn_special_enemy, update_reaper_spawn_pressure, update_special_spawns, weighted_enemy_kind
    from ..entities import Enemy, Hazard
else:
    from Sobrevivencia.data.constants import *
    from Sobrevivencia.core.inimigos.elites.arauto.ai import harbinger_velocity
    from Sobrevivencia.core.inimigos.elites.ceifador.ai import apply_reaper_presence, reaper_velocity, start_reaper_blink, start_reaper_dash, start_reaper_doom
    from Sobrevivencia.core.inimigos.elites.miniboss.ai import miniboss_velocity, start_miniboss_charge, start_miniboss_laser, start_miniboss_leap, start_miniboss_shockwave, start_miniboss_summon
    from Sobrevivencia.core.inimigos.scaling import active_spitter_cap, apply_enemy_tier, choose_enemy_tier, enemy_difficulty_rating, enemy_spawn_scales, highest_player_level, player_power_rating, player_power_rating_for
    from Sobrevivencia.core.inimigos.spawning import spawn_enemies, spawn_one_enemy, spawn_special_enemy, update_reaper_spawn_pressure, update_special_spawns, weighted_enemy_kind
    from Sobrevivencia.core.entities import Enemy, Hazard

class EnemyManager:
    def _spawn_enemies(self, dt):
        return spawn_enemies(self, dt)

    def _enemy_difficulty_rating(self):
        return enemy_difficulty_rating(self)

    def _highest_player_level(self):
        return highest_player_level(self)

    def _player_power_rating(self):
        return player_power_rating(self)

    def _player_power_rating_for(self, player):
        return player_power_rating_for(self, player)

    def _enemy_spawn_scales(self, kind, difficulty):
        return enemy_spawn_scales(kind, difficulty)

    def _choose_enemy_tier(self, kind, difficulty):
        return choose_enemy_tier(self, kind, difficulty)

    def _apply_enemy_tier(self, enemy, tier):
        return apply_enemy_tier(enemy, tier)

    def _active_spitter_cap(self):
        return active_spitter_cap(self)

    def _update_special_spawns(self, dt, difficulty):
        return update_special_spawns(self, dt, difficulty)

    def _update_reaper_spawn_pressure(self, dt):
        return update_reaper_spawn_pressure(self, dt)

    def _spawn_special_enemy(self, kind, difficulty):
        return spawn_special_enemy(self, kind, difficulty)

    def _spawn_one_enemy(self, difficulty):
        return spawn_one_enemy(self, difficulty)

    def _weighted_enemy_kind(self, pos):
        return weighted_enemy_kind(self, pos)

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
        time_scale = self.omni_time_freeze_multiplier() if hasattr(self, "omni_time_freeze_multiplier") else 1.0
        enemy_dt = dt * time_scale
        for enemy in list(self.enemies):
            enemy.phase += enemy_dt
            enemy.frozen_timer = max(0, enemy.frozen_timer - enemy_dt)
            enemy.hit_flash = max(0, enemy.hit_flash - enemy_dt)
            enemy.blood_mark_timer = max(0, getattr(enemy, "blood_mark_timer", 0) - enemy_dt)
            if enemy.blood_mark_timer <= 0:
                enemy.blood_mark_level = 0
                enemy.blood_harvest_value = 0
            if enemy.lifetime > 0:
                enemy.lifetime -= enemy_dt
                if enemy.lifetime <= 0 and enemy.kind == "chromatic":
                    self.add_floater(enemy.pos, "escapou", COLORS["muted"])
                    self._cleanup_physics_entity(enemy)
                    continue
            if enemy.poison_timer > 0:
                enemy.poison_timer = max(0, enemy.poison_timer - enemy_dt)
                self.damage_enemy(enemy, enemy.poison_dps * enemy_dt, source="poison")
                if enemy.health <= 0:
                    self._cleanup_physics_entity(enemy)
                    continue
            if enemy.bleed_timer > 0:
                enemy.bleed_timer = max(0, enemy.bleed_timer - enemy_dt)
                self.damage_enemy(enemy, enemy.bleed_dps * enemy_dt, source="bleed")
                if enemy.health <= 0:
                    self._cleanup_physics_entity(enemy)
                    continue

            if enemy.kind == "phantom":
                enemy.special_timer -= enemy_dt
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
            elif enemy.kind == "harbinger":
                enemy.immune_to_knockback = True
            elif enemy.kind == "reaper":
                enemy.immune_to_knockback = True
                self._apply_reaper_presence(enemy, enemy_dt)
            elif enemy.kind == "necromancer":
                enemy.summon_cooldown -= enemy_dt
                enemy.special_timer -= enemy_dt
                if enemy.special_timer <= 0:
                    healed = 0
                    for ally in self.enemies:
                        if ally is enemy or ally.health <= 0:
                            continue
                        if ally.pos.distance_squared_to(enemy.pos) <= 210 * 210 and ally.health < ally.max_health:
                            ally.health = min(ally.max_health, ally.health + 22)
                            ally.hit_flash = 0.08
                            healed += 1
                    if healed:
                        self.emit_particles(enemy.pos, count=24, color="#86EFAC", speed=110)
                        self.add_alert(enemy.pos, f"CURA x{healed}", "#86EFAC")
                    enemy.special_timer = 7.5
                if enemy.summon_cooldown <= 0 and len(self.enemies) < MAX_ENEMIES:
                    enemy.summon_cooldown = 12.0
                    for _ in range(2):
                        if len(self.enemies) < MAX_ENEMIES:
                            self._spawn_minion(enemy.pos + self.random_offset(25))
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
            if center is not None and enemy.kind not in ("miniboss", "reaper"):
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
                velocity = self._miniboss_velocity(enemy, direction, chase_speed, enemy_dt)
            elif enemy.kind == "spitter":
                velocity = self._spitter_velocity(enemy, direction, chase_speed, enemy_dt)
            elif enemy.kind == "harbinger":
                velocity = self._harbinger_velocity(enemy, direction, chase_speed, enemy_dt)
            elif enemy.kind == "reaper":
                velocity = self._reaper_velocity(enemy, direction, chase_speed, enemy_dt)
            elif enemy.kind == "god":
                velocity = self._god_velocity(enemy, direction, chase_speed, enemy_dt)
            elif enemy.kind in ("morcego_sombra", "lobo_infectado"):
                velocity = self._nightstalker_velocity(enemy, direction, chase_speed, enemy_dt)
            else:
                velocity = direction * chase_speed
            if enemy.knockback.length_squared() > 1:
                velocity += enemy.knockback
                if getattr(enemy, "immune_to_knockback", False):
                    enemy.knockback = Vector2(0, 0)
                else:
                    enemy.knockback *= max(0, 1.0 - 7.0 * enemy_dt)

            if enemy.body:
                enemy.body.velocity = velocity.x, velocity.y
            else:
                enemy.pos = self._move_enemy(enemy, direction, chase_speed, velocity, enemy_dt)

            # Contact damage: check all alive players and NPCs
            sapper_detonated = False
            
            if getattr(self, 'escort_event_active', False) and getattr(self, 'escort_state', '') == 'escorting':
                for npc in getattr(self, 'escort_npcs', []):
                    if npc.hp <= 0: continue
                    distance_sq = enemy.pos.distance_squared_to(npc.pos)
                    contact_radius = enemy.radius + npc.radius
                    if distance_sq <= contact_radius * contact_radius:
                        npc.hp -= enemy.damage * enemy_dt
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
                        self.damage_enemy(enemy, 22 * enemy_dt, source="shield")
                    elif player.invulnerable_timer <= 0:
                        self._damage_player_direct(player, enemy.damage * enemy_dt)
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
                    self._apply_laser_damage(start, end, 28, 18, ignore_enemy=enemy)
                    self.item_events.append({
                        "type": "laser",
                        "start": start,
                        "end": end,
                        "width": 28,
                        "age": 0.0,
                        "duration": 0.18,
                        "color": "#84CC16",
                    })
                enemy.action = ""
                enemy.special_timer = self.random.uniform(4.0, 5.8)
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

    def _harbinger_velocity(self, enemy, direction, chase_speed, dt):
        return harbinger_velocity(self, enemy, direction, chase_speed, dt)

    def _apply_reaper_presence(self, enemy, dt):
        return apply_reaper_presence(self, enemy, dt)

    def _reaper_velocity(self, enemy, direction, chase_speed, dt):
        return reaper_velocity(self, enemy, direction, chase_speed, dt)

    def _start_reaper_blink(self, enemy, target):
        return start_reaper_blink(self, enemy, target)

    def _start_reaper_dash(self, enemy, target):
        return start_reaper_dash(self, enemy, target)

    def _start_reaper_doom(self, enemy, target):
        return start_reaper_doom(self, enemy, target)

    def _god_velocity(self, enemy, direction, chase_speed, dt):
        target = self._nearest_alive_player(enemy.pos)
        distance = enemy.pos.distance_to(target.pos)
        
        # Invocacao de lacaios do Harbinger
        enemy.summon_cooldown -= dt
        if enemy.summon_cooldown <= 0:
            enemy.summon_cooldown = self.random.uniform(6.0, 9.0)
            for i in range(3):
                pos = enemy.pos + self.random_offset(150)
                if len(self.enemies) < MAX_ENEMIES:
                    kind = self.random.choice(["bulwark", "phantom", "necromancer"])
                    # Re-use _spawn_one_enemy with a forced position? No, use _spawn_minion equivalent or create enemy directly
                    from Sobrevivencia.core.entities import Enemy
                    data = ENEMY_TYPES[kind]
                    minion = Enemy(
                        id=self.enemy_id,
                        pos=pos,
                        kind=kind,
                        radius=data["radius"],
                        speed=data["speed"],
                        max_health=data["health"],
                        health=data["health"],
                        damage=data["damage"],
                        xp_value=data["xp"],
                        color=data["color"],
                        special_value=data["special"],
                        coin_chance=data["coin_chance"],
                    )
                    self.enemy_id += 1
                    self._setup_physics_entity(minion)
                    self.enemies.append(minion)
            self.add_alert(enemy.pos, "GUARDA DIVINA", "#FDE047")
            self.emit_particles(enemy.pos, count=30, color="#FDE047", speed=200)

        if enemy.action:
            enemy.action_timer -= dt
            if enemy.action == "reaper_dash":
                if enemy.action_timer <= 0:
                    start = Vector2(getattr(enemy, "dash_start", enemy.pos))
                    end = Vector2(enemy.pos)
                    self._apply_laser_damage(start, end, 100, enemy.damage * 1.5, ignore_enemy=enemy)
                    self.item_events.append({
                        "type": "laser",
                        "start": start,
                        "end": end,
                        "width": 100,
                        "age": 0.0,
                        "duration": 0.3,
                        "color": "#FDE047",
                    })
                    self.screen_shake = max(self.screen_shake, 18.0)
                    enemy.action = ""
                    enemy.special_timer = self.random.uniform(1.5, 2.5)
                    return Vector2(0, 0)
                return Vector2(getattr(enemy, "dash_dir", direction)) * chase_speed * 4.0
            if enemy.action_timer <= 0:
                if enemy.action == "reaper_blink":
                    landing = self.world.move_circle(Vector2(enemy.target_pos), enemy.radius, Vector2(0, 0), include_destructibles=False)
                    enemy.pos = landing
                    if enemy.body:
                        enemy.body.position = landing.x, landing.y
                    self._apply_area_damage(landing, 200, enemy.damage * 1.2, "god", ignore_enemy=enemy)
                    self.item_events.append({
                        "type": "explosion",
                        "pos": landing,
                        "radius": 200,
                        "damage": 0,
                        "age": 0.0,
                        "duration": 0.4,
                    })
                    self.emit_particles(landing, count=40, color="#FDE047", speed=250, lifetime=0.5, size=8)
                    self.screen_shake = max(self.screen_shake, 15.0)
                elif enemy.action == "reaper_doom":
                    center = Vector2(enemy.target_pos)
                    self._apply_area_damage(center, REAPER_DOOM_RADIUS + 50, enemy.damage * 1.5, "god", ignore_enemy=enemy)
                    self.item_events.append({
                        "type": "explosion",
                        "pos": center,
                        "radius": REAPER_DOOM_RADIUS + 50,
                        "damage": 0,
                        "age": 0.0,
                        "duration": 0.5,
                    })
                    self.emit_particles(center, count=50, color="#CA8A04", speed=250, lifetime=0.6, size=9)
                    self.screen_shake = max(self.screen_shake, 20.0)
                enemy.action = ""
                enemy.special_timer = self.random.uniform(1.8, 3.0)
            return Vector2(0, 0)

        enemy.special_timer -= dt
        if enemy.special_timer <= 0 and distance < 1000:
            roll = self.random.random()
            if distance > 300 and roll < 0.4:
                self._start_reaper_blink(enemy, target)
                self.message = "Deus transita pelo tecido do universo."
                return Vector2(0, 0)
            if roll < 0.8:
                self._start_reaper_dash(enemy, target)
                self.message = "Uma investida divina se prepara."
                return Vector2(0, 0)
            self._start_reaper_doom(enemy, target)
            self.message = "Julgamento divino eminente!"
            return Vector2(0, 0)

        side = direction.rotate(90 if math.sin(enemy.phase * 3.1 + enemy.id) > 0 else -90)
        if distance > 400:
            desired = direction * 1.6 + side * 0.2
        elif distance < 150:
            desired = direction * 0.8 + side * 0.6
        else:
            desired = direction * 1.2 + side * 0.4
        return desired.normalize() * chase_speed

    def _nightstalker_velocity(self, enemy, direction, chase_speed, dt):
        target = self._nearest_alive_player(enemy.pos)
        enemy.special_timer -= dt
        if enemy.kind == "morcego_sombra" and enemy.special_timer <= 0:
            side = direction.rotate(90 if enemy.id % 2 == 0 else -90)
            enemy.pos = self.world.move_circle(enemy.pos, enemy.radius, (direction * 95 + side * 150), include_destructibles=False)
            enemy.special_timer = self.random.uniform(2.2, 3.4)
            self.emit_particles(enemy.pos, count=10, color="#C084FC", speed=95)
        elif enemy.kind == "lobo_infectado" and enemy.special_timer <= 0:
            enemy.action = "charge"
            enemy.action_timer = 0.42
            enemy.target_pos = Vector2(target.pos)
            enemy.special_timer = self.random.uniform(3.0, 4.6)
        if enemy.action == "charge":
            enemy.action_timer -= dt
            if enemy.action_timer <= 0:
                enemy.action = ""
            return direction * chase_speed * 2.1
        side = direction.rotate(90 if math.sin(enemy.phase * 3.0 + enemy.id) > 0 else -90)
        return (direction * 0.78 + side * 0.42).normalize() * chase_speed

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


    def _miniboss_velocity(self, enemy, direction, chase_speed, dt):
        return miniboss_velocity(self, enemy, direction, chase_speed, dt)

    def _start_miniboss_leap(self, enemy):
        return start_miniboss_leap(self, enemy)

    def _start_miniboss_laser(self, enemy):
        return start_miniboss_laser(self, enemy)

    def _start_miniboss_shockwave(self, enemy):
        return start_miniboss_shockwave(self, enemy)

    def _start_miniboss_charge(self, enemy):
        return start_miniboss_charge(self, enemy)

    def _start_miniboss_summon(self, enemy):
        return start_miniboss_summon(self, enemy)

    def _spawn_minion(self, pos, kind="minion"):
        data = ENEMY_TYPES[kind]
        scales = self._enemy_spawn_scales(kind, self._enemy_difficulty_rating())
        minion = Enemy(
            id=self.enemy_id,
            pos=Vector2(pos),
            kind=kind,
            radius=data["radius"],
            speed=data["speed"] * scales["speed"] * self.director_speed,
            max_health=data["health"] * scales["health"] * self.director_health,
            health=data["health"] * scales["health"] * self.director_health,
            damage=data["damage"] * scales["damage"] * self.director_damage,
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
        self.director_eval_timer = getattr(self, "director_eval_timer", 0.0) + dt
        if self.director_eval_timer >= DIRECTOR_PRESSURE_INTERVAL:
            window = max(1.0, self.director_eval_timer)
            self.director_eval_timer = 0.0
            kills_rate = getattr(self, "director_recent_kills", 0) * 60.0 / window
            damage_rate = getattr(self, "director_recent_damage_taken", 0.0) * 60.0 / window
            kill_pressure = (kills_rate - DIRECTOR_TARGET_KILLS_PER_MIN) / DIRECTOR_TARGET_KILLS_PER_MIN
            safety_pressure = (DIRECTOR_TARGET_DAMAGE_PER_MIN - damage_rate) / DIRECTOR_TARGET_DAMAGE_PER_MIN
            target_pressure = max(0.0, min(DIRECTOR_MAX_PRESSURE, kill_pressure * 0.62 + safety_pressure * 0.38))
            self.director_pressure = self.director_pressure * 0.72 + target_pressure * 0.28
            self.director_recent_kills = 0
            self.director_recent_damage_taken = 0.0

        elapsed_minute = int(self.time_alive // 60.0)
        if elapsed_minute > self.director_minute:
            self.director_minute = elapsed_minute
            pressure = getattr(self, "director_pressure", 0.0)
            self.director_health = 1.0 + min(2.20, self.director_minute * 0.065 + pressure * 0.85)
            self.director_damage = 1.0 + min(0.85, self.director_minute * 0.024 + pressure * 0.35)
            self.director_speed = 1.0 + min(0.45, self.director_minute * 0.014 + pressure * 0.16)
            self.director_enemy_cap_bonus = min(90, int(self.director_minute * 6 + pressure * 28))
            self.message = f"Minuto {self.director_minute}: inimigos mais fortes!"
