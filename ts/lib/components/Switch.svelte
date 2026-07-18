<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<script lang="ts">
    interface SwitchProps {
        id: string | undefined;
        value: boolean;
        disabled?: boolean;
        onchange?: (event: Event) => void;
    }

    let { id, value = $bindable(), disabled = false, onchange }: SwitchProps = $props();

    const rtl: boolean = window.getComputedStyle(document.body).direction == "rtl";
</script>

<div class="switch" class:rtl>
    <input
        {id}
        type="checkbox"
        role="switch"
        class="switch-input"
        bind:checked={value}
        {disabled}
        {onchange}
    />
    <div class="switch-handle"></div>
    <div class="switch-hover"></div>
</div>

<style lang="scss">
    .switch {
        position: relative;
        display: inline-flex;
        width: 3.25rem;
        height: 2rem;
        flex-shrink: 0;
    }

    .switch-input {
        -webkit-appearance: none;
        appearance: none;
        width: 100%;
        height: 100%;
        margin: 0;
        border-radius: 999px;
        background-color: var(--canvas-inset);
        border: 2px solid var(--border);
        cursor: pointer;
        transition:
            background-color 0.15s ease-in-out,
            border-color 0.15s ease-in-out;

        &:checked {
            background-color: var(--button-primary-bg);
            border-color: var(--button-primary-bg);
        }

        &:focus-visible {
            outline: 2px solid var(--border-focus);
            outline-offset: 1px;
        }

        &:disabled {
            background-color: color-mix(in srgb, var(--canvas-inset) 62%, transparent);
            border-color: color-mix(in srgb, var(--border) 62%, transparent);
            cursor: auto;
        }

        &:checked:disabled {
            background-color: color-mix(
                in srgb,
                var(--button-primary-bg) 38%,
                transparent
            );
            border-color: transparent;
        }
    }

    .switch-handle {
        position: absolute;
        top: 50%;
        left: 0.5rem;
        width: 1rem;
        height: 1rem;
        border-radius: 999px;
        background-color: var(--fg-subtle);
        pointer-events: none;
        translate: 0 -50%;
        transition:
            left 0.15s cubic-bezier(0.2, 0, 0, 1),
            scale 0.15s cubic-bezier(0.2, 0, 0, 1),
            background-color 0.15s ease-in-out;
    }

    .switch-input:checked ~ .switch-handle {
        left: 1.75rem;
        scale: 1.5;
        background-color: var(--canvas-elevated);
    }

    .switch:active .switch-input:enabled ~ .switch-handle {
        scale: 1.75;
    }

    .switch-input:disabled ~ .switch-handle {
        background-color: color-mix(in srgb, var(--fg-subtle) 38%, transparent);
    }

    .switch-input:checked:disabled ~ .switch-handle {
        background-color: var(--canvas);
    }

    .switch-hover {
        position: absolute;
        top: 50%;
        left: 1rem;
        width: 2.5rem;
        height: 2.5rem;
        border-radius: 999px;
        background-color: transparent;
        pointer-events: none;
        translate: -50% -50%;
        transition:
            left 0.15s cubic-bezier(0.2, 0, 0, 1),
            background-color 0.15s ease-in-out;
    }

    .switch-input:checked ~ .switch-hover {
        left: 2.25rem;
    }

    .switch:hover .switch-input:enabled ~ .switch-hover {
        background-color: color-mix(in srgb, var(--fg) 8%, transparent);
    }

    .switch:hover .switch-input:checked:enabled ~ .switch-hover {
        background-color: color-mix(in srgb, var(--button-primary-bg) 8%, transparent);
    }

    .switch.rtl {
        .switch-handle {
            left: auto;
            right: 0.5rem;
        }

        .switch-hover {
            left: auto;
            right: 1rem;
            translate: 50% -50%;
        }

        .switch-input:checked ~ .switch-handle {
            left: auto;
            right: 1.75rem;
        }

        .switch-input:checked ~ .switch-hover {
            left: auto;
            right: 2.25rem;
        }
    }
</style>
