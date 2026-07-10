// Copyright: Ankitects Pty Ltd and contributors
// License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import type { Writable } from "svelte/store";

export const splitViewKey = Symbol("splitView");

export interface SplitViewContext {
    panes: Writable<PaneState[]>;
    direction: "horizontal" | "vertical";
    register(pane: PaneState): void;
    unregister(id: string): void;
    /** Move the divider trailing `id` by `delta` px, clamped to the panes'
     * size constraints. Returns the px actually applied (i.e. the real
     * divider displacement), which may be smaller in magnitude than `delta`
     * or zero when a min-size boundary was hit. */
    resize(id: string, delta: number): number;
    toggleCollapsed(id: string): void;
    setHidden(id: string, hidden: boolean): void;
}

export interface PaneState {
    id: string;
    /** Current width/height in px. Ignored while `grow` or `collapsed`. */
    size: number;
    /** Minimum width/height in px, enforced while resizing. */
    min: number;
    /** Fills remaining space via flex-grow instead of a fixed `size`. At most
     * one pane on either side of a given divider should be a filler, or
     * dragging that divider has no effect. */
    grow: boolean;
    collapsed: boolean;
    /** Taken out of the layout entirely, along with its divider. Unlike an
     * unrendered pane, a hidden one keeps its contents mounted - callers rely
     * on this to preserve expensive children across show/hide. Not persisted. */
    hidden?: boolean;
}

/** The id of the last pane that takes part in the layout. The divider trailing
 * that pane is suppressed, so hiding the rightmost pane also hides the divider
 * that would otherwise dangle after its neighbour. */
export function lastVisiblePaneId(panes: readonly PaneState[]): string | null {
    const visible = panes.filter((pane) => !pane.hidden);
    return visible.length > 0 ? visible[visible.length - 1].id : null;
}

/** Resize the divider trailing `panes[index]`, transferring `delta` px
 * to/from its neighbour(s). A `grow` pane absorbs space automatically via
 * flexbox and is left untouched unless its non-growing neighbour needs a
 * matching adjustment; if neither side has a fixed size to give, the drag
 * is a no-op. Collapsed panes are not resized. */
export function resizeDivider(
    panes: readonly PaneState[],
    index: number,
    delta: number,
): PaneState[] {
    const left = panes[index];
    const right = panes[index + 1];
    if (!left || !right || left.collapsed || right.collapsed || left.hidden || right.hidden) {
        return panes.slice();
    }

    const result = panes.slice();

    if (!left.grow && !right.grow) {
        // Neither side auto-fills, so keep their combined width constant.
        const maxGrow = right.size - right.min;
        const maxShrink = left.size - left.min;
        const clamped = Math.max(-maxShrink, Math.min(maxGrow, delta));
        result[index] = { ...left, size: left.size + clamped };
        result[index + 1] = { ...right, size: right.size - clamped };
    } else if (!left.grow) {
        result[index] = { ...left, size: Math.max(left.min, left.size + delta) };
    } else if (!right.grow) {
        result[index + 1] = { ...right, size: Math.max(right.min, right.size - delta) };
    }
    // If both sides are fillers, dragging has no defined effect.

    return result;
}

/** The px the divider trailing `panes[index]` moved between `before` and
 * `after` (both produced by `resizeDivider` for the same `index`). Its
 * on-screen displacement equals the size change of whichever side is fixed:
 * the left pane grows when it isn't a filler, otherwise the right pane
 * shrinks by the same amount. Zero when the drag was clamped or a no-op. */
export function appliedDividerDelta(
    before: readonly PaneState[],
    after: readonly PaneState[],
    index: number,
): number {
    const left = before[index];
    if (!left || index + 1 >= before.length) {
        return 0;
    }
    return left.grow
        ? before[index + 1].size - after[index + 1].size
        : after[index].size - left.size;
}

export function toggleCollapsed(panes: readonly PaneState[], id: string): PaneState[] {
    return panes.map((pane) => pane.id === id ? { ...pane, collapsed: !pane.collapsed } : pane);
}

interface StoredPaneLayout {
    size: number;
    collapsed: boolean;
}

function storageKey(viewId: string): string {
    return `splitView:${viewId}`;
}

/** Overlays sizes/collapsed-state persisted under `viewId` onto `defaults`,
 * matching panes by id. Panes absent from storage (e.g. added since the
 * layout was last saved) keep their default. */
export function loadPaneLayout(
    viewId: string,
    defaults: readonly PaneState[],
): PaneState[] {
    let saved: Record<string, StoredPaneLayout>;
    try {
        const raw = localStorage.getItem(storageKey(viewId));
        if (!raw) {
            return defaults.slice();
        }
        saved = JSON.parse(raw);
    } catch {
        return defaults.slice();
    }

    return defaults.map((pane) => {
        const stored = saved[pane.id];
        return stored
            ? { ...pane, size: stored.size, collapsed: stored.collapsed }
            : pane;
    });
}

export function savePaneLayout(viewId: string, panes: readonly PaneState[]): void {
    const data: Record<string, StoredPaneLayout> = {};
    for (const pane of panes) {
        data[pane.id] = { size: pane.size, collapsed: pane.collapsed };
    }
    try {
        localStorage.setItem(storageKey(viewId), JSON.stringify(data));
    } catch {
        // storage may be unavailable (e.g. private browsing) - layout just
        // won't persist across reloads.
    }
}
