<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<script lang="ts">
    import type { Snippet } from "svelte";

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
    .container {
        width: 100%;
        background: var(--canvas-elevated);
        border: 1px solid var(--border-subtle);
        border-radius: var(--border-radius-medium, 10px);

        padding: 1rem 1.75rem 0.75rem 1.25rem;
        &.rtl {
            padding: 1rem 1.25rem 0.75rem 1.75rem;
        }
        page-break-inside: avoid;
    }
    .help-badge {
        right: 0;
        top: 0;
        color: var(--fg-subtle);
        &.rtl {
            right: unset;
            left: 0;
        }
    }
</style>
