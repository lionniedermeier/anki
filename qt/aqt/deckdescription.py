# Copyright: Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

from __future__ import annotations

import aqt
import aqt.main
import aqt.operations
from anki.decks import DeckDict, DeckId
from aqt.operations import QueryOp
from aqt.qt import *
from aqt.utils import disable_help_button, restoreGeom, saveGeom, tr
from aqt.webview import AnkiWebView, AnkiWebViewKind


class DeckDescriptionDialog(QDialog):
    TITLE = "deckDescription"
    silentlyClose = True

    def __init__(self, mw: aqt.main.AnkiQt) -> None:
        QDialog.__init__(self, mw, Qt.WindowType.Window)
        self.mw = mw

        QueryOp(
            parent=self.mw,
            op=lambda col: col.decks.current(),
            success=self._setup_and_show,
        ).run_in_background()

    def _setup_and_show(self, deck: DeckDict) -> None:
        if deck["dyn"]:
            return

        self._deck_id = DeckId(deck["id"])
        self._setup_ui()

    def _setup_ui(self) -> None:
        self.setWindowTitle(tr.scheduling_description())
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.mw.garbage_collect_on_dialog_finish(self)
        self.setMinimumWidth(400)
        disable_help_button(self)
        restoreGeom(self, self.TITLE, default_size=(400, 400))

        self.web = AnkiWebView(kind=AnkiWebViewKind.DECK_DESCRIPTION)
        self.web.set_bridge_command(self._on_bridge_cmd, self)
        self.web.load_sveltekit_page(f"deck-description/{self._deck_id}")
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.web)
        self.setLayout(layout)
        self.show()

    def _on_bridge_cmd(self, cmd: str) -> None:
        if cmd == "close":
            # defer so the webview isn't torn down from inside its own callback
            QTimer.singleShot(0, self.close)

    def reject(self) -> None:
        self.web.cleanup()
        self.web = None  # type: ignore
        saveGeom(self, self.TITLE)
        # the description is saved from the page via the update_deck backend
        # call, which does not run through the Qt operation pipeline, so refresh
        # the current screen to reflect the change.
        self.mw.reset()
        QDialog.reject(self)
