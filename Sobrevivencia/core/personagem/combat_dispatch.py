def cast_weapon_special(game, channel, aim_world, player=None):
    if player is None:
        player = game.player
    if player.char_class == "vanguard":
        if channel == "ranged":
            game._cast_vanguard_radial(player=player)
        else:
            game._cast_vanguard_charge(aim_world, player=player)
    elif player.char_class == "reaper":
        if channel == "ranged":
            game._cast_reaper_rosary(aim_world, player=player)
        else:
            game._cast_reaper_harvest(aim_world, player=player)
    elif player.char_class == "engineer":
        if channel == "ranged":
            game._cast_engineer_turret_grid(aim_world, player=player)
        else:
            game._cast_engineer_magnetic_implosion(aim_world, player=player)
    else:
        if channel == "ranged":
            game._cast_huntress_arrow_rain(aim_world, player=player)
        else:
            game._cast_huntress_dagger_dance(player=player)


def cast_ultimate(game, aim_world, player=None):
    if player is None:
        player = game.player
    if player.char_class == "vanguard":
        game._cast_vanguard_ultimate(aim_world, player)
    elif player.char_class == "reaper":
        game._cast_reaper_ultimate(aim_world, player)
    elif player.char_class == "engineer":
        game._cast_engineer_ultimate(aim_world, player)
    else:
        game._cast_huntress_ultimate(aim_world, player)
    game.screen_shake = max(game.screen_shake, 18.0)


def auto_attack_for(game, dt, aim_world, player):
    direction = aim_world - player.pos
    if direction.length_squared() < 0.01:
        direction.update(1, 0)
    direction = direction.normalize()
    inv = game.get_inventory(player.player_index)

    if player.mode == "weapon_1":
        if player.char_class == "vanguard":
            game._fire_vanguard_primary(player, direction, inv)
        elif player.char_class == "reaper":
            game._fire_reaper_primary(player, direction, inv)
        elif player.char_class == "engineer":
            game._fire_engineer_primary(player, direction, inv)
        else:
            game._fire_huntress_primary(player, direction, inv)
    else:
        if player.char_class == "vanguard":
            game._swing_vanguard_melee(player, direction, inv)
        elif player.char_class == "reaper":
            game._swing_reaper_melee(player, direction, inv)
        elif player.char_class == "engineer":
            game._swing_engineer_melee(player, direction, inv)
        else:
            game._swing_huntress_melee(player, direction, inv)
