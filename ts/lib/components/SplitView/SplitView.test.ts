// Copyright: Ankitects Pty Ltd and contributors
// License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import { beforeEach, describe, expect, test, vi } from "vitest";

import {
    appliedDividerDelta,
    lastVisiblePaneId,
    loadPaneLayout,
    type PaneState,
    resizeDivider,
    savePaneLayout,
    toggleCollapsed,
} from "./SplitView";

function pane(overrides: Partial<PaneState> & { id: string }): PaneState {
    return { size: 200, min: 100, grow: false, collapsed: false, ...overrides };
}

describe("resizeDivider", () => {
    test("two fixed panes: dragging transfers size between them", () => {
        const panes = [pane({ id: "a" }), pane({ id: "b" })];
        const result = resizeDivider(panes, 0, 30);
        expect(result[0].size).toBe(230);
        expect(result[1].size).toBe(170);
    });

    test("two fixed panes: shrink is clamped at the left pane's minimum", () => {
        const panes = [pane({ id: "a", size: 110 }), pane({ id: "b" })];
        const result = resizeDivider(panes, 0, -50);
        expect(result[0].size).toBe(100);
        expect(result[1].size).toBe(210);
    });

    test("two fixed panes: growing left is clamped at the right pane's minimum", () => {
        const panes = [pane({ id: "a" }), pane({ id: "b", size: 110 })];
        const result = resizeDivider(panes, 0, 50);
        expect(result[0].size).toBe(210);
        expect(result[1].size).toBe(100);
    });

    test("fixed pane next to a growing pane only resizes the fixed pane", () => {
        const panes = [pane({ id: "a" }), pane({ id: "b", grow: true })];
        const result = resizeDivider(panes, 0, 40);
        expect(result[0].size).toBe(240);
        expect(result[1]).toEqual(panes[1]);
    });

    test("growing pane next to a fixed pane only resizes the fixed pane", () => {
        const panes = [pane({ id: "a", grow: true }), pane({ id: "b" })];
        const result = resizeDivider(panes, 0, 40);
        expect(result[0]).toEqual(panes[0]);
        // dragging the divider right (positive delta) shrinks the trailing
        // fixed pane
        expect(result[1].size).toBe(160);
    });

    test("resizing a fixed pane past its minimum stops at the minimum", () => {
        const panes = [pane({ id: "a", grow: true }), pane({ id: "b", size: 110 })];
        const result = resizeDivider(panes, 0, 100);
        expect(result[1].size).toBe(100);
    });

    test("two growing panes: dragging is a no-op", () => {
        const panes = [pane({ id: "a", grow: true }), pane({ id: "b", grow: true })];
        const result = resizeDivider(panes, 0, 40);
        expect(result).toEqual(panes);
    });

    test("collapsed neighbour: dragging is a no-op", () => {
        const panes = [pane({ id: "a", collapsed: true }), pane({ id: "b" })];
        const result = resizeDivider(panes, 0, 40);
        expect(result).toEqual(panes);
    });

    test("hidden neighbour: dragging is a no-op", () => {
        const panes = [pane({ id: "a" }), pane({ id: "b", hidden: true })];
        const result = resizeDivider(panes, 0, 40);
        expect(result).toEqual(panes);
    });
});

describe("lastVisiblePaneId", () => {
    test("returns the trailing pane when all are visible", () => {
        const panes = [pane({ id: "a" }), pane({ id: "b" })];
        expect(lastVisiblePaneId(panes)).toBe("b");
    });

    // The browse view hides its trailing editor pane, and the divider that
    // would otherwise dangle after the table has to go with it.
    test("skips trailing hidden panes", () => {
        const panes = [pane({ id: "a" }), pane({ id: "b", hidden: true })];
        expect(lastVisiblePaneId(panes)).toBe("a");
    });

    test("returns null when every pane is hidden", () => {
        expect(lastVisiblePaneId([pane({ id: "a", hidden: true })])).toBe(null);
    });
});

