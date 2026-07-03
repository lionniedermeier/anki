// Copyright: Ankitects Pty Ltd and contributors
// License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import { expect, test } from "vitest";

import { buriedDelta } from "./lib";

test("buriedDelta formats with an explicit sign", () => {
    expect(buriedDelta(0)).toBe("");
    expect(buriedDelta(3)).toBe("+3");
    expect(buriedDelta(-1)).toBe("-1");
});
