import math
import random

from pygame.math import Vector2

if __package__:
    from ..config.runtime import optional_import
    from ..data.constants import *
    from ..data.stamps import stamp_total_bonus
    from .entities import Drop, Enemy, Player, Projectile, Slash, EscortNPC
    from ..data.items import Inventory, item_display_name, RELIC_DEFINITIONS
    from .omni_kernel import system as omni_kernel
    from .omni_kernel.progresso import calice
    from .hud_status import camera as camera_system
    from .altares import sistema as altar_system
    from .mundo import dimensoes
    from .mundo import escolta as escort_system
    from .personagem import atributos
    from .personagem import movimento
    from .meta_progress import character_upgrades, upgrade_effect_value
    from .world import World, circle_rect_overlap
else:
    from Sobrevivencia.config.runtime import optional_import
    from Sobrevivencia.data.constants import *
    from Sobrevivencia.data.stamps import stamp_total_bonus
    from Sobrevivencia.core.entities import Drop, Enemy, Player, Projectile, Slash, EscortNPC
    from Sobrevivencia.data.items import Inventory, item_display_name, RELIC_DEFINITIONS
    from Sobrevivencia.core.omni_kernel import system as omni_kernel
    from Sobrevivencia.core.omni_kernel.progresso import calice
    from Sobrevivencia.core.hud_status import camera as camera_system
    from Sobrevivencia.core.altares import sistema as altar_system
    from Sobrevivencia.core.mundo import dimensoes
    from Sobrevivencia.core.mundo import escolta as escort_system
    from Sobrevivencia.core.personagem import atributos
    from Sobrevivencia.core.personagem import movimento
    from Sobrevivencia.core.meta_progress import character_upgrades, upgrade_effect_value
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
        self.main_world = self.world
        self.pocket_world = None
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
            self.shared_level = 1
            self.shared_xp = 0
            self.shared_xp_to_next = int(40 + 25 * self.shared_level)
            self.draft_active = False
            self.draft_turn_player = 0  # 0 ou 1
            self.draft_first_picker = 0 # Alterna a cada nível
        else:
            self.player2 = None
            self.inventory2 = None
            self.players = [self.player]
            self.inventories = [self.inventory]
            self.shared_coins = 0
            self.shared_level = 1 # Para compatibilidade

        for i, p in enumerate(self.players):
            self._apply_meta_upgrades(p)
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
        self.kill_counts = {}
        self.run_coins_collected = 0
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
        self.altar_spawn_timer = altar_system.ALTAR_FIRST_SPAWN_DELAY
        self.time_scale = 1.0
        self.menu_just_opened_by_altar = None
        self.black_market_cooldown = 0.0
        self.stat_shop_rerolls = 0
        self.pity_counter = 0
        self.current_dimension = "main"
        self.pocket_dimension_state = None
        self.combo_count = 0
        self.combo_timer = 0.0
        self.combo_kps = 0.0
        self.combo_window = 1.0
        self._combo_recent_kills = []
        self.item_events = []
        self.particle_events = []
        self.stamp_fusion_target = None
        self.stamp_fusion_materials = []
        self.stamp_fusion_msg = ""
        self.message = "Sobreviva o maximo que puder."
        self.random = random.Random()
        self.chromatic_spawn_timer = self.random.uniform(CHROMATIC_SPAWN_MIN, CHROMATIC_SPAWN_MAX)
        self.miniboss_spawn_timer = self.random.uniform(MINIBOSS_SPAWN_MIN, MINIBOSS_SPAWN_MAX)
        self.miniboss_arena_center = None
        self.miniboss_arena_radius = 520.0
        self.miniboss_trapped_player = None
        self.harbinger_spawn_timer = HARBINGER_SPAWN_INTERVAL
        self.harbinger_defeats = 0
        self.reaper_spawn_timer = REAPER_SPAWN_INTERVAL
        self.reaper_defeats = 0
        self.reaper_area_anchor = Vector2(self.player.pos)
        self.reaper_area_linger = 0.0
        self.reaper_pressure_level = 0.0
        self.miniboss_kills = 0
        self.completed_escorts = 0
        self.completed_quick_quests = 0
        self.chalice_fragments = {entry["key"]: False for entry in CHALICE_FRAGMENTS}
        self.chalice_hidden_pos = self.player.pos + Vector2(180, -90)
        self.spawn_drop("chalice", self.chalice_hidden_pos, "world_hidden")
        self.chalice_hidden_pos = Vector2(999999, 999999)
        self.pocket_chalice_pos = Vector2(180, -120)
        self.omni_kernel_active = False
        self.omni_orbital_timer = OMNI_ORBITAL_COOLDOWN
        self.omni_active_cooldown = 0.0
        self.omni_time_freeze_timer = 0.0
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
        self.director_pressure = 0.0
        self.director_eval_timer = 0.0
        self.director_recent_kills = 0
        self.director_recent_damage_taken = 0.0
        self.director_enemy_cap_bonus = 0
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

    def _apply_meta_upgrades(self, player):
        upgrades = character_upgrades()
        effects = {key: upgrade_effect_value(key, data["active_level"]) for key, data in upgrades.items()}
        health_mult = max(0.35, 1.0 + effects.get("max_health", 0.0))
        player.max_health = max(1.0, player.max_health * health_mult)
        player.health = player.max_health
        player.defense_bonus += effects.get("defense", 0.0)
        player.speed_bonus += effects.get("speed", 0.0)
        player.attack_rate_bonus += effects.get("attack_rate", 0.0)
        player.damage_bonus += effects.get("damage", 0.0)
        player.vampirism += effects.get("vampirism", 0.0)
        player.magazine_bonus += int(round(effects.get("magazine", 0.0)))
        player.ammo_reserve_bonus += int(round(effects.get("ammo_reserve", 0.0)))
        player.ammo_magazine = max(1, self.magazine_capacity_for(player))
        player.ammo_reserve = max(0, self.max_ammo_reserve_for(player))

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
        return camera_system.camera_focus(self)
    def alive_players(self):
        return [p for p in self.players if not p.is_down]

    def passive_unlock_status(self, key, player=None):
        player = player or self.get_player(self.menu_player_index)
        if key != "robotic_necromancy" or player.char_class != "engineer":
            return True, ""
        if player.passives.get(key, 0) > 0:
            return True, ""
        invested_elsewhere = sum(
            level for passive_key, level in player.passives.items()
            if passive_key != key
        )
        requirements = []
        if player.level < ROBOTIC_NECROMANCY_UNLOCK_LEVEL:
            requirements.append(f"Nivel {ROBOTIC_NECROMANCY_UNLOCK_LEVEL}")
        if invested_elsewhere < ROBOTIC_NECROMANCY_UNLOCK_OTHER_SKILL_LEVELS:
            requirements.append(
                f"{ROBOTIC_NECROMANCY_UNLOCK_OTHER_SKILL_LEVELS} niveis em outras skills"
            )
        if requirements:
            return False, "Requer " + " e ".join(requirements) + "."
        return True, ""

    def omni_active_ready(self):
        return omni_kernel.active_ready(self)

    def omni_time_freeze_active(self):
        return omni_kernel.time_freeze_active(self)

    def omni_time_freeze_multiplier(self):
        return omni_kernel.time_freeze_multiplier(self)

    def omni_active_charge_ratio(self):
        return omni_kernel.active_charge_ratio(self)

    def omni_active_status(self):
        return omni_kernel.active_status(self)

    def register_kill_combo(self):
        now = self.time_alive
        self.combo_count = getattr(self, "combo_count", 0) + 1
        self.combo_timer = 2.2
        recent = getattr(self, "_combo_recent_kills", [])
        recent.append(now)
        cutoff = now - getattr(self, "combo_window", 1.0)
        self._combo_recent_kills = [t for t in recent if t >= cutoff]
        self.combo_kps = len(self._combo_recent_kills) / max(0.1, getattr(self, "combo_window", 1.0))

    def _update_kill_combo(self, dt):
        if getattr(self, "combo_timer", 0.0) <= 0.0:
            self.combo_timer = 0.0
            self.combo_count = 0
            self.combo_kps = 0.0
            self._combo_recent_kills = []
            return
        self.combo_timer = max(0.0, self.combo_timer - dt)
        cutoff = self.time_alive - getattr(self, "combo_window", 1.0)
        self._combo_recent_kills = [t for t in getattr(self, "_combo_recent_kills", []) if t >= cutoff]
        self.combo_kps = len(self._combo_recent_kills) / max(0.1, getattr(self, "combo_window", 1.0))
        if self.combo_timer <= 0.0:
            self.combo_count = 0
            self.combo_kps = 0.0
            self._combo_recent_kills = []

    def enter_pocket_dimension(self):
        return dimensoes.enter_pocket_dimension(self)
    def exit_pocket_dimension(self, reward=True):
        return dimensoes.exit_pocket_dimension(self, reward)
    def enter_olympus_dimension(self):
        return dimensoes.enter_olympus_dimension(self)
    def exit_olympus_dimension(self):
        return dimensoes.exit_olympus_dimension(self)
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
        r = int(255 * self.light_level + 76 * (1.0 - self.light_level))
        g = int(255 * self.light_level + 84 * (1.0 - self.light_level))
        b = int(255 * self.light_level + 122 * (1.0 - self.light_level))
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
            if d.get("movement_slow_timer", 0.0) <= 0.0:
                d["movement_slow_multiplier"] = 1.0
                
        # Update shop cooldowns
        if getattr(self, 'black_market_cooldown', 0.0) > 0.0:
            self.black_market_cooldown = max(0.0, self.black_market_cooldown - dt)
        self.time_alive += dt
        self._update_chalice_system(dt)

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

        self._update_kill_combo(dt)
        
        # Lógica da Dimensão de Bolso (Pocket Dimension)
        if getattr(self, "current_dimension", "main") == "pocket":
            self.pocket_dimension_timer = getattr(self, "pocket_dimension_timer", 30.0) - dt
            for p in self.alive_players():
                p.health = max(0.0, p.health - 1.5 * dt)
                if self.random.random() < dt * 0.4:
                    self.add_floater(p.pos, "-1.5 HP/s VOZ", "#C084FC")
            
            if self.pocket_dimension_timer <= 0.0:
                self.exit_pocket_dimension(reward=True)
                
        # Lógica da Dimensão do Olimpo
        if getattr(self, "current_dimension", "main") == "olympus":
            # Atualiza timers de distorcao
            if getattr(self, "olympus_distortion_timer", 0.0) > 0:
                self.olympus_distortion_timer -= dt
                if self.olympus_distortion_timer <= 0:
                    self.olympus_distortion_type = ""
                    self.olympus_distortion_cooldown = self.random.uniform(10.0, 15.0)
            else:
                self.olympus_distortion_cooldown = getattr(self, "olympus_distortion_cooldown", 5.0) - dt
                if self.olympus_distortion_cooldown <= 0:
                    self.olympus_distortion_type = self.random.choice(["invert_mouse", "invert_keyboard", "flip_screen"])
                    self.olympus_distortion_timer = 5.0
                    self.message = f"Distorcao Divina: {self.olympus_distortion_type}!"
            
            # Checa se o Boss God morreu
            has_god = any(e.kind == "god" for e in self.enemies)
            god_spawned = getattr(self, "god_spawned", False)
            if god_spawned and not has_god:
                self.exit_olympus_dimension()

        if self.time_alive >= 3600.0 and not getattr(self, "olympus_triggered", False):
            self.enter_olympus_dimension()

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
        if self.game_over:
            self.miniboss_arena_center = None
            self.miniboss_trapped_player = None

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
        return movimento.move_player(self, dt, move_vector, aim_world)

    def _move_player_for(self, dt, move_vector, aim_world, player):
        return movimento.move_player_for(self, dt, move_vector, aim_world, player)
    # ------------------------------------------------------------------ #
    # PER-PLAYER STAT HELPERS                                              #
    # ------------------------------------------------------------------ #

    def effective_speed_multiplier_for(self, player):
        return atributos.effective_speed_multiplier_for(self, player)

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

    def magazine_capacity_for(self, player):
        return atributos.magazine_capacity_for(player)

    def max_ammo_reserve_for(self, player):
        return atributos.max_ammo_reserve_for(player)





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
        return escort_system.update_world_timers(self, dt)

    def _trigger_escort_event(self):
        return escort_system.trigger_escort_event(self)

    def _update_escort_event(self, dt):
        return escort_system.update_escort_event(self, dt)





















    def _update_hazards(self, dt):
        focus = self.camera_focus  # já é um Vector2
        for hazard in list(self.world.nearby_hazards(focus.x, focus.y, 980)):
            hazard.pulse += dt
            if hazard.kind == "mine":
                is_dash_mine = str(getattr(hazard, "id", "")).startswith("dash_mine:")
                trigger_pos = None
                if not is_dash_mine:
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
        return camera_system.update_camera(self, dt)
    def random_offset(self, amount):
        angle = self.random.random() * math.tau
        distance = self.random.uniform(0, amount)
        return Vector2(math.cos(angle), math.sin(angle)) * distance

    def grant_chalice_fragment(self, key, pos=None):
        return calice.grant_fragment(self, key, pos)

    def _update_chalice_system(self, dt):
        return calice.update_progress(self, dt)

    def _activate_omni_kernel(self, pos):
        return omni_kernel.activate(self, pos)

    def _fire_omni_orbital_laser(self):
        return omni_kernel.fire_orbital_laser(self)

    def try_omni_active(self):
        return omni_kernel.try_active(self)


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
                if c.kind == "robo_minion":
                    self._apply_area_damage(c.pos, 118 + c.level * 8, 42 + c.level * 7, "special", damage_players=False)
                    self.item_events.append({"type": "explosion", "pos": Vector2(c.pos), "radius": 118 + c.level * 8, "damage": 0, "age": 0.0, "duration": 0.28, "owner": c.owner})
                self.emit_particles(c.pos, count=15, color="#FBBF24" if c.kind in ("turret", "laser_turret", "drone", "robo_minion") else ("#F97316" if c.kind == "torch" else "#38BDF8"), speed=100)
                continue
                
            if c.kind in ("turret", "laser_turret", "drone", "robo_minion"):
                owner_player = self.get_player(c.owner)
                reinforced = owner_player.passives.get("reinforced_turrets", 0)
                overclock = owner_player.passives.get("overclock", 0)
                c.attack_timer -= dt
                if c.kind in ("drone", "robo_minion"):
                    owner_pos = owner_player.pos
                    if c.kind == "robo_minion":
                        leash_radius = 310.0
                        inner_radius = 105.0
                        orbit_dir = Vector2(math.cos(c.angle + c.age * 1.25), math.sin(c.angle + c.age * 1.25))
                        desired = owner_pos + orbit_dir * (170.0 + 34.0 * math.sin(c.age * 1.7 + c.angle))
                        enemy_target = self._nearest_enemy(c.pos, 360)
                        if enemy_target is not None and enemy_target.pos.distance_squared_to(owner_pos) <= leash_radius * leash_radius:
                            desired = enemy_target.pos - (enemy_target.pos - owner_pos).normalize() * 90 if enemy_target.pos != owner_pos else desired
                        offset = c.pos - owner_pos
                        if offset.length_squared() > leash_radius * leash_radius:
                            desired = owner_pos + offset.normalize() * (leash_radius * 0.82)
                        elif offset.length_squared() < inner_radius * inner_radius and offset.length_squared() > 0:
                            desired = owner_pos + offset.normalize() * inner_radius
                        move = desired - c.pos
                        if move.length_squared() > 1:
                            c.pos += move.normalize() * min(move.length(), 245.0 * dt)
                    else:
                        desired_dist = 180
                        if c.pos.distance_squared_to(owner_pos) > desired_dist * desired_dist:
                            direction_to_owner = owner_pos - c.pos
                            if direction_to_owner.length_squared() > 0:
                                c.pos += direction_to_owner.normalize() * 220 * dt
                        c.pos += Vector2(math.cos(self.time_alive * 2.2 + c.angle), math.sin(self.time_alive * 2.0 + c.angle)) * 18 * dt
                best_dist = (420 if c.kind == "laser_turret" else 330)**2
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
                        damage = self.projectile_damage_for(owner_player, inv) * (1.0 + c.level * 0.18 + reinforced * 0.18)
                        if c.kind == "robo_minion" and int(c.age * 10) % 45 < 2:
                            start = Vector2(c.pos)
                            end = start + direction * 440
                            self._apply_laser_damage(start, end, 16, damage * 0.58, damage_player=False, killer_index=c.owner, knockback=280)
                            self.item_events.append({"type": "laser", "start": start, "end": end, "width": 16, "age": 0.0, "duration": 0.16, "color": "#FDE047"})
                            c.attack_timer = 0.42
                        elif c.kind == "laser_turret":
                            start = Vector2(c.pos)
                            end = start + direction * 520
                            self._apply_laser_damage(start, end, 18 + c.level * 4, damage * 0.62, damage_player=False, killer_index=c.owner)
                            self.item_events.append({
                                "type": "laser",
                                "start": start,
                                "end": end,
                                "width": 18 + c.level * 4,
                                "age": 0.0,
                                "duration": 0.16,
                                "color": "#FACC15",
                            })
                            c.attack_timer = max(0.38, 1.05 - reinforced * 0.05 - overclock * 0.03)
                        else:
                            speed_mult = 1.75 if c.kind in ("drone", "robo_minion") else 1.5
                            self.projectiles.append(
                                Projectile(
                                    pos=Vector2(c.pos) + direction * c.radius,
                                    vel=direction * PROJECTILE_SPEED * speed_mult,
                                    damage=damage * (0.62 if c.kind in ("drone", "robo_minion") else 1.0),
                                    radius=self.projectile_radius_for(owner_player, PROJECTILE_RADIUS * (0.9 if c.kind in ("drone", "robo_minion") else 1.2)),
                                    owner=c.owner
                                )
                            )
                            c.attack_timer = max(0.16, (0.40 if c.kind in ("drone", "robo_minion") else 0.6) - reinforced * 0.045 - overclock * 0.025)
                        
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
        return altar_system.spawn_altar(self)

    def _update_altars(self, dt):
        return altar_system.update_altars(self, dt)

    def finish_altar_interaction(self, destroy=True):
        return altar_system.finish_altar_interaction(self, destroy)

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
