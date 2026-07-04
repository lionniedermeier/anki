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
    import { createEventDispatcher } from "svelte";

    export let width: number;
    export let min: number = 60;

    const KEY_STEP = 20;

    // Fired once the drag ends, so a consumer that persists widths (e.g. to
    // localStorage) can do so once per drag instead of on every pointermove.
    const dispatch = createEventDispatcher<{ commit: void }>();

    let startX = 0;
    let startWidth = 0;

    function onPointerDown(event: PointerEvent): void {
        if (event.button !== 0) {
            return;
        }
        startX = event.clientX;
        startWidth = width;
        window.addEventListener("pointermove", onPointerMove);
        window.addEventListener("pointerup", onPointerUp);
    }

    function onPointerMove(event: PointerEvent): void {
        width = Math.max(min, startWidth + (event.clientX - startX));
    }

    function onPointerUp(): void {
        window.removeEventListener("pointermove", onPointerMove);
        window.removeEventListener("pointerup", onPointerUp);
        dispatch("commit");
    }

    function onKeydown(event: KeyboardEvent): void {
        if (event.key === "ArrowRight") {
            width = Math.max(min, width + KEY_STEP);
            dispatch("commit");
            event.preventDefault();
        } else if (event.key === "ArrowLeft") {
            width = Math.max(min, width - KEY_STEP);
            dispatch("commit");
            event.preventDefault();
        }
    }
</script>

<!-- Focusable separator (WAI-ARIA APG "Window Splitter" pattern), matching
SplitPane's divider: a resizable column edge is legitimately both a static
role and a keyboard/pointer-operable widget, which the linter's fixed
interactive-role list doesn't recognize. -->
<!-- svelte-ignore a11y-no-noninteractive-tabindex -->
<!-- svelte-ignore a11y-no-noninteractive-element-interactions -->
<div
    class="resize-handle"
    role="separator"
    aria-orientation="vertical"
    aria-valuenow={width}
    aria-valuemin={min}
    tabindex="0"
    on:pointerdown|stopPropagation={onPointerDown}
    on:keydown|stopPropagation={onKeydown}
    on:click|stopPropagation
></div>

<style lang="scss">
    .resize-handle {
        position: absolute;
        top: 0;
        bottom: 0;
        // Sit fully inside the cell's right edge so a `overflow: hidden`
        // header cell doesn't clip the handle away (which made resizing
        // impossible when the handle extended outside the box).
        right: 0;
        width: 6px;
        cursor: col-resize;
        z-index: 1;
        user-select: none;

        &:hover,
        &:focus-visible {
            background: var(--border-focus);
        }
    }
</style>
