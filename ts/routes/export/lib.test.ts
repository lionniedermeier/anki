// Copyright: Ankitects Pty Ltd and contributors
// License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import { describe, expect, test } from "vitest";

import { defaultFormatId, defaultOptions, EXPORT_FORMATS } from "./lib";

describe("defaultFormatId", () => {
    test("bare export defaults to collection package (colpkg)", () => {
        expect(defaultFormatId(false, false)).toBe(1);
    });

    test("exporting a deck defaults to deck package (apkg)", () => {
        expect(defaultFormatId(true, false)).toBe(0);
    });

    test("exporting selected notes defaults to deck package (apkg)", () => {
        expect(defaultFormatId(false, true)).toBe(0);
    });
});

describe("defaultOptions", () => {
    test("scheduling is included by default", () => {
        expect(defaultOptions(false).includeScheduling).toBe(true);
    });

    test("scheduling is excluded when exporting a single deck", () => {
        expect(defaultOptions(true).includeScheduling).toBe(false);
    });

    test("media, html and tags are included by default", () => {
        const options = defaultOptions(false);
        expect(options.includeMedia).toBe(true);
        expect(options.includeHtml).toBe(true);
        expect(options.includeTags).toBe(true);
    });
});

describe("EXPORT_FORMATS", () => {
    test("ids match their array index, as Python indexes into the same list", () => {
        EXPORT_FORMATS.forEach((format, index) => {
            expect(format.id).toBe(index);
        });
    });
});
