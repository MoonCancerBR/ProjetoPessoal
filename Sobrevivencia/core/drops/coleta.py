if __package__:
    from ...data.constants import *
    from ..meta_progress import add_coins
else:
    from Sobrevivencia.data.constants import *
    from Sobrevivencia.core.meta_progress import add_coins


def collect_drop(game, drop, player=None):
    if player is None:
        player = game.player
    if drop.kind == "xp":
        game.add_xp(drop.value, player)
    elif drop.kind == "ammo":
        max_res = game.max_ammo_reserve_for(player)
        if player.ammo_reserve >= max_res:
            if player.full_ammo_msg_timer <= 0:
                game.add_floater(player.pos, "Cheio!", COLORS["muted"])
                player.full_ammo_msg_timer = 2.0
            return False
        amount = int(drop.value)
        added = min(amount, max_res - player.ammo_reserve)
        player.ammo_reserve += added
        game.add_floater(player.pos, f"+{added} mun", COLORS["projectile"])
        if player.ammo_magazine <= 0 and player.reload_timer <= 0:
            game._start_reload_for(player)
    elif drop.kind == "coin":
        if game.multiplayer:
            game.shared_coins += 1
        else:
            player.coins += 1
        game.run_coins_collected = getattr(game, "run_coins_collected", 0) + 1
        add_coins(1)
        player.score += 25
        total_coins = game.shared_coins if game.multiplayer else player.coins
        if total_coins % 5 == 0:
            game.activate_random_coin_buff(player)
    elif drop.kind == "heal":
        player.health = min(player.max_health, player.health + drop.value)
        game.add_floater(player.pos, f"+{int(drop.value)}", COLORS["health"])
    elif drop.kind == "shield":
        player.activate_shield()
        game.message = "Escudo ativo: invulneravel, rapido e repelente."
    elif drop.kind == "item_box":
        game.grant_random_item(player.player_index)
    elif drop.kind == "stamp":
        game.grant_stamp(str(drop.value), player.player_index)
    elif drop.kind == "vacuum":
        game.magnet_timer = 4.0
        game.add_floater(player.pos, "IMA GLOBAL!", "#06B6D4")
        game.message = "Ima Global ativado! Coletando tudo."
    elif drop.kind == "portal":
        game.enter_pocket_dimension()
        if hasattr(game, "_spawn_special_enemy"):
            game._spawn_special_enemy("chromatic", 1.5)
            game._spawn_special_enemy("chromatic", 1.5)
    elif drop.kind == "exit_portal":
        game.exit_pocket_dimension(reward=True)
    elif drop.kind == "chalice":
        game.grant_chalice_fragment(str(drop.value), player.pos)
    return True
