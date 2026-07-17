<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<script lang="ts">
    import * as tr from "@generated/ftl";
    import { HelpPage } from "@tslib/help-page";
    import type Carousel from "bootstrap/js/dist/carousel";
    import type Modal from "$lib/components/Modal.svelte";
    import { untrack } from "svelte";

    import DynamicallySlottable from "$lib/components/DynamicallySlottable.svelte";
    import HelpModal from "$lib/components/HelpModal.svelte";
    import Item from "$lib/components/Item.svelte";
    import SettingTitle from "$lib/components/SettingTitle.svelte";
    import SwitchRow from "$lib/components/SwitchRow.svelte";
    import type { HelpItem } from "$lib/components/types";

    import type { DeckOptionsState } from "./lib";
    import SettingsSection from "./SettingsSection.svelte";

    interface Props {
        state: DeckOptionsState;
        api: Record<string, never>;
    }

    let { state: deckState, api }: Props = $props();

    const config = untrack(() => deckState.currentConfig);
    const defaults = untrack(() => deckState.defaults);

    const settings = {
        disableAutoplay: {
            title: tr.deckConfigDisableAutoplay(),
            help: tr.deckConfigDisableAutoplayTooltip(),
        },
        skipQuestionWhenReplaying: {
            title: tr.deckConfigSkipQuestionWhenReplaying(),
            help: tr.deckConfigAlwaysIncludeQuestionAudioTooltip(),
        },
    };
    const helpSections: HelpItem[] = Object.values(settings);

    let modal: Modal;
    let carousel: Carousel;

    function openHelpModal(index: number): void {
        modal.show();
        carousel.to(index);
    }
</script>

<SettingsSection title={tr.deckConfigAudioTitle()}>
    {#snippet tooltip()}
        <HelpModal
            title={tr.deckConfigAudioTitle()}
            url={HelpPage.DeckOptions.audio}
            {helpSections}
            onMounted={(m, c) => {
                modal = m;
                carousel = c;
            }}
        />
    {/snippet}
    <DynamicallySlottable slotHost={Item} {api}>
        <Item>
            <SwitchRow
                bind:value={$config.disableAutoplay}
                defaultValue={defaults.disableAutoplay}
            >
                <SettingTitle
                    on:click={() =>
                        openHelpModal(Object.keys(settings).indexOf("disableAutoplay"))}
                >
                    {settings.disableAutoplay.title}
                </SettingTitle>
            </SwitchRow>
        </Item>

        <Item>
            <SwitchRow
                bind:value={$config.skipQuestionWhenReplayingAnswer}
                defaultValue={defaults.skipQuestionWhenReplayingAnswer}
            >
                <SettingTitle
                    on:click={() =>
                        openHelpModal(
                            Object.keys(settings).indexOf("skipQuestionWhenReplaying"),
                        )}
                >
                    {settings.skipQuestionWhenReplaying.title}
                </SettingTitle>
            </SwitchRow>
        </Item>
    </DynamicallySlottable>
</SettingsSection>
