# Sobrevivência

Jogo de ação top-down survival / bullet heaven tático, desenvolvido em **Python + Pygame**.

## Arquivos na Raiz

| Arquivo | Função |
|---|---|
| `main.py` | Loop principal, captura de input (teclado/mouse/joystick) e state machine (menu → seleção → gameplay → pause → game over). |
| `__init__.py` | Marca o diretório como pacote Python importável. |

## Estrutura de Diretórios

| Pasta | Responsabilidade |
|---|---|
| `core/` | Motor do jogo — lógica pura de gameplay, entidades e mundo. |
| `data/` | Dados estáticos — constantes numéricas, definições de itens e fusões. |
| `presentation/` | Renderização — HUD, menus e telas (depende de Pygame). |
| `assets/` | Recursos visuais e sonoros (imagens, sons, fontes). |
| `config/` | Configurações externas em JSON (resolução, balance, keybinds). |
| `tools/` | Scripts de desenvolvimento (profiling, editor de balance). |
| `documentacao/` | Documentação técnica: GDD canônico, diagrama Mermaid, resumo do projeto. |

## Como Executar

```bash
python -m Sobrevivencia.main
```

## Instalação e Requisitos de Sistema

O projeto é modular e foi arquitetado para rodar com o **mínimo possível de dependências obrigatórias**, garantindo excelente compatibilidade multiplataforma (Windows e Linux). As bibliotecas são organizadas em perfis:

### 1. Perfil Mínimo (Apenas Execução Básica)
Para rodar o jogo em sua forma mais simples e leve, é necessária apenas uma biblioteca:
* **`pygame-ce` (>= 2.5)**: A edição comunitária do Pygame (*Pygame Community Edition*), que gerencia a janela, captura inputs (teclado, mouse, joystick), processa o áudio e realiza a renderização na CPU.
  
> [!IMPORTANT]
> Se você tiver a biblioteca `pygame` clássica instalada, é recomendável desinstalá-la antes (`pip uninstall pygame`) para evitar conflitos de importação com o `pygame-ce`.

Para instalar apenas o necessário para execução:
```bash
python -m pip install -r requirements-minimal.txt
```

### 2. Perfil Completo (Desenvolvimento & Recursos Premium)
Recomendado para a melhor experiência visual, física e sonora. Contém recursos otimizados e interfaces modernas:

| Biblioteca | Tipo | Função / Papel no Jogo | Comportamento Sem Ela (Fallback) |
|---|---|---|---|
| **`pygame_gui`** | Recomendada | Janelas, abas e controles interativos ricos (menus de Inventário e Mercado Negro). | Usa menus manuais legados mais simples. |
| **`pygame-menu`** | Recomendada | Telas de início, pausa, configurações e Game Over polidas e animadas. | Abre um menu nativo textual simples em Pygame. |
| **`pytweening`** | Recomendada | Curvas de interpolação e efeitos de transição suaves (menus e HUD). | Usa interpolação linear ou quadrática nativa direta. |
| **`loguru`** | Recomendada | Sistema de logs robusto, colorido e assíncrono para debugging. | Faz fallback para o módulo `logging` nativo do Python. |
| **`numpy`** | Opcional | Processamento matemático e simulação de partículas vetorizadas. | Utiliza listas padrão do Python (desempenho reduzido). |
| **`pymunk`** | Opcional | Simulador de física 2D robusto para colisões de projéteis e inimigos. | Usa cálculos de colisão simples integrados no módulo `World`. |
| **`pytmx`** | Opcional | Mapeamento de cenários e carregamento de arquivos de mapa Tiled (`.tmx`). | O jogo continua gerando o mundo de forma procedural. |
| **`moderngl`** | Experimental | Aceleração por GPU para renderização avançada e pós-processamento (shaders). | Utiliza o renderizador padrão via CPU do Pygame. |
| **`numba`** | Experimental | Compilação JIT de funções matemáticas intensivas para velocidade de C/C++. | Executa as mesmas funções matemáticas em Python puro. |

Para instalar o perfil completo de desenvolvimento e todos os recursos premium:
```bash
python -m pip install -r requirements.txt
```

## Validação

```bash
python -m Sobrevivencia.tools.config_check
python -m Sobrevivencia.tools.smoke_test
python -m Sobrevivencia.tools.profiler --mode core --seconds 1
```

## Configuração Externa

- `config/settings.json`: resolução, FPS, fullscreen inicial e volumes.
- `config/balance.json`: overrides de constantes de balance.
- `config/keybinds.json`: atalhos iniciais de teclado/mouse.
