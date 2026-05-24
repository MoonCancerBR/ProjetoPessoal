# Game Design Document (GDD): Sobrevivência

**Última atualização:** 18/05/2026 — Altares, RNG, Relógio, Minimapa e Crachás de Selos  
**Plataforma:** PC  
**Tecnologia:** Python + Pygame (Modernizado com `freetype`, `pytweening` e `pygame-gui`)  
**Resolução alvo:** 1100 x 720 px, 60 FPS, com opção de tela cheia escalada  
**Gênero:** Top-down action survival / bullet heaven tático  
**Referências:** Vampire Survivors, Brotato, roguelites de arena com troca de armas

---

## 1. Visão Geral

Sobrevivência é um jogo de ação em arena infinita no qual o jogador enfrenta hordas crescentes de inimigos enquanto monta uma build durante a partida. O jogo combina ataques automáticos, mira com mouse, coleta de recursos, escolhas de upgrade, itens passivos, fusões e eventos temporários.

A mudança central de arsenal é que armas de longa distância não são mais infinitas. Elas usam pente, reserva de munição e recarga. Quando o pente esvazia, o personagem alterna automaticamente para a arma corpo a corpo enquanto recarrega em segundo plano. Isso transforma a troca de armas em parte essencial do ritmo da partida.

### Core Loop

1. Mover pelo mapa infinito e evitar contato, hazards e ataques especiais.
2. Usar a arma de longa distância enquanto houver munição no pente.
3. Ao esvaziar o pente, sobreviver com a arma corpo a corpo durante a recarga.
4. Coletar XP, moedas, munição, curas, escudos e caixas de item.
5. Escolher upgrades comuns, passivas específicas e itens passivos.
6. Fundir itens em híbridos e relíquias.
7. Completar missões, derrotar inimigos especiais e ampliar a build.

---

## 2. Pilares de Design

- **Troca tática:** a arma corpo a corpo deixa de ser reserva emergencial e vira parte obrigatória da rotação.
- **Munição como recurso:** disparar é forte, mas depende de pente, reserva e pickups.
- **Builds com identidade:** cada personagem possui aprimoramentos de distância, melee, híbridos e especial.
- **Legibilidade:** ameaças importantes usam avisos visuais claros.
- **Escalada constante:** tempo, nível e Game Director pressionam o jogador progressivamente.
- **Juice & Feedback:** animações suaves e fontes modernas para uma experiência premium.

---

## 3. Arsenal, Munição e Tactical Swap

### 3.1 Pente e Reserva

- Capacidade base do pente: **20 projéteis**.
- Capacidade aumenta com o nível: `20 + (nível - 1) x 2`.
- Reserva inicial: **60 munições**.
- Disparos consomem munição do pente.
- Ao recarregar, munição é movida da reserva para o pente.
- Se a reserva estiver vazia, o jogador permanece com a arma corpo a corpo até coletar munição.

### 3.2 Recarga Inteligente

A recarga do pente inicia automaticamente sempre que o jogador troca para a arma corpo a corpo, independentemente de o pente estar zerado ou não:

1. Se o jogador trocar manualmente para a espada com munição restante no pente, a recarga começa em segundo plano imediatamente.
2. Quando o pente chega a 0, o jogo alterna automaticamente para a arma corpo a corpo e a recarga começa.
3. Duração base da recarga: **2,15 s**.
4. Ao concluir a recarga, o jogo alterna automaticamente de volta para a arma de longa distância.
5. Se não houver reserva, a arma de longa distância fica indisponível até coletar munição.

### 3.3 Consumo de Munição

- Cada ciclo de disparo consome **1 munição do pente**.
- Multishot e flechas laterais consomem apenas **1 munição**, mesmo gerando vários projéteis.
- Isso incentiva upgrades de área e tiros múltiplos sem punir demais builds focadas em projéteis.

### 3.4 Munição no Mundo

Inimigos derrotados podem derrubar munição:

| Inimigo | Chance | Quantidade |
|---|---:|---:|
| Errante | 18% | 5 a 12 |
| Corredor | 16% | 5 a 12 |
| Bruto | 42% | 10 a 18 |
| Errático Cromático | 70% | 18 a 30 |
| Atirador Ácido | 26% | 5 a 12 |
| Guardião Blindado | 46% | 14 a 24 |
| Demolidor Instável | 22% | 6 a 14 |
| Servo do Colosso | 8% | 2 a 5 |

Mini-boss derrotado concede **+80 munições na reserva** junto das outras recompensas.

---

## 4. Personagens

Cada personagem possui duas armas, dois especiais e dez passivas específicas. As passivas aparecem em upgrades grandes, a cada 3 níveis, mas também podem ser desbloqueadas e aprimoradas manualmente na janela de Gerenciamento de Skills. Cada passiva chega ao nível 10.

### 4.0 Sistema de Especiais e Combo Ultimate

Cada personagem possui **duas barras de especial independentes**: uma para a arma de distância (`ESP DIST`) e uma para a arma corpo a corpo (`ESP MELEE`). Ambas são exibidas no HUD de cada jogador e se carregam por fontes distintas:

| Barra | Fontes de carga |
|---|---|
| **ESP DIST** | Abates com projéteis, veneno, itens ofensivos à distância |
| **ESP MELEE** | Abates com golpes, sangramento, escudo, efeitos de área próxima |

**Uso normal do especial (tecla `E` por padrão):**
- Ativa o especial da **arma atualmente empunhada**.
- Consome apenas a barra correspondente (`ESP DIST` ou `ESP MELEE`).
- Se a barra ainda não estiver cheia, exibe um alerta no HUD informando a carga atual.

**Ativação do Combo Ultimate (segurar `E` por ≈ 1,15 s):**
- Requer **ambas as barras cheias simultaneamente**.
- Ao manter o botão pressionado por `SPECIAL_COMBO_HOLD_SECONDS` (~1,15 s), o jogo chama `try_combo_special()`, que consome **as duas barras ao mesmo tempo** e ativa a ultimate do personagem.
- Gera **tremor de câmera intenso** (`screen_shake = 40–50`) e um efeito de **distorção temporal** (`time_warp_timer = 1.5 s`).
- Se soltar antes de atingir o tempo, nada é consumido — o jogador pode soltar sem acionar acidentalmente.

