<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<script lang="ts" generics="T extends TreeViewNode">
    import type { Snippet } from "svelte";
    import { onDestroy, onMount } from "svelte";

    import { chevronDown } from "../icons";
    import Icon from "../Icon.svelte";
    import IconConstrain from "../IconConstrain.svelte";
    import { collectSubtreeIds, flattenVisible, type TreeViewNode } from "./TreeView";

    interface Props {
        nodes: T[];
        /** Indentation per depth level, in rem. */
        indent?: number;
        /** Renders an always-present drop target (via the `topLevel` snippet)
         * that reports a null targetId, for un-parenting a dragged row. */
        topLevelDroppable?: boolean;
        /** Id of the selected row. Only meaningful together with `onSelect`. */
        selectedId?: string | null;
        onToggle?: (id: string) => void;
        /** When provided, rows become the clickable and focusable surface, and
         * paint hover/selected states. Omit for a presentational tree whose
         * rows carry their own controls. */
        onSelect?: (id: string) => void;
        onDragdrop?: (sourceId: string, targetId: string | null) => void;
        row: Snippet<[T, number]>;
        topLevel?: Snippet;
    }

    let {
        nodes,
        indent = 1.25,
        topLevelDroppable = false,
        selectedId = null,
        onToggle,
        onSelect,
        onDragdrop,
        row,
        topLevel,
    }: Props = $props();

    const visibleRows = $derived(flattenVisible(nodes));
    const nodeById = $derived(new Map(visibleRows.map((r) => [r.node.id, r.node])));
    const selectable = $derived(onSelect !== undefined);

    const TOP_LEVEL = "__top_level__";
    // Pointer movement (px) required before a press becomes a drag rather than
    // a click. Anki's webview does not support native HTML5 drag-and-drop
    // reliably.
    const DRAG_THRESHOLD = 5;

    let pointerStart: { x: number; y: number; node: T } | null = null;
    let dragging = $state(false);
    let draggedNode: T | null = $state(null);
    let dragOverId: string | null = $state(null);
    let excludedIds = new Set<string>();
    let ghostX = $state(0);
    let ghostY = $state(0);
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
                onDragdrop?.(sourceId, null);
            } else if (dragOverId) {
                onDragdrop?.(sourceId, dragOverId);
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

    function onRowKeyDown(event: KeyboardEvent, id: string): void {
        if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            onSelect?.(id);
        }
    }

    function toggle(event: MouseEvent, id: string): void {
        // Expanding a node must not also select it.
        event.stopPropagation();
        onToggle?.(id);
    }

    function onChevronKeyDown(event: KeyboardEvent, id: string): void {
        if (event.key === "Enter" || event.key === " ") {
            // Toggle on the chevron, and stop the row from also handling it.
            event.preventDefault();
            event.stopPropagation();
            onToggle?.(id);
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

<div class="tree-view" class:drag-over-top-level={dragOverId === TOP_LEVEL}>
    {#each visibleRows as { node, depth } (node.id)}
        <!-- The role and tabindex are only set when the tree is selectable,
        which the compiler can't see through. -->
        <!-- svelte-ignore a11y_no_noninteractive_tabindex -->
        <div
            class="tree-row"
            class:selectable
            class:selected={selectable && node.id === selectedId}
            class:drag-over={dragOverId === node.id}
            class:dragged={dragging && draggedNode?.id === node.id}
            style="padding-inline-start: {depth * indent}rem"
            data-tree-row-id={node.id}
            role={selectable ? "button" : undefined}
            tabindex={selectable ? 0 : undefined}
            onpointerdown={(event) => onPointerDown(event, node)}
            onclick={() => onSelect?.(node.id)}
            onkeydown={(event) => onRowKeyDown(event, node.id)}
        >
            {#if node.children.length > 0}
                <div
                    class="tree-chevron interactive"
                    role="button"
                    tabindex="0"
                    aria-expanded={!node.collapsed}
                    onclick={(event) => toggle(event, node.id)}
                    onkeydown={(event) => onChevronKeyDown(event, node.id)}
                >
                    <span class="tree-chevron-icon" class:collapsed={node.collapsed}>
                        <IconConstrain iconSize={100}>
                            <Icon icon={chevronDown} />
                        </IconConstrain>
                    </span>
                </div>
            {:else}
                <div class="tree-chevron"></div>
            {/if}
            <div class="tree-row-content">
                {@render row(node, depth)}
            </div>
        </div>
    {/each}
    {#if topLevelDroppable && dragging}
        <div class="tree-top-level-drop" class:drag-over={dragOverId === TOP_LEVEL}>
            {@render topLevel?.()}
        </div>
    {/if}
</div>

{#if dragging && draggedNode}
    <div class="tree-drag-ghost" style="left: {ghostX}px; top: {ghostY}px">
        {@render row(draggedNode!, 0)}
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
        width: 100%;
        padding-inline-end: 0.25rem;
        border-radius: var(--border-radius, 5px);

        &.selectable {
            cursor: pointer;
            user-select: none;

            &:hover {
                background: var(--highlight-bg);
                color: var(--highlight-fg);
            }

            &.selected {
                background: var(--selected-bg);
                color: var(--selected-fg);
            }
        }

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

    .tree-chevron {
        flex: none;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 40px;
        height: 40px;

        &.interactive {
            cursor: pointer;
        }
    }

    .tree-chevron-icon {
        display: inline-flex;
        transition: transform 0.1s ease-in-out;

        &.collapsed {
            transform: rotate(-90deg);
        }
    }

    .tree-row-content {
        flex: 1 1 auto;
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
