import math
import random

from pygame.math import Vector2

if __package__:
    from ..config.runtime import optional_import
    from ..data.constants import *
    from ..data.stamps import stamp_total_bonus
    from .entities import Drop, Enemy, Player, Projectile, Slash, EscortNPC
    from ..data.items import Inventory, item_display_name, RELIC_DEFINITIONS
    from .world import World, circle_rect_overlap
else:
    from Sobrevivencia.config.runtime import optional_import
    from Sobrevivencia.data.constants import *
    from Sobrevivencia.data.stamps import stamp_total_bonus
    from Sobrevivencia.core.entities import Drop, Enemy, Player, Projectile, Slash, EscortNPC
    from Sobrevivencia.data.items import Inventory, item_display_name, RELIC_DEFINITIONS
    from Sobrevivencia.core.world import World, circle_rect_overlap

pymunk = optional_import("pymunk")





from .managers.combat_manager import CombatManager
from .managers.enemy_manager import EnemyManager
from .managers.item_manager import ItemManager
from .managers.quest_manager import QuestManager
from .managers.buff_applicator import ensure_item_bonus_fields, recalc_item_buffs

class GameLogic(CombatManager, EnemyManager, ItemManager, QuestManager):
    def __init__(self, char_class="vanguard", char_class_2="vanguard", multiplayer=False):
        self.char_class = char_class
        self.char_class_2 = char_class_2
        self.multiplayer = multiplayer
        self.world = World()
        self.player = Player(char_class=char_class, player_index=0)
        self.inventory = Inventory()
        if multiplayer:
            self.player2 = Player(char_class=char_class_2, player_index=1)
            self.player2.pos = self.player.pos + Vector2(72, 0)
            self.inventory2 = Inventory()
            self.players = [self.player, self.player2]
            self.inventories = [self.inventory, self.inventory2]
            self.shared_coins = 0
            # XP Compartilhado
            self.shared_level = 25
            self.shared_xp = 0
            self.shared_xp_to_next = int(40 + 25 * 25)
            self.draft_active = False
            self.draft_turn_player = 0  # 0 ou 1
            self.draft_first_picker = 0 # Alterna a cada nível
        else:
            self.player2 = None
            self.inventory2 = None
            self.players = [self.player]
            self.inventories = [self.inventory]
            self.shared_coins = 0
            self.shared_level = 25 # Para compatibilidade

        # Debug start values for easy testing (Level 25, 60 points, Level 10 Relic)
        for p in self.players:
            p.level = 25
            p.xp_to_next = int(40 + 25 * 25)
        
        for inv in self.inventories:
            inv.points = 60
            status, item = inv.add_relic("blade_relay+chrono_boots+guardian_plate+magnet_orb")
            if item:
                item.level = 10
            inv.check_black_market_unlock()
            
        for i, p in enumerate(self.players):
            ensure_item_bonus_fields(p)
            recalc_item_buffs(p, self.inventories[i])
        self.camera = Vector2(
            self.player.pos.x - SCREEN_WIDTH * 0.5,
            self.player.pos.y - SCREEN_HEIGHT * 0.5,
        )
        self.camera_focus_index = 0
        self.enemies = []
        self.projectiles = []
        self.slashes = []
        self.drops = []
        self.floaters = []
        self.stat_shop_offers = []
        self.upgrade_choices = []
        self.upgrade_is_major = False
        self.level_up_pending = False
        self.level_up_player_index = 0
        self.menu_player_index = 0
        self.game_over = False
        self.time_alive = 0.0
        self.spawn_timer = 0.2
        self.enemy_id = 1
        self.screen_shake = 0.0
        self.time_warp_timer = 0.0
        self.special_box_timer = 12.0
        self.special_blast_timer = 0.0
        self.magnet_timer = 0.0
        self.drones = []
        self.escort_event_active = False
        self.escort_state = None
        self.escort_npcs = []
        self.escort_spawn_pos = Vector2(0, 0)
        self.escort_extract_pos = Vector2(0, 0)
        self.next_escort_timer = 180.0  # 3 minutos para o PRIMEIRO evento
        self.prev_escort_state = ""
        self._first_escort_done = False
        self.escort_post_event_timer = 0.0
        self.heat_level = 0.0
        self.player_constructs = []
        self.player_debuffs = {}
        self.day_night_timer = 0.0
        self.light_level = 1.0
        self.torch_cooldowns = {0: 0.0, 1: 0.0}
        self.altars = []
        self.active_altar = None
        self.altar_spawn_timer = 20.0
        self.time_scale = 1.0
        self.menu_just_opened_by_altar = None
        self.black_market_cooldown = 0.0
        self.stat_shop_cooldown = 0.0
        self.stat_shop_rerolls = 0
        self.pity_counter = 0
        self.current_dimension = "main"
        self.item_events = []
        self.particle_events = []
        self.stamp_fusion_target = None
        self.stamp_fusion_materials = []
        self.stamp_fusion_msg = ""
        self.message = "Sobreviva o maximo que puder."
        self.random = random.Random()
        self.chromatic_spawn_timer = self.random.uniform(CHROMATIC_SPAWN_MIN, CHROMATIC_SPAWN_MAX)
        self.miniboss_spawn_timer = self.random.uniform(MINIBOSS_SPAWN_MIN, MINIBOSS_SPAWN_MAX)
        self.world.ensure_area(self.player.pos, 2)
        # Quest system
        self.quest = None
        self.quest_progress = 0.0
        self.next_quest_timer = self.random.uniform(60.0, 90.0)
        self._player_in_fire = False
        # Game Director
        self.director_minute = 0
        self.director_tick = 0.0
        self.director_health = 1.0
        self.director_damage = 1.0
        self.director_speed = 1.0
        # Relic aura
        self.relic_aura_angle = 0.0
        self.camera_zoom = 1.0

        # Physics Space. Pymunk is optional; the World collision fallback keeps the game playable.
        self.space = pymunk.Space() if pymunk is not None else None
        if self.space is not None:
            self.space.gravity = (0, 0)
        self.physics_chunks = set()

        # Collision Types
        self.COLLISION_TYPE_PLAYER = 1
        self.COLLISION_TYPE_ENEMY = 2
        self.COLLISION_TYPE_WALL = 3

        # Setup Players Physics
        for p in self.players:
            self._setup_physics_entity(p, is_player=True)
            # Garante que os campos item_*_bonus existem mesmo antes do primeiro recalc
            ensure_item_bonus_fields(p)

    def restart(self):
        self.__init__(self.char_class, self.char_class_2, self.multiplayer)

    def _setup_physics_entity(self, entity, is_player=False):
        if self.space is None or pymunk is None:
            entity.body = None
            entity.shape = None
            return
        mass = 1
        moment = pymunk.moment_for_circle(mass, 0, entity.radius)
        body = pymunk.Body(mass, moment)
        body.position = entity.pos.x, entity.pos.y
        shape = pymunk.Circle(body, entity.radius)
        shape.elasticity = 0.5
        shape.friction = 0.5

        if is_player:
            shape.collision_type = self.COLLISION_TYPE_PLAYER
        else:
            shape.collision_type = self.COLLISION_TYPE_ENEMY

        self.space.add(body, shape)
        entity.body = body
        entity.shape = shape

    def _cleanup_physics_entity(self, entity):
        if entity.body and entity.shape:
            try:
                if self.space is not None:
                    self.space.remove(entity.body, entity.shape)
            except:
                pass
            entity.body = None
            entity.shape = None

    def _add_static_obstacle(self, rect):
        if self.space is None or pymunk is None:
            return
        body = pymunk.Body(body_type=pymunk.Body.STATIC)
        body.position = rect.center.x, rect.center.y
        shape = pymunk.Poly.create_box(body, (rect.w, rect.h))
        shape.friction = 0.5
        shape.elasticity = 0.2
        shape.collision_type = self.COLLISION_TYPE_WALL
        self.space.add(body, shape)

    def _sync_world_to_physics(self):
        if self.space is None:
            return
        focus = self.camera_focus
        cx, cy = self.world.chunk_coords(focus.x, focus.y)
        for oy in range(-2, 3):
            for ox in range(-2, 3):
                key = (cx + ox, cy + oy)
                if key not in self.physics_chunks:
                    chunk = self.world.ensure_chunk(key[0], key[1])
                    for rect in chunk["obstacles"]:
                        # Pymunk box position is center
                        self._add_static_obstacle(rect)
                    self.physics_chunks.add(key)

    def _sync_physics_to_entities(self):
        if self.space is None:
            return
        for p in self.players:
            if p.body and not p.is_down:
                p.pos = Vector2(p.body.position.x, p.body.position.y)
        for e in self.enemies:
            if e.body:
                e.pos = Vector2(e.body.position.x, e.body.position.y)

    def emit_particles(self, pos, count=10, color="#FFFFFF", speed=50, lifetime=0.5, size=4):
        self.particle_events.append({
            "pos": Vector2(pos),
            "count": count,
            "color": color,
            "speed": speed,
            "lifetime": lifetime,
            "size": size
        })

    def get_player(self, index=0):
        if index == 1 and self.player2 is not None:
            return self.player2
        return self.player

    def get_inventory(self, index=0):
        if index == 1 and self.inventory2 is not None:
            return self.inventory2
        return self.inventory

    @property
    def camera_focus(self):
        if self.multiplayer and self.player2:
            alive = self.alive_players()
            if len(alive) == 2:
                # Ponto médio
                return (alive[0].pos + alive[1].pos) * 0.5
            elif len(alive) == 1:
                return alive[0].pos
            return self.players[0].pos
        
        p = self.get_player(self.camera_focus_index)
        if p.is_down and self.multiplayer:
            other = self.get_player(1 - self.camera_focus_index)
            if not other.is_down:
                return other.pos
        return p.pos

    def alive_players(self):
        return [p for p in self.players if not p.is_down]

    def toggle_mode(self, player_index=0):
        player = self.get_player(player_index)
        if player.is_down:
            return
        
        if player.mode == "weapon_1": # Mudando para weapon_2 (espada)
            player.mode = "weapon_2"
            player.forced_reload = False
            if player.ammo_magazine < self.magazine_capacity_for(player) and player.reload_timer <= 0:
                self._start_reload_for(player, forced=False, show_message=False)
        else:
            if not self._ranged_weapon_ready_for(player, show_message=True):
                return
            player.mode = "weapon_1"
            player.forced_reload = False
        
        w_name = CHARACTERS[player.char_class][player.mode]
        self.message = f"J{player_index + 1}: modo {w_name}"












    def item_level(self, key):
        return self.inventory.active_effect_level(key)

    def hybrid_level(self):
        return self.inventory.active_hybrid_level()

    def passive_level(self, key):
        return self.player.passives.get(key, 0)

    def magazine_capacity(self):
        level_capacity = BASE_MAGAZINE_CAPACITY + max(0, self.player.level - 1) * MAGAZINE_CAPACITY_PER_LEVEL
        return level_capacity + self.player.magazine_bonus

    def current_reload_duration(self):
        reload_bonus = (
            self.passive_level("combat_drill") * 0.015
            + self.passive_level("predator_focus") * 0.015
            + self.player.reload_speed_bonus
        )
        return max(0.75, RELOAD_DURATION * (1.0 - min(0.35, reload_bonus)))

    @property
    def is_night(self):
        return self.light_level < 0.1

    @property
    def phase_info(self):
        t = self.day_night_timer
        if t < 60.0:
            return "dia", 60.0 - t
        elif t < 75.0:
            return "entardecer", 75.0 - t
        elif t < 110.0:
            return "noite", 110.0 - t
        else:
            return "amanhecer", 120.0 - t

    @property
    def light_color(self):
        r = int(255 * self.light_level + 12 * (1.0 - self.light_level))
        g = int(255 * self.light_level + 16 * (1.0 - self.light_level))
        b = int(255 * self.light_level + 32 * (1.0 - self.light_level))
        return (r, g, b)

    def try_place_light(self, player_index):
        if player_index >= len(self.players):
            return
        player = self.players[player_index]
        
        # Check cooldown
        if self.torch_cooldowns.get(player_index, 0.0) > 0.0:
            self.message = "Tocha em recarga!"
            return
            
        # Count existing torches of this owner
        torches = [c for c in self.player_constructs if c.kind == "torch" and c.owner == player_index]
        if len(torches) >= 3:
            oldest = torches[0]
            if oldest in self.player_constructs:
                self.player_constructs.remove(oldest)
                
        spawn_pos = Vector2(player.pos)
        
        try:
            from .entities import PlayerConstruct
        except ImportError:
            from Sobrevivencia.core.entities import PlayerConstruct

        torch = PlayerConstruct(
            pos=spawn_pos,
            kind="torch",
            hp=100.0,
            max_hp=100.0,
            radius=12.0,
            duration=60.0,
            owner=player_index,
            level=1
        )
        
        self.player_constructs.append(torch)
        self.torch_cooldowns[player_index] = 15.0
        self.message = "Tocha implantada!"
        self.emit_particles(spawn_pos, count=15, color="#F97316", speed=80)























    def update(self, dt, move_vector, aim_world, move_vector_2=None, aim_world_2=None):
        if self.game_over:
            return

        dt = min(dt, 0.05)
        
        # Update player debuffs
        debuffs = getattr(self, 'player_debuffs', {})
        for pi in list(debuffs.keys()):
            d = debuffs[pi]
            if d.get("movement_slow_timer", 0.0) > 0.0:
                d["movement_slow_timer"] = max(0.0, d["movement_slow_timer"] - dt)
                
        # Update shop cooldowns
        if getattr(self, 'black_market_cooldown', 0.0) > 0.0:
            self.black_market_cooldown = max(0.0, self.black_market_cooldown - dt)
        if getattr(self, 'stat_shop_cooldown', 0.0) > 0.0:
            self.stat_shop_cooldown = max(0.0, self.stat_shop_cooldown - dt)

        self.time_alive += dt

        # Atualiza o ciclo de Dia/Noite
        cycle_duration = 120.0
        self.day_night_timer = (self.day_night_timer + dt) % cycle_duration
        t = self.day_night_timer
        if t < 60.0:
            self.light_level = 1.0
        elif t < 75.0:
            self.light_level = 1.0 - (t - 60.0) / 15.0
        elif t < 110.0:
            self.light_level = 0.0
        else:
            self.light_level = (t - 110.0) / 10.0

        # Decrementa recargas de tocha
        for pi in list(self.torch_cooldowns.keys()):
            if self.torch_cooldowns[pi] > 0.0:
                self.torch_cooldowns[pi] = max(0.0, self.torch_cooldowns[pi] - dt)
        
        # Scale dt based on bullet time (time_scale)
        if getattr(self, 'time_scale', 1.0) != 1.0:
            dt *= self.time_scale
            
        if getattr(self, 'time_warp_timer', 0) > 0:
            self.time_warp_timer -= dt
            dt *= 0.15
        
        # Lógica da Dimensão de Bolso (Pocket Dimension)
        if getattr(self, "current_dimension", "main") == "pocket":
            self.pocket_dimension_timer = getattr(self, "pocket_dimension_timer", 30.0) - dt
            for p in self.alive_players():
                p.health = max(0.0, p.health - 1.5 * dt)
                if self.random.random() < dt * 0.4:
                    self.add_floater(p.pos, "-1.5 HP/s VOZ", "#C084FC")
            
            if self.pocket_dimension_timer <= 0.0:
                self.current_dimension = "main"
                self.message = "Sobreviveu ao Vazio! Caixa Lendaria obtida!"
                for p in self.alive_players():
                    orig = getattr(p, "original_pos", p.pos)
                    p.pos = Vector2(orig)
                    if p.body:
                        p.body.position = p.pos.x, p.pos.y
                    self.spawn_drop("item_box", p.pos, 1)

        self._player_in_fire = False
        self.world.ensure_area(self.player.pos, 2)
        self._update_director(dt)

        # --- Per-player updates ---
        inputs = [(self.player, move_vector, aim_world)]
        if self.multiplayer and self.player2 is not None:
            mv2 = move_vector_2 if move_vector_2 is not None else Vector2(0, 0)
            aw2 = aim_world_2 if aim_world_2 is not None else self.player2.pos + Vector2(1, 0)
            inputs.append((self.player2, mv2, aw2))

        for player, mv, aw in inputs:
            if player.is_down:
                continue
            self._update_player_timers_for(dt, player)
            self._move_player_for(dt, mv, aw, player)
            self._auto_attack_for(dt, aw, player)

        self._spawn_enemies(dt)
        self._update_world_timers(dt)
        self._update_projectiles(dt)
        self._update_slashes(dt)
        self._update_enemies(dt)
        self._update_constructs(dt)
        self._update_hazards(dt)
        self._update_item_system(dt)
        self._update_relic_aura(dt)
        self._update_drops(dt)
        self._update_floaters(dt)
        self._update_quests(dt)
        self._update_altars(dt)
        
        # Heat (Threat) Gauge Decay
        self.heat_level = max(0.0, getattr(self, "heat_level", 0.0) - 1.8 * dt)
        
        # Escort NPCs Self-Defense
        if getattr(self, "escort_event_active", False) and getattr(self, "escort_state", "") == "escorting":
            for npc in getattr(self, "escort_npcs", []):
                if getattr(npc, "hp", 0) <= 0:
                    continue
                npc.shoot_timer = getattr(npc, "shoot_timer", 0.0) - dt
                if npc.shoot_timer <= 0.0:
                    closest_enemy = None
                    closest_dist = 450.0
                    for enemy in self.enemies:
                        if enemy.health <= 0:
                            continue
                        dist = npc.pos.distance_to(enemy.pos)
                        if dist < closest_dist:
                            closest_dist = dist
                            closest_enemy = enemy
                    
                    if closest_enemy is not None:
                        dir_vector = (closest_enemy.pos - npc.pos).normalize()
                        self.projectiles.append(
                            Projectile(
                                pos=Vector2(npc.pos) + dir_vector * (npc.radius + 8),
                                vel=dir_vector * 620.0,
                                damage=18.0,
                                freeze=False,
                                poison=False,
                                poison_dps=0.0,
                                bounces_left=0,
                                pierce=0,
                                owner=0,
                            )
                        )
                        npc.shoot_timer = 0.6

        # Check Escort Success transition to grant Drone reward
        curr_escort_state = getattr(self, "escort_state", "")
        prev_escort_state = getattr(self, "prev_escort_state", "")
        if prev_escort_state == "escorting" and curr_escort_state != "escorting":
            survived = any(getattr(npc, "hp", 0) > 0 for npc in getattr(self, "escort_npcs", []))
            if survived:
                self.drones.append({
                    "angle": 0.0,
                    "shoot_timer": 0.0,
                })
                self.message = "MISSAO CUMPRIDA: Drone Mascote Concedido!"
        self.prev_escort_state = curr_escort_state

        # Update orbital Drones Mascot
        for drone in getattr(self, "drones", []):
            drone["angle"] += 3.0 * dt
            orbit_radius = 55.0
            drone_x = self.player.pos.x + math.cos(drone["angle"]) * orbit_radius
            drone_y = self.player.pos.y + math.sin(drone["angle"]) * orbit_radius
            drone_pos = Vector2(drone_x, drone_y)
            drone["pos"] = drone_pos

            drone["shoot_timer"] -= dt
            if drone["shoot_timer"] <= 0.0:
                closest_enemy = None
                closest_dist = 400.0
                for enemy in self.enemies:
                    if enemy.health <= 0:
                        continue
                    dist = drone_pos.distance_to(enemy.pos)
                    if dist < closest_dist:
                        closest_dist = dist
                        closest_enemy = enemy
                
                if closest_enemy is not None:
                    dir_vector = (closest_enemy.pos - drone_pos).normalize()
                    self.projectiles.append(
                        Projectile(
                            pos=Vector2(drone_pos) + dir_vector * 6,
                            vel=dir_vector * 580.0,
                            damage=14.0,
                            freeze=False,
                            poison=False,
                            poison_dps=0.0,
                            bounces_left=0,
                            pierce=0,
                            owner=0,
                        )
                    )
                    drone["shoot_timer"] = 0.7

        self._update_camera(dt)
        self.screen_shake = max(0, self.screen_shake - SCREEN_SHAKE_DECAY * 20 * dt)
        self.special_blast_timer = max(0, self.special_blast_timer - dt)

        # Physics step
        if self.space is not None:
            self._sync_world_to_physics()
            self.space.step(dt)
            self._sync_physics_to_entities()

        # --- Multiplayer: tethering and revive ---
        if self.multiplayer and self.player2 is not None:
            self._update_tethering()
            self._update_revive(dt)

        # --- Game over check ---
        for player in self.players:
            if player.health <= 0 and not player.is_down:
                if self.multiplayer:
                    player.is_down = True
                    player.health = 0
                    self.message = f"Jogador {player.player_index + 1} caiu!"
                else:
                    player.health = 0
                    self.game_over = True
        if self.multiplayer and all(p.is_down for p in self.players):
            self.game_over = True

    def _update_player_timers(self, dt):
        self._update_player_timers_for(dt, self.player)

    def _update_player_timers_for(self, dt, player):
        player.shoot_timer = max(0, player.shoot_timer - dt)
        player.sword_timer = max(0, player.sword_timer - dt)
        player.dash_cooldown = max(0, player.dash_cooldown - dt)
        player.dash_timer = max(0, player.dash_timer - dt)
        player.invulnerable_timer = max(0, player.invulnerable_timer - dt)
        player.shield_timer = max(0, player.shield_timer - dt)
        player.full_ammo_msg_timer = max(0, player.full_ammo_msg_timer - dt)
        if player.mode == "weapon_2" and player.ammo_magazine < self.magazine_capacity_for(player) and player.ammo_reserve > 0:
            player.reload_timer = max(0, player.reload_timer - dt)
            player.reload_step_timer -= dt
            
            if player.reload_step_timer <= 0:
                player.ammo_reserve -= 1
                player.ammo_magazine += 1
                
                capacity = self.magazine_capacity_for(player)
                if player.ammo_magazine < capacity and player.ammo_reserve > 0:
                    time_per_bullet = player.reload_duration / capacity
                    player.reload_step_timer += time_per_bullet
                else:
                    player.reload_timer = 0
                    player.reload_step_timer = 0
                    if player.forced_reload:
                        player.mode = "weapon_1"
                        player.forced_reload = False
                        
                        w_name = CHARACTERS[player.char_class][player.mode]
                        self.message = f"J{player.player_index + 1}: modo {w_name}"
        else:
            if player.reload_timer > 0:
                player.reload_timer = 0
                player.reload_step_timer = 0

        expired = []
        for name in player.buffs:
            player.buffs[name] = max(0, player.buffs[name] - dt)
            if player.buffs[name] <= 0:
                expired.append(name)
        for name in expired:
            del player.buffs[name]

    def _move_player(self, dt, move_vector, aim_world):
        self._move_player_for(dt, move_vector, aim_world, self.player)

    def _move_player_for(self, dt, move_vector, aim_world, player):
        if move_vector.length_squared() > 0:
            move_vector = move_vector.normalize()
            player.last_move_dir = Vector2(move_vector)

        if player.dash_timer > 0:
            velocity = player.dash_dir * DASH_SPEED
        else:
            terrain_speed = self.world.speed_multiplier_at(player.pos.x, player.pos.y)
            speed = player.base_speed * self.effective_speed_multiplier_for(player) * terrain_speed
            velocity = move_vector * speed

        player.pos = self.world.move_circle(player.pos, player.radius, velocity * dt)

        # Restrição da Arena do Miniboss
        center = getattr(self, "miniboss_arena_center", None)
        if center is not None:
            is_trapped = (getattr(self, "miniboss_trapped_player", None) == player) if getattr(self, "miniboss_trapped_player", None) is not None else True
            radius = getattr(self, "miniboss_arena_radius", 520.0)
            dist = player.pos.distance_to(center)
            if is_trapped:
                if dist > radius:
                    to_center = (center - player.pos).normalize()
                    player.pos = center + (player.pos - center).normalize() * radius
                    damage_taken = 6.0 * dt
                    # Apply knockback if player has a knockback property, or just apply it
                    # We can use player.knockback += to_center * 150.0
                    if hasattr(player, "knockback"):
                        player.knockback += to_center * 150.0
                    self._damage_player_direct(player, damage_taken)
                    self.message = "Fugindo da Arena do Miniboss! Sofrendo dano!"
            else:
                if dist < radius:
                    to_outside = (player.pos - center).normalize()
                    player.pos = center + to_outside * radius
                    damage_taken = 6.0 * dt
                    if hasattr(player, "knockback"):
                        player.knockback += to_outside * 150.0
                    self._damage_player_direct(player, damage_taken)
                    self.message = "Impossivel entrar na Arena do Miniboss!"

        if player.body:
            player.body.position = player.pos.x, player.pos.y
            player.body.velocity = 0, 0
        if player.shield_timer > 0:
            self._repel_enemies(dt, player)



    # ------------------------------------------------------------------ #
    # PER-PLAYER STAT HELPERS                                              #
    # ------------------------------------------------------------------ #

    def effective_speed_multiplier_for(self, player):
        inv = self.get_inventory(player.player_index)
        chrono = inv.active_effect_level("chrono_boots")
        return player.speed_multiplier() * (1.0 + chrono * 0.015)

    def effective_attack_rate_multiplier_for(self, player, inv):
        blade = inv.active_effect_level("blade_relay")
        hybrid = inv.active_hybrid_level()
        both_bonus = player.passives.get("combat_drill", 0) * 0.01 + player.passives.get("predator_focus", 0) * 0.012
        stamp_bonus = stamp_total_bonus(player, player.mode, "haste")
        return player.attack_rate_multiplier() * (1.0 + blade * 0.012 + hybrid * 0.01 + both_bonus + stamp_bonus)

    def projectile_damage_for(self, player, inv):
        storm = inv.active_effect_level("storm_core")
        stamp_bonus = stamp_total_bonus(player, "weapon_1", "impact")
        ranged_mult = (
            1.0
            + player.passives.get("combat_drill", 0) * 0.025
            + player.passives.get("predator_focus", 0) * 0.020
            + player.passives.get("piercing_rounds", 0) * 0.015
            + stamp_bonus
        )
        return player.projectile_damage() * (1.0 + storm * 0.01) * ranged_mult

    def sword_damage_for(self, player, inv):
        blade = inv.active_effect_level("blade_relay")
        stamp_bonus = stamp_total_bonus(player, "weapon_2", "impact")
        melee_mult = (
            1.0
            + player.passives.get("combat_drill", 0) * 0.025
            + player.passives.get("predator_focus", 0) * 0.020
            + player.passives.get("fan_blades", 0) * 0.018
            + stamp_bonus
        )
        return player.sword_damage() * (1.0 + blade * 0.012) * melee_mult

    def projectile_radius_for(self, player, base_radius=PROJECTILE_RADIUS):
        caliber_bonus = stamp_total_bonus(player, "weapon_1", "caliber")
        return base_radius * (1.0 + caliber_bonus)

    def sword_radius_for(self, player, inv):
        blade = inv.active_effect_level("blade_relay")
        hybrid = inv.active_hybrid_level()
        melee_bonus = player.passives.get("wide_cleave", 0) * 0.030 + player.passives.get("fan_blades", 0) * 0.028
        return player.sword_radius() * (1.0 + blade * 0.018 + hybrid * 0.018 + melee_bonus)

    def sword_arc_for(self, player):
        return SWORD_ARC + math.radians(player.passives.get("wide_cleave", 0) * 2.4)

    def dagger_arc_for(self, player):
        return SWORD_ARC * 0.6 + math.radians(player.passives.get("fan_blades", 0) * 2.8)

    def magazine_capacity_for(self, player):
        level_capacity = BASE_MAGAZINE_CAPACITY + max(0, player.level - 1) * MAGAZINE_CAPACITY_PER_LEVEL
        return level_capacity + player.magazine_bonus

    def max_ammo_reserve_for(self, player):
        return STARTING_AMMO_RESERVE + max(0, player.level - 1) * 20





    # ------------------------------------------------------------------ #
    # MULTIPLAYER: TETHERING & REVIVE                                      #
    # ------------------------------------------------------------------ #

    def _update_tethering(self):
        if not self.multiplayer or not self.player2:
            return
        
        alive = self.alive_players()
        if len(alive) < 2:
            return

        p1, p2 = alive[0], alive[1]
        dist = p1.pos.distance_to(p2.pos)
        if dist > TETHER_MAX_DISTANCE:
            # Teleporta ambos para ficarem no limite permitido em relação ao ponto médio
            mid = (p1.pos + p2.pos) * 0.5
            diff = (p1.pos - p2.pos).normalize()
            limit = TETHER_MAX_DISTANCE * 0.48
            p1.pos = mid + diff * limit
            p2.pos = mid - diff * limit
            
            # Garante que não atravessam paredes no teleporte
            p1.pos = self.world.move_circle(p1.pos, p1.radius, Vector2(0, 0))
            p2.pos = self.world.move_circle(p2.pos, p2.radius, Vector2(0, 0))
            
            self.add_floater(mid, "Fiquem Juntos!", COLORS["special"])

    def _update_revive(self, dt):
        alive = [p for p in self.players if not p.is_down]
        down = [p for p in self.players if p.is_down]
        for downed in down:
            reviving = False
            for helper in alive:
                if helper.pos.distance_to(downed.pos) <= REVIVE_RADIUS:
                    downed.revive_progress += dt
                    reviving = True
                    if downed.revive_progress >= REVIVE_TIME:
                        downed.is_down = False
                        downed.health = downed.max_health * REVIVE_HP_PERCENT
                        downed.invulnerable_timer = 2.0
                        downed.revive_progress = 0.0
                        self.message = f"Jogador {downed.player_index + 1} revivido!"
                        self.add_floater(downed.pos, "REVIVIDO!", COLORS["xp"])
                    break
            if not reviving:
                downed.revive_progress = max(0, downed.revive_progress - dt * 0.5)







    def _update_world_timers(self, dt):
        for chunk in self.world.chunks.values():
            for item in chunk["destructibles"]:
                item.hit_flash = max(0, item.hit_flash - dt)

        # Escort Event Timer & State Machine
        if not self.escort_event_active:
            self.next_escort_timer = getattr(self, "next_escort_timer", 180.0) - dt
            if self.next_escort_timer <= 0.0:
                self._trigger_escort_event()
        else:
            self._update_escort_event(dt)

    def _trigger_escort_event(self):
        self.escort_event_active = True
        self.escort_state = "seeking_spawn"
        
        # Spawn position: random angle, 900px distance from player
        angle = self.random.uniform(0, 2 * math.pi)
        spawn_dist = 900.0
        self.escort_spawn_pos = self.player.pos + Vector2(math.cos(angle), math.sin(angle)) * spawn_dist
        
        # Extraction position: random angle, 1600px distance from spawn position
        extract_angle = self.random.uniform(0, 2 * math.pi)
        extract_dist = 1600.0
        self.escort_extract_pos = self.escort_spawn_pos + Vector2(math.cos(extract_angle), math.sin(extract_angle)) * extract_dist
        
        self.escort_npcs = []
        self.message = "MISSAO DE ESCOLTA: Encontre os aliados!"

    def _update_escort_event(self, dt):
        if self.escort_state == "seeking_spawn":
            # Check if any alive player reaches the spawn zone
            player_reached = False
            for player in self.alive_players():
                if player.pos.distance_to(self.escort_spawn_pos) <= 150.0:
                    player_reached = True
                    break
            if player_reached:
                self.escort_state = "escorting"
                self.escort_npcs = [
                    EscortNPC(
                        pos=Vector2(self.escort_spawn_pos) + Vector2(-15, -15),
                        hp=120.0,
                        max_hp=120.0,
                        speed=85.0,
                        kind="soldier",
                    ),
                    EscortNPC(
                        pos=Vector2(self.escort_spawn_pos) + Vector2(15, 15),
                        hp=150.0,
                        max_hp=150.0,
                        speed=80.0,
                        kind="executive",
                    ),
                ]
                self.message = "MISSAO DE ESCOLTA: Proteja os aliados ate o ponto de extracao!"
        
        elif self.escort_state == "escorting":
            # Update NPCs movement and hit flash decay
            npcs_alive = 0
            reached_extract = 0
            for npc in self.escort_npcs:
                if npc.hp <= 0:
                    continue
                npcs_alive += 1
                npc.hit_flash = max(0, npc.hit_flash - dt)
                
                # Move towards extraction point
                to_extract = self.escort_extract_pos - npc.pos
                dist = to_extract.length()
                if dist > 50.0:
                    dir_vector = to_extract.normalize()
                    npc.pos += dir_vector * npc.speed * dt
                else:
                    reached_extract += 1
            
            # Check Failure
            if npcs_alive == 0:
                self.escort_state = "failed"
                self.message = "MISSAO FALHOU: Todos os aliados morreram."
                self.escort_post_event_timer = 5.0
            
            # Check Success: if all alive NPCs reached the extraction point
            elif reached_extract == npcs_alive:
                self.escort_state = "completed"
                self.escort_post_event_timer = 5.0
                
        elif self.escort_state in ("completed", "failed"):
            # Hold the completed/failed state for 5 seconds, then reset
            self.escort_post_event_timer = getattr(self, "escort_post_event_timer", 5.0) - dt
            if self.escort_post_event_timer <= 0.0:
                self.escort_event_active = False
                self.escort_state = None
                self.escort_npcs = []
                self.next_escort_timer = 240.0  # 4 minutos para o PROXIMO evento





















    def _update_hazards(self, dt):
        focus = self.camera_focus  # já é um Vector2
        for hazard in list(self.world.nearby_hazards(focus.x, focus.y, 980)):
            hazard.pulse += dt
            if hazard.kind == "mine":
                trigger_pos = None
                for player in self.alive_players():
                    if circle_rect_overlap(player.pos.x, player.pos.y, player.radius + MINE_TRIGGER_RADIUS, hazard.rect):
                        trigger_pos = Vector2(player.pos)
                        break
                if trigger_pos is None:
                    for enemy in list(self.enemies):
                        if circle_rect_overlap(enemy.pos.x, enemy.pos.y, enemy.radius + MINE_TRIGGER_RADIUS, hazard.rect):
                            trigger_pos = Vector2(enemy.pos)
                            break
                if trigger_pos is not None:
                    self._detonate_mine(hazard, trigger_pos)

            elif hazard.kind == "fire":
                for player in self.alive_players():
                    if circle_rect_overlap(player.pos.x, player.pos.y, player.radius, hazard.rect):
                        self._damage_player_direct(player, FIRE_DAMAGE_PER_SECOND * dt, source="fire")
                        self._player_in_fire = True
                for enemy in list(self.enemies):
                    if circle_rect_overlap(enemy.pos.x, enemy.pos.y, enemy.radius, hazard.rect):
                        self.damage_enemy(enemy, FIRE_DAMAGE_PER_SECOND * 0.72 * dt, source="fire")




    def _nearest_enemy(self, pos, radius):
        best = None
        best_distance = radius * radius
        for enemy in self.enemies:
            distance = enemy.pos.distance_squared_to(pos)
            if distance < best_distance:
                best = enemy
                best_distance = distance
        return best



    def _update_camera(self, dt):
        focus_pos = self.camera_focus
        target = Vector2(
            focus_pos.x - SCREEN_WIDTH * 0.5,
            focus_pos.y - SCREEN_HEIGHT * 0.5,
        )
        
        # Zoom dinâmico no multiplayer
        if self.multiplayer and self.player2:
            alive = self.alive_players()
            if len(alive) == 2:
                dist = alive[0].pos.distance_to(alive[1].pos)
                scale = 1.0
                if dist > 300:
                    t = min(1.0, (dist - 300) / (CAMERA_ZOOM_MAX_DISTANCE - 300))
                    scale = 1.0 - t * (1.0 - CAMERA_ZOOM_MIN_SCALE)
                self.camera_zoom += (scale - self.camera_zoom) * dt * 2.0
            else:
                self.camera_zoom += (1.0 - self.camera_zoom) * dt * 2.0
        else:
            self.camera_zoom = 1.0

        self.camera += (target - self.camera) * min(1.0, CAMERA_SMOOTHING * dt)






































    def random_offset(self, amount):
        angle = self.random.random() * math.tau
        distance = self.random.uniform(0, amount)
        return Vector2(math.cos(angle), math.sin(angle)) * distance


    # ------------------------------------------------------------------ #
    # MINIBOSS SUMMON                                                       #
    # ------------------------------------------------------------------ #



    # ------------------------------------------------------------------ #
    # GAME DIRECTOR                                                         #
    # ------------------------------------------------------------------ #


    # ------------------------------------------------------------------ #
    # QUEST SYSTEM                                                          #
    # ------------------------------------------------------------------ #





    # ------------------------------------------------------------------ #
    # RELIC AURA                                                            #
    # ------------------------------------------------------------------ #

    def _update_relic_aura(self, dt):
        self.relic_aura_angle = (self.relic_aura_angle + dt * 1.8) % math.tau
        aura_radius = 82
        for player in self.alive_players():
            inv = self.get_inventory(player.player_index)
            if not any(item.is_relic for item in inv.active_items()):
                continue
            for enemy in list(self.enemies):
                if enemy.pos.distance_to(player.pos) <= aura_radius + enemy.radius:
                    self.damage_enemy(enemy, 8.0 * dt, source="relic", killer_index=player.player_index)

    def _update_constructs(self, dt):
        alive = []
        for c in self.player_constructs:
            c.age += dt
            if c.hit_flash > 0:
                c.hit_flash -= dt
                
            if c.hp <= 0 or c.age >= c.duration:
                self.emit_particles(c.pos, count=15, color="#FBBF24" if c.kind == "turret" else ("#F97316" if c.kind == "torch" else "#38BDF8"), speed=100)
                continue
                
            if c.kind == "turret":
                owner_player = self.get_player(c.owner)
                reinforced = owner_player.passives.get("reinforced_turrets", 0)
                overclock = owner_player.passives.get("overclock", 0)
                c.attack_timer -= dt
                best_dist = 300**2
                best_enemy = None
                for enemy in self.enemies:
                    d = enemy.pos.distance_squared_to(c.pos)
                    if d < best_dist:
                        best_dist = d
                        best_enemy = enemy
                if best_enemy:
                    desired = math.atan2(best_enemy.pos.y - c.pos.y, best_enemy.pos.x - c.pos.x)
                    delta = (desired - c.angle + math.pi) % (math.tau) - math.pi
                    c.angle += delta * min(1.0, dt * 9.0)
                if c.attack_timer <= 0:
                    if best_enemy:
                        direction = (best_enemy.pos - c.pos).normalize()
                        inv = self.get_inventory(c.owner)
                        
                        damage = self.projectile_damage_for(owner_player, inv) * (1.2 + reinforced * 0.18)
                        self.projectiles.append(
                            Projectile(
                                pos=Vector2(c.pos) + direction * c.radius,
                                vel=direction * PROJECTILE_SPEED * 1.5,
                                damage=damage,
                                radius=self.projectile_radius_for(owner_player, PROJECTILE_RADIUS * 1.2),
                                owner=c.owner
                            )
                        )
                        c.attack_timer = max(0.18, 0.6 - reinforced * 0.045 - overclock * 0.025)
                        
            elif c.kind == "barrier":
                owner_player = self.get_player(c.owner)
                shock_level = owner_player.passives.get("shocking_barrier", 0)
                overclock = owner_player.passives.get("overclock", 0)
                c.attack_timer -= dt
                if c.attack_timer <= 0:
                    for enemy in self.enemies:
                        d_sq = enemy.pos.distance_squared_to(c.pos)
                        if d_sq <= (c.radius + enemy.radius + 15)**2:
                            self.damage_enemy(enemy, c.max_hp * 0.15 * (1 + shock_level * 0.16), source="special", killer_index=c.owner)
                            diff = enemy.pos - c.pos
                            if diff.length_squared() > 0:
                                enemy.knockback += diff.normalize() * (200 + shock_level * 45)
                            enemy.hit_flash = 0.2
                            self.emit_particles(enemy.pos, count=3, color="#0EA5E9", speed=100)
                    c.attack_timer = max(0.18, 0.3 - overclock * 0.012)
            elif c.kind == "torch":
                c.attack_timer -= dt
                if c.attack_timer <= 0:
                    self.emit_particles(c.pos + Vector2(0, -6), count=1, color="#F97316", speed=20, lifetime=0.4, size=3)
                    c.attack_timer = 0.15
            
            alive.append(c)
        self.player_constructs = alive

    def spawn_altar(self):
        angle = self.random.random() * math.tau
        distance = self.random.uniform(400.0, 600.0)
        spawn_pos = self.player.pos + Vector2(math.cos(angle), math.sin(angle)) * distance
        
        # Ensure position is inside world boundaries
        spawn_pos = self.world.move_circle(spawn_pos, 24.0, Vector2(0, 0))
        
        kinds = ["weapon_altar", "skill_altar", "stat_altar"]
        kind = self.random.choice(kinds)
        
        try:
            from .entities import Altar
        except ImportError:
            from Sobrevivencia.core.entities import Altar
            
        new_altar = Altar(pos=spawn_pos, kind=kind)
        self.altars.append(new_altar)
        
        names = {
            "weapon_altar": "Armas (Inventario)",
            "skill_altar": "Habilidades (Passivas)",
            "stat_altar": "Status"
        }
        self.message = f"Um Altar de {names[kind]} se manifestou na arena!"
        if hasattr(self, 'add_floater'):
            self.add_floater(spawn_pos, "ALTAR", COLORS["special"])

    def _update_altars(self, dt):
        alive = []
        for altar in self.altars:
            altar.age += dt
            if altar.hit_flash > 0:
                altar.hit_flash -= dt
            
            if altar.active:
                alive.append(altar)
                
                # Check collision with alive players
                if self.active_altar is None:
                    for player in self.alive_players():
                        if player.pos.distance_to(altar.pos) <= player.radius + altar.radius:
                            self.active_altar = altar
                            self.time_scale = 0.2  # Bullet Time / Slow motion
                            self.menu_player_index = player.player_index
                            self.menu_just_opened_by_altar = altar.kind
                            self.message = "Altar ativado! Selecione seus aprimoramentos."
                            self.emit_particles(altar.pos, count=25, color="#F59E0B", speed=150)
                            break
            else:
                self.emit_particles(altar.pos, count=30, color="#EF4444", speed=200)
                
        self.altars = alive
        
        if getattr(self, 'altar_spawn_timer', 0.0) > 0.0:
            self.altar_spawn_timer -= dt
            if self.altar_spawn_timer <= 0.0:
                self.spawn_altar()
                self.altar_spawn_timer = 90.0

    def finish_altar_interaction(self, destroy=True):
        altar = getattr(self, "active_altar", None)
        if altar is not None and destroy:
            altar.active = False
            self.emit_particles(altar.pos, count=36, color="#F59E0B", speed=220)
            self.screen_shake = max(self.screen_shake, 10.0)
        self.active_altar = None
        self.menu_just_opened_by_altar = None
        self.time_scale = 1.0

    def roll_upgrade_rng(self, player_index, attempted_levels=1):
        attempted_levels = max(1, int(attempted_levels))
        greed = min(0.30, max(0, attempted_levels - 1) * 0.04)

        super_chance = 0.10 + self.pity_counter * 0.15
        success_chance = max(0.18, 0.58 - greed)
        partial_chance = 0.22 + greed * 0.55
        fail_chance = 0.10 + greed * 0.45

        total = super_chance + success_chance + partial_chance + fail_chance
        super_chance /= total
        success_chance /= total
        partial_chance /= total

        r = self.random.random()
        if r < super_chance:
            self.pity_counter = 0
            return "super"
        if r < super_chance + success_chance:
            self.pity_counter = 0
            return "sucesso"
        if r < super_chance + success_chance + partial_chance:
            self.pity_counter += 1
            return "parcial"
        self.pity_counter += 1
        return "falha"
