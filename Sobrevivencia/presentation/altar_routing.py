def handle_altar_menu_transition(
    game,
    state,
    inventory_tab,
    inventory_selected,
    skill_selected,
    stat_shop_selected,
    skills_return_state,
    stat_shop_return_state,
    special_holding,
    special_hold_triggered,
    special_combo_checked,
    combo_holding,
    combo_hold_triggered,
):
    if getattr(game, "active_altar", None) is None or getattr(game, "menu_just_opened_by_altar", None) is None:
        return state, inventory_tab, inventory_selected, skill_selected, stat_shop_selected, skills_return_state, stat_shop_return_state

    kind = game.menu_just_opened_by_altar
    game.menu_just_opened_by_altar = None
    menu_player = getattr(game, "menu_player_index", 0)
    for player_index in (0, 1):
        special_holding[player_index] = False
        special_hold_triggered[player_index] = False
        special_combo_checked[player_index] = False
        combo_holding[player_index] = False
        combo_hold_triggered[player_index] = False

    if kind == "weapon_altar":
        state = "inventory"
        inventory_tab = "items"
        inventory_selected = min(inventory_selected, max(0, len(game.get_inventory(menu_player).item_list()) - 1))
    elif kind == "stamps_altar":
        state = "inventory"
        inventory_tab = "stamps"
        player = game.get_player(menu_player)
        stamp_count = len(player.weapon_stamps.get("weapon_1", [])) + len(player.weapon_stamps.get("weapon_2", [])) + len(player.stamp_reserve)
        inventory_selected = min(inventory_selected, max(0, stamp_count - 1))
    elif kind == "black_market_altar":
        state = "inventory"
        inventory_tab = "shop"
        inventory_selected = 0
    elif kind == "skill_altar":
        skills_return_state = "playing"
        state = "skills"
        skill_selected = min(skill_selected, max(0, len(game.get_player(menu_player).passives) - 1))
    elif kind == "stat_altar":
        stat_shop_return_state = "playing"
        state = "stat_shop"
        stat_shop_selected = 0

    return state, inventory_tab, inventory_selected, skill_selected, stat_shop_selected, skills_return_state, stat_shop_return_state
