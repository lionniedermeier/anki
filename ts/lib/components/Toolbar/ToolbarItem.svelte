<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<script lang="ts">
    import type { Snippet } from "svelte";

    import { getToolbarContext } from "./Toolbar";

    interface Props {
        id: string;
        /** Hide this item. Combined (OR) with the controller's state. */
        hidden?: boolean;
        /** Disable this item. Combined (OR) with the controller's state. The
         * resolved value is passed into the `children` snippet so the wrapped
         * control can wire its own `disabled` attribute. */
        disabled?: boolean;
        class?: string;
        /** Receives the resolved disabled state:
         * `{#snippet children(disabled)}<button {disabled}>…</button>{/snippet}` */
        children?: Snippet<[boolean]>;
    }

    let {
        id,
        hidden = false,
        disabled = false,
        class: className = "",
        children,
    }: Props = $props();

    // Throws if not rendered inside a <Toolbar>.
    const { hidden: hiddenIds, disabled: disabledIds } = getToolbarContext().controller;
    const isHidden = $derived(hidden || $hiddenIds.has(id));
    const isDisabled = $derived(disabled || $disabledIds.has(id));
</script>

{#if !isHidden}
    <!-- display:contents so the wrapper doesn't affect toolbar layout. -->
    <div class="toolbar-item {className}" class:disabled={isDisabled}>
        {@render children?.(isDisabled)}
    </div>
{/if}

<style lang="scss">
    .toolbar-item {
        display: contents;
    }
</style>