#### Efeitos das Ultimates por Personagem

| Personagem | Nome do Combo | Efeito |
|---|---|---|
| **Vanguarda** | Protocolo Cerco / Sobrecarga Total | Executa **Explosão Radial** (×2 dano, ×1.5 raio) + **Carga Titânica** (×2 dano) simultaneamente. |
| **Caçadora** | Tempestade Predatória / Eclipse Predatório | Executa **Chuva de Flechas** (×1.8 dano, ×1.5 raio) + **Dança das Adagas** (×1.8 dano, ×1.5 raio) simultaneamente. |
| **Engenheiro** | Protocolo Ragnarok / Matriz de Defesa Suprema | Implanta Torreta + Barreira de Choque + dano de área de 250px (×2.5). Com passiva `core_meltdown`, deixa plasma persistente no chão por 2,5–4 s. |

#### Indicadores de HUD para o Combo
- Quando **ambas as barras estiverem cheias**, o HUD exibe a mensagem pulsante **"SUPREMA"** em dourado (`#FACC15`) no painel do jogador como alerta de combo disponível.


### 4.1 A Vanguarda

- **Visual:** corpo circular branco (`#F8FAFC`) com triângulo azul (`#38BDF8`).
- **Arma de distância - Pistola:** tiros diretos e constantes. Boa base para multishot, ricochete, veneno e perfuração.
- **Arma corpo a corpo - Espada:** golpe em arco, com dano alto, knockback e destruição de objetos.
- **Especial de distância - Explosão Radial:** explosão ao redor do jogador, causando dano massivo, knockback e destruição de objetos próximos.
- **Especial corpo a corpo - Carga Titânica:** avanço em linha com dano largo e forte, funcionando como abertura ou fuga agressiva.
- **Combo - Protocolo Cerco:** combina Explosão Radial e Carga Titânica em uma ultimate de alto impacto.

#### Passivas da Vanguarda

| Categoria | Chave | Nome | Efeito |
|---|---|---|---|
| Distância | `ricochet` | Balas Ricocheteantes | Projéteis saltam para inimigos próximos. |
| Distância | `poison` | Munição Venenosa | Projéteis aplicam veneno por 3,4 s. |
| Distância | `multishot` | Rajada Paralela | Adiciona +1 projétil paralelo por nível, consumindo só 1 munição por salva. |
| Distância | `piercing_rounds` | Projéteis Perfurantes | Tiros ganham perfuração a cada 3 níveis e dano leve por nível. |
| Corpo a corpo | `wide_cleave` | Corte Amplo | Espada ganha alcance e arco. |
| Corpo a corpo | `execution_edge` | Fio Executor | Espada causa dano extra em inimigos com vida baixa. |
| Corpo a corpo | `shockwave` | Onda de Impacto | Golpes de espada espalham dano em área ao redor do alvo. |
| Ambas | `combat_drill` | Doutrina de Combate | Aumenta dano, cadência e reduz levemente a recarga. |
| Ambas | `field_salvage` | Saque de Campo | Abates podem recuperar munição extra. |
| Especial | `reactor_blast` | Reator Crítico | Especial ganha dano, raio e restaura parte do pente. |

### 4.2 A Caçadora

- **Visual:** corpo circular verde-escuro (`#166534`) com núcleo laranja (`#F97316`).
- **Arma de distância - Arco Longo:** flechas rápidas, fortes e com perfuração base.
- **Arma corpo a corpo - Adagas:** golpes curtos, rápidos e com alto potencial de status.
- **Especial de distância - Chuva de Flechas:** área marcada no cursor que causa dano contínuo por alguns segundos.
- **Especial corpo a corpo - Dança das Adagas:** ataque circular ao redor da Caçadora, aplicando sangramento, knockback e invulnerabilidade curta.
- **Combo - Tempestade Predatória:** combina Chuva de Flechas e Dança das Adagas, criando controle de área e explosão de dano.

#### Passivas da Caçadora

| Categoria | Chave | Nome | Efeito |
|---|---|---|---|
| Distância | `explosive` | Flechas Explosivas | Flechas explodem ao expirar ou bater em parede/objeto. |
| Distância | `homing` | Flecha Teleguiada | Flechas corrigem trajetória rumo ao inimigo mais próximo. |
| Distância | `splinter_arrows` | Flechas Estilhaço | Disparos lançam flechas laterais menores, consumindo só 1 munição. |
| Corpo a corpo | `prey_mark` | Marca da Presa | Adagas reduzem velocidade do alvo e aumentam o dano recebido pelo golpe. |
| Corpo a corpo | `bleeding_blades` | Lâminas Sangrentas | Adagas aplicam sangramento por tempo. |
| Corpo a corpo | `fan_blades` | Leque de Adagas | Adagas ganham arco, alcance e dano. |
| Corpo a corpo | `shadow_lunge` | Investida Sombria | Acertos de adaga reduzem a recarga do dash e dão invulnerabilidade curtíssima. |
| Ambas | `predator_focus` | Foco Predador | Aumenta dano, ritmo das duas armas e reduz levemente a recarga. |
| Ambas | `ammo_siphon` | Saque Preciso | Abates podem recuperar munição e carga de especial. |
| Especial | `storm_eye` | Olho da Tempestade | Chuva de Flechas dura mais, cobre área maior e causa mais dano. |

---

### 4.3 O Engenheiro

- **Visual:** corpo circular amarelo-claro (`#FEF08A`) com núcleo dourado (`#EAB308`) e forma `circle_square`.
- **Arma de distância - Canhão de Plasma:** projéteis explosivos de curto alcance com dano em área ao impacto.
- **Arma corpo a corpo - Chave Magnética:** golpes pesados com força de atração que puxam inimigos para perto.
- **Especial de distância - Torreta Sentinela:** implanta uma torreta autônoma no chão que atira automaticamente nos inimigos mais próximos enquanto estiver ativa.
- **Especial corpo a corpo - Barreira de Choque:** erige uma barreira elétrica estática que danifica e empurra inimigos ao contato.
- **Combo - Protocolo Ragnarok:** combina Torreta Sentinela e Barreira de Choque em uma ultimate de controle de área de alto impacto, implantando múltiplas construções simultâneas.

