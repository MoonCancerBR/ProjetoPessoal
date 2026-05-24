# Lore e Sistemas de Jogabilidade: Sobrevivência

Este documento reúne a análise técnica dos sistemas de jogo e a narrativa criativa do universo de **Sobrevivência**, servindo como um guia complementar de lore e *gameplay feel*.

---

## 🛠️ 1. Análise Arquitetural do Projeto

O projeto **Sobrevivência** é um jogo de ação top-down tático (*bullet heaven* / *survival* de arena) desenvolvido em **Python e Pygame** (modernizado com Pygame Community Edition, `pygame_gui` e `pytweening`). 

Sua estrutura modular e desacoplada segue as melhores práticas de desenvolvimento de jogos:

1. **`main.py`**: O orquestrador central e ponto de entrada do jogo. Controla o loop de eventos e gerencia a **Máquina de Estados** global (Menu → Seleção de Personagem → Gameplay → Pause → Game Over).
2. **`core/` (Lógica Pura de Gameplay)**:
   * **`game_logic.py`**: O "motor" do jogo. Livre de renderização direta, processa a movimentação, IAs, cooldowns, detecção de colisões (integrando-se com a física avançada do **Pymunk** se disponível) e o Game Director.
   * **`entities.py`**: Contém dataclasses limpas para representar o estado das entidades (jogador, inimigos, projéteis, slashes, construtos e altares).
   * **`world.py`**: Gerador procedural do terreno em chunks infinitos, contendo obstáculos, hazards e áreas destrutíveis.
3. **`data/` (Banco de Dados Estático)**:
   * **`constants.py`**: Parâmetros fundamentais de balanceamento, cores e configurações padrão.
   * **`items.py`**: A lógica do inventário, o sistema de pontos de item, fusões e a mecânica probabilística de transformação de itens.
   * **`stamps.py`**: Definições e bônus matemáticos do sistema de Selos (Stamps).
4. **`presentation/` (Renderização e Interface)**:
   * Gerencia toda a camada gráfica, o HUD, transições de tela e efeitos visuais usando `pytweening` e `pygame_gui` para menus dinâmicos.
5. **`config/` (Configurações em JSON)**:
   * Separação de dados cruciais (`settings.json`, `balance.json` e `keybinds.json`) para permitir ajustes sem tocar na lógica do código.

---

## ⚔️ 2. Como Funciona a Jogabilidade?

A jogabilidade de **Sobrevivência** se diferencia dos *bullet heavens* tradicionais por adicionar **camadas táticas profundas de gerenciamento de recursos, posicionamento físico no mapa e risco/recompensa**:

### A. O Ritmo do "Tactical Swap" (Troca de Armas)
Armas de longa distância **não possuem munição infinita**. O jogador tem um pente limitado e uma reserva de munição.
* Ao descarregar o pente, o personagem **alterna automaticamente** para a arma corpo a corpo (melee).
* A recarga do pente é feita **em segundo plano** (durando 2,15s base) enquanto o jogador luta com a espada/adagas/chave inglesa.
* Ao concluir a recarga, ele volta automaticamente para a arma de longa distância.
* O jogador também pode trocar manualmente para a arma melee para iniciar a recarga preventiva em segundo plano. Se a reserva de munição zerar, ele é forçado a sobreviver no corpo a corpo até encontrar novos *pickups* de munição no mapa.

### B. Barras de Especial Duplas e o Combo Ultimate (Suprema)
O jogador possui **duas barras independentes de especial**:
* **ESP DIST**: Carregada através de abates com projéteis ou efeitos à distância.
* **ESP MELEE**: Carregada por abates com golpes físicos ou efeitos de área próximos.
* **Uso Normal (`E`)**: Dispara o especial da arma empunhada no momento (ex: Explosão Radial ou Chuva de Flechas).
* **Combo Ultimate (Segurar `E` por 1,15s)**: Se **ambas** as barras estiverem cheias, o jogador ativa o Combo Suprema do personagem. Isso causa um tremor violento de tela (`screen_shake`), desacelera o tempo global temporariamente (`time_warp` de 85% de slow) e executa os dois especiais amplificados simultaneamente.

