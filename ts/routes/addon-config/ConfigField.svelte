<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<script lang="ts">
    import { renderMarkdown } from "@tslib/helpers";
    import type { Choice } from "$lib/components/EnumSelector.svelte";
    import EnumSelectorRow from "$lib/components/EnumSelectorRow.svelte";
    import SwitchRow from "$lib/components/SwitchRow.svelte";

    import JsonRow from "./JsonRow.svelte";
    import NumberRow from "./NumberRow.svelte";
    import TextRow from "./TextRow.svelte";
    import Error from "../+error.svelte";
    import type { FieldDescriptor } from "./types";
    import Spacer from "$lib/components/Spacer.svelte";

    /** The JSON Schema property key. */
    export let key: string;
    /** The JSON Schema property definition. */
    export let prop: FieldDescriptor;
    /** Current value (bound two-way from parent). */
    export let value: unknown;
    /** Factory default value for the revert button. */
    export let defaultValue: unknown;

    function splitPropertyName(title: string): [string[], string] {
        if (title.includes(".")) {
            let parts = title.split(".");
            let settingName = parts.pop();
            if (settingName === undefined) {
                throw Error;
            }
            return [parts, settingName];
        }
        return [new Array(), title];
    }

    function capitalizeFirstLetter(val) {
        return String(val).charAt(0).toUpperCase() + String(val).slice(1);
    }

    function readableLabel(label: string): string {
        let parts = label.split(/(?=[A-Z])/);
        parts[0] = capitalizeFirstLetter(parts[0]);
        return parts.join(" ");
    }

    // Derive the display label: prefer schema title, fall back to key.
    // $: label = (prop.title as string | undefined) ?? key;
    $: setting = splitPropertyName(key as string);
    $: label = readableLabel(setting[1]);
    $: section = setting[0].map((x) => capitalizeFirstLetter(x));
    $: description = prop.description ?? "";
    $: descriptionHtml = description ? renderMarkdown(description) : "";

    // Determine which control to render.
    type FieldKind = "boolean" | "number" | "string" | "enum" | "json";
    function fieldKind(p: FieldDescriptor): FieldKind {
        if (Array.isArray(p.enum)) {
            return "enum";
        }
        if (p.type === "boolean") {
            return "boolean";
        }
        if (p.type === "integer" || p.type === "number") {
            return "number";
        }
        if (p.type === "string") {
            return "string";
        }
        return "json";
    }
    $: kind = fieldKind(prop);

    // Build Choice list for enum fields.
    $: choices = (() => {
        if (kind !== "enum") {
            return [] as Choice<unknown>[];
        }
        const enumValues = prop.enum ?? [];
        const enumDescriptions = prop.enumDescriptions ?? [];
        return enumValues.map(
            (v, i): Choice<unknown> => ({
                label: enumDescriptions[i] ?? String(v),
                value: v,
            }),
        );
    })();
</script>

<div class="config-field" tabindex="-1">
    {#if kind === "boolean"}
        <SwitchRow
            bind:value={value as boolean}
            defaultValue={defaultValue as boolean}
        >
            <div><span class="section-breadcrum">{section.join(">")}:&nbsp;</span><span>{label}</span></div>
            {#if descriptionHtml}
                <span class="description">{@html descriptionHtml}</span>
            {/if}
        </SwitchRow>
    {:else if kind === "number"}
        <NumberRow
            {prop}
            bind:value={value as number}
            defaultValue={defaultValue as number}
        >
            <span>{label}</span>
            {#if descriptionHtml}
                <span class="description">{@html descriptionHtml}</span>
            {/if}
        </NumberRow>
    {:else if kind === "string"}
        <TextRow
            bind:value={value as string}
            defaultValue={defaultValue as string}
            multiline={prop.multiline ?? false}
        >
            <span>{label}</span>
            {#if descriptionHtml}
                <span class="description">{@html descriptionHtml}</span>
            {/if}
        </TextRow>
    {:else if kind === "enum"}
        <EnumSelectorRow
            bind:value
            defaultValue
            {choices}
        >
            <span>{label}</span>
            {#if descriptionHtml}
                <span class="description">{@html descriptionHtml}</span>
            {/if}
        </EnumSelectorRow>
    {:else}
        <JsonRow bind:value {defaultValue} {label} {description} />
    {/if}
</div>

<style lang="scss">
    .config-field {
        padding: 8px;
        // Reserve the border space up-front so toggling it on focus doesn't
        // shift the layout by 1px.
        border: 1px solid transparent;
        border-radius: var(--border-radius);

        &:focus-within {
            border-color: lightblue;
        }

        // The container is focusable (tabindex=-1) so a click anywhere on it —
        // not just on the input — highlights it. Suppress the default focus
        // outline since the border above is our focus indicator.
        &:focus {
            outline: none;
        }

        :global(.description) {
            display: block;
            font-size: 0.8em;
            color: var(--fg-subtle);
            margin-top: 0.1em;
        }
    }

    .section-breadcrum {
        color: var(--fg-subtle);
    }
</style>
