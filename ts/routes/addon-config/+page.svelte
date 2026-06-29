<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<script lang="ts">
    import { closeAddonConfig, setAddonConfig } from "@generated/backend";
    import LabelButton from "$lib/components/LabelButton.svelte";
    import ConfigContainer from "./ConfigContainer.svelte";

    import type { PageData } from "./$types";
    import ConfigField from "./ConfigField.svelte";
    import type { ConfigProperties, ConfigValues } from "./types";

    export let data: PageData;

    // Parse the JSON payloads supplied by the Python backend.
    // schema_json is always the normalized properties map (field key → descriptor).
    $: properties = JSON.parse(data.schemaJson) as ConfigProperties;
    $: defaults = JSON.parse(data.defaultsJson) as ConfigValues;
    $: values = JSON.parse(data.configJson) as ConfigValues;

    let errorMessage = "";

    async function onSave(): Promise<void> {
        errorMessage = "";
        try {
            await setAddonConfig({ configJson: JSON.stringify(values) });
            await closeAddonConfig({});
        } catch (err) {
            errorMessage = String(err);
        }
    }

    async function onCancel(): Promise<void> {
        await closeAddonConfig({});
    }

    function onRestoreDefaults(): void {
        values = { ...defaults };
    }
</script>

<div class="addon-config">
    <ConfigContainer title={data.title}>
        {#if data.helpHtml}
            <div class="help-html">{@html data.helpHtml}</div>
        {/if}

        <div class="fields">
            {#each Object.entries(properties) as [key, prop] (key)}
                <ConfigField
                    {key}
                    {prop}
                    defaultValue={defaults[key]}
                    bind:value={values[key]}
                />
            {/each}
        </div>
    </ConfigContainer>

    {#if errorMessage}
        <div class="error-message">{errorMessage}</div>
    {/if}

    <div class="footer">
        <LabelButton
            --border-left-radius="5px"
            --border-right-radius="5px"
            on:click={onRestoreDefaults}
        >
            Restore Defaults
        </LabelButton>
        <div class="spacer"></div>
        <LabelButton
            --border-left-radius="5px"
            --border-right-radius="5px"
            on:click={onCancel}
        >
            Cancel
        </LabelButton>
        <LabelButton
            --border-left-radius="5px"
            --border-right-radius="5px"
            primary
            on:click={onSave}
        >
            Save
        </LabelButton>
    </div>
</div>

<style lang="scss">
    .addon-config {
        display: flex;
        flex-direction: column;
        height: 100vh;
        padding: 0.75rem;
        box-sizing: border-box;
        gap: 0.5rem;
        --buttons-size: 2rem;
    }

    .fields {
        display: flex;
        flex-direction: column;
        gap: 0.25rem;
        padding: 0.5rem 0;
    }

    .help-html {
        padding: 0.5rem 0;
        color: var(--fg-subtle);
        font-size: 0.9em;
    }

    .error-message {
        color: var(--state-suspended);
        padding: 0.25rem 0.5rem;
        border-radius: var(--border-radius);
        border: 1px solid var(--state-suspended);
        font-size: 0.9em;
    }

    .footer {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding-top: 0.25rem;
        border-top: 1px solid var(--border);
    }

    .spacer {
        flex: 1;
    }
</style>
