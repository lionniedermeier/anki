<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<script lang="ts" generics="T">
    import { getContext } from "svelte";
    import type { Writable } from "svelte/store";
    import type { Snippet } from "svelte";
    import { selectKey } from "./context-keys";
    import DropdownItem from "./DropdownItem.svelte";

    interface Props {
        selected?: boolean;
        disabled?: boolean;
        id: string;
        value: T;
        element?: HTMLButtonElement;
        children?: Snippet;
    }

    let {
        selected = false,
        disabled = false,
        id,
        value,
        element = $bindable(undefined),
        children,
    }: Props = $props();

    const selectContext: Writable<{ value: T; setValue: Function }> =
        getContext(selectKey);
    const setValue = $selectContext.setValue;
</script>

<DropdownItem
    {disabled}
    {selected}
    id={selected ? id : undefined}
    active={value == $selectContext.value}
    role="option"
    onclick={() => setValue(value)}
    bind:buttonRef={element}
>
    {@render children?.()}
</DropdownItem>
