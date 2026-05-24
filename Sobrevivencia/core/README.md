# core/

Motor do jogo — contém **toda a lógica de gameplay** sem dependência direta de Pygame.

## Arquivos

| Arquivo | Função |
|---|---|
| `game_logic.py` | Classe `GameLogic`: movimento, combate, spawns, IA de inimigos, drops, progressão (XP/level up), missões temporárias, Game Director, modo coop (câmera, tether, draft, revive). |
| `entities.py` | Dataclasses puras (`Player`, `Enemy`, `Projectile`, `Slash`, `Drop`, `Hazard`, `Destructible`). Armazenam estado; não contêm lógica de jogo. |
| `world.py` | Classe `World`: geração procedural de chunks (768 px), terrenos, hazards, obstáculos e colisão círculo-retângulo. |
| `__init__.py` | Exporta os símbolos do pacote. |

## Dependências Internas

- Importa `data.constants` (parâmetros de balance) e `data.items` (Inventory, fusões).
- **Não** importa Pygame — toda renderização é feita por `presentation/`.
