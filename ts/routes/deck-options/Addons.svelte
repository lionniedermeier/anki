<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<script lang="ts">
    import { untrack } from "svelte";
    import type { DeckOptionsState } from "./lib";
    import SettingsSection from "./SettingsSection.svelte";

    interface Props {
        state: DeckOptionsState;
    }

    let { state: deckState }: Props = $props();

    const components = untrack(() => deckState.addonComponents);
    const auxData = untrack(() => deckState.currentAuxData);
</script>

{#if $components.length}
    <SettingsSection title="Add-ons">
        {#each $components as addon}
            <addon.component bind:data={$auxData} {...addon} />
        {/each}
    </SettingsSection>
{/if}
