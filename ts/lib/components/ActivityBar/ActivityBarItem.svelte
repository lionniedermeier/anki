<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<script lang="ts">
    import type { Snippet } from "svelte";

    interface Props {
        id?: string;
        class?: string;
        active?: boolean;
        disabled?: boolean;
        tooltip?: string;
        onclick?: (event: MouseEvent) => void;
        children?: Snippet;
    }

    let {
        id,
        class: className = "",
        active = false,
        disabled = false,
        tooltip,
        onclick,
        children,
    }: Props = $props();

    function onkeydown() {}
</script>

<!-- svelte-ignore a11y_click_events_have_key_events -->
<div
    {id}
    class="activity-bar-item {className}"
    class:active
    title={tooltip}
    role="tab"
    tabindex="0"
    aria-selected={active}
    {onclick}
>
    {@render children?.()}
</div>

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
