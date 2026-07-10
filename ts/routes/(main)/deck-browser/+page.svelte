<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<script lang="ts">
    import {
        getDeckBrowserContent,
        reparentDecks,
        setDeckCollapsed,
    } from "@generated/backend";
    import { SetDeckCollapsedRequest_Scope } from "@generated/anki/decks_pb";
    import * as tr from "@generated/ftl";
    import { bridgeCommand } from "@tslib/bridgecommand";
    import { onMount } from "svelte";

    import { cogIcon } from "$lib/components/icons";
    import Icon from "$lib/components/Icon.svelte";
    import IconButton from "$lib/components/IconButton.svelte";
    import LabelButton from "$lib/components/LabelButton.svelte";
    import TreeView from "$lib/components/TreeView/TreeView.svelte";

    import { countClass, deckTreeToRows, findRow } from "./lib";
    import type { PageData } from "./$types";

    export let data: PageData;

    let rows = deckTreeToRows(data.tree);
    let currentDeckId = data.currentDeckId;
    let studiedToday = data.studiedToday;

    async function refresh(): Promise<void> {
        const content = await getDeckBrowserContent({});
        rows = deckTreeToRows(content.tree);
        currentDeckId = content.currentDeckId;
        studiedToday = content.studiedToday;
    }

    onMount(() => {
        (window as any).refreshDeckBrowser = refresh;
        return () => {
            delete (window as any).refreshDeckBrowser;
        };
    });

    function open(deckId: bigint): void {
        bridgeCommand(`open:${deckId}`);
    }

    function openKeydown(event: KeyboardEvent, deckId: bigint): void {
        if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            open(deckId);
        }
    }

    function openOptions(deckId: bigint): void {
        bridgeCommand(`opts:${deckId}`);
    }

    function toggle(id: string): void {
        const row = findRow(rows, id);
        if (!row) {
            return;
        }
        row.collapsed = !row.collapsed;
        rows = rows;
        setDeckCollapsed({
            deckId: row.deckId,
            collapsed: row.collapsed,
            scope: SetDeckCollapsedRequest_Scope.REVIEWER,
        }).then(() => bridgeCommand("changed"));
    }

    async function dragdrop(sourceId: string, targetId: string | null): Promise<void> {
        await reparentDecks({
            deckIds: [BigInt(sourceId)],
            newParent: targetId ? BigInt(targetId) : 0n,
        });
        // These calls go straight to the backend, bypassing the Python
        // CollectionOp wrapper that normally fires operation_did_execute -
        // tell Python a change happened so the sync status indicator, undo
        // stack, etc. stay in sync.
        bridgeCommand("changed");
        await refresh();
    }

    function createDeck(): void {
        bridgeCommand("create");
    }

    function importFile(): void {
        bridgeCommand("import");
    }

    function getShared(): void {
        bridgeCommand("shared");
    }
</script>

<div class="deck-browser">
    <div class="tree-header">
        <span class="col-name">{tr.decksDeck()}</span>
        <span class="col-count">{tr.actionsNew()}</span>
        <span class="col-count">{tr.decksLearnHeader()}</span>
        <span class="col-count">{tr.decksReviewHeader()}</span>
        <span class="col-opts"></span>
    </div>

    <div class="tree-scroll">
        <TreeView
            nodes={rows}
            topLevelDroppable
            onToggle={toggle}
            onDragdrop={dragdrop}
        >
            {#snippet row(node)}
                <div class="deck-row" class:current={node.deckId === currentDeckId}>
                    <div
                        class="deck-name"
                        class:filtered={node.filtered}
                        role="button"
                        tabindex="0"
                        on:click={() => open(node.deckId)}
                        on:keydown={(event) => openKeydown(event, node.deckId)}
                    >
                        {node.name}
                    </div>
                    <span class={countClass(node.newCount, "new-count")}>
                        {node.newCount}
                    </span>
                    <span class={countClass(node.learnCount, "learn-count")}>
                        {node.learnCount}
                    </span>
                    <span class={countClass(node.reviewCount, "review-count")}>
                        {node.reviewCount}
                    </span>
                    <IconButton
                        tabbable
                        class="deck-opts"
                        tooltip={tr.actionsOptions()}
                        on:click={() => openOptions(node.deckId)}
                    >
                        <Icon icon={cogIcon} />
                    </IconButton>
                </div>
            {/snippet}
            {#snippet topLevel()}
                {tr.decksDropHereToRemoveFromParent()}
            {/snippet}
        </TreeView>
    </div>

    <div class="stats">{studiedToday}</div>

    <div class="bottom-bar">
        <LabelButton tabbable on:click={createDeck}>
            {tr.decksCreateDeck()}
        </LabelButton>
        <LabelButton tabbable on:click={importFile}>
            {tr.decksImportFile()}
        </LabelButton>
        <LabelButton tabbable on:click={getShared}>
            {tr.decksGetShared()}
        </LabelButton>
    </div>
</div>

<style lang="scss">
    @use "../../../lib/sass/card-counts";

    .deck-browser {
        display: flex;
        flex-direction: column;
        height: 100%;
        padding: 0.5rem 1rem;
        gap: 0.25rem;
    }

    .tree-header,
    .deck-row {
        display: grid;
        grid-template-columns: 1fr 3rem 3rem 3rem 2.5rem;
        align-items: center;
        column-gap: 0.5rem;
        width: 100%;
    }

    .tree-header {
        flex: none;
        font-weight: bold;
        padding-block: 0.25rem;
        border-bottom: 1px solid var(--border-subtle);
    }

    .tree-scroll {
        flex: 1;
        min-height: 0;
        overflow-y: auto;
        overflow-x: hidden;
    }

    .col-count {
        text-align: end;
    }

    .deck-row {
        min-width: 0;
    }

    .deck-name {
        min-width: 0;
        padding: 8px 0;
        text-align: start;
        overflow: hidden;
        white-space: nowrap;
        text-overflow: ellipsis;
        cursor: pointer;
        user-select: none;
    }

    .deck-name.filtered {
        font-style: italic;
    }

    .current .deck-name {
        font-weight: bold;
    }

    .deck-row :global(.deck-opts) {
        visibility: hidden;
    }

    .deck-row:hover :global(.deck-opts),
    .deck-row :global(.deck-opts):focus-visible {
        visibility: visible;
    }

    .new-count,
    .learn-count,
    .review-count,
    .zero-count {
        text-align: end;
        user-select: none;
    }

    .stats {
        flex: none;
        margin-top: 1rem;
        text-align: center;
    }

    .bottom-bar {
        flex: none;
        display: flex;
        justify-content: center;
        gap: 0.5rem;
        margin-top: 1rem;
        padding-top: 0.5rem;
        border-top: 1px solid var(--border-subtle);
    }
</style>
