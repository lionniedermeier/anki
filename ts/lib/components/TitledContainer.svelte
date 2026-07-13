<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<script lang="ts">
    import type { Snippet } from "svelte";

    import { pageTheme } from "$lib/sveltelib/theme";

    const rtl: boolean = window.getComputedStyle(document.body).direction == "rtl";

    interface TitledContainerProps {
        id?: string;
        class?: string;
        title: string;
        tooltip?: Snippet;
        children?: Snippet;
    }

    let {
        id = undefined,
        class: className = "",
        title,
        tooltip,
        children,
    }: TitledContainerProps = $props();
</script>

<div
    {id}
    class="container {className}"
    class:light={!$pageTheme.isDark}
    class:dark={$pageTheme.isDark}
    class:rtl
    style:--gutter-block="2px"
    style:--container-margin="0"
>
    <div class="position-relative">
        <h4>
            {title}
        </h4>
        <div class="help-badge position-absolute" class:rtl>
            {@render tooltip?.()}
        </div>
    </div>
    {@render children?.()}
</div>

<style lang="scss">
    @use "../sass/elevation" as *;
    .container {
        width: 100%;
        background: var(--canvas-elevated);
        border: 1px solid var(--border-subtle);
        border-radius: var(--border-radius-medium, 10px);

        &.light {
            @include elevation(3);
        }
        &.dark {
            @include elevation(4);
        }

        padding: 1rem 1.75rem 0.75rem 1.25rem;
        &.rtl {
            padding: 1rem 1.25rem 0.75rem 1.75rem;
        }
        page-break-inside: avoid;
    }
    .help-badge {
        right: 0;
        top: 0;
        color: #555;
        &.rtl {
            right: unset;
            left: 0;
        }
    }

    :global(.night-mode) .help-badge {
        color: var(--fg);
    }
</style>
