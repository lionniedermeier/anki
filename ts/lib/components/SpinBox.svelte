<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<script lang="ts">
    import * as tr from "@generated/ftl";
    import { isDesktop } from "@tslib/platform";
    import { tick } from "svelte";

    import { chevronDown, chevronUp } from "$lib/components/icons";

    import Icon from "./Icon.svelte";
    import IconConstrain from "./IconConstrain.svelte";

    interface SpinBoxProps {
        value: number;
        step?: number;
        min?: number;
        max?: number;
        /**
         * Whether the value is shown as a percentage to the user.
         * It's saved as a proportion.
         */
        percentage?: boolean;
        focused?: boolean;
    }

    let {
        value = $bindable(),
        step = 1,
        min = 1,
        max = 9999,
        percentage = false,
        focused = $bindable(false),
    }: SpinBoxProps = $props();

    let input: HTMLInputElement | undefined = $state();
    const multiplier = $derived(percentage ? 100 : 1);

    /** Set value to a new number, clamping it to a valid range, and
        leaving it unchanged if `newValue` is NaN. */
    function updateValue(newValue: number) {
        if (Number.isNaN(newValue)) {
            // avoid updating the value
        } else {
            value = Math.min(max, Math.max(min, newValue));
        }
        // Assigning to `value` will trigger the stringValue reactive statement below,
        // but Svelte may not redraw the UI. For example, if '1' was shown, and the user
        // enters '0', if the value gets clamped back to '1', Svelte will think the value hasn't
        // changed, and will skip the UI update. So we manually update the DOM to ensure it stays
        // in sync.
        tick().then(() => {
            if (input) {
                input.value = stringValue;
            }
            percentageText = splitPercentage(stringValue);
        });
    }

    /**
     * The number of decimal places to record. May be different than the number of decimal places displayed for percentages.
     * @param value The size of the step.
     */
    function decimalPlaces(value: number) {
        if (Math.floor(value) === value) {
            // If the step is an integer, do not show decimal places.
            return 0;
        }
        const places = value.toString().split(".")[1].length || 0;
        const displayedPlace = percentage ? places - 2 : places;
        return Math.max(0, displayedPlace);
    }

    const stringValue = $derived((value * multiplier).toFixed(decimalPlaces(step)));

    function update(): void {
        updateValue(parseFloat(input!.value) / multiplier);
    }

    function handleWheel(event: WheelEvent) {
        if (focused) {
            updateValue(value + (event.deltaY < 0 ? step : -step));
            event.preventDefault();
        }
    }

    function change(step: number): void {
        updateValue(value + step);
        if (pressed) {
            setTimeout(() => change(step), timeout);
        }
    }

    const progression = [1500, 1250, 1000, 750, 500, 250];

    async function longPress(func: Function): Promise<void> {
        pressed = true;
        timeout = 128;
        pressTimer = setTimeout(func, 250);

        for (const delay of progression) {
            timeout = await new Promise((resolve) =>
                setTimeout(() => resolve(pressed ? timeout / 2 : 128), delay),
            );
        }
    }

    function splitPercentage(value: string): string[] {
        // Separate the % from the padding text.
        return tr
            .deckConfigPercentInput({ pct: value })
            .replaceAll("%", "-%-")
            .split("-");
    }

    function onInput() {
        percentageText = splitPercentage(input!.value);
    }

    // Invisible, used to shift the % sign the correct amount.
    // svelte-ignore state_referenced_locally
    let percentageText: string[] = $state(splitPercentage(stringValue));

    $effect(() => {
        percentageText = splitPercentage(stringValue);
    });

    // If the input box should be moved right for leading percentage symbol.
    const percentagePadding = $derived(
        percentage && !percentageText[0] ? "2.2ch" : undefined,
    );

    let pressed = false;
    let timeout: number;
    let pressTimer: any;
</script>

<div class="spin-box" onwheel={handleWheel}>
    <input
        type="number"
        pattern="[0-9]*"
        inputmode="numeric"
        min={min * multiplier}
        max={max * multiplier}
        step={step * multiplier}
        value={stringValue}
        bind:this={input}
        onblur={update}
        onchange={update}
        oninput={onInput}
        onfocusin={() => (focused = true)}
        onfocusout={() => (focused = false)}
        style:padding-left={percentagePadding}
    />
    {#if percentage}
        <span class="suffix">
            {#each percentageText as str}
                {#if str == "%"}
                    %
                {:else}
                    <span class="invisible">{str}</span>
                {/if}
            {/each}
        </span>
    {/if}
    {#if isDesktop()}
        <!-- svelte-ignore a11y_click_events_have_key_events -->
        <div
            class="spinner decrement"
            class:active={value > min}
            tabindex="-1"
            title={tr.actionsDecrementValue()}
            role="button"
            onclick={() => {
                input?.focus();
                if (value > min) {
                    change(-step);
                }
            }}
            onmousedown={() =>
                longPress(() => {
                    if (value > min) {
                        change(-step);
                    }
                })}
            onmouseup={() => {
                clearTimeout(pressTimer);
                pressed = false;
            }}
        >
            <IconConstrain>
                <Icon icon={chevronDown} />
            </IconConstrain>
        </div>
        <!-- svelte-ignore a11y_click_events_have_key_events -->
        <div
            class="spinner increment"
            class:active={value < max}
            tabindex="-1"
            title={tr.actionsIncrementValue()}
            role="button"
            onclick={() => {
                input?.focus();
                if (value < max) {
                    change(step);
                }
            }}
            onmousedown={() =>
                longPress(() => {
                    if (value < max) {
                        change(step);
                    }
                })}
            onmouseup={() => {
                clearTimeout(pressTimer);
                pressed = false;
            }}
        >
            <IconConstrain>
                <Icon icon={chevronUp} />
            </IconConstrain>
        </div>
    {/if}
</div>

<style lang="scss">
    .spin-box {
        width: 100%;
        background: var(--canvas-inset);
        border: 1px solid var(--border);
        border-radius: var(--border-radius);
        overflow: hidden;
        position: relative;
        display: flex;
        justify-content: space-between;

        .suffix {
            position: absolute;
            pointer-events: none;
            white-space: pre;
            left: 0.5em;
            top: 1px;

            @supports (-webkit-touch-callout: none) {
                /* CSS specific to iOS devices */
                top: 3.5px;
            }
        }

        .invisible {
            color: transparent;
            pointer-events: none;
        }

        input {
            flex-grow: 1;
            border: none;
            outline: none;
            background: transparent;
            &::-webkit-inner-spin-button {
                display: none;
            }
            padding-left: 0.5em;
            padding-right: 0.5em;
        }

        &:hover,
        &:focus-within {
            .spinner {
                opacity: 0.1;
                &.active {
                    opacity: 0.4;
                    cursor: pointer;
                    &:hover {
                        opacity: 1;
                    }
                }
            }
        }
    }
    .spinner {
        opacity: 0;
        height: 100%;
    }
</style>
