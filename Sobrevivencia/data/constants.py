import math
import pygame


SCREEN_WIDTH = 1100
SCREEN_HEIGHT = 720
FPS = 60

PIXEL_ART_MODE = True
PIXEL_ART_DOWNSCALE = 2

WORLD_TILE_SIZE = 96
CHUNK_SIZE = 768
VIEW_PADDING = 180

PLAYER_RADIUS = 18
PLAYER_MAX_HEALTH = 120
PLAYER_BASE_SPEED = 235.0
PLAYER_CONTACT_GRACE = 0.35

DASH_SPEED = 790.0
DASH_DURATION = 0.17
DASH_COOLDOWN = 1.25

PROJECTILE_SPEED = 720.0
PROJECTILE_RADIUS = 5
PROJECTILE_DAMAGE = 16
PROJECTILE_COOLDOWN = 0.17
PROJECTILE_LIFE = 1.65
MAX_PROJECTILES = 130
PROJECTILE_PARALLEL_SPACING = 11
RICOCHET_RANGE = 360
RICOCHET_DAMAGE_MULTIPLIER = 0.76
POISON_DURATION = 3.4
POISON_BASE_DPS = 6.0

BASE_MAGAZINE_CAPACITY = 20
MAGAZINE_CAPACITY_PER_LEVEL = 2
STARTING_AMMO_RESERVE = 60
RELOAD_DURATION = 2.15
AMMO_DROP_PICKUP_MIN = 5
AMMO_DROP_PICKUP_MAX = 12

SWORD_DAMAGE = 46
SWORD_RADIUS = 92
SWORD_ARC = math.radians(88)
SWORD_COOLDOWN = 0.42
SWORD_DURATION = 0.16

SPECIAL_MAX = 100
SPECIAL_RADIUS = 560
SPECIAL_DAMAGE = 230
SPECIAL_CHARGE_BASIC = 9
SPECIAL_CHARGE_RUNNER = 7
SPECIAL_CHARGE_BRUTE = 16
SPECIAL_COMBO_HOLD_SECONDS = 1.15
SKILL_UPGRADE_COST = 3
SKILL_UNLOCK_COST = 5
SPECIAL_SKILL_UPGRADE_COST = 6
SPECIAL_SKILL_UNLOCK_COST = 8
STAT_SHOP_UNLOCK_LEVEL = 1
STAT_SHOP_ROLL_COST = 1
STAT_SHOP_REROLL_COST = 1
FUSION_COST = 3
STAMP_RESERVE_LIMIT = 60

STAT_SHOP_STATS = [
    {
        "key": "max_health",
        "label": "Vida maxima",
        "base": 10.0,
        "cost": 0.22,
        "kind": "flat",
        "unit": "vida",
    },
    {
        "key": "damage",
        "label": "Dano",
        "base": 0.035,
        "cost": 75.0,
        "kind": "percent",
        "unit": "dano",
    },
    {
        "key": "speed",
        "label": "Velocidade",
        "base": 0.030,
        "cost": 68.0,
        "kind": "percent",
        "unit": "velocidade",
    },
    {
        "key": "attack_rate",
        "label": "Cadencia",
        "base": 0.032,
        "cost": 70.0,
        "kind": "percent",
        "unit": "cadencia",
    },
    {
        "key": "sword_range",
        "label": "Alcance corpo a corpo",
        "base": 0.045,
        "cost": 52.0,
        "kind": "percent",
        "unit": "alcance",
    },
    {
        "key": "special_gain",
        "label": "Carga de especial",
        "base": 0.050,
        "cost": 46.0,
        "kind": "percent",
        "unit": "carga",
    },
    {
        "key": "vampirism",
        "label": "Vampirismo",
        "base": 0.8,
        "cost": 1.35,
        "kind": "decimal",
        "unit": "cura/abate",
    },
    {
        "key": "magazine",
        "label": "Pente",
        "base": 3.0,
        "cost": 0.82,
        "kind": "integer",
        "unit": "municoes",
    },
    {
        "key": "reload_speed",
        "label": "Recarga",
        "base": 0.030,
        "cost": 74.0,
        "kind": "percent",
        "unit": "recarga",
    },
]

