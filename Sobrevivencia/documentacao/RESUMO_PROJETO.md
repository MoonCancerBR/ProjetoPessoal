# RESUMO TÉCNICO DO PROJETO "Sobrevivência"

> Guia rápido para desenvolvedores – rastreabilidade das responsabilidades, funções essenciais e fluxo de interação entre os módulos.

---

## 1. Raiz do Projeto

### Mapeamento de Arquivos
- **main.py** – Loop principal, captura de input (teclado/joystick), orquestra a *state machine* (menu → jogo → pause → game‑over) e instancia os componentes de `core`, `presentation` e `config`.
- **gdd_sobrevivencia.md** – Documento de design (não faz parte da execução).
- **__init__.py** – Marca o diretório como pacote Python.

### Detalhamento de Funções
- `main()` : inicia o jogo, carrega configuração (`data.constants`), cria instâncias de `GameLogic` e `UI`, executa o laço `while running`.
- `handle_events()` : delega eventos de teclado/joystick a `GameLogic.process_input` e a `UI.handle_event`.
- `run()` : controla a taxa de *ticks* (FPS) e chama `GameLogic.update(dt)` e `UI.render()`.

### Arquitetura de Interação
`main.py` importa **core.game_logic**, **presentation.ui** e **data.constants**.  Nenhum outro módulo importa `main.py` – ele é o ponto de entrada.

### Lógica de Gameplay
Todo o comportamento de jogabilidade (movimento, dash, troca de arma, spawn, IA, drops, missões, nível‑up) está encapsulado em `core.game_logic.GameLogic` e suas dependências (`core.entities`, `core.world`, `data.items`).

---

## 2. Diretório `core/`

### Mapeamento de Arquivos
- **game_logic.py** – Motor de gameplay (classe `GameLogic`).
- **entities.py** – Dataclasses puras: `Player`, `Enemy`, `Projectile`, `Slash`, `Drop`, `Hazard`, `Destructible`.
- **world.py** – Geração procedural de chunks, verificação de colisão terreno/obstáculos, definição de hazards.
- **__init__.py** – Exporta os símbolos principais.

### Detalhamento de Funções
- `GameLogic.__init__(self, config)` : carrega constantes, cria `Player`, inicializa `World`, `Inventory` e registra handlers de UI.
- `GameLogic.process_input(event)` : traduz eventos em ações de movimento, dash, troca de arma, disparo, especial.
- `GameLogic.update(dt)` :
  - `self.update_players(dt)` – movimentação, recarga, cooldowns.
  - `self.update_enemies(dt)` – IA básica (perseguir, fugir, atacar).
  - `self.handle_spawns(dt)` – cronômetro para `Enemy`/`Hazard`.
  - `self.resolve_collisions()` – detecção e aplicação de dano / pickups.
  - `self.check_level_up()` – cálculo de XP, geração de draft de upgrade.
- `Entity` dataclasses – apenas armazenam estado (posição, velocidade, vida, atributos).  Não têm lógica própria.
- `World.generate_chunk(x, y)` – cria terreno, posiciona obstáculos, itens e hazards.
- `World.check_collision(entity, terrain)` – utilitário usado por `GameLogic`.

### Arquitetura de Interação
- `GameLogic` importa **core.entities**, **core.world**, **data.constants** e **data.items**.
- `World` usa **data.constants.TERRAIN_TYPES** para escolher tiles.
- `entities` são consumidos por `GameLogic` (ex.: `Player` recebe input; `Enemy` recebe IA).
- `presentation.ui` recebe apenas os objetos de estado (`Player`, lista de `Enemy`, `Inventory`) para renderizar.

### Lógica de Gameplay
- Mecânicas de **Tactical Swap** (arma de longo alcance ↔ melee) são implementadas em `GameLogic._swap_weapon()` e na recarga automática (`_auto_reload`).
- Sistema de **XP / Level‑up** e **draft** está em `GameLogic.check_level_up()`.
- **Drops** (munição, moedas, curas, etc.) são gerados em `World.spawn_drop()` e consumidos em `GameLogic.handle_pickup()`.
- **Missões temporárias** são verificadas em `GameLogic.update_missions(dt)` (não listada aqui, mas parte do arquivo).

---

## 3. Diretório `data/`

