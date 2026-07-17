// Copyright: Ankitects Pty Ltd and contributors
// License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import { describe, expect, test } from "vitest";

import {
    collectSubtreeIds,
    flattenVisible,
    parentIndex,
    type TreeViewNode,
} from "./TreeView";

function node(
    id: string,
    children: TreeViewNode[] = [],
    collapsed = false,
): TreeViewNode {
    return { id, collapsed, children };
}

describe("flattenVisible", () => {
    test("flat list with no children", () => {
        const rows = flattenVisible([node("a"), node("b")]);
        expect(rows).toEqual([
            { node: node("a"), depth: 0 },
            { node: node("b"), depth: 0 },
        ]);
    });

    test("expanded children are included at depth + 1", () => {
        const tree = [node("a", [node("a1"), node("a2")])];
        const rows = flattenVisible(tree);
        expect(rows.map((r) => [r.node.id, r.depth])).toEqual([
            ["a", 0],
            ["a1", 1],
            ["a2", 1],
        ]);
    });

    test("collapsed nodes hide their children", () => {
        const tree = [node("a", [node("a1")], true)];
        const rows = flattenVisible(tree);
        expect(rows.map((r) => r.node.id)).toEqual(["a"]);
    });

    test("collapsed grandchildren stay hidden even if the child is expanded", () => {
        const tree = [node("a", [node("a1", [node("a1-1")], true)])];
        const rows = flattenVisible(tree);
        expect(rows.map((r) => r.node.id)).toEqual(["a", "a1"]);
    });

    test("multiple nested levels are walked depth-first", () => {
        const tree = [
            node("a", [node("a1", [node("a1-1")])]),
            node("b"),
        ];
        const rows = flattenVisible(tree);
        expect(rows.map((r) => [r.node.id, r.depth])).toEqual([
            ["a", 0],
            ["a1", 1],
            ["a1-1", 2],
            ["b", 0],
        ]);
    });
});

describe("collectSubtreeIds", () => {
    test("a leaf node yields only its own id", () => {
        expect(collectSubtreeIds(node("a"))).toEqual(new Set(["a"]));
    });

    test("includes the node and all descendants", () => {
        const tree = node("a", [node("a1", [node("a1-1")]), node("a2")]);
        expect(collectSubtreeIds(tree)).toEqual(
            new Set(["a", "a1", "a1-1", "a2"]),
        );
    });
});

describe("parentIndex", () => {
    test("a first child resolves to the parent", () => {
        const rows = flattenVisible([node("a", [node("a1"), node("a2")])]);
        expect(parentIndex(rows, 1)).toBe(0);
    });

    test("a later child also resolves to the parent, not a sibling", () => {
        const rows = flattenVisible([node("a", [node("a1"), node("a2")])]);
        expect(parentIndex(rows, 2)).toBe(0);
    });

    test("three levels deep resolves to the immediate parent, not the grandparent", () => {
        const rows = flattenVisible([
            node("a", [node("a1", [node("a11"), node("a12")])]),
        ]);
        expect(parentIndex(rows, 2)).toBe(1); // a11 -> a1
        expect(parentIndex(rows, 3)).toBe(1); // a12 -> a1, skipping a11
    });

    test("a top-level node has no parent", () => {
        const rows = flattenVisible([node("a"), node("b")]);
        expect(parentIndex(rows, 0)).toBeNull();
        expect(parentIndex(rows, 1)).toBeNull();
    });
});
