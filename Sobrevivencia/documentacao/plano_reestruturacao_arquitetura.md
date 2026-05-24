# Plano de Reestruturacao Arquitetural

Objetivo: reduzir arquivos gigantes, melhorar rastreabilidade de bugs e separar
responsabilidades por dominio sem alterar o funcionamento do jogo.

## Principios

- Migracao incremental: cada etapa deve compilar e passar no smoke test.
- Fachadas temporarias: `GameLogic`, `UI` e os managers atuais continuam como
  ponto de entrada enquanto delegam para pacotes menores.
- Um dominio por pasta: inimigos, personagens, missoes, altares, Omni-Kernel,
  mundo, drops, equipamentos, selos, mecanicas, HUD e multiplayer.
- Sem mudanca de regra junto com movimentacao de codigo, exceto quando a tarefa
  pedir balanceamento explicitamente.

## Estrutura alvo

```text
core/
  inimigos/
    normais/
      errante/
      corredor/
      bruto/
      atirador_acido/
      sapper/
      golem/
      necromancer/
      sombra/
    elites/
      god/
      miniboss/
      arauto/
      ceifador/
    scaling.py
    spawning.py
  personagem/
    vanguarda/
      arma/
      skills_passivas/
      especiais/
    cacadora/
      arma/
      skills_passivas/
      especiais/
    engenheiro/
      arma/
      skills_passivas/
      especiais/
    ceifadora/
      arma/
      skills_passivas/
      especiais/
    atributos.py
  missoes/
    escolta/
    objetivos_rapidos/
    progresso_calice/
  altares/
    armas/
    skills/
    status/
    selos/
    mercado_negro/
  omni_kernel/
    progresso/
    item/
    ativa/
    passiva/
  mundo/
    principal/
    bolso/
    olimpo/
    terrenos/
    dia_noite/
  drops/
    xp/
    moeda/
    municao/
    cura/
    escudo/
    item_box/
    portal/
    calice/
  equipamentos/
    tier_1/
    tier_2/
    tier_3/
    hibridos/
    reliquias/
  selos/
    inventario/
    fusao/
    efeitos/
  mecanicas/
    reacoes_elementares/
    sinergia_itens/
    fisica/
    combate_base/
  hud_status/
    hud/
    menus_tempo_real/
    atributos/
  multiplayer/
    revive/
    camera/
    tether/
    draft/
```

## Fases

1. Criar pacotes de destino e READMEs de ownership.
2. Extrair regras puras e sem estado primeiro: scaling, pesos de spawn,
   formulas de atributos, custos, descricoes e tabelas.
3. Separar inimigos: primeiro scaling/spawn, depois AI normal, depois cada elite.
4. Separar personagem: armas primarias/melee por classe, especiais e passivas.
5. Separar progressao: missoes, calice e Omni-Kernel.
6. Separar inventario: equipamentos, tiers, hibridos, reliquias, selos e fusoes.
7. Separar apresentacao: render de inimigos/personagens/mundo/drops em pacotes
   espelhando os dominios.
8. Reduzir fachadas finais: `GameLogic`, `CombatManager`, `EnemyManager`,
   `ItemManager`, `UI` e `main.py` devem ficar como orquestradores curtos.

## Ordem recomendada para os maiores arquivos

- `core/managers/enemy_manager.py`: extrair `inimigos/scaling.py`, depois
  `spawning.py`, `normais/ai.py`, e arquivos por elite.
- `core/managers/combat_manager.py`: extrair armas e especiais por personagem.
- `core/game_logic.py`: extrair estado inicial, movimento, camera, mundo,
  Omni-Kernel e Calice.
- `main.py`: separar estados/telas em controladores de fluxo menores.
- `presentation/menus/hud.py`: separar HUD de combate, cooldowns, buffs,
  rastreador do Calice e multiplayer.

## Regra de validacao por etapa

Rodar pelo menos:

```powershell
python -m py_compile core\managers\enemy_manager.py core\inimigos\scaling.py
python -m Sobrevivencia.tools.smoke_test
```