XP_MAGNET_RADIUS = 150
DROP_PICKUP_RADIUS = 32
DROP_ATTRACT_SPEED = 360.0

SHIELD_DURATION = 7.0
BUFF_DURATION = 8.0
FREEZE_DURATION = 2.4

CHROMATIC_LIFETIME = 12.0
CHROMATIC_SPAWN_MIN = 18.0
CHROMATIC_SPAWN_MAX = 32.0

MINIBOSS_SPAWN_MIN = 86.0
MINIBOSS_SPAWN_MAX = 132.0
MINIBOSS_LEAP_WARNING = 0.95
MINIBOSS_LEAP_RADIUS = 128
MINIBOSS_LEAP_DAMAGE = 48
MINIBOSS_LASER_WARNING = 0.85
MINIBOSS_LASER_RANGE = 760
MINIBOSS_LASER_WIDTH = 46
MINIBOSS_LASER_DAMAGE = 28
MINIBOSS_SUMMON_DURATION = 2.0
MINIBOSS_SUMMON_COUNT_MIN = 3
MINIBOSS_SUMMON_COUNT_MAX = 5
MINIBOSS_SUMMON_COOLDOWN_MIN = 18.0
MINIBOSS_SUMMON_COOLDOWN_MAX = 28.0
HARBINGER_SPAWN_INTERVAL = 30 * 60.0
REAPER_SPAWN_INTERVAL = 60 * 60.0
REAPER_MIN_SPAWN_TIME = 30 * 60.0
REAPER_STALL_RADIUS = 520.0
REAPER_STALL_GRACE = 95.0
REAPER_STALL_ACCEL_MAX = 1.45
REAPER_AURA_RADIUS = 250
REAPER_AURA_DPS = 11.0
REAPER_BLINK_WARNING = 0.65
REAPER_DOOM_WARNING = 0.82
REAPER_DASH_WARNING = 0.34
REAPER_DASH_RANGE = 560
REAPER_DOOM_RADIUS = 190

MINE_TRIGGER_RADIUS = 28
MINE_EXPLOSION_RADIUS = 145
MINE_DAMAGE = 74
FIRE_DAMAGE_PER_SECOND = 17.0
ICE_SPEED_MULTIPLIER = 1.36

MAX_ENEMIES = 95
SPAWN_START_DELAY = 1.15
SPAWN_MIN_DELAY = 0.23
SPAWN_DISTANCE_MIN = 560
SPAWN_DISTANCE_MAX = 760
CONTACT_DAMAGE_PER_SECOND = 17.0

# Balanceamento dinamico de fim de partida
POWER_SCORE_WEIGHT = 0.95
DIRECTOR_PRESSURE_INTERVAL = 8.0
DIRECTOR_TARGET_KILLS_PER_MIN = 72.0
DIRECTOR_TARGET_DAMAGE_PER_MIN = 22.0
DIRECTOR_MAX_PRESSURE = 1.0
LATE_GAME_START_TIME = 12 * 60.0
ELITE_TIER_START_TIME = 7 * 60.0

CAMERA_SMOOTHING = 9.5
SCREEN_SHAKE_DECAY = 5.5

# Configurações de Câmera Dinâmica
CAMERA_ZOOM_MIN_SCALE = 0.85
CAMERA_ZOOM_MAX_DISTANCE = 550

# Multiplayer Co-op
TETHER_MAX_DISTANCE = 650
TETHER_TELEPORT_MARGIN = 60
REVIVE_RADIUS = 80
REVIVE_TIME = 4.0
REVIVE_HP_PERCENT = 0.5
P1_AIM_COLOR = "#38BDF8"
P2_AIM_COLOR = "#FF3B58"

