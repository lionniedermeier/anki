<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<script lang="ts">
    import type { Snippet } from "svelte";

    interface Props {
        id?: string;
        role?: string;
        selected?: boolean;
        class?: string;
        buttonRef?: HTMLButtonElement;
        tooltip?: string;
        active?: boolean;
        disabled?: boolean;
        tabbable?: boolean;
        children?: Snippet;
        onmouseenter?: (e: MouseEvent) => void;
        onfocus?: (e: FocusEvent) => void;
        onkeydown?: (e: KeyboardEvent) => void;
        onclick?: (e: MouseEvent) => void;
        onmousedown?: (e: MouseEvent) => void;
    }

    let {
        id = undefined,
        role = undefined,
        selected = false,
        class: className = "",
        buttonRef = $bindable(undefined),
        tooltip = undefined,
        active = false,
        disabled = false,
        tabbable = false,
        children,
        onmouseenter,
        onfocus,
        onkeydown,
        onclick,
        onmousedown,
    }: Props = $props();

    const rtl: boolean = window.getComputedStyle(document.body).direction == "rtl";

    $effect(() => {
        if (buttonRef && active) {
            buttonRef!.scrollIntoView({
                behavior: "smooth",
                block: "nearest",
            });
        }
    });

    function handleMousedown(e: MouseEvent) {
        e.preventDefault();
        onmousedown?.(e);
    }
</script>

<button
    bind:this={buttonRef}
    {id}
    {role}
    aria-selected={selected}
    tabindex={tabbable ? 0 : -1}
    class="dropdown-item {className}"
    class:active
    class:rtl
    title={tooltip}
    {disabled}
    {onmouseenter}
    {onfocus}
    {onkeydown}
    {onclick}
    onmousedown={handleMousedown}
>
    {@render children?.()}
</button>

<style lang="scss">
    button {
        display: flex;
        justify-content: start;
        width: 100%;
        padding: 0.25rem 1rem;
        white-space: nowrap;
        font-size: var(--dropdown-font-size, small);

        background: none;
        box-shadow: none !important;
        border: none;
        border-radius: 4px;
        color: var(--fg);

        &:hover {
            border: none;
        }

        &:hover:not([disabled]) {
            background: var(--highlight-bg);
            color: var(--highlight-fg);
        }

        &.focus {
            // TODO this is subtly different from hovering with the mouse for some reason
            @extend button, :hover;
        }

        &[disabled] {
            cursor: default;
            color: var(--fg-disabled);
        }

        &.active {
            &:not(.rtl) {
                border-left-color: var(--border-focus);
            }
            &.rtl {
                border-right-color: var(--border-focus);
            }
        }
    }
</style>
