// Copyright: Ankitects Pty Ltd and contributors
// License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import { BrowseSidebarNode, BrowseSidebarNode_NodeType } from "@generated/anki/frontend_pb";
import { BrowserRow_Color } from "@generated/anki/search_pb";
import { describe, expect, test } from "vitest";

import {
    colorVarForRow,
    filterSidebarRows,
    findSidebarRow,
    iconForNodeType,
    sidebarToRows,
    type SidebarRowNode,
} from "./lib";

function makeNode(partial: Partial<BrowseSidebarNode>): BrowseSidebarNode {
    return new BrowseSidebarNode(partial as any);
}

describe("sidebarToRows", () => {
    test("undefined root yields no rows", () => {
        expect(sidebarToRows(undefined)).toEqual([]);
    });

    test("only the root's children become rows, not the synthetic root itself", () => {
        const root = makeNode({
            nodeType: BrowseSidebarNode_NodeType.ROOT,
            children: [
                makeNode({
                    name: "Decks",
                    nodeType: BrowseSidebarNode_NodeType.DECK_ROOT,
                    search: "deck:_*",
                }),
            ],
        });
        const rows = sidebarToRows(root);
        expect(rows).toHaveLength(1);
        expect(rows[0].name).toBe("Decks");
        expect(rows[0].search).toBe("deck:_*");
    });

    test("nested children are converted recursively with stable, unique ids", () => {
        const root = makeNode({
            children: [
                makeNode({
                    name: "Decks",
                    nodeType: BrowseSidebarNode_NodeType.DECK_ROOT,
                    children: [
                        makeNode({
                            name: "Default",
                            nodeType: BrowseSidebarNode_NodeType.DECK,
                            id: 1n,
                        }),
                    ],
                }),
            ],
        });
        const rows = sidebarToRows(root);
        expect(rows[0].children).toHaveLength(1);
        expect(rows[0].children[0].name).toBe("Default");
        // ids are unique across the whole tree
        expect(rows[0].id).not.toBe(rows[0].children[0].id);
    });

    test("collapsed mirrors the inverse of the backend's expanded flag", () => {
        const root = makeNode({
            children: [makeNode({ name: "Tags", expanded: false })],
        });
        expect(sidebarToRows(root)[0].collapsed).toBe(true);
    });

    test("two nodes with the same name/id=0 in different sections still get distinct ids", () => {
        const root = makeNode({
            children: [
                makeNode({
                    name: "Section A",
                    children: [makeNode({ name: "shared" })],
                }),
                makeNode({
                    name: "Section B",
                    children: [makeNode({ name: "shared" })],
                }),
            ],
        });
        const rows = sidebarToRows(root);
        expect(rows[0].children[0].id).not.toBe(rows[1].children[0].id);
    });
});

describe("findSidebarRow", () => {
    test("finds a nested row by id", () => {
        const root = makeNode({
            children: [
                makeNode({
                    name: "Decks",
                    children: [makeNode({ name: "Default", id: 1n })],
                }),
            ],
        });
        const rows = sidebarToRows(root);
        const targetId = rows[0].children[0].id;
        expect(findSidebarRow(rows, targetId)?.name).toBe("Default");
    });

    test("returns undefined for an id that isn't present", () => {
        expect(findSidebarRow([], "missing")).toBeUndefined();
    });
});

describe("filterSidebarRows", () => {
    function row(
        name: string,
        children: SidebarRowNode[] = [],
        collapsed = true,
    ): SidebarRowNode {
        return {
            id: name,
            name,
            nodeType: BrowseSidebarNode_NodeType.DECK,
            search: "",
            collapsed,
            children,
        };
    }

    test("blank query returns rows unchanged, preserving collapsed state", () => {
        const rows = [row("Decks", [row("Default")])];
        expect(filterSidebarRows(rows, "  ")).toBe(rows);
    });

    test("keeps a node whose own name matches, dropping non-matching siblings", () => {
        const rows = [row("Decks"), row("Tags")];
        const filtered = filterSidebarRows(rows, "deck");
        expect(filtered.map((r) => r.name)).toEqual(["Decks"]);
    });

    test("keeps an ancestor chain leading to a matching descendant, expanded", () => {
        const rows = [row("Decks", [row("Japanese", [row("Default")], true)], true)];
        const filtered = filterSidebarRows(rows, "default");
        expect(filtered).toHaveLength(1);
        expect(filtered[0].collapsed).toBe(false);
        expect(filtered[0].children[0].collapsed).toBe(false);
        expect(filtered[0].children[0].children[0].name).toBe("Default");
    });

    test("match is case-insensitive", () => {
        const rows = [row("Decks")];
        expect(filterSidebarRows(rows, "DECK")).toHaveLength(1);
    });

    test("no matches anywhere yields an empty list", () => {
        const rows = [row("Decks", [row("Default")])];
        expect(filterSidebarRows(rows, "nonexistent")).toEqual([]);
    });

    test("does not mutate the original tree", () => {
        const original = row("Decks", [row("Default")], true);
        filterSidebarRows([original], "default");
        expect(original.collapsed).toBe(true);
    });
});

describe("iconForNodeType", () => {
    test("returns an icon for known node types", () => {
        expect(iconForNodeType(BrowseSidebarNode_NodeType.DECK)).not.toBeNull();
    });

    test("returns null for the synthetic root, which has no icon", () => {
        expect(iconForNodeType(BrowseSidebarNode_NodeType.ROOT)).toBeNull();
    });
});

describe("colorVarForRow", () => {
    test("maps flag colors to their CSS custom property", () => {
        expect(colorVarForRow(BrowserRow_Color.FLAG_RED)).toBe("--flag-1");
    });

    test("maps state colors to their CSS custom property", () => {
        expect(colorVarForRow(BrowserRow_Color.SUSPENDED)).toBe("--state-suspended");
    });

    test("returns null for the default (untinted) color", () => {
        expect(colorVarForRow(BrowserRow_Color.DEFAULT)).toBeNull();
    });
});