#### Passivas do Engenheiro

| Categoria | Chave | Nome | Efeito |
|---|---|---|---|
| Distância | `plasma_aoe` | Plasma Estendido | Aumenta o raio da explosão dos tiros de plasma. |
| Distância | `supercharge` | Sobrecarga de Energia | Tiros de plasma têm chance de dar curto-circuito em inimigos próximos. |
| Corpo a corpo | `heavy_alloy` | Liga Pesada | Aumenta dano e empurrão da Chave Magnética. |
| Corpo a corpo | `magnetic_pull` | Atração Magnética | Aumenta a força de atração ao golpear. |
| Especial | `reinforced_turrets` | Aço Estrutural | Torretas duram mais tempo e atiram mais rápido. |
| Especial | `shocking_barrier` | Cerca Elétrica | Barreiras causam mais dano ao colidir com inimigos. |
| Ambas | `tech_scavenger` | Reciclagem | Abates rendem mais moedas e munição. |
| Ambas | `overclock` | Overclock | Acelera todas as recargas passivas (torreta, barreira, especiais). |
| Defesa | `structural_shield` | Escudo de Campo | Perto de construções ativas, ganha escudo temporário. |
| Ultimate | `core_meltdown` | Fusão do Núcleo | Ragnarok incendeia o chão deixando plasma persistente por alguns segundos. |

---

## 5. Mecânicas Principais

### 5.1 Movimento

- Movimento livre em 8 direções com WASD ou setas por padrão.
- Os atalhos de jogabilidade podem ser remapeados durante a sessão pela tela de Configurações, incluindo teclado, mouse e joystick/controle.
- Velocidade base: 235 px/s.
- Terrenos, buffs, escudo, itens e upgrades modificam a velocidade final.

### 5.2 Dash

- Ativado com Espaço por padrão.
- Velocidade: 790 px/s.
- Duração: 0,17 s.
- Invulnerabilidade curta: duração do dash + 0,08 s.
- Cooldown base: 1,25 s.
- Botas Crono, híbridos e Investida Sombria podem reduzir a recarga efetiva.

### 5.3 Dano e Status

- **Dano de contato:** inimigos causam dano contínuo ao encostar.
- **Knockback:** espada, adagas, escudo, explosões, minas e especiais empurram inimigos.
- **Congelamento:** projéteis com buff reduzem inimigos para 28% da velocidade por 2,4 s.
- **Veneno:** dano contínuo aplicado por Munição Venenosa.
- **Sangramento:** dano contínuo aplicado por Lâminas Sangrentas.
- **Escudo:** concede invulnerabilidade por 7 s, +25% velocidade, repulsão e dano próximo.
- **Dano Flutuante:** números de dano agora usam animações de suavização (`pytweening`) para melhor feedback visual.

---

## 6. Progressão

### 6.1 Level Up — Singleplayer

- Fórmula de XP: `40 + 25 x nível_atual`.
- Ao subir de nível, o jogador escolhe 1 entre 3 cartas.
- Níveis comuns oferecem upgrades gerais.
- A cada 3 níveis, o upgrade é grande e oferece passivas específicas do personagem.
- Quando todas as passivas específicas chegarem ao nível 10, upgrades grandes passam a oferecer Omni Upgrades.

### 6.1.1 Level Up — Multiplayer (Draft por Revezamento)

No modo cooperativo, o nível é **global para a dupla**. O XP coletado por qualquer jogador alimenta uma barra de nível compartilhada. Ao subir de nível, ambos os jogadores ganham a oportunidade de escolher um upgrade de status por meio de um sistema de draft:

- **Pool de escolhas:** o jogo gera uma lista única com **3 opções** de status aleatórias (+vida, +velocidade, +dano etc.).
- **Fluxo de seleção (draft):**
  1. O Jogador A (quem tem prioridade neste nível) escolhe **1 das 3** opções disponíveis.
  2. O Jogador B escolhe **1 das 2** opções restantes.
  3. A opção que sobrar é **descartada**.
- **Alternância de prioridade (anti-fixa):** o jogo rastreia quem iniciou a escolha no nível anterior. A cada novo level up, a ordem inverte automaticamente. No primeiro nível, a prioridade é definida por **sorteio** e alternada nos subsequentes.
- **Bloqueio ativo de input:**
  - Enquanto o Jogador A estiver selecionando, o input do Jogador B é **completamente ignorado**.
  - Após a escolha do Jogador A, o sistema libera o input do Jogador B e bloqueia o do Jogador A automaticamente.
  - A UI destaca com **brilho ou cursor colorido** (P1/P2) de quem é a vez em tempo real.
- **Passivas exclusivas:** passivas específicas de personagem permanecem individuais e separadas da escolha comum de draft.
- A cada 3 níveis, o upgrade grande continua oferecendo passivas específicas, aplicadas individualmente a cada jogador.

### 6.2 Upgrades Comuns

| Chave | Nome | Efeito |
|---|---|---|
| `speed` | Passos Leves | +8% velocidade permanente. |
| `damage` | Lâmina e Cano | +13% dano em todos os ataques. |
| `max_health` | Pulso Vital | +22 vida máxima e cura parcial. |
| `fire_rate` | Ritmo de Combate | +11% cadência de tiros e golpes. |
| `sword_range` | Alcance da Espada | +10% alcance do corte. |
| `special_gain` | Núcleo Instável | +16% carga de especial por abate. |
| `vampirism` | Vampirismo | Recupera +2,5 de vida por inimigo derrotado. |

### 6.3 Omni Upgrades

| Chave | Nome | Efeito |
|---|---|---|
| `omni_power` | Poder Absoluto | +25% dano, cadência e alcance de espada. |
| `omni_survival` | Resiliência Máxima | +45 vida máxima, +45% velocidade e +5 vampirismo. |
| `omni_special` | Mestre Supremo | +100% carga de especial, +35% alcance de espada e +15% cadência. |

### 6.4 Pontos de Item

