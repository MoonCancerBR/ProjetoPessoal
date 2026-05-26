from pygame.math import Vector2
import pygame


def scaled_mouse_pos(final_screen, virtual_screen):
    raw_mouse_pos = pygame.mouse.get_pos()
    fw, fh = final_screen.get_size()
    vw, vh = virtual_screen.get_size()
    if fw != vw or fh != vh:
        return (int(raw_mouse_pos[0] * vw / fw), int(raw_mouse_pos[1] * vh / fh))
    return raw_mouse_pos


def scaled_event_pos(event_pos, final_screen, virtual_screen):
    fw, fh = final_screen.get_size()
    vw, vh = virtual_screen.get_size()
    if fw != vw or fh != vh:
        return (int(event_pos[0] * vw / fw), int(event_pos[1] * vh / fh))
    return event_pos


def update_aim_state(app, game, ui, mouse_pos, joystick_aim_dir, aim_mode):
    joystick_aim = app._joystick_aim_vector()
    if joystick_aim.length_squared() > 0:
        joystick_aim_dir = joystick_aim.normalize()
        aim_mode = "joystick"

    aim_pos = app._aim_screen_pos(game, joystick_aim_dir) if aim_mode == "joystick" and not game.multiplayer else mouse_pos
    aim_world = ui.screen_to_world(aim_pos, game.camera)
    p2_aim_screen = None
    p2_aim_world = None
    if game.multiplayer and game.player2 is not None:
        p2_aim_screen = app._aim_screen_pos_for(game, game.player2, joystick_aim_dir)
        p2_aim_world = ui.screen_to_world(p2_aim_screen, game.camera)
    return joystick_aim_dir, aim_mode, aim_pos, aim_world, p2_aim_screen, p2_aim_world


def present_virtual_screen(virtual_screen):
    final_screen = pygame.display.get_surface()
    fw, fh = final_screen.get_size()
    vw, vh = virtual_screen.get_size()
    if fw != vw or fh != vh:
        pygame.transform.smoothscale(virtual_screen, (fw, fh), final_screen)
    else:
        final_screen.blit(virtual_screen, (0, 0))
    pygame.display.flip()
