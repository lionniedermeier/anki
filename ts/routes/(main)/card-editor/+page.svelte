<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<script lang="ts">
    import type { PageData } from "./$types";
    import CardTypeEditor from "./CardTypeEditor.svelte";

    let { data }: { data: PageData } = $props();
</script>

<CardTypeEditor
    notetypeNames={data.notetypeNames}
    initialNotetypeId={data.initialNotetypeId}
/>
