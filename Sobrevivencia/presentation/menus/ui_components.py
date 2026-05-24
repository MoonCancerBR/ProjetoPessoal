import pygame

try:
    import pygame_gui
    from pygame_gui.elements import UIButton, UILabel, UIPanel, UIScrollingContainer, UITextBox, UITextEntryLine, UIWindow, UIImage
    from pygame_gui.core import ObjectID
except ImportError:
    pygame_gui = None
    UIButton = UILabel = UIPanel = UIScrollingContainer = UITextBox = UITextEntryLine = UIWindow = None

    class ObjectID:
        def __init__(self, class_id=None, object_id=None):
            self.class_id = class_id
            self.object_id = object_id

if __package__:
    from ...data.constants import SCREEN_HEIGHT, SCREEN_WIDTH
else:
    from Sobrevivencia.data.constants import SCREEN_HEIGHT, SCREEN_WIDTH


WINDOW_ATTRS = (
    "pause_window",
    "game_over_window",
    "inv_window",
    "fusion_confirm_window",
    "stamp_fusion_window",
    "point_confirm_window",
    "stat_shop_window",
    "skills_window",
    "upgrade_window",
    "constructions_window",
    "start_window",
    "mode_select_window",
    "character_select_window",
    "commands_window",
    "settings_window",
    "encyclopedia_window",
    "rng_result_window",
)


STATE_WINDOW_ALLOWLIST = {
    "start": {"start_window"},
    "mode_select": {"mode_select_window"},
    "character_select": {"character_select_window"},
    "commands": {"commands_window"},
    "settings": {"settings_window"},
    "encyclopedia": {"encyclopedia_window"},
    "paused": {"pause_window"},
    "inventory": {"inv_window"},
    "fusion_confirm": {"inv_window", "fusion_confirm_window"},
    "stamp_fusion_confirm": {"inv_window", "stamp_fusion_window"},
    "point_confirm": {
        "inv_window",
        "skills_window",
        "stat_shop_window",
        "constructions_window",
        "point_confirm_window",
        "stamp_fusion_window",
    },
    "rng_result": {
        "inv_window",
        "skills_window",
        "stat_shop_window",
        "rng_result_window",
    },
    "stat_shop": {"stat_shop_window"},
    "constructions": {"constructions_window"},
    "skills": {"skills_window"},
    "upgrade": {"upgrade_window"},
    "game_over": {"game_over_window"},
    "playing": set(),
}


BUTTON_INTENTS = {
    "primary": ObjectID(class_id="@primary_button"),
    "secondary": ObjectID(class_id="@secondary_button"),
    "muted": ObjectID(class_id="@muted_button"),
    "danger": ObjectID(class_id="@danger_button"),
    "selected": ObjectID(class_id="@selected_panel"),
}


PLAYER_WINDOW_CLASS_IDS = {
    0: "@player_one_window",
    1: "@player_two_window",
}


def centered_rect(size, y=None):
    width, height = size
    x = (SCREEN_WIDTH - width) // 2
    top = (SCREEN_HEIGHT - height) // 2 if y is None else y
    return pygame.Rect((x, top), (width, height))


def is_alive(element):
    return bool(element and hasattr(element, "alive") and element.alive())


def kill_window(owner, attr_name):
    window = getattr(owner, attr_name, None)
    if is_alive(window):
        window.kill()
    setattr(owner, attr_name, None)


def kill_windows_except(owner, allowed):
    allowed = set(allowed)
    for attr_name in WINDOW_ATTRS:
        if attr_name not in allowed:
            kill_window(owner, attr_name)


def sync_windows_for_state(owner, state):
    kill_windows_except(owner, STATE_WINDOW_ALLOWLIST.get(state, set()))


class UIComponentFactory:
    def __init__(self, manager):
        self.manager = manager

    @property
    def available(self):
        return pygame_gui is not None and self.manager is not None

    def window(self, title, size, object_id, y=None, player_index=None, close_button=True, always_on_top=False):
        if not self.available:
            return None
        resolved_object_id = object_id
        if player_index in PLAYER_WINDOW_CLASS_IDS:
            resolved_object_id = ObjectID(
                class_id=PLAYER_WINDOW_CLASS_IDS[player_index],
                object_id=object_id,
            )
        win = UIWindow(
            rect=centered_rect(size, y),
            manager=self.manager,
            window_display_title=title,
            object_id=resolved_object_id,
            resizable=False,
            draggable=False,
            always_on_top=always_on_top,
        )
        if not close_button and getattr(win, "close_window_button", None):
            win.close_window_button.kill()
        return win

    def panel(self, rect, container=None, object_id=None):
        if not self.available:
            return None
        return UIPanel(
            relative_rect=rect,
            manager=self.manager,
            container=container,
            object_id=object_id,
        )

    def label(self, rect, text, container=None, object_id=None):
        if not self.available:
            return None
        return UILabel(
            relative_rect=rect,
            text=text,
            manager=self.manager,
            container=container,
            object_id=object_id,
        )

    def text_box(self, rect, html_text, container=None, object_id=None):
        if not self.available:
            return None
        return UITextBox(
            html_text=html_text,
            relative_rect=rect,
            manager=self.manager,
            container=container,
            object_id=object_id,
        )

    def text_entry(self, rect, text="", container=None, object_id=None):
        if not self.available:
            return None
        entry = UITextEntryLine(
            relative_rect=rect,
            manager=self.manager,
            container=container,
            object_id=object_id,
        )
        if text:
            entry.set_text(text)
        return entry

    def scroll(self, rect, container=None, object_id=None):
        if not self.available:
            return None
        return UIScrollingContainer(
            relative_rect=rect,
            manager=self.manager,
            container=container,
            object_id=object_id,
        )

    def button(self, rect, text, container=None, intent="secondary", tooltip=None, object_id=None):
        if not self.available:
            return None
        if object_id is None:
            object_id = BUTTON_INTENTS.get(intent)
        return UIButton(
            relative_rect=rect,
            text=text,
            manager=self.manager,
            container=container,
            tool_tip_text=tooltip,
            object_id=object_id,
        )

    def image(self, rect, image_surface, container=None, object_id=None):
        if not self.available:
            return None
        return UIImage(
            relative_rect=rect,
            image_surface=image_surface,
            manager=self.manager,
            container=container,
            object_id=object_id,
        )
