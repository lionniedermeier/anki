<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<script lang="ts">
    import type { PageData } from "./$types";
    import NotetypeList from "./NotetypeList.svelte";

    let { data }: { data: PageData } = $props();
</script>

<NotetypeList notetypes={data.notetypes} />
