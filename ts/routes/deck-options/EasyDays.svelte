<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<script lang="ts">
    import * as tr from "@generated/ftl";
    import { untrack } from "svelte";
    import DynamicallySlottable from "$lib/components/DynamicallySlottable.svelte";
    import Item from "$lib/components/Item.svelte";
    import type { DeckOptionsState } from "./lib";
    import SettingsSection from "./SettingsSection.svelte";
    import Warning from "./Warning.svelte";
    import EasyDaysInput from "./EasyDaysInput.svelte";

    interface Props {
        state: DeckOptionsState;
        api: Record<string, never>;
    }

    let { state: deckState, api }: Props = $props();

    const fsrsEnabled = untrack(() => deckState.fsrs);
    const reschedule = untrack(() => deckState.fsrsReschedule);
    const config = untrack(() => deckState.currentConfig);
    const defaults = untrack(() => deckState.defaults);
    const prevEasyDaysPercentages = $config.easyDaysPercentages.slice();

    $effect(() => {
        if ($config.easyDaysPercentages.length !== 7) {
            $config.easyDaysPercentages = defaults.easyDaysPercentages.slice();
        }
    });

    const easyDaysChanged = $derived(
        $config.easyDaysPercentages.some(
            (value, index) => value !== prevEasyDaysPercentages[index],
        ),
    );

    const noNormalDay = $derived(
        $config.easyDaysPercentages.some((p) => p === 1.0)
            ? ""
            : tr.deckConfigEasyDaysNoNormalDays(),
    );

    const rescheduleWarning = $derived(
        easyDaysChanged && !($fsrsEnabled && $reschedule)
            ? tr.deckConfigEasyDaysChange()
            : "",
    );
</script>

<datalist id="easy_day_steplist">
    <option>0.5</option>
</datalist>

<SettingsSection title={tr.deckConfigEasyDaysTitle()}>
    <DynamicallySlottable slotHost={Item} {api}>
        <EasyDaysInput bind:values={$config.easyDaysPercentages} />
        <Item>
            <Warning warning={noNormalDay} />
        </Item>
        <Item>
            <Warning warning={rescheduleWarning} />
        </Item>
    </DynamicallySlottable>
</SettingsSection>
