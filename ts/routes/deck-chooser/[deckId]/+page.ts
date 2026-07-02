// Copyright: Ankitects Pty Ltd and contributors
// License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import { getDeck } from "@generated/backend";

import type { PageLoad } from "./$types";

export const load = (async ({ params, url }) => {
    const did = BigInt(params.deckId);
    const deck = await getDeck({ did });
    // parents that don't want the leading "Deck:" label pass ?label=0
    const showLabel = url.searchParams.get("label") !== "0";
    return { deck, showLabel };
}) satisfies PageLoad;
