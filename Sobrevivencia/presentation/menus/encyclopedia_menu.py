import html
import pygame

try:
    import pygame_gui
except ImportError:
    pygame_gui = None

if __package__:
    from ...data.constants import COLORS, P2_AIM_COLOR, SCREEN_HEIGHT, SCREEN_WIDTH
    from ...data.encyclopedia import ENCYCLOPEDIA_CATEGORIES, ENCYCLOPEDIA_ENTRIES
    from ...data.items import InventoryItem
    from ...data.stamps import Stamp
    from ..ui_utils import hex_color
else:
    from Sobrevivencia.data.constants import COLORS, P2_AIM_COLOR, SCREEN_HEIGHT, SCREEN_WIDTH
    from Sobrevivencia.data.encyclopedia import ENCYCLOPEDIA_CATEGORIES, ENCYCLOPEDIA_ENTRIES
    from Sobrevivencia.data.items import InventoryItem
    from Sobrevivencia.data.stamps import Stamp
    from Sobrevivencia.presentation.ui_utils import hex_color


class EncyclopediaMenu:
    def init_encyclopedia_menu(self):
        self.encyclopedia_window = None
        self.encyclopedia_buttons = {}
        self.encyclopedia_topic_buttons = {}
        self.encyclopedia_category_buttons = {}
        self.encyclopedia_search_entry = None
        self._last_encyclopedia_signature = None

    def filtered_encyclopedia_entries(self, category="Todos", query=""):
        query = (query or "").strip().lower()
        entries = []
        for entry in ENCYCLOPEDIA_ENTRIES:
            if category and category != "Todos" and entry["category"] != category:
                continue
            haystack = " ".join(
                [
                    entry["category"],
                    entry["title"],
                    entry["body"],
                    " ".join(entry.get("bullets", [])),
                    " ".join(str(k) for k in entry.get("keywords", [])),
                ]
            ).lower()
            if query and query not in haystack:
                continue
            entries.append(entry)
        return entries

    def render_encyclopedia(self, selected, mouse_pos, category="Todos", query=""):
        self.screen.fill(hex_color(COLORS["bg"]))
        self._draw_menu_background()
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((5, 10, 18, 224))
        self.screen.blit(overlay, (0, 0))

        if pygame_gui is None or not getattr(self, "components", None) or not self.components.available:
            return self._render_encyclopedia_fallback(selected, mouse_pos, category, query)

        entries = self.filtered_encyclopedia_entries(category, query)
        selected = max(0, min(selected, len(entries) - 1)) if entries else 0
        selected_title = entries[selected]["title"] if entries else ""
        signature = (
            selected,
            category,
            query,
            len(entries),
            selected_title,
            tuple(entry["title"] for entry in entries[:80]),
        )

        if not self.encyclopedia_window or not self.encyclopedia_window.alive() or self._last_encyclopedia_signature != signature:
            if self.encyclopedia_window:
                self.encyclopedia_window.kill()
            self._create_encyclopedia_window(entries, selected, category, query)
            self._last_encyclopedia_signature = signature

        self.draw_gui_layer()
        return []

    def _create_encyclopedia_window(self, entries, selected, category, query):
        c = self.components
        self.encyclopedia_buttons = {}
        self.encyclopedia_topic_buttons = {}
        self.encyclopedia_category_buttons = {}
        self.encyclopedia_window = c.arcade_window(
            "ENCICLOPEDIA",
            (1020, 640),
            "#encyclopedia_window",
            y=40,
        )
        if self.encyclopedia_window is None:
            return

        c.label(pygame.Rect((22, 12), (90, 28)), "Busca", container=self.encyclopedia_window)
        self.encyclopedia_search_entry = c.text_entry(
            pygame.Rect((112, 10), (420, 32)),
            query,
            container=self.encyclopedia_window,
        )
        if query and self.encyclopedia_search_entry is not None:
            try:
                self.encyclopedia_search_entry.focus()
            except AttributeError:
                pass
        c.label(
            pygame.Rect((552, 12), (300, 28)),
            f"{len(entries)} topico(s)",
            container=self.encyclopedia_window,
        )

        btn_clear = c.button(pygame.Rect((858, 10), (64, 32)), "Limpar", container=self.encyclopedia_window, intent="muted")
        self.encyclopedia_buttons[btn_clear] = "encyclopedia_clear_search"
        btn_back = c.button(pygame.Rect((930, 10), (64, 32)), "Voltar", container=self.encyclopedia_window, intent="secondary")
        self.encyclopedia_buttons[btn_back] = "encyclopedia_back"

        category_panel = c.scroll(pygame.Rect((20, 56), (180, 528)), container=self.encyclopedia_window)
        topic_panel = c.scroll(pygame.Rect((214, 56), (270, 528)), container=self.encyclopedia_window)
        detail_panel = c.panel(pygame.Rect((500, 56), (494, 528)), container=self.encyclopedia_window)

        categories = ("Todos",) + ENCYCLOPEDIA_CATEGORIES
        y = 10
        for cat in categories:
            btn = c.button(
                pygame.Rect((10, y), (150, 32)),
                cat,
                container=category_panel,
                intent="selected" if cat == category else "secondary",
            )
            self.encyclopedia_category_buttons[btn] = f"encyclopedia_category:{cat}"
            y += 40
        category_panel.set_scrollable_area_dimensions((160, max(528, y + 10)))

        y = 10
        for index, entry in enumerate(entries):
            title = entry["title"][:27]
            btn = c.button(
                pygame.Rect((10, y), (230, 36)),
                title,
                container=topic_panel,
                intent="selected" if index == selected else "secondary",
                tooltip=f"{entry['category']} | {entry['title']}",
            )
            self.encyclopedia_topic_buttons[btn] = f"encyclopedia_select:{index}"
            y += 44
        topic_panel.set_scrollable_area_dimensions((250, max(528, y + 10)))
        if entries:
            self._scroll_container_to_item(topic_panel, 10 + selected * 44, 36, 528, max(528, y + 10))

        if not entries:
            c.text_box(
                pygame.Rect((18, 18), (456, 180)),
                "Nenhum topico encontrado.<br><br>Tente buscar por item, selo, drop, inimigo, tag ou terreno.",
                container=detail_panel,
            )
            return

        entry = entries[selected]
        c.label(pygame.Rect((18, 14), (456, 30)), f"{entry['category']} | {entry['title']}", container=detail_panel)
        visual = self._encyclopedia_visual(entry.get("visual", {}), (128, 96))
        if visual is not None:
            c.image(pygame.Rect((18, 56), (128, 96)), visual, container=detail_panel)

        html_text = self._entry_html(entry)
        c.text_box(pygame.Rect((160, 54), (314, 168)), html_text, container=detail_panel)

        detail_scroll = c.scroll(pygame.Rect((18, 238), (456, 266)), container=detail_panel)
        lines = []
        for bullet in entry.get("bullets", []):
            lines.append(f"- {html.escape(str(bullet))}")
        keywords = ", ".join(str(k) for k in entry.get("keywords", [])[:8])
        if keywords:
            lines.append("")
            lines.append(f"Busca relacionada: {html.escape(keywords)}")
        c.text_box(
            pygame.Rect((8, 8), (424, 250)),
            "<br>".join(lines) if lines else "Sem subtopicos adicionais.",
            container=detail_scroll,
        )
        detail_scroll.set_scrollable_area_dimensions((432, 300))

    def _entry_html(self, entry):
        title = html.escape(entry["title"])
        body = html.escape(entry["body"])
        return f"<b>{title}</b><br><br>{body}"

    def _encyclopedia_visual(self, visual, size):
        kind = visual.get("kind")
        surf = pygame.Surface(size, pygame.SRCALPHA)
        rect = surf.get_rect()
        if kind == "item":
            item = InventoryItem(key=visual.get("key", "storm_core"))
            icon = self._create_item_surface(item, (72, 72), None)
            surf.blit(icon, icon.get_rect(center=rect.center))
        elif kind == "stamp":
            stamp = Stamp(key=visual.get("key", "impact"))
            icon = self._create_stamp_surface(stamp, (72, 72))
            surf.blit(icon, icon.get_rect(center=rect.center))
        elif kind == "drops":
            colors = [COLORS["xp"], COLORS["coin"], COLORS["health"], COLORS["shield"], COLORS["projectile"], COLORS["special"]]
            for i, color in enumerate(colors):
                x = 20 + (i % 3) * 42
                y = 24 + (i // 3) * 42
                pygame.draw.circle(surf, hex_color(color), (x, y), 11)
            stamp = self._create_stamp_surface(Stamp("impact"), (28, 28))
            surf.blit(stamp, (88, 55))
        elif kind == "tags":
            labels = [("EL", "#38BDF8"), ("DF", "#22C55E"), ("UT", "#F59E0B"), ("CN", "#A78BFA"), ("OF", "#EF4444")]
            for i, (label, color) in enumerate(labels):
                box = pygame.Rect(6 + (i % 3) * 40, 18 + (i // 3) * 34, 34, 24)
                pygame.draw.rect(surf, hex_color(color), box, border_radius=4)
                text, tr = self.font_tiny.render(label, (5, 10, 18))
                surf.blit(text, text.get_rect(center=box.center))
        elif kind in ("stamp_slots", "weapon_pair"):
            for row, color in enumerate((COLORS["projectile"], COLORS["sword"])):
                y = 28 + row * 42
                pygame.draw.rect(surf, hex_color(color), (8, y - 10, 38, 20), border_radius=4)
                for i in range(3):
                    pygame.draw.rect(surf, hex_color(COLORS["panel_2"]), (58 + i * 22, y - 8, 16, 16), width=1, border_radius=3)
        elif kind == "enemies":
            specs = [("#EF4444", 13), ("#F97316", 18), ("#8B5CF6", 11), ("#06B6D4", 15)]
            for i, (color, radius) in enumerate(specs):
                pygame.draw.circle(surf, hex_color(color), (24 + i * 30, 48), radius)
        elif kind == "terrain":
            pygame.draw.rect(surf, (45, 55, 72), (10, 20, 48, 42), border_radius=4)
            pygame.draw.rect(surf, (127, 29, 29), (70, 18, 42, 28), border_radius=5)
            pygame.draw.circle(surf, (234, 88, 12), (92, 72), 16)
        elif kind == "altar":
            pygame.draw.polygon(surf, hex_color(COLORS["special"]), [(64, 12), (108, 84), (20, 84)])
            pygame.draw.circle(surf, hex_color(COLORS["upgrade"]), (64, 54), 18)
        elif kind == "coop":
            pygame.draw.circle(surf, hex_color(COLORS["player"]), (42, 48), 18)
            pygame.draw.circle(surf, hex_color(P2_AIM_COLOR), (86, 48), 18)
        elif kind == "fusion":
            left = self._create_item_surface(InventoryItem("storm_core", level=10), (42, 42), None)
            right = self._create_item_surface(InventoryItem("blade_relay", level=10), (42, 42), None)
            surf.blit(left, (8, 30))
            surf.blit(right, (78, 30))
            pygame.draw.line(surf, hex_color(COLORS["upgrade"]), (54, 50), (74, 50), 3)
        elif kind == "stamp_fusion":
            for i, key in enumerate(("haste", "frost", "toxic")):
                surf.blit(self._create_stamp_surface(Stamp(key), (30, 30)), (8 + i * 34, 48))
            surf.blit(self._create_stamp_surface(Stamp("impact", 2), (44, 44)), (78, 16))
        elif kind == "special":
            pygame.draw.circle(surf, hex_color(COLORS["special"]), rect.center, 34)
            pygame.draw.circle(surf, (255, 255, 255), rect.center, 16, width=3)
        elif kind == "item_grid":
            for i, key in enumerate(("storm_core", "guardian_plate", "magnet_orb", "chrono_boots", "blade_relay")):
                icon = self._create_item_surface(InventoryItem(key), (34, 34), None)
                surf.blit(icon, (8 + i * 24, 34))
        else:
            pygame.draw.rect(surf, hex_color(COLORS["panel_2"]), rect.inflate(-24, -24), border_radius=6)
        return surf

    def handle_encyclopedia_event(self, event):
        if pygame_gui is None:
            return None
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            for btn, action in getattr(self, "encyclopedia_buttons", {}).items():
                if event.ui_element == btn:
                    return action
            for btn, action in getattr(self, "encyclopedia_topic_buttons", {}).items():
                if event.ui_element == btn:
                    return action
            for btn, action in getattr(self, "encyclopedia_category_buttons", {}).items():
                if event.ui_element == btn:
                    return action
        if event.type == pygame_gui.UI_TEXT_ENTRY_CHANGED and event.ui_element == self.encyclopedia_search_entry:
            return f"encyclopedia_search:{event.text}"
        return None

    def _render_encyclopedia_fallback(self, selected, mouse_pos, category, query):
        entries = self.filtered_encyclopedia_entries(category, query)
        selected = max(0, min(selected, len(entries) - 1)) if entries else 0
        self._center_text("ENCICLOPEDIA", self.font_big, 72, COLORS["text"])
        self._center_text(f"Categoria: {category} | Busca: {query or '-'}", self.font_small, 124, COLORS["muted"])
        buttons = []
        y = 170
        for index, entry in enumerate(entries[:9]):
            buttons.append(self._button(70, y + index * 48, 340, 38, entry["title"][:28], f"encyclopedia_select:{index}", mouse_pos, COLORS["upgrade"] if index == selected else COLORS["panel_2"]))
        if entries:
            entry = entries[selected]
            self.font_title.render_to(self.screen, (470, 178), entry["title"], hex_color(COLORS["text"]))
            for i, line in enumerate(self._wrap_text(entry["body"], 56)[:8]):
                self.font_small.render_to(self.screen, (470, 224 + i * 24), line, hex_color(COLORS["muted"]))
        buttons.append(self._button(410, 632, 280, 40, "Voltar", "encyclopedia_back", mouse_pos, COLORS["muted_2"]))
        return buttons
