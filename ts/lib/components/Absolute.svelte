<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<script lang="ts">
    import type { Snippet } from "svelte";

    interface AbsoluteProps {
        top?: boolean;
        bottom?: boolean;
        left?: boolean;
        right?: boolean;
        children?: Snippet;
    }

    let {
        top = false,
        bottom = false,
        left = false,
        right = false,
        children,
    }: AbsoluteProps = $props();
</script>

<div class="absolute" class:top class:bottom class:left class:right>
    {@render children?.()}
</div>

<style lang="scss">
    .absolute {
        position: absolute;
        margin: var(--margin, 0);
        z-index: 20;
    }

    .top {
        top: 0;
    }

    .bottom {
        bottom: 0;
    }

    .left {
        left: 0;
    }

    .right {
        right: 0;
    }
</style>
