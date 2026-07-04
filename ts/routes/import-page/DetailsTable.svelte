<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<script lang="ts">
    import * as tr from "@generated/ftl";

    import Icon from "$lib/components/Icon.svelte";
    import IconButton from "$lib/components/IconButton.svelte";
    import { magnifyIcon } from "$lib/components/icons";
    import ColumnResizeHandle from "$lib/components/VirtualTable/ColumnResizeHandle.svelte";
    import VirtualTable from "$lib/components/VirtualTable/VirtualTable.svelte";
    import { loadColumnWidths, saveColumnWidths } from "$lib/components/VirtualTable/VirtualTable";

    import { getRows, showInBrowser } from "./lib";
    import TableCellWithTooltip from "./TableCellWithTooltip.svelte";
    import type { SummarizedLogQueues } from "./types";

    export let summaries: SummarizedLogQueues[];
    export let bottomOffset: number = 0;

    const VIEW_ID = "importDetailsTable";

    let bottom: HTMLElement;
    $: rows = getRows(summaries);

    let columnWidths = loadColumnWidths(VIEW_ID, [50, 90, 400, 50]);

    function onColumnResizeCommit(): void {
        saveColumnWidths(VIEW_ID, columnWidths);
    }
</script>

<div bind:this={bottom}>
    {#if bottom}
        <VirtualTable
            class="details-table"
            itemHeight={40}
            itemsCount={rows.length}
            bind:columnWidths
            {bottomOffset}
        >
            {#snippet headers()}
                <div class="vg-row">
                    <div class="vg-cell">
                        #
                        <ColumnResizeHandle bind:width={columnWidths[0]} on:commit={onColumnResizeCommit} />
                    </div>
                    <div class="vg-cell">
                        {tr.importingStatus()}
                        <ColumnResizeHandle bind:width={columnWidths[1]} on:commit={onColumnResizeCommit} />
                    </div>
                    <div class="vg-cell">
                        {tr.editingFields()}
                        <ColumnResizeHandle bind:width={columnWidths[2]} on:commit={onColumnResizeCommit} />
                    </div>
                    <div class="vg-cell">
                        <ColumnResizeHandle bind:width={columnWidths[3]} on:commit={onColumnResizeCommit} />
                    </div>
                </div>
            {/snippet}
            {#snippet row(index)}
                <div class="vg-row">
                    <div class="vg-cell index-cell">{index + 1}</div>
                    <TableCellWithTooltip
                        class="status-cell"
                        tooltip={rows[index].queue.reason}
                    >
                        {rows[index].summary.action}
                    </TableCellWithTooltip>
                    <TableCellWithTooltip
                        class="contents-cell"
                        tooltip={rows[index].note.fields.join(",")}
                    >
                        {rows[index].note.fields.join(",")}
                    </TableCellWithTooltip>
                    <div class="vg-cell search-cell">
                        <IconButton
                            class="search-icon"
                            iconSize={100}
                            active={false}
                            disabled={!rows[index].summary.canBrowse}
                            on:click={() => {
                                showInBrowser([rows[index].note]);
                            }}
                        >
                            <Icon icon={magnifyIcon} />
                        </IconButton>
                    </div>
                </div>
            {/snippet}
        </VirtualTable>
    {/if}
</div>

<style lang="scss">
    :global(.details-table) {
        margin: 0 auto;

        :global(.search-icon) {
            border: none !important;
            background: transparent !important;
        }
        .vg-row {
            text-align: center;
        }
        :global(.contents-cell) {
            text-align: left;
        }
    }
</style>
