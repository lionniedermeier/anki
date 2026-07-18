<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<script lang="ts">
    import type { Notetype } from "@generated/anki/notetypes_pb";
    import {
        Notetype_Field,
        Notetype_Field_Config,
    } from "@generated/anki/notetypes_pb";
    import * as tr from "@generated/ftl";

    import Icon from "$lib/components/Icon.svelte";
    import { chevronDown, chevronUp } from "$lib/components/icons";
    import IconConstrain from "$lib/components/IconConstrain.svelte";

    interface Props {
        notetype: Notetype;
        save: (mutate: (nt: Notetype) => void) => Promise<void>;
    }

    let { notetype, save }: Props = $props();

    let selectedIdx = $state(0);
    // Clamp the selection after a field is deleted out from under it.
    $effect(() => {
        if (selectedIdx >= notetype.fields.length) {
            selectedIdx = Math.max(0, notetype.fields.length - 1);
        }
    });

    const selectedField = $derived(notetype.fields[selectedIdx] ?? null);

    function validateName(name: string, excludeIdx: number | null): string | null {
        const trimmed = name.trim();
        if (!trimmed) {
            return null;
        }
        if ("#^/".includes(trimmed[0])) {
            alert(tr.fieldsNameFirstLetterNotValid());
            return null;
        }
        if ([...'":{}'].some((char) => trimmed.includes(char))) {
            alert(tr.fieldsNameInvalidLetter());
            return null;
        }
        const clash = notetype.fields.some(
            (field, idx) =>
                idx !== excludeIdx &&
                field.name.toLowerCase() === trimmed.toLowerCase(),
        );
        if (clash) {
            alert(tr.fieldsThatFieldNameIsAlreadyUsed());
            return null;
        }
        return trimmed;
    }

    async function addField(): Promise<void> {
        const input = prompt(tr.fieldsFieldName());
        if (input === null) {
            return;
        }
        const name = validateName(input, null);
        if (!name) {
            return;
        }
        await save((nt) => {
            nt.fields.push(
                new Notetype_Field({ name, config: new Notetype_Field_Config() }),
            );
        });
        selectedIdx = notetype.fields.length - 1;
    }

    async function renameField(): Promise<void> {
        if (!selectedField) {
            return;
        }
        const idx = selectedIdx;
        const input = prompt(tr.actionsNewName(), selectedField.name);
        if (input === null) {
            return;
        }
        const name = validateName(input, idx);
        if (!name || name === selectedField.name) {
            return;
        }
        await save((nt) => {
            nt.fields[idx].name = name;
        });
    }

    async function deleteField(): Promise<void> {
        if (!selectedField) {
            return;
        }
        if (notetype.fields.length < 2) {
            alert(tr.fieldsNotesRequireAtLeastOneField());
            return;
        }
        if (selectedField.config?.preventDeletion) {
            alert(tr.fieldsFieldIsRequired());
            return;
        }
        if (!confirm(tr.fieldsDeleteFieldFrom({ val: selectedField.name }))) {
            return;
        }
        const idx = selectedIdx;
        await save((nt) => {
            nt.fields.splice(idx, 1);
        });
    }

    async function moveField(delta: number): Promise<void> {
        const from = selectedIdx;
        const to = from + delta;
        if (to < 0 || to >= notetype.fields.length) {
            return;
        }
        await save((nt) => {
            const [field] = nt.fields.splice(from, 1);
            nt.fields.splice(to, 0, field);
        });
        selectedIdx = to;
    }

    async function setSortField(idx: number): Promise<void> {
        await save((nt) => {
            if (nt.config) {
                nt.config.sortFieldIdx = idx;
            }
        });
    }

    async function updateConfig(
        mutate: (config: Notetype_Field_Config) => void,
    ): Promise<void> {
        const idx = selectedIdx;
        await save((nt) => {
            const field = nt.fields[idx];
            field.config ??= new Notetype_Field_Config();
            mutate(field.config);
        });
    }
</script>

