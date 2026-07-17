<!--
    Copyright: Ankitects Pty Ltd and contributors
    License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<script lang="ts">
    import type { Snippet } from "svelte";

    import Col from "$lib/components/Col.svelte";
    import ConfigInput from "$lib/components/ConfigInput.svelte";
    import RevertButton from "$lib/components/RevertButton.svelte";
    import Row from "$lib/components/Row.svelte";
    import SpinBox from "$lib/components/SpinBox.svelte";

    interface Props {
        value: number;
        defaultValue: number;
        min?: number;
        max?: number;
        children?: Snippet;
        tabs?: Snippet;
    }

    let {
        value = $bindable(),
        defaultValue,
        min = 0,
        max = 9999,
        children,
        tabs,
    }: Props = $props();
</script>

<Row --cols={13}>
    <Col --col-size={7} breakpoint="xs">
        {@render children?.()}
    </Col>
    <Col --col-size={6} breakpoint="xs">
        <Row class="flex-grow-1">
            {@render tabs?.()}
            <ConfigInput>
                <SpinBox bind:value {min} {max} />
                {#snippet revert()}
                    <RevertButton bind:value {defaultValue} />
                {/snippet}
            </ConfigInput>
        </Row>
    </Col>
</Row>
