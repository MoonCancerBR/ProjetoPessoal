from dataclasses import dataclass, field

if __package__:
    from .constants import RELIC_DEFINITIONS
else:
    from Sobrevivencia.data.constants import RELIC_DEFINITIONS


MAX_ITEM_LEVEL = 10
MAX_ACTIVE_ITEMS = 5
RELIC_UPGRADE_COST = 7

ITEM_DEFINITIONS = {
    "storm_core": {
        "name": "Nucleo da Tempestade",
        "short": "Raio automatico",
        "description": "Solta um raio no inimigo mais proximo em ciclos.",
    },
    "guardian_plate": {
        "name": "Placa Guardia",
        "short": "Defesa em perigo",
        "description": "Reduz dano recebido quando a vida esta baixa.",
    },
    "magnet_orb": {
        "name": "Orbe Magnetico",
        "short": "Coleta ampliada",
        "description": "Aumenta o alcance de coleta de XP, moedas e itens.",
    },
    "chrono_boots": {
        "name": "Botas Crono",
        "short": "Movimento e dash",
        "description": "Aumenta velocidade e reduz recarga do dash.",
    },
    "blade_relay": {
        "name": "Rele da Lamina",
        "short": "Espada ampliada",
        "description": "Aumenta alcance da espada e ritmo de combate.",
    },
}

BASE_ITEM_KEYS = tuple(ITEM_DEFINITIONS.keys())


def get_item_tags(item):
    base_tags = {
        "storm_core": "elemental",
        "guardian_plate": "defensiva",
        "magnet_orb": "utilitaria",
        "chrono_boots": "cinetica",
        "blade_relay": "ofensiva",
    }
    if item.rank == 1:
        return [base_tags.get(item.key, "normal")]
    elif item.hybrid_sources:
        return [base_tags.get(src, "normal") for src in item.hybrid_sources]
    return ["normal"]


@dataclass
class InventoryItem:
    key: str
    level: int = 1
    hybrid_sources: tuple = field(default_factory=tuple)
    timers: dict = field(default_factory=dict)
    slot_key: str = None

    def __post_init__(self):
        if self.slot_key is None:
            self.slot_key = self.key

    @property
    def rank(self):
        if self.key.startswith("relic:"):
            return 3
        if self.hybrid_sources:
            return 2
        return 1

    @property
    def is_hybrid(self):
        return self.rank == 2

    @property
    def is_relic(self):
        return self.rank == 3

    def effect_keys(self):
        if self.hybrid_sources:
            return self.hybrid_sources
        return (self.key,)


