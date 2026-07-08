// Copyright: Ankitects Pty Ltd and contributors
// License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import { getNotetypeNames } from "@generated/backend";

import type { PageLoad } from "./$types";

export const load = (async () => {
    const { entries } = await getNotetypeNames({});
    return { notetypeNames: entries };
}) satisfies PageLoad;
