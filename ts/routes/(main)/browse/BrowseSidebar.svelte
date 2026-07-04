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
    import LabelButton from "$lib/components/LabelButton.svelte";
    import TreeView from "$lib/components/TreeView/TreeView.svelte";

    import {
        filterSidebarRows,
        findSidebarRow,
        iconForNodeType,
        type SidebarRowNode,
    } from "./lib";

    export let rows: SidebarRowNode[];

    let filterText = "";

    $: displayRows = filterSidebarRows(rows, filterText);

    const dispatch = createEventDispatcher<{ search: { search: string } }>();

    function toggle(event: CustomEvent<{ id: string }>): void {
        const row = findSidebarRow(rows, event.detail.id);
        if (!row) {
            return;
        }
        row.collapsed = !row.collapsed;
        rows = rows;
    }

    function select(row: SidebarRowNode): void {
        if (row.search) {
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
        <TreeView nodes={displayRows} on:toggle={toggle}>
            <svelte:fragment slot="row" let:node>
                {@const row = node as SidebarRowNode}
                {@const icon = iconForNodeType(row.nodeType)}
                <LabelButton
                    tabbable
                    ellipsis
                    class="sidebar-row"
                    on:click={() => select(row)}
                >
                    {#if icon}
                        <IconConstrain>
                            <Icon {icon} />
                        </IconConstrain>
                    {/if}
                    {row.name}
                </LabelButton>
            </svelte:fragment>
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
        padding: 0.25rem 0.5rem;
    }

    :global(.sidebar-row) {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        width: 100%;
        text-align: start;
        padding: 4px 0;
    }
</style>
