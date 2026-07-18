<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<script lang="ts">
    import { createEventDispatcher, onMount } from "svelte";

    let className: string = "";
    export { className as class };

    export let tagName: string; // used by add-ons to target individual tag elements
    export let tooltip: string | undefined = undefined;
    export let selected = false;

    const dispatch = createEventDispatcher();

    let flashing: boolean = false;

    export function flash(): void {
        flashing = true;
        setTimeout(() => (flashing = false), 300);
    }

    let button: HTMLButtonElement;

    onMount(() => dispatch("mount", { button }));
</script>

<button
    bind:this={button}
    class="tag d-inline-flex align-items-center text-nowrap ps-2 pe-1 {className}"
    class:selected
    class:flashing
    tabindex="-1"
    title={tooltip}
    data-addon-tag={tagName}
    on:mousemove
    on:click
>
    <slot />
</button>

<style lang="scss">
    @keyframes flash {
        0% {
            filter: invert(0);
        }
        50% {
            filter: invert(0.4);
        }
        100% {
            filter: invert(0);
        }
    }

    .tag {
        -webkit-appearance: none;
        appearance: none;
        cursor: pointer;
        border: 1px solid var(--border-subtle);
        border-bottom-color: var(--shadow);
        background: var(--button-bg);
        &:hover {
            background: linear-gradient(
                180deg,
                var(--button-gradient-start) 0%,
                var(--button-gradient-end) 100%
            );
            /* Makes distinguishing hover state in light theme easier */
            border: 1px solid var(--shadow);
        }
        color: var(--fg);

        vertical-align: middle;
        font-size: var(--font-size);
        padding: 0;

        --border-color: var(--border);

        border: 1px solid var(--border-color) !important;
        border-radius: 5px;

        &:focus,
        &:active {
            outline: none;
            box-shadow: none;
        }

        &.flashing {
            animation: flash 0.3s linear;
        }

        &.selected {
            box-shadow: 0 0 0 2px var(--border-focus);
            --border-color: var(--border-focus);
        }
    }
</style>