### C. O Sistema Físico de Altares e a Tensão do RNG
Para evitar que o jogador pause constantemente o jogo para gastar seus pontos e quebrar o ritmo da partida, **todos os upgrades ativos foram vinculados a Altares físicos no mapa**:
* A cada **90 segundos**, um Altar surge aleatoriamente (de Armas, Habilidades ou Status). Uma bússola no HUD guia o jogador até ele.
* Ao colidir com um Altar ativo, o jogo entra em **Bullet Time (tempo desacelerado em 80%)** e abre a respectiva interface.
* Todo upgrade em um Altar passa por uma verificação de sorte (RNG):
  * **Super Sucesso (15%)**: O item/habilidade sobe **+2 níveis pelo custo de 1** (efeito dourado e tremor de tela).
  * **Sucesso (55%)**: Ganha +1 nível normalmente.
  * **Sucesso Parcial (20%)**: Ganha +1 nível e recebe **50% de reembolso** do custo.
  * **Falha Instável (10%)**: O upgrade falha, os recursos são perdidos, o Altar se **auto-destrói em combustão** e o jogador recebe um vírus de lentidão (**-10% de velocidade por 20 segundos**).
  * **Pity System**: Cada falha ou sucesso parcial acumula +15% de chance de Super Sucesso na próxima tentativa, resetando ao vencer.

### D. Progressão Permanente: Inventário, Fusões e Selos (Stamps)
* **Fusão de Itens**: Itens básicos idênticos ou compatíveis no nível máximo (Lv10) podem ser fundidos. Duas passivas básicas formam um item **Híbrido**. Dois Híbridos no nível 10 podem ser fundidos em uma **Relíquia** lendária.
* **Aura de Fogo**: Equipar uma Relíquia ativa faz com que dois círculos rúnicos de fogo orbitem o jogador continuamente, fritando inimigos próximos.
* **Loja de Status e Sacrifício de HP**: Para roletar as ofertas na Loja de Status, o primeiro Reroll custa 1 Ponto. Os seguintes exigem um **sacrifício de -5 de HP Máximo permanente** de sua build.
* **Mercado Negro e Transformações**: Ao maximizar uma Relíquia, o Mercado Negro é aberto, permitindo comprar itens base diretamente ou arriscar 15 pontos para transformar um item base Lv10 diretamente em um Híbrido aleatório (com risco de falha crítica e degradação).
* **Selos de Armas (Weapon Stamps)**: Selos como *Impacto*, *Rapidez*, *Vampírico*, *Explosivo*, *Congelante* ou *Venenoso* podem ser equipados em slots (até 3) de cada arma. Eles aparecem no HUD como elegantes crachás abreviados (`IMP`, `RAP`, `VAM`) com bordas prateadas ou douradas com base no nível (1 a 3). Selos de "Sucata" (`junk`) não têm efeitos, servindo apenas para fusão ou venda.

### E. Multiplayer Cooperativo Tático
No modo Coop, a barra de XP é compartilhada:
* **Draft de Revezamento**: Ao subir de nível, surge uma lista de 3 melhorias. Os jogadores alternam a prioridade de escolha a cada nível. O jogador da vez escolhe primeiro, travando os comandos do parceiro. O segundo escolhe entre as duas opções restantes, e a última é descartada.
* **Tethering (Elástico)**: Os jogadores não podem se separar além do limite seguro de tela. Caso tentem se afastar demais, a física do traje os puxa de volta ao centro e um aviso visual flutuante diz: *"Fiquem Juntos!"*.
* **Mecânica de Reviver**: Se um jogador cair, o outro deve entrar no seu raio e defendê-lo por alguns segundos para reanimá-lo com vida parcial.

---

## 🌌 3. A Lore de "Sobrevivência" — A Margem de Silício

