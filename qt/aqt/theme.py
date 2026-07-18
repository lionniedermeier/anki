# Copyright: Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

from __future__ import annotations

import enum
import inspect
import json
import os
import re
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import anki.lang
import aqt
from anki.lang import is_rtl
from anki.utils import is_lin, is_mac, is_win
from aqt import colors, gui_hooks
from aqt.qt import (
    QApplication,
    QColor,
    QIcon,
    QPainter,
    QPalette,
    QPixmap,
    QStyle,
    QStyleFactory,
    Qt,
    qtmajor,
    qtminor,
)


@dataclass
class ColoredIcon:
    path: str
    color: dict[str, str]

    def current_color(self, night_mode: bool) -> str:
        if night_mode:
            return self.color.get("dark", "")
        else:
            return self.color.get("light", "")

    def with_color(self, color: dict[str, str]) -> ColoredIcon:
        return ColoredIcon(path=self.path, color=color)


_token_to_base_colors: dict[str, dict[str, str]] = {
    name.lower().replace("_", "-"): value
    for name, value in vars(colors).items()
    if isinstance(value, dict) and "light" in value
}
_color_dict_to_token: dict[int, str] = {
    id(value): token for token, value in _token_to_base_colors.items()
}

BUILTIN_LIGHT_THEME_ID = "anki-light"
BUILTIN_DARK_THEME_ID = "anki-dark"


@dataclass
class ColorTheme:
    """A theme distributed by an add-on or found in the user's themes folder.

    `colors` maps a semantic token name (e.g. "canvas", "button-primary-bg" -
    see qt/_aqt/theme_schema.json for the full list) to a single CSS color
    value. A theme need not cover every token; tokens it omits keep their
    built-in value. `type` is "light" or "dark", and determines which slot
    the theme is offered for in the theme picker.
    """

    id: str
    name: str
    type: str
    colors: dict[str, str]


def _builtin_theme(theme_id: str, name: str, side: str) -> ColorTheme:
    return ColorTheme(
        id=theme_id,
        name=name,
        type=side,
        colors={token: base[side] for token, base in _token_to_base_colors.items()},
    )


class WidgetStyle(enum.IntEnum):
    ANKI = 0
    NATIVE = 1


class Theme(enum.IntEnum):
    FOLLOW_SYSTEM = 0
    LIGHT = 1
    DARK = 2


