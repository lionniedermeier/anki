// Copyright: Ankitects Pty Ltd and contributors
// License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import { BrowseSidebarNode_NodeType } from "@generated/anki/frontend_pb";
import type { BrowseSidebarNode } from "@generated/anki/frontend_pb";
import { BrowserRow_Color } from "@generated/anki/search_pb";

import {
    applicationBracesOutlineIcon,
    bookClockOutlineIcon,
    bookOutlineIcon,
    circleIcon,
    circleOutlineIcon,
    clockOutlineIcon,
    flagVariantIcon,
    flagVariantOffOutlineIcon,
    flagVariantOutlineIcon,
    formTextboxIcon,
    heartOutlineIcon,
    newspaperIcon,
    tagIcon,
    tagOffOutlineIcon,
} from "$lib/components/icons";
import type { TreeViewNode } from "$lib/components/TreeView/TreeView";
import type { IconData } from "$lib/components/types";

export interface SidebarRowNode extends TreeViewNode {
    name: string;
    nodeType: BrowseSidebarNode_NodeType;
    /** Parsable search string; empty for nodes that aren't directly
     * searchable (e.g. the synthetic root). */
    search: string;
    /** Flag index (1-7), only set for NodeType.FLAG rows. */
    flagIndex?: number;
    children: SidebarRowNode[];
}

const NodeType = BrowseSidebarNode_NodeType;

function toRow(node: BrowseSidebarNode, parentPath: string, index: number): SidebarRowNode {
    const key = node.id !== 0n ? node.id.toString() : node.name || `i${index}`;
    const id = `${parentPath}/${node.nodeType}:${key}`;
    return {
        id,
        name: node.name,
        nodeType: node.nodeType,
        search: node.search,
        flagIndex: node.nodeType === NodeType.FLAG ? Number(node.id) : undefined,
        collapsed: !node.expanded,
        children: node.children.map((child, childIndex) => toRow(child, id, childIndex)),
    };
}

/** The root BrowseSidebarNode is a synthetic node with no useful fields of
 * its own; only its children (the section roots) are real rows. */
export function sidebarToRows(root: BrowseSidebarNode | undefined): SidebarRowNode[] {
    return root ? root.children.map((child, index) => toRow(child, "root", index)) : [];
}

export function findSidebarRow(
    rows: SidebarRowNode[],
    id: string,
): SidebarRowNode | undefined {
    for (const row of rows) {
        if (row.id === id) {
            return row;
        }
        const found = findSidebarRow(row.children, id);
        if (found) {
            return found;
        }
    }
    return undefined;
}

/** Returns a filtered view of `rows` for the sidebar's own name filter,
 * keeping a node if its name matches `query` or any descendant's does, and
 * force-expanding kept branches so matches are visible. Returns `rows`
 * as-is (respecting each node's own collapsed state) when `query` is blank.
 * Operates on shallow copies so the caller's underlying tree/collapsed
 * state is untouched. */
export function filterSidebarRows(
    rows: SidebarRowNode[],
    query: string,
): SidebarRowNode[] {
    const trimmed = query.trim().toLowerCase();
    if (!trimmed) {
        return rows;
    }

    function filterNode(node: SidebarRowNode): SidebarRowNode | null {
        const children = node.children
            .map(filterNode)
            .filter((child): child is SidebarRowNode => child !== null);
        const selfMatches = node.name.toLowerCase().includes(trimmed);
        if (!selfMatches && children.length === 0) {
            return null;
        }
        return { ...node, collapsed: false, children };
    }

    return rows.map(filterNode).filter((node): node is SidebarRowNode => node !== null);
}

const sidebarIcons: Partial<Record<BrowseSidebarNode_NodeType, IconData>> = {
    [NodeType.SAVED_SEARCH_ROOT]: heartOutlineIcon,
    [NodeType.SAVED_SEARCH]: heartOutlineIcon,
    [NodeType.TODAY_ROOT]: clockOutlineIcon,
    [NodeType.TODAY]: clockOutlineIcon,
    [NodeType.FLAG_ROOT]: flagVariantOutlineIcon,
    [NodeType.FLAG]: flagVariantIcon,
    [NodeType.FLAG_NONE]: flagVariantOffOutlineIcon,
    [NodeType.CARD_STATE_ROOT]: circleOutlineIcon,
    [NodeType.CARD_STATE]: circleIcon,
    [NodeType.DECK_ROOT]: bookOutlineIcon,
    [NodeType.DECK_CURRENT]: bookClockOutlineIcon,
    [NodeType.DECK]: bookOutlineIcon,
    [NodeType.NOTETYPE_ROOT]: newspaperIcon,
    [NodeType.NOTETYPE]: newspaperIcon,
    [NodeType.NOTETYPE_TEMPLATE]: applicationBracesOutlineIcon,
    [NodeType.NOTETYPE_FIELD]: formTextboxIcon,
    [NodeType.TAG_ROOT]: tagIcon,
    [NodeType.TAG]: tagIcon,
    [NodeType.TAG_NONE]: tagOffOutlineIcon,
};

export function iconForNodeType(nodeType: BrowseSidebarNode_NodeType): IconData | null {
    return sidebarIcons[nodeType] ?? null;
}

/** CSS custom property backing a flag row's icon color, or null for
 * non-flag rows (and the "Flags"/"No Flag" rows, which stay neutral). */
export function flagColorVarForRow(row: SidebarRowNode): string | null {
    return row.nodeType === NodeType.FLAG && row.flagIndex
        ? `--flag-${row.flagIndex}`
        : null;
}

/** Card state rows aren't tagged with which state they represent, so this
 * keys off their search string, which the backend derives 1:1 from the
 * state (see `write_state` in rslib/src/search/writer.rs). */
const cardStateColorVars: Partial<Record<string, string>> = {
    "is:new": "--state-new",
    "is:learn": "--state-learn",
    "is:review": "--state-review",
    "is:suspended": "--state-suspended",
    "is:buried": "--state-buried",
};

/** CSS custom property backing a card-state row's icon color, or null for
 * non-card-state rows (and the "Card State" section root, which stays
 * neutral). */
export function cardStateColorVarForRow(row: SidebarRowNode): string | null {
    return row.nodeType === NodeType.CARD_STATE
        ? cardStateColorVars[row.search] ?? null
        : null;
}

const colorVars: Partial<Record<BrowserRow_Color, string>> = {
    [BrowserRow_Color.MARKED]: "--state-marked",
    [BrowserRow_Color.SUSPENDED]: "--state-suspended",
    [BrowserRow_Color.BURIED]: "--state-buried",
    [BrowserRow_Color.FLAG_RED]: "--flag-1",
    [BrowserRow_Color.FLAG_ORANGE]: "--flag-2",
    [BrowserRow_Color.FLAG_GREEN]: "--flag-3",
    [BrowserRow_Color.FLAG_BLUE]: "--flag-4",
    [BrowserRow_Color.FLAG_PINK]: "--flag-5",
    [BrowserRow_Color.FLAG_TURQUOISE]: "--flag-6",
    [BrowserRow_Color.FLAG_PURPLE]: "--flag-7",
};

/** CSS custom property backing a row's background tint, or null for the
 * default (untinted) row. */
export function colorVarForRow(color: BrowserRow_Color): string | null {
    return colorVars[color] ?? null;
}
