<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<script lang="ts">
    import * as tr from "@generated/ftl";
    import { bridgeCommand } from "@tslib/bridgecommand";
    import { onMount } from "svelte";

    import LabelButton from "$lib/components/LabelButton.svelte";

    import type { PageData } from "./$types";

    export let data: PageData;

    let deckName = data.deck.name;

    function choose(): void {
        bridgeCommand("choose");
    }

    onMount(() => {
        // Allow the Python host to update the displayed name when the deck is
        // changed programmatically, renamed, or selected via the picker.
        (window as any).updateDeckChooser = (name: string) => {
            deckName = name;
        };
        return () => {
            delete (window as any).updateDeckChooser;
        };
    });
</script>

<div class="deck-chooser">
    {#if data.showLabel}
        <span class="label">{tr.decksDeck()}</span>
    {/if}
    <LabelButton
        tabbable
        ellipsis
        class="deck-button"
        tooltip={tr.qtMiscTargetDeckCtrlandd()}
        on:click={choose}>{deckName}</LabelButton
    >
</div>

<style lang="scss">
    :global(html, body) {
        background: transparent;
        margin: 0;
        padding: 0;
        overflow: hidden;
    }

    .deck-chooser {
        display: flex;
        align-items: center;
        gap: 8px;
        width: 100%;
    }

    .label {
        white-space: nowrap;
    }

    .deck-chooser :global(.deck-button) {
        flex: 1;
        min-width: 0;
        text-align: start;
    }
</style>
