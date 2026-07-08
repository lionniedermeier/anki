// Copyright: Ankitects Pty Ltd and contributors
// License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import type { Writable } from "svelte/store";

export const tabViewKey = Symbol("tabView");

export interface TabState {
    id: string;
    title: string;
}

export interface TabViewContext {
    /** The tabs currently registered, in registration (declaration) order. */
    tabs: Writable<TabState[]>;
    /** The id of the active tab, or null when no tabs are registered. */
    activeId: Writable<string | null>;
    register(tab: TabState): void;
    unregister(id: string): void;
    setActive(id: string): void;
}
