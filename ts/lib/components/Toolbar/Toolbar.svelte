<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<script lang="ts">
    import type { Snippet } from "svelte";
    import { untrack } from "svelte";

    import type { ToolbarController } from "./Toolbar";
    import { createToolbar, setToolbarContext } from "./Toolbar";

    interface Props {
        /** Optional controller for hiding/disabling items by id. Created
         * internally when omitted. Pass your own to control items
         * programmatically from outside the toolbar. */
        controller?: ToolbarController;
        role?: string;
        /** Let items wrap onto multiple lines instead of overflowing. */
        wrap?: boolean;
        class?: string;
        children?: Snippet;
    }

    let {
        controller: controllerProp,
        role = "toolbar",
        wrap = false,
        class: className = "",
        children,
    }: Props = $props();

    // The controller is a stable handle established once; read it untracked so
    // context isn't tied to prop-identity changes (matches Tab.svelte).
    const controller = untrack(() => controllerProp ?? createToolbar());

    setToolbarContext({ controller });
</script>

<div class="toolbar {className}" class:wrap {role}>
    {@render children?.()}
</div>

<style lang="scss">
    .toolbar {
        display: flex;
        width: 100%;
        align-items: center;
        gap: var(--toolbar-gap, 0.5rem);

        &.wrap {
            flex-wrap: wrap;
        }
    }
</style>
