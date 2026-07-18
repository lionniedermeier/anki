<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<script lang="ts">
    import { createEventDispatcher, onMount } from "svelte";

    export let id: string | undefined = undefined;
    let className: string = "";
    export { className as class };
    export let primary = false;

    export let tooltip: string | undefined = undefined;
    export let active = false;
    export let disabled = false;
    export let tabbable = false;
    export let ellipsis = false;

    let buttonRef: HTMLButtonElement;

    const dispatch = createEventDispatcher();
    onMount(() => dispatch("mount", { button: buttonRef }));
</script>

<button
    bind:this={buttonRef}
    {id}
    class="label-button {className}"
    class:active
    class:primary
    class:ellipsis
    title={tooltip}
    {disabled}
    tabindex={tabbable ? 0 : -1}
    on:click
    on:mousedown|preventDefault
>
    <slot />
</button>

<style lang="scss">
    .label-button {
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
        &:active {
            box-shadow: inset 0 calc(var(--buttons-size, 10px) / 15)
                calc(var(--buttons-size, 10px) / 5) rgba(0, 0, 0, 0.35);
            border-color: var(--border-subtle);
        }
        &.active {
            box-shadow: inset 0 calc(var(--buttons-size, 10px) / 15)
                calc(var(--buttons-size, 10px) / 5) rgba(0, 0, 0, 0.35);
            background: var(--button-primary-bg);
            color: white;
            border-color: var(--border);
        }
        &[disabled],
        &[disabled]:hover {
            cursor: not-allowed;
            color: var(--fg-disabled);
            box-shadow: none !important;
            background: var(--button-gradient-end);
            border-bottom-color: var(--border-subtle);
        }
        &.primary {
            -webkit-appearance: none;
            appearance: none;
            cursor: pointer;
            border: none;
            background: var(--button-primary-bg);
            &:hover {
                background: linear-gradient(
                    180deg,
                    var(--button-primary-gradient-start) 0%,
                    var(--button-primary-gradient-end) 100%
                );
            }
            color: white;
            &:active {
                box-shadow: inset 0 calc(var(--buttons-size, 10px) / 15)
                    calc(var(--buttons-size, 10px) / 5) rgba(0, 0, 0, 0.35);
                border-color: var(--border-subtle);
            }
            &[disabled],
            &[disabled]:hover {
                cursor: not-allowed;
                color: var(--fg-disabled);
                box-shadow: none !important;
                background: var(--button-gradient-end);
                border-bottom-color: var(--border-subtle);
            }
        }
        border-top-left-radius: var(--border-left-radius);
        border-bottom-left-radius: var(--border-left-radius);
        border-top-right-radius: var(--border-right-radius);
        border-bottom-right-radius: var(--border-right-radius);

        white-space: nowrap;
        &.ellipsis {
            overflow: hidden;
            text-overflow: ellipsis;
        }
        padding: 0 calc(var(--buttons-size) / 3);
        font-size: var(--font-size);
        width: auto;
        height: var(--buttons-size);
    }
</style>
