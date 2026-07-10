// Copyright: Ankitects Pty Ltd and contributors
// License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import { createContext } from "svelte";
import type { Writable } from "svelte/store";
import { get, writable } from "svelte/store";

/**
 * Imperative, reactive handle for controlling toolbar items by id.
 *
 * `ToolbarItem`/`ToolbarGroup` also accept declarative `hidden`/`disabled`
 * props; the controller is the programmatic path for the same state, so an
 * item ends up hidden (or disabled) if either source says so. Method names
 * echo the legacy `dynamic-slotting` interface (`hide`/`show`/`toggle`) for
 * cross-codebase consistency.
 */
export interface ToolbarController {
    /** Ids currently hidden. Read reactively in components via `$hidden`. */
    hidden: Writable<Set<string>>;
    /** Ids currently disabled. Read reactively in components via `$disabled`. */
    disabled: Writable<Set<string>>;
    /** Non-reactive lookup; components should derive from the stores instead. */
    isHidden(id: string): boolean;
    isDisabled(id: string): boolean;
    hide(id: string): void;
    show(id: string): void;
    toggle(id: string): void;
    setHidden(id: string, hidden: boolean): void;
    disable(id: string): void;
    enable(id: string): void;
    setDisabled(id: string, disabled: boolean): void;
}

export interface ToolbarContext {
    controller: ToolbarController;
}

/** Type-safe context pair; `getToolbarContext` throws if used outside a
 * `<Toolbar>`. */
export const [getToolbarContext, setToolbarContext] = createContext<ToolbarContext>();

/** Mutate a `Set` store, always notifying subscribers. */
function updateSet(
    store: Writable<Set<string>>,
    mutate: (set: Set<string>) => void,
): void {
    store.update((set) => {
        mutate(set);
        return set;
    });
}

/**
 * Create a toolbar controller. Consumers own the instance and pass it to
 * `<Toolbar controller={...}>`, then call e.g. `controller.hide("edit")` from
 * anywhere. If no controller is passed, `Toolbar` creates its own.
 */
export function createToolbar(): ToolbarController {
    const hidden = writable(new Set<string>());
    const disabled = writable(new Set<string>());

    return {
        hidden,
        disabled,
        isHidden: (id) => get(hidden).has(id),
        isDisabled: (id) => get(disabled).has(id),
        hide: (id) => updateSet(hidden, (set) => set.add(id)),
        show: (id) => updateSet(hidden, (set) => set.delete(id)),
        toggle: (id) =>
            updateSet(hidden, (set) => {
                if (!set.delete(id)) {
                    set.add(id);
                }
            }),
        setHidden: (id, value) => updateSet(hidden, (set) => (value ? set.add(id) : set.delete(id))),
        disable: (id) => updateSet(disabled, (set) => set.add(id)),
        enable: (id) => updateSet(disabled, (set) => set.delete(id)),
        setDisabled: (id, value) => updateSet(disabled, (set) => (value ? set.add(id) : set.delete(id))),
    };
}