- Cada nível concede +1 ponto de item.
- Upgrades grandes concedem +2 pontos extras.
- Derrotar mini-boss concede +3 pontos.
- Pontos são usados no inventário para subir o nível dos itens, no Gerenciamento de Skills, na Loja de Status e no **Mercado Negro**.

### 6.5 Gerenciamento de Skills

A janela **Gerenciamento de Skills** lista todas as passivas específicas do personagem:

- Skills com nível 0 aparecem como bloqueadas.
- Skills com nível 1 ou mais aparecem como ativas.
- O jogador pode gastar pontos de item para desbloquear ou upar uma skill.
- Skills comuns custam **3 pontos** por nível.
- Skills da categoria **Especial** custam **6 pontos** por nível.
- O nível máximo continua sendo 10.
- A janela pode ser acessada pelo pause ou pela tecla K por padrão durante a partida.
- A lista usa cards escuros de alto contraste; a cor da categoria aparece como borda/etiqueta para preservar leitura.

### 6.6 Loja de Status

A **Loja de Status** é uma mecânica de progressão permanente dentro da sessão:

- Desbloqueio inicial de teste: **nível 20**.
- Acessada pelo pause pela opção **Loja de Status**.
- Usa os mesmos pontos ganhos por nível, criando disputa com itens e skills.
- Ao abrir a loja desbloqueada, o jogador pode usar **Roletar** para gastar 1 ponto e gerar 3 ofertas.
- Cada oferta mostra atributos aleatórios, força da melhoria e custo de compra.
- Abaixo de cada oferta existe o botão **Jogar novamente**, que custa 1 ponto e rerrola apenas aquela oferta.
- Rerrolar uma oferta pode aumentar sua força, chegando até melhorias lendárias.
- O custo de compra é calculado de acordo com a quantidade e intensidade dos status oferecidos.
- Ao comprar uma oferta, seus status são aplicados permanentemente na run e a loja volta ao estado sem ofertas.

---

## 7. Inventário, Itens e Construções

O inventário é aberto com I ou TAB por padrão. Ele possui 5 slots ativos e 20 slots de reserva. Apenas itens ativos aplicam efeitos. A interface agora utiliza **pygame-gui** para uma navegação mais moderna e fluida.

### 7.1 Itens Base

| Chave | Nome | Efeito |
|---|---|---|
| `storm_core` | Núcleo da Tempestade | Solta raio automático no inimigo mais próximo. |
| `guardian_plate` | Placa Guardiã | Reduz dano recebido quando a vida está abaixo de 42%. |
| `magnet_orb` | Orbe Magnético | Aumenta raio de coleta de XP, moedas e caixas. |
| `chrono_boots` | Botas Crono | Aumenta velocidade e reduz cooldown do dash. |
| `blade_relay` | Relé da Lâmina | Aumenta cadência, dano e alcance da espada. |

### 7.2 Upgrade de Itens

| Rank | Tipo | Custo por nível | Nível máximo |
|---|---|---:|---:|
| 1 | Item base | 1 ponto | 10 |
| 2 | Híbrido | 3 pontos | 10 |
| 3 | Relíquia | 7 pontos | 10 |

### 7.3 Fusão

- Dois itens de mesmo rank e nível 10 podem ser marcados com F.
- A fusão exige confirmação em uma tela dedicada com árvore de visualização.
- Itens usados são consumidos.
- Dois itens base criam um híbrido.
- Dois híbridos compatíveis criam uma relíquia.
- Relíquias não podem ser fundidas.

### 7.4 Venda de Itens

O jogador pode vender itens para recuperar pontos de item:
- **Restrição:** Só é possível vender itens que estão na **reserva** (não equipados).
- **Valores de venda:**
  - Rank 1 (Básico): `1 + (nível - 1) // 2` pontos.
  - Rank 2 (Híbrido): `5 + (nível - 1) * 2` pontos.
  - Rank 3 (Relíquia): `15 + (nível - 1) * 5` pontos.

---

## 8. Mercado Negro e Evolução

O **Mercado Negro** é uma aba especial no Inventário desbloqueada permanentemente na sessão ao atingir o **nível 10 com qualquer Relíquia**.

### 8.1 Loja do Mercado Negro
Permite a compra direta de itens base para acelerar builds:
- **Custo:** 15 pontos por item base (nível 1).
- Comprar um item que o jogador já possui aumenta o nível do mesmo.

### 8.2 Transformação de Itens
Mecânica de alto risco para forçar a criação de híbridos:
- **Custo:** 15 pontos.
- **Alvo:** Item base (Rank 1) no nível 10.
- **Resultados:**
  - **Sucesso (50%):** O item evolui instantaneamente para um Híbrido aleatório compatível.
  - **Falha Segura (25%):** Nada acontece, mas os pontos são consumidos.
  - **Falha Crítica (25%):** O item sofre degradação e se transforma em outro item base aleatório.

---

## 9. Relíquias

Relíquias são itens Tier 3 criados por fusão de híbridos ou obtidos raramente em caixas.

### 9.1 Relíquias Pré-definidas

| Nome | Fontes |
|---|---|
| Relíquia do Caçador Eterno | `blade_relay + chrono_boots + guardian_plate + magnet_orb` |
| Relíquia da Vontade de Ferro | `blade_relay + chrono_boots + guardian_plate + storm_core` |
| Relíquia da Velocidade Caótica | `blade_relay + chrono_boots + magnet_orb + storm_core` |
| Relíquia do Colossus Estático | `blade_relay + guardian_plate + magnet_orb + storm_core` |
| Relíquia do Tempo Absoluto | `chrono_boots + guardian_plate + magnet_orb + storm_core` |

### 9.2 Aura de Fogo

Ao equipar pelo menos uma relíquia ativa:

- Dois círculos de fogo orbitam o personagem.
- Raio: cerca de 82 px.
- Dano: 8 dano/s em inimigos dentro da área.
- Visual: anel roxo translúcido com glóbulos laranja/dourados.

---

## 10. Mundo e Inimigos

### 10.1 Inimigos Base

Todos os inimigos escalam em vida (× máx 2,6) e velocidade (× máx 1,75) conforme a dificuldade dinâmica dirigida pelo **Game Director**. A tabela abaixo usa os valores base.

