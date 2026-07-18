// Copyright: Ankitects Pty Ltd and contributors
// License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import { getNotetypeNames } from "@generated/backend";

import type { PageLoad } from "./$types";

export const load = (async ({ url }) => {
    const { entries } = await getNotetypeNames({});
    const ntidParam = url.searchParams.get("ntid");
    const initialNotetypeId = ntidParam ? BigInt(ntidParam) : null;
    return { notetypeNames: entries, initialNotetypeId };
}) satisfies PageLoad;