COLORS = {
    "bg": "#05050A",
    "panel": "#111827",
    "panel_2": "#1B2440",
    "text": "#FFF7D6",
    "muted": "#A7B0C7",
    "muted_2": "#5E6A86",
    "health": "#FF3B58",
    "health_bg": "#39111B",
    "special": "#28D7FF",
    "xp": "#35F06B",
    "coin": "#FFD447",
    "player": "#FFF7D6",
    "player_core": "#28D7FF",
    "projectile": "#7DF9FF",
    "projectile_freeze": "#A6F3FF",
    "poison": "#8BFF4A",
    "sword": "#FFE66D",
    "shield": "#4F8CFF",
    "danger": "#FF5C7A",
    "upgrade": "#D96CFF",
}

TERRAIN_TYPES = {
    "grass": {
        "color": "#12351F",
        "accent": "#1B6B36",
        "speed": 1.0,
        "name": "Grama",
    },
    "sand": {
        "color": "#6B5A2A",
        "accent": "#C39B3B",
        "speed": 0.55,
        "name": "Areia",
    },
    "mud": {
        "color": "#352235",
        "accent": "#66415D",
        "speed": 0.76,
        "name": "Lama",
    },
    "stone": {
        "color": "#20233F",
        "accent": "#414A78",
        "speed": 0.92,
        "name": "Pedra",
    },
}

ENEMY_TYPES = {
    "basic": {
        "name": "Errante",
        "radius": 17,
        "speed": 122.0,
        "health": 36,
        "damage": 14.0,
        "xp": 11,
        "color": "#F97316",
        "special": SPECIAL_CHARGE_BASIC,
        "coin_chance": 0.12,
    },
    "runner": {
        "name": "Corredor",
        "radius": 13,
        "speed": 178.0,
        "health": 24,
        "damage": 11.0,
        "xp": 9,
        "color": "#F43F5E",
        "special": SPECIAL_CHARGE_RUNNER,
        "coin_chance": 0.10,
    },
    "brute": {
        "name": "Bruto",
        "radius": 24,
        "speed": 82.0,
        "health": 95,
        "damage": 25.0,
        "xp": 25,
        "color": "#A855F7",
        "special": SPECIAL_CHARGE_BRUTE,
        "coin_chance": 0.28,
    },
    "chromatic": {
        "name": "Erratico Cromatico",
        "radius": 20,
        "speed": 255.0,
        "health": 62,
        "damage": 6.0,
        "xp": 36,
        "color": "#22D3EE",
        "special": 18,
        "coin_chance": 0.75,
    },
    "miniboss": {
        "name": "Colosso Errante",
        "radius": 46,
        "speed": 58.0,
        "health": 720,
        "damage": 22.0,
        "xp": 180,
        "color": "#7C3AED",
        "special": 40,
        "coin_chance": 1.0,
    },
    "spitter": {
        "name": "Atirador Acido",
        "radius": 16,
        "speed": 92.0,  # Reduzido de 108
        "health": 58,
        "damage": 9.0,   # Reduzido de 13
        "xp": 18,
        "color": "#84CC16",
        "special": 11,
        "coin_chance": 0.18,
    },
    "bulwark": {
        "name": "Guardiao Blindado",
        "radius": 29,
        "speed": 66.0,
        "health": 175,
        "damage": 30.0,
        "xp": 38,
        "color": "#64748B",
        "special": 22,
        "coin_chance": 0.34,
    },
    "sapper": {
        "name": "Demolidor Instavel",
        "radius": 15,
        "speed": 168.0,
        "health": 32,
        "damage": 8.0,
        "xp": 16,
        "color": "#FACC15",
        "special": 10,
        "coin_chance": 0.16,
    },
    "minion": {
        "name": "Servo do Colosso",
        "radius": 11,
        "speed": 200.0,
        "health": 18,
        "damage": 8.0,
        "xp": 4,
        "color": "#C084FC",
        "special": 3,
        "coin_chance": 0.0,
    },
    "phantom": {
        "name": "Espectro Intangivel",
        "radius": 18,
        "speed": 135.0,
        "health": 48,
        "damage": 12.0,
        "xp": 22,
        "color": "#D8B4FE",
        "special": 15,
        "coin_chance": 0.20,
    },
    "golem": {
        "name": "Golem de Magnetita",
        "radius": 26,
        "speed": 72.0,
        "health": 145,
        "damage": 28.0,
        "xp": 35,
        "color": "#475569",
        "special": 20,
        "coin_chance": 0.35,
    },
    "necromancer": {
        "name": "Invocador Sombrio",
        "radius": 22,
        "speed": 98.0,
        "health": 85,
        "damage": 15.0,
        "xp": 42,
        "color": "#9333EA",
        "special": 25,
        "coin_chance": 0.40,
    },
    "morcego_sombra": {
        "name": "Morcego Sombra",
        "radius": 12,
        "speed": 230.0,
        "health": 22,
        "damage": 10.0,
        "xp": 12,
        "color": "#C084FC",
        "special": 6,
        "coin_chance": 0.08,
    },
    "lobo_infectado": {
        "name": "Lobo Infectado",
        "radius": 18,
        "speed": 185.0,
        "health": 58,
        "damage": 24.0,
        "xp": 22,
        "color": "#FB7185",
        "special": 14,
        "coin_chance": 0.18,
    },
    "harbinger": {
        "name": "Arauto do Fim",
        "radius": 34,
        "speed": 172.0,
        "health": 5200,
        "damage": 58.0,
        "xp": 520,
        "color": "#DC2626",
        "special": 100,
        "coin_chance": 1.0,
    },
    "reaper": {
        "name": "Ceifador da Margem",
        "radius": 42,
        "speed": 228.0,
        "health": 7600,
        "damage": 72.0,
        "xp": 760,
        "color": "#111827",
        "special": 140,
        "coin_chance": 1.0,
    },
    "god": {
        "name": "GOD",
        "radius": 50,
        "speed": 300.0,
        "health": 99999,
        "damage": 150.0,
        "xp": 9999,
        "color": "#FFD700",
        "special": 999,
        "coin_chance": 1.0,
    },
}

