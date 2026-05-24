# Inimigos

Pasta dona de tudo que decide como inimigos nascem, escalam, se movem, atacam
e sao renderizados.

## Estrutura alvo

- `normais/`: inimigos comuns como errante, corredor, bruto, atirador, sapper,
  golem, necromancer e variantes de terreno/noite.
- `elites/miniboss/`: Colosso Errante, arena, pulos, lasers, invocacao e reward.
- `elites/arauto/`: Arauto do Fim, invocacoes, pressao e portal.
- `elites/ceifador/`: Ceifador da Margem, aura, blink, dash e doom.
- `elites/god/`: GOD/Olimpo e habilidades finais.
- `scaling.py`: regras de dificuldade baseadas em tempo, nivel e poder real do
  jogador.

Durante a migracao, `core/managers/enemy_manager.py` continua sendo a fachada
usada por `GameLogic`, delegando partes cada vez menores para este pacote.

