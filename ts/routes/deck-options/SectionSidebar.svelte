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

    /** Groups have no counterpart in the settings list, so selecting one takes
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

    function select(id: string): void {
        const sectionId = firstSectionId(rows, id);
        if (sectionId) {
            onSelect(sectionId);
        }
    }
</script>

<div class="section-sidebar">
    <div class="tree-scroll">
        <TreeView nodes={rows} {selectedId} onToggle={toggle} onSelect={select}>
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
