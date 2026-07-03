// Copyright: Ankitects Pty Ltd and contributors
// License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

/** Formats a buried-count delta with an explicit sign (e.g. "+3", "-1"),
 * or "" when there is no difference. Mirrors the legacy overview's `{:+}`. */
export function buriedDelta(count: number): string {
    if (!count) {
        return "";
    }
    return count > 0 ? `+${count}` : `${count}`;
}
