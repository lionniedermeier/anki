<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<script lang="ts">
    import type { PlainMessage } from "@bufbuild/protobuf";
    import type { DeckOverviewContent } from "@generated/anki/frontend_pb";
    import * as tr from "@generated/ftl";
    import { bridgeCommand } from "@tslib/bridgecommand";

    import LabelButton from "$lib/components/LabelButton.svelte";

    import { buriedDelta } from "./lib";

    export let content: PlainMessage<DeckOverviewContent>;

    const buriedTooltip = tr.studyingCountsDiffer();
</script>

<div class="deck-overview">
    <div class="content">
        <h2 class="deck-name">{content.deckName}</h2>

        {#if content.sharedFrom}
            <a
                class="share-link"
                href="#review"
                on:click|preventDefault={() => bridgeCommand("review")}
            >
                Reviews and Updates
            </a>
        {/if}

        {#if content.descriptionHtml}
            <!-- rendered server-side (markdown / filtered-deck blurb) -->
            {@html content.descriptionHtml}
        {/if}

        <table class="counts">
            <tbody>
                <tr>
                    <td class="label">{tr.actionsNew()}:</td>
                    <td class="value">
                        <span class="new-count">{content.newCount}</span>
                        <span class="bury-count" title={buriedTooltip}>
                            {buriedDelta(content.buriedNew)}
                        </span>
                    </td>
                </tr>
                <tr>
                    <td class="label">{tr.schedulingLearning()}:</td>
                    <td class="value">
                        <span class="learn-count">{content.learnCount}</span>
                        <span class="bury-count" title={buriedTooltip}>
                            {buriedDelta(content.buriedLearn)}
                        </span>
                    </td>
                </tr>
                <tr>
                    <td class="label">{tr.studyingToReview()}:</td>
                    <td class="value">
                        <span class="review-count">{content.reviewCount}</span>
                        <span class="bury-count" title={buriedTooltip}>
                            {buriedDelta(content.buriedReview)}
                        </span>
                    </td>
                </tr>
            </tbody>
        </table>

        <div class="study">
            <LabelButton primary tabbable on:click={() => bridgeCommand("study")}>
                {tr.studyingStudyNow()}
            </LabelButton>
        </div>
    </div>

    <div class="bottom-bar">
        <LabelButton tabbable on:click={() => bridgeCommand("opts")}>
            {tr.actionsOptions()}
        </LabelButton>
        {#if content.isFiltered}
            <LabelButton tabbable on:click={() => bridgeCommand("refresh")}>
                {tr.actionsRebuild()}
            </LabelButton>
            <LabelButton tabbable on:click={() => bridgeCommand("empty")}>
                {tr.studyingEmpty()}
            </LabelButton>
        {:else}
            <LabelButton tabbable on:click={() => bridgeCommand("studymore")}>
                {tr.actionsCustomStudy()}
            </LabelButton>
        {/if}
        {#if content.haveBuried}
            <LabelButton tabbable on:click={() => bridgeCommand("unbury")}>
                {tr.studyingUnbury()}
            </LabelButton>
        {/if}
        {#if !content.isFiltered}
            <LabelButton tabbable on:click={() => bridgeCommand("description")}>
                {tr.schedulingDescription()}
            </LabelButton>
        {/if}
    </div>
</div>

<style lang="scss">
    .review-count {
        color: var(--state-review);
    }

    .new-count {
        color: var(--state-new);
    }

    .learn-count {
        color: var(--state-learn);
    }

    .bury-count {
        color: var(--fg-disabled);
        font-weight: bold;
        margin-inline-start: 2px;

        &:empty {
            display: none;
        }
    }

    .deck-overview {
        display: flex;
        flex-direction: column;
        height: 100%;
        padding: 0.5rem 1rem;
    }

    .content {
        flex: 1;
        min-height: 0;
        overflow-y: auto;
        display: flex;
        flex-direction: column;
        align-items: center;
        text-align: center;
    }

    .deck-name {
        margin-top: 1rem;
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

    .counts {
        margin: 1rem 0;
        border-spacing: 0.5rem;

        .label {
            text-align: end;
        }

        .value {
            text-align: start;
            font-weight: bold;
        }
    }

    .study {
        margin-bottom: 1rem;
    }

    .bottom-bar {
        flex: none;
        display: flex;
        justify-content: center;
        flex-wrap: wrap;
        gap: 0.5rem;
        margin-top: 1rem;
        padding-top: 0.5rem;
        border-top: 1px solid var(--border-subtle);
    }
</style>
