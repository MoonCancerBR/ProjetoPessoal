"""
buff_applicator.py
==================
Centraliza toda a lógica de injeção de buffs de itens no objeto Player.

Responsabilidades:
  - Recalcular os bônus derivados dos itens equipados em um Player.
  - Fornecer a fórmula de escala de nível de item (nível 1-10).
  - Ser chamado sempre que o inventário ativo muda (equip/desequip/upgrade).

FILOSOFIA DE DESIGN
-------------------
Os atributos base do Player (speed_bonus, damage_bonus, etc.) são a soma de:
  1. Bônus ganhos via upgrades de level-up e Loja de Status  →  persistentes
  2. Bônus injetados pelos itens equipados                   →  recalculados sempre

Para separar essas duas fontes sem quebrar o sistema existente, mantemos dois
conjuntos de campos no Player:
  - `*_bonus`        → fonte 1 (persistente, acumulado por upgrades)
  - `item_*_bonus`   → fonte 2 (volátil, sobrescrito a cada recalc)

As funções de dano/velocidade do Player somam ambos internamente.

FÓRMULA DE ESCALA DE NÍVEL (nível 1 → 10)
------------------------------------------
  scale(level) = 1.0 + (level - 1) * ITEM_SCALE_PER_LEVEL

Cada item tem uma contribuição base ao level 1, e cresce linearmente.
Hybrids têm um multiplicador extra; Relics têm um ainda maior.

Mapa de contribuições por item (valores ADITIVOS por nível de efeito):
  chrono_boots   → +1.5% velocidade   / nível ativo
  blade_relay    → +1.2% cadência     / nível ativo   |  +1.8% alcance espada
  storm_core     → +1.0% dano ranged  / nível ativo   (o timer/dano do proc é separado)
  guardian_plate → -2.2% dano recebido quando HP <= 42%  / nível ativo
  magnet_orb     → +9px raio de atração / nível ativo

Esses valores já existiam espalhados pelo código. Este módulo centraliza e injeta
no Player via campos `item_*_bonus` para que o HUD possa exibir os totais corretos.
"""

from __future__ import annotations
from typing import TYPE_CHECKING

try:
    from ..equipment_fusion_effects import apply_passive_hooks
except ImportError:
    from Sobrevivencia.core.equipment_fusion_effects import apply_passive_hooks

if TYPE_CHECKING:
    from ..entities import Player
    from ...data.items import Inventory

# ---------------------------------------------------------------------------
# Escala de nível de item
# ---------------------------------------------------------------------------

ITEM_SCALE_PER_LEVEL = 0.18   # +18% de eficácia por nível adicional (nível 2 = 1.18x, nível 10 = 2.62x)
HYBRID_RANK_BONUS   = 0.20   # Hybrids têm +20% sobre o valor calculado
RELIC_RANK_BONUS    = 0.45   # Relics têm +45% sobre o valor calculado


def item_power_scale(level: int, rank: int) -> float:
    """
    Retorna o multiplicador de potência para um item de ``level`` e ``rank`` dados.

    - Rank 1 (base):   escala linear simples.
    - Rank 2 (hybrid): bônus adicional de 20%.
    - Rank 3 (relic):  bônus adicional de 45%.

    Exemplos (rank 1):
      level 1  → 1.00×
      level 5  → 1.72×
      level 10 → 2.62×
    """
    base = 1.0 + (level - 1) * ITEM_SCALE_PER_LEVEL
    if rank == 2:
        base *= (1.0 + HYBRID_RANK_BONUS)
    elif rank == 3:
        base *= (1.0 + RELIC_RANK_BONUS)
    return base


# ---------------------------------------------------------------------------
# Contribuições base por nível de efeito (por nível do somatório active_effect_level)
# ---------------------------------------------------------------------------
# Esses valores são multiplicados por item_power_scale de cada item individualmente
# e depois somados quando há múltiplos itens com o mesmo efeito.

EFFECT_CONTRIBUTIONS = {
    # chrono_boots: velocidade +1.5% / nível, cooldown dash -2.5% / nível
    "chrono_speed_per_level":       0.015,
    "chrono_dash_reduction_per_level": 0.025,

    # blade_relay: cadência +1.2% / nível, alcance espada +1.8% / nível, dano espada +1.2% / nível
    "blade_rate_per_level":         0.012,
    "blade_range_per_level":        0.018,
    "blade_damage_per_level":       0.012,

    # storm_core: dano ranged +1.0% / nível
    "storm_damage_per_level":       0.010,

    # guardian_plate: redução de dano recebido +2.2% / nível (quando HP <= 42%)
    "guardian_dmg_reduction_per_level": 0.022,

    # magnet_orb: raio de atração +9px / nível  (tratado separadamente em drop_magnet_radius)
}


