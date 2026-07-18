<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<script lang="ts">
    import { goto } from "$app/navigation";
    import type { NotetypeNameIdUseCount } from "@generated/anki/notetypes_pb";
    import * as tr from "@generated/ftl";

    interface Props {
        notetypes: NotetypeNameIdUseCount[];
    }

    let { notetypes }: Props = $props();
</script>

<div class="notetype-list-page">
    <h1>{tr.notetypesNoteTypes()}</h1>
    <ul class="notetype-list">
        {#each notetypes as notetype (notetype.id)}
            <li>
                <button
                    type="button"
                    class="notetype"
                    onclick={() => goto(`/manage-notetypes/${notetype.id}`)}
                >
                    <span class="name">{notetype.name}</span>
                    <span class="count">
                        {tr.browsingNoteCount({ count: notetype.useCount })}
                    </span>
                </button>
            </li>
        {/each}
    </ul>
</div>

<style lang="scss">
    .notetype-list-page {
        display: flex;
        flex-direction: column;
        height: 100%;
        min-height: 0;
        padding: 1rem 1.5rem;

        h1 {
            flex: 0 0 auto;
            font-size: 1.2rem;
            margin-block-end: 0.75rem;
        }
    }

    .notetype-list {
        flex: 1 1 auto;
        min-height: 0;
        overflow-y: auto;
        margin: 0;
        padding: 0;
        list-style: none;
        max-width: 32rem;
    }

    .notetype {
        display: flex;
        width: 100%;
        justify-content: space-between;
        align-items: baseline;
        gap: 0.75rem;
        padding: 0.5rem 0.75rem;
        margin-block-end: 0.25rem;
        border: 1px solid transparent;
        border-radius: 0.35rem;
        background: transparent;
        color: var(--fg);
        text-align: start;
        cursor: pointer;

        &:hover {
            background: var(--canvas-inset);
        }

        .name {
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }

        .count {
            flex: 0 0 auto;
            color: var(--fg-subtle);
            font-size: 0.85em;
        }
    }
</style>
