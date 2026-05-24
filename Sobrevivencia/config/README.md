# config/

Pasta para **configurações externas** do jogo — editáveis sem alterar código Python.

## Arquivos

| Arquivo | Função |
|---|---|
| `settings.json` | Resolução, FPS, fullscreen e volumes base. |
| `balance.json` | Overrides de balance carregados por `data/constants.py`. |
| `keybinds.json` | Mapeamento inicial de teclado/mouse para ações do jogo. |
| `config_loader.py` | Loader JSON resiliente e aplicação controlada de overrides. |
| `runtime.py` | Fallbacks para dependências opcionais (`loguru`, `numba`, `pytweening`, UI nula). |
| `__init__.py` | Marca o diretório como pacote Python. |

## Dependências Internas

- `data/constants.py` carrega `SCREEN_WIDTH`, `SCREEN_HEIGHT`, `FPS` e overrides de `balance.json` no import.
- `main.py` usa `settings.json` para definir fullscreen inicial.
- `input/input_manager.py` carrega `keybinds.json` e preserva defaults quando uma entrada é inválida.
- `config/runtime.py` permite que dependências externas sejam opcionais sem quebrar o jogo.

## Como Editar Balance

```bash
python -m Sobrevivencia.tools.balance_editor list
python -m Sobrevivencia.tools.balance_editor set PLAYER_BASE_SPEED 245.0 --backup
python -m Sobrevivencia.tools.config_check
```