### O Contexto do Mundo
No século XXIV, a galáxia é governada com punho de ferro pela megacorporação **Antigravidade S.A.** e seu nefasto algoritmo de otimização humana: o **Game Director**. 

A fim de limpar os setores habitados de "lixo eletrônico indesejado", a corporação despeja toneladas de silício senciente, hardware obsoleto e cobaias rebeldes em uma arena dimensional infinita conhecida como **A Margem**. Lá, a gravidade é instável, o terreno se gera de maneira procedural em *chunks* geométricos de concreto e metal, e anomalias de fogo digital e minas de magnetita cercam qualquer um que ouse pisar fora das zonas seguras.

Para os condenados, a sobrevivência não é apenas um teste físico; é uma métrica de produtividade corporativa.

---

### 👥 Os Protagonistas: Os Terceirizados Sencientes

Para sobreviver na Margem, a resistência montou uma equipe de cobaias altamente modificadas com trajes rúnicos experimentais. Para evitar que fujam, seus trajes são acoplados por um cordão invisível de energia quântica — se eles se afastarem demais, a gravidade os puxa de volta sob o alerta *"Fiquem Juntos!"*.

#### 🔵 Vanguarda (Unidade de Choque 01)
* **Visual no Traje**: Um chassi circular branco imaculado (`#F8FAFC`) com uma viseira triangular azul-celeste (`#38BDF8`).
* **Lore**: Originalmente um androide de contenção de rebeliões da *Antigravidade S.A.*, a Vanguarda desenvolveu empatia e foi descartada na Margem. Equipado com uma Pistola Eletrostática de longo alcance e uma pesada Espada de Liga Titânica. 
* **O Especial**: Quando suas barras de dados estão cheias, a Vanguarda aciona o **Protocolo Cerco**. Ele injeta energia nuclear no chassi, descarregando uma *Explosão Radial* que pulveriza inimigos ao redor enquanto executa a *Carga Titânica*, avançando como um cometa de silício pelo campo de batalha, quebrando obstáculos e inimigos em pedaços.

#### 🟢 Caçadora (A Infiltradora Orgânica)
* **Visual no Traje**: Uma armadura circular verde-floresta (`#166534`) alimentada por um bio-núcleo pulsante laranja (`#F97316`).
* **Lore**: Nascida nas colônias agrárias abandonadas, a Caçadora é uma rastreadora cibernética que caça drones corporativos por esporte. Seu arco longo dispara flechas de plasma de alta velocidade, e suas adagas cirúrgicas aplicam sangramentos fatais.
* **O Especial**: Ao liberar sua ultimate, a **Tempestade Predatória**, ela marca a tela com um cursor de foco. O tempo ao seu redor entra em *Bullet Time* enquanto ela salta no ar descarregando uma *Chuva de Flechas* ácidas e executa a *Dança das Adagas*, cortando tudo ao seu redor com invulnerabilidade absoluta.

#### 🟡 Engenheiro (O Operário Demitido)
* **Visual no Traje**: Um robusto corpo circular-quadrado amarelo (`#FEF08A`) com um núcleo central dourado (`#EAB308`).
* **Lore**: O Engenheiro trabalhou 45 anos na manutenção dos geradores da corporação. Ao ser demitido sem rescisão sob o pretexto de "corte de custos algorítmico", ele roubou os projetos mais confidenciais da empresa e se jogou voluntariamente na Margem. Usa um destrutivo Canhão de Plasma e uma pesada Chave Magnética que puxa inimigos pela força da gravidade.
* **O Especial**: Ao acionar o **Protocolo Ragnarok**, o Engenheiro implanta uma *Torreta Sentinela* autônoma de fogo rápido e uma *Barreira de Choque* elétrica. A ultimate entra em colapso nuclear (`core_meltdown`), incendiando o solo com plasma de fusão persistente.

---

### 👾 A Horda: O Ecossistema de Sucata

