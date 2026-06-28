<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<script lang="ts">
    import * as tr from "@generated/ftl";
    import {
        deleteAddon,
        openAddonConfig,
        openAddonFolder,
        openAddonPage,
        setAddonEnabled,
    } from "@generated/backend";
    import type { Addon } from "@generated/anki/addons_pb";
    import { invalidateAll } from "$app/navigation";

    import DropdownDivider from "$lib/components/DropdownDivider.svelte";
    import DropdownItem from "$lib/components/DropdownItem.svelte";
    import Icon from "$lib/components/Icon.svelte";
    import IconButton from "$lib/components/IconButton.svelte";
    import LabelButton from "$lib/components/LabelButton.svelte";
    import Popover from "$lib/components/Popover.svelte";
    import Switch from "$lib/components/Switch.svelte";
    import WithFloating from "$lib/components/WithFloating.svelte";
    import { dotsIcon } from "$lib/components/icons";

    export let addon: Addon;

    let showMenu = false;

    function label(): string {
        if (!addon.compatible) {
            return `${addon.humanName} (${tr.addonsRequires({ val: addon.compatSummary })})`;
        }
        if (!addon.enabled) {
            return `${addon.humanName} ${tr.addonsDisabled2()}`;
        }
        return addon.humanName;
    }

    async function onToggle(): Promise<void> {
        await setAddonEnabled({ dirName: addon.dirName, enabled: !addon.enabled });
        await invalidateAll();
    }

    async function onConfig(): Promise<void> {
        await openAddonConfig({ dirName: addon.dirName });
    }

    async function onViewFiles(): Promise<void> {
        showMenu = false;
        await openAddonFolder({ dirName: addon.dirName });
    }

    async function onViewPage(): Promise<void> {
        showMenu = false;
        await openAddonPage({ dirName: addon.dirName });
    }

    async function onDelete(): Promise<void> {
        showMenu = false;
        await deleteAddon({ dirName: addon.dirName });
        await invalidateAll();
    }
</script>

<div
    class="addon-item"
    class:disabled={!addon.enabled}
    class:incompatible={!addon.compatible}
>
    <span class="addon-name" title={label()}>{label()}</span>

    <div class="addon-actions">
        <Switch
            id={addon.dirName + "-toggle"}
            value={addon.enabled}
            on:change={onToggle}
        />

        {#if addon.hasConfig}
            <LabelButton
                --border-left-radius="5px"
                --border-right-radius="5px"
                on:click={onConfig}
            >
                {tr.addonsConfig()}
            </LabelButton>
        {/if}

        <WithFloating
            show={showMenu}
            closeOnInsideClick
            inline
            on:close={() => (showMenu = false)}
        >
            <IconButton
                slot="reference"
                tooltip={tr.actionsOptions()}
                on:click={() => (showMenu = !showMenu)}
            >
                <Icon icon={dotsIcon} />
            </IconButton>
            <Popover slot="floating">
                <DropdownItem on:click={onViewFiles}>
                    {tr.addonsViewFiles()}
                </DropdownItem>
                {#if addon.pageUrl}
                    <DropdownItem on:click={onViewPage}>
                        {tr.addonsViewAddonPage()}
                    </DropdownItem>
                {/if}
                <DropdownDivider />
                <DropdownItem on:click={onDelete}>
                    {tr.actionsDelete()}
                </DropdownItem>
            </Popover>
        </WithFloating>
    </div>
</div>

<style lang="scss">
    .addon-item {
        display: flex;
        align-items: center;
        padding: 0.5rem 0.75rem;
        border-bottom: 1px solid var(--border);
        gap: 0.5rem;

        &:last-child {
            border-bottom: none;
        }

        &.disabled .addon-name {
            color: var(--fg-subtle);
        }

        &.incompatible .addon-name {
            color: var(--fg-subtle);
            font-style: italic;
        }
    }

    .addon-name {
        flex: 1;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }

    .addon-actions {
        display: flex;
        align-items: center;
        gap: 0.25rem;
        flex-shrink: 0;
        --buttons-size: 2rem;
    }
</style>
