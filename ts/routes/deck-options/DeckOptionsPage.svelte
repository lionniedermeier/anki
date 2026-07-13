<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<script lang="ts">
    import * as tr from "@generated/ftl";
    import { onDestroy, onMount } from "svelte";
    import type { Writable } from "svelte/store";

    import "$lib/sveltelib/export-runtime";

    import Icon from "$lib/components/Icon.svelte";
    import IconConstrain from "$lib/components/IconConstrain.svelte";
    import { magnifyIcon } from "$lib/components/icons";
    import SplitPane from "$lib/components/SplitView/SplitPane.svelte";
    import SplitView from "$lib/components/SplitView/SplitView.svelte";
    import type { DynamicSvelteComponent } from "$lib/sveltelib/dynamicComponent";

    import Addons from "./Addons.svelte";
    import AdvancedOptions from "./AdvancedOptions.svelte";
    import AudioOptions from "./AudioOptions.svelte";
    import AutoAdvance from "./AutoAdvance.svelte";
    import BuryOptions from "./BuryOptions.svelte";
    import ConfigSelector from "./ConfigSelector.svelte";
    import DailyLimits from "./DailyLimits.svelte";
    import DisplayOrder from "./DisplayOrder.svelte";
    import EasyDays from "./EasyDays.svelte";
    import FsrsOptionsOuter from "./FsrsOptionsOuter.svelte";
    import HtmlAddon from "./HtmlAddon.svelte";
    import LapseOptions from "./LapseOptions.svelte";
    import type { DeckOptionsState } from "./lib";
    import NewOptions from "./NewOptions.svelte";
    import SectionSidebar from "./SectionSidebar.svelte";
    import { filterSections, sectionIds, sectionNodes } from "./sections";
    import TimerOptions from "./TimerOptions.svelte";

    export let state: DeckOptionsState;
    const addons = state.addonComponents;

    export function auxData(): Writable<Record<string, unknown>> {
        return state.currentAuxData;
    }

    export function addSvelteAddon(component: DynamicSvelteComponent): void {
        $addons = [...$addons, component];
    }

    export function addHtmlAddon(html: string, mounted: () => void): void {
        $addons = [
            ...$addons,
            {
                component: HtmlAddon,
                html,
                mounted,
            },
        ];
    }

    export const options = {};
    export const dailyLimits = {};
    export const newOptions = {};
    export const lapseOptions = {};
    export const buryOptions = {};
    export const displayOrder = {};
    export const timerOptions = {};
    export const audioOptions = {};
    export const advancedOptions = {};
    export const easyDays = {};

    let dailyLimitsComponent: DailyLimits | undefined;
    let fsrsOptionsOuterComponent: FsrsOptionsOuter | undefined;

    function onPresetChange() {
        if (dailyLimitsComponent) {
            dailyLimitsComponent.onPresetChange();
        }
        if (fsrsOptionsOuterComponent) {
            fsrsOptionsOuterComponent.onPresetChange();
        }
    }

    // Below this width the settings list would be squeezed into an unusable
    // column, so the sidebar gives way.
    const SIDEBAR_BREAKPOINT = 600;
    // Long enough for a smooth scroll to settle.
    const SCROLL_SETTLE_MS = 600;

    let innerWidth = 0;
    let query = "";
    let selectedId: string | null = null;
    let scrollArea: HTMLElement;

    $: narrow = innerWidth > 0 && innerWidth < SIDEBAR_BREAKPOINT;
    $: nodes = sectionNodes($addons.length > 0);
    $: matchingNodes = filterSections(nodes, query);
    $: visibleIds = new Set(sectionIds(matchingNodes));

    let observer: IntersectionObserver | undefined;
    let observerPaused = false;
    let scrollTimeout: number | undefined;
    const sectionElements = new Set<HTMLElement>();
    const intersecting = new Set<string>();

    /** Registers a section with the scroll spy. Filtered-out sections keep
     * their registration; being `display: none` they simply stop intersecting. */
    function spy(element: HTMLElement) {
        sectionElements.add(element);
        observer?.observe(element);
        return {
            destroy() {
                sectionElements.delete(element);
                intersecting.delete(element.dataset.sectionId!);
                observer?.unobserve(element);
            },
        };
    }

    function scrollToSection(id: string): void {
        const section = scrollArea?.querySelector(`[data-section-id="${id}"]`);
        if (!section) {
            return;
        }
        selectedId = id;
        // Without this the spy would walk the selection through every section
        // the smooth scroll passes on its way to the target.
        observerPaused = true;
        window.clearTimeout(scrollTimeout);
        scrollTimeout = window.setTimeout(
            () => (observerPaused = false),
            SCROLL_SETTLE_MS,
        );
        section.scrollIntoView({ behavior: "smooth", block: "start" });
    }

    onMount(() => {
        observer = new IntersectionObserver(
            (entries) => {
                for (const entry of entries) {
                    const id = (entry.target as HTMLElement).dataset.sectionId!;
                    if (entry.isIntersecting) {
                        intersecting.add(id);
                    } else {
                        intersecting.delete(id);
                    }
                }
                if (observerPaused) {
                    return;
                }
                const topmost = sectionIds(nodes).find((id) => intersecting.has(id));
                if (topmost) {
                    selectedId = topmost;
                }
            },
            // Only the top of the pane counts, so the section being read wins
            // over the ones trailing below it.
            { root: scrollArea, rootMargin: "0px 0px -70% 0px" },
        );
        for (const element of sectionElements) {
            observer.observe(element);
        }
    });

    onDestroy(() => {
        observer?.disconnect();
        window.clearTimeout(scrollTimeout);
    });
