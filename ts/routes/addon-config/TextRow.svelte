<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<!-- A plain text-input row for JSON Schema string fields. -->
<script lang="ts">
    import ConfigInput from "$lib/components/ConfigInput.svelte";
    import Label from "$lib/components/Label.svelte";
    import RevertButton from "$lib/components/RevertButton.svelte";
    import Row from "$lib/components/Row.svelte";

    export let value: string;
    export let defaultValue: string;
    /** Render a multi-line <textarea> instead of a single-line input. */
    export let multiline = false;

    const id = Math.random().toString(36).substring(2);
</script>

<Row --cols={13}>
    <div>
        <Label for={id} preventMouseClick><slot /></Label>
        <ConfigInput>
            {#if multiline}
                <textarea
                    {id}
                    class="text-input text-area"
                    rows={4}
                    bind:value
                ></textarea>
            {:else}
                <input
                    {id}
                    class="text-input"
                    type="text"
                    bind:value
                />
            {/if}
            <RevertButton slot="revert" bind:value {defaultValue} />
        </ConfigInput>
    </div>
</Row>

<style lang="scss">
    .text-input {
        width: 100%;
        height: var(--buttons-size);
        padding: 0 0.4rem;
        border: 1px solid var(--border-subtle);
        border-bottom-color: var(--shadow);
        border-radius: var(--border-radius);
        background: var(--canvas);
        color: var(--fg);
        font-size: var(--font-size);
        box-sizing: border-box;

        &:focus {
            outline: none;
            border-color: var(--border);
        }
    }

    .text-area {
        height: auto;
        width: 80%;
        padding: 0.4rem;
        font-family: inherit;
        resize: vertical;
    }
</style>
