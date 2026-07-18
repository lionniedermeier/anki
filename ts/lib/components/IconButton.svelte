<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<script lang="ts">
    import IconConstrain from "./IconConstrain.svelte";

    export let id: string | undefined = undefined;
    let className = "";
    export { className as class };

    export let tooltip: string | undefined = undefined;
    export let primary = false;
    export let active = false;
    export let disabled = false;
    export let tabbable = false;

    export let iconSize = 75;
    export let widthMultiplier = 1;
    export let flipX = false;
</script>

<button
    {id}
    class="icon-button {className}"
    class:active
    class:primary
    title={tooltip}
    {disabled}
    tabindex={tabbable ? 0 : -1}
    on:click
    on:mousedown|preventDefault
>
    <IconConstrain {flipX} {widthMultiplier} {iconSize}>
        <slot />
    </IconConstrain>
</button>

<style lang="scss">
    .icon-button {
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

        padding: 0 var(--padding-inline, 0);
        font-size: var(--font-size);
        height: var(--buttons-size);
        min-width: calc(var(--buttons-size) * 0.75);
    }
</style>
