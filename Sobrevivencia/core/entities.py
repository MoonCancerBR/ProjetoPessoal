from dataclasses import dataclass, field
from typing import Any

from pygame.math import Vector2

if __package__:
    from ..data.constants import (
        BUFF_DURATION,
        BASE_MAGAZINE_CAPACITY,
        PLAYER_BASE_SPEED,
        PLAYER_MAX_HEALTH,
        PLAYER_RADIUS,
        PROJECTILE_DAMAGE,
        PROJECTILE_LIFE,
        PROJECTILE_RADIUS,
        SHIELD_DURATION,
        STARTING_AMMO_RESERVE,
        SPECIAL_MAX,
        SWORD_ARC,
        SWORD_DAMAGE,
        SWORD_DURATION,
        SWORD_RADIUS,
        CHARACTERS,
    )
else:
    from Sobrevivencia.data.constants import (
        BUFF_DURATION,
        BASE_MAGAZINE_CAPACITY,
        PLAYER_BASE_SPEED,
        PLAYER_MAX_HEALTH,
        PLAYER_RADIUS,
        PROJECTILE_DAMAGE,
        PROJECTILE_LIFE,
        PROJECTILE_RADIUS,
        SHIELD_DURATION,
        STARTING_AMMO_RESERVE,
        SPECIAL_MAX,
        SWORD_ARC,
        SWORD_DAMAGE,
        SWORD_DURATION,
        SWORD_RADIUS,
        CHARACTERS,
    )


@dataclass
class RectBody:
    x: float
    y: float
    w: float
    h: float

    @property
    def left(self):
        return self.x

    @property
    def right(self):
        return self.x + self.w

    @property
    def top(self):
        return self.y

    @property
    def bottom(self):
        return self.y + self.h

    @property
    def center(self):
        return Vector2(self.x + self.w * 0.5, self.y + self.h * 0.5)

    def intersects(self, other, padding=0):
        return not (
            self.right + padding < other.left
            or self.left - padding > other.right
            or self.bottom + padding < other.top
            or self.top - padding > other.bottom
        )


@dataclass
class Player:
    char_class: str = "vanguard"
    pos: Vector2 = field(default_factory=lambda: Vector2(0, 0))
    radius: float = PLAYER_RADIUS
    max_health: float = PLAYER_MAX_HEALTH
    health: float = PLAYER_MAX_HEALTH
    base_speed: float = PLAYER_BASE_SPEED
    mode: str = "weapon_1"
    level: int = 1
    xp: float = 0
    xp_to_next: float = 55
    coins: int = 0
    kills: int = 0
    score: int = 0
    special: float = 0
    special_ranged: float = 0
    special_melee: float = 0
    ammo_magazine: int = BASE_MAGAZINE_CAPACITY
    ammo_reserve: int = STARTING_AMMO_RESERVE
    reload_timer: float = 0
    reload_duration: float = 0
    reload_step_timer: float = 0
    full_ammo_msg_timer: float = 0
    forced_reload: bool = False
    shoot_timer: float = 0
    sword_timer: float = 0
    dash_timer: float = 0
    dash_cooldown: float = 0
    invulnerable_timer: float = 0
    shield_timer: float = 0
    last_move_dir: Vector2 = field(default_factory=lambda: Vector2(1, 0))
    dash_dir: Vector2 = field(default_factory=lambda: Vector2(1, 0))
    buffs: dict = field(default_factory=dict)
    speed_bonus: float = 0
    damage_bonus: float = 0
    attack_rate_bonus: float = 0
    sword_range_bonus: float = 0
    special_gain_bonus: float = 0
    vampirism: float = 0
    magazine_bonus: int = 0
    reload_speed_bonus: float = 0
    passives: dict = field(default_factory=dict)
    # Bônus injetados pelos itens equipados (recalculados a cada mudança de inventário)
    item_speed_bonus: float = 0
    item_damage_bonus: float = 0
    item_attack_rate_bonus: float = 0
    item_sword_range_bonus: float = 0
    item_guardian_reduction: float = 0
    # Multiplayer Co-op
    player_index: int = 0
    is_down: bool = False
    revive_progress: float = 0.0

    # Sistema de Selos (Stamps) — Modificadores Globais de Armas
    # weapon_stamps: dict { "weapon_1": [Stamp, ...], "weapon_2": [Stamp, ...] } — max 3 por arma
    # stamp_reserve: list[Stamp] — selos coletados mas não equipados
    weapon_stamps: dict = field(default_factory=lambda: {"weapon_1": [], "weapon_2": []})
    stamp_reserve: list = field(default_factory=list)
    
    # Physics
    body: Any = field(default=None, init=False)
    shape: Any = field(default=None, init=False)

    def __post_init__(self):
        if self.char_class in CHARACTERS:
            self.passives = {k: 0 for k in CHARACTERS[self.char_class]["passives"]}
        self.xp_to_next = int(40 + 25 * self.level)

    def damage_multiplier(self):
        multiplier = 1.0 + self.damage_bonus + self.item_damage_bonus
        if self.buffs.get("power", 0) > 0:
            multiplier += 0.25
        return multiplier

    def speed_multiplier(self):
        multiplier = 1.0 + self.speed_bonus + self.item_speed_bonus
        if self.buffs.get("speed", 0) > 0:
            multiplier += 0.45
        if self.shield_timer > 0:
            multiplier += 0.25
        return multiplier

    def attack_rate_multiplier(self):
        return 1.0 + self.attack_rate_bonus + self.item_attack_rate_bonus

    def projectile_damage(self):
        return PROJECTILE_DAMAGE * self.damage_multiplier()

    def sword_damage(self):
        return SWORD_DAMAGE * self.damage_multiplier()

    def sword_radius(self):
        return SWORD_RADIUS * (1.0 + self.sword_range_bonus + self.item_sword_range_bonus)

    def add_special(self, amount, channel="ranged"):
        gained = amount * (1.0 + self.special_gain_bonus)
        if channel == "melee":
            self.special_melee = min(SPECIAL_MAX, self.special_melee + gained)
        else:
            self.special_ranged = min(SPECIAL_MAX, self.special_ranged + gained)
        self.special = max(self.special_ranged, self.special_melee)

    def activate_buff(self, name):
        self.buffs[name] = BUFF_DURATION

    def activate_shield(self):
        self.shield_timer = SHIELD_DURATION
        self.invulnerable_timer = max(self.invulnerable_timer, SHIELD_DURATION)


