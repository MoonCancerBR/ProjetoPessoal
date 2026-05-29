def apply_passive_hooks(player, item, scale):
    for hook in getattr(_definition(item), "hooks", ()):
        handler = PASSIVE_HOOKS.get(hook)
        if handler:
            handler(player, item, scale)


def generic_hybrid_bonus(player, item, scale):
    player.item_damage_bonus += 0.008 * item.level * scale
    player.item_attack_rate_bonus += 0.008 * item.level * scale


PASSIVE_HOOKS = {
    "generic_hybrid_bonus": generic_hybrid_bonus,
}


def _definition(item):
    try:
        from ..data.equipment_fusions import get_fusion_definition
    except ImportError:
        from Sobrevivencia.data.equipment_fusions import get_fusion_definition
    return get_fusion_definition(item)