| Tipo | Nome | Raio | Vida | Dano | Vel. | XP | Cor |
|---|---|:---:|---:|---:|---:|---:|---|
| `basic` | Errante | 17 | 36 | 14 | 122 | 11 | Laranja |
| `runner` | Corredor | 13 | 24 | 11 | 178 | 9 | Rosa-escuro |
| `brute` | Bruto | 24 | 95 | 25 | 82 | 25 | Roxo |
| `chromatic` | Errático Cromático | 20 | 62 | 6 | 255 | 36 | Ciano |
| `spitter` | Atirador Ácido | 16 | 58 | 9 | 92 | 18 | Verde-lima |
| `bulwark` | Guardião Blindado | 29 | 175 | 30 | 66 | 38 | Cinza-azul |
| `sapper` | Demolidor Instável | 15 | 32 | 8 | 168 | 16 | Amarelo |

### 10.2 Inimigos Avançados (Habilidades Especiais)

| Tipo | Nome | Vida | Vel. | XP | Comportamento Especial |
|---|---|---:|---:|---:|---|
| `phantom` | Espectro Intangível | 48 | 135 | 22 | Alterna entre **intangível** (imune a dano) e tangível a cada 4–6 s. Fica mais claro enquanto intangível. |
| `golem` | Golem de Magnetita | 145 | 72 | 35 | **Imune a knockback**. Avança de forma irresístivel, causando impacto pesado. |
| `necromancer` | Invocador Sombrio | 85 | 98 | 42 | **Invoca 2 Servos** (minions) a cada 12 s enquanto estiver vivo, até o limite global de inimigos. |

### 10.3 Inimigos de Elite e Chefes

| Tipo | Nome | Raio | Vida | Dano | XP | Observação |
|---|---|:---:|---:|---:|---:|---|
| `minion` | Servo do Colosso | 11 | 18 | 8 | 4 | Invocado pelo Necromancer, rápido e fraco. |
| `miniboss` | Colosso Errante | 46 | 720 | 22 | 180 | Chefe periódico, concede +3 pontos e +80 munições ao morrer. |

### 10.4 Tabela de Drops de Munição por Inimigo

| Inimigo | Chance | Quantidade |
|---|---:|---:|
| Errante | 12% | 5 a 12 |
| Corredor | 10% | 5 a 12 |
| Bruto | 28% | 10 a 18 |
| Errático Cromático | 75% | 18 a 30 |
| Atirador Ácido | 18% | 5 a 12 |
| Guardião Blindado | 34% | 14 a 24 |
| Demolidor Instável | 16% | 6 a 14 |
| Servo do Colosso | 0% | — |
| Espectro Intangível | 20% | 5 a 10 |
| Golem de Magnetita | 35% | 12 a 20 |
| Invocador Sombrio | 40% | 8 a 18 |
| Colosso Errante | 100% | +80 (bonuário direto) |

---

## 11. Interface Modernizada

A interface do jogo passou por uma reformulação técnica completa para melhorar a legibilidade e o "game feel".

### 11.1 Tecnologias de UI
- **Pygame-GUI:** Utilizado em um "Design System Modular" para as telas de Inventário, Mercado Negro, Upgrades, Seleção de Personagem, Modos e Configurações. As janelas modais nativas agora gerenciam pop-ups de confirmação, barras de rolagem nativas e imagens sobrepostas vetoriais, substituindo os antigos canvas absolutos.
- **Pygame Freetype:** Substituiu o sistema de fontes legado, permitindo renderização de texto em alta qualidade, rotação e efeitos de contorno sem perda de performance.
- **Animation Manager (Tweening):** Sistema centralizado baseado em `pytweening` que gerencia transições suaves, números flutuantes de dano e efeitos de "pop" em elementos da interface.

### 11.2 Regras de Navegação
- **Voltar ao Menu:** Redireciona o jogador para a tela inicial do modo `Sobrevivência`, mantendo o jogo ativo na memória para recomeços rápidos, sem fechar a aplicação principal.
- **Fechar (Quit / X):** Encerra a sessão da aplicação ativa devolvendo o fluxo para o Arcade de Jogos raiz.

### 11.3 HUD e Telas
- **Feedback de Munição:** Mensagens flutuantes "RECARREGANDO" ou "SEM MUNIÇÃO" com efeito de pulso sobre o jogador.
- **Dano Flutuante:** Números que sobem e desaparecem com curvas de suavização (Ease Out).
- **Miras Coloridas:** Mira azul para P1 e vermelha para P2, com ponteiros específicos para joystick.

---

## 12. Arquitetura Técnica (v2.0)

### 12.1 Dependências
- `pygame` (Core)
- `pygame-ce` (Opcional, recomendado para performance)
- `pygame_gui` (Sistemas de menu modulares)
- `pytweening` (Animações)

### 12.2 Organização de Código
- `presentation/animation_manager.py`: Orquestra todas as interpolações temporais.
- `presentation/menus/`: Contém os componentes de UI modulares (como `ui_components.py`, que atua como Factory para botões, painéis, caixas de texto e superfícies).
- `core/game_logic.py`: Mantém a separação entre lógica pura e visual, comunicando-se com a UI via eventos.
- `core/managers/buff_applicator.py`: O novo coração do sistema matemático de itens.

### 12.3 Status Injetados e Buff Applicator
O `buff_applicator.py` centraliza a matemática de escala dos itens. Em vez de o jogo consultar o inventário a cada frame (o que antes causava quedas bruscas de performance), as funções embutem valores pré-calculados nas seguintes variáveis diretamente no objeto `Player` após o equip/desequip/upgrade:
- `item_speed_bonus`: Multiplicador de velocidade acumulativo de itens.
- `item_damage_bonus`: Bônus direto em ataques e armas.
- `item_attack_rate_bonus`: Aceleração da cadência base.
- `item_sword_range_bonus`: Extensão do hitbox e arco da espada.
- `item_guardian_reduction`: Fração redutora de dano pré-calculada do item `guardian_plate`.

Esses bônus de itens somam-se separadamente aos bônus permanentes ganhos pelo ganho de nível.

---

## 13. Roadmap de UIX e Performance

