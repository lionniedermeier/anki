<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<script lang="ts">
    import { createEventDispatcher } from "svelte";
    import * as tr from "@generated/ftl";

    import Icon from "$lib/components/Icon.svelte";
    import IconConstrain from "$lib/components/IconConstrain.svelte";
    import { magnifyIcon } from "$lib/components/icons";
    import TreeView from "$lib/components/TreeView/TreeView.svelte";

    import {
        filterSidebarRows,
        findSidebarRow,
        iconForNodeType,
        type SidebarRowNode,
    } from "./lib";

    export let rows: SidebarRowNode[];

    let filterText = "";
    let selectedId: string | null = null;

    $: displayRows = filterSidebarRows(rows, filterText);

    const dispatch = createEventDispatcher<{ search: { search: string } }>();

    function toggle(id: string): void {
        const row = findSidebarRow(rows, id);
        if (!row) {
            return;
        }
        row.collapsed = !row.collapsed;
        rows = rows;
    }

    function select(id: string): void {
        selectedId = id;
        const row = findSidebarRow(rows, id);
        if (row?.search) {
            dispatch("search", { search: row.search });
        }
    }
</script>

<div class="browse-sidebar">
    <div class="toolbar">
        <IconConstrain>
            <Icon icon={magnifyIcon} />
        </IconConstrain>
        <input
            type="text"
            class="filter-input"
            placeholder={tr.browsingSidebarFilter()}
            bind:value={filterText}
        />
    </div>
    <div class="tree-scroll">
        <TreeView nodes={displayRows} {selectedId} onToggle={toggle} onSelect={select}>
            {#snippet row(node)}
                {@const icon = iconForNodeType(node.nodeType)}
                <div class="sidebar-row">
                    {#if icon}
                        <IconConstrain>
                            <Icon {icon} />
                        </IconConstrain>
                    {/if}
                    <span class="sidebar-row-name">{node.name}</span>
                </div>
            {/snippet}
        </TreeView>
    </div>
</div>

<style lang="scss">
    .browse-sidebar {
        display: flex;
        flex-direction: column;
        height: 100%;
        min-height: 0;
    }

    .toolbar {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        flex: none;
        padding: 0.5rem;
        border-bottom: 1px solid var(--border-subtle);
    }

    .filter-input {
        flex: 1 1 auto;
        min-width: 0;
    }

    .tree-scroll {
        flex: 1 1 auto;
        min-height: 0;
        overflow-y: auto;
        overflow-x: hidden;
        padding: 0.25rem;
    }

    .sidebar-row {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        min-width: 0;
        padding: 4px 0;
    }

    .sidebar-row-name {
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
</style>
