# Copyright: Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

from __future__ import annotations

from typing import Any

import aqt
import aqt.operations
from anki.collection import OpChanges
from anki.decks import DeckId
from aqt import AnkiQt, gui_hooks
from aqt.deckoptions import display_options_for_deck_id
from aqt.operations import QueryOp
from aqt.operations.deck import (
    add_deck_dialog,
    remove_decks,
    rename_deck,
    set_current_deck,
)
from aqt.qt import *
from aqt.sound import av_player
from aqt.utils import getOnlyText, openLink, tr


class DeckBrowser:
    """The main deck list shown when Anki starts.

    Renders a Svelte page (a tree of decks with due/new/learn counts) inside
    the shared main webview (``mw.web``). The page includes its own
    ActivityBar (Decks/Add/Browse/Stats/Sync) and bottom bar (Create
    Deck/Import File/Get Shared), all dispatched through bridge commands.
    Bridge commands also cover the bits that stay native: starting a
    review, the gear/options menu, and creating a deck. Collapsing a deck
    and drag-and-drop reparenting are handled entirely on the Svelte side,
    calling the backend directly.
    """

    def __init__(self, mw: AnkiQt) -> None:
        self.mw = mw
        self.web = mw.web
        self._refresh_needed = False

    def show(self) -> None:
        av_player.stop_and_clear_queue()
        self.web.set_bridge_command(self._on_bridge_cmd, self)
        # redraw top bar for theme change
        self.mw.toolbar.redraw()
        self.web.load_sveltekit_page("deck-browser")
        # the deck browser page renders its own bottom bar
        self.mw.bottomWeb.hide()
        self._refresh_needed = False

    def refresh(self) -> None:
        """Push fresh data to an already-loaded deck browser page."""
        self.web.eval(
            "typeof refreshDeckBrowser === 'function' && refreshDeckBrowser();"
        )
        self._refresh_needed = False
        # undo the dimming applied by fade_out_webview() when an op (eg. sync)
        # completed while the window was unfocused
        self.mw.fade_in_webview()

    def refresh_if_needed(self) -> None:
        if self._refresh_needed:
            self.refresh()

    def op_executed(
        self, changes: OpChanges, handler: object | None, focused: bool
    ) -> bool:
        if changes.study_queues and handler is not self:
            self._refresh_needed = True

        if focused:
            self.refresh_if_needed()

        return self._refresh_needed

    # Event handlers
    ##########################################################################

    def _on_bridge_cmd(self, cmd: str) -> Any:
        if ":" in cmd:
            (kind, arg) = cmd.split(":", 1)
        else:
            kind = cmd
            arg = ""
        if kind == "open":
            self.set_current_deck(DeckId(int(arg)))
        elif kind == "opts":
            self._showOptions(arg)
        elif kind == "changed":
            self._on_changed()
        elif kind == "decks":
            self.mw.moveToState("deckBrowser")
        elif kind == "add":
            self.mw.onAddCard()
        elif kind == "browse":
            self.mw.browse.show()
        elif kind == "stats":
            self.mw.onStats()
        elif kind == "sync":
            self.mw.on_sync_button_clicked()
        elif kind == "create":
            self._on_create()
        elif kind == "import":
            self.mw.onImport()
        elif kind == "shared":
            self._onShared()
        return False

    def _on_changed(self) -> None:
        """Collapsing/reparenting decks calls the backend directly from the
        Svelte side, bypassing CollectionOp - fire the hook ourselves so the
        sync status indicator, undo stack, etc. stay in sync."""
        changes = OpChanges()
        changes.deck = True
        changes.mtime = True
        changes.browser_sidebar = True
        gui_hooks.operation_did_execute(changes, self)

    def set_current_deck(self, deck_id: DeckId) -> None:
        set_current_deck(parent=self.mw, deck_id=deck_id).success(
            lambda _: self.mw.onOverview()
        ).run_in_background(initiator=self)

    # Options
    ##########################################################################

    def _showOptions(self, did: str) -> None:
        m = QMenu(self.mw)
        a = m.addAction(tr.actions_rename())
        assert a is not None
        qconnect(a.triggered, lambda b, did=did: self._rename(DeckId(int(did))))
        a = m.addAction(tr.actions_options())
        assert a is not None
        qconnect(a.triggered, lambda b, did=did: self._options(DeckId(int(did))))
        a = m.addAction(tr.actions_export())
        assert a is not None
        qconnect(a.triggered, lambda b, did=did: self._export(DeckId(int(did))))
        a = m.addAction(tr.actions_delete())
        assert a is not None
        qconnect(a.triggered, lambda b, did=did: self._delete(DeckId(int(did))))
        gui_hooks.deck_browser_will_show_options_menu(m, int(did))
        m.popup(QCursor.pos())

    def _export(self, did: DeckId) -> None:
        self.mw.onExport(did=did)

    def _rename(self, did: DeckId) -> None:
        def prompt(name: str) -> None:
            new_name = getOnlyText(
                tr.decks_new_deck_name(), default=name, title=tr.actions_rename()
            )
            if not new_name or new_name == name:
                return
            else:
                rename_deck(
                    parent=self.mw, deck_id=did, new_name=new_name
                ).run_in_background()

        QueryOp(
            parent=self.mw, op=lambda col: col.decks.name(did), success=prompt
        ).run_in_background()

    def _options(self, did: DeckId) -> None:
        display_options_for_deck_id(did)

    def _delete(self, did: DeckId) -> None:
        deck = self.mw.col.decks.get(did)
        assert deck is not None
        remove_decks(
            parent=self.mw, deck_ids=[did], deck_name=deck["name"]
        ).run_in_background()

    # Bottom bar
    ######################################################################

    def _onShared(self) -> None:
        openLink(f"{aqt.appShared}decks/")

    def _on_create(self) -> None:
        if op := add_deck_dialog(
            parent=self.mw, default_text=self.mw.col.decks.current()["name"]
        ):
            op.run_in_background()
