# presentation/

Camada de **renderização** — toda a interface visual do jogo (Pygame). Não executa lógica de gameplay.

## Arquivos

| Arquivo | Função |
|---|---|
| `ui.py` | Classe `UI`: renderiza HUD (vida, XP, especiais, pente, dash, buffs, itens, passivas, missão, painel de status), menu principal, seleção de personagem, pause, level up (draft P1/P2), inventário, Gerenciamento de Skills, Loja de Status, Construções, confirmação de fusão, Comandos, Configurações, Game Over e fullscreen via smoothscale. |
| `__init__.py` | Exporta os símbolos do pacote. |

## Dependências Internas

- Importa `data.constants` (nomes, cores, ícones) e `data.items` (descrições de itens).
- Recebe objetos de estado de `core.game_logic` (Player, Enemy, Inventory) — apenas leitura.
