// Copyright: Ankitects Pty Ltd and contributors
// License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import { DeckTreeNode } from "@generated/anki/decks_pb";
import { describe, expect, test } from "vitest";

import { countClass, deckTreeToRows, findRow } from "./lib";

function makeNode(partial: Partial<DeckTreeNode>): DeckTreeNode {
    return new DeckTreeNode(partial as any);
}

describe("deckTreeToRows", () => {
    test("undefined root yields no rows", () => {
        expect(deckTreeToRows(undefined)).toEqual([]);
    });

    test("only the root's children become rows, not the root itself", () => {
        const root = makeNode({
            deckId: 0n,
            name: "",
            children: [makeNode({ deckId: 1n, name: "Deck 1" })],
        });
        const rows = deckTreeToRows(root);
        expect(rows).toHaveLength(1);
        expect(rows[0].id).toBe("1");
        expect(rows[0].name).toBe("Deck 1");
    });

    test("nested children are converted recursively", () => {
        const root = makeNode({
            children: [
                makeNode({
                    deckId: 1n,
                    name: "Parent",
                    children: [makeNode({ deckId: 2n, name: "Child" })],
                }),
            ],
        });
        const rows = deckTreeToRows(root);
        expect(rows[0].children).toHaveLength(1);
        expect(rows[0].children[0].id).toBe("2");
    });

    test("counts, collapsed and filtered flags are carried over", () => {
        const root = makeNode({
            children: [
                makeNode({
                    deckId: 1n,
                    name: "Deck 1",
                    newCount: 5,
                    learnCount: 2,
                    reviewCount: 10,
                    collapsed: true,
                    filtered: true,
                }),
            ],
        });
        const row = deckTreeToRows(root)[0];
        expect(row.newCount).toBe(5);
        expect(row.learnCount).toBe(2);
        expect(row.reviewCount).toBe(10);
        expect(row.collapsed).toBe(true);
        expect(row.filtered).toBe(true);
    });

    test("rows are draggable and droppable by default", () => {
        const root = makeNode({ children: [makeNode({ deckId: 1n, name: "Deck 1" })] });
        const row = deckTreeToRows(root)[0];
        expect(row.draggable).toBe(true);
        expect(row.droppable).toBe(true);
    });
});

describe("findRow", () => {
    const rows = deckTreeToRows(
        makeNode({
            children: [
                makeNode({
                    deckId: 1n,
                    name: "Parent",
                    children: [makeNode({ deckId: 2n, name: "Child" })],
                }),
            ],
        }),
    );

    test("finds a top-level row", () => {
        expect(findRow(rows, "1")?.name).toBe("Parent");
    });

    test("finds a nested row", () => {
        expect(findRow(rows, "2")?.name).toBe("Child");
    });

    test("returns undefined for an unknown id", () => {
        expect(findRow(rows, "999")).toBeUndefined();
    });
});

describe("countClass", () => {
    test("returns zero-count for a zero count", () => {
        expect(countClass(0, "new-count")).toBe("zero-count");
    });

    test("returns the provided class for a non-zero count", () => {
        expect(countClass(3, "new-count")).toBe("new-count");
    });
});