O **Game Director** envia ondas de robôs defeituosos e mutantes de sucata para reciclar os protagonistas. Conforme os heróis sobrevivem, o Director aumenta dinamicamente a vida e a velocidade da horda.

* **Os Errantes & Corredores (Laranja e Rosa)**: Antigos robôs de serviço e drones mensageiros que enlouqueceram pela radiação eletromagnética da Margem. Atacam em enxames desesperados por peças sobressalentes.
* **Os Brutos (Roxos)**: Carregadores hidráulicos industriais reprogramados para esmagar intrusos com impacto pesado.
* **Os Erráticos Cromáticos (Cianos)**: Anomalias computacionais ultrarápidas que se movem de forma imprevisível em velocidades absurdas, deixando rastros de luz pelo mapa.
* **Os Espectros Intangíveis**: Fantasmas de dados criados por falhas na física da Margem. Eles entram em estado quântico de intangibilidade a cada poucos segundos, brilhando em tons claros e tornando-se imunes a qualquer dano.
* **O Golem de Magnetita**: Uma montanha ambulante de sucatas ferrosas. Devido ao seu gigantesco campo magnético, o Golem é **completamente imune a knockback** (empurrão), avançando de forma implacável e esmagadora.
* **Os Invocadores Sombrios (Necromancers)**: Servidores portáteis corrompidos que reconstroem rapidamente peças de metal caídas no chão, gerando pequenos *Servos do Colosso* (minions mecânicos) para cercar os heróis.
* **O Colosso Errante**: O maior pesadelo da Margem. Um tanque de demolição descontrolado de 9 metros de altura. O Game Director o libera periodicamente. Derrotá-lo é uma tarefa colossal, mas suas engrenagens guardam o prêmio máximo: uma enorme carga de munição na reserva (+80 balas) e valiosos pontos de item.

---

### 🏢 Os NPCs: Os Executivos Perdidos e a Burocracia

A maior ironia da Margem de Silício são as **Missões de Escolta Corporativa**. 

Periodicamente, o sistema de comunicações dos heróis sofre uma interceptação: *"Evento Corporativo Iniciado! Encontre os aliados no mapa."*

Os **Executivos** (`executive`) andam devagar em seus ternos de kevlar brilhantes, resmungando que a poeira da Margem está estragando suas sedas finas. Os **Funcionários** (`employee`) correm em desespero, carregando pranchetas e implorando por proteção. Os heróis são obrigados a escoltá-los até a zona de evacuação marcada em troca de recompensas raras oferecidas pelas seguradoras da empresa, que não querem perder suas "peças de gerência".

---

### 🛕 Os Altares: As Vozes da Antiga Rede

Espalhados pela Margem, jazem os **Altares de Silício**, monumentos mecânicos conectados à infraestrutura subterrânea original. Cada altar possui runas brilhantes e uma esfera central de energia (Vermelho para Armas, Roxo para Skills, Dourado para Status).

Quando os heróis se aproximam de um Altar, a colossal transferência de dados sobrecarrega seus trajes, criando o efeito de **Bullet Time** (o tempo ao redor congela a 20% da velocidade). 

A interface de dados de seus trajes pisca. Mas a rede é antiga e instável:
* Conseguir um **Super Sucesso** faz com que o Altar brilhe em ouro, injetando uma dose dupla de dados no traje do jogador.
* Mas se o jogador rolar um **10% de Falha Instável**, o Altar explode em uma labareda eletromagnética. A descarga frita os atuadores do traje do jogador, deixando-o lento por 20 segundos enquanto ele é forçado a fugir de uma horda enfurecida em tempo real.
* Pior ainda: quando os recursos de rede (Pontos de Item) secam no Altar de Status, a máquina exige uma moeda orgânica. O traje avisa: *"Aviso de Sacrifício de HP Máximo!"*. A máquina perfura o peito do hospedeiro, drenando permanentemente **-5 de Vida Máxima** para alimentar seus antigos processadores em troca de mais uma chance de roletar o destino.