class ThemeManager:
    _night_mode_preference = False
    _icon_cache_light: dict[str, QIcon] = {}
    _icon_cache_dark: dict[str, QIcon] = {}
    _icon_size = 128
    _dark_mode_available: bool | None = None
    _default_style: str | None = None
    _current_widget_style: WidgetStyle | None = None
    _default_button_layout: int | None = None
    _primitive_overrides: dict[str, dict[str, str]] = {}
    _registered_themes: dict[str, ColorTheme] = {}
    _active_light_theme_id: str = BUILTIN_LIGHT_THEME_ID
    _active_dark_theme_id: str = BUILTIN_DARK_THEME_ID
    _resolved_colors: dict[str, dict[str, str]] = {}
    _schema_tokens: set[str] | None = None

    def rtl(self) -> bool:
        return is_rtl(anki.lang.current_lang)

    def left(self) -> str:
        return "right" if self.rtl() else "left"

    def right(self) -> str:
        return "left" if self.rtl() else "right"

    # Qt applies a gradient to the buttons in dark mode
    # from about #505050 to #606060.
    DARK_MODE_BUTTON_BG_MIDPOINT = "#555555"

    def macos_dark_mode(self) -> bool:
        "True if the user has night mode on."
        if not is_mac:
            return False

        if not self._night_mode_preference:
            return False

        if self._dark_mode_available is None:
            self._dark_mode_available = set_macos_dark_mode(True)

        return self._dark_mode_available

    def get_night_mode(self) -> bool:
        return self._night_mode_preference

    def set_night_mode(self, val: bool) -> None:
        self._night_mode_preference = val
        self._update_stat_colors()

    night_mode = property(get_night_mode, set_night_mode)

    def themed_icon(self, path: str) -> str:
        "Fetch themed version of svg."
        from aqt.utils import aqt_data_folder

        if m := re.match(r"(?:mdi:)(.+)$", path):
            name = m.group(1)
        else:
            return path

        filename = f"{name}-{'dark' if self.night_mode else 'light'}.svg"
        path = os.path.join(aqt_data_folder(), "qt", "icons", filename)
        path = path.replace("\\\\?\\", "").replace("\\", "/")
        # Workaround for Qt bug. First attempt was percent-escaping the chars,
        # but Qt can't handle that.
        # https://forum.qt.io/topic/55274/solved-qss-with-special-characters/11
        path = re.sub(r"(['\u00A1-\u00FF])", r"\\\1", path)
        return path

    def icon_from_resources(self, path: str | ColoredIcon) -> QIcon:
        "Fetch icon from Qt resources."
        if self.night_mode:
            cache = self._icon_cache_light
        else:
            cache = self._icon_cache_dark

        if isinstance(path, str):
            key = path
        else:
            key = f"{path.path}-{path.color}"

        icon = cache.get(key)
        if icon:
            return icon

        if isinstance(path, str):
            # default black/white
            if "mdi:" in path:
                icon = QIcon(self.themed_icon(path))
            else:
                icon = QIcon(path)
                if self.night_mode:
                    img = icon.pixmap(self._icon_size, self._icon_size).toImage()
                    img.invertPixels()
                    icon = QIcon(QPixmap(img))
        else:
            # specified colours
            icon = QIcon(path.path)
            pixmap = icon.pixmap(16)
            painter = QPainter(pixmap)
            painter.setCompositionMode(
                QPainter.CompositionMode.CompositionMode_SourceIn
            )
            painter.fillRect(pixmap.rect(), QColor(path.current_color(self.night_mode)))
            painter.end()
            icon = QIcon(pixmap)
            return icon

        return cache.setdefault(path, icon)

    def body_class(self, night_mode: bool | None = None, reviewer: bool = False) -> str:
        "Returns space-separated class list for platform/theme/global settings."
        classes = []
        if is_win:
            classes.append("isWin")
        elif is_mac:
            classes.append("isMac")
        else:
            classes.append("isLin")

        if night_mode is None:
            night_mode = self.night_mode
        if night_mode:
            classes.extend(["nightMode", "night_mode"])
            if self.macos_dark_mode():
                classes.append("macos-dark-mode")
        if aqt.mw.pm.reduce_motion() and not reviewer:
            classes.append("reduce-motion")
        if not aqt.mw.pm.minimalist_mode():
            classes.append("fancy")
        if qtmajor == 5 and qtminor < 15:
            classes.append("no-blur")
        return " ".join(classes)

    def body_classes_for_card_ord(
        self, card_ord: int, night_mode: bool | None = None
    ) -> str:
        "Returns body classes used when showing a card."
        return f"card card{card_ord + 1} {self.body_class(night_mode, reviewer=True)}"

    def set_primitive_override(self, token: str, light: str, dark: str) -> None:
        self._primitive_overrides[token] = {"light": light, "dark": dark}
        gui_hooks.theme_did_change()

    def set_primitive_overrides(self, overrides: dict[str, dict[str, str]]) -> None:
        "Like set_primitive_override(), but applies several tokens with a single redraw."
        self._primitive_overrides.update(overrides)
        gui_hooks.theme_did_change()

    def clear_primitive_override(self, token: str) -> None:
        self._primitive_overrides.pop(token, None)
        gui_hooks.theme_did_change()

    def reset_primitive_overrides(self) -> None:
        self._primitive_overrides.clear()
        gui_hooks.theme_did_change()

    def primitive_overrides(self) -> dict[str, dict[str, str]]:
        return self._primitive_overrides

    def register_theme(self, theme: ColorTheme) -> None:
        "Make a theme distributed by an add-on or found in the user's themes folder available for selection."
        theme.colors = self._validate_theme_colors(theme.id, theme.colors)
        self._registered_themes[theme.id] = theme
        gui_hooks.themes_did_change()

    def registered_themes(self) -> list[ColorTheme]:
        return list(self._registered_themes.values())

    def light_theme_id(self) -> str:
        return self._active_light_theme_id

    def dark_theme_id(self) -> str:
        return self._active_dark_theme_id

    def _theme_schema_tokens(self) -> set[str]:
        "Valid semantic color token names a theme may override, loaded from the generated schema."
        if self._schema_tokens is None:
            import _aqt.colors

            schema_path = Path(inspect.getfile(_aqt.colors)).with_name(
                "theme_schema.json"
            )
            try:
                with open(schema_path, encoding="utf8") as f:
                    self._schema_tokens = set(
                        json.load(f)["properties"]["colors"]["properties"]
                    )
            except OSError:
                self._schema_tokens = set()
        return self._schema_tokens

    def _validate_theme_colors(
        self, theme_id: str, colors_in: dict[str, str]
    ) -> dict[str, str]:
        valid_tokens = self._theme_schema_tokens()
        validated: dict[str, str] = {}
        for token, value in colors_in.items():
            if valid_tokens and token not in valid_tokens:
                print(f"theme '{theme_id}': unknown token '{token}', ignoring")
                continue
            if not value:
                print(f"theme '{theme_id}': token '{token}' missing value, ignoring")
                continue
            validated[token] = value
        return validated

    def _resolve_theme_id(self, theme_id: str | None, side: str) -> str:
        default = (
            BUILTIN_LIGHT_THEME_ID if side == "light" else BUILTIN_DARK_THEME_ID
        )
        if theme_id is None:
            return default
        theme = self._registered_themes.get(theme_id)
        if theme is None or theme.type != side:
            return default
        return theme_id

    def _recompute_resolved_colors(self) -> None:
        light_theme = self._registered_themes[self._active_light_theme_id]
        dark_theme = self._registered_themes[self._active_dark_theme_id]
        resolved: dict[str, dict[str, str]] = {}
        for token, base in _token_to_base_colors.items():
            resolved[token] = {
                "light": light_theme.colors.get(token, base["light"]),
                "dark": dark_theme.colors.get(token, base["dark"]),
            }
        self._resolved_colors = resolved

    def resolved_theme(self) -> dict[str, dict[str, str]]:
        "Full token -> {light, dark} map produced by the active light/dark themes."
        return self._resolved_colors

    def apply_themes(self, light_theme_id: str | None, dark_theme_id: str | None) -> None:
        "Select the preferred light/dark themes and recompute resolved colors."
        self._active_light_theme_id = self._resolve_theme_id(light_theme_id, "light")
        self._active_dark_theme_id = self._resolve_theme_id(dark_theme_id, "dark")
        self._recompute_resolved_colors()
        gui_hooks.theme_did_change()

    def var(self, vars: dict[str, str]) -> str:
        """Given day/night colors/props, return the correct one for the current theme."""
        side = "dark" if self.night_mode else "light"
        token = _color_dict_to_token.get(id(vars))
        if token is not None:
            if token in self._primitive_overrides:
                return self._primitive_overrides[token][side]
            if token in self._resolved_colors:
                return self._resolved_colors[token][side]
        return vars[side]

    def qcolor(self, colors: dict[str, str]) -> QColor:
        """Create QColor instance from CSS string for the current theme."""

        if m := re.match(
            r"rgba\((\d+),\s*(\d+),\s*(\d+),\s*(\d+\.*\d+?)\)", self.var(colors)
        ):
            return QColor(
                int(m.group(1)),
                int(m.group(2)),
                int(m.group(3)),
                int(255 * float(m.group(4))),
            )
        return QColor(self.var(colors))

    def _determine_night_mode(self) -> bool:
        theme = aqt.mw.pm.theme()
        if theme == Theme.LIGHT:
            return False
        elif theme == Theme.DARK:
            return True
        elif is_win:
            return get_windows_dark_mode()
        elif is_mac:
            return get_macos_dark_mode()
        else:
            return get_linux_dark_mode()

    def apply_style(self) -> None:
        "Apply currently configured style."
        new_theme = self._determine_night_mode()
        theme_changed = self.night_mode != new_theme
        new_widget_style = aqt.mw.pm.get_widget_style()
        style_changed = self._current_widget_style != new_widget_style
        if not theme_changed and not style_changed:
            return
        self.night_mode = new_theme
        self._current_widget_style = new_widget_style
        app = aqt.mw.app
        if not self._default_style:
            style = app.style()
            assert style is not None
            self._default_style = style.objectName()
            self._default_button_layout = style.styleHint(
                QStyle.StyleHint.SH_DialogButtonLayout
            )
        self._apply_palette(app)
        self._apply_style(app)
        gui_hooks.theme_did_change()

    def _apply_style(self, app: QApplication) -> None:
        buf = ""

        if aqt.mw.pm.get_widget_style() == WidgetStyle.ANKI:
            from aqt.stylesheets import custom_styles

            app.setStyle(QStyleFactory.create("fusion"))  # type: ignore

            buf += "".join(
                [
                    custom_styles.general(self),
                    custom_styles.button(self),
                    custom_styles.checkbox(self),
                    custom_styles.menu(self),
                    custom_styles.combobox(self),
                    custom_styles.tabwidget(self),
                    custom_styles.table(self),
                    custom_styles.spinbox(self),
                    custom_styles.scrollbar(self),
                    custom_styles.slider(self),
                    custom_styles.splitter(self),
                ]
            )

        else:
            app.setStyle(QStyleFactory.create(self._default_style))  # type: ignore
            # Qt 6.10+ reads this from the system's theme
            buf += f"QTableView {{ gridline-color: {self.var(colors.BORDER_SUBTLE)}; }}"

        # allow addons to modify the styling
        buf = gui_hooks.style_did_init(buf)

        app.setStyleSheet(buf)

    def _apply_palette(self, app: QApplication) -> None:
        set_macos_dark_mode(self.night_mode)

        palette = QPalette()
        text = self.qcolor(colors.FG)
        palette.setColor(QPalette.ColorRole.WindowText, text)
        palette.setColor(QPalette.ColorRole.ToolTipText, text)
        palette.setColor(QPalette.ColorRole.Text, text)
        palette.setColor(QPalette.ColorRole.ButtonText, text)

        hlbg = self.qcolor(colors.HIGHLIGHT_BG)
        palette.setColor(
            QPalette.ColorRole.HighlightedText, self.qcolor(colors.HIGHLIGHT_FG)
        )
        palette.setColor(QPalette.ColorRole.Highlight, hlbg)

        canvas = self.qcolor(colors.CANVAS)
        palette.setColor(QPalette.ColorRole.Window, canvas)
        palette.setColor(QPalette.ColorRole.AlternateBase, canvas)

        palette.setColor(QPalette.ColorRole.Button, canvas)

        input_base = self.qcolor(colors.CANVAS_CODE)
        palette.setColor(QPalette.ColorRole.Base, input_base)
        palette.setColor(QPalette.ColorRole.ToolTipBase, input_base)

        palette.setColor(
            QPalette.ColorRole.PlaceholderText, self.qcolor(colors.FG_SUBTLE)
        )

        disabled_color = self.qcolor(colors.FG_DISABLED)
        palette.setColor(
            QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, disabled_color
        )
        palette.setColor(
            QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, disabled_color
        )
        palette.setColor(
            QPalette.ColorGroup.Disabled,
            QPalette.ColorRole.HighlightedText,
            disabled_color,
        )

        palette.setColor(QPalette.ColorRole.Link, self.qcolor(colors.FG_LINK))

        palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)

        app.setPalette(palette)

    def _update_stat_colors(self) -> None:
        import anki.stats as s

        s.colLearn = self.var(colors.STATE_NEW)
        s.colRelearn = self.var(colors.STATE_LEARN)
        s.colCram = self.var(colors.STATE_SUSPENDED)
        s.colSusp = self.var(colors.STATE_SUSPENDED)
        s.colMature = self.var(colors.STATE_REVIEW)
        s._legacy_nightmode = self._night_mode_preference


