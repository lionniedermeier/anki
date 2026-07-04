<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<script lang="ts">
    import { onMount } from "svelte";

    import BrowsePage from "./BrowsePage.svelte";
    import type { PageData } from "./$types";

    export let data: PageData;

    let page: BrowsePage;

    onMount(() => {
        (window as any).refreshBrowse = () => page?.refresh();
        return () => {
            delete (window as any).refreshBrowse;
        };
    });
</script>

<BrowsePage
    bind:this={page}
    sidebar={data.sidebar}
    initialSearch={data.initialSearch}
    initialIds={data.initialIds}
/>
