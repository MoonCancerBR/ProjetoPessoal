if __package__:
    from ..data.constants import *
    from ..data.items import BASE_ITEM_KEYS
else:
    from Sobrevivencia.data.constants import *
    from Sobrevivencia.data.items import BASE_ITEM_KEYS


def render_state(
    app,
    ui,
    game,
    state,
    mouse_pos,
    aim_pos,
    aim_mode,
    p2_aim_screen,
    dt,
    controls,
    selections,
    fullscreen,
    capture_binding,
    inventory_tab,
):
    if state == "playing":
        ui.render_game(game, aim_pos, dt=dt, flip=False, aim_from_joystick=aim_mode == "joystick", p2_aim_pos=p2_aim_screen)
        return [], selections, inventory_tab

    if state == "start":
        return ui.render_start(mouse_pos, selections["start"]), selections, inventory_tab
    if state == "mode_select":
        return ui.render_mode_select(mouse_pos, selections["mode"], app._joystick_count()), selections, inventory_tab
    if state == "character_select":
        selected_index = selections["character_2"] if selections["multiplayer"] and selections["character_player"] == 1 else selections["character"]
        char_class = list(CHARACTERS.keys())[selected_index]
        char_class_2 = list(CHARACTERS.keys())[selections["character_2"]]
        return ui.render_character_select(char_class, mouse_pos, selections["multiplayer"], char_class_2, selections["character_player"]), selections, inventory_tab
    if state == "paused":
        return ui.render_pause(game, PAUSE_OPTIONS, selections["pause"], mouse_pos), selections, inventory_tab
    if state == "commands":
        return ui.render_commands(mouse_pos, app._command_lines(controls)), selections, inventory_tab
    if state == "progression":
        return ui.render_progression(game, mouse_pos), selections, inventory_tab
    if state == "settings":
        selections["settings"] = min(selections["settings"], len(CONTROL_ACTIONS) - 1)
        return ui.render_settings(app._control_rows(controls), selections["settings"], selections["settings_slot"], capture_binding, fullscreen, app.control_preference, app._joystick_count(), mouse_pos), selections, inventory_tab
    if state == "encyclopedia":
        entries = ui.filtered_encyclopedia_entries(selections["encyclopedia_category"], selections["encyclopedia_query"])
        selections["encyclopedia"] = min(selections["encyclopedia"], max(0, len(entries) - 1))
        return ui.render_encyclopedia(selections["encyclopedia"], mouse_pos, selections["encyclopedia_category"], selections["encyclopedia_query"]), selections, inventory_tab
    if state == "stat_shop":
        return ui.render_stat_shop(game, selections["stat_shop"], mouse_pos), selections, inventory_tab
    if state == "constructions":
        selections["construction"] = min(selections["construction"], max(0, len(ui.construction_catalog()) - 1))
        return ui.render_constructions(game, selections["construction"], mouse_pos), selections, inventory_tab
    if state == "skills":
        selections["skill"] = min(selections["skill"], max(0, len(game.get_player(game.menu_player_index).passives) - 1))
        return ui.render_skills(game, selections["skill"], mouse_pos), selections, inventory_tab
    if state == "upgrade":
        return ui.render_upgrade(game, selections["upgrade"], mouse_pos), selections, inventory_tab
    if state == "inventory":
        inv = game.get_inventory(game.menu_player_index)
        if inventory_tab == "shop":
            selections["inventory"] = min(selections["inventory"], max(0, len(list(BASE_ITEM_KEYS)) - 1))
        elif inventory_tab == "stamps":
            player = game.get_player(game.menu_player_index)
            stamp_count = len(player.weapon_stamps.get("weapon_1", [])) + len(player.weapon_stamps.get("weapon_2", [])) + len(player.stamp_reserve)
            selections["inventory"] = min(selections["inventory"], max(0, stamp_count - 1))
        else:
            selections["inventory"] = min(selections["inventory"], max(0, len(inv.item_list()) - 1))
        return ui.render_inventory_gui(game, selections["inventory"], mouse_pos, inventory_tab), selections, inventory_tab
    if state == "fusion_confirm":
        selections["inventory"] = min(selections["inventory"], max(0, len(game.get_inventory(game.menu_player_index).item_list()) - 1))
        return ui.render_fusion_confirm(game, selections["inventory"], selections["fusion_confirm"], mouse_pos), selections, inventory_tab
    if state == "stamp_fusion_confirm":
        player = game.get_player(game.menu_player_index)
        stamp_count = len(player.weapon_stamps.get("weapon_1", [])) + len(player.weapon_stamps.get("weapon_2", [])) + len(player.stamp_reserve)
        selections["inventory"] = min(selections["inventory"], max(0, stamp_count - 1))
        return ui.render_stamp_fusion_confirm(game, selections["inventory"], selections["fusion_confirm"], mouse_pos), selections, inventory_tab
    if state == "point_confirm":
        _render_point_background(app, ui, game, selections, mouse_pos, inventory_tab)
        app._refresh_point_confirm_quantity(game)
        return ui.render_point_confirm(game, app.point_confirm_cost, app.point_confirm_msg, app.point_confirm_selected, mouse_pos, app.point_confirm_quantity, app.point_confirm_max_quantity, app.point_confirm_total_cost), selections, inventory_tab
    if state == "rng_result":
        _render_point_background(app, ui, game, selections, mouse_pos, inventory_tab)
        return ui.render_rng_result(game, mouse_pos), selections, inventory_tab
    if state == "game_over":
        return ui.render_game_over(game, mouse_pos, selections["game_over"]), selections, inventory_tab
    return [], selections, inventory_tab


def _render_point_background(app, ui, game, selections, mouse_pos, inventory_tab):
    if app.point_confirm_return == "stat_shop":
        ui.render_stat_shop(game, selections["stat_shop"], mouse_pos)
    elif app.point_confirm_return == "skills":
        ui.render_skills(game, selections["skill"], mouse_pos)
    elif app.point_confirm_return == "inventory":
        ui.render_inventory_gui(game, selections["inventory"], mouse_pos, inventory_tab)
