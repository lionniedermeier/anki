<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<script lang="ts">
    import type { PlainMessage } from "@bufbuild/protobuf";
    import {
        buildSearchString,
        getBrowseSidebar,
        searchCards,
        searchNotes,
    } from "@generated/backend";
    import type { BrowseSidebarNode } from "@generated/anki/frontend_pb";
    import type { SortOrder } from "@generated/anki/search_pb";
    import * as tr from "@generated/ftl";

    import Icon from "$lib/components/Icon.svelte";
    import IconConstrain from "$lib/components/IconConstrain.svelte";
    import { magnifyIcon } from "$lib/components/icons";
    import SplitPane from "$lib/components/SplitView/SplitPane.svelte";
    import SplitView from "$lib/components/SplitView/SplitView.svelte";
    import Switch from "$lib/components/Switch.svelte";

    import BrowseEditor from "./BrowseEditor.svelte";
    import BrowseSidebar from "./BrowseSidebar.svelte";
    import BrowseTable from "./BrowseTable.svelte";
    import { sidebarToRows, type SidebarRowNode } from "./lib";

    export let sidebar: BrowseSidebarNode;
    export let initialSearch: string;
    export let initialIds: bigint[];

    let rows: SidebarRowNode[] = sidebarToRows(sidebar);
    let searchText = initialSearch;
    let notesMode = false;
    let previousMode = notesMode;
    let ids = initialIds;
    let sortColumn: string | null = null;
    let sortReverse = false;
    let selectedIds = new Set<string>();

    // The editor only makes sense for a single note, so it is hidden when
    // nothing or more than one row is selected.
    $: selectedRowId =
        selectedIds.size === 1 ? BigInt(selectedIds.values().next().value!) : null;

    export async function refresh(): Promise<void> {
        sidebar = await getBrowseSidebar({});
        rows = sidebarToRows(sidebar);
        await runSearch(searchText);
    }

    function order(): PlainMessage<SortOrder> {
        return sortColumn
            ? {
                  value: {
                      case: "builtin",
                      value: { column: sortColumn, reverse: sortReverse },
                  },
              }
            : { value: { case: "none", value: {} } };
    }

    async function runSearch(text: string): Promise<void> {
        const request = { search: text, order: order() };
        const result = notesMode
            ? await searchNotes(request)
            : await searchCards(request);
        ids = result.ids;
        searchText = text;
    }

    async function onSearchSubmit(): Promise<void> {
        try {
            const normalized = await buildSearchString({
                filter: { case: "parsableText", value: searchText },
            });
            await runSearch(normalized.val);
        } catch {
            // Invalid search - leave the results and search text as-is,
            // matching the legacy browser's behaviour.
        }
    }

    function onSidebarSearch(event: CustomEvent<{ search: string }>): void {
        runSearch(event.detail.search);
    }

    function onSort(detail: { column: string }): void {
        if (sortColumn === detail.column) {
            sortReverse = !sortReverse;
        } else {
            sortColumn = detail.column;
            sortReverse = false;
        }
        runSearch(searchText);
    }

    $: if (notesMode !== previousMode) {
        previousMode = notesMode;
        // Row ids switch between card and note ids with the mode, so carrying
        // the old ones over would resolve to unrelated notes.
        selectedIds = new Set();
        runSearch(searchText);
    }
</script>

<div class="browse-page">
    <div class="content">
        <SplitView id="browse" direction="horizontal">
            <SplitPane id="browse-sidebar" size={260} min={180} collapsible={false}>
                <BrowseSidebar {rows} on:search={onSidebarSearch} />
            </SplitPane>
            <SplitPane id="browse-table" grow collapsible={false}>
                <div class="table-pane">
                    <div class="toolbar">
                        <label class="mode-toggle">
                            <span>{tr.browsingCards()}</span>
                            <Switch id="browse-mode-switch" bind:value={notesMode} />
                            <span>{tr.browsingNotes()}</span>
                        </label>
                        <IconConstrain>
                            <Icon icon={magnifyIcon} />
                        </IconConstrain>
                        <input
                            type="text"
                            class="search-input"
                            bind:value={searchText}
                            on:keydown={(event) =>
                                event.key === "Enter" && onSearchSubmit()}
                        />
                    </div>
                    <div class="table-content">
                        <BrowseTable {ids} {notesMode} bind:selectedIds {onSort} />
                    </div>
                </div>
            </SplitPane>
            <!-- Hidden rather than unrendered: NoteEditor is only ever torn
            down with the page it owns, so its teardown throws outside add mode,
            and each fresh mount would re-register a backend operation handler
            that is never removed. -->
            <SplitPane
                id="browse-editor"
                size={420}
                min={280}
                collapsible={false}
                hidden={selectedRowId === null}
            >
                <BrowseEditor rowId={selectedRowId} {notesMode} />
            </SplitPane>
        </SplitView>
    </div>
</div>

<style lang="scss">
    .browse-page {
        display: flex;
        flex-direction: column;
        height: 100%;
        min-height: 0;
    }

    .content {
        flex: 1 1 auto;
        min-height: 0;
        height: 100%;
    }

    .table-pane {
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

    .search-input {
        flex: 1 1 auto;
        min-width: 0;
    }

    .mode-toggle {
        display: flex;
        align-items: center;
        gap: 0.25rem;
        flex: none;
    }

    .table-content {
        flex: 1 1 auto;
        min-height: 0;
    }
</style>
