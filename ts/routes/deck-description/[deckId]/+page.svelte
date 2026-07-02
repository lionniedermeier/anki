<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<script lang="ts">
    import { updateDeck } from "@generated/backend";
    import * as tr from "@generated/ftl";
    import { bridgeCommand } from "@tslib/bridgecommand";

    import CheckBox from "$lib/components/CheckBox.svelte";
    import LabelButton from "$lib/components/LabelButton.svelte";

    import type { PageData } from "./$types";

    export let data: PageData;

    const deck = data.deck;
    const normal = deck.kind.case === "normal" ? deck.kind.value : undefined;

    let description = normal?.description ?? "";
    let markdown = normal?.markdownDescription ?? false;

    async function save(): Promise<void> {
        if (normal) {
            normal.description = description;
            normal.markdownDescription = markdown;
            await updateDeck(deck);
        }
        bridgeCommand("close");
    }

    function cancel(): void {
        bridgeCommand("close");
    }
</script>

<div class="deck-description">
    <label class="markdown" title={tr.deckConfigDescriptionNewHandlingHint()}>
        <CheckBox bind:value={markdown} />
        {tr.deckConfigDescriptionNewHandling()}
    </label>

    <textarea class="description" bind:value={description}></textarea>

    <div class="buttons">
        <LabelButton tabbable on:click={cancel}>{tr.actionsCancel()}</LabelButton>
        <LabelButton primary tabbable on:click={save}>{tr.actionsSave()}</LabelButton>
    </div>
</div>

<style lang="scss">
    .deck-description {
        display: flex;
        flex-direction: column;
        height: 100vh;
        padding: 0.75rem;
        box-sizing: border-box;
        gap: 0.5rem;
    }

    .markdown {
        display: flex;
        align-items: center;
        gap: 0.25rem;
    }

    .description {
        flex: 1;
        resize: none;
        width: 100%;
        box-sizing: border-box;
    }

    .buttons {
        display: flex;
        justify-content: flex-end;
        gap: 0.5rem;
    }
</style>
