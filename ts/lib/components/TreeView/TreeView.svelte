<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<script lang="ts">
    import { createEventDispatcher, onDestroy, onMount } from "svelte";

    import { chevronDown } from "../icons";
    import Icon from "../Icon.svelte";
    import IconButton from "../IconButton.svelte";
    import { collectSubtreeIds, flattenVisible, type TreeViewNode } from "./TreeView";

    type T = $$Generic<TreeViewNode>;

    export let nodes: T[];
    /** Indentation per depth level, in rem. */
    export let indent = 1.25;
    /** Renders an always-present drop target (via the "topLevel" slot) that
     * reports a null targetId, for un-parenting a dragged row. */
    export let topLevelDroppable = false;

    const dispatch = createEventDispatcher<{
        toggle: { id: string };
        dragdrop: { sourceId: string; targetId: string | null };
    }>();

    $: visibleRows = flattenVisible(nodes);
    $: nodeById = new Map(visibleRows.map((row) => [row.node.id, row.node]));

    const TOP_LEVEL = "__top_level__";
    // Pointer movement (px) required before a press becomes a drag rather than
    // a click. Anki's webview does not support native HTML5 drag-and-drop
    // reliably (see TreeView notes), so dragging is implemented with pointer
    // events instead.
    const DRAG_THRESHOLD = 5;

    let pointerStart: { x: number; y: number; node: T } | null = null;
    let dragging = false;
    let draggedNode: T | null = null;
    let dragOverId: string | null = null;
    let excludedIds = new Set<string>();
    let ghostX = 0;
    let ghostY = 0;
    // Set when a drag completes, to swallow the click the browser fires right
    // after pointerup so it doesn't also trigger the row's click action.
    let suppressNextClick = false;

    function onPointerDown(event: PointerEvent, node: T): void {
        if (!node.draggable || event.button !== 0) {
            return;
        }
        pointerStart = { x: event.clientX, y: event.clientY, node };
        window.addEventListener("pointermove", onPointerMove);
        window.addEventListener("pointerup", onPointerUp);
        window.addEventListener("pointercancel", onPointerCancel);
    }

    function beginDrag(node: T): void {
        dragging = true;
        draggedNode = node;
        excludedIds = collectSubtreeIds(node);
    }

    function updateDropTarget(x: number, y: number): void {
        const el = document.elementFromPoint(x, y);
        const rowEl = el?.closest("[data-tree-row-id]");
        if (rowEl) {
            // Hovering a row: nest onto it, unless it's the dragged node
            // itself or one of its own descendants (invalid reparent), or it
            // opts out of drops.
            const id = rowEl.getAttribute("data-tree-row-id")!;
            const target = nodeById.get(id);
            const valid = target && target.droppable !== false && !excludedIds.has(id);
            dragOverId = valid ? id : null;
        } else if (topLevelDroppable) {
            // Anywhere else in the view (blank space around/below the rows,
            // the header, ...) counts as "drop outside any deck" so
            // un-parenting isn't confined to a single hard-to-hit target.
            dragOverId = TOP_LEVEL;
        } else {
            dragOverId = null;
        }
    }

    function onPointerMove(event: PointerEvent): void {
        if (!pointerStart) {
            return;
        }
        if (!dragging) {
            const dx = event.clientX - pointerStart.x;
            const dy = event.clientY - pointerStart.y;
            if (Math.hypot(dx, dy) < DRAG_THRESHOLD) {
                return;
            }
            beginDrag(pointerStart.node);
        }
        // suppress text selection while dragging
        event.preventDefault();
        ghostX = event.clientX;
        ghostY = event.clientY;
        updateDropTarget(event.clientX, event.clientY);
    }

    function onPointerUp(): void {
        removeListeners();
        if (dragging && draggedNode) {
            const sourceId = draggedNode.id;
            if (dragOverId === TOP_LEVEL) {
                dispatch("dragdrop", { sourceId, targetId: null });
            } else if (dragOverId) {
                dispatch("dragdrop", { sourceId, targetId: dragOverId });
            }
            // a click event follows pointerup; swallow it so a drag that ends
            // on the source row doesn't also fire the row's click action
            suppressNextClick = true;
            setTimeout(() => (suppressNextClick = false), 0);
        }
        reset();
    }

    function onPointerCancel(): void {
        removeListeners();
        reset();
    }

    function removeListeners(): void {
        window.removeEventListener("pointermove", onPointerMove);
        window.removeEventListener("pointerup", onPointerUp);
        window.removeEventListener("pointercancel", onPointerCancel);
    }

    function reset(): void {
        pointerStart = null;
        dragging = false;
        draggedNode = null;
        dragOverId = null;
        excludedIds = new Set();
    }

    function onWindowClickCapture(event: MouseEvent): void {
        if (suppressNextClick) {
            suppressNextClick = false;
            event.stopPropagation();
            event.preventDefault();
        }
    }

    onMount(() => {
        window.addEventListener("click", onWindowClickCapture, true);
    });

    onDestroy(() => {
        removeListeners();
        window.removeEventListener("click", onWindowClickCapture, true);
    });
