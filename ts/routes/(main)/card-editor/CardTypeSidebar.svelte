<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<script lang="ts">
    import type {
        Notetype_Template,
        NotetypeNameId,
    } from "@generated/anki/notetypes_pb";

    import Select from "$lib/components/Select.svelte";

    interface Props {
        notetypeNames: NotetypeNameId[];
        selectedNotetypeId: bigint | null;
        templates: Notetype_Template[];
        selectedOrd: number | null;
        /** Request switching to another notetype (may be vetoed by the parent
         * when there are unsaved edits, so selection is not bound directly). */
        onSelectNotetype: (id: bigint) => void;
        /** Request switching to another card template. */
        onSelectTemplate: (ord: number | null) => void;
    }

    let {
        notetypeNames,
        selectedNotetypeId,
        templates,
        selectedOrd,
        onSelectNotetype,
        onSelectTemplate,
    }: Props = $props();

    const selectedName = $derived(
        notetypeNames.find((n) => n.id === selectedNotetypeId)?.name ?? "",
    );
</script>

<div class="sidebar">
    <div class="chooser">
        <Select
            class="notetype-select"
            list={notetypeNames}
            value={selectedNotetypeId}
            on:change={(e) => onSelectNotetype(e.detail.value)}
            parser={(notetype) => ({
                content: notetype.name,
                value: notetype.id,
            })}
            label={selectedName}
        />
    </div>

    <ul class="card-type-list">
        {#each templates as template, index (template.ord?.val ?? index)}
            <li>
                <button
                    type="button"
                    class="card-type"
                    class:selected={template.ord?.val === selectedOrd}
                    onclick={() => onSelectTemplate(template.ord?.val ?? null)}
                >
                    {template.name}
                </button>
            </li>
        {/each}
    </ul>
</div>

<style lang="scss">
    .sidebar {
        display: flex;
        flex-direction: column;
        height: 100%;
        min-height: 0;
        background: var(--canvas);
    }

    .chooser {
        padding: 0.5rem;
        border-bottom: 1px solid var(--border-subtle);

        :global(.notetype-select) {
            width: 100%;
        }
    }

    .card-type-list {
        flex: 1 1 auto;
        min-height: 0;
        overflow-y: auto;
        margin: 0;
        padding: 0.25rem;
        list-style: none;
    }

    .card-type {
        display: block;
        width: 100%;
        padding: 0.4rem 0.6rem;
        text-align: start;
        border: 1px solid transparent;
        border-radius: 0.25rem;
        background: transparent;
        color: var(--fg);
        cursor: pointer;

        &:hover {
            background: var(--canvas-inset);
        }

        &.selected {
            border-color: var(--border-focus);
            background: var(--canvas-inset);
        }
    }
</style>
