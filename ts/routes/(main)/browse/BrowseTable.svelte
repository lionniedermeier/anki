<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<script lang="ts">
    import {
        allBrowserColumns,
        getBrowserRows,
        setActiveBrowserColumns,
        setConfigBool,
    } from "@generated/backend";
    import { ConfigKey_Bool } from "@generated/anki/config_pb";
    import type { BrowserColumns_Column, BrowserRow } from "@generated/anki/search_pb";
    import { createEventDispatcher, onMount } from "svelte";

    import ColumnResizeHandle from "$lib/components/VirtualTable/ColumnResizeHandle.svelte";
    import VirtualTable from "$lib/components/VirtualTable/VirtualTable.svelte";
    import { loadColumnWidths, saveColumnWidths } from "$lib/components/VirtualTable/VirtualTable";

    import { colorVarForRow } from "./lib";

    export let ids: bigint[];
    export let notesMode: boolean;
    /** Selected row ids (as strings, since bigint doesn't work well as a Set
     * key across reactive re-renders). Exposed so a future editor/preview
     * pane can bind to the current selection. */
    export let selectedIds = new Set<string>();

    const dispatch = createEventDispatcher<{ sort: { column: string } }>();

    const ROW_HEIGHT = 30;
    const DEFAULT_COLUMN_WIDTH = 150;
    // Matches pylib/anki/browser.py's BrowserDefaults; column customization
    // (persisting the user's chosen active columns) is deferred for now.
    const DEFAULT_CARD_COLUMNS = ["noteFld", "template", "cardDue", "deck"];
    const DEFAULT_NOTE_COLUMNS = ["noteFld", "note", "template", "noteTags"];

    let allColumns = new Map<string, BrowserColumns_Column>();
    let rowCache = new Map<string, BrowserRow>();
    let lastAnchor: string | null = null;
    // Last-known visible window, so a new search/mode switch can re-fetch it
    // directly instead of relying on VirtualTable's `visible` event to
    // re-fire (see fetchMissing's doc comment for why that can't be trusted).
    let visibleRange = { start: 0, end: 0 };

    onMount(async () => {
        const result = await allBrowserColumns({});
        allColumns = new Map(result.columns.map((column) => [column.key, column]));
    });

    $: activeKeys = notesMode ? DEFAULT_NOTE_COLUMNS : DEFAULT_CARD_COLUMNS;
    $: activeColumns = activeKeys
        .map((key) => allColumns.get(key))
        .filter((column): column is BrowserColumns_Column => Boolean(column));
    $: idStrings = ids.map((id) => id.toString());

    // Cards and Notes mode both happen to have 4 columns, so a single
    // storage key could carry sizes from one mode's columns over to the
    // other's; keep them separate per mode instead.
    $: columnWidthsViewId = notesMode ? "browseTableNotes" : "browseTableCards";
    let columnWidths: number[] = [];
    // Only (re)load when the mode's view id or the column count actually
    // changes - not on every reactive tick - so a live drag (which mutates
    // columnWidths[i]) isn't immediately clobbered by a reload.
    let loadedWidthsFor = "";
    $: if (
        activeColumns.length > 0
        && `${columnWidthsViewId}:${activeColumns.length}` !== loadedWidthsFor
    ) {
        loadedWidthsFor = `${columnWidthsViewId}:${activeColumns.length}`;
        columnWidths = loadColumnWidths(
            columnWidthsViewId,
            activeColumns.map(() => DEFAULT_COLUMN_WIDTH),
        );
    }

    function onColumnResizeCommit(): void {
        saveColumnWidths(columnWidthsViewId, columnWidths);
    }

    // `ids` is reassigned by the parent on every new search or mode switch,
    // so keying the cache reset off it also covers mode changes (which
    // always come with a fresh search). Re-fetching the visible window here
    // (rather than waiting for VirtualTable's `visible` event) is required:
    // Svelte's reactive statements skip re-running dependents when an
    // intermediate computed value (VirtualTable's `endIndex`) happens to
    // equal its previous value, which is common when old and new result
    // counts both exceed the visible window - so `visible` isn't a reliable
    // signal that the underlying ids changed.
    $: if (ids) {
        rowCache = new Map();
        fetchMissing(visibleRange.start, visibleRange.end);
    }

    async function fetchMissing(start: number, end: number): Promise<void> {
        const visible = idStrings.slice(start, end);
        const missing = visible.filter((id) => !rowCache.has(id));
        if (missing.length === 0) {
            return;
        }
        await setActiveBrowserColumns({ vals: activeKeys });
        // browser_row_for_id interprets the given ids as card or note ids
        // based on this stored flag, not on anything passed to the RPC
        // itself - it must be kept in sync before fetching rows, exactly
        // like the active columns above.
        await setConfigBool({
            key: ConfigKey_Bool.BROWSER_TABLE_SHOW_NOTES_MODE,
            value: notesMode,
            undoable: false,
        });
        const response = await getBrowserRows({ ids: missing.map((id) => BigInt(id)) });
        const next = new Map(rowCache);
        missing.forEach((id, index) => next.set(id, response.rows[index]));
        rowCache = next;
    }

    function onVisible(range: { start: number; end: number }): void {
        visibleRange = range;
        fetchMissing(visibleRange.start, visibleRange.end);
    }

    function labelFor(column: BrowserColumns_Column): string {
        return notesMode ? column.notesModeLabel : column.cardsModeLabel;
    }

    function cellText(row: BrowserRow | undefined, index: number): string {
        return row?.cells[index]?.text ?? "";
    }

    function rowStyle(row: BrowserRow | undefined): string {
        const cssVar = row && colorVarForRow(row.color);
        return cssVar ? `background: var(${cssVar});` : "";
    }

    function onRowClick(event: MouseEvent, id: string, index: number): void {
        const next = new Set(selectedIds);
        if (event.shiftKey && lastAnchor !== null) {
            const anchorIndex = idStrings.indexOf(lastAnchor);
            const [start, end] =
                anchorIndex < index ? [anchorIndex, index] : [index, anchorIndex];
            for (let i = start; i <= end; i++) {
                next.add(idStrings[i]);
            }
        } else if (event.ctrlKey || event.metaKey) {
            if (next.has(id)) {
                next.delete(id);
            } else {
                next.add(id);
            }
            lastAnchor = id;
        } else {
            next.clear();
            next.add(id);
            lastAnchor = id;
        }
        selectedIds = next;
    }

    function sortBy(key: string): void {
        dispatch("sort", { column: key });
    }

    function onHeaderKeydown(event: KeyboardEvent, key: string): void {
        if (event.key === "Enter" || event.key === " ") {
            sortBy(key);
            event.preventDefault();
        }
    }
