<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<script lang="ts">
    import type { Snippet } from "svelte";

    interface ButtonGroupProps {
        id?: string;
        class?: string;
        size?: number;
        wrap?: boolean;
        children?: Snippet;
    }

    let {
        id = undefined,
        class: className = "",
        size = undefined,
        wrap = undefined,
        children,
    }: ButtonGroupProps = $props();

    const buttonSize = $derived(size ? `--buttons-size: ${size}rem; ` : "");
    const buttonWrap = $derived.by(() => {
        if (wrap === undefined) {
            return "";
        }
        return wrap ? `--buttons-wrap: wrap; ` : `--buttons-wrap: nowrap; `;
    });

    const style = $derived(buttonSize + buttonWrap);
</script>

<div {id} class="button-group btn-group {className}" {style} dir="ltr" role="group">
    {@render children?.()}
</div>

<style lang="scss">
    .button-group {
        display: flex;
        flex-flow: row var(--buttons-wrap);
    }
</style>