</script>

<!--
    Note: this does not use ARIA tree/treeitem roles. Those roles imply
    arrow-key navigation, which isn't implemented yet (tracked as Phase E
    follow-up work) - declaring them without that support would be a false
    promise to assistive-technology users.
-->
<div class="tree-view" class:drag-over-top-level={dragOverId === TOP_LEVEL}>
    {#each visibleRows as { node, depth } (node.id)}
        <!-- svelte-ignore a11y-no-static-element-interactions -->
        <div
            class="tree-row"
            class:drag-over={dragOverId === node.id}
            class:dragged={dragging && draggedNode?.id === node.id}
            data-tree-row-id={node.id}
            on:pointerdown={(event) => onPointerDown(event, node)}
        >
            <span class="tree-indent" style="width: {depth * indent}rem"></span>
            {#if node.children.length > 0}
                <IconButton
                    class="tree-chevron"
                    tabbable
                    on:click={() => dispatch("toggle", { id: node.id })}
                >
                    <span class="tree-chevron-icon" class:collapsed={node.collapsed}>
                        <Icon icon={chevronDown} />
                    </span>
                </IconButton>
            {:else}
                <span class="tree-chevron tree-chevron-spacer"></span>
            {/if}
            <div class="tree-row-content">
                <slot name="row" {node} {depth} />
            </div>
        </div>
    {/each}
    {#if topLevelDroppable && dragging}
        <div class="tree-top-level-drop" class:drag-over={dragOverId === TOP_LEVEL}>
            <slot name="topLevel" />
        </div>
    {/if}
</div>

{#if dragging && draggedNode}
    <div class="tree-drag-ghost" style="left: {ghostX}px; top: {ghostY}px">
        <slot name="row" node={draggedNode!} depth={0} />
    </div>
{/if}

<style lang="scss">
    .tree-view {
        border-radius: var(--border-radius, 5px);
        transition: outline-color 0.1s ease-in-out;
        outline: 1px dashed transparent;
        outline-offset: 4px;

        &.drag-over-top-level {
            outline-color: var(--border-focus);
        }
    }

    .tree-row {
        display: flex;
        align-items: center;

        &.drag-over {
            outline: 1px solid var(--border-focus);
        }

        &.dragged {
            opacity: 0.4;
        }
    }

    .tree-top-level-drop {
        display: flex;
        align-items: center;
        justify-content: center;
        margin-top: 0.25rem;
        padding: 0.4rem;
        border: 1px dashed var(--border);
        border-radius: var(--border-radius, 5px);
        color: var(--fg-subtle);
        font-size: 0.9em;

        &.drag-over {
            border-color: var(--border-focus);
            color: var(--fg);
            background: var(--canvas-elevated, var(--canvas));
        }
    }

    .tree-indent {
        flex-shrink: 0;
    }

    .tree-chevron-spacer {
        display: inline-block;
        width: var(--buttons-size);
        min-width: calc(var(--buttons-size) * 0.75);
    }

    .tree-chevron-icon {
        display: inline-flex;
        transition: transform 0.1s ease-in-out;

        &.collapsed {
            transform: rotate(-90deg);
        }
    }

    .tree-row-content {
        flex: 1;
        min-width: 0;
    }

    .tree-drag-ghost {
        position: fixed;
        z-index: 100;
        transform: translate(8px, 8px);
        pointer-events: none;
        opacity: 0.85;
        padding: 0 0.5rem;
        border-radius: var(--border-radius, 5px);
        background: var(--canvas-elevated, var(--canvas));
        box-shadow: 0 2px 8px rgb(0 0 0 / 25%);
    }
</style>
