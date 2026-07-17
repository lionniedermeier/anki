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

    import StepsInput from "./StepsInput.svelte";

    interface Props {
        value: number[];
        defaultValue: number[];
        children?: Snippet;
    }

    let { value = $bindable(), defaultValue, children }: Props = $props();
</script>

<Row --cols={13}>
    <Col --col-size={7} breakpoint="xs">
        {@render children?.()}
    </Col>
    <Col --col-size={6} breakpoint="xs">
        <ConfigInput>
            <StepsInput bind:value />
            {#snippet revert()}
                <RevertButton bind:value {defaultValue} />
            {/snippet}
        </ConfigInput>
    </Col>
</Row>
