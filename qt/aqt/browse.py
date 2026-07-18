# Copyright: Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

from __future__ import annotations

from typing import Any

from aqt import AnkiQt
from aqt.sound import av_player


class Browse:
    """The Svelte card/note browser, reached from the main window's
    ActivityBar.

    Unlike DeckBrowser/Overview, this doesn't register a new ``mw.state`` -
    it's a content swap on top of whatever state was active before, so
    navigating away (Decks/Stats/etc in its ActivityBar) just runs the
    normal state transition. The legacy Qt Browser window (Ctrl+B) remains
    available separately for editing/previewing, which this page does not
    yet support.
    """

    def __init__(self, mw: AnkiQt) -> None:
        self.mw = mw
        self.web = mw.web

    def show(self, skip_reload: bool = False) -> None:
        av_player.stop_and_clear_queue()
        self.web.set_bridge_command(self._on_bridge_cmd, self)
        if not skip_reload:
            self.web.load_sveltekit_page("browse")
        # the browse page renders its own bottom bar (search/mode controls)
        self.mw.bottomWeb.hide()

    def refresh(self) -> None:
        """Push fresh data to an already-loaded browse page."""
        self.web.eval("typeof refreshBrowse === 'function' && refreshBrowse();")

    def _on_bridge_cmd(self, cmd: str) -> Any:
        if cmd == "decks":
            self.mw.moveToState("deckBrowser", skip_reload=True)
        elif cmd == "add":
            self.mw.onAddCard()
        elif cmd == "browse":
            self.show(skip_reload=True)
        elif cmd == "stats":
            self.mw.onStats(skip_reload=True)
        elif cmd == "sync":
            self.mw.on_sync_button_clicked()
        return False
