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
    import EnumSelectorRow from "$lib/components/EnumSelectorRow.svelte";
    import HelpModal from "$lib/components/HelpModal.svelte";
    import Item from "$lib/components/Item.svelte";
    import SettingTitle from "$lib/components/SettingTitle.svelte";
    import SwitchRow from "$lib/components/SwitchRow.svelte";
    import type { HelpItem } from "$lib/components/types";

    import { answerChoices, questionActionChoices } from "./choices";
    import type { DeckOptionsState } from "./lib";
    import SettingsSection from "./SettingsSection.svelte";
    import SpinBoxFloatRow from "./SpinBoxFloatRow.svelte";

    interface Props {
        state: DeckOptionsState;
        api: Record<string, never>;
    }

    let { state: deckState, api }: Props = $props();

    const config = untrack(() => deckState.currentConfig);
    const defaults = untrack(() => deckState.defaults);

    const settings = {
        secondsToShowQuestion: {
            title: tr.deckConfigSecondsToShowQuestion(),
            help: tr.deckConfigSecondsToShowQuestionTooltip3(),
        },
        secondsToShowAnswer: {
            title: tr.deckConfigSecondsToShowAnswer(),
            help: tr.deckConfigSecondsToShowAnswerTooltip2(),
        },
        waitForAudio: {
            title: tr.deckConfigWaitForAudio(),
            help: tr.deckConfigWaitForAudioTooltip2(),
        },
        questionAction: {
            title: tr.deckConfigQuestionAction(),
            help: tr.deckConfigQuestionActionToolTip(),
        },
        answerAction: {
            title: tr.deckConfigAnswerAction(),
            help: tr.deckConfigAnswerActionTooltip2(),
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

<SettingsSection title={tr.actionsAutoAdvance()}>
    {#snippet tooltip()}
        <HelpModal
            title={tr.actionsAutoAdvance()}
            url={HelpPage.DeckOptions.autoAdvance}
            {helpSections}
            onMounted={(m, c) => {
                modal = m;
                carousel = c;
            }}
        />
    {/snippet}
    <DynamicallySlottable slotHost={Item} {api}>
        <Item>
            <SpinBoxFloatRow
                bind:value={$config.secondsToShowQuestion}
                defaultValue={defaults.secondsToShowQuestion}
                step={0.1}
            >
                <SettingTitle
                    on:click={() =>
                        openHelpModal(
                            Object.keys(settings).indexOf("secondsToShowQuestion"),
                        )}
                >
                    {settings.secondsToShowQuestion.title}
                </SettingTitle>
            </SpinBoxFloatRow>
        </Item>

        <Item>
            <SpinBoxFloatRow
                bind:value={$config.secondsToShowAnswer}
                defaultValue={defaults.secondsToShowAnswer}
                step={0.1}
            >
                <SettingTitle
                    on:click={() =>
                        openHelpModal(
                            Object.keys(settings).indexOf("secondsToShowAnswer"),
                        )}
                >
                    {settings.secondsToShowAnswer.title}
                </SettingTitle>
            </SpinBoxFloatRow>
        </Item>

        <Item>
            <SwitchRow
                bind:value={$config.waitForAudio}
                defaultValue={defaults.waitForAudio}
            >
                <SettingTitle
                    on:click={() =>
                        openHelpModal(Object.keys(settings).indexOf("waitForAudio"))}
                >
                    {settings.waitForAudio.title}
                </SettingTitle>
            </SwitchRow>
        </Item>

        <Item>
            <EnumSelectorRow
                bind:value={$config.questionAction}
                defaultValue={defaults.questionAction}
                choices={questionActionChoices()}
            >
                <SettingTitle
                    on:click={() =>
                        openHelpModal(Object.keys(settings).indexOf("questionAction"))}
                >
                    {settings.questionAction.title}
                </SettingTitle>
            </EnumSelectorRow>
        </Item>
        <Item>
            <EnumSelectorRow
                bind:value={$config.answerAction}
                defaultValue={defaults.answerAction}
                choices={answerChoices()}
            >
                <SettingTitle
                    on:click={() =>
                        openHelpModal(Object.keys(settings).indexOf("answerAction"))}
                >
                    {settings.answerAction.title}
                </SettingTitle>
            </EnumSelectorRow>
        </Item>
    </DynamicallySlottable>
</SettingsSection>
