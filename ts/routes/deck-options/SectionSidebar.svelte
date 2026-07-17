<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<script lang="ts">
    import type { TreeViewNode } from "$lib/components/TreeView/TreeView";
    import TreeView from "$lib/components/TreeView/TreeView.svelte";

    import type { SectionNode } from "./sections";

    interface SectionRow extends TreeViewNode {
        title: string;
        children: SectionRow[];
    }

    interface SectionSidebarProps {
        /** Already narrowed to the current query. */
        nodes: SectionNode[];
        selectedId: string | null;
        onSelect: (id: string) => void;
    }

    let { nodes, selectedId, onSelect }: SectionSidebarProps = $props();

    let collapsedIds: string[] = $state([]);
    // The tree's own cursor: unlike `selectedId` (the section actually shown
    // in the settings pane, which only ever names a leaf), this is allowed to
    // rest on a group heading while the user is navigating with the keyboard.
    let cursorId: string | null = $state(null);

    $effect(() => {
        cursorId = selectedId;
    });

    const rows = $derived(toRows(nodes));

    function toRows(nodes: SectionNode[]): SectionRow[] {
        return nodes.map((node) => ({
            id: node.id,
            title: node.title(),
            collapsed: collapsedIds.includes(node.id),
            children: node.children ? toRows(node.children) : [],
        }));
    }

    function toggle(id: string): void {
        collapsedIds = collapsedIds.includes(id)
            ? collapsedIds.filter((collapsed) => collapsed !== id)
            : [...collapsedIds, id];
    }

    /** Groups have no counterpart in the settings list, so clicking one takes
     * you to the first section below it. */
    function firstSectionId(rows: SectionRow[], id: string): string | null {
        for (const row of rows) {
            if (row.id === id) {
                return row.children.length
                    ? firstSectionId(row.children, row.children[0].id)
                    : row.id;
            }
            const found = firstSectionId(row.children, id);
            if (found) {
                return found;
            }
        }
        return null;
    }

    function findRow(rows: SectionRow[], id: string): SectionRow | null {
        for (const row of rows) {
            if (row.id === id) {
                return row;
            }
            const found = findRow(row.children, id);
            if (found) {
                return found;
            }
        }
        return null;
    }

    function select(id: string, source: "pointer" | "keyboard"): void {
        if (source === "keyboard") {
            // Let the keyboard cursor rest on a group heading (e.g. after
            // navigating to a parent) instead of bouncing straight back into
            // its first child - only jump the settings pane when the cursor
            // actually lands on a real section.
            cursorId = id;
            if (findRow(rows, id)?.children.length === 0) {
                onSelect(id);
            }
            return;
        }
        const sectionId = firstSectionId(rows, id);
        if (sectionId) {
            cursorId = sectionId;
            onSelect(sectionId);
        }
    }
</script>

<div class="section-sidebar">
    <div class="tree-scroll">
        <TreeView nodes={rows} selectedId={cursorId} onToggle={toggle} onSelect={select}>
            {#snippet row(node)}
                <span class="section-row">{node.title}</span>
            {/snippet}
        </TreeView>
    </div>
</div>

<style lang="scss">
    .section-sidebar {
        display: flex;
        flex-direction: column;
        height: 100%;
        min-height: 0;
    }

    .tree-scroll {
        flex: 1 1 auto;
        min-height: 0;
        overflow-y: auto;
        overflow-x: hidden;
        padding: 0.25rem;
        --tree-row-height: 28px;
    }

    .section-row {
        display: block;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
</style>
