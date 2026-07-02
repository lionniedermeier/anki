<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<script lang="ts">
    export let id: string | undefined = undefined;
    let className = "";
    export { className as class };

    export let active = false;
    export let disabled = false;
    export let tooltip: string | undefined = undefined;
</script>

<button
    {id}
    class="activity-bar-item {className}"
    class:active
    title={tooltip}
    {disabled}
    role="tab"
    aria-selected={active}
    on:click
>
    <slot />
</button>

<style lang="scss">
    .activity-bar-item {
        position: relative;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
        width: 100%;
        aspect-ratio: 1;
        padding: 0;
        border: none;
        background: none;
        color: var(--fg-subtle);
        cursor: pointer;

        &:hover {
            color: var(--fg);
        }

        &.active {
            color: var(--fg);

            &::before {
                content: "";
                position: absolute;
                inset-inline-start: 0;
                inset-block: 0.5rem;
                width: 2px;
                background: var(--border-focus);
            }
        }

        &:disabled {
            cursor: default;
            opacity: 0.5;
        }
    }
</style>
