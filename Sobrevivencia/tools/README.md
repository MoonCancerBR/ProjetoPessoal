# tools/

Scripts de **desenvolvimento e performance** — não são importados pelo jogo em produção.

## Arquivos

| Arquivo | Função |
|---|---|
| `profiler.py` | Análise de performance com `cProfile`: mede update do core e update/render da UI em modo headless. |
| `balance_editor.py` | Editor CLI para ajustar `config/balance.json`, com validação contra `data.constants` e backup opcional. |
| `config_check.py` | Valida JSONs de config, keybinds e disponibilidade das dependências recomendadas/opcionais. |
| `smoke_test.py` | Inicializa o jogo por alguns segundos em modo headless e fecha via evento `QUIT`. |
| `__init__.py` | Marca o diretório como pacote Python. |

## Dependências Internas

- Ferramentas são **stand-alone**: não são importadas por nenhum módulo do jogo.
- `balance_editor.py` lê e escreve em `config/balance.json` e pode gerar `balance.json.bak`.
- `profiler.py` executa cenários controlados e salva relatório de performance em `tools/profiler_report.txt`.

## Como Executar

```bash
python -m Sobrevivencia.tools.smoke_test
python -m Sobrevivencia.tools.config_check
python -m Sobrevivencia.tools.profiler --mode core --seconds 8
python -m Sobrevivencia.tools.profiler --mode ui --seconds 5
python -m Sobrevivencia.tools.balance_editor list
python -m Sobrevivencia.tools.balance_editor get PLAYER_BASE_SPEED
python -m Sobrevivencia.tools.balance_editor set PLAYER_BASE_SPEED 245.0 --backup
```
