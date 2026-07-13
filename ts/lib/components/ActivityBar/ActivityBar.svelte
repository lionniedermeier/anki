<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<script lang="ts">
    import type { Snippet } from "svelte";

    interface ActivityBarProps {
        id?: string;
        class?: string;
        /** Lay items out in a column rather than a row. */
        vertical?: boolean;
        children?: Snippet;
    }

    let {
        id,
        class: className = "",
        vertical = true,
        children,
    }: ActivityBarProps = $props();
</script>

<div
    {id}
    class="activity-bar {className}"
    class:vertical
    class:horizontal={!vertical}
    role="tablist"
    aria-orientation={vertical ? "vertical" : "horizontal"}
>
    {@render children?.()}
</div>

<style lang="scss">
    .activity-bar {
        display: flex;
        flex-shrink: 0;

        &.vertical {
            flex-direction: column;
            width: var(--activity-bar-size, 3rem);
        }

        &.horizontal {
            flex-direction: row;
            height: var(--activity-bar-size, 3rem);
        }
    }
</style>
