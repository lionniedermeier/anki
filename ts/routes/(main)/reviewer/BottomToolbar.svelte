<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<script lang="ts">
    import { onDestroy } from "svelte";

    import * as tr from "@generated/ftl";
    import { bridgeCommand } from "@tslib/bridgecommand";

    import { bottomState } from "./bottom";

    let time = $state(0);
    let intervalId: number | undefined;

    let easesContainer = $state<HTMLDivElement | null>(null);

    function formatTime(value: number, max: number): string {
        const clamped = Math.min(max, value);
        const m = Math.floor(clamped / 60);
        const s = String(clamped % 60).padStart(2, "0");
        return `${m}:${s}`;
    }

    $effect(() => {
        const state = $bottomState;
        if (state.phase === "question") {
            time = state.timeTaken;
            if (intervalId !== undefined) {
                clearInterval(intervalId);
            }
            intervalId = window.setInterval(() => {
                if (!$bottomState.stopTimer && $bottomState.maxTime > 0) {
                    time += 1;
                }
            }, 1000);
        }
    });

    $effect(() => {
        if ($bottomState.phase === "answer" && easesContainer) {
            const target = easesContainer.querySelector<HTMLButtonElement>(
                "[data-default='true']",
            );
            target?.focus();
        }
    });

    onDestroy(() => {
        if (intervalId !== undefined) {
            clearInterval(intervalId);
        }
    });

    const showTimer = $derived($bottomState.maxTime > 0);
    const timeString = $derived(formatTime(time, $bottomState.maxTime));
    const atMax = $derived(showTimer && time >= $bottomState.maxTime);
</script>

<div class="reviewer-bottom">
    <button
        class="side"
        title={tr.actionsShortcutKey({ val: "E" })}
        onclick={() => bridgeCommand("edit")}
    >
        {tr.studyingEdit()}
    </button>

    <div class="middle">
        {#if $bottomState.phase === "question"}
            <button
                class="answer"
                title={tr.actionsShortcutKey({ val: tr.studyingSpace() })}
                onclick={() => bridgeCommand("ans")}
            >
                {tr.studyingShowAnswer()}
                {#if $bottomState.remaining.show}
                    <span class="counts">
                        <span
                            class="new-count"
                            class:active={$bottomState.remaining.active === 0}
                        >{$bottomState.remaining.counts[0]}</span> +
                        <span
                            class="learn-count"
                            class:active={$bottomState.remaining.active === 1}
                        >{$bottomState.remaining.counts[1]}</span> +
                        <span
                            class="review-count"
                            class:active={$bottomState.remaining.active === 2}
                        >{$bottomState.remaining.counts[2]}</span>
                    </span>
                {/if}
            </button>
        {:else}
            <div class="eases" bind:this={easesContainer}>
                {#each $bottomState.buttons as button (button.ease)}
                    <button
                        class="ease"
                        title={button.key}
                        data-ease={button.ease}
                        data-default={button.default}
                        onclick={() => bridgeCommand(`ease${button.ease}`)}
                    >
                        {button.label}
                        {#if button.interval}
                            <span class="interval">{button.interval}</span>
                        {/if}
                    </button>
                {/each}
            </div>
        {/if}
    </div>

    <button
        class="side"
        title={tr.actionsShortcutKey({ val: "M" })}
        onclick={() => bridgeCommand("more")}
    >
        {tr.studyingMore()} ▾
        {#if showTimer}
            <span class="time" class:at-max={atMax}>{timeString}</span>
        {/if}
    </button>
</div>

<style lang="scss">
    .reviewer-bottom {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 0.5rem;
        padding: 0.25rem 0.5rem;
        border-top: 1px solid var(--border);
        background: var(--canvas-elevated);
    }

    .middle {
        flex: 1 1 auto;
        display: flex;
        justify-content: center;
    }

    .eases {
        display: flex;
        gap: 0.5rem;
    }

    button {
        cursor: pointer;
        border: 1px solid var(--border);
        border-radius: var(--border-radius, 5px);
        background: var(--button-bg, var(--canvas));
        color: var(--fg);
        padding: 0.35rem 0.75rem;
    }

    .counts,
    .interval {
        display: block;
        font-size: 0.75rem;
        opacity: 0.8;
    }

    .counts .active {
        text-decoration: underline;
    }

    .time.at-max {
        color: red;
    }
</style>