def get_windows_dark_mode() -> bool:
    "True if Windows system is currently in dark mode."
    if not is_win:
        return False

    from winreg import (  # type: ignore[attr-defined]
        HKEY_CURRENT_USER,
        OpenKey,
        QueryValueEx,
    )

    try:
        key = OpenKey(
            HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
        )
        return not QueryValueEx(key, "AppsUseLightTheme")[0]
    except Exception:
        # key reportedly missing or set to wrong type on some systems
        return False


def set_macos_dark_mode(enabled: bool) -> bool:
    "True if setting successful."
    from aqt._macos_helper import macos_helper

    if not macos_helper:
        return False
    return macos_helper.set_darkmode_enabled(enabled)


def get_macos_dark_mode() -> bool:
    "True if macOS system is currently in dark mode."
    from aqt._macos_helper import macos_helper

    if not macos_helper:
        return False
    return macos_helper.system_is_dark()


def get_linux_dark_mode() -> bool:
    """True if Linux system is in dark mode.
    Only works if D-Bus is installed and system uses org.freedesktop.appearance
    color-scheme to indicate dark mode preference OR if GNOME theme has
    '-dark' in the name."""
    if not is_lin:
        return False

    def parse_stdout_dbus_send(stdout: str) -> bool:
        dbus_response = stdout.split()
        if len(dbus_response) != 4:
            return False

        # https://github.com/flatpak/xdg-desktop-portal/blob/main/data/org.freedesktop.impl.portal.Settings.xml#L40
        PREFER_DARK = "1"

        return dbus_response[-1] == PREFER_DARK

    dark_mode_detection_strategies: list[tuple[str, Callable[[str], bool]]] = [
        (
            "dbus-send --session --print-reply=literal --reply-timeout=1000 "
            "--dest=org.freedesktop.portal.Desktop /org/freedesktop/portal/desktop "
            "org.freedesktop.portal.Settings.Read string:'org.freedesktop.appearance' "
            "string:'color-scheme'",
            parse_stdout_dbus_send,
        ),
        (
            "gsettings get org.gnome.desktop.interface gtk-theme",
            lambda stdout: "-dark" in stdout.lower(),
        ),
    ]

    for cmd, parse_stdout in dark_mode_detection_strategies:
        try:
            process = subprocess.run(
                cmd,
                shell=True,
                check=True,
                capture_output=True,
                encoding="utf8",
            )
        except FileNotFoundError:
            # detection strategy failed, missing program
            # print(e)
            continue

        except subprocess.CalledProcessError:
            # detection strategy failed, command returned error
            # print(e)
            continue

        return parse_stdout(process.stdout)

    return False  # all dark mode detection strategies failed


theme_manager = ThemeManager()
theme_manager.register_theme(
    _builtin_theme(BUILTIN_LIGHT_THEME_ID, "Anki Light", "light")
)
theme_manager.register_theme(_builtin_theme(BUILTIN_DARK_THEME_ID, "Anki Dark", "dark"))
theme_manager._recompute_resolved_colors()


def load_user_themes(themes_folder: str) -> None:
    "Registers any *.json theme files found in the user's themes folder."
    if not os.path.isdir(themes_folder):
        return
    for entry in sorted(os.listdir(themes_folder)):
        if not entry.endswith(".json"):
            continue
        path = os.path.join(themes_folder, entry)
        try:
            with open(path, encoding="utf8") as f:
                data = json.load(f)
            theme_id = data.get("id") or os.path.splitext(entry)[0]
            theme_type = data.get("type")
            if theme_type not in ("light", "dark"):
                print(f"failed to load theme '{path}': missing/invalid 'type'")
                continue
            theme = ColorTheme(
                id=theme_id,
                name=data.get("name", theme_id),
                type=theme_type,
                colors=data.get("colors", {}),
            )
        except (OSError, ValueError) as e:
            print(f"failed to load theme '{path}': {e}")
            continue
        theme_manager.register_theme(theme)
