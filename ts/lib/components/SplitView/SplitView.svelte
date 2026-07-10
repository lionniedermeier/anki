<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<script lang="ts">
    import type { Snippet } from "svelte";
    import { onMount, setContext } from "svelte";
    import { writable } from "svelte/store";

    import type { PaneState, SplitViewContext } from "./SplitView";
    import {
        appliedDividerDelta,
        loadPaneLayout,
        resizeDivider,
        savePaneLayout,
        splitViewKey,
        toggleCollapsed as toggleCollapsedState,
    } from "./SplitView";

    interface SplitViewProps {
        /** Persistence key; pane sizes/collapsed state are remembered across
         * reloads under this id (see SplitView.ts's storageKey). */
        id: string;
        direction?: "horizontal" | "vertical";
        class?: string;
        children?: Snippet;
    }

    let {
        id,
        direction = "horizontal",
        class: className = "",
        children,
    }: SplitViewProps = $props();

    const panes = writable<PaneState[]>([]);
    let registered: PaneState[] = [];
    let layoutLoaded = false;

    function register(pane: PaneState): void {
        registered = [...registered, pane];
        panes.set(registered);
    }

    function unregister(paneId: string): void {
        registered = registered.filter((pane) => pane.id !== paneId);
        panes.set(registered);
    }

    function persist(next: PaneState[]): void {
        registered = next;
        panes.set(next);
        if (layoutLoaded) {
            savePaneLayout(id, next);
        }
    }

    function resize(paneId: string, delta: number): number {
        const index = registered.findIndex((pane) => pane.id === paneId);
        if (index === -1 || index + 1 >= registered.length) {
            return 0;
        }
        const before = registered;
        const next = resizeDivider(before, index, delta);
        persist(next);
        return appliedDividerDelta(before, next, index);
    }

    function toggleCollapsed(paneId: string): void {
        persist(toggleCollapsedState(registered, paneId));
    }

    /** Visibility is driven by the owning view, not by the user, so it is
     * applied without going through persist(). */
    function setHidden(paneId: string, hidden: boolean): void {
        const current = registered.find((pane) => pane.id === paneId);
        if (!current || (current.hidden ?? false) === hidden) {
            return;
        }
        registered = registered.map((pane) =>
            pane.id === paneId ? { ...pane, hidden } : pane,
        );
        panes.set(registered);
    }

    setContext<SplitViewContext>(splitViewKey, {
        panes,
        get direction() {
            return direction;
        },
        register,
        unregister,
        resize,
        toggleCollapsed,
        setHidden,
    });

    // Slotted SplitPane children register themselves during their own
    // instantiation, which happens while this component's fragment is being
    // created - i.e. after this script block runs, but before onMount. Only
    // once mounted is `registered` guaranteed to hold every declared pane,
    // so the persisted layout is overlaid here rather than at the top level.
    onMount(() => {
        persist(loadPaneLayout(id, registered));
        layoutLoaded = true;
    });
</script>

<div class="split-view {className}" class:vertical={direction === "vertical"}>
    {@render children?.()}
</div>

<style lang="scss">
    .split-view {
        display: flex;
        flex-direction: row;
        align-items: stretch;
        height: 100%;
        min-height: 0;

        &.vertical {
            flex-direction: column;
        }
    }
</style>
