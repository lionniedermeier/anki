<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<!--
Fallback for object/array/other schema fields: a small raw-JSON textarea.
Validates JSON on blur and reverts to the previous valid value on parse error.
-->
<script lang="ts">
    export let value: unknown;
    export let defaultValue: unknown;
    export let label: string;
    export let description: string;

    let text = JSON.stringify(value, null, 2);
    let parseError = "";

    function onBlur(): void {
        try {
            value = JSON.parse(text);
            parseError = "";
        } catch {
            parseError = "Invalid JSON";
            text = JSON.stringify(value, null, 2);
        }
    }

    function onRestore(): void {
        value = defaultValue;
        text = JSON.stringify(value, null, 2);
        parseError = "";
    }
</script>

<div class="json-row">
    <div class="json-header">
        <span class="json-label">{label}</span>
        {#if description}
            <span class="json-description">{description}</span>
        {/if}
        <button class="revert-btn" on:click={onRestore} title="Restore default">
            ↺
        </button>
    </div>
    <textarea
        class="json-textarea"
        bind:value={text}
        on:blur={onBlur}
        rows={3}
    ></textarea>
    {#if parseError}
        <span class="parse-error">{parseError}</span>
    {/if}
</div>

<style lang="scss">
    .json-row {
        display: flex;
        flex-direction: column;
        gap: 0.25rem;
        padding: 0.25rem 0;
    }

    .json-header {
        display: flex;
        align-items: baseline;
        gap: 0.5rem;
    }

    .json-label {
        font-weight: 500;
    }

    .json-description {
        font-size: 0.8em;
        color: var(--fg-subtle);
        flex: 1;
    }

    .revert-btn {
        background: none;
        border: none;
        cursor: pointer;
        color: var(--fg-subtle);
        font-size: 1rem;
        padding: 0 0.2rem;

        &:hover {
            color: var(--fg);
        }
    }

    .json-textarea {
        width: 100%;
        font-family: monospace;
        font-size: 0.85em;
        border: 1px solid var(--border-subtle);
        border-radius: var(--border-radius);
        background: var(--canvas);
        color: var(--fg);
        padding: 0.25rem 0.4rem;
        box-sizing: border-box;
        resize: vertical;
    }

    .parse-error {
        font-size: 0.8em;
        color: var(--state-suspended);
    }
</style>
