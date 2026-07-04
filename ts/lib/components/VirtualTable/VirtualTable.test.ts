// Copyright: Ankitects Pty Ltd and contributors
// License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import { beforeEach, describe, expect, test, vi } from "vitest";

import { computeVisibleRange, loadColumnWidths, saveColumnWidths } from "./VirtualTable";

describe("computeVisibleRange", () => {
    test("empty list yields an empty range", () => {
        expect(computeVisibleRange(0, 300, 30, 0)).toEqual({ startIndex: 0, endIndex: 0 });
    });

    test("scrolled within range returns a window sized to fit the container", () => {
        expect(computeVisibleRange(0, 90, 30, 100)).toEqual({ startIndex: 0, endIndex: 3 });
        expect(computeVisibleRange(60, 90, 30, 100)).toEqual({ startIndex: 2, endIndex: 5 });
    });

    test("scrolled past the end of a shrunk list clamps to itemsCount", () => {
        expect(computeVisibleRange(3000, 90, 30, 10)).toEqual({
            startIndex: 10,
            endIndex: 10,
        });
    });

    test("window is clamped exactly at itemsCount when near the end", () => {
        expect(computeVisibleRange(240, 90, 30, 10)).toEqual({ startIndex: 8, endIndex: 10 });
    });
});

describe("column width persistence", () => {
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

    test("loadColumnWidths falls back to defaults when nothing is stored", () => {
        expect(loadColumnWidths("browseTable", [100, 150])).toEqual([100, 150]);
    });

    test("saved widths round-trip", () => {
        saveColumnWidths("browseTable", [120, 200]);
        expect(loadColumnWidths("browseTable", [100, 150])).toEqual([120, 200]);
    });

    test("stored length mismatch (e.g. column set changed) falls back to defaults", () => {
        saveColumnWidths("browseTable", [120, 200, 80]);
        expect(loadColumnWidths("browseTable", [100, 150])).toEqual([100, 150]);
    });

    test("corrupt storage falls back to defaults", () => {
        localStorage.setItem("columnWidths:browseTable", "not json");
        expect(loadColumnWidths("browseTable", [100, 150])).toEqual([100, 150]);
    });
});
