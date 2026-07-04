<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<script lang="ts">
    import { onMount, setContext } from "svelte";
    import { writable } from "svelte/store";

    import type { PaneState, SplitViewContext } from "./SplitView";
    import {
        loadPaneLayout,
        resizeDivider,
        savePaneLayout,
        splitViewKey,
        toggleCollapsed as toggleCollapsedState,
    } from "./SplitView";

    /** Persistence key; pane sizes/collapsed state are remembered across
     * reloads under this id (see SplitView.ts's storageKey). */
    export let id: string;
    export let direction: "horizontal" | "vertical" = "horizontal";

    let className = "";
    export { className as class };

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

    function resize(paneId: string, delta: number): void {
        const index = registered.findIndex((pane) => pane.id === paneId);
        if (index === -1) {
            return;
        }
        persist(resizeDivider(registered, index, delta));
    }

    function toggleCollapsed(paneId: string): void {
        persist(toggleCollapsedState(registered, paneId));
    }

    setContext<SplitViewContext>(splitViewKey, {
        panes,
        direction,
        register,
        unregister,
        resize,
        toggleCollapsed,
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
    <slot />
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
