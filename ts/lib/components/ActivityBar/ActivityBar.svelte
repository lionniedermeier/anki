<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<script lang="ts">
    export let id: string | undefined = undefined;
    let className = "";
    export { className as class };

    /** Lay items out in a column (VSCode-style) rather than a row. */
    export let vertical = true;
</script>

<div
    {id}
    class="activity-bar {className}"
    class:vertical
    class:horizontal={!vertical}
    role="tablist"
    aria-orientation={vertical ? "vertical" : "horizontal"}
>
    <slot />
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
