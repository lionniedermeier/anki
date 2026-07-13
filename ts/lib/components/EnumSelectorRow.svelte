<!--
    Copyright: Ankitects Pty Ltd and contributors
    License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<script lang="ts" generics="T">
    import type { Snippet } from "svelte";

    import Col from "./Col.svelte";
    import ConfigInput from "./ConfigInput.svelte";
    import EnumSelector, { type Choice } from "./EnumSelector.svelte";
    import RevertButton from "./RevertButton.svelte";
    import Row from "./Row.svelte";
    import type { Breakpoint } from "./types";

    interface EnumSelectorRowProps {
        value: T;
        defaultValue: T;
        breakpoint?: Breakpoint;
        choices: Choice<T>[];
        disabled?: boolean;
        disabledChoices?: T[];
        children?: Snippet;
    }

    let {
        value = $bindable(),
        defaultValue,
        breakpoint = "md",
        choices,
        disabled = false,
        disabledChoices = [],
        children,
    }: EnumSelectorRowProps = $props();
</script>

<Row --cols={13}>
    <Col --col-size={7} {breakpoint}>
        {@render children?.()}
    </Col>
    <Col --col-size={6} {breakpoint}>
        <ConfigInput>
            <EnumSelector bind:value {choices} {disabled} {disabledChoices} />
            {#snippet revert()}
                <RevertButton bind:value {defaultValue} />
            {/snippet}
        </ConfigInput>
    </Col>
</Row>
