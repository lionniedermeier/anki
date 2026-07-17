<!--
    Copyright: Ankitects Pty Ltd and contributors
    License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<script lang="ts">
    import type { Snippet } from "svelte";

    import ConfigInput from "$lib/components/ConfigInput.svelte";
    import RevertButton from "$lib/components/RevertButton.svelte";

    import ParamsInput from "./ParamsInput.svelte";

    interface Props {
        value: number[];
        defaultValue: number[];
        children?: Snippet;
    }

    let { value = $bindable(), defaultValue, children }: Props = $props();
</script>

{@render children?.()}
<ConfigInput>
    <ParamsInput bind:value />
    {#snippet revert()}
        <RevertButton bind:value {defaultValue} />
    {/snippet}
</ConfigInput>