</script>

<VirtualTable
    class="browse-table"
    itemsCount={idStrings.length}
    itemHeight={ROW_HEIGHT}
    bind:columnWidths
    onvisible={onVisible}
>
    {#snippet headers()}
        <div class="vg-row">
            {#each activeColumns as column, i (column.key)}
                <div
                    class="vg-cell header-cell"
                    role="columnheader"
                    tabindex="0"
                    on:click={() => sortBy(column.key)}
                    on:keydown={(event) => onHeaderKeydown(event, column.key)}
                >
                    {labelFor(column)}
                    <ColumnResizeHandle
                        bind:width={columnWidths[i]}
                        on:commit={onColumnResizeCommit}
                    />
                </div>
            {/each}
        </div>
    {/snippet}
    {#snippet row(index)}
        {@const id = idStrings[index]}
        {@const rowData = rowCache.get(id)}
        <!-- Rows are click-selectable; keyboard-based selection is a separate
        feature not yet migrated, so no keydown handler / focus role here. -->
        <!-- svelte-ignore a11y-click-events-have-key-events a11y-no-static-element-interactions -->
        <div
            class="vg-row"
            class:selected={selectedIds.has(id)}
            style={rowStyle(rowData)}
            on:click={(event) => onRowClick(event, id, index)}
        >
            {#each activeColumns as column, columnIndex (column.key)}
                <div class="vg-cell">{cellText(rowData, columnIndex)}</div>
            {/each}
        </div>
    {/snippet}
</VirtualTable>

<style lang="scss">
    :global(.browse-table) {
        height: 100%;
    }

    .vg-row {
        cursor: pointer;

        &.selected {
            background: var(--selected-bg);
            color: var(--selected-fg);
        }
    }

    .header-cell {
        cursor: pointer;
        user-select: none;
    }
</style>
