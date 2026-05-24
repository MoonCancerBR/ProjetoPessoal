# data/

Camada de **dados estáticos** — fonte única de verdade para constantes numéricas, definições de itens e lógica de inventário/fusão.

## Arquivos

| Arquivo | Função |
|---|---|
| `constants.py` | Todas as constantes do jogo: `FPS`, `SCREEN_SIZE`, `CHARACTERS` (Vanguarda/Caçadora), `ENEMY_TYPES`, `TERRAIN_TYPES`, `UPGRADES_COMMON`, `UPGRADES_OMNI`, `RELIC_DEFINITIONS`, cores, fórmulas de XP, parâmetros do Game Director e taxas de drop. |
| `constants_backup.py` | Snapshot de segurança gerado antes de grandes refatorações. Não é importado em produção. |
| `items.py` | `ITEM_DEFINITIONS` (5 itens base), classe `Inventory` (slots ativos + reserva), lógica de upgrade por rank, `preview_fusion` e `confirm_fusion` (Híbrido/Relíquia), pool de ofertas da Loja de Status. |
| `__init__.py` | Exporta os símbolos do pacote. |

## Dependências Internas

- Consumido por `core.game_logic` (leitura de parâmetros) e `presentation.ui` (nomes/ícones para exibição).
- Futuro: `config/balance.json` poderá sobrescrever valores de `constants.py` na inicialização.
