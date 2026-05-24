"""
data/stamps.py
==============
Define o Sistema de Selos (Stamps) — Modificadores Globais de Armas.

Cada Stamp pode ser equipado em até 3 slots por arma (Distância ou Corpo a Corpo).
Selos funcionais conferem bônus passivos e/ou efeitos de acerto (on-hit).
Selos de Sucata (junk) não têm efeito próprio; existem apenas como material de
Fusão de Sacrifício ou como items vendáveis.
"""

from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Nível máximo de evolução de um Stamp
# ---------------------------------------------------------------------------
MAX_STAMP_LEVEL = 3

# Custo em Pontos de Item ao vender um Stamp por nível
STAMP_SELL_VALUES = {1: 8, 2: 20, 3: 45}

# Valor "junk" — selos de sucata valem menos ao serem vendidos
JUNK_STAMP_SELL_VALUE = 4


# ---------------------------------------------------------------------------
# Dataclass principal
# ---------------------------------------------------------------------------
@dataclass
class Stamp:
    """Representa uma instância de um Selo equipado ou na reserva."""
    key: str
    level: int = 1

    @property
    def is_junk(self):
        return self.key.startswith("junk_")

    @property
    def is_max_level(self):
        return self.level >= MAX_STAMP_LEVEL or self.is_junk


# ---------------------------------------------------------------------------
# Definições completas de todos os selos
# ---------------------------------------------------------------------------
# Estrutura de cada entrada:
#   "key": {
#       "name": str,                       # Nome de exibição
#       "hud_color": str,                  # Cor HEX para os dots no HUD
#       "is_junk": bool,                   # True = sem efeito funcional
#       "description": [str, str, str],    # Descrição por nível (len=3)
#       "effect_values": [v1, v2, v3],     # Valor numérico do efeito por nível
#       "on_equip": bool,                  # Efeito passivo aplicado ao equip?
#       "on_hit": bool,                    # Efeito disparado por acerto?
#   }
# ---------------------------------------------------------------------------
STAMP_DEFINITIONS: dict = {

    # ---------------------------------------------------------- Funcionais --
    "impact": {
        "name": "Selo de Impacto",
        "hud_color": "#EF4444",   # Vermelho
        "is_junk": False,
        "description": [
            "+15% de Dano da Arma",
            "+30% de Dano da Arma",
            "+50% de Dano da Arma",
        ],
        "effect_values": [0.15, 0.30, 0.50],
        "on_equip": True,
        "on_hit": False,
    },

    "haste": {
        "name": "Selo de Rapidez",
        "hud_color": "#F59E0B",   # Amarelo
        "is_junk": False,
        "description": [
            "+10% de Cadência / Velocidade de Ataque",
            "+20% de Cadência / Velocidade de Ataque",
            "+35% de Cadência / Velocidade de Ataque",
        ],
        "effect_values": [0.10, 0.20, 0.35],
        "on_equip": True,
        "on_hit": False,
    },

    "lifesteal": {
        "name": "Selo Vampírico",
        "hud_color": "#8B5CF6",   # Roxo
        "is_junk": False,
        "description": [
            "+1% do dano causado convertido em vida",
            "+2% do dano causado convertido em vida",
            "+3% do dano causado convertido em vida",
        ],
        "effect_values": [0.01, 0.02, 0.03],
        "on_equip": False,
        "on_hit": True,
    },

    "blast": {
        "name": "Selo Explosivo",
        "hud_color": "#F97316",   # Laranja
        "is_junk": False,
        "description": [
            "12% de chance de Explosão em área (30% do dano) no acerto",
            "20% de chance de Explosão em área (30% do dano) no acerto",
            "32% de chance de Explosão em área (30% do dano) no acerto",
        ],
        "effect_values": [0.12, 0.20, 0.32],
        "on_equip": False,
        "on_hit": True,
    },

    "frost": {
        "name": "Selo Congelante",
        "hud_color": "#3B82F6",   # Azul
        "is_junk": False,
        "description": [
            "15% de chance de Lentidão (35% slow) por 3s no acerto",
            "25% de chance de Lentidão (35% slow) por 3s no acerto",
            "40% de chance de Lentidão (35% slow) por 3s no acerto",
        ],
        "effect_values": [0.15, 0.25, 0.40],
        "on_equip": False,
        "on_hit": True,
    },

    "toxic": {
        "name": "Selo Venenoso",
        "hud_color": "#10B981",   # Verde
        "is_junk": False,
        "description": [
            "15% de chance de Veneno (12 DPS) por 4s no acerto",
            "25% de chance de Veneno (12 DPS) por 4s no acerto",
            "40% de chance de Veneno (12 DPS) por 4s no acerto",
        ],
        "effect_values": [0.15, 0.25, 0.40],
        "on_equip": False,
        "on_hit": True,
    },

    "caliber": {
        "name": "Selo de Calibre",
        "hud_color": "#06B6D4",   # Ciano
        "is_junk": False,
        "description": [
            "+25% de Tamanho dos Projéteis",
            "+50% de Tamanho dos Projéteis",
            "+80% de Tamanho dos Projéteis",
        ],
        "effect_values": [0.25, 0.50, 0.80],
        "on_equip": True,
        "on_hit": False,
    },

    "repulse": {
        "name": "Selo de Repulsão",
        "hud_color": "#EC4899",   # Rosa
        "is_junk": False,
        "description": [
            "Knockback leve (velocidade 180) em todo acerto",
            "Knockback médio (velocidade 320) em todo acerto",
            "Knockback forte (velocidade 500) em todo acerto",
        ],
        "effect_values": [180, 320, 500],
        "on_equip": False,
        "on_hit": True,
    },

    # ------------------------------------------------------- Sucata (Junk) --
    "junk_grey": {
        "name": "Fragmento Cinza",
        "hud_color": "#6B7280",   # Cinza
        "is_junk": True,
        "description": [
            "Sem efeito. Material de Fusão ou venda.",
            "Sem efeito. Material de Fusão ou venda.",
            "Sem efeito. Material de Fusão ou venda.",
        ],
        "effect_values": [0, 0, 0],
        "on_equip": False,
        "on_hit": False,
    },

    "junk_rust": {
        "name": "Fragmento Enferrujado",
        "hud_color": "#92400E",   # Marrom
        "is_junk": True,
        "description": [
            "Sem efeito. Material de Fusão ou venda.",
            "Sem efeito. Material de Fusão ou venda.",
            "Sem efeito. Material de Fusão ou venda.",
        ],
        "effect_values": [0, 0, 0],
        "on_equip": False,
        "on_hit": False,
    },

    "junk_cracked": {
        "name": "Fragmento Quebrado",
        "hud_color": "#374151",   # Cinza escuro
        "is_junk": True,
        "description": [
            "Sem efeito. Material de Fusão ou venda.",
            "Sem efeito. Material de Fusão ou venda.",
            "Sem efeito. Material de Fusão ou venda.",
        ],
        "effect_values": [0, 0, 0],
        "on_equip": False,
        "on_hit": False,
    },
}