CHALICE_FRAGMENTS = [
    {"key": "miniboss_3", "label": "III", "name": "Nucleo do Colosso"},
    {"key": "world_hidden", "label": "MAP", "name": "Fragmento Perdido"},
    {"key": "pocket_hidden", "label": "DIM", "name": "Fragmento do Vazio"},
    {"key": "escort_4", "label": "ESC", "name": "Juramento de Escolta"},
    {"key": "quest_5", "label": "OBJ", "name": "Selo de Objetivos"},
    {"key": "combat_mark", "label": "K", "name": "Memoria de Combate"},
    {"key": "time_mark", "label": "T", "name": "Ampulheta Singular"},
]

CHALICE_KILL_TARGET = 650
CHALICE_COMBO_TARGET = 80
CHALICE_TIME_TARGET = 20 * 60.0
OMNI_ORBITAL_COOLDOWN = 9.0
OMNI_TIME_FREEZE_COOLDOWN = 55.0
OMNI_TIME_FREEZE_DURATION = 4.5
OMNI_TIME_FREEZE_ENEMY_MULTIPLIER = 0.12
ROBOTIC_NECROMANCY_UNLOCK_LEVEL = 8
ROBOTIC_NECROMANCY_UNLOCK_OTHER_SKILL_LEVELS = 5

UPGRADES = {
    "speed": {
        "title": "Passos Leves",
        "description": "+8% velocidade permanente.",
    },
    "damage": {
        "title": "Lamina e Cano",
        "description": "+13% dano em todos os ataques.",
    },
    "max_health": {
        "title": "Pulso Vital",
        "description": "+22 vida maxima e cura parcial.",
    },
    "fire_rate": {
        "title": "Ritmo de Combate",
        "description": "+11% cadencia de tiros e golpes.",
    },
    "sword_range": {
        "title": "Alcance da Espada",
        "description": "+10% alcance do corte.",
    },
    "special_gain": {
        "title": "Nucleo Instavel",
        "description": "+16% carga de especial por abate.",
    },
    "vampirism": {
        "title": "Vampirismo",
        "description": "Recupera vida sempre que derrota inimigos.",
    },
}