### Curto Prazo
- Implementar **Pygame-CE** como motor padrão para ganho de performance imediato (até 20% em loops de renderização).
- Migrar o restante dos menus manuais para o `pygame_gui`.

### Médio Prazo
- Avaliar **Numba/Cython** para as rotinas de colisão de hordas (>200 inimigos).
- Adicionar suporte a **Shaders (GLSL)** via `ModernGL` para efeitos de aura e distorção sem sobrecarregar a CPU.

### End-Game: Forja Direta de Relíquias
**Gatilho:** Ter no mínimo 3 itens Tier 3 (Relíquias) no inventário do jogador.

**Comportamento:**
- Ao atingir o critério, a janela de **Construções** exibe um botão de compra direta para cada Relíquia Tier 3 listada.
- O botão exibe `"Forjar Relíquia (50 pts)"` quando desbloqueado, ou `"Bloqueado: Requer 3 Relíquias (X/3)"` com progresso visual quando ainda não atingido.
- A compra passa pelo fluxo de confirmação de pontos (`point_confirm`) antes de ser efetivada.

**Custo:** 50 Pontos de Item — alto o suficiente para criar um sumidouro de recursos significativo no final da partida (late-game).

**Objetivo de Design:** Dar ao jogador experiente um alvo claro de progressão de poder máximo após completar a construção das relíquias disponíveis por fusão, recompensando a dedicação à jornada de itens.

### Longo Prazo
- Sistema de partículas acelerado por GPU.
- UI Dinâmica que reage ao ritmo da música e intensidade do combate.

---

## 14. Refatoração do Sistema de Upgrades (Altares e RNG)

Uma grande atualização de arquitetura e game design foi implementada para mitigar o vício de pausar constantemente o jogo para microgerenciar atributos. O microgerenciamento estático através de menus de pausa foi substituído por mecânicas físicas no mapa (Altares) integradas com elementos de risco, recompensa e RNG dinâmico.

### 14.1 Alteração do Escopo das Janelas de UI Estáticas
- **Inventário e Skills:** As janelas abertas por inputs do jogador (I, TAB, K) passam a ser exclusivamente informativas e de consulta. O jogador pode equipar/desequipar itens da reserva, consultar passivas e atributos, mas **todos os upgrades ativos estão bloqueados** durante a gameplay normal (`game.active_altar is None`).
- **Acesso Limitado:** Upgrades de itens (Rank 1/2/3), desbloqueio de passivas e compras na Loja de Status só são permitidos quando o jogador está em colisão ativa com um Altar físico correspondente no mapa.

### 14.2 Entidade Altar, Spawning e Bullet Time (Tempo Desacelerado)
- **Tipos de Altares:**
  - `weapon_altar` (Altar de Armas): Permite upgrades e transformações de itens no Inventário.
  - `skill_altar` (Altar de Habilidades): Permite desbloquear e aprimorar passivas na janela de Skills.
  - `stat_altar` (Altar de Status): Permite acessar as melhorias permanentes da Loja de Status.
- **Spawning Periódico:** Um novo Altar surge dinamicamente no mapa a cada **90 segundos**, alternando de forma aleatória entre os três tipos.
- **Bullet Time (Física Temporal):** Ao aproximar-se e colidir com um Altar ativo, a escala de tempo global do jogo é desacelerada para `0.2` (Bullet Time), a janela de upgrade do Altar correspondente abre automaticamente, e uma **vinheta visual dinâmica** com moldura brilhante e o aviso `"TEMPO DESACELERADO"` é renderizada na tela.

### 14.3 Matemática de RNG Dinâmico e Pity System (Azar)
Toda tentativa de upgrade realizada em um Altar passa por uma verificação probabilística de 4 resultados baseados no fator sorte do jogador:

1. **Super Sucesso (15%):**
   - *Efeito:* O item/habilidade ganha **+2 níveis pelo custo de apenas 1**. Em caso de Loja de Status, o bônus adquirido é **duplicado**.
   - *Visual:* Dispara partículas douradas adicionais e causa um tremor na tela.
2. **Sucesso (55%):**
   - *Efeito:* Aplica o aprimoramento padrão de +1 nível pelo custo normal.
3. **Sucesso Parcial (20%):**
   - *Efeito:* O upgrade é bem-sucedido (+1 nível), mas o jogador recebe **50% de reembolso dos pontos/moedas** gastos (arredondado para cima).
4. **Falha Instável (10%):**
   - *Efeito:* O upgrade falha (nenhum nível é ganho), os pontos e moedas investidos são totalmente perdidos, o Altar entra em combustão e **se auto-destrói imediatamente** (`altar.active = False`), retornando o jogo ao tempo real (`time_scale = 1.0`).
   - *Debuff Temporal:* O jogador recebe o debuff **Falha Instável** que reduz permanentemente `-10% de velocidade de movimento` por **20 segundos** reais.

- **Sistema de Pity (Azar Acumulado):**
  - Para evitar séries frustrantes de derrotas, o jogo possui um contador oculto de azar (`pity_counter`).
  - A cada *Falha Instável* ou *Sucesso Parcial*, o contador acumula **+15%** à chance de *Super Sucesso* no rolar seguinte.
  - Ao obter um *Super Sucesso*, a probabilidade de Super Sucesso retorna ao valor base de 15%.

### 14.4 Restrições, Cooldowns e HP Sacrificial
- **Cooldown de Lojas:**
  - **Mercado Negro:** Após realizar uma transação (compra ou transformação), a loja entra em cooldown de **60 segundos** reais.
  - **Loja de Status:** Após comprar uma melhoria, a loja entra em cooldown de **30 segundos** reais.
- **Rerolls com Sacrifício de Vida (HP):**
  - O primeiro Reroll de ofertas da Loja de Status em um Altar de Status custa 1 ponto de item comum.
  - Rerolls subsequentes no mesmo altar exigem um **sacrifício permanente de -5 de Vida Máxima (Max HP)** do jogador. O jogo exibe um **pop-up de aviso explícito** antes de concretizar o sacrifício para evitar acidentes.

