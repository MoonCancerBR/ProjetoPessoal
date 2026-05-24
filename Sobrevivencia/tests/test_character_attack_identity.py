import sys
from pathlib import Path

from pygame.math import Vector2

PACKAGE_PARENT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PACKAGE_PARENT))


def _spawn_dummy_enemy(game, offset_x=150):
    from Sobrevivencia.core.entities import Enemy

    enemy = Enemy(
        id=999,
        pos=Vector2(game.player.pos.x + offset_x, game.player.pos.y),
        kind="dummy",
        radius=16,
        speed=0,
        max_health=250,
        health=250,
        damage=0,
        xp_value=0,
        color="#FFFFFF",
        special_value=0,
        coin_chance=0,
    )
    game.enemies.append(enemy)
    return enemy


def test_vanguard_primary_is_a_short_range_shotgun_salvo():
    from Sobrevivencia.core.game_logic import GameLogic
    from Sobrevivencia.data.constants import PROJECTILE_LIFE

    game = GameLogic("vanguard")
    player = game.player
    ammo_before = player.ammo_magazine

    game._auto_attack_for(0.016, player.pos + Vector2(120, 0), player)

    assert player.ammo_magazine == ammo_before - 1
    assert len(game.projectiles) == 3
    assert all(projectile.style == "vanguard_pellet" for projectile in game.projectiles)
    assert all(projectile.color == "#EF4444" for projectile in game.projectiles)
    assert all(projectile.life < PROJECTILE_LIFE for projectile in game.projectiles)


def test_huntress_primary_fires_a_three_round_burst_for_one_ammo():
    from Sobrevivencia.core.game_logic import GameLogic
    from Sobrevivencia.data.constants import PROJECTILE_LIFE, PROJECTILE_SPEED

    game = GameLogic("huntress")
    player = game.player
    ammo_before = player.ammo_magazine

    game._auto_attack_for(0.016, player.pos + Vector2(180, 0), player)

    assert player.ammo_magazine == ammo_before - 1
    assert len(game.projectiles) == 3
    assert all(projectile.style == "huntress_burst" for projectile in game.projectiles)
    assert all(projectile.life > PROJECTILE_LIFE for projectile in game.projectiles)
    assert all(projectile.vel.length() > PROJECTILE_SPEED for projectile in game.projectiles)


def test_engineer_primary_uses_blue_laser_without_spawning_projectiles():
    from Sobrevivencia.core.game_logic import GameLogic

    game = GameLogic("engineer")
    player = game.player
    enemy = _spawn_dummy_enemy(game, offset_x=140)
    ammo_before = player.ammo_magazine

    game._auto_attack_for(0.016, player.pos + Vector2(220, 0), player)

    assert player.ammo_magazine == ammo_before - 1
    assert game.projectiles == []
    assert any(event.get("type") == "laser" and event.get("color") == "#38BDF8" for event in game.item_events)
    assert enemy.health < enemy.max_health


def test_reaper_primary_marks_targets_with_dark_needles():
    from Sobrevivencia.core.game_logic import GameLogic

    game = GameLogic("reaper")
    player = game.player
    enemy = _spawn_dummy_enemy(game, offset_x=70)
    ammo_before = player.ammo_magazine

    game._auto_attack_for(0.016, player.pos + Vector2(180, 0), player)

    assert player.ammo_magazine == ammo_before - 1
    assert len(game.projectiles) == 2
    assert all(projectile.style == "reaper_needle" for projectile in game.projectiles)

    for _ in range(8):
        game._update_projectiles(0.02)

    assert enemy.health < enemy.max_health
    assert enemy.blood_mark_timer > 0
    assert enemy.blood_mark_level >= 1


def test_each_character_has_a_distinct_melee_profile():
    from Sobrevivencia.core.game_logic import GameLogic

    vanguard = GameLogic("vanguard")
    vanguard.player.mode = "weapon_2"
    vanguard._auto_attack_for(0.016, vanguard.player.pos + Vector2(80, 0), vanguard.player)

    huntress = GameLogic("huntress")
    huntress.player.mode = "weapon_2"
    huntress._auto_attack_for(0.016, huntress.player.pos + Vector2(80, 0), huntress.player)

    engineer = GameLogic("engineer")
    engineer.player.mode = "weapon_2"
    engineer._auto_attack_for(0.016, engineer.player.pos + Vector2(80, 0), engineer.player)

    reaper = GameLogic("reaper")
    reaper.player.mode = "weapon_2"
    reaper._auto_attack_for(0.016, reaper.player.pos + Vector2(80, 0), reaper.player)

    assert len(vanguard.slashes) == 1
    assert vanguard.slashes[0].style == "vanguard_cleave"
    assert vanguard.slashes[0].knockback >= 430

    assert len(huntress.slashes) == 2
    assert all(slash.style == "huntress_combo" for slash in huntress.slashes)

    assert len(engineer.slashes) == 1
    assert engineer.slashes[0].style == "engineer_wrench"
    assert engineer.slashes[0].pull_strength > 0

    assert len(reaper.slashes) == 1
    assert reaper.slashes[0].style == "reaper_scythe"
    assert reaper.slashes[0].consume_mark is True


def test_reaper_specials_create_blood_zone_and_frenzy():
    from Sobrevivencia.core.game_logic import GameLogic

    game = GameLogic("reaper")
    player = game.player

    game._cast_reaper_rosary(player.pos + Vector2(120, 0), player=player)
    assert any(event.get("type") == "blood_zone" for event in game.item_events)

    game.item_events.clear()
    _spawn_dummy_enemy(game, offset_x=60)
    game._cast_reaper_ultimate(player.pos + Vector2(40, 0), player)

    assert player.buffs.get("reaper_frenzy", 0) > 0
    assert any(event.get("type") == "blood_zone" for event in game.item_events)