OMNI_UPGRADES = {
    "omni_power": {
        "title": "Poder Absoluto",
        "description": "+25% Dano, Cadência e Tamanho da Arma.",
    },
    "omni_survival": {
        "title": "Resiliência Máxima",
        "description": "+45 Vida Max, Velocidade e Vampirismo.",
    },
    "omni_special": {
        "title": "Mestre Supremo",
        "description": "Ganha 2x de carga no especial e mais alcance.",
    },
}

CHARACTERS = {
    "vanguard": {
        "name": "A Vanguarda",
        "color": "#F8FAFC",
        "core_color": "#38BDF8",
        "shape": "circle_triangle",
        "weapon_1": "Pistola",
        "weapon_2": "Espada",
        "special": "Explosão Radial",
        "specials": {
            "weapon_1": "Explosão Radial",
            "weapon_2": "Carga Titânica",
            "combo": "Bastiao de Ruptura",
        },
        "passives": {
            "ricochet": {
                "title": "Balas Ricocheteantes",
                "short": "RIC",
                "category": "Distância",
                "description": "Projéteis saltam para inimigos próximos.",
            },
            "poison": {
                "title": "Munição Venenosa",
                "short": "VEN",
                "category": "Distância",
                "description": "Aplica dano contínuo ao inimigo atingido.",
            },
            "multishot": {
                "title": "Rajada Paralela",
                "short": "MUL",
                "category": "Distância",
                "description": "Adiciona balas paralelas ao disparo.",
            },
            "piercing_rounds": {
                "title": "Projéteis Perfurantes",
                "short": "PER",
                "category": "Distância",
                "description": "Tiros ganham perfuração e dano leve.",
            },
            "wide_cleave": {
                "title": "Corte Amplo",
                "short": "AMP",
                "category": "Corpo a corpo",
                "description": "Espada ganha arco e alcance.",
            },
            "execution_edge": {
                "title": "Fio Executor",
                "short": "EXE",
                "category": "Corpo a corpo",
                "description": "Espada causa mais dano em inimigos feridos.",
            },
            "shockwave": {
                "title": "Onda de Impacto",
                "short": "OND",
                "category": "Corpo a corpo",
                "description": "Golpes espalham dano ao redor do alvo.",
            },
            "combat_drill": {
                "title": "Doutrina de Combate",
                "short": "DOU",
                "category": "Ambas",
                "description": "Aumenta dano e cadência das duas armas.",
            },
            "field_salvage": {
                "title": "Saque de Campo",
                "short": "SAQ",
                "category": "Ambas",
                "description": "Abates podem recuperar munição extra.",
            },
            "reactor_blast": {
                "title": "Reator Crítico",
                "short": "REA",
                "category": "Especial",
                "description": "Especial fica maior, mais forte e reabastece o pente.",
            },
        }
    },
    "huntress": {
        "name": "A Caçadora",
        "color": "#166534",
        "core_color": "#F97316",
        "shape": "circle_star",
        "weapon_1": "Arco Longo",
        "weapon_2": "Adagas",
        "special": "Chuva de Flechas",
        "specials": {
            "weapon_1": "Chuva de Flechas",
            "weapon_2": "Dança das Adagas",
            "combo": "Eclipse da Predadora",
        },
        "passives": {
            "explosive": {
                "title": "Flechas Explosivas",
                "short": "EXP",
                "category": "Distância",
                "description": "Impacto da flecha causa explosão em área.",
            },
            "prey_mark": {
                "title": "Marca da Presa",
                "short": "MAR",
                "category": "Corpo a corpo",
                "description": "Adagas marcam, inimigo toma mais dano.",
            },
            "homing": {
                "title": "Flecha Teleguiada",
                "short": "TEL",
                "category": "Distância",
                "description": "Flechas buscam os inimigos no ar.",
            },
            "splinter_arrows": {
                "title": "Flechas Estilhaço",
                "short": "EST",
                "category": "Distância",
                "description": "Disparos lançam flechas laterais menores.",
            },
            "bleeding_blades": {
                "title": "Lâminas Sangrentas",
                "short": "SAN",
                "category": "Corpo a corpo",
                "description": "Adagas aplicam sangramento acumulável.",
            },
            "fan_blades": {
                "title": "Leque de Adagas",
                "short": "LEQ",
                "category": "Corpo a corpo",
                "description": "Adagas ganham arco, alcance e dano.",
            },
            "shadow_lunge": {
                "title": "Investida Sombria",
                "short": "INV",
                "category": "Corpo a corpo",
                "description": "Acertos de adaga reduzem recarga do dash.",
            },
            "predator_focus": {
                "title": "Foco Predador",
                "short": "FOC",
                "category": "Ambas",
                "description": "Aumenta dano e ritmo das duas armas.",
            },
            "ammo_siphon": {
                "title": "Saque Preciso",
                "short": "SAQ",
                "category": "Ambas",
                "description": "Abates podem render munição e carga de especial.",
            },
            "storm_eye": {
                "title": "Olho da Tempestade",
                "short": "OLH",
                "category": "Especial",
                "description": "Chuva de Flechas dura mais e cobre área maior.",
            },
        }
    },
    "engineer": {
        "name": "O Engenheiro",
        "color": "#FEF08A",
        "core_color": "#EAB308",
        "shape": "circle_square",
        "weapon_1": "Canhão de Plasma",
        "weapon_2": "Chave Magnética",
        "special": "Grade de Torretas",
        "specials": {
            "weapon_1": "Grade de Torretas",
            "weapon_2": "Singularidade Magnetica",
            "combo": "Fabrica Ragnarok",
        },
        "passives": {
            "plasma_aoe": {
                "title": "Plasma Estendido",
                "short": "PLA",
                "category": "Distância",
                "description": "Aumenta o raio da explosão dos tiros.",
            },
            "supercharge": {
                "title": "Sobrecarga de Energia",
                "short": "SOB",
                "category": "Distância",
                "description": "Tiros de plasma têm chance de dar curto-circuito.",
            },
            "heavy_alloy": {
                "title": "Liga Pesada",
                "short": "LIG",
                "category": "Corpo a corpo",
                "description": "Aumenta dano e empurrão da Chave.",
            },
            "magnetic_pull": {
                "title": "Atração Magnética",
                "short": "MAG",
                "category": "Corpo a corpo",
                "description": "Aumenta a força de atração ao golpear.",
            },
            "reinforced_turrets": {
                "title": "Aço Estrutural",
                "short": "ACO",
                "category": "Especial",
                "description": "Torretas duram mais e atiram mais rápido.",
            },
            "shocking_barrier": {
                "title": "Cerca Elétrica",
                "short": "CER",
                "category": "Especial",
                "description": "Barreiras causam mais dano ao colidir.",
            },
            "robotic_necromancy": {
                "title": "Necromancia Robotica",
                "short": "NEC",
                "category": "Ambas",
                "description": "Abates podem converter inimigos em aliados roboticos temporarios. Exige progressao para ser destravada.",
            },
            "overclock": {
                "title": "Overclock",
                "short": "OVR",
                "category": "Ambas",
                "description": "Acelera as recargas passivas de tudo.",
            },
            "structural_shield": {
                "title": "Escudo de Campo",
                "short": "ESC",
                "category": "Defesa",
                "description": "Perto de construções ganha escudo.",
            },
            "core_meltdown": {
                "title": "Fusão do Núcleo",
                "short": "FUS",
                "category": "Ultimate",
                "description": "Ragnarok incendeia o chão deixando plasma.",
            },
        }
    },
    "reaper": {
        "name": "A Ceifadora",
        "color": "#0B0B0F",
        "core_color": "#DC2626",
        "shape": "circle_diamond",
        "weapon_1": "Lamentos",
        "weapon_2": "Foice Carmesim",
        "special": "Rosario de Dor",
        "specials": {
            "weapon_1": "Rosario de Dor",
            "weapon_2": "Colheita Rubra",
            "combo": "Noite da Degola",
        },
        "passives": {
            "blood_mark": {
                "title": "Marca de Sangue",
                "short": "MDS",
                "category": "Distancia",
                "description": "Lamentos marcam alvos e ampliam a janela de execucao da Foice.",
            },
            "mourning_pierce": {
                "title": "Costura Funebre",
                "short": "COS",
                "category": "Distancia",
                "description": "Agulhas ganham perfuracao e causam mais dano contra alvos marcados.",
            },
            "funeral_volley": {
                "title": "Rajada Velada",
                "short": "RAJ",
                "category": "Distancia",
                "description": "Aumenta a quantidade de agulhas por salva e prolonga as marcas.",
            },
            "funeral_chain": {
                "title": "Corrente Funebre",
                "short": "COR",
                "category": "Distancia",
                "description": "Abates em alvos marcados espalham a maldicao para inimigos proximos.",
            },
            "reaping_arc": {
                "title": "Arco Ceifador",
                "short": "ARC",
                "category": "Corpo a corpo",
                "description": "A Foice ganha arco e alcance, facilitando colher grupos inteiros.",
            },
            "hemorrhage": {
                "title": "Hemorragia Ritual",
                "short": "HEM",
                "category": "Corpo a corpo",
                "description": "Golpes da Foice aplicam sangramento escalavel.",
            },
            "soul_tithe": {
                "title": "Dizimo de Almas",
                "short": "DIZ",
                "category": "Corpo a corpo",
                "description": "Consumir marcas no melee gera carga adicional de especial.",
            },
            "harvest_heal": {
                "title": "Colheita Vital",
                "short": "COL",
                "category": "Ambas",
                "description": "Abates em alvos marcados curam a Ceifadora.",
            },
            "scarlet_reload": {
                "title": "Pacto Escarlate",
                "short": "PAC",
                "category": "Ambas",
                "description": "Abates marcados devolvem municao direto ao pente.",
            },
            "red_eclipse": {
                "title": "Eclipse Rubro",
                "short": "ECL",
                "category": "Especial",
                "description": "Fortalece Rosario, Colheita e a ultimate com area e dano extras.",
            },
        }
    }
}