### Mapeamento de Arquivos
- **constants.py** – Dicionários e valores globais: `FPS`, `SCREEN_SIZE`, `CHARACTERS`, `ENEMY_TYPES`, `TERRAIN_TYPES`, `ITEM_DEFINITIONS`, `RELIC_DEFINITIONS`, etc.
- **constants_backup.py** – Snapshot de segurança da versão anterior de `constants.py` (não importado em produção).
- **items.py** – Implementação da classe `Inventory`, lógica de *fusion* (`preview_fusion`, `confirm_fusion`) e definição de itens passivos.
- **__init__.py** – Re‑exporta `constants` e `items`.

### Detalhamento de Funções
- `load_constants()` : (opcional) pode ler `config/balance.json` para sobrescrever valores em tempo de execução.
- `Inventory.add_item(item_id)`, `Inventory.upgrade(item_id)`, `Inventory.use(item_id)` – gerenciam slots ativos, reserva e pontos de item.
- `preview_fusion(item_a, item_b)` – valida se dois itens de mesmo rank/nível podem ser fundidos.
- `confirm_fusion(item_a, item_b)` – consome os itens e cria híbrido ou relíquia conforme `RELIC_DEFINITIONS`.

### Arquitetura de Interação
- `core.game_logic` importa `data.constants` para ler parâmetros de balance e `data.items.Inventory` para manipular o inventário do jogador.
- `presentation.ui` consulta `data.constants` apenas para nomes e ícones (por ex., ao desenhar a barra de passivas).
- `tools.balance_editor.py` (futuro) lerá `config/balance.json` e sobrescreverá valores em `constants.py`.

### Lógica de Gameplay
- Todas as **estatísticas de personagens, inimigos e itens** são centralizadas aqui, facilitando ajuste sem tocar código.
- O **sistema de fusão** e **pontos de item** residem em `items.py` e são invocados por `GameLogic` quando o jogador marca fusão (`F` no inventário).

---

## 4. Diretório `presentation/`

### Mapeamento de Arquivos
- **ui.py** – Classe `UI` responsável por renderizar HUD, menus, telas de pause, level‑up draft, inventário, skills, loja de status, construções, etc.
- **__init__.py** – Exporta `UI`.

### Detalhamento de Funções
- `UI.__init__(self, screen, assets)` : carrega fontes, imagens e cria surfaces.
- `UI.handle_event(event)` : captura cliques/teclas de navegação de UI (ex.: seleção de upgrade, confirmação de fusão).
- `UI.render(state)` : desenha a cena atual (menu, gameplay, pause) usando os objetos de estado recebidos (`player`, `enemies`, `inventory`).
- Sub‑métodos como `draw_hud()`, `draw_menu()`, `draw_inventory()` organizam a camada visual.

### Arquitetura de Interação
- `main.py` cria a instância `ui = UI(screen, assets)` e a passa a `GameLogic` somente para eventos de UI.
- `GameLogic` devolve ao `UI` apenas dados de estado (listas de entidades, textos de mensagem).  Não há dependência inversa.

### Lógica de Gameplay
- A UI **não contém lógica de jogo**; apenas exibe o resultado das decisões tomadas por `GameLogic`.
- Elementos interativos (ex.: draft de level‑up) enviam eventos que `GameLogic.process_input` interpreta e aplica.

---

## 5. Diretório `assets/`

