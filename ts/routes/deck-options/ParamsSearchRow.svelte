<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<script lang="ts">
    import ConfigInput from "$lib/components/ConfigInput.svelte";

    interface Props {
        value: string;
        placeholder: string;
    }

    let { value = $bindable(), placeholder }: Props = $props();
</script>

<ConfigInput>
    <input type="text" bind:value {placeholder} class="w-100 mb-1" />
</ConfigInput>
