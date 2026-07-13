<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<script module lang="ts">
    export interface Choice<T> {
        label: string;
        value: T;
    }
</script>

<script lang="ts" generics="T">
    import Select from "./Select.svelte";

    interface EnumSelectorProps {
        value: T;
        choices?: Choice<T>[];
        disabled?: boolean;
        disabledChoices?: T[];
    }

    let {
        value = $bindable(),
        choices = [],
        disabled = false,
        disabledChoices = [],
    }: EnumSelectorProps = $props();

    const label = $derived(choices.find((c) => c.value === value)?.label);
    const parser = $derived((item: Choice<T>) => ({
        content: item.label,
        value: item.value,
        disabled: disabledChoices.includes(item.value),
    }));
</script>

<Select bind:value {label} {disabled} list={choices} {parser} />