</script>

<svelte:window bind:innerWidth />

<div class="deck-options-page">
    <ConfigSelector {state} on:presetchange={onPresetChange} />

    <div class="search-bar">
        <IconConstrain>
            <Icon icon={magnifyIcon} />
        </IconConstrain>
        <input
            type="text"
            class="search-input"
            placeholder={tr.deckConfigSearchSettings()}
            bind:value={query}
        />
    </div>

    <SplitView id="deck-options" direction="horizontal">
        <SplitPane id="deck-options-sidebar" size={240} min={160} hidden={narrow}>
            <SectionSidebar
                nodes={matchingNodes}
                {selectedId}
                onSelect={scrollToSection}
            />
        </SplitPane>

        <SplitPane id="deck-options-content" grow>
            <div class="sections" bind:this={scrollArea}>
                <div
                    class="section"
                    class:hidden={!visibleIds.has("daily-limits")}
                    data-section-id="daily-limits"
                    use:spy
                >
                    <DailyLimits
                        {state}
                        api={dailyLimits}
                        bind:this={dailyLimitsComponent}
                    />
                </div>

                <div
                    class="section"
                    class:hidden={!visibleIds.has("new-cards")}
                    data-section-id="new-cards"
                    use:spy
                >
                    <NewOptions {state} api={newOptions} />
                </div>

                <div
                    class="section"
                    class:hidden={!visibleIds.has("lapses")}
                    data-section-id="lapses"
                    use:spy
                >
                    <LapseOptions {state} api={lapseOptions} />
                </div>

                <div
                    class="section"
                    class:hidden={!visibleIds.has("fsrs")}
                    data-section-id="fsrs"
                    use:spy
                >
                    <FsrsOptionsOuter
                        {state}
                        api={{}}
                        bind:this={fsrsOptionsOuterComponent}
                    />
                </div>

                <div
                    class="section"
                    class:hidden={!visibleIds.has("easy-days")}
                    data-section-id="easy-days"
                    use:spy
                >
                    <EasyDays {state} api={easyDays} />
                </div>

                <div
                    class="section"
                    class:hidden={!visibleIds.has("display-order")}
                    data-section-id="display-order"
                    use:spy
                >
                    <DisplayOrder {state} api={displayOrder} />
                </div>

                <div
                    class="section"
                    class:hidden={!visibleIds.has("burying")}
                    data-section-id="burying"
                    use:spy
                >
                    <BuryOptions {state} api={buryOptions} />
                </div>

                <div
                    class="section"
                    class:hidden={!visibleIds.has("timers")}
                    data-section-id="timers"
                    use:spy
                >
                    <TimerOptions {state} api={timerOptions} />
                </div>

                <div
                    class="section"
                    class:hidden={!visibleIds.has("audio")}
                    data-section-id="audio"
                    use:spy
                >
                    <AudioOptions {state} api={audioOptions} />
                </div>

                <div
                    class="section"
                    class:hidden={!visibleIds.has("auto-advance")}
                    data-section-id="auto-advance"
                    use:spy
                >
                    <AutoAdvance {state} api={timerOptions} />
                </div>

                <div
                    class="section"
                    class:hidden={!visibleIds.has("advanced")}
                    data-section-id="advanced"
                    use:spy
                >
                    <AdvancedOptions {state} api={advancedOptions} />
                </div>

                {#if $addons.length}
                    <div
                        class="section"
                        class:hidden={!visibleIds.has("addons")}
                        data-section-id="addons"
                        use:spy
                    >
                        <Addons {state} />
                    </div>
                {/if}
            </div>
        </SplitPane>
    </SplitView>
</div>

<style lang="scss">
    .deck-options-page {
        display: flex;
        flex-direction: column;
        height: 100vh;
        overflow: hidden;
        word-break: break-word;

        // The preset selector is a header now that scrolling has moved into
        // the settings pane.
        :global(.sticky-container) {
            flex: none;
        }

        :global(.split-view) {
            flex: 1 1 auto;
            min-height: 0;
        }
    }

    .search-bar {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        flex: none;
        padding: 0.5rem 0.75rem;
        border-bottom: 1px solid var(--border-subtle);
    }

    .search-input {
        flex: 1 1 auto;
        min-width: 0;
    }

    .sections {
        height: 100%;
        overflow-y: auto;
        overflow-x: hidden;
        padding: 0.5rem 1.5rem;
    }

    .hidden {
        display: none;
    }
</style>
