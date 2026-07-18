<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<script lang="ts">
    import * as tr from "@generated/ftl";
    import Modal from "$lib/components/Modal.svelte";
    import type { HistoryEntry } from "./types";
    import { searchInBrowser } from "@generated/backend";

    export let history: HistoryEntry[] = [];
    export let modal: Modal;

    function onEntryClick(entry: HistoryEntry): void {
        searchInBrowser({
            filter: {
                case: "nids",
                value: { ids: [entry.noteId] },
            },
        });
        modal.hide();
    }
</script>

<Modal bind:this={modal}>
    {#snippet header()}
        <div class="modal-header">
            <h5 class="modal-title" id="modalLabel">{tr.addingHistory()}</h5>
            <button
                type="button"
                class="btn-close"
                data-bs-dismiss="modal"
                aria-label="Close"
            ></button>
        </div>
    {/snippet}
    {#snippet body()}
        <div class="modal-body">
            <ul class="history-list">
                {#each history as entry}
                    <li>
                        <button
                            type="button"
                            class="history-entry"
                            on:click={() => onEntryClick(entry)}
                        >
                            {entry.text}
                        </button>
                    </li>
                {/each}
            </ul>
        </div>
    {/snippet}
    {#snippet footer()}
        <div class="modal-footer">
            <button
                type="button"
                class="btn btn-secondary"
                on:click={modal.cancelHandler}
            >
                Cancel
            </button>
        </div>
    {/snippet}
</Modal>

<style lang="scss">
    .history-list {
        list-style: none;
        padding: 0;
        margin: 0;
        max-height: 400px;
        overflow-y: auto;
    }

    .history-list li {
        margin-bottom: 8px;
    }

    .history-list li:last-child {
        margin-bottom: 0;
    }

    .history-entry {
        display: block;
        width: 100%;
        padding: 12px 16px;
        background-color: var(--canvas-elevated);
        border: 1px solid var(--border);
        border-radius: 6px;
        transition: all 0.2s ease;
        font-size: 14px;
        line-height: 1.4;
        word-break: break-word;
        text-align: left;
        color: var(--fg);
        text-decoration: none;
        cursor: pointer;
        position: relative;
    }

    .history-entry::after {
        content: "";
        position: absolute;
        bottom: 8px;
        left: 16px;
        right: 16px;
        height: 1px;
        background-color: var(--fg-link);
        opacity: 0;
        transition: opacity 0.2s ease;
    }

    .history-entry:hover {
        background-color: var(--canvas-elevated-hover);
        border-color: var(--border-strong);
        transform: translateY(-1px);
        color: var(--fg-link);
    }

    .history-entry:hover::after {
        opacity: 0.6;
    }

    .history-entry:active {
        transform: translateY(0px);
    }

    .history-entry:focus {
        outline: 2px solid var(--fg-link);
        outline-offset: 2px;
    }
</style>