QUEST_DEFINITIONS = [
    {
        "id": "kill_fast",
        "description": "Mate 50 inimigos em 30s",
        "goal_type": "kill_count",
        "target": 50,
        "time_limit": 30.0,
    },
    {
        "id": "melee_only",
        "description": "Sobreviva 60s so com arma corpo-a-corpo",
        "goal_type": "survive_melee",
        "target": 60.0,
        "time_limit": 60.0,
    },
    {
        "id": "stand_fire",
        "description": "Fique 15s dentro de area de fogo",
        "goal_type": "stand_fire",
        "target": 15.0,
        "time_limit": 90.0,
    },
    {
        "id": "kill_brutes",
        "description": "Abata 5 Brutos",
        "goal_type": "kill_brutes",
        "target": 5,
        "time_limit": 90.0,
    },
    {
        "id": "survive_no_dash",
        "description": "Sobreviva 45s sem usar dash",
        "goal_type": "survive_no_dash",
        "target": 45.0,
        "time_limit": 45.0,
    },
]

RELIC_DEFINITIONS = {
    "blade_relay+chrono_boots+guardian_plate+magnet_orb": {
        "name": "Reliquia do Cacador Eterno",
        "short": "Sem Tempestade",
        "description": "Magnetismo, agilidade, defesa e lamina fundidos.",
    },
    "blade_relay+chrono_boots+guardian_plate+storm_core": {
        "name": "Reliquia da Vontade de Ferro",
        "short": "Sem Ima",
        "description": "Tempestade, defesa, crono e lamina em harmonia.",
    },
    "blade_relay+chrono_boots+magnet_orb+storm_core": {
        "name": "Reliquia da Velocidade Caotica",
        "short": "Sem Defesa",
        "description": "Raios, magnetismo, velocidade e laminas em frenesi.",
    },
    "blade_relay+guardian_plate+magnet_orb+storm_core": {
        "name": "Reliquia do Colossus Estatico",
        "short": "Sem Crono",
        "description": "Raios, magnetismo, defesa e laminas como fortaleza.",
    },
    "chrono_boots+guardian_plate+magnet_orb+storm_core": {
        "name": "Reliquia do Tempo Absoluto",
        "short": "Sem Lamina",
        "description": "Raios, magnetismo, defesa e crono. O tempo e seu.",
    },
}

