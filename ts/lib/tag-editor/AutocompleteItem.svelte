<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<script lang="ts">
    export let selected = false;
    export let active = false;
    export let suggestion: string; // used by add-ons to target individual suggestions

    let buttonRef: HTMLElement;

    $: if (selected && buttonRef) {
        /* buttonRef.scrollIntoView({ behavior: "smooth", block: "start" }); */
        /* TODO will not work on Gecko */
        (buttonRef as any).scrollIntoViewIfNeeded({
            behavior: "smooth",
            block: "start",
        });
    }
</script>

<div
    bind:this={buttonRef}
    tabindex="-1"
    class="autocomplete-item"
    class:selected
    class:active
    data-addon-suggestion={suggestion}
    on:mousedown|preventDefault
    on:mouseup
    on:mouseenter
    on:mouseleave
    role="button"
>
    <slot />
</div>

<style lang="scss">
    .autocomplete-item {
        padding: 4px 8px;

        text-align: start;
        white-space: nowrap;
        flex-grow: 1;
        border-radius: 0;
        border: 1px solid transparent;
        &:not(:first-child) {
            border-top-color: var(--border-subtle);
        }

        &:hover {
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
        }
        &.selected {
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
            &.active {
                box-shadow: inset 0 calc(var(--buttons-size, 10px) / 15)
                    calc(var(--buttons-size, 10px) / 5) rgba(0, 0, 0, 0.35);
                background: var(--button-primary-bg);
                color: white;
                border-color: var(--border);
            }
        }
    }
</style>
