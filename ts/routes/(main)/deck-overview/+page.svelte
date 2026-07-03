<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<script lang="ts">
    import { getDeckOverviewContent } from "@generated/backend";
    import { onMount } from "svelte";

    import OverviewPage from "./OverviewPage.svelte";
    import type { PageData } from "./$types";

    export let data: PageData;

    let content = data;

    async function refresh(): Promise<void> {
        content = await getDeckOverviewContent({});
    }

    onMount(() => {
        (window as any).refreshDeckOverview = refresh;
        return () => {
            delete (window as any).refreshDeckOverview;
        };
    });
</script>

<OverviewPage {content} />
