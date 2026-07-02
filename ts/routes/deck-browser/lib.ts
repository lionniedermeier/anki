// Copyright: Ankitects Pty Ltd and contributors
// License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import type { DeckTreeNode } from "@generated/anki/decks_pb";

import type { TreeViewNode } from "$lib/components/TreeView/TreeView";

export interface DeckRowNode extends TreeViewNode {
    deckId: bigint;
    name: string;
    newCount: number;
    learnCount: number;
    reviewCount: number;
    filtered: boolean;
    children: DeckRowNode[];
}

function toRow(node: DeckTreeNode): DeckRowNode {
    return {
        id: node.deckId.toString(),
        deckId: node.deckId,
        name: node.name,
        collapsed: node.collapsed,
        newCount: node.newCount,
        learnCount: node.learnCount,
        reviewCount: node.reviewCount,
        filtered: node.filtered,
        draggable: true,
        droppable: true,
        children: node.children.map(toRow),
    };
}

/** The root DeckTreeNode is a synthetic node with no useful fields of its
 * own; only its children are real top-level decks. */
export function deckTreeToRows(root: DeckTreeNode | undefined): DeckRowNode[] {
    return root ? root.children.map(toRow) : [];
}

export function findRow(rows: DeckRowNode[], id: string): DeckRowNode | undefined {
    for (const row of rows) {
        if (row.id === id) {
            return row;
        }
        const found = findRow(row.children, id);
        if (found) {
            return found;
        }
    }
    return undefined;
}

/** Empty string when zero, so the caller can style zero-count cells
 * differently, matching the pre-migration deck browser. */
export function countClass(count: number, nonZeroClass: string): string {
    return count === 0 ? "zero-count" : nonZeroClass;
}
