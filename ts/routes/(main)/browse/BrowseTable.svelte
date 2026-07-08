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
    import { createEventDispatcher, onMount, untrack } from "svelte";

    import ColumnResizeHandle from "$lib/components/VirtualTable/ColumnResizeHandle.svelte";
    import VirtualTable from "$lib/components/VirtualTable/VirtualTable.svelte";
    import {
        loadColumnWidths,
        saveColumnWidths,
    } from "$lib/components/VirtualTable/VirtualTable";

    import { colorVarForRow } from "./lib";

    interface Props {
        ids: bigint[];
        notesMode: boolean;
        selectedIds?: Set<string>;
        onSort?: (detail: { column: string }) => void;
    }

    let {
        ids,
        notesMode,
        /** Selected row ids (as strings, since bigint doesn't work well as a Set
         * key across reactive re-renders). Exposed so a future editor/preview
         * pane can bind to the current selection. */
        selectedIds = $bindable(new Set<string>()),
        onSort,
    }: Props = $props();

    const dispatch = createEventDispatcher<{ sort: { column: string } }>();

    const ROW_HEIGHT = 30;
    const DEFAULT_COLUMN_WIDTH = 150;
    // Matches pylib/anki/browser.py's BrowserDefaults; column customization
    // (persisting the user's chosen active columns) is deferred for now.
    const DEFAULT_CARD_COLUMNS = ["noteFld", "template", "cardDue", "deck"];
    const DEFAULT_NOTE_COLUMNS = ["noteFld", "note", "template", "noteTags"];

    let allColumns = $state(new Map<string, BrowserColumns_Column>());
    let rowCache = $state(new Map<string, BrowserRow>());
    let lastAnchor: string | null = null;
    // Last-known visible window, so a new search/mode switch can re-fetch it
    // directly instead of relying on VirtualTable's `visible` event to
    // re-fire (see fetchMissing's doc comment for why that can't be trusted).
    let visibleRange = $state({ start: 0, end: 0 });

    onMount(async () => {
        const result = await allBrowserColumns({});
        allColumns = new Map(result.columns.map((column) => [column.key, column]));
    });

    let activeKeys = $derived(notesMode ? DEFAULT_NOTE_COLUMNS : DEFAULT_CARD_COLUMNS);
    let activeColumns = $derived(
        activeKeys
            .map((key) => allColumns.get(key))
            .filter((column): column is BrowserColumns_Column => Boolean(column)),
    );
    let idStrings = $derived(ids.map((id) => id.toString()));

    // Cards and Notes mode both happen to have 4 columns, so a single
    // storage key could carry sizes from one mode's columns over to the
    // other's; keep them separate per mode instead.
    let columnWidthsViewId = $derived(
        notesMode ? "browseTableNotes" : "browseTableCards",
    );
    let columnWidths: number[] = $state([]);
    // Only (re)load when the mode's view id or the column count actually
    // changes - not on every reactive tick - so a live drag (which mutates
    // columnWidths[i]) isn't immediately clobbered by a reload.
    let loadedWidthsFor = $state("");

    $effect(() => {
        if (
            activeColumns.length > 0 &&
            `${columnWidthsViewId}:${activeColumns.length}` !== loadedWidthsFor
        ) {
            loadedWidthsFor = `${columnWidthsViewId}:${activeColumns.length}`;
            columnWidths = loadColumnWidths(
                columnWidthsViewId,
                activeColumns.map(() => DEFAULT_COLUMN_WIDTH),
            );
        }
    });

    function onColumnResizeCommit(): void {
        saveColumnWidths(columnWidthsViewId, columnWidths);
    }

    let prevIds: bigint[] | null = null;

    $effect(() => {
        // Track ids AND the visible window: a new search/mode switch changes
        // ids, and measurement/scrolling changes visibleRange. Both must drive
        // a fetch. Everything touching rowCache stays inside untrack so the
        // read (.has) and writes below don't register as dependencies, which
        // is what caused the cascade.
        const currentIds = ids;
        const { start, end } = visibleRange;

        untrack(() => {
            // Reset only when the id list itself changed, not merely because
            // the window scrolled, otherwise every scroll throws away the cache.
            if (currentIds !== prevIds) {
                prevIds = currentIds;
                rowCache = new Map();
            }
            fetchMissing(start, end);
        });
    });

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
        // VirtualTable re-emits `visible` on every render, including the
        // re-renders that fetchMissing itself triggers by writing rowCache.
        // Reassigning visibleRange to a fresh object each time (even with an
        // unchanged window) would re-run the fetch effect and cascade into an
        // update loop, so bail out when the window hasn't actually moved. The
        // fetch itself is left to the effect that tracks visibleRange, keeping
        // a single fetch trigger.
        if (range.start === visibleRange.start && range.end === visibleRange.end) {
            return;
        }
        visibleRange = range;
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
                    onclick={() => sortBy(column.key)}
                    onkeydown={(event) => onHeaderKeydown(event, column.key)}
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
        <!-- svelte-ignore a11y_click_events_have_key_events, a11y_no_static_element_interactions -->
        <div
            class="vg-row"
            class:selected={selectedIds.has(id)}
            style={rowStyle(rowData)}
            onclick={(event) => onRowClick(event, id, index)}
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
