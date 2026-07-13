// Copyright: Ankitects Pty Ltd and contributors
// License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import { expect, test } from "vitest";

import type { SectionNode } from "./sections";
import { filterSections, sectionIds } from "./sections";

const nodes: SectionNode[] = [
    {
        id: "scheduling",
        title: () => "Scheduling",
        children: [
            {
                id: "lapses",
                title: () => "Lapses",
                keywords: () => ["Minimum interval", "Leech threshold"],
            },
            { id: "easy-days", title: () => "Easy Days" },
        ],
    },
    {
        id: "advanced",
        title: () => "Advanced",
        keywords: () => ["Maximum interval"],
    },
];

test("an empty query keeps everything", () => {
    expect(filterSections(nodes, "  ")).toBe(nodes);
});

test("keywords match, and non-matching leaves are pruned", () => {
    const filtered = filterSections(nodes, "interval");
    expect(sectionIds(filtered)).toStrictEqual(["lapses", "advanced"]);
});

test("matching a group keeps all of its children", () => {
    const filtered = filterSections(nodes, "schedul");
    expect(sectionIds(filtered)).toStrictEqual(["lapses", "easy-days"]);
});

test("matching is case-insensitive", () => {
    expect(sectionIds(filterSections(nodes, "EASY"))).toStrictEqual(["easy-days"]);
});

test("a query matching nothing yields no sections", () => {
    expect(filterSections(nodes, "nonexistent")).toStrictEqual([]);
});
