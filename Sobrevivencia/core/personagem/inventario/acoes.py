if __package__:
    from ....data.constants import *
    from ...managers.buff_applicator import ensure_item_bonus_fields, recalc_item_buffs
else:
    from Sobrevivencia.data.constants import *
    from Sobrevivencia.core.managers.buff_applicator import ensure_item_bonus_fields, recalc_item_buffs


def toggle_inventory_item(game, key):
    inv = game.get_inventory(game.menu_player_index)
    success, message = inv.toggle_active(key)
    if success:
        player = game.get_player(game.menu_player_index)
        ensure_item_bonus_fields(player)
        recalc_item_buffs(player, inv)
    game.message = message
    return success


def upgrade_inventory_item(game, key):
    inv = game.get_inventory(game.menu_player_index)
    success, message = inv.upgrade_with_point(key)
    if success:
        player = game.get_player(game.menu_player_index)
        ensure_item_bonus_fields(player)
        recalc_item_buffs(player, inv)
    game.message = message
    return success


def buy_shop_item(game, item_key):
    inv = game.get_inventory(game.menu_player_index)
    cost = 15
    if inv.points < cost:
        game.message = f"Pontos insuficientes para comprar (custa {cost})."
        return False

    inv.points -= cost
    status, item = inv.add_item(item_key)
    game.message = f"Item {item.key} adquirido no Mercado Negro!"
    player = game.get_player(game.menu_player_index)
    ensure_item_bonus_fields(player)
    recalc_item_buffs(player, inv)
    return True


def skill_upgrade_cost(game, key):
    player = game.get_player(game.menu_player_index)
    data = CHARACTERS[player.char_class]["passives"].get(key, {})
    level = player.passives.get(key, 0)
    is_special = data.get("category") == "Especial"
    if level == 0:
        return SPECIAL_SKILL_UNLOCK_COST if is_special else SKILL_UNLOCK_COST
    return SPECIAL_SKILL_UPGRADE_COST if is_special else SKILL_UPGRADE_COST


def upgrade_skill(game, key):
    player = game.get_player(game.menu_player_index)
    inv = game.get_inventory(game.menu_player_index)
    if key not in player.passives:
        game.message = "Skill nao encontrada."
        return False
    unlock_ready, unlock_text = game.passive_unlock_status(key, player)
    if player.passives.get(key, 0) <= 0 and not unlock_ready:
        game.message = unlock_text
        return False
    if player.passives[key] >= 10:
        game.message = "Skill ja esta no nivel maximo."
        return False
    cost = skill_upgrade_cost(game, key)
    if inv.points < cost:
        game.message = f"Pontos insuficientes para upar skill (custa {cost})."
        return False
    inv.points -= cost
    player.passives[key] += 1
    data = CHARACTERS[player.char_class]["passives"][key]
    state = "desbloqueada" if player.passives[key] == 1 else "aprimorada"
    game.message = f"Skill {state}: {data['title']}."
    return True


def mark_or_fuse_item(game, key):
    inv = game.get_inventory(game.menu_player_index)
    success, message = inv.mark_for_fusion(key)
    game.message = message
    return success


def fusion_preview(game):
    inv = game.get_inventory(game.menu_player_index)
    success, preview, message = inv.preview_marked_fusion()
    return success, preview, message


def has_pending_fusion(game):
    success, _, _ = fusion_preview(game)
    return success


def confirm_pending_fusion(game):
    inv = game.get_inventory(game.menu_player_index)
    if inv.points < FUSION_COST:
        game.message = f"Pontos insuficientes para fusao (custa {FUSION_COST})."
        return False
    success, message = inv.fuse_marked_items()
    if success:
        inv.points -= FUSION_COST
        player = game.get_player(game.menu_player_index)
        ensure_item_bonus_fields(player)
        recalc_item_buffs(player, inv)
    game.message = message
    return success


def cancel_pending_fusion(game):
    inv = game.get_inventory(game.menu_player_index)
    inv.clear_fusion_marks()
    game.message = "Fusao cancelada."
