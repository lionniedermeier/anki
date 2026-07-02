<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<script lang="ts">
    import type { Addon } from "@generated/anki/addons_pb";

    import AddonItem from "./AddonItem.svelte";

    export let addons: Addon[];
</script>

<div class="addon-list">
    {#each addons as addon (addon.dirName)}
        <AddonItem {addon} />
    {/each}
    {#if addons.length === 0}
        <div class="empty-state">No add-ons installed.</div>
    {/if}
</div>

<style lang="scss">
    .addon-list {
        flex: 1;
        overflow-y: auto;
        border: 1px solid var(--border);
        border-radius: var(--border-radius);
    }

    .empty-state {
        padding: 2rem;
        text-align: center;
        color: var(--fg-subtle);
    }
</style>
