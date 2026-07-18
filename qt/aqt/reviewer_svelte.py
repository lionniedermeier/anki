# Copyright: Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

from __future__ import annotations

import json
from typing import Sequence

import aqt
from anki.scheduler.v3 import Scheduler as V3Scheduler
from aqt import AnkiQt
from aqt.reviewer import Reviewer
from aqt.utils import tr


class SvelteReviewer(Reviewer):
    def __init__(self, mw: AnkiQt) -> None:
        super().__init__(mw)
        self._reviewer_ready = False
        self._pending_show_question = False

    def _initWeb(self) -> None:
        self._reps = 0
        self._reviewer_ready = False
        self._pending_show_question = False
        self.web.load_sveltekit_page("reviewer")
        self.web.allow_drops = True

    def _linkHandler(self, url: str) -> None:
        if url == "reviewerReady":
            self._reviewer_ready = True
            if self._pending_show_question:
                self._pending_show_question = False
                self._showQuestion()
            return
        super()._linkHandler(url)

    def _showQuestion(self) -> None:
        if not self._reviewer_ready:
            self._pending_show_question = True
            return
        super()._showQuestion()

    def onEnterKey(self) -> None:
        if self.state == "question":
            self._getTypedAnswer()
        elif self.state == "answer" and aqt.mw.pm.spacebar_rates_card():
            self.web.evalWithCallback("selectedAnswerButton()", self._onAnswerButton)

    def _showAnswerButton(self) -> None:
        if self.card.should_show_timer():
            max_time = int(self.card.time_limit() // 1000)
        else:
            max_time = 0
        state = {
            "phase": "question",
            "remaining": self._remaining_data(),
            "maxTime": max_time,
            "timeTaken": self.card.time_taken() // 1000,
            "stopTimer": False,
        }
        self.web.eval(f"__ankiSetBottom({json.dumps(state)});")

    def _showEaseButtons(self) -> None:
        if not self._states_mutated:
            self.mw.progress.single_shot(50, self._showEaseButtons)
            return
        conf = self.mw.col.decks.config_dict_for_deck_id(self.card.current_deck_id())
        state = {
            "phase": "answer",
            "buttons": self._answer_button_payload(),
            "stopTimer": conf["stopTimerOnAnswer"],
        }
        self.web.eval(f"__ankiSetBottom({json.dumps(state)});")

    def _remaining_data(self) -> dict:
        if not self.mw.col.conf["dueCounts"]:
            return {"counts": [0, 0, 0], "active": 0, "show": False}
        idx, counts = self._v3.counts()
        return {"counts": list(counts), "active": idx, "show": True}

    def _answer_button_payload(self) -> list[dict]:
        default = self._defaultEase()
        assert isinstance(self.mw.col.sched, V3Scheduler)
        labels = self.mw.col.sched.describe_next_states(self._v3.states)
        payload = []
        for ease, label in self._answerButtonList():
            key = aqt.mw.pm.get_answer_key(ease)
            payload.append(
                {
                    "ease": ease,
                    "label": label,
                    "interval": self._button_time_text(ease, labels),
                    "key": tr.actions_shortcut_key(val=key) if key else "",
                    "default": ease == default,
                }
            )
        return payload

    def _button_time_text(self, i: int, v3_labels: Sequence[str]) -> str:
        if self.mw.col.conf["estTimes"]:
            return v3_labels[i - 1]
        return ""
