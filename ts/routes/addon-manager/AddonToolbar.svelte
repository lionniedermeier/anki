<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<script lang="ts">
    import * as tr from "@generated/ftl";
    import {
        checkForAddonUpdates,
        getAddonsFromAnkiWeb,
        installAddonsFromFiles,
    } from "@generated/backend";

    import ButtonGroup from "$lib/components/ButtonGroup.svelte";
    import ButtonToolbar from "$lib/components/ButtonToolbar.svelte";
    import LabelButton from "$lib/components/LabelButton.svelte";

    async function onGetAddons(): Promise<void> {
        await getAddonsFromAnkiWeb({});
    }

    async function onInstallFromFile(): Promise<void> {
        await installAddonsFromFiles({});
    }

    async function onCheckUpdates(): Promise<void> {
        await checkForAddonUpdates({});
    }
</script>

<ButtonToolbar>
    <ButtonGroup size={2}>
        <LabelButton
            --border-left-radius="5px"
            --border-right-radius="0"
            on:click={onGetAddons}
        >
            {tr.addonsGetAddons()}
        </LabelButton>
        <LabelButton
            --border-left-radius="0"
            --border-right-radius="0"
            on:click={onInstallFromFile}
        >
            {tr.addonsInstallFromFile()}
        </LabelButton>
        <LabelButton
            --border-left-radius="0"
            --border-right-radius="5px"
            on:click={onCheckUpdates}
        >
            {tr.addonsCheckForUpdates()}
        </LabelButton>
    </ButtonGroup>
</ButtonToolbar>