### Mapeamento de Arquivos
- **items/** – Ícones PNG 32×32 para cada item/passiva.
- **sprites/** – (futuro) Sprite sheets de personagens, inimigos, efeitos.
- **sfx/** – (futuro) Efeitos sonoros `.ogg`/`.wav` (tiro, dash, pickup, fusão, recarga).
- **bgm/** – (futuro) Trilha(s) musical(is) de fundo.
- **fonts/** – (futuro) Fontes `.ttf` usadas pelo `UI`.

### Detalhamento de Funções
- Não há código executável; os recursos são carregados por `presentation.ui` via `pygame.image.load` e `pygame.mixer.Sound`.

### Arquitetura de Interação
- `UI` solicita imagens/sons por caminho relativo ao diretório `assets/`.
- `GameLogic` não acessa diretamente assets – apenas referencia nomes de sprites quando cria `Entity` (ex.: `player.sprite = "sprites/player.png"`).

### Lógica de Gameplay
- Os **ícones** são exibidos no HUD e no inventário; **sfx** serão disparados nos pontos críticos (tiro, recarga, fusão) quando o código de `GameLogic` chamar `UI.play_sound(name)`.

---

## 6. Diretório `config/`

### Mapeamento de Arquivos
- **settings.json** – Resolução, fullscreen, volume, idioma.
- **balance.json** – Valores de balance (HP, dano, velocidade, taxas de drop) que podem sobrescrever `data.constants`.
- **keybinds.json** – Mapeamento de teclas e botões de gamepad.
- **config_loader.py** - Loader JSON resiliente para settings, balance e keybinds.
- **runtime.py** - Fallbacks para dependencias opcionais e logging.

> Os arquivos JSON ja existem fisicamente e sao carregados com fallback seguro.

### Detalhamento de Funções
- `config_loader.load_json_config(filename)` retorna dicionario ou fallback vazio quando o JSON esta ausente/invalido.
- `config_loader.apply_overrides(globals, overrides)` aplica apenas chaves existentes e tipos compativeis.
- `runtime.optional_import(name)` carrega bibliotecas externas sem quebrar o import do jogo.
- `runtime.configure_file_logging()` usa `loguru` quando disponivel e `logging` nativo como fallback.
- `data.constants` aplica `settings.json` (`SCREEN_WIDTH`, `SCREEN_HEIGHT`, `FPS`) e `balance.json` na inicializacao.
- `input.input_manager` aplica `keybinds.json` preservando defaults quando uma entrada e invalida.

### Arquitetura de Interação
- `main.py` chama `load_settings()` para fullscreen inicial antes do loop.
- `data.constants` chama `config_loader` para settings/balance.
- `input.input_manager` chama `config_loader` para keybinds.
- `core.world`, `core.game_logic` e `presentation` usam `runtime` para dependencias opcionais.

### Lógica de Gameplay
- As **configurações externas** permitem mudar resolução, volume e keybinds sem tocar no código Python, facilitando testes de performance e acessibilidade.

---

## 7. Diretório `tools/`

### Mapeamento de Arquivos
- **profiler.py** – Script de profiling (cProfile) para medir FPS, tempo de update/render e identificar gargalos.
- **balance_editor.py** – Interface (CLI/GUI) para editar `balance.json` e gerar snapshots de `constants_backup.py`.
- **config_check.py** - Valida JSONs, keybinds e disponibilidade das dependencias recomendadas/opcionais.
- **smoke_test.py** - Inicializa o jogo em modo headless por alguns segundos e fecha por evento `QUIT`.

### Detalhamento de Funções
- `profiler.py --mode core|ui` roda cenarios controlados e salva `tools/profiler_report*.txt`.
- `balance_editor.py list|get|set` atualiza `config/balance.json` e pode gerar `balance.json.bak`.
- `config_check.py` deve ser usado antes de builds/testes para confirmar configuracao carregavel.
- `smoke_test.py` valida o loop principal sem abrir janela real.

### Arquitetura de Interação
- Ferramentas são *stand‑alone*; não são importadas pelo jogo.
- `balance_editor` altera apenas `config/balance.json`; os overrides sao aplicados no proximo import de `data.constants`.

### Lógica de Gameplay
- Não interferem na gameplay; servem ao desenvolvedor para otimização e balanceamento.

---

## 8. Diretório `documentacao/`

### Mapeamento de Arquivos
- **estrutura_projeto.mmd** – Diagrama Mermaid da árvore de diretórios (visualização completa).
- **gdd_sobrevivencia.md** – Documentação de design (cópia canônica).
- **RESUMO_PROJETO.md** – **Este** guia técnico criado para rastreabilidade rápida.

---

# Como usar este resumo
1. **Encontrar lógica** – Consulte a seção do diretório correspondente e procure o arquivo‑classe‑função listada.
2. **Rastrear fluxo** – Observe a “Arquitetura de Interação” para entender quem importa quem.
3. **Estender** – Quando precisar adicionar nova mecânica, siga o padrão:
   - Defina consts em `data/constants`.
   - Crie/edite dataclasses em `core/entities` se for novo tipo de objeto.
   - Implemente comportamento em `core/game_logic`.
   - Atualize UI em `presentation/ui`.
   - Opcional: adicione assets e configuração.

---

*Este documento será mantido sincronizado com o diagrama `estrutura_projeto.mmd` e o GDD.  Qualquer mudança estrutural deve atualizar ambas as referências.*
