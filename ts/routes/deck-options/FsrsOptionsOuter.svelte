<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<script lang="ts">
    import * as tr from "@generated/ftl";
    import { HelpPage } from "@tslib/help-page";
    import type Carousel from "bootstrap/js/dist/carousel";
    import type Modal from "$lib/components/Modal.svelte";

    import DynamicallySlottable from "$lib/components/DynamicallySlottable.svelte";
    import HelpModal from "$lib/components/HelpModal.svelte";
    import Item from "$lib/components/Item.svelte";
    import SettingTitle from "$lib/components/SettingTitle.svelte";
    import SwitchRow from "$lib/components/SwitchRow.svelte";
    import { type HelpItem, HelpItemScheduler } from "$lib/components/types";

    import FsrsOptions from "./FsrsOptions.svelte";
    import GlobalLabel from "./GlobalLabel.svelte";
    import type { DeckOptionsState } from "./lib";
    import SettingsSection from "./SettingsSection.svelte";

    export let state: DeckOptionsState;
    export let api: Record<string, never>;

    let fsrsOptionsComponent: FsrsOptions | undefined;
    export function onPresetChange() {
        if (fsrsOptionsComponent) {
            fsrsOptionsComponent.onPresetChange();
        }
    }

    const fsrs = state.fsrs;
    let newlyEnabled = false;
    $: if (!$fsrs) {
        newlyEnabled = true;
    }

    const settings = {
        fsrs: {
            title: "FSRS",
            help: tr.deckConfigFsrsTooltip(),
            url: HelpPage.DeckOptions.fsrs,
            global: true,
        },
        desiredRetention: {
            title: tr.deckConfigDesiredRetention(),
            help:
                tr.deckConfigDesiredRetentionTooltip() +
                "\n\n" +
                tr.deckConfigDesiredRetentionTooltip2(),
            sched: HelpItemScheduler.FSRS,
        },
        modelParams: {
            title: tr.deckConfigWeights(),
            help:
                tr.deckConfigWeightsTooltip2() +
                "\n\n" +
                tr.deckConfigComputeOptimalWeightsTooltip2(),
            sched: HelpItemScheduler.FSRS,
        },
        rescheduleCardsOnChange: {
            title: tr.deckConfigRescheduleCardsOnChange(),
            help: tr.deckConfigRescheduleCardsOnChangeTooltip(),
            sched: HelpItemScheduler.FSRS,
            global: true,
        },
        healthCheck: {
            title: tr.deckConfigHealthCheck(),
            help:
                tr.deckConfigAffectsEntireCollection() +
                "\n\n" +
                tr.deckConfigHealthCheckTooltip1() +
                "\n\n" +
                tr.deckConfigHealthCheckTooltip2(),
            sched: HelpItemScheduler.FSRS,
            global: true,
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

<SettingsSection title={"FSRS"}>
    {#snippet tooltip()}
        <HelpModal
            title={"FSRS"}
            url={HelpPage.DeckOptions.fsrs}
            fsrs={$fsrs}
            {helpSections}
            onMounted={(m, c) => {
                modal = m;
                carousel = c;
            }}
        />
    {/snippet}
    <DynamicallySlottable slotHost={Item} {api}>
        <Item>
            <SwitchRow bind:value={$fsrs} defaultValue={false}>
                <SettingTitle
                    on:click={() =>
                        openHelpModal(Object.keys(settings).indexOf("fsrs"))}
                >
                    <GlobalLabel title={settings.fsrs.title} />
                </SettingTitle>
            </SwitchRow>
        </Item>

        {#if $fsrs}
            <FsrsOptions
                bind:this={fsrsOptionsComponent}
                {state}
                {newlyEnabled}
                openHelpModal={(key) =>
                    openHelpModal(Object.keys(settings).indexOf(key))}
                {onPresetChange}
            />
        {/if}
    </DynamicallySlottable>
</SettingsSection>
