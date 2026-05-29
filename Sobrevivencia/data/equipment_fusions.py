from dataclasses import dataclass, field


@dataclass(frozen=True)
class FusionDefinition:
    id: str
    sources: tuple
    name: str
    short: str
    description: str
    tags: tuple = field(default_factory=tuple)
    effect_keys: tuple = field(default_factory=tuple)
    hooks: tuple = field(default_factory=tuple)


BASE_TAGS = {
    "storm_core": "elemental",
    "guardian_plate": "defensiva",
    "magnet_orb": "utilitaria",
    "chrono_boots": "cinetica",
    "blade_relay": "ofensiva",
}


def fusion_id_for_sources(sources):
    return "hybrid:" + "+".join(sorted(sources))


def _fallback_definition(sources):
    sources = tuple(sorted(sources))
    return FusionDefinition(
        id=fusion_id_for_sources(sources),
        sources=sources,
        name="Hibrido: " + " + ".join(sources),
        short=" + ".join(sources),
        description="Combina os efeitos base dos equipamentos fundidos.",
        tags=tuple(BASE_TAGS.get(src, "normal") for src in sources),
        effect_keys=sources,
        hooks=("generic_hybrid_bonus",),
    )


FUSION_DEFINITIONS = {
    fusion_id_for_sources(("storm_core", "guardian_plate")): FusionDefinition(
        id=fusion_id_for_sources(("storm_core", "guardian_plate")),
        sources=("guardian_plate", "storm_core"),
        name="Bateria Ionica",
        short="Raio defensivo",
        description="Base arquitetural: fusao de tempestade e defesa. Pronta para receber efeito unico.",
        tags=("elemental", "defensiva"),
        effect_keys=("storm_core", "guardian_plate"),
        hooks=("generic_hybrid_bonus",),
    ),
    fusion_id_for_sources(("storm_core", "blade_relay")): FusionDefinition(
        id=fusion_id_for_sources(("storm_core", "blade_relay")),
        sources=("blade_relay", "storm_core"),
        name="Condutor Voltaico",
        short="Cadencia eletrica",
        description="Base arquitetural: fusao ofensiva elemental. Pronta para efeito unico.",
        tags=("ofensiva", "elemental"),
        effect_keys=("blade_relay", "storm_core"),
        hooks=("generic_hybrid_bonus",),
    ),
}


def get_fusion_definition(item_or_sources):
    sources = item_or_sources
    fusion_id = None
    if hasattr(item_or_sources, "hybrid_sources"):
        sources = item_or_sources.hybrid_sources
        fusion_id = getattr(item_or_sources, "fusion_id", None)
    sources = tuple(sorted(sources))
    fusion_id = fusion_id or fusion_id_for_sources(sources)
    return FUSION_DEFINITIONS.get(fusion_id) or _fallback_definition(sources)


def fusion_tags(item):
    return list(get_fusion_definition(item).tags)


def fusion_effect_keys(item):
    return tuple(get_fusion_definition(item).effect_keys)
