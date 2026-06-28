<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<script lang="ts">
    import { addonsReady } from "@generated/backend";
    import { invalidateAll } from "$app/navigation";
    import { onMount } from "svelte";

    import type { PageData } from "./$types";
    import AddonToolbar from "./AddonToolbar.svelte";
    import AddonList from "./AddonList.svelte";

    export let data: PageData;

    globalThis.anki ||= {};
    globalThis.anki.refreshAddons = async (): Promise<void> => {
        await invalidateAll();
    };

    onMount(async () => {
        await addonsReady({});
    });
</script>

<div class="addon-manager">
    <AddonToolbar />
    <AddonList addons={data.addons} />
</div>

<style lang="scss">
    .addon-manager {
        display: flex;
        flex-direction: column;
        height: 100vh;
        padding: 0.75rem;
        box-sizing: border-box;
        gap: 0.5rem;
    }
</style>
