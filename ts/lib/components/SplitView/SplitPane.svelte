<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<script lang="ts">
    import { getContext, onDestroy } from "svelte";
    import * as tr from "@generated/ftl";

    import { chevronDown, chevronLeft, chevronRight, chevronUp } from "../icons";
    import Icon from "../Icon.svelte";
    import IconButton from "../IconButton.svelte";
    import type { SplitViewContext } from "./SplitView";
    import { splitViewKey } from "./SplitView";

    export let id: string;
    /** Initial width/height in px. Ignored while `grow` is set. */
    export let size = 240;
    export let min = 120;
    /** Fill remaining space instead of being individually resizable. Use
     * this for the main/content pane. */
    export let grow = false;
    /** Whether the divider trailing this pane offers a collapse toggle. */
    export let collapsible = true;

    const ctx = getContext<SplitViewContext>(splitViewKey);
    if (!ctx) {
        throw new Error("SplitPane must be used inside a SplitView");
    }

    const panes = ctx.panes;

    ctx.register({ id, size, min, grow, collapsed: false });
    onDestroy(() => ctx.unregister(id));

    $: state = $panes.find((pane) => pane.id === id);
    $: collapsed = state?.collapsed ?? false;
    $: flexBasis = state?.grow
        ? "1 1 0"
        : `0 0 ${collapsed ? 0 : (state?.size ?? size)}px`;
    $: isLast = $panes.length > 0 && $panes[$panes.length - 1].id === id;
    $: vertical = ctx.direction === "vertical";
    $: collapseIcon = collapseIconFor(vertical, collapsed);

    function collapseIconFor(vertical: boolean, collapsed: boolean) {
        if (vertical) {
            return collapsed ? chevronDown : chevronUp;
        }
        return collapsed ? chevronRight : chevronLeft;
    }

    const DRAG_KEY_STEP = 20;
    let dragPos: number | null = null;

    function pointerPos(event: PointerEvent): number {
        return vertical ? event.clientY : event.clientX;
    }

    function startDrag(event: PointerEvent): void {
        if (event.button !== 0) {
            return;
        }
        dragPos = pointerPos(event);
        window.addEventListener("pointermove", onDragMove);
        window.addEventListener("pointerup", onDragEnd);
    }

    function onDragMove(event: PointerEvent): void {
        if (dragPos === null) {
            return;
        }
        const pos = pointerPos(event);
        ctx.resize(id, pos - dragPos);
        dragPos = pos;
    }

    function onDragEnd(): void {
        dragPos = null;
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

<div class="split-pane" class:collapsed style={`flex: ${flexBasis};`}>
    {#if !collapsed}
        <div class="split-pane-content">
            <slot />
        </div>
    {/if}
</div>
{#if !isLast}
    <!-- Focusable separator (WAI-ARIA APG "Window Splitter" pattern): a
    resizable divider is legitimately both a static role and a keyboard/
    pointer-operable widget, which the linter's fixed interactive-role list
    doesn't recognize. -->
    <!-- svelte-ignore a11y-no-noninteractive-tabindex -->
    <!-- svelte-ignore a11y-no-noninteractive-element-interactions -->
    <div
        class="split-view-divider"
        class:vertical
        role="separator"
        aria-orientation={vertical ? "horizontal" : "vertical"}
        aria-valuenow={state?.grow ? undefined : (state?.size ?? size)}
        aria-valuemin={state?.grow ? undefined : min}
        tabindex="0"
        on:pointerdown={startDrag}
        on:keydown={onKeydown}
    >
        {#if collapsible}
            <IconButton
                tabbable
                tooltip={collapsed
                    ? tr.browsingSidebarExpand()
                    : tr.browsingSidebarCollapse()}
                on:click={() => ctx.toggleCollapsed(id)}
            >
                <Icon icon={collapseIcon} />
            </IconButton>
        {/if}
    </div>
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
        width: 6px;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: col-resize;
        background: var(--border-subtle);
        touch-action: none;

        &.vertical {
            width: auto;
            height: 6px;
            cursor: row-resize;
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
