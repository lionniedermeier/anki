<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<script lang="ts">
    import type { Snippet } from "svelte";
    import { setContext } from "svelte";
    import { writable } from "svelte/store";

    import type { TabState, TabViewContext } from "./TabView";
    import { tabViewKey } from "./TabView";

    interface TabViewProps {
        id: string;
        /** Stretch the tabs to share the full width of the tab bar equally
         * instead of sizing each to its content. */
        grow?: boolean;
        class?: string;
        children?: Snippet;
    }

    let { id, grow = false, class: className = "", children }: TabViewProps =
        $props();

    const tabs = writable<TabState[]>([]);
    const activeId = writable<string | null>(null);
    let registered: TabState[] = [];

    function register(tab: TabState): void {
        registered = [...registered, tab];
        tabs.set(registered);
        // Seed the active tab from the first one to register.
        activeId.update((current) => current ?? tab.id);
    }

    function unregister(tabId: string): void {
        registered = registered.filter((tab) => tab.id !== tabId);
        tabs.set(registered);
        // If the active tab went away, fall back to the first remaining one.
        activeId.update((current) =>
            current === tabId ? (registered[0]?.id ?? null) : current,
        );
    }

    function setActive(tabId: string): void {
        activeId.set(tabId);
    }

    setContext<TabViewContext>(tabViewKey, {
        tabs,
        activeId,
        register,
        unregister,
        setActive,
    });
</script>

<div class="tab-view {className}">
    <div class="tab-bar" class:grow role="tablist">
        {#each $tabs as tab (tab.id)}
            <button
                type="button"
                role="tab"
                class="tab"
                class:active={$activeId === tab.id}
                aria-selected={$activeId === tab.id}
                onclick={() => setActive(tab.id)}
            >
                {tab.title}
            </button>
        {/each}
    </div>
    <div class="tab-content" data-tab-view={id}>
        {@render children?.()}
    </div>
</div>

<style lang="scss">
    .tab-view {
        display: flex;
        flex-direction: column;
        height: 100%;
        min-height: 0;
    }

    .tab-bar {
        display: flex;
        align-items: flex-end;
        flex: 0 0 auto;
        gap: 0.125rem;
        padding: 0.25rem 0.25rem 0;
        border-bottom: 1px solid var(--border-subtle);
        background: var(--canvas);
        // Scroll the tabs when the pane is too narrow rather than letting them
        // shrink or wrap.
        overflow-x: auto;

        // Stretch tabs to share the full width equally.
        &.grow .tab {
            flex: 1 1 0;
            text-align: center;
        }
    }

    .tab {
        // A full, always-present 1px border keeps the box the same size in
        // every state, so hover/active only change colours - never dimensions
        // (which previously nudged the tab content by a pixel).
        box-sizing: border-box;
        appearance: none;
        margin: 0;
        // Keep each tab at its natural size; never shrink or wrap when the pane
        // gets too small to fit them all.
        flex: 0 0 auto;
        white-space: nowrap;
        padding: 0.4rem 0.8rem;
        border: 1px solid transparent;
        border-top-left-radius: 0.35rem;
        border-top-right-radius: 0.35rem;
        background: transparent;
        color: var(--fg-subtle);
        line-height: 1.2;
        cursor: pointer;

        &:hover {
            color: var(--fg);
            background: var(--canvas-inset);
        }

        &.active {
            color: var(--fg);
            background: var(--canvas-elevated);
            border-color: var(--border-subtle);
        }
    }

    .tab-content {
        flex: 1 1 auto;
        min-height: 0;
        overflow: hidden;
    }
</style>