PAUSE_OPTIONS = [
    ("Continuar", "resume"),
    ("Inventario", "inventory"),
    ("Gerenciamento de Skills", "skills"),
    ("Progressao", "progression"),
    ("Construcoes", "constructions"),
    ("Enciclopedia", "encyclopedia"),
    ("Comandos", "commands"),
    ("Configuracoes", "settings"),
    ("Mudar Modo de Jogo", "change_character"),
    ("Reiniciar", "restart"),
    ("Voltar ao Menu", "menu"),
    ("Fechar", "quit"),
]


START_OPTIONS = [
    ("Iniciar Jogo", "character_select"),
    ("Records", "records"),
    ("Loja de moedas", "coin_shop"),
    ("Enciclopedia", "encyclopedia"),
    ("Comandos", "commands"),
    ("Configuracoes", "settings"),
    ("Voltar ao Menu", "menu"),
]


CONTROL_ACTIONS = [
    ("move_up", "Mover para cima"),
    ("move_down", "Mover para baixo"),
    ("move_left", "Mover para esquerda"),
    ("move_right", "Mover para direita"),
    ("dash", "Dash"),
    ("special", "Especial"),
    ("combo_special", "Ultimate"),
    ("omni_active", "Omni-Kernel"),
    ("toggle_weapon", "Alternar arma"),
    ("inventory", "Inventario"),
    ("skills", "Skills"),
    ("pause", "Pausar"),
    ("settings", "Configuracoes"),
    ("fullscreen", "Tela cheia"),
    ("place_light", "Implantar Tocha"),
]


