# Plano de performance, visual e organizacao

Este plano evolui o projeto sem trocar o motor principal. A regra e manter Python + Pygame como caminho estavel, com bibliotecas opcionais e modulos nativos apenas onde houver gargalo medido.

## Bibliotecas e onde aplicar

| Area | Ferramenta | Uso recomendado | Validacao sem compilar |
|---|---|---|---|
| Personagens e inimigos | `pygame.sprite`, atlas PNG + JSON | Animacoes por estados, cache de frames, flip e tint pre-renderizados | Teste headless carregando atlas e contando frames |
| Interface, janelas e avisos | `pygame_gui`, `pygame-menu` | Inventario, loja, popups, abas, tooltips e telas de sistema | Render dummy com screenshot em `scratch/` |
| Animacoes de skill e feedback | `pytweening`, `numpy` | Curvas de dash, impacto, floating text, particulas vetorizadas | Profiler UI e teste de particulas isolado |
| Ambientacao do mapa | `pytmx`, assets por bioma | Tilesets, decoracoes, layers de colisao e props | Loader TMX com fallback procedural |
| Colisao e fisica | `pymunk` | Corpos estaticos para obstaculos, sensores de pickup e projeteis especiais | Simulacao curta sem abrir janela |
| Sombras e luz | `pygame.Surface` precomputada, opcional `moderngl` | Sombras fake 2D, vinheta, light masks, pos-processamento leve | Comparar FPS com `tools/profiler.py --mode ui` |
| Hot loops matematicos | `numba` ou C++ via modulo nativo | Distancias, broadphase, steering e particulas grandes | Benchmark puro Python vs acelerado |
| Render GPU experimental | `moderngl`, futuramente Vulkan externo | Shaders de tela cheia e efeitos opt-in | Feature flag desligada por padrao |

## C++ e Vulkan com seguranca

1. C++ deve entrar primeiro como biblioteca matematica/fisica pequena, chamada por uma API Python com fallback puro.
2. Vulkan nao deve substituir o render do Pygame agora. O caminho seguro e experimentar shaders com `moderngl`; Vulkan fica para um prototipo isolado em `native_core/docs/` quando houver necessidade real.
3. Nenhuma funcionalidade de gameplay deve depender do modulo nativo para o jogo abrir.
4. Builds nativas ficam fora do fluxo normal: o desenvolvimento diario valida com smoke tests, profiler e loaders headless.

## Tasks pequenas com validacoes

### Fase 1 - Medicao e base visual

- Criar baseline de FPS de core e UI.
  - Validacao: `python -m Sobrevivencia.tools.profiler --mode core --seconds 3`
  - Validacao: `python -m Sobrevivencia.tools.profiler --mode ui --seconds 3 --output tools/profiler_report_ui.txt`
- Adicionar `AssetRegistry` para carregar sprites, fontes, sons e shaders uma vez.
  - Validacao: teste de import e carregamento de assets existentes.
- Padronizar cache de surfaces, fontes e icones.
  - Validacao: profiler UI nao deve piorar o tempo acumulado.

### Fase 2 - Personagens, inimigos e skills

- Criar loader de atlas em `presentation/rendering/`.
  - Validacao: script headless renderiza 1 frame de cada estado em `scratch/`.
- Separar animacoes de skill em `presentation/effects/`.
  - Validacao: teste unitario atualiza efeitos por 2 segundos sem entidades reais.
- Trocar efeitos repetitivos desenhados frame a frame por surfaces pre-renderizadas.
  - Validacao: comparar profiler UI antes/depois.

### Fase 3 - UI, janelas e avisos

- Consolidar popups, confirmacoes e avisos em componentes reutilizaveis.
  - Validacao: screenshots dummy das telas start, pause, inventario, upgrade e confirmacao.
- Mover textos e medidas de UI para tokens/config.
  - Validacao: `config_check` e smoke test.
- Cortar duplicacoes restantes entre `presentation/ui.py` e `presentation/menus/*`.
  - Validacao: `rg` para funcoes antigas e smoke test.

### Fase 4 - Mapa, ambiente e sombra

- Criar camada de decoracao do mapa separada da colisao.
  - Validacao: mundo procedural continua funcionando sem `pytmx`.
- Adicionar sombras fake em `presentation/rendering/shadows.py`.
  - Validacao: flag liga/desliga e profiler UI.
- Adicionar loader TMX opcional.
  - Validacao: quando `pytmx` ausente, cair no mundo procedural sem excecao.

### Fase 5 - Fisica

- Isolar contrato de fisica em `core/physics/`.
  - Validacao: testes rodam com backend simples atual.
- Adicionar backend `pymunk` opt-in para obstaculos e sensores.
  - Validacao: simulacao headless com 100 inimigos e 200 projeteis.
- Medir se `pymunk` melhora ou piora o caso real antes de tornar padrao.
  - Validacao: profiler core e gameplay smoke.

### Fase 6 - Nativo, sem travar o projeto

- Criar API nativa minima para broadphase/distancia, com fallback Python.
  - Validacao: teste compara saida Python vs nativo.
- So compilar quando houver mudanca em `native_core/src` ou `native_core/include`.
  - Validacao cotidiana: imports e testes Python, sem rebuild.
- Prototipar GPU em `moderngl` antes de qualquer Vulkan.
  - Validacao: flag experimental desligada por padrao.

## Criterios de limpeza de codigo morto

- Remover arquivos vazios ou backup sem import.
- Antes de apagar funcao: confirmar com `rg` que nao ha chamada.
- Funcoes antigas de UI devem virar wrappers temporarios ou serem removidas na mesma task que migra a chamada.
- Arquivos acima de 800 linhas entram em fila de extracao, priorizando `main.py`, `presentation/ui.py` e `core/game_logic.py`.
- Relatorios, caches, builds e binarios gerados nao devem entrar em versionamento.

## Ordem sugerida

1. Baseline de profiler.
2. Asset registry e cache visual.
3. Loader de atlas e efeitos.
4. Consolidacao de UI.
5. Sombras e ambientacao.
6. Contrato de fisica.
7. Backend `pymunk`.
8. Micro-aceleracoes com `numba` ou C++.
9. Experimentos GPU opt-in.
