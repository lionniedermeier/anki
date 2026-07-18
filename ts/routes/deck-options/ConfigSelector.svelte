<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<script lang="ts">
    import * as tr from "@generated/ftl";
    import { noop } from "@tslib/functional";
    import type Modal from "bootstrap/js/dist/modal";
    import { getContext, untrack } from "svelte";

    import { modalsKey } from "$lib/components/context-keys";
    import Select from "$lib/components/Select.svelte";
    import StickyContainer from "$lib/components/StickyContainer.svelte";

    import type { ConfigListEntry, DeckOptionsState } from "./lib";
    import SaveButton from "./SaveButton.svelte";
    import TextInputModal from "./TextInputModal.svelte";

    interface Props {
        state: DeckOptionsState;
        onpresetchange?: () => void;
        onSaved?: () => void;
    }

    let { state: deckState, onpresetchange, onSaved }: Props = $props();

    const configList = untrack(() => deckState.configList);

    let value = $state($configList.findIndex((entry) => entry.current));
    $effect(() => {
        value = $configList.findIndex((entry) => entry.current);
    });
    const label = $derived(configLabel($configList[value]));

    function configLabel(entry: ConfigListEntry): string {
        const count = tr.deckConfigUsedByDecks({ decks: entry.useCount });
        return `${entry.name} (${count})`;
    }

    function blur(e: CustomEvent): void {
        deckState.setCurrentIndex(e.detail.value);
        onpresetchange?.();
    }

    function onAddConfig(text: string): void {
        const trimmed = text.trim();
        if (trimmed.length) {
            deckState.addConfig(trimmed);
            onpresetchange?.();
        }
    }

    function onCloneConfig(text: string): void {
        const trimmed = text.trim();
        if (trimmed.length) {
            deckState.cloneConfig(trimmed);
            onpresetchange?.();
        }
    }

    function onRenameConfig(text: string): void {
        deckState.setCurrentName(text);
    }

    const modals = getContext<Map<string, Modal>>(modalsKey);

    const modalKey = Math.random().toString(36).substring(2);
    let modalStartingValue = $state("");
    let modalTitle = $state("");
    let modalSuccess: (text: string) => void = $state(noop);

    function promptToAdd() {
        modalTitle = tr.deckConfigAddGroup();
        modalSuccess = onAddConfig;
        modalStartingValue = "";
        modals.get(modalKey)!.show();
    }

    function promptToClone() {
        modalTitle = tr.deckConfigCloneGroup();
        modalSuccess = onCloneConfig;
        modalStartingValue = deckState.getCurrentName();
        modals.get(modalKey)!.show();
    }

    function promptToRename() {
        modalTitle = tr.deckConfigRenameGroup();
        modalSuccess = onRenameConfig;
        modalStartingValue = deckState.getCurrentName();
        modals.get(modalKey)!.show();
    }
</script>

<TextInputModal
    title={modalTitle}
    prompt={tr.deckConfigNamePrompt()}
    initialValue={modalStartingValue}
    onOk={modalSuccess}
    {modalKey}
/>

<StickyContainer --gutter-block="0.5rem" --sticky-borders="0 0 1px" breakpoint="sm">
    <div class="button-bar">
        <Select
            class="flex-grow-1 mr1"
            bind:value
            {label}
            list={$configList}
            parser={(entry) => ({
                content: configLabel(entry),
                value: entry.idx,
            })}
            on:change={blur}
        />

        <SaveButton
            state={deckState}
            onadd={promptToAdd}
            onclone={promptToClone}
            onrename={promptToRename}
            onremove={onpresetchange}
            {onSaved}
        />
    </div>
</StickyContainer>

<style lang="scss">
    .button-bar {
        display: flex;
        flex-wrap: nowrap;
        justify-content: space-between;

        flex-grow: 1;
    }

    /* TODO replace with gap once available (blocked by Qt5 / Chromium 77) */
    :global(.mr1) {
        margin-right: 1rem;
    }
</style>
