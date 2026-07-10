<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<script lang="ts">
    /** Meant to be placed inside a `position: relative` header cell (e.g.
     * VirtualTable's `.vg-header .vg-cell`, which is `position: relative`),
     * bound to one slot of the same `columnWidths` array passed to
     * `VirtualTable`'s `columnWidths` prop, e.g.:
     * `<div class="vg-cell">{label}<ColumnResizeHandle
     * bind:width={columnWidths[i]} /></div>` */
    import { stopPropagation } from "../helpers";

    interface ColumnResizeHandleProps {
        width: number;
        min?: number;
        // Fired once the drag ends, so a consumer that persists widths (e.g. to
        // localStorage) can do so once per drag instead of on every pointermove.
        oncommit?: () => void;
    }

    let { width = $bindable(), min = 60, oncommit }: ColumnResizeHandleProps = $props();

    const KEY_STEP = 20;

    let startX = $state(0);
    let startWidth = $state(0);

    // Keeps the divider highlighted for the whole drag, since the pointer
    // routinely leaves the handle's narrow grab target while dragging.
    let active = $state(false);

    function onPointerDown(event: PointerEvent): void {
        if (event.button !== 0) {
            return;
        }
        active = true;
        startX = event.clientX;
        startWidth = width;
        window.addEventListener("pointermove", onPointerMove);
        window.addEventListener("pointerup", onPointerUp);
    }

    function onPointerMove(event: PointerEvent): void {
        width = Math.max(min, startWidth + (event.clientX - startX));
    }

    function onPointerUp(): void {
        active = false;
        window.removeEventListener("pointermove", onPointerMove);
        window.removeEventListener("pointerup", onPointerUp);
        oncommit?.();
    }

    function onKeydown(event: KeyboardEvent): void {
        if (event.key === "ArrowRight") {
            width = Math.max(min, width + KEY_STEP);
            oncommit?.();
            event.preventDefault();
        } else if (event.key === "ArrowLeft") {
            width = Math.max(min, width - KEY_STEP);
            oncommit?.();
            event.preventDefault();
        }
    }
</script>

<!-- svelte-ignore a11y_no_noninteractive_tabindex -->
<!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
<div
    class="resize-handle"
    class:active
    role="separator"
    aria-orientation="vertical"
    aria-valuenow={width}
    aria-valuemin={min}
    tabindex="0"
    onpointerdown={stopPropagation(onPointerDown)}
    onkeydown={stopPropagation(onKeydown)}
    onclick={stopPropagation(() => {})}
></div>

<style lang="scss">
    .resize-handle {
        position: absolute;
        top: 0;
        bottom: 0;
        // Straddle the boundary so the grab target is centered on the column
        // edge. The header cell uses `overflow: clip` with an
        // `overflow-clip-margin` so the part sticking out isn't clipped.
        right: -3px;
        width: 8px;
        z-index: 2;
        cursor: col-resize;
        user-select: none;

        &::before {
            content: "";
            position: absolute;
            top: 0;
            bottom: 0;
            left: 50%;
            transform: translateX(-50%);
            width: 2px;
            background: transparent;
        }

        &:hover::before,
        &:focus-visible::before,
        &.active::before {
            background: var(--border-focus);
        }
    }
</style>
