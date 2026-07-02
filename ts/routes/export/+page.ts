// Copyright: Ankitects Pty Ltd and contributors
// License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import { getDeckNames } from "@generated/backend";

import type { PageLoad } from "./$types";

export const load = (async ({ url }) => {
    const didParam = url.searchParams.get("did");
    const nidsParam = url.searchParams.get("nids");

    const did = didParam ? BigInt(didParam) : null;
    const nids = nidsParam ? nidsParam.split(",").map((n) => BigInt(n)) : null;

    const decks = await getDeckNames({ skipEmptyDefault: false, includeFiltered: true });

    return { did, nids, deckNameIds: decks.entries };
}) satisfies PageLoad;
