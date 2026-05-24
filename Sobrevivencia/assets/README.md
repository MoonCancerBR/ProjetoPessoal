# assets/

Recursos **visuais e sonoros** do jogo. Não contém código Python executável.

## Subpastas

| Pasta | Conteúdo |
|---|---|
| `items/` | Ícones PNG dos itens passivos (usados no HUD e inventário). |
| `sprites/` | *(planejado)* Sprite sheets de personagens, inimigos e efeitos. |
| `sfx/` | *(planejado)* Efeitos sonoros — tiro, dash, pickup, fusão, recarga, etc. (`.ogg`/`.wav`). |
| `bgm/` | *(planejado)* Trilhas musicais de fundo por fase/bioma (`.ogg` em loop). |
| `fonts/` | *(planejado)* Fontes customizadas `.ttf` usadas pela camada `presentation/`. |

## Convenções

- Imagens de itens: **PNG**, resolução de referência **32×32 px**.
- Sons: formato **OGG** preferido (boa compressão com suporte nativo do Pygame).
- Nomeação: `snake_case` descritivo (ex.: `blade_relay.png`, `shot_fire.ogg`).
