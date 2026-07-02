<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<script lang="ts">
    import * as tr from "@generated/ftl";
    import { bridgeCommand } from "@tslib/bridgecommand";

    import CheckBox from "$lib/components/CheckBox.svelte";
    import EnumSelector from "$lib/components/EnumSelector.svelte";
    import LabelButton from "$lib/components/LabelButton.svelte";

    import { defaultFormatId, defaultOptions, EXPORT_FORMATS } from "./lib";
    import type { PageData } from "./$types";

    export let data: PageData;

    const hasDid = data.did !== null;
    const hasNids = data.nids !== null;

    let formatId = defaultFormatId(hasDid, hasNids);
    $: format = EXPORT_FORMATS[formatId];

    let deckId: bigint = data.did ?? 0n;
    const options = defaultOptions(hasDid);

    const formatChoices = EXPORT_FORMATS.map((f) => ({ label: f.name(), value: f.id }));

    const deckChoices = hasNids
        ? [{ label: tr.exportingSelectedNotes(), value: 0n }]
        : [
              { label: tr.exportingAllDecks(), value: 0n },
              ...data.deckNameIds.map(({ id, name }) => ({ label: name, value: id })),
          ];

    function cancel(): void {
        bridgeCommand("close");
    }

    function submit(): void {
        const chosenDeckId =
            !hasNids && format.showDeckList && deckId ? deckId.toString() : null;
        const payload = {
            formatId,
            deckId: chosenDeckId,
            ...options,
        };
        bridgeCommand(`export:${JSON.stringify(payload)}`);
    }
</script>

<div class="export">
    <div class="row">
        <span class="label">{@html tr.exportingExportFormat()}</span>
        <EnumSelector bind:value={formatId} choices={formatChoices} />
    </div>

    {#if format.showDeckList}
        <div class="row">
            <EnumSelector
                bind:value={deckId}
                choices={deckChoices}
                disabled={hasNids}
            />
        </div>
    {/if}

    <div class="includes">
        <span class="label">{@html tr.exportingInclude()}</span>
        {#if format.showIncludeScheduling}
            <CheckBox bind:value={options.includeScheduling}>
                {tr.exportingIncludeSchedulingInformation()}
            </CheckBox>
        {/if}
        {#if format.showIncludeDeckConfigs}
            <CheckBox bind:value={options.includeDeckConfigs}>
                {tr.exportingIncludeDeckConfigs()}
            </CheckBox>
        {/if}
        {#if format.showIncludeMedia}
            <CheckBox bind:value={options.includeMedia}>
                {tr.exportingIncludeMedia()}
            </CheckBox>
        {/if}
        {#if format.showIncludeHtml}
            <CheckBox bind:value={options.includeHtml}>
                {tr.exportingIncludeHtmlAndMediaReferences()}
            </CheckBox>
        {/if}
        {#if format.showIncludeTags}
            <CheckBox bind:value={options.includeTags}>
                {tr.exportingIncludeTags()}
            </CheckBox>
        {/if}
        {#if format.showIncludeDeck}
            <CheckBox bind:value={options.includeDeck}>
                {tr.exportingIncludeDeck()}
            </CheckBox>
        {/if}
        {#if format.showIncludeNotetype}
            <CheckBox bind:value={options.includeNotetype}>
                {tr.exportingIncludeNotetype()}
            </CheckBox>
        {/if}
        {#if format.showIncludeGuid}
            <CheckBox bind:value={options.includeGuid}>
                {tr.exportingIncludeGuid()}
            </CheckBox>
        {/if}
        {#if format.showLegacySupport}
            <CheckBox bind:value={options.legacySupport}>
                {tr.exportingSupportOlderAnkiVersions()}
            </CheckBox>
        {/if}
    </div>

    <div class="buttons">
        <LabelButton tabbable on:click={cancel}>{tr.actionsCancel()}</LabelButton>
        <LabelButton primary tabbable on:click={submit}>
            {tr.exportingExport()}
        </LabelButton>
    </div>
</div>

<style lang="scss">
    .export {
        display: flex;
        flex-direction: column;
        height: 100vh;
        padding: 0.75rem;
        box-sizing: border-box;
        gap: 0.75rem;
    }

    .row {
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    .includes {
        display: flex;
        flex-direction: column;
        gap: 0.35rem;
        flex: 1;
    }

    .label {
        white-space: nowrap;
    }

    .buttons {
        display: flex;
        justify-content: flex-end;
        gap: 0.5rem;
    }
</style>