# ---------------------------------------------------------------------------
# Injeção de buffs no Player
# ---------------------------------------------------------------------------

def recalc_item_buffs(player: "Player", inventory: "Inventory") -> None:
    """
    Recalcula e injeta no ``player`` todos os bônus provenientes dos itens
    atualmente equipados (active_slots) do ``inventory``.

    Deve ser chamado sempre que:
      - Um item é equipado ou desequipado (toggle_active).
      - Um item tem seu nível alterado (upgrade_with_point, add_item level_up).
      - O inventário é carregado do zero.

    Esta função SOBRESCREVE apenas os campos `item_*_bonus` do Player,
    preservando os bônus acumulados por upgrades de level-up (`*_bonus`).
    """
    # Zera todos os bônus de itens antes de recalcular
    player.item_speed_bonus      = 0.0
    player.item_damage_bonus     = 0.0
    player.item_attack_rate_bonus = 0.0
    player.item_sword_range_bonus = 0.0
    player.item_guardian_reduction = 0.0   # guardada separada; usada em _damage_player_direct
    player.item_magnet_bonus      = 0.0

    active = inventory.active_items()

    for item in active:
        scale = item_power_scale(item.level, item.rank)
        keys  = item.effect_keys()

        # --- chrono_boots: velocidade e dash ---
        if "chrono_boots" in keys:
            # Contribuição escalonada: nível base multiplicado pela escala de poder
            player.item_speed_bonus += EFFECT_CONTRIBUTIONS["chrono_speed_per_level"] * item.level * scale

        # --- blade_relay: cadência e alcance da espada ---
        if "blade_relay" in keys:
            player.item_attack_rate_bonus += EFFECT_CONTRIBUTIONS["blade_rate_per_level"]  * item.level * scale
            player.item_sword_range_bonus += EFFECT_CONTRIBUTIONS["blade_range_per_level"] * item.level * scale

        # --- storm_core: dano ranged ---
        if "storm_core" in keys:
            player.item_damage_bonus += EFFECT_CONTRIBUTIONS["storm_damage_per_level"] * item.level * scale

        # --- guardian_plate: redução de dano (condicional ao HP) ---
        if "guardian_plate" in keys:
            player.item_guardian_reduction += EFFECT_CONTRIBUTIONS["guardian_dmg_reduction_per_level"] * item.level * scale

        # --- Bônus de Hybrid: sinergia geral ---
        if item.is_hybrid:
            # Hybrids dão pequeno bônus de dano e rate universais além de seus efeitos base
            apply_passive_hooks(player, item, scale)

        # --- Bônus de Relic: sinergia maior ---
        if item.is_relic:
            # Relics amplificam ainda mais os bônus universais
            player.item_damage_bonus      += 0.015 * item.level * scale
            player.item_attack_rate_bonus += 0.012 * item.level * scale
            player.item_speed_bonus       += 0.010 * item.level * scale

    # --- Bônus de Sinergias de Tags (2+ ativos com mesma tag) ---
    active_syns = inventory.get_active_synergies()
    for syn in active_syns:
        if syn == "elemental":
            player.item_damage_bonus += 0.10
        elif syn == "defensiva":
            player.item_guardian_reduction += 0.08
        elif syn == "utilitaria":
            player.item_magnet_bonus += 40.0
        elif syn == "cinetica":
            player.item_speed_bonus += 0.12
        elif syn == "ofensiva":
            player.item_attack_rate_bonus += 0.15


def ensure_item_bonus_fields(player: "Player") -> None:
    """
    Garante que os campos `item_*_bonus` existem no Player.
    Deve ser chamado em Player.__post_init__ ou na inicialização do GameLogic.
    """
    if not hasattr(player, "item_speed_bonus"):
        player.item_speed_bonus       = 0.0
    if not hasattr(player, "item_damage_bonus"):
        player.item_damage_bonus      = 0.0
    if not hasattr(player, "item_attack_rate_bonus"):
        player.item_attack_rate_bonus = 0.0
    if not hasattr(player, "item_sword_range_bonus"):
        player.item_sword_range_bonus = 0.0
    if not hasattr(player, "item_guardian_reduction"):
        player.item_guardian_reduction = 0.0
    if not hasattr(player, "item_magnet_bonus"):
        player.item_magnet_bonus      = 0.0
