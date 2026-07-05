// Copyright: Ankitects Pty Ltd and contributors
// License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

/* eslint
@typescript-eslint/no-explicit-any: "off",
 */

import "../(main)/graphs/graphs-base.scss";

import { ModuleName, setupI18n } from "@tslib/i18n";
import { checkNightMode } from "@tslib/nightmode";
import type { Component } from "svelte";

import GraphsPage from "../(main)/graphs/GraphsPage.svelte";

const i18n = setupI18n({ modules: [ModuleName.STATISTICS, ModuleName.SCHEDULING] });

export async function setupGraphs(
    graphs: Component<any>[],
    {
        search = "deck:current",
        days = 365,
        controller = null satisfies Component<any> | null,
    } = {},
): Promise<GraphsPage> {
    checkNightMode();
    await i18n;

    return new GraphsPage({
        target: document.body,
        props: {
            initialSearch: search,
            initialDays: days,
            graphs,
            controller,
        },
    });
}

import AddedGraph from "../(main)/graphs/AddedGraph.svelte";
import ButtonsGraph from "../(main)/graphs/ButtonsGraph.svelte";
import CalendarGraph from "../(main)/graphs/CalendarGraph.svelte";
import CardCounts from "../(main)/graphs/CardCounts.svelte";
import DifficultyGraph from "../(main)/graphs/DifficultyGraph.svelte";
import EaseGraph from "../(main)/graphs/EaseGraph.svelte";
import FutureDue from "../(main)/graphs/FutureDue.svelte";
import { RevlogRange } from "../(main)/graphs/graph-helpers";
import HourGraph from "../(main)/graphs/HourGraph.svelte";
import IntervalsGraph from "../(main)/graphs/IntervalsGraph.svelte";
import RangeBox from "../(main)/graphs/RangeBox.svelte";
import RetrievabilityGraph from "../(main)/graphs/RetrievabilityGraph.svelte";
import ReviewsGraph from "../(main)/graphs/ReviewsGraph.svelte";
import StabilityGraph from "../(main)/graphs/StabilityGraph.svelte";
import TodayStats from "../(main)/graphs/TodayStats.svelte";

export const graphComponents = {
    TodayStats,
    FutureDue,
    CalendarGraph,
    ReviewsGraph,
    CardCounts,
    IntervalsGraph,
    StabilityGraph,
    EaseGraph,
    DifficultyGraph,
    RetrievabilityGraph,
    HourGraph,
    ButtonsGraph,
    AddedGraph,
    RangeBox,
    RevlogRange,
};
