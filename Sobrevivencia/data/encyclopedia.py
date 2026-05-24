if __package__:
    from .items import BASE_ITEM_KEYS, ITEM_DEFINITIONS, InventoryItem, get_item_tags, item_display_name, item_short_description
    from .stamps import STAMP_DEFINITIONS, Stamp, stamp_description, stamp_display_name
else:
    from Sobrevivencia.data.items import BASE_ITEM_KEYS, ITEM_DEFINITIONS, InventoryItem, get_item_tags, item_display_name, item_short_description
    from Sobrevivencia.data.stamps import STAMP_DEFINITIONS, Stamp, stamp_description, stamp_display_name


def _entry(category, title, body, bullets=None, visual=None, keywords=None):
    return {
        "category": category,
        "title": title,
        "body": body,
        "bullets": bullets or [],
        "visual": visual or {},
        "keywords": keywords or [],
    }


def encyclopedia_entries():
    entries = [
        _entry(
            "Combate",
            "Armas principais",
            "Cada personagem alterna entre arma de distancia e arma corpo a corpo. A arma ativa define quais selos aplicam bonus e efeitos de acerto.",
            [
                "Distancia consome municao do pente e recarrega enquanto voce luta de corpo a corpo.",
                "Corpo a corpo usa arcos de corte e costuma empurrar inimigos atingidos.",
                "O HUD mostra os slots de selos das duas armas como pequenas marcas coloridas.",
            ],
            {"kind": "weapon_pair"},
            ["weapon_1", "weapon_2", "arma", "tiro", "espada"],
        ),
        _entry(
            "Combate",
            "Especiais e combo",
            "Especiais carregam ao causar abates e dano por fonte compativel. Em coop, certas entradas tambem disparam a habilidade combinada.",
            [
                "Canais de especial sao separados por arma: distancia e corpo a corpo.",
                "A carga aparece no HUD do jogador.",
                "Algumas passivas aumentam ganho, raio ou dano do especial.",
            ],
            {"kind": "special"},
            ["especial", "combo", "ultimate"],
        ),
        _entry(
            "Itens",
            "Inventario ativo e reserva",
            "Itens passivos ficam no inventario e ate cinco podem ficar ativos. Somente itens ativos aplicam seus efeitos e contam para sinergias de tags.",
            [
                "Caixas especiais concedem itens ou melhoram itens existentes.",
                "Itens ativos aparecem na faixa superior da aba Itens.",
                "Itens na reserva podem ser vendidos, fundidos ou equipados depois.",
            ],
            {"kind": "item_grid"},
            ["inventario", "ativo", "reserva", "passivo"],
        ),
        _entry(
            "Itens",
            "Tags e sinergias",
            "Tags sao afinidades dos itens. Quando dois ou mais itens hibridos ou reliquias ativos compartilham a mesma tag, a sinergia acende o item e ativa bonus passivos.",
            [
                "Tags atuais: elemental, defensiva, utilitaria, cinetica e ofensiva.",
                "Itens basicos possuem tag, mas a sinergia visual e calculada para itens de rank 2+.",
                "O brilho ciano no slot indica item sinergizado.",
            ],
            {"kind": "tags"},
            ["tag", "tags", "sinergia", "hibrido", "reliquia"],
        ),
        _entry(
            "Itens",
            "Fusao e reliquias",
            "Dois itens nivel 10 do mesmo rank podem ser fundidos. Bases viram hibridos; hibridos diferentes podem virar reliquias.",
            [
                "A fusao consome os dois materiais marcados.",
                "Reliquias desbloqueiam sistemas avancados como o Mercado Negro quando chegam ao nivel maximo.",
                "A aba de confirmacao mostra o resultado antes de consumir os materiais.",
            ],
            {"kind": "fusion"},
            ["fusao", "hibrido", "reliquia", "nivel 10"],
        ),
        _entry(
            "Selos",
            "Slots por arma",
            "Selos sao modificadores de armas. Cada arma principal tem tres slots proprios: tres para distancia e tres para corpo a corpo.",
            [
                "Selos equipados na arma de distancia nao afetam golpes corpo a corpo.",
                "Selos equipados no corpo a corpo nao afetam projeteis.",
                "Fragmentos de sucata ficam na reserva e servem para venda ou sacrificio.",
            ],
            {"kind": "stamp_slots"},
            ["stamp", "stamps", "selo", "selos", "arma"],
        ),
        _entry(
            "Selos",
            "Sacrificio e nivel",
            "Um selo funcional pode subir ate o nivel 3. Para subir +1 nivel, escolha um selo alvo e sacrifique exatamente tres selos da reserva.",
            [
                "O alvo nao pode ser sacrificado junto com os materiais.",
                "Selos equipados precisam ser desequipados antes de vender.",
                "Selos de nivel maior vendem por mais pontos.",
            ],
            {"kind": "stamp_fusion"},
            ["sacrificio", "sacrificar", "upar", "nivel", "vender"],
        ),
        _entry(
            "Drops",
            "Coletas da arena",
            "Drops aparecem no mundo e sao atraidos pelo jogador quando entram no raio de coleta. Cada tipo tem cor e forma propria.",
            [
                "XP aumenta nivel e abre escolhas de upgrade.",
                "Moedas podem ativar buffs periodicos.",
                "Caixas especiais concedem itens; selos aparecem como losangos coloridos.",
            ],
            {"kind": "drops"},
            ["drop", "drops", "xp", "moeda", "cura", "escudo", "municao", "caixa"],
        ),
        _entry(
            "Inimigos",
            "Tipos e ameacas",
            "Inimigos variam entre perseguidores simples, corredores, brutos, unidades especiais e encontros maiores. O diretor aumenta pressao conforme a partida avanca.",
            [
                "Brutos tendem a soltar mais municao e podem ter chance maior de selo.",
                "Chromatic e minibosses concedem recompensas mais fortes.",
                "Alguns inimigos aplicam pressao por laser, veneno, explosao ou invocacoes.",
            ],
            {"kind": "enemies"},
            ["inimigo", "inimigos", "brute", "chromatic", "miniboss"],
        ),
        _entry(
            "Mundo",
            "Terreno e hazards",
            "O mundo e dividido em chunks com obstaculos, terreno, minas, fogo e outros perigos. O terreno pode alterar movimento e bloquear projeteis.",
            [
                "Fogo causa dano continuo enquanto o jogador permanece dentro.",
                "Minas detonam por proximidade.",
                "Obstaculos fisicos protegem, mas tambem limitam rotas de fuga.",
            ],
            {"kind": "terrain"},
            ["terreno", "mundo", "hazard", "fogo", "mina", "obstaculo"],
        ),
        _entry(
            "Altares",
            "Altares e lojas",
            "Altares surgem na arena e abrem menus de aprimoramento com o tempo desacelerado. Eles conectam o combate aos sistemas de build.",
            [
                "Altar de Armas abre o inventario.",
                "Altar de Skills abre passivas do personagem.",
                "Altar de Status permite roletar ofertas permanentes.",
            ],
            {"kind": "altar"},
            ["altar", "loja", "status", "skills", "mercado"],
        ),
        _entry(
            "Coop",
            "Multiplayer local",
            "No cooperativo local, jogadores possuem inventarios separados, mas varios eventos de progressao sao compartilhados ou alternados por draft.",
            [
                "P1 usa teclado/mouse e P2 usa controle.",
                "Jogador caido pode ser revivido por proximidade.",
                "O HUD mostra paineis separados com vida, arma e selos.",
            ],
            {"kind": "coop"},
            ["coop", "multiplayer", "reviver", "draft", "jogador"],
        ),
    ]

    for key in BASE_ITEM_KEYS:
        item = InventoryItem(key=key)
        tags = ", ".join(get_item_tags(item))
        entries.append(
            _entry(
                "Itens",
                item_display_name(item),
                item_short_description(item),
                [
                    f"Tag base: {tags}.",
                    "Aparece como icone circular no inventario.",
                    "Pode subir ate o nivel 10 e participar de fusoes.",
                ],
                {"kind": "item", "key": key},
                [key, tags, ITEM_DEFINITIONS[key]["short"]],
            )
        )

    for key, definition in STAMP_DEFINITIONS.items():
        stamp = Stamp(key=key)
        entries.append(
            _entry(
                "Selos",
                stamp_display_name(stamp),
                stamp_description(stamp),
                [
                    "Representado como losango colorido no drop, inventario e HUD.",
                    "Funcional" if not definition.get("is_junk") else "Sucata: material de sacrificio ou venda.",
                    "Escala ate nivel 3." if not definition.get("is_junk") else "Nao possui niveis funcionais.",
                ],
                {"kind": "stamp", "key": key},
                [key, definition.get("name", ""), "stamp", "selo"],
            )
        )

    return entries


ENCYCLOPEDIA_ENTRIES = encyclopedia_entries()
ENCYCLOPEDIA_CATEGORIES = tuple(dict.fromkeys(entry["category"] for entry in ENCYCLOPEDIA_ENTRIES))
