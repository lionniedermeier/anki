# Copyright: Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

import aqt
import aqt.forms
import aqt.main
from aqt import gui_hooks
from aqt.qt import *
from aqt.sound import av_player
from aqt.theme import theme_manager
from aqt.utils import (
    disable_help_button,
    getSaveFile,
    maybeHideClose,
    restoreGeom,
    saveGeom,
    tooltip,
    tr,
)
from aqt.webview import LegacyStatsWebView


class Stats:
    """The Svelte statistics/graphs screen, reached from the main window's
    ActivityBar.

    Like Browse, this doesn't register a new ``mw.state`` - it's a content
    swap on top of whatever state was active before.
    """

    def __init__(self, mw: aqt.main.AnkiQt) -> None:
        self.mw = mw
        self.web = mw.web

    def show(self) -> None:
        av_player.stop_and_clear_queue()
        self.web.set_bridge_command(self._on_bridge_cmd, self)
        self.web.load_sveltekit_page("graphs")
        self.mw.bottomWeb.hide()

    def _on_bridge_cmd(self, cmd: str) -> Any:
        if cmd.startswith("browserSearch"):
            _, query = cmd.split(":", 1)
            browser = aqt.dialogs.open("Browser", self.mw)
            browser.search_for(query)
        elif cmd == "decks":
            self.mw.moveToState("deckBrowser")
        elif cmd == "add":
            self.mw.onAddCard()
        elif cmd == "browse":
            self.mw.browse.show()
        elif cmd == "stats":
            self.show()
        elif cmd == "sync":
            self.mw.on_sync_button_clicked()
        return False


class DeckStats(QDialog):
    """Legacy deck stats, used by some add-ons."""

    def __init__(self, mw: aqt.main.AnkiQt) -> None:
        QDialog.__init__(self, mw, Qt.WindowType.Window)
        mw.garbage_collect_on_dialog_finish(self)
        self.mw = mw
        self.name = "deckStats"
        self.period = 0
        self.form = aqt.forms.stats.Ui_Dialog()
        # Hack: Switch out web views dynamically to avoid maintaining multiple
        # Qt forms for different versions of the stats dialog.
        self.form.web = LegacyStatsWebView(self.mw)
        self.oldPos = None
        self.wholeCollection = False
        self.setMinimumWidth(700)
        disable_help_button(self)
        f = self.form
        if theme_manager.night_mode and not theme_manager.macos_dark_mode():
            # the grouping box renders incorrectly in the fusion theme. 5.9+
            # 5.13 behave differently to 5.14, but it looks bad in either case,
            # and adjusting the top margin makes the 'save PDF' button show in
            # the wrong place, so for now we just disable the border instead
            self.setStyleSheet("QGroupBox { border: 0; }")
        f.setupUi(self)
        restoreGeom(self, self.name)
        b = f.buttonBox.addButton(
            tr.statistics_save_pdf(), QDialogButtonBox.ButtonRole.ActionRole
        )
        assert b is not None
        qconnect(b.clicked, self.saveImage)
        b.setAutoDefault(False)
        qconnect(f.groups.clicked, lambda: self.changeScope("deck"))
        f.groups.setShortcut("g")
        qconnect(f.all.clicked, lambda: self.changeScope("collection"))
        qconnect(f.month.clicked, lambda: self.changePeriod(0))
        qconnect(f.year.clicked, lambda: self.changePeriod(1))
        qconnect(f.life.clicked, lambda: self.changePeriod(2))
        maybeHideClose(self.form.buttonBox)
        gui_hooks.stats_dialog_old_will_show(self)
        self.show()
        self.refresh()
        self.activateWindow()

    def reject(self) -> None:
        self.form.web.cleanup()
        self.form.web = None  # type: ignore
        saveGeom(self, self.name)
        aqt.dialogs.markClosed("DeckStats")
        QDialog.reject(self)

    def closeWithCallback(self, callback: Callable[[], None]) -> None:
        self.reject()
        callback()

    def _imagePath(self) -> str | None:
        name = time.strftime("-%Y-%m-%d@%H-%M-%S.pdf", time.localtime(time.time()))
        name = f"anki-{tr.statistics_stats()}{name}"
        file = getSaveFile(
            self,
            title=tr.statistics_save_pdf(),
            dir_description="stats",
            key="stats",
            ext=".pdf",
            fname=name,
        )
        return file

    def saveImage(self) -> None:
        path = self._imagePath()
        if not path:
            return
        form_web_page = self.form.web.page()
        assert form_web_page is not None
        form_web_page.printToPdf(path)
        tooltip(tr.statistics_saved())

    def changePeriod(self, n: int) -> None:
        self.period = n
        self.refresh()

    def changeScope(self, type: str) -> None:
        self.wholeCollection = type == "collection"
        self.refresh()

    def refresh(self) -> None:
        self.mw.progress.start(parent=self)
        stats = self.mw.col.stats()
        stats.wholeCollection = self.wholeCollection
        self.report = stats.report(type=self.period)
        self.form.web.stdHtml(
            f"<html><body>{self.report}</body></html>",
            js=["js/vendor/jquery.min.js", "js/vendor/plot.js"],
            context=self,
        )
        self.mw.progress.finish()