describe("appliedDividerDelta", () => {
    // Mirrors how a pointer drag is anchored: the delta actually applied,
    // rather than the requested one, is what advances the drag so that
    // overshoot past a min-size boundary is not baked into the origin.
    test("two fixed panes: reports the full delta when unclamped", () => {
        const panes = [pane({ id: "a" }), pane({ id: "b" })];
        const next = resizeDivider(panes, 0, 30);
        expect(appliedDividerDelta(panes, next, 0)).toBe(30);
    });

    test("two fixed panes: reports only the delta applied before the minimum", () => {
        const panes = [pane({ id: "a", size: 110 }), pane({ id: "b" })];
        const next = resizeDivider(panes, 0, -50);
        // left could only give up 10px before hitting its min of 100
        expect(appliedDividerDelta(panes, next, 0)).toBe(-10);
    });

    test("fixed pane trailing a filler: reports the fixed pane's shrink", () => {
        const panes = [pane({ id: "a", grow: true }), pane({ id: "b", size: 110 })];
        const next = resizeDivider(panes, 0, 100);
        // right shrinks from 110 to its min of 100, so only 10px applied
        expect(appliedDividerDelta(panes, next, 0)).toBe(10);
    });

    test("two growing panes: reports zero", () => {
        const panes = [pane({ id: "a", grow: true }), pane({ id: "b", grow: true })];
        const next = resizeDivider(panes, 0, 40);
        expect(appliedDividerDelta(panes, next, 0)).toBe(0);
    });

    test("last pane has no divider: reports zero", () => {
        const panes = [pane({ id: "a" }), pane({ id: "b" })];
        expect(appliedDividerDelta(panes, panes, 1)).toBe(0);
    });
});

describe("toggleCollapsed", () => {
    test("flips only the targeted pane", () => {
        const panes = [pane({ id: "a" }), pane({ id: "b" })];
        const result = toggleCollapsed(panes, "b");
        expect(result[0].collapsed).toBe(false);
        expect(result[1].collapsed).toBe(true);
    });
});

describe("pane layout persistence", () => {
    // Vitest runs these tests under Node, which has no `localStorage` global;
    // stub a minimal in-memory implementation for the pure persistence
    // helpers to read/write against.
    beforeEach(() => {
        const store = new Map<string, string>();
        vi.stubGlobal("localStorage", {
            getItem: (key: string) => store.get(key) ?? null,
            setItem: (key: string, value: string) => store.set(key, value),
            clear: () => store.clear(),
        });
    });

    test("loadPaneLayout falls back to defaults when nothing is stored", () => {
        const defaults = [pane({ id: "a", size: 250 })];
        expect(loadPaneLayout("browse", defaults)).toEqual(defaults);
    });

    test("saved size/collapsed state overlays matching panes by id", () => {
        const defaults = [pane({ id: "a", size: 250 }), pane({ id: "b", size: 300 })];
        savePaneLayout("browse", [
            { ...defaults[0], size: 400, collapsed: true },
            defaults[1],
        ]);

        const loaded = loadPaneLayout("browse", defaults);
        expect(loaded[0].size).toBe(400);
        expect(loaded[0].collapsed).toBe(true);
        expect(loaded[1]).toEqual(defaults[1]);
    });

    test("panes absent from storage keep their default", () => {
        savePaneLayout("browse", [pane({ id: "a", size: 400 })]);
        const defaults = [pane({ id: "a", size: 250 }), pane({ id: "c", size: 300 })];
        const loaded = loadPaneLayout("browse", defaults);
        expect(loaded[0].size).toBe(400);
        expect(loaded[1]).toEqual(defaults[1]);
    });

    test("corrupt storage falls back to defaults", () => {
        localStorage.setItem("splitView:browse", "not json");
        const defaults = [pane({ id: "a" })];
        expect(loadPaneLayout("browse", defaults)).toEqual(defaults);
    });
});
