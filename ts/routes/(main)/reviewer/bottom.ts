// Copyright: Ankitects Pty Ltd and contributors
// License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import { writable } from "svelte/store";

export interface AnswerButton {
    ease: number;
    label: string;
    interval: string;
    key: string;
    default: boolean;
}

export interface RemainingCounts {
    counts: [number, number, number];
    active: number;
    show: boolean;
}

export interface BottomState {
    phase: "question" | "answer";
    remaining: RemainingCounts;
    buttons: AnswerButton[];
    maxTime: number;
    timeTaken: number;
    stopTimer: boolean;
}

const initial: BottomState = {
    phase: "question",
    remaining: { counts: [0, 0, 0], active: 0, show: false },
    buttons: [],
    maxTime: 0,
    timeTaken: 0,
    stopTimer: false,
};

export const bottomState = writable<BottomState>(initial);

export function setBottom(patch: Partial<BottomState>): void {
    bottomState.update((state) => ({ ...state, ...patch }));
}
