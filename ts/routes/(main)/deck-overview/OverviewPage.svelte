<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<script lang="ts">
    import { goto } from "$app/navigation";
    import type { PlainMessage } from "@bufbuild/protobuf";
    import type { DeckOverviewContent } from "@generated/anki/frontend_pb";
    import * as tr from "@generated/ftl";
    import { bridgeCommand } from "@tslib/bridgecommand";

    import { buriedDelta } from "./lib";
    import Stat from "./Stat.svelte";

    interface Props {
        content: PlainMessage<DeckOverviewContent>;
    }

    let { content }: Props = $props();

    const buriedTooltip = tr.studyingCountsDiffer();

    function subdeckName(deckName: string): string {
        return deckName.includes("::") ? deckName.split("::").pop()! : deckName;
    }

    const displayName = $derived(subdeckName(content.deckName));

    function openOptions(e: MouseEvent): void {
        if (content.deckId && !e.shiftKey) {
            goto("/deck-overview/options");
        } else {
            bridgeCommand("opts");
        }
    }
</script>

<div class="deck-overview">
    <div class="content">
        <h1 class="deck-name">{displayName}</h1>

        {#if content.sharedFrom}
            <a
                class="share-link"
                href="#review"
                onclick={(e) => {
                    e.preventDefault();
                    bridgeCommand("review");
                }}
            >
                Reviews and Updates
            </a>
        {/if}

        {#if content.descriptionHtml}
            <!-- rendered server-side (markdown / filtered-deck blurb) -->
            {@html content.descriptionHtml}
        {/if}

        <div class="stats">
            <Stat
                title={tr.actionsNew()}
                value={content.newCount}
                buried={buriedDelta(content.buriedNew)}
                {buriedTooltip}
                color="var(--state-new)"
            />
            <Stat
                title={tr.schedulingLearning()}
                value={content.learnCount}
                buried={buriedDelta(content.buriedLearn)}
                {buriedTooltip}
                color="var(--state-learn)"
            />
            <Stat
                title={tr.studyingToReview()}
                value={content.reviewCount}
                buried={buriedDelta(content.buriedReview)}
                {buriedTooltip}
                color="var(--state-review)"
            />
        </div>

        <div class="study">
            <button
                type="button"
                class="overview-button primary btn-study"
                onclick={() => bridgeCommand("study")}
            >
                {tr.studyingStudyNow()}
            </button>
        </div>
    </div>

    <div class="bottom-bar">
        <button type="button" class="overview-button" onclick={openOptions}>
            {tr.actionsOptions()}
        </button>
        {#if content.isFiltered}
            <button
                type="button"
                class="overview-button"
                onclick={() => bridgeCommand("refresh")}
            >
                {tr.actionsRebuild()}
            </button>
            <button
                type="button"
                class="overview-button"
                onclick={() => bridgeCommand("empty")}
            >
                {tr.studyingEmpty()}
            </button>
        {:else}
            <button
                type="button"
                class="overview-button"
                onclick={() => bridgeCommand("studymore")}
            >
                {tr.actionsCustomStudy()}
            </button>
        {/if}
        {#if content.haveBuried}
            <button
                type="button"
                class="overview-button"
                onclick={() => bridgeCommand("unbury")}
            >
                {tr.studyingUnbury()}
            </button>
        {/if}
        {#if !content.isFiltered}
            <button
                type="button"
                class="overview-button"
                onclick={() => bridgeCommand("description")}
            >
                {tr.schedulingDescription()}
            </button>
        {/if}
    </div>
</div>

<style lang="scss">
    .deck-overview {
        display: flex;
        flex-direction: column;
        flex: 1;
        min-height: 0;
    }

    .content {
        flex: 1;
        min-height: 0;
        overflow-y: auto;
        display: flex;
        flex-direction: column;
        align-items: flex-start;
        text-align: left;
    }

    .deck-name {
        font-size: 30pt;
        margin: 0 0 0.5rem;
    }

    .share-link {
        color: var(--fg-link);
        text-decoration: none;
        font-size: 0.9em;
    }

    .content :global(.description) {
        max-width: 30em;
        margin: 1rem 0;
    }

    .stats {
        display: flex;
        flex-wrap: wrap;
        margin: 1rem 0;
        gap: 8px;
    }

    .study {
        margin-bottom: 1rem;
    }

    .overview-button {
        appearance: none;
        height: var(--buttons-size);
        padding: 0 calc(var(--buttons-size) / 3);
        border: 1px solid var(--border-subtle);
        border-bottom-color: var(--shadow);
        border-top-left-radius: var(--border-left-radius);
        border-bottom-left-radius: var(--border-left-radius);
        border-top-right-radius: var(--border-right-radius);
        border-bottom-right-radius: var(--border-right-radius);
        background: var(--button-bg);
        color: var(--fg);
        cursor: pointer;
        font: inherit;
        font-size: var(--font-size);

        &:hover {
            background: linear-gradient(
                180deg,
                var(--button-gradient-start) 0%,
                var(--button-gradient-end) 100%
            );
            border: 1px solid var(--shadow);
        }

        &.primary {
            border: none;
            background: var(--button-primary-bg);
            color: white;

            &:hover {
                background: linear-gradient(
                    180deg,
                    var(--button-primary-gradient-start) 0%,
                    var(--button-primary-gradient-end) 100%
                );
            }
        }
    }

    .overview-button.btn-study {
        padding: 8px 24px;
        border-radius: 4px;
    }

    .bottom-bar {
        flex: none;
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        margin-top: 1rem;
        padding-top: 0.5rem;
        border-top: 1px solid var(--border-subtle);
    }
</style>