# Chaves de selos funcionais que podem ser equipados nas armas
FUNCTIONAL_STAMP_KEYS: list[str] = [
    k for k, v in STAMP_DEFINITIONS.items() if not v["is_junk"]
]

# Chaves de selos de sucata
JUNK_STAMP_KEYS: list[str] = [
    k for k, v in STAMP_DEFINITIONS.items() if v["is_junk"]
]

# Todos os selos que podem aparecer como drops (inclui junk, exclui nada)
ALL_DROPPABLE_STAMP_KEYS: list[str] = list(STAMP_DEFINITIONS.keys())


# ---------------------------------------------------------------------------
# Funções auxiliares
# ---------------------------------------------------------------------------

def stamp_display_name(stamp: "Stamp") -> str:
    """Retorna o nome de exibição do Stamp, incluindo o nível."""
    defn = STAMP_DEFINITIONS.get(stamp.key, {})
    base = defn.get("name", stamp.key)
    if defn.get("is_junk"):
        return base
    return f"{base} Nv{stamp.level}"


def stamp_description(stamp: "Stamp") -> str:
    """Retorna a descrição do efeito do Stamp no nível atual."""
    defn = STAMP_DEFINITIONS.get(stamp.key, {})
    descriptions = defn.get("description", ["Sem descrição."])
    idx = max(0, min(stamp.level - 1, len(descriptions) - 1))
    return descriptions[idx]


def stamp_sell_value(stamp: "Stamp") -> int:
    """Retorna os Pontos de Item ganhos ao vender este Stamp."""
    defn = STAMP_DEFINITIONS.get(stamp.key, {})
    if defn.get("is_junk"):
        return JUNK_STAMP_SELL_VALUE
    return STAMP_SELL_VALUES.get(stamp.level, STAMP_SELL_VALUES[1])


def stamp_effect_value(stamp: "Stamp") -> float:
    """Retorna o valor numérico do efeito do Stamp no nível atual."""
    defn = STAMP_DEFINITIONS.get(stamp.key, {})
    values = defn.get("effect_values", [0, 0, 0])
    idx = max(0, min(stamp.level - 1, len(values) - 1))
    return values[idx]


def stamp_hud_color(stamp: "Stamp") -> str:
    """Retorna a cor HEX característica do Stamp para exibição no HUD."""
    defn = STAMP_DEFINITIONS.get(stamp.key, {})
    return defn.get("hud_color", "#6B7280")


def stamps_equipped_for_weapon(player, weapon_key: str) -> list:
    """Retorna a lista de Stamps equipados na arma indicada ('weapon_1' ou 'weapon_2')."""
    return getattr(player, "weapon_stamps", {}).get(weapon_key, [])


def stamp_total_bonus(player, weapon_key: str, effect_key: str) -> float:
    """
    Soma os bônus de todos os Stamps do tipo `effect_key` equipados em `weapon_key`.
    Usado pelos cálculos de dano e cadência no CombatManager.
    """
    total = 0.0
    for stamp in stamps_equipped_for_weapon(player, weapon_key):
        if stamp.key == effect_key:
            total += stamp_effect_value(stamp)
    return total