<div class="field-options">
    <div class="field-list-pane">
        <ul class="field-list">
            {#each notetype.fields as field, idx (idx)}
                <li>
                    <button
                        type="button"
                        class="field-row"
                        class:selected={idx === selectedIdx}
                        onclick={() => (selectedIdx = idx)}
                    >
                        {field.name}
                        {#if notetype.config?.sortFieldIdx === idx}
                            <span
                                class="sort-marker"
                                title={tr.fieldsSortByThisFieldInThe()}
                            >
                                *
                            </span>
                        {/if}
                    </button>
                </li>
            {/each}
        </ul>
        <div class="field-list-actions">
            <button type="button" onclick={addField}>{tr.fieldsAddField()}</button>
            <button type="button" onclick={renameField} disabled={!selectedField}>
                {tr.actionsRename()}
            </button>
            <button type="button" onclick={deleteField} disabled={!selectedField}>
                {tr.actionsDelete()}
            </button>
            <button
                type="button"
                class="icon-button"
                onclick={() => moveField(-1)}
                disabled={selectedIdx <= 0}
                aria-label="Move up"
            >
                <IconConstrain><Icon icon={chevronUp} /></IconConstrain>
            </button>
            <button
                type="button"
                class="icon-button"
                onclick={() => moveField(1)}
                disabled={selectedIdx >= notetype.fields.length - 1}
                aria-label="Move down"
            >
                <IconConstrain><Icon icon={chevronDown} /></IconConstrain>
            </button>
        </div>
    </div>
    {#if selectedField}
        {#key selectedIdx}
            <div class="field-config-pane">
                <label class="text-row">
                    <span>{tr.fieldsFont()}</span>
                    <input
                        type="text"
                        value={selectedField.config?.fontName ?? ""}
                        onchange={(e) => {
                            const value = e.currentTarget.value;
                            updateConfig((c) => (c.fontName = value));
                        }}
                    />
                </label>
                <label class="text-row">
                    <span>{tr.fieldsSize()}</span>
                    <input
                        type="number"
                        min="1"
                        value={selectedField.config?.fontSize ?? 20}
                        onchange={(e) => {
                            const value = Number(e.currentTarget.value) || 20;
                            updateConfig((c) => (c.fontSize = value));
                        }}
                    />
                </label>
                <label class="text-row">
                    <span>{tr.fieldsDescription()}</span>
                    <input
                        type="text"
                        value={selectedField.config?.description ?? ""}
                        onchange={(e) => {
                            const value = e.currentTarget.value;
                            updateConfig((c) => (c.description = value));
                        }}
                    />
                </label>
                <label class="checkbox-row">
                    <input
                        type="checkbox"
                        checked={notetype.config?.sortFieldIdx === selectedIdx}
                        onchange={(e) => {
                            if (e.currentTarget.checked) {
                                setSortField(selectedIdx);
                            } else {
                                // Matches the legacy dialog: the sort field
                                // can be changed, not unset.
                                e.currentTarget.checked = true;
                            }
                        }}
                    />
                    {tr.fieldsSortByThisFieldInThe()}
                </label>
                <label class="checkbox-row">
                    <input
                        type="checkbox"
                        checked={selectedField.config?.rtl ?? false}
                        onchange={(e) => {
                            const checked = e.currentTarget.checked;
                            updateConfig((c) => (c.rtl = checked));
                        }}
                    />
                    {tr.fieldsReverseTextDirectionRtl()}
                </label>
                <label class="checkbox-row">
                    <input
                        type="checkbox"
                        checked={selectedField.config?.plainText ?? false}
                        onchange={(e) => {
                            const checked = e.currentTarget.checked;
                            updateConfig((c) => (c.plainText = checked));
                        }}
                    />
                    {tr.fieldsHtmlByDefault()}
                </label>
                <label class="checkbox-row">
                    <input
                        type="checkbox"
                        checked={selectedField.config?.collapsed ?? false}
                        onchange={(e) => {
                            const checked = e.currentTarget.checked;
                            updateConfig((c) => (c.collapsed = checked));
                        }}
                    />
                    {tr.fieldsCollapseByDefault()}
                </label>
                <label class="checkbox-row">
                    <input
                        type="checkbox"
                        checked={selectedField.config?.excludeFromSearch ?? false}
                        onchange={(e) => {
                            const checked = e.currentTarget.checked;
                            updateConfig((c) => (c.excludeFromSearch = checked));
                        }}
                    />
                    {tr.fieldsExcludeFromSearch()}
                </label>
            </div>
        {/key}
    {/if}
</div>

<style lang="scss">
    .field-options {
        display: flex;
        height: 100%;
        min-height: 0;
    }

    .field-list-pane {
        display: flex;
        flex-direction: column;
        flex: 0 0 16rem;
        min-height: 0;
        border-right: 1px solid var(--border-subtle);
    }

    .field-list {
        flex: 1 1 auto;
        min-height: 0;
        overflow-y: auto;
        margin: 0;
        padding: 0.25rem;
        list-style: none;
    }

    .field-row {
        display: flex;
        justify-content: space-between;
        width: 100%;
        padding: 0.35rem 0.6rem;
        border: 1px solid transparent;
        border-radius: 0.25rem;
        background: transparent;
        color: var(--fg);
        text-align: start;
        cursor: pointer;

        &:hover {
            background: var(--canvas-inset);
        }

        &.selected {
            border-color: var(--border-focus);
            background: var(--canvas-inset);
        }
    }

    .field-list-actions {
        display: flex;
        flex-wrap: wrap;
        gap: 0.35rem;
        padding: 0.5rem;
        border-top: 1px solid var(--border-subtle);

        button {
            appearance: none;
            padding: 0.3rem 0.6rem;
            border: 1px solid var(--border);
            border-radius: 0.3rem;
            background: var(--canvas-elevated);
            color: var(--fg);
            cursor: pointer;

            &:hover:not(:disabled) {
                background: var(--canvas-inset);
            }

            &:disabled {
                opacity: 0.5;
                cursor: default;
            }
        }

        .icon-button {
            padding: 0.3rem;
        }
    }

    .field-config-pane {
        flex: 1 1 auto;
        min-width: 0;
        overflow-y: auto;
        display: flex;
        flex-direction: column;
        gap: 0.6rem;
        padding: 0.75rem 1rem;
        max-width: 28rem;
    }

    .text-row {
        display: flex;
        flex-direction: column;
        gap: 0.2rem;
    }

    .checkbox-row {
        display: flex;
        align-items: center;
        gap: 0.4rem;
    }

    .sort-marker {
        color: var(--fg-subtle);
    }
</style>