BINDING_SLOT_COUNT = 3


DEFAULT_BINDINGS = {
    "move_up": [("key", pygame.K_w), ("key", pygame.K_UP), None],
    "move_down": [("key", pygame.K_s), ("key", pygame.K_DOWN), None],
    "move_left": [("key", pygame.K_a), ("key", pygame.K_LEFT), None],
    "move_right": [("key", pygame.K_d), ("key", pygame.K_RIGHT), None],
    "dash": [("key", pygame.K_SPACE), None, None],
    "special": [("key", pygame.K_e), None, None],
    "combo_special": [("key", pygame.K_r), None, None],
    "omni_active": [("key", pygame.K_h), None, None],
    "toggle_weapon": [("key", pygame.K_q), ("key", pygame.K_LSHIFT), None],
    "inventory": [("key", pygame.K_i), ("key", pygame.K_TAB), None],
    "skills": [("key", pygame.K_k), None, None],
    "pause": [("key", pygame.K_ESCAPE), None, None],
    "settings": [("key", pygame.K_o), None, None],
    "fullscreen": [("key", pygame.K_F11), None, None],
    "place_light": [("key", pygame.K_f), None, None],
}


JOYSTICK_DEFAULT_BINDINGS = {
    "move_up": ("joy_axis", 1, -1),
    "move_down": ("joy_axis", 1, 1),
    "move_left": ("joy_axis", 0, -1),
    "move_right": ("joy_axis", 0, 1),
    "dash": ("joy_button", 0),
    "special": ("joy_button", 2),
    "combo_special": ("joy_button", 3),
    "omni_active": ("joy_button", 10),
    "toggle_weapon": ("joy_button", 1),
    "inventory": ("joy_button", 6),
    "skills": ("joy_button", 5),
    "pause": ("joy_button", 7),
    "place_light": ("joy_button", 8),
}


JOYSTICK_DEADZONE = 0.55
JOYSTICK_AIM_DEADZONE = 0.28
JOYSTICK_AIM_DISTANCE = 230


if __package__:
    from ..config.config_loader import apply_overrides, load_balance, load_settings
else:
    from Sobrevivencia.config.config_loader import apply_overrides, load_balance, load_settings

apply_overrides(globals(), load_settings(), {"SCREEN_WIDTH", "SCREEN_HEIGHT", "FPS"})
apply_overrides(globals(), load_balance())
