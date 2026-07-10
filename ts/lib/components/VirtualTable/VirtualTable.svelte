<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<script lang="ts">
    import type { Snippet } from "svelte";

    import { computeVisibleRange } from "./VirtualTable";

    interface Props {
        class?: string;
        itemsCount?: number;
        itemHeight: number;
        bottomOffset?: number;
        /** Per-column widths in px. Rendered as the fixed tracks of the
         * grid's `--vg-columns` template, so column widths come solely from
         * this array (never from cell content). Consumers own dragging
         * (e.g. via `ColumnResizeHandle.svelte`) and pass the resulting
         * array back in. */
        columnWidths?: number[];
        /** Lets consumers whose row data must be fetched on demand (e.g.
         * from a backend) know which rows need loading, without every
         * consumer having to duplicate this component's scroll/height
         * math. */
        onvisible?: (range: { start: number; end: number }) => void;
        headers?: Snippet;
        row?: Snippet<[index: number]>;
    }

    const {
        class: className = "",
        itemsCount = 0,
        itemHeight,
        bottomOffset = 0,
        columnWidths = $bindable([]),
        onvisible,
        headers,
        row,
    }: Props = $props();

    let container: HTMLElement | undefined = $state();
    let scrollTop = $state(0);
    let containerHeight = $state(0);
    let pendingFrame: number | null = null;

    // A trailing flexible track absorbs any leftover horizontal space so the
    // grid fills the container without a dead gap, while never shrinking the
    // real (fixed-px) columns; it collapses to 0 when the columns overflow.
    const gridColumns = $derived(
        [...columnWidths.map((w) => `${w}px`), "minmax(0, 1fr)"].join(" "),
    );

    const visibleRange = $derived(
        computeVisibleRange(scrollTop, containerHeight, itemHeight, itemsCount),
    );
    const slice = $derived(
        new Array(visibleRange.endIndex - visibleRange.startIndex)
            .fill(0)
            .map((_, i) => visibleRange.startIndex + i),
    );

    $effect(() => {
        onvisible?.({ start: visibleRange.startIndex, end: visibleRange.endIndex });
    });

    function onScroll(): void {
        // Batch to at most one `scrollTop` update per animation frame - a
        // scroll gesture can fire many native scroll events per frame (e.g.
        // trackpads/high-poll-rate mice), and each update re-enters Svelte's
        // reactive graph above.
        if (pendingFrame !== null || !container) {
            return;
        }
        const target = container;
        pendingFrame = requestAnimationFrame(() => {
            scrollTop = target.scrollTop;
            pendingFrame = null;
        });
    }

    $effect(() => {
        // Re-measure whenever `container`/`itemHeight`/`bottomOffset` change
        // (tracked automatically), and also on every window resize (not
        // reactive state, so it needs an explicit listener).
        function measure(): void {
            containerHeight = container
                ? Math.floor(
                      (document.documentElement.clientHeight -
                          container.offsetTop -
                          bottomOffset) /
                          itemHeight,
                  ) * itemHeight
                : 0;
        }
        measure();
        window.addEventListener("resize", measure);
        return () => {
            window.removeEventListener("resize", measure);
            if (pendingFrame !== null) {
                cancelAnimationFrame(pendingFrame);
            }
        };
    });
</script>

<div
    class="vg-scroll"
    style="--container-height: {containerHeight}px"
    bind:this={container}
    onscroll={onScroll}
>
    <div
        class="vg-grid {className}"
        style="--vg-columns: {gridColumns}; --vg-row-height: {itemHeight}px"
    >
        <div class="vg-header">
            {@render headers?.()}
        </div>
        <div class="vg-body">
            {#if itemHeight * visibleRange.startIndex > 0}
                <div
                    class="vg-spacer"
                    style="height: {itemHeight * visibleRange.startIndex}px;"
                ></div>
            {/if}

            {#each slice as index (index)}
                {@render row?.(index)}
            {/each}

            {#if itemHeight * itemsCount - itemHeight * visibleRange.endIndex > 0}
                <div
                    class="vg-spacer"
                    style="height: {itemHeight * itemsCount -
                        itemHeight * visibleRange.endIndex}px;"
                ></div>
            {/if}
        </div>
    </div>
</div>

<style lang="scss">
    .vg-scroll {
        width: 100%;
        overflow: auto;

        max-height: var(--container-height);
        margin: 0 auto;
    }

    .vg-grid {
        // Grow to fit wider columns, but never narrower than the viewport so
        // the header/rows fill the available width.
        min-width: 100%;
        width: max-content;
        white-space: nowrap;
    }

    .vg-header {
        position: sticky;
        top: 0;
        z-index: 1;
    }

    :global(.vg-row) {
        display: grid;
        grid-template-columns: var(--vg-columns);
        align-items: center;
    }

    .vg-body :global(.vg-row) {
        height: var(--vg-row-height);
    }

    :global(.vg-cell) {
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        border-right: 1px solid var(--border-subtle);
        border-bottom: 1px solid var(--border-subtle);
        padding: 0.25rem 0.5rem;
    }

    .vg-header :global(.vg-cell) {
        position: relative;
        background: var(--border);
        text-align: center;
        border-top: 1px solid var(--border-subtle);
        // Let the resize handle straddle the cell's right edge without being
        // clipped, while header labels still effectively clip.
        overflow: clip;
        overflow-clip-margin: 4px;
    }
</style>
