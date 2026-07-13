<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<script lang="ts">
    import type { Snippet } from "svelte";

    interface RenderChildrenProps {
        children?: Snippet;
    }

    let { children }: RenderChildrenProps = $props();
</script>

{@render children?.()}
