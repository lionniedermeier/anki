<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<!-- A spinbox row driven by JSON Schema minimum/maximum/multipleOf. -->
<script lang="ts">
    import ConfigInput from "$lib/components/ConfigInput.svelte";
    import Label from "$lib/components/Label.svelte";
    import RevertButton from "$lib/components/RevertButton.svelte";
    import Row from "$lib/components/Row.svelte";
    import SpinBox from "$lib/components/SpinBox.svelte";

    import type { FieldDescriptor } from "./types";

    /** JSON Schema property definition (for min/max/step). */
    export let prop: FieldDescriptor;
    export let value: number;
    export let defaultValue: number;

    $: min = prop.minimum ?? 0;
    $: max = prop.maximum ?? 9999;
    $: step = prop.multipleOf ?? 1;

    const id = Math.random().toString(36).substring(2);
</script>

<Row --cols={13}>
    <div>
        <Label for={id} preventMouseClick><slot /></Label>
        <ConfigInput>
            <SpinBox bind:value {min} {max} {step} />
            {#snippet revert()}
                <RevertButton bind:value {defaultValue} />
            {/snippet}
        </ConfigInput>
    </div>
</Row>
