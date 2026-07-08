<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<script lang="ts">
    import type { Snippet } from "svelte";
    import { getContext, onDestroy, untrack } from "svelte";

    import type { TabViewContext } from "./TabView";
    import { tabViewKey } from "./TabView";

    interface TabProps {
        id: string;
        title: string;
        children?: Snippet;
    }

    let { id, title, children }: TabProps = $props();

    const ctx = getContext<TabViewContext>(tabViewKey);
    if (!ctx) {
        throw new Error("Tab must be used inside a TabView");
    }

    // Register during instantiation so the TabView's tab bar picks this up
    // while its fragment is being created (see SplitPane for the same pattern).
    // id/title are read untracked to capture their initial values.
    untrack(() => ctx.register({ id, title }));
    onDestroy(() => ctx.unregister(id));

    const { activeId } = ctx;
    const active = $derived($activeId === id);
</script>

{#if active}
    <div role="tabpanel" class="tab-panel">
        {@render children?.()}
    </div>
{/if}

<style lang="scss">
    .tab-panel {
        height: 100%;
        min-height: 0;
        overflow: auto;
    }
</style>
