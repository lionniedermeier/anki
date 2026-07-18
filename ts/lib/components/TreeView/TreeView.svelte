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
    import {
        collectSubtreeIds,
        flattenVisible,
        parentIndex,
        type TreeViewNode,
    } from "./TreeView";

    interface TreeViewProps {
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
         * rows carry their own controls.
         * `source` distinguishes a direct pointer click from the cursor
         * landing on a row as a side effect of arrow-key traversal (e.g.
         * moving to a parent), so callers whose ids don't all map to
         * independently-selectable content (like a group heading) can treat
         * the two differently. */
        onSelect?: (id: string, source: "pointer" | "keyboard") => void;
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
    }: TreeViewProps = $props();

    const visibleRows = $derived(flattenVisible(nodes));
    const nodeById = $derived(new Map(visibleRows.map((r) => [r.node.id, r.node])));
    const rowIndexById = $derived(new Map(visibleRows.map((r, i) => [r.node.id, i])));
    const selectable = $derived(onSelect !== undefined);

    let containerEl: HTMLElement | undefined = $state();

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

    // Keyboard navigation tracks the "current" row via `selectedId` rather
    // than native per-row DOM focus: rows are removed/recreated whenever the
    // tree data changes, and in Anki's embedded webview, focus placed on a
    // row via a plain `element.focus()` call is not reliably retained. Real
    // browser focus instead stays on this stable container div for the
    // lifetime of the component (see Select.svelte for the same pattern),
    // and the currently-selected row doubles as the visual keyboard cursor.
    function focusContainer(): void {
        containerEl?.focus();
    }

    function scrollRowIntoView(id: string): void {
        containerEl
            ?.querySelector<HTMLElement>(`[data-tree-row-id="${CSS.escape(id)}"]`)
            ?.scrollIntoView({ block: "nearest" });
    }

    function selectRow(id: string, source: "pointer" | "keyboard"): void {
        onSelect?.(id, source);
        scrollRowIntoView(id);
        // Re-assert container focus on every selection path (not just
        // clicks), so a keyboard-driven selection that triggers a focus
        // steal elsewhere on the page (e.g. an async search re-render) is
        // self-healed the same way clicks already are - otherwise all
        // subsequent key presses would silently go nowhere.
        focusContainer();
    }

    function moveTo(targetIndex: number, event: KeyboardEvent): void {
        if (targetIndex < 0 || targetIndex >= visibleRows.length) {
            return;
        }
        event.preventDefault();
        selectRow(visibleRows[targetIndex].node.id, "keyboard");
    }

    function onTreeKeyDown(event: KeyboardEvent): void {
        if (!selectable || visibleRows.length === 0) {
            return;
        }

        const index = selectedId !== null ? rowIndexById.get(selectedId) : undefined;

        switch (event.key) {
            case "ArrowDown":
                moveTo(index === undefined ? 0 : index + 1, event);
                break;
            case "ArrowUp":
                if (index === undefined) {
                    moveTo(visibleRows.length - 1, event);
                } else {
                    moveTo(index - 1, event);
                }
                break;
            case "ArrowRight": {
                if (index === undefined) {
                    break;
                }
                const node = visibleRows[index].node;
                event.preventDefault();
                if (node.children.length > 0 && node.collapsed) {
                    onToggle?.(node.id);
                } else if (node.children.length > 0) {
                    moveTo(index + 1, event);
                }
                break;
            }
            case "ArrowLeft": {
                if (index === undefined) {
                    break;
                }
                const node = visibleRows[index].node;
                event.preventDefault();
                if (node.children.length > 0 && !node.collapsed) {
                    onToggle?.(node.id);
                } else {
                    const p = parentIndex(visibleRows, index);
                    if (p !== null) {
                        selectRow(visibleRows[p].node.id, "keyboard");
                    }
                }
                break;
            }
        }
    }

    function toggle(event: MouseEvent, id: string): void {
        // Expanding a node must not also select it.
        event.stopPropagation();
        onToggle?.(id);
    }

    function onChevronKeyDown(event: KeyboardEvent, id: string): void {
        if (event.key === "Enter" || event.key === " ") {
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

<!-- The container is the sole focusable/keyboard-handled surface; rows are
selected by id rather than individually focused (see the comment above
onTreeKeyDown), so the compiler can't infer their interactivity relationship. -->
<!-- svelte-ignore a11y_no_static_element_interactions -->
<!-- svelte-ignore a11y_no_noninteractive_tabindex -->
<div
    class="tree-view"
    class:drag-over-top-level={dragOverId === TOP_LEVEL}
    bind:this={containerEl}
    tabindex={selectable ? 0 : undefined}
    onkeydown={onTreeKeyDown}
>
    {#each visibleRows as { node, depth } (node.id)}
        <!-- svelte-ignore a11y_click_events_have_key_events -->
        <!-- svelte-ignore a11y_no_static_element_interactions -->
        <div
            class="tree-row"
            class:selectable
            class:selected={selectable && node.id === selectedId}
            class:drag-over={dragOverId === node.id}
            class:dragged={dragging && draggedNode?.id === node.id}
            style="padding-inline-start: calc(8px + {depth * indent}rem)"
            data-tree-row-id={node.id}
            onpointerdown={(event) => onPointerDown(event, node)}
            onclick={() => selectRow(node.id, "pointer")}
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
        min-height: var(--tree-row-height, 40px);
        padding-inline-end: 8px;
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
        // Explicit size (not align-self: stretch + aspect-ratio) so the
        // empty spacer used for childless rows doesn't collapse to 0 width.
        width: var(--tree-row-height, 40px);
        height: var(--tree-row-height, 40px);

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
        box-shadow: 0 2px 8px var(--shadow-subtle);
    }
</style>