class Inventory:
    def __init__(self):
        self.items = {}
        self.active_slots = []
        self.points = 0
        self.fusion_marks = []
        self.black_market_unlocked = False

    def check_black_market_unlock(self):
        if self.black_market_unlocked:
            return
        for item in self.items.values():
            if item.is_relic and item.level >= MAX_ITEM_LEVEL:
                self.black_market_unlocked = True
                break

    def item_list(self):
        return list(self.items.values())

    def active_items(self):
        return [self.items[k] for k in self.active_slots if k in self.items]

    def get(self, key):
        return self.items.get(key)

    def is_active(self, slot_key):
        return slot_key in self.active_slots

    def add_random_item(self, rng):
        eligible_hybrids = [item for item in self.items.values() if item.is_hybrid and item.level < MAX_ITEM_LEVEL]

        if eligible_hybrids and rng.random() < 0.10:
            return self.add_item(rng.choice(eligible_hybrids).key)

        eligible_base = []
        for key in BASE_ITEM_KEYS:
            if key in self.items and self.items[key].level >= MAX_ITEM_LEVEL:
                continue

            is_fused = False
            for item in self.items.values():
                if item.hybrid_sources and key in item.hybrid_sources:
                    is_fused = True
                    break

            if not is_fused:
                eligible_base.append(key)

        if not eligible_base:
            if eligible_hybrids:
                return self.add_item(rng.choice(eligible_hybrids).key)
            return "duplicate_max", None

        return self.add_item(rng.choice(eligible_base))

    def add_item(self, key):
        target_dict_key = None
        for k, v in self.items.items():
            if v.key == key and v.level < MAX_ITEM_LEVEL:
                target_dict_key = k
                break

        if target_dict_key:
            item = self.items[target_dict_key]
            item.level += 1
            self.check_black_market_unlock()
            return "level_up", item

        new_dict_key = key
        count = 1
        while new_dict_key in self.items:
            new_dict_key = f"{key}_dup_{count}"
            count += 1

        item = InventoryItem(key=key, slot_key=new_dict_key)
        self.items[new_dict_key] = item
        if len(self.active_slots) < MAX_ACTIVE_ITEMS:
            self.active_slots.append(new_dict_key)
        self.check_black_market_unlock()
        return "new", item

    def add_relic(self, relic_source_key):
        """Add a pre-defined relic by its source key (sorted base keys joined by +)."""
        if relic_source_key not in RELIC_DEFINITIONS:
            return "invalid", None
        relic_key = "relic:" + relic_source_key
        sources = tuple(relic_source_key.split("+"))
        
        target_dict_key = None
        for k, v in self.items.items():
            if v.key == relic_key and v.level < MAX_ITEM_LEVEL:
                target_dict_key = k
                break

        if target_dict_key:
            item = self.items[target_dict_key]
            item.level += 1
            self.check_black_market_unlock()
            return "level_up", item
            
        new_dict_key = relic_key
        count = 1
        while new_dict_key in self.items:
            new_dict_key = f"{relic_key}_dup_{count}"
            count += 1

        item = InventoryItem(key=relic_key, level=1, hybrid_sources=sources, slot_key=new_dict_key)
        self.items[new_dict_key] = item
        if len(self.active_slots) < MAX_ACTIVE_ITEMS:
            self.active_slots.append(new_dict_key)
        self.check_black_market_unlock()
        return "new", item

    def toggle_active(self, key):
        if key not in self.items:
            return False, "Item nao encontrado."
        if key in self.active_slots:
            self.active_slots.remove(key)
            return True, "Item removido dos ativos."
        if len(self.active_slots) >= MAX_ACTIVE_ITEMS:
            return False, "Slots ativos cheios."
        self.active_slots.append(key)
        return True, "Item equipado."

    def get_sell_value(self, key):
        item = self.items.get(key)
        if not item:
            return 0
        if item.rank == 3: # Relic
            return 15 + (item.level - 1) * 5
        if item.rank == 2: # Hybrid
            return 5 + (item.level - 1) * 2
        return 1 + (item.level - 1) // 2 # Basic

    def sell_item(self, key):
        if key not in self.items:
            return False, "Item nao encontrado."
        
        value = self.get_sell_value(key)
        self.points += value
        
        self.items.pop(key)
        if key in self.active_slots:
            self.active_slots.remove(key)
            
        return True, f"Item vendido por {value} pontos."

    def upgrade_with_point(self, key):
        item = self.items.get(key)
        if item is None:
            return False, "Item nao encontrado."

        if item.is_relic:
            cost = RELIC_UPGRADE_COST
        elif item.is_hybrid:
            cost = 3
        else:
            cost = 1

        if self.points < cost:
            return False, f"Sem pontos suficientes (Custa {cost})."

        if item.level >= MAX_ITEM_LEVEL:
            return False, "Item ja esta no nivel maximo."

        self.points -= cost
        item.level += 1
        self.check_black_market_unlock()
        return True, "Item aprimorado."

    def attempt_transformation(self, dict_key, rng):
        item = self.items.get(dict_key)
        if not item or item.rank != 1 or item.level < MAX_ITEM_LEVEL:
            return False, "Requisitos nao atendidos."
        if self.points < 15:
            return False, "Sem moedas suficientes (15)."

        self.points -= 15

        chance = rng.random()
        if chance < 0.5: # 50% success
            other_keys = [k for k in BASE_ITEM_KEYS if k != item.key]
            other = rng.choice(other_keys)
            sources = tuple(sorted([item.key, other]))
            hybrid_key = "hybrid:" + "+".join(sources)

            # Remove old
            self.items.pop(dict_key)
            if dict_key in self.active_slots:
                self.active_slots.remove(dict_key)

            # Add new
            new_item = InventoryItem(key=hybrid_key, level=1, hybrid_sources=sources, slot_key=hybrid_key)
            self.items[new_item.slot_key] = new_item
            if len(self.active_slots) < MAX_ACTIVE_ITEMS:
                self.active_slots.append(new_item.slot_key)
            self.check_black_market_unlock()
            return True, "Sucesso! Item evoluiu para Hibrido."
        else:
            if rng.random() < 0.5: # 25% intact
                return False, "Falha! O item permaneceu intacto."
            else: # 25% degrade
                other_keys = [k for k in BASE_ITEM_KEYS if k != item.key]
                other = rng.choice(other_keys)
                item.key = other # Degrades to another base item
                return False, f"Degradacao! Transformou-se em {ITEM_DEFINITIONS[other]['name']}."

    def mark_for_fusion(self, key):
        item = self.items.get(key)
        if item is None:
            return False, "Item nao encontrado."
        if item.level < MAX_ITEM_LEVEL:
            return False, "Fusao exige item nivel 10."
        if item.is_relic:
            return False, "Reliquia nao pode ser fundida."

        # Enforce same-rank rule
        if self.fusion_marks:
            other = self.items.get(self.fusion_marks[0])
            if other and other.rank != item.rank:
                return False, f"So e possivel fundir itens do mesmo ranking (Rank {other.rank})."

        if key in self.fusion_marks:
            self.fusion_marks.remove(key)
            return True, "Marcacao removida."
        if len(self.fusion_marks) >= 2:
            self.fusion_marks = []
        self.fusion_marks.append(key)
        if len(self.fusion_marks) == 2:
            success, preview, message = self.preview_marked_fusion()
            if not success:
                self.fusion_marks = []
                return False, message
            return True, f"Confirme a fusao: {item_display_name(preview)}."
        return True, "Item marcado para fusao."

    def clear_fusion_marks(self):
        self.fusion_marks = []

    def preview_marked_fusion(self):
        return self.preview_fusion(self.fusion_marks)

    def preview_fusion(self, keys):
        if len(keys) != 2:
            return False, None, "Marque dois itens nivel 10 do mesmo ranking."

        first_key, second_key = keys
        first = self.items.get(first_key)
        second = self.items.get(second_key)

        if first is None or second is None:
            return False, None, "Fusao invalida."
            
        if first.key == second.key and first_key != second_key and first.rank == 1:
            pass # Permitida a fusão de dois itens idênticos do Rank 1
        elif first.key == second.key:
            return False, None, "Fusao invalida. Mesma chave base."

        if first.level < MAX_ITEM_LEVEL or second.level < MAX_ITEM_LEVEL:
            return False, None, "Fusao exige dois itens nivel 10."
        if first.rank != second.rank:
            return False, None, "So e possivel fundir itens do mesmo ranking."

        if first.key == second.key and first.rank == 1:
            import random
            other_keys = [k for k in BASE_ITEM_KEYS if k != first.key]
            other_key = random.Random(hash(first_key + second_key)).choice(other_keys)
            combined_sources = tuple(sorted([first.key, other_key]))
        else:
            combined_sources = tuple(sorted(set(first.effect_keys() + second.effect_keys())))

        if first.rank == 1:
            hybrid_key = "hybrid:" + "+".join(combined_sources)
            hybrid = InventoryItem(key=hybrid_key, level=1, hybrid_sources=combined_sources, slot_key=hybrid_key)
            return True, hybrid, "Item hibrido sera criado."

        if first.rank == 2:
            if len(combined_sources) != 4:
                return False, None, "Fontes da Reliquia se sobrepoem. Escolha hibridos diferentes."
            relic_source_key = "+".join(combined_sources)
            if relic_source_key not in RELIC_DEFINITIONS:
                return False, None, "Combinacao de Reliquia invalida."
            relic_key = "relic:" + relic_source_key
            relic = InventoryItem(key=relic_key, level=1, hybrid_sources=combined_sources, slot_key=relic_key)
            return True, relic, "Reliquia sera forjada."

        return False, None, "Fusao nao suportada para este ranking."

    def fuse_marked_items(self):
        success, result_item, message = self.preview_marked_fusion()
        if not success:
            self.fusion_marks = []
            return False, message
        first_key, second_key = self.fusion_marks
        self.fusion_marks = []

        for key in (first_key, second_key):
            self.items.pop(key, None)
            if key in self.active_slots:
                self.active_slots.remove(key)
                
        new_dict_key = result_item.key
        count = 1
        while new_dict_key in self.items:
            new_dict_key = f"{result_item.key}_dup_{count}"
            count += 1
            
        result_item.slot_key = new_dict_key
        self.items[new_dict_key] = result_item
        if len(self.active_slots) < MAX_ACTIVE_ITEMS:
            self.active_slots.append(new_dict_key)
        self.check_black_market_unlock()

        if result_item.is_relic:
            return True, "Reliquia forjada!"
        return True, "Item hibrido criado."

    def active_effect_level(self, effect_key):
        total = 0
        for item in self.active_items():
            if effect_key in item.effect_keys():
                total += item.level
        return total

    def active_hybrid_level(self):
        return sum(item.level for item in self.active_items() if item.is_hybrid)

    def active_relic_level(self):
        return sum(item.level for item in self.active_items() if item.is_relic)

    def get_active_synergies(self):
        tag_counts = {}
        active_items = self.active_items()
        for item in active_items:
            if item.rank >= 2:
                for tag in get_item_tags(item):
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1
        return {tag for tag, count in tag_counts.items() if count >= 2}

    def is_item_synergized(self, item):
        if item.rank < 2:
            return False
        active_syns = self.get_active_synergies()
        item_tags = get_item_tags(item)
        return any(t in active_syns for t in item_tags)



def item_display_name(item):
    if item.is_relic:
        relic_key = item.key[len("relic:"):]
        return RELIC_DEFINITIONS.get(relic_key, {}).get("name", "Reliquia Desconhecida")
    if item.is_hybrid:
        names = [ITEM_DEFINITIONS[key]["name"] for key in item.hybrid_sources]
        return "Hibrido: " + " + ".join(names)
    return ITEM_DEFINITIONS[item.key]["name"]


def item_short_description(item):
    if item.is_relic:
        relic_key = item.key[len("relic:"):]
        return RELIC_DEFINITIONS.get(relic_key, {}).get("description", "Aura de fogo giratoria.")
    if item.is_hybrid:
        names = [ITEM_DEFINITIONS[key]["short"] for key in item.hybrid_sources]
        return " + ".join(names) + " | extra: area e recarga"
    return ITEM_DEFINITIONS[item.key]["description"]
