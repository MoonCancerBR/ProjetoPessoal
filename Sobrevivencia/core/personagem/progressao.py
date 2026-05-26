from pygame.math import Vector2

if __package__:
    from ...data.constants import *
    from ...data.items import RELIC_DEFINITIONS, item_display_name
    from ...data.stamps import Stamp
    from ..managers.buff_applicator import ensure_item_bonus_fields, recalc_item_buffs
else:
    from Sobrevivencia.data.constants import *
    from Sobrevivencia.data.items import RELIC_DEFINITIONS, item_display_name
    from Sobrevivencia.data.stamps import Stamp
    from Sobrevivencia.core.managers.buff_applicator import ensure_item_bonus_fields, recalc_item_buffs


def grant_random_item(game, player_index=0):
    inv = game.get_inventory(player_index)
    player = game.get_player(player_index)
    if game.random.random() < 0.005:
        relic_source_key = game.random.choice(list(RELIC_DEFINITIONS.keys()))
        result, item = inv.add_relic(relic_source_key)
        if item is not None and result in ("new", "level_up"):
            name = item_display_name(item)
            game.message = f"RELIQUIA LENDARIA encontrada: {name}!"
            game.screen_shake = max(game.screen_shake, 14.0)
            ensure_item_bonus_fields(player)
            recalc_item_buffs(player, inv)
            return
    result, item = inv.add_random_item(game.random)
    if item is None:
        inv.points += 1
        game.message = "Sem itens disponiveis. +1 ponto de item."
        return
    name = item_display_name(item)
    if result == "new":
        game.message = f"Novo item: {name}."
        game.add_alert(player.pos, f"ITEM: {name}", "#38BDF8")
    elif result == "level_up":
        game.message = f"{name} subiu para o nivel {item.level}."
        game.add_alert(player.pos, f"UP: {name} Nv{item.level}", "#A78BFA")
    else:
        inv.points += 1
        game.message = f"{name} ja esta no maximo. +1 ponto de item."
        game.add_alert(player.pos, f"MAX: +1 ponto", "#64748B")
    ensure_item_bonus_fields(player)
    recalc_item_buffs(player, inv)


def add_xp(game, amount, player=None):
    if player is None:
        player = game.player
    if game.multiplayer:
        game.shared_xp += amount
        for p in game.players:
            p.score += int(amount * 3)
        while game.shared_xp >= game.shared_xp_to_next:
            game.shared_xp -= game.shared_xp_to_next
            game.shared_level += 1
            for p in game.players:
                p.level = game.shared_level
                game._apply_level_up_stats(p)
            for inv in game.inventories:
                inv.points += 1
            game.shared_xp_to_next = int(40 + 25 * game.shared_level)
            game.level_up_pending = True
            major = game.shared_level % 3 == 0
            game.upgrade_is_major = major
            if major:
                for inv in game.inventories:
                    inv.points += 2
                for p in game.players:
                    if not p.is_down:
                        game.spawn_drop("item_box", p.pos + game.random_offset(120), 1)
                game.level_up_player_index = 0
                game.draft_active = False
                game.upgrade_choices = game.generate_upgrade_choices(True, game.level_up_player_index)
            else:
                game.draft_active = True
                game.draft_turn_player = game.draft_first_picker
                if len(game.players) > 1 and game.players[game.draft_turn_player].is_down:
                    other_player = 1 - game.draft_turn_player
                    if not game.players[other_player].is_down:
                        game.draft_turn_player = other_player
                game.level_up_player_index = game.draft_turn_player
                game.upgrade_choices = game.generate_upgrade_choices(False, game.draft_turn_player)
                game.draft_first_picker = 1 - game.draft_first_picker
            game.message = "DRAFT: escolha um upgrade!" if game.draft_active else "Evolucao de Classe!"
            break
        return
    pi = player.player_index
    inv = game.get_inventory(pi)
    player.xp += amount
    player.score += int(amount * 6)
    while player.xp >= player.xp_to_next:
        player.xp -= player.xp_to_next
        player.level += 1
        game._apply_level_up_stats(player)
        inv.points += 1
        player.xp_to_next = int(40 + 25 * player.level)
        game.level_up_player_index = pi
        game.upgrade_is_major = player.level % 3 == 0
        if game.upgrade_is_major:
            inv.points += 2
            game.spawn_drop("item_box", player.pos + game.random_offset(120), 1)
        if player.level % 10 == 0:
            game.level_up_pending = True
            game.upgrade_is_major = True
            game.upgrade_choices = game.generate_singleplayer_milestone_choices(pi)
            game.message = "Marco de nivel: escolha uma melhoria mista."
        else:
            game.level_up_pending = False
            game.upgrade_is_major = False
            game.upgrade_choices = []
            game.message = f"Nivel {player.level}: atributos aumentaram."
        break


