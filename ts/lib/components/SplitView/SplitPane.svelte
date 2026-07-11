<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<script lang="ts">
    import type { Snippet } from "svelte";
    import { getContext, onDestroy, untrack } from "svelte";

    import { chevronDown, chevronLeft, chevronRight, chevronUp } from "../icons";
    import type { SplitViewContext } from "./SplitView";
    import { lastVisiblePaneId, splitViewKey } from "./SplitView";

    interface SplitPaneProps {
        id: string;
        /** Initial width/height in px. Ignored while `grow` is set. */
        size?: number;
        min?: number;
        /** Fill remaining space instead of being individually resizable. Use
         * this for the main/content pane. */
        grow?: boolean;
        /** Whether the pane is collapsible. */
        collapsible?: boolean;
        /** Drop the pane and its divider out of the layout while keeping its
         * contents mounted. Prefer this over an `{#if}` around the pane when
         * re-creating the children would be costly or destructive. */
        hidden?: boolean;
        children?: Snippet;
    }

    let {
        id,
        size = 240,
        min = 120,
        grow = false,
        collapsible = false,
        hidden = false,
        children,
    }: SplitPaneProps = $props();

    const ctx = getContext<SplitViewContext>(splitViewKey);
    if (!ctx) {
        throw new Error("SplitPane must be used inside a SplitView");
    }

    const panes = ctx.panes;

    // Register once with the pane's initial size/constraints; subsequent
    // sizing is driven through the shared store, so the props are read
    // untracked here to capture their initial values.
    untrack(() => ctx.register({ id, size, min, grow, collapsed: false, hidden }));
    onDestroy(() => ctx.unregister(id));

    // Visibility, unlike size, stays owned by the parent, so mirror the prop
    // into the shared store for the neighbouring panes' divider logic.
    $effect(() => {
        ctx.setHidden(id, hidden);
    });

    const state = $derived($panes.find((pane) => pane.id === id));
    const collapsed = $derived(state?.collapsed ?? false);
    const flexBasis = $derived(
        state?.grow ? "1 1 0" : `0 0 ${collapsed ? 0 : (state?.size ?? size)}px`,
    );
    const isLast = $derived(lastVisiblePaneId($panes) === id);
    const vertical = $derived(ctx.direction === "vertical");
    const collapseIcon = $derived(collapseIconFor(vertical, collapsed));

    function collapseIconFor(vertical: boolean, collapsed: boolean) {
        if (vertical) {
            return collapsed ? chevronDown : chevronUp;
        }
        return collapsed ? chevronRight : chevronLeft;
    }

    const DRAG_KEY_STEP = 20;
    // Pointer position where the current drag started, or null when idle.
    let dragOrigin: number | null = null;
    // Px already applied to the divider this drag. Because we always request
    // the delta relative to `dragOrigin` minus what has actually been applied,
    // overshoot past a min-size boundary is not baked into the origin: the
    // divider only starts moving again once the pointer returns to the
    // position where it stopped.
    let appliedDelta = 0;

    function pointerPos(event: PointerEvent): number {
        return vertical ? event.clientY : event.clientX;
    }

    function startDrag(event: PointerEvent): void {
        if (event.button !== 0) {
            return;
        }
        // Capture the pointer on the divider so pointer events keep flowing to
        // it even when the cursor moves over an iframe pane. Without this, a
        // fast drag toward an iframe lets the iframe swallow the pointermove
        // events and the divider stops tracking.
        try {
            (event.currentTarget as HTMLElement).setPointerCapture(event.pointerId);
        } catch {
            // Non-fatal: fall back to the window listeners below.
        }
        dragOrigin = pointerPos(event);
        appliedDelta = 0;
        window.addEventListener("pointermove", onDragMove);
        window.addEventListener("pointerup", onDragEnd);
    }

    function onDragMove(event: PointerEvent): void {
        if (dragOrigin === null) {
            return;
        }
        const desired = pointerPos(event) - dragOrigin;
        appliedDelta += ctx.resize(id, desired - appliedDelta);
    }

    function onDragEnd(): void {
        dragOrigin = null;
        window.removeEventListener("pointermove", onDragMove);
        window.removeEventListener("pointerup", onDragEnd);
    }

    onDestroy(() => {
        window.removeEventListener("pointermove", onDragMove);
        window.removeEventListener("pointerup", onDragEnd);
    });

    function onKeydown(event: KeyboardEvent): void {
        const forwardKey = vertical ? "ArrowDown" : "ArrowRight";
        const backwardKey = vertical ? "ArrowUp" : "ArrowLeft";
        if (event.key === forwardKey) {
            ctx.resize(id, DRAG_KEY_STEP);
            event.preventDefault();
        } else if (event.key === backwardKey) {
            ctx.resize(id, -DRAG_KEY_STEP);
            event.preventDefault();
        } else if (collapsible && (event.key === "Enter" || event.key === " ")) {
            ctx.toggleCollapsed(id);
            event.preventDefault();
        }
    }
</script>

<div class="split-pane" class:collapsed class:hidden style={`flex: ${flexBasis};`}>
    {#if !collapsed}
        <div class="split-pane-content">
            {@render children?.()}
        </div>
    {/if}
</div>
{#if !isLast && !hidden}
    <!-- Focusable separator (WAI-ARIA APG "Window Splitter" pattern): a
    resizable divider is legitimately both a static role and a keyboard/
    pointer-operable widget, which the linter's fixed interactive-role list
    doesn't recognize. -->
    <!-- svelte-ignore a11y_no_noninteractive_tabindex -->
    <!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
    <div
        class="split-view-divider"
        class:vertical
        role="separator"
        aria-orientation={vertical ? "horizontal" : "vertical"}
        aria-valuenow={state?.grow ? undefined : (state?.size ?? size)}
        aria-valuemin={state?.grow ? undefined : min}
        tabindex="0"
        onpointerdown={startDrag}
        onkeydown={onKeydown}
    ></div>
{/if}

<style lang="scss">
    .split-pane {
        display: flex;
        min-width: 0;
        min-height: 0;
        overflow: hidden;

        &.collapsed {
            flex-basis: 0 !important;
        }

        // display:none rather than an {#if}, so the children keep their state.
        &.hidden {
            display: none;
        }
    }

    .split-pane-content {
        flex: 1 1 auto;
        min-width: 0;
        min-height: 0;
        overflow: hidden;
    }

    .split-view-divider {
        position: relative;
        flex: 0 0 auto;
        width: 1px;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: col-resize;
        background: var(--border-subtle);
        touch-action: none;
        z-index: 1;

        &::before {
            content: "";
            position: absolute;
            top: 0;
            bottom: 0;
            left: 50%;
            width: 11px;
            translate: -50% 0;
        }

        &.vertical {
            width: auto;
            height: 1px;
            cursor: row-resize;

            &::before {
                top: 50%;
                bottom: auto;
                left: 0;
                right: 0;
                width: auto;
                height: 11px;
                translate: 0 -50%;
            }
        }

        &:hover,
        &:focus-visible {
            background: var(--border-focus);
        }

        :global(.icon-button) {
            position: absolute;
            background: var(--canvas);
            border: 1px solid var(--border-subtle);
            border-radius: 50%;
        }
    }
</style>
