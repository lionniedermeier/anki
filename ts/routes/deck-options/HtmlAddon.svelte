<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<script lang="ts">
    import { onMount } from "svelte";

    interface Props {
        html: string;
        mounted: () => void;
    }

    let { html, mounted }: Props = $props();

    onMount(() => mounted());
</script>

{@html html}
