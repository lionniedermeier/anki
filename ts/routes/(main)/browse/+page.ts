// Copyright: Ankitects Pty Ltd and contributors
// License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import type { PlainMessage } from "@bufbuild/protobuf";
import type { SortOrder } from "@generated/anki/search_pb";
import { getBrowseSidebar, searchCards } from "@generated/backend";

import type { PageLoad } from "./$types";

const unsorted: PlainMessage<SortOrder> = { value: { case: "none", value: {} } };

export const load = (async () => {
    const [sidebar, search] = await Promise.all([
        getBrowseSidebar({}),
        searchCards({ search: "deck:current", order: unsorted }),
    ]);
    return { sidebar, initialSearch: "deck:current", initialIds: search.ids };
}) satisfies PageLoad;
