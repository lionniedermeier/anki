// Copyright: Ankitects Pty Ltd and contributors
// License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import { getDeck } from "@generated/backend";

import type { PageLoad } from "./$types";

export const load = (async ({ params }) => {
    const did = BigInt(params.deckId);
    const deck = await getDeck({ did });
    return { deck };
}) satisfies PageLoad;
