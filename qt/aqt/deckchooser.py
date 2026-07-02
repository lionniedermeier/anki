# Copyright: Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

from __future__ import annotations

import json
from collections.abc import Callable

from anki.collection import OpChanges
from anki.decks import DEFAULT_DECK_ID, DeckId
from aqt import AnkiQt, gui_hooks
from aqt.qt import *
from aqt.qt import sip
from aqt.utils import HelpPage, tr
from aqt.webview import AnkiWebView, AnkiWebViewKind


class DeckChooser(QHBoxLayout):
    """Embedded deck selector.

    Renders a Svelte page (a "Deck" label plus a button showing the selected
    deck) inside a small ``AnkiWebView``. Clicking the button opens the (still
    PyQt) ``StudyDeck`` picker. The selected deck id is cached in Python so that
    parent dialogs can read ``selected_deck_id`` synchronously.
    """

    def __init__(
        self,
        mw: AnkiQt,
        widget: QWidget,
        label: bool = True,
        starting_deck_id: DeckId | None = None,
        on_deck_changed: Callable[[int], None] | None = None,
        dyn: bool = False,
    ) -> None:
        QHBoxLayout.__init__(self)
        self._widget = widget  # type: ignore
        self.mw = mw
        self.dyn = dyn
        self.on_deck_changed = on_deck_changed

        self._selected_deck_id = DeckId(0)
        # default to current deck if starting id not provided
        if starting_deck_id is None:
            starting_deck_id = DeckId(self.mw.col.get_config("curDeck", default=1) or 1)
        # validate before the web view exists (label push is a no-op until then)
        self.selected_deck_id = starting_deck_id

        self._setup_ui(show_label=label)
        gui_hooks.operation_did_execute.append(self.on_operation_did_execute)

    def _setup_ui(self, show_label: bool) -> None:
        self.setContentsMargins(0, 0, 0, 0)
        self.setSpacing(8)

        self.web = AnkiWebView(kind=AnkiWebViewKind.DECK_CHOOSER)
        self.web.set_bridge_command(self._on_bridge_cmd, self)
        label_param = "1" if show_label else "0"
        self.web.load_sveltekit_page(
            f"deck-chooser/{self._selected_deck_id}?label={label_param}"
        )
        # keep the embedded view to a single control's height
        self.web.setFixedHeight(QPushButton().sizeHint().height())
        self.web.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        self.addWidget(self.web)

        qconnect(
            QShortcut(QKeySequence("Ctrl+D"), self._widget).activated, self.choose_deck
        )
        self._widget.setLayout(self)

    def selected_deck_name(self) -> str:
        return (
            self.mw.col.decks.name_if_exists(self.selected_deck_id) or "missing default"
        )

    @property
    def selected_deck_id(self) -> DeckId:
        self._ensure_selected_deck_valid()

        return self._selected_deck_id

    @selected_deck_id.setter
    def selected_deck_id(self, id: DeckId) -> None:
        if id != self._selected_deck_id:
            self._selected_deck_id = id
            self._ensure_selected_deck_valid()
            self._push_label()

    def _ensure_selected_deck_valid(self) -> None:
        deck = self.mw.col.decks.get(self._selected_deck_id, default=False)
        if not deck or (not self.dyn and deck["dyn"]):
            self.selected_deck_id = DEFAULT_DECK_ID

    def _push_label(self) -> None:
        """Update the deck name shown on the page."""
        web = getattr(self, "web", None)
        if web and not sip.isdeleted(web):
            name = json.dumps(self.selected_deck_name())
            web.eval(
                f"typeof updateDeckChooser === 'function' && updateDeckChooser({name});"
            )

    def show(self) -> None:
        self._widget.show()  # type: ignore

    def hide(self) -> None:
        self._widget.hide()  # type: ignore

    def _on_bridge_cmd(self, cmd: str) -> None:
        if cmd == "choose":
            self.choose_deck()

    def choose_deck(self) -> None:
        from aqt.studydeck import StudyDeck

        current = self.selected_deck_name()

        def callback(ret: StudyDeck) -> None:
            if not ret.name:
                return
            deck = self.mw.col.decks.by_name(ret.name)
            assert deck is not None
            new_selected_deck_id = deck["id"]
            if self.selected_deck_id != new_selected_deck_id:
                self.selected_deck_id = new_selected_deck_id
                if func := self.on_deck_changed:
                    func(new_selected_deck_id)

        StudyDeck(
            self.mw,
            current=current,
            accept=tr.actions_choose(),
            title=tr.qt_misc_choose_deck(),
            help=HelpPage.EDITING,
            cancel=True,
            parent=self._widget,
            geomKey="selectDeck",
            callback=callback,
            dyn=self.dyn,
        )

    def on_operation_did_execute(
        self, changes: OpChanges, handler: object | None
    ) -> None:
        if changes.deck:
            self._push_label()

    def cleanup(self) -> None:
        gui_hooks.operation_did_execute.remove(self.on_operation_did_execute)
        if self.web and not sip.isdeleted(self.web):
            self.web.cleanup()
            self.web = None  # type: ignore

    # legacy

    onDeckChange = choose_deck
    deckName = selected_deck_name

    def selectedId(self) -> DeckId:
        return self.selected_deck_id
