import os
import pygame
pygame.init()
pygame.freetype.init()
pygame.display.set_mode((1100, 720), pygame.HIDDEN)

from Sobrevivencia.presentation.ui import UI
from Sobrevivencia.core.game_logic import GameLogic

game = GameLogic("vanguard", "vanguard", False)
game.player.health = 80
game.player.max_health = 100
game.player.xp = 150
game.player.xp_to_next = 300
game.player.level = 5

game.inventory.get_active_synergies = lambda: ["elemental", "cinetica"]
game.message = "Sinergias elementais em vigor!"

# Mock assets loading
ui = UI(pygame.Surface((1100, 720)))
ui.screen.fill((10, 15, 20)) # Dark bg to see HUD
ui._draw_hud(game)

out_path = r"C:\Users\ferna\.gemini\antigravity\brain\0d16b02f-73a0-45b8-8931-1d8699618636\synergy_hud.png"
pygame.image.save(ui.screen, out_path)
print("Saved to", out_path)
