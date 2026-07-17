// Copyright: Ankitects Pty Ltd and contributors
// License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import * as tr from "@generated/ftl";

export interface SectionNode {
    id: string;
    title: () => string;
    /** Leaf sections only: additional text the search box matches against.
     * Mirrors the setting titles declared inside the section's component. */
    keywords?: () => string[];
    /** Groups only. A group is a heading in the sidebar; it has no counterpart
     * in the settings list, so it carries no scroll anchor. */
    children?: SectionNode[];
}

export function sectionNodes(hasAddons: boolean): SectionNode[] {
    const nodes: SectionNode[] = [
        {
            id: "scheduling",
            title: tr.deckConfigGroupScheduling,
            children: [
                {
                    id: "daily-limits",
                    title: tr.deckConfigDailyLimits,
                    keywords: () => [
                        tr.schedulingNewCardsday(),
                        tr.schedulingMaximumReviewsday(),
                        tr.deckConfigNewCardsIgnoreReviewLimit(),
                        tr.deckConfigApplyAllParentLimits(),
                    ],
                },
                {
                    id: "new-cards",
                    title: tr.schedulingNewCards,
                    keywords: () => [
                        tr.deckConfigLearningSteps(),
                        tr.schedulingGraduatingInterval(),
                        tr.schedulingEasyInterval(),
                        tr.deckConfigNewInsertionOrder(),
                    ],
                },
                {
                    id: "lapses",
                    title: tr.schedulingLapses,
                    keywords: () => [
                        tr.deckConfigRelearningSteps(),
                        tr.schedulingMinimumInterval(),
                        tr.schedulingLeechThreshold(),
                        tr.schedulingLeechAction(),
                    ],
                },
                {
                    id: "fsrs",
                    title: () => "FSRS",
                    keywords: () => [
                        tr.deckConfigDesiredRetention(),
                        tr.deckConfigWeights(),
                        tr.deckConfigRescheduleCardsOnChange(),
                        tr.deckConfigHealthCheck(),
                    ],
                },
                {
                    id: "easy-days",
                    title: tr.deckConfigEasyDaysTitle,
                },
            ],
        },
        {
            id: "reviewing",
            title: tr.deckConfigGroupReviewing,
            children: [
                {
                    id: "display-order",
                    title: tr.deckConfigOrderingTitle,
                    keywords: () => [
                        tr.deckConfigNewGatherPriority(),
                        tr.deckConfigNewCardSortOrder(),
                        tr.deckConfigNewReviewPriority(),
                        tr.deckConfigInterdayStepPriority(),
                        tr.deckConfigReviewSortOrder(),
                    ],
                },
                {
                    id: "burying",
                    title: tr.deckConfigBuryTitle,
                    keywords: () => [
                        tr.deckConfigBuryNewSiblings(),
                        tr.deckConfigBuryReviewSiblings(),
                        tr.deckConfigBuryInterdayLearningSiblings(),
                    ],
                },
                {
                    id: "timers",
                    title: tr.deckConfigTimerTitle,
                    keywords: () => [
                        tr.deckConfigMaximumAnswerSecs(),
                        tr.schedulingShowAnswerTimer(),
                        tr.deckConfigStopTimerOnAnswer(),
                    ],
                },
                {
                    id: "audio",
                    title: tr.deckConfigAudioTitle,
                    keywords: () => [
                        tr.deckConfigDisableAutoplay(),
                        tr.deckConfigSkipQuestionWhenReplaying(),
                    ],
                },
                {
                    id: "auto-advance",
                    title: tr.actionsAutoAdvance,
                    keywords: () => [
                        tr.deckConfigSecondsToShowQuestion(),
                        tr.deckConfigSecondsToShowAnswer(),
                        tr.deckConfigWaitForAudio(),
                        tr.deckConfigQuestionAction(),
                        tr.deckConfigAnswerAction(),
                    ],
                },
            ],
        },
        {
            id: "advanced",
            title: tr.deckConfigAdvancedTitle,
            keywords: () => [
                tr.schedulingMaximumInterval(),
                tr.deckConfigHistoricalRetention(),
                tr.deckConfigIgnoreBefore(),
                tr.schedulingStartingEase(),
                tr.schedulingEasyBonus(),
                tr.schedulingIntervalModifier(),
                tr.schedulingHardInterval(),
                tr.schedulingNewInterval(),
                tr.deckConfigCustomScheduling(),
            ],
        },
    ];

    if (hasAddons) {
        nodes.push({ id: "addons", title: () => "Add-ons" });
    }

    return nodes;
}

function matchesQuery(node: SectionNode, query: string): boolean {
    const haystack = [node.title(), ...(node.keywords?.() ?? [])];
    return haystack.some((text) => text.toLowerCase().includes(query));
}

/** The nodes matching `query`, with non-matching leaves pruned. A group is kept
 * when it matches in its own right - in which case all of its children come
 * along - or when at least one of its children matches. An empty query returns
 * the tree unchanged. */
export function filterSections(nodes: SectionNode[], query: string): SectionNode[] {
    const needle = query.trim().toLowerCase();
    if (!needle) {
        return nodes;
    }
    const filtered: SectionNode[] = [];
    for (const node of nodes) {
        const selfMatches = matchesQuery(node, needle);
        if (!node.children) {
            if (selfMatches) {
                filtered.push(node);
            }
            continue;
        }
        if (selfMatches) {
            filtered.push(node);
            continue;
        }
        const children = filterSections(node.children, query);
        if (children.length) {
            filtered.push({ ...node, children });
        }
    }
    return filtered;
}

/** The ids of the leaf sections in `nodes`, depth-first. */
export function sectionIds(nodes: SectionNode[]): string[] {
    return nodes.flatMap((node) =>
        node.children ? sectionIds(node.children) : [node.id],
    );
}