### 14.5 Feedback Visual e Navegação
- **Altares Animados:** Cada Altar possui uma base rúnica de alto contraste e um **núcleo de energia flutuante** que orbita e pulsa no mapa com a cor correspondente (Vermelho para Armas, Roxo para Skills, Dourado para Status).
- **Bússola Dinâmica:** O HUD apresenta uma seta compasso direcional dinâmica na cor do Altar ativo mais próximo, mostrando em tempo real a distância em metros até ele para facilitar a localização no mapa infinito.

---

## 15. Relógio de Partida e Minimapa de Radar

### 15.1 Relógio de Gameplay (Stopwatch)

Um cronômetro de partida em formato `HH:MM:SS` é exibido no topo central da tela em um card flutuante semitransparente com bordas azul-neon (`#38BDF8`) durante toda a sessão:

- **Posicionamento:** Topo central (`x = SCREEN_WIDTH // 2`, `y = 12`) sem conflitar com nenhum painel de jogador.
- **Pausa Automática:** O relógio **não avança** enquanto o jogo está pausado ou em telas de menu (Inventário, Skills, Loja de Status), pois é derivado diretamente de `game.time_alive`, que só incrementa dentro do loop ativo de física.
- **Suporte Multijogador:** Chamado tanto em `_draw_hud` (Singleplayer) quanto em `_draw_coop_hud` (Cooperativo), posicionado harmoniosamente entre os painéis do P1 e P2.

### 15.2 Minimapa de Radar Glassmórfico

Um radar circular semitransparente é exibido no canto inferior esquerdo da tela durante toda a partida:

- **Posicionamento:** Canto inferior esquerdo (`x = 20 + r`, `y = SCREEN_HEIGHT - 20 - r`), diâmetro de aproximadamente 110 px escalados.
- **Estética:** Fundo circular escuro translúcido (`rgba 15, 23, 42, 190`), borda metálica dupla e traços de bússola direcional nas extremidades Norte, Sul, Leste e Oeste.
- **Elementos Rastreados no Radar (alcance = 1600 px de jogo):**
  - **P1**: Ponto azul-celeste (`#38BDF8`) fixo no centro do radar.
  - **P2 (Coop)**: Ponto vermelho (`#EF4444`) relativo à posição de P2; omitido se P2 estiver caído.
  - **Altares Ativos**: Pontos pulsantes com a cor do tipo do Altar — Vermelho para Armas, Roxo para Habilidades, Dourado para Status. A pulsação é animada em tempo real.
  - **Mini-bosses e Chefes**: Pontos laranja (`#F97316`) piscantes quando o inimigo especial entra no raio de detecção do radar.
- **Implementação:** Método `_draw_minimap(self, game)` em `presentation/ui.py`, chamado logo após `_draw_hud(game)` no renderizador principal.

---

## 16. Crachás de Selos (Weapon Stamps Badges) no HUD

O sistema de exibição de selos equipados nas armas do jogador foi refatorado de **pontos coloridos** (que exigiam memorização de cores) para **micro-crachás de texto** descritivos e intuitivos exibidos durante o gameplay:

### 16.1 Layout e Posicionamento

- Cada arma do jogador possui **3 slots de crachá** exibidos imediatamente abaixo das células de munição/espada na barra de cooldowns do HUD.
- Dimensões unitárias de `11 x 8 px` com espaçamento de `2 px`, totalizando `37 px` — exatamente a largura disponível sob cada célula de arma.
- **Zero sobreposição**: Os badges reutilizam a área livre já reservada no layout do HUD, sem deslocar nenhum outro elemento visual.

### 16.2 Abreviações por Selo

| Chave | Abreviação | Cor Característica |
|---|:---:|---|
| `impact` | `IMP` | Vermelho (`#EF4444`) |
| `haste` | `RAP` | Amarelo (`#F59E0B`) |
| `lifesteal` | `VAM` | Roxo (`#8B5CF6`) |
| `blast` | `EXP` | Laranja (`#F97316`) |
| `frost` | `CON` | Azul (`#3B82F6`) |
| `toxic` | `VEN` | Verde (`#10B981`) |
| `caliber` | `CAL` | Ciano (`#06B6D4`) |
| `repulse` | `REP` | Rosa (`#EC4899`) |
| `junk_grey` | `CIN` | Cinza (`#6B7280`) |
| `junk_rust` | `FER` | Marrom (`#92400E`) |
| `junk_cracked` | `QUE` | Cinza Escuro (`#374151`) |

### 16.3 Indicação de Nível

- **Nível 1:** Badge preenchido com a cor do selo, texto branco.
- **Nível 2:** Badge preenchido + borda branca luminosa ao redor do contorno.
- **Nível 3 (Máximo):** Badge preenchido + borda dourada pulsante (`#FFD700`) animada em tempo real, texto em dourado suave.
- **Slot Vazio:** Badge escuro com traço `-` em cinza discreto (`rgb 70, 85, 105`).

---

## 17. Expansão de Gameplay Premium: Mecânicas e Fases de Jogo (v2.5)

Esta seção descreve formalmente as 8 fases de mecânicas de gameplay premium desenvolvidas para enriquecer o ritmo tático, o desafio e a atmosfera visual de *Sobrevivência*.

### 17.1 [Fase 1] Tags e Sinergias de Equipamentos (Tier 3 / Híbridos)
Para orientar melhor o jogador na construção do seu arsenal ativo, o sistema analisa os atributos, tags e categorias dos equipamentos no inventário:
- **Aviso Luminoso no Inventário:** Slots de itens ativos que possuem sinergia de tags (como corpo a corpo, área, velocidade ou elemental) recebem uma **borda de neon ciano pulsante** (`#22D3EE`) desenhada sobre o frame de seleção na UI.
- **Identificação Dinâmica:** O realce visual serve para dar confirmação imediata de bônus cumulativos de sinergia aplicados.

### 17.2 [Fase 2] Ímã de Coleta Global (Efeito Vacuum)
Uma mecânica clássica de atração total de drops no cenário:
- **Drop Físico:** Um item de utilidade clássico com formato de ímã de alta fidelidade (extremidades azul/vermelha) surge raramente no mundo ao derrotar inimigos.
- **Mecânica de Coleta:** Ao ser tocado, ativa o `magnet_timer` por **4 segundos**. Durante este período, **todos** os XP, moedas e caixas de itens espalhados pelo mapa infinito são atraídos na direção dos jogadores a uma velocidade exponencial de **1200 px/s**.

