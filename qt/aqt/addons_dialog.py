# Copyright: Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

from __future__ import annotations

import aqt
from aqt.addons import AddonManager
from aqt.qt import *
from aqt.utils import disable_help_button, restoreGeom, saveGeom, tooltip, tr
from aqt.webview import AnkiWebView, AnkiWebViewKind


class AddonConfigDialog(QDialog):
    """Thin Qt shell hosting the schema-driven Svelte add-on config editor."""

    silentlyClose = True

    def __init__(self, addonsManager: AddonManager, dir_name: str) -> None:
        self.mgr = addonsManager
        self.mw = addonsManager.mw
        self.dir_name = dir_name
        QDialog.__init__(self, self.mw, Qt.WindowType.Window)
        self._setup_ui()

    def _setup_ui(self) -> None:
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.mw.garbage_collect_on_dialog_finish(self)
        disable_help_button(self)
        restoreGeom(self, "addon-config", default_size=(600, 500))
        self.web = AnkiWebView(kind=AnkiWebViewKind.ADDON_CONFIG)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.web)
        self.setLayout(layout)
        self.web.load_sveltekit_page("addon-config")
        self.show()

    def reject(self) -> None:
        self.web.cleanup()
        self.web = None  # type: ignore
        saveGeom(self, "addon-config")
        QDialog.reject(self)


class AddonsWebDialog(QDialog):
    """Thin Qt shell that hosts the Svelte add-on manager page."""

    silentlyClose = True

    def __init__(self, addonsManager: AddonManager) -> None:
        self.mgr = addonsManager
        self.mw = addonsManager.mw
        QDialog.__init__(self, self.mw, Qt.WindowType.Window)
        self._require_restart = False
        self._ready = False
        self._setup_ui()

    def _setup_ui(self) -> None:
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.mw.garbage_collect_on_dialog_finish(self)
        disable_help_button(self)
        restoreGeom(self, "addons", default_size=(800, 600))
        self.setWindowTitle(tr.addons_window_title())

        self.web = AnkiWebView(kind=AnkiWebViewKind.ADDONS)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.web)
        self.setLayout(layout)

        self.web.load_sveltekit_page("addon-manager")
        self.show()
        self.web.hide_while_preserving_layout()

    def set_ready(self) -> None:
        self._ready = True
        self.web.show()

    def refresh_list(self) -> None:
        """Ask the Svelte page to reload the add-on list."""
        self.web.eval("anki.refreshAddons && anki.refreshAddons();")

    def reject(self) -> None:
        if self._require_restart:
            tooltip(tr.addons_changes_will_take_effect_when_anki(), parent=self.mw)
        self.web.cleanup()
        self.web = None  # type: ignore
        saveGeom(self, "addons")
        aqt.dialogs.markClosed("AddonsDialog")
        QDialog.reject(self)
