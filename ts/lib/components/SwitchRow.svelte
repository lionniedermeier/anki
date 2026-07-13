<!--
    Copyright: Ankitects Pty Ltd and contributors
    License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<script lang="ts">
    import type { Snippet } from "svelte";

    import Col from "./Col.svelte";
    import ConfigInput from "./ConfigInput.svelte";
    import Label from "./Label.svelte";
    import RevertButton from "./RevertButton.svelte";
    import Row from "./Row.svelte";
    import Switch from "./Switch.svelte";

    interface SwitchRowProps {
        value: boolean;
        defaultValue: boolean;
        disabled?: boolean;
        children?: Snippet;
    }

    let {
        value = $bindable(),
        defaultValue,
        disabled = false,
        children,
    }: SwitchRowProps = $props();

    const id = Math.random().toString(36).substring(2);
</script>

<Row --cols={6}>
    <Col --col-size={4}>
        <Label for={id} preventMouseClick>{@render children?.()}</Label>
    </Col>
    <Col --col-justify="flex-end">
        <ConfigInput grow={false}>
            <Switch {id} bind:value {disabled} />
            {#snippet revert()}
                <RevertButton bind:value {defaultValue} />
            {/snippet}
        </ConfigInput>
    </Col>
</Row>