def grant_random_reward(game, pos, strong=False, player_index=0):
    pos = Vector2(pos)
    player = game.get_player(player_index)
    inv = game.get_inventory(player_index)
    rewards = ["item", "coins", "xp", "heal", "shield", "points"]
    if strong:
        rewards.extend(["item", "coins", "points"])
    reward = game.random.choice(rewards)
    if reward == "item":
        grant_random_item(game, player_index)
    elif reward == "coins":
        amount = 10 if strong else 5
        for _ in range(amount):
            game.spawn_drop("coin", pos + game.random_offset(56), 1)
        game.message = "Recompensa: chuva de moedas."
    elif reward == "xp":
        amount = 150 if strong else 55
        add_xp(game, amount, player)
        game.message = "Recompensa: experiencia extra."
    elif reward == "heal":
        amount = player.max_health if strong else 38
        player.health = min(player.max_health, player.health + amount)
        game.add_floater(player.pos, f"+{int(amount)}", COLORS["health"])
        game.message = "Recompensa: cura imediata."
    elif reward == "shield":
        player.activate_shield()
        game.message = "Recompensa: escudo ativado."
    else:
        amount = 1600 if strong else 420
        player.score += amount
        inv.points += 2 if strong else 1
        game.message = "Recompensa: pontos e carga de itens."


def grant_miniboss_reward(game, pos, killer_index=0):
    game.miniboss_kills = getattr(game, "miniboss_kills", 0) + 1
    game.miniboss_arena_center = None
    game.miniboss_trapped_player = None
    killer = game.get_player(killer_index)
    inv = game.get_inventory(killer_index)
    killer.health = killer.max_health
    killer.ammo_reserve += 80
    killer.score += 5200 + int(game.time_alive * 35)
    inv.points += 3
    grant_bonus_levels(game, 3, killer_index)
    if game.miniboss_kills >= 3:
        game.grant_chalice_fragment("miniboss_3", killer.pos)
    game.spawn_drop("portal", Vector2(pos), 1)
    for _ in range(14):
        game.spawn_drop("coin", Vector2(pos) + game.random_offset(88), 1)
    grant_random_reward(game, pos, strong=True, player_index=killer_index)
    game.message = "Mini-boss derrotado: Altar de Portal Ativo!"


def grant_bonus_levels(game, amount, player_index=0):
    if game.multiplayer:
        major = False
        for _ in range(amount):
            game.shared_level += 1
            for p in game.players:
                p.level = game.shared_level
                game._apply_level_up_stats(p)
            for inv in game.inventories:
                inv.points += 1
            if game.shared_level % 3 == 0:
                major = True
                for inv in game.inventories:
                    inv.points += 2
                for p in game.players:
                    if not p.is_down:
                        game.spawn_drop("item_box", p.pos + game.random_offset(130), 1)
        game.shared_xp = 0
        game.shared_xp_to_next = int(40 + 25 * game.shared_level)
        game.level_up_pending = True
        game.upgrade_is_major = major
        if major:
            game.level_up_player_index = 0
            game.draft_active = False
            game.upgrade_choices = game.generate_upgrade_choices(True, 0)
        else:
            game.draft_active = True
            game.draft_turn_player = game.draft_first_picker
            if len(game.players) > 1 and game.players[game.draft_turn_player].is_down:
                other_player = 1 - game.draft_turn_player
                if not game.players[other_player].is_down:
                    game.draft_turn_player = other_player
            game.level_up_player_index = game.draft_turn_player
            game.upgrade_choices = game.generate_upgrade_choices(False, game.draft_turn_player)
            game.draft_first_picker = 1 - game.draft_first_picker
        return
    player = game.get_player(player_index)
    inv = game.get_inventory(player_index)
    major = False
    for _ in range(amount):
        player.level += 1
        game._apply_level_up_stats(player)
        inv.points += 1
        if player.level % 3 == 0:
            major = True
            inv.points += 2
            game.spawn_drop("item_box", player.pos + game.random_offset(130), 1)
    player.xp = 0
    player.xp_to_next = int(40 + 25 * player.level)
    game.level_up_pending = True
    game.level_up_player_index = player_index
    game.upgrade_is_major = major
    game.upgrade_choices = game.generate_upgrade_choices(major, player_index)