@dataclass
class Enemy:
    id: int
    pos: Vector2
    kind: str
    radius: float
    speed: float
    max_health: float
    health: float
    damage: float
    xp_value: int
    color: str
    special_value: float
    coin_chance: float
    frozen_timer: float = 0
    poison_timer: float = 0
    poison_dps: float = 0
    hit_flash: float = 0
    bleed_timer: float = 0
    bleed_dps: float = 0
    knockback: Vector2 = field(default_factory=lambda: Vector2(0, 0))
    lifetime: float = -1
    phase: float = 0
    special_timer: float = 0
    summon_cooldown: float = 0.0
    immune_to_knockback: bool = False
    blood_mark_timer: float = 0.0
    blood_mark_level: int = 0
    blood_harvest_value: int = 0
    
    # Physics
    body: Any = field(default=None, init=False)
    shape: Any = field(default=None, init=False)
    enraged: bool = False
    intangible: bool = False
    action: str = ""
    action_timer: float = 0
    target_pos: Vector2 = field(default_factory=lambda: Vector2(0, 0))


@dataclass
class Projectile:
    pos: Vector2
    vel: Vector2
    damage: float = PROJECTILE_DAMAGE
    radius: float = PROJECTILE_RADIUS
    life: float = PROJECTILE_LIFE
    freeze: bool = False
    poison: bool = False
    poison_dps: float = 0
    bounces_left: int = 0
    hit_ids: set = field(default_factory=set)
    pierce: int = 0
    explosive_level: int = 0
    homing_level: int = 0
    stun_level: int = 0
    owner: int = 0
    style: str = "bullet"
    color: str = ""
    trail_scale: float = 3.2
    knockback: float = 0.0
    mark_level: int = 0
    mark_duration: float = 0.0


@dataclass
class Slash:
    origin: Vector2
    direction: Vector2
    radius: float = SWORD_RADIUS
    arc: float = SWORD_ARC
    damage: float = SWORD_DAMAGE
    duration: float = SWORD_DURATION
    age: float = 0
    hit_ids: set = field(default_factory=set)
    prey_mark_level: int = 0
    execute_level: int = 0
    shockwave_level: int = 0
    bleed_level: int = 0
    shadow_lunge_level: int = 0
    heavy_alloy_level: int = 0
    magnetic_pull_level: int = 0
    owner: int = 0
    style: str = "swing"
    color: str = ""
    edge_color: str = ""
    knockback: float = 330.0
    pull_strength: float = 0.0
    mark_level: int = 0
    consume_mark: bool = False


@dataclass
class Drop:
    pos: Vector2
    kind: str
    value: float = 1
    radius: float = 10
    ttl: float = 18.0
    bob: float = 0
    activation_timer: float = 0.0
    activation_player_index: int = -1


@dataclass
class Destructible:
    id: str
    rect: RectBody
    hp: float
    max_hp: float
    kind: str
    chunk: tuple
    hit_flash: float = 0


@dataclass
class Hazard:
    id: str
    rect: RectBody
    kind: str
    chunk: tuple
    pulse: float = 0


@dataclass
class StaticLight:
    id: str
    pos: Vector2
    kind: str
    radius: float
    chunk: tuple
    pulse: float = 0.0


@dataclass
class EscortNPC:
    pos: Vector2
    hp: float
    max_hp: float
    speed: float
    kind: str
    radius: float = 12.0
    hit_flash: float = 0.0

@dataclass
class PlayerConstruct:
    pos: Vector2
    kind: str
    hp: float
    max_hp: float
    radius: float
    duration: float
    age: float = 0
    attack_timer: float = 0
    owner: int = 0
    hit_flash: float = 0
    level: int = 0
    angle: float = 0.0

@dataclass
class Altar:
    pos: Vector2
    kind: str  # "weapon_altar", "skill_altar", "stat_altar", "stamps_altar", "black_market_altar"
    radius: float = 24.0
    active: bool = True
    age: float = 0.0
    hit_flash: float = 0.0
