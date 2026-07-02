// Copyright: Ankitects Pty Ltd and contributors
// License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

export interface TreeViewNode {
    id: string;
    collapsed: boolean;
    children: TreeViewNode[];
    /** Whether this row can be dragged. Defaults to false. */
    draggable?: boolean;
    /** Whether other rows can be dropped onto this row. Defaults to true. */
    droppable?: boolean;
}

export interface VisibleRow<T extends TreeViewNode> {
    node: T;
    depth: number;
}

/** Flattens a nested tree into the rows currently visible (i.e. not hidden
 * behind a collapsed ancestor), depth-first. */
export function flattenVisible<T extends TreeViewNode>(
    nodes: T[],
    depth = 0,
): VisibleRow<T>[] {
    const rows: VisibleRow<T>[] = [];
    for (const node of nodes) {
        rows.push({ node, depth });
        if (!node.collapsed && node.children.length > 0) {
            rows.push(...flattenVisible(node.children as T[], depth + 1));
        }
    }
    return rows;
}

/** Collects the id of `node` and of all its descendants. Used to reject drop
 * targets that lie inside the dragged subtree (a node can't be reparented
 * onto itself or its own descendant). */
export function collectSubtreeIds(node: TreeViewNode): Set<string> {
    const ids = new Set<string>();
    const stack: TreeViewNode[] = [node];
    while (stack.length > 0) {
        const current = stack.pop()!;
        ids.add(current.id);
        stack.push(...current.children);
    }
    return ids;
}
