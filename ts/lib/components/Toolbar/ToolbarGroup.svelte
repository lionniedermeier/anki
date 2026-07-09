<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<script lang="ts">
    import type { Snippet } from "svelte";

    import { getToolbarContext } from "./Toolbar";

    interface Props {
        /** When set, the whole group can be hidden via the controller
         * (`controller.hide(id)`) or the declarative `hidden` prop. */
        id?: string;
        hidden?: boolean;
        class?: string;
        children?: Snippet;
    }

    let { id, hidden = false, class: className = "", children }: Props = $props();

    // Throws if not rendered inside a <Toolbar>.
    const { hidden: hiddenIds } = getToolbarContext().controller;
    const isHidden = $derived(hidden || (id !== undefined && $hiddenIds.has(id)));
</script>

{#if !isHidden}
    <div class="toolbar-group {className}" role="group">
        {@render children?.()}
    </div>
{/if}

<style lang="scss">
    .toolbar-group {
        display: flex;
        align-items: center;
        gap: var(--toolbar-group-gap, 0.125rem);
    }

    // Separate adjacent groups, mirroring the `.section + .section` idiom. The
    // preceding sibling is `:global` because each group is its own component
    // instance, so Svelte's scoped-CSS analysis can't see the adjacency and
    // would otherwise prune this rule.
    :global(.toolbar-group) + .toolbar-group {
        padding-inline-start: var(--toolbar-gap, 0.5rem);
        border-inline-start: 1px solid var(--border-subtle);
    }
</style>
