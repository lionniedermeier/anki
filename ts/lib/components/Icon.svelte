<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<script lang="ts">
    import type { IconData } from "./types";

    interface IconProps {
        icon: IconData;
    }

    let { icon }: IconProps = $props();

    // @ts-expect-error internal property
    const Component = $derived(import.meta.env ? (icon.component as any) : null);
</script>

{#if Component}
    <Component />
{:else}
    {@html icon.url}
{/if}