### 17.3 [Fase 3] Colosso Errante Aprimorado: Arena de Neon e Co-op Assimétrico
Ao surgir no mapa, o Mini-boss *Colosso Errante* altera as regras de movimentação física do cenário:
- **Barreira de Arena:** Uma barreira circular enorme em neon carmim com raio de **520 px** é erguida instantaneamente.
- **Co-op Assimétrico:** No modo multiplayer, o sistema divide a dupla de forma assimétrica. Um jogador fica preso no lado de dentro da arena contra o Colosso Errante, e o outro jogador fica isolado do lado de fora.
- **Perigo na Borda:** Jogadores que tentarem atravessar a barreira de energia sofrem **6 HP/s de dano direto** e recebem um **forte empurrão (knockback)** de volta.
- **Público Gladiador (Multidão):** Outros inimigos que tentam alcançar os jogadores aguardam do lado de fora da arena física, orbitando entre 550px e 680px da barreira em círculo, esperando o desfecho do duelo para atacar em bando.

### 17.4 [Fase 4] Reações Elementares e Combos de Status
Combates que utilizam múltiplos efeitos nocivos aplicam combos de reações explosivas em cadeia:
- **Choque Térmico (Thermal Shock):** Desferir um ataque físico/cortante em um oponente sob efeito de **Congelamento** quebra instantaneamente o gelo, aplicando dano crítico de **1.5x do dano base + 60 de dano fixo**, dispersando partículas ciano brilhantes no ar.
- **Hemotoxina (Hemotoxin):** Aplicar simultaneamente **Sangramento** e **Veneno** em um mesmo alvo consome instantaneamente ambos os debuffs para causar dano imediato devastador igual a **(poison_dps + bleed_dps) * 4.0**, gerando uma explosão de partículas verdes e roxas.

### 17.5 [Fase 5] Portais do Vazio e Dimensão de Bolso (Pocket Dimension)
Após o Colosso Errante ser derrotado, um **Portal do Vazio** em espiral tridimensional roxa e magenta surge em suas coordenadas físicas de morte:
- **Ativação e Teletransporte:** Qualquer jogador que tocar no portal ativa o teletransporte cooperativo para a Dimensão de Bolso, um espaço isolado nas coordenadas físicas `(20000, 20000)`.
- **Desafio do Vazio (Void Decay):** Os jogadores lutam contra hordas de monstros elites sob uma **vinheta de tela roxa escura com contagem regressiva de 30 segundos**. Durante este tempo, todos os sobreviventes sofrem decaimento constante de **-1.5 HP/s (Void Decay)**.
- **Recompensa Lendária:** Ao término dos 30 segundos, todos são teletransportados de volta às coordenadas originais do portal de entrada, e uma **Caixa de Item Lendária** surge em suas posições como recompensa de sobrevivência.

### 17.6 [Fase 6] Spawn Noturno Especial e o Bloody Altar (Altar Sangrento)
O ciclo Dia/Noite dinâmico recebe novos desafios quando a luminosidade do ambiente cai drasticamente (`light_level < 0.15`):
- **Spawn Exclusivo:** Monstros normais adormecem, dando lugar a spawns de **Morcego da Sombra** (rápido e frágil) e **Lobo Infectado** (alto dano de contato e comportamento veloz).
- ** bloody Altar (Pacto de Sangue):** O *Altar de Status* transmuta-se em um altar carmim. Ofertas de upgrades permanentes no menu passam a custar **20% do Max HP atual** do jogador em vez de pontos de inventário.
- **Bônus de Sangue:** Aceitar este pacto sacrificial de HP concede um buff permanente e cumulativo de **+15% de Dano de Ataque** (`damage_bonus += 0.15`). A UI se adapta perfeitamente com botões no tema perigo (`intent="danger"`) e legendas vermelhas.

### 17.7 [Fase 7] NPCs de Escolta Ativos e o Drone Mascote Orbital
Os eventos de escolta no mapa tornam-se mais cooperativos e recompensadores:
- **Autodefesa de Escolta:** Os NPCs que os jogadores devem proteger atiram de forma autônoma a cada **0.6 segundos** nos inimigos mais próximos a um raio de detecção de **450 px**.
- **Drone Mascote:** Concluir o evento de escolta com sucesso concede ao jogador um **Drone Mascote** de suporte tecnológico.
- **Comportamento do Mascote:** O Drone orbita o jogador gerando belíssimos anéis de luz neon ciano no HUD e dispara raios laser a cada **0.7 segundos** no inimigo mais próximo a um raio de **400 px** com dano consistente.

### 17.8 [Fase 8] Barra de Alerta Dinâmica (Heat / Threat Level Gauge)
Uma mecânica que recompensa jogadores agressivos e habilidosos ao mesmo tempo que pune a estagnação:
- **Medição do Heat:** Eliminar monstros acumula calor na barra (`heat_level` de `0` a `100`). Abater monstros básicos concede `+3.5`, elites/noturnos `+8.0`, brutos `+12.0` e mini-bosses `+35.0`. O medidor resfria estavelmente a `-1.8 / segundo` na ausência de Kills.
- **Escala de Perigo (Dificuldade):** Níveis altos de Heat multiplicam o ritmo e periculosidade de spawn de novos inimigos em até **+75%**, acelerando spawns de cromáticos em até **2.5x**.
- **Chances de Drops Raros:** Em contrapartida direta, quanto maior o Heat, mais caem moedas, cura e escudos. Adicionalmente, inimigos mortos ganham até **2.5% de chance de dropar Caixas de Itens** no chão em combate em alta temperatura.
- **HUD Glassmórfico Neon:** Exibe um medidor glassmórfico de gradiente **amarelo-laranja-carmim** posicionado no centro do topo, logo abaixo do relógio. Ao ultrapassar **75%**, a palavra **"AMEAÇA MÁXIMA!"** pisca emitindo um glow carmim ao redor do visor, aumentando o game feel de urgência.
