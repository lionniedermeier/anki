// Copyright: Ankitects Pty Ltd and contributors
// License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

/** Given the current scroll position and container/item sizing, returns the
 * inclusive-exclusive range of item indices that should be rendered. */
export function computeVisibleRange(
    scrollTop: number,
    containerHeight: number,
    itemHeight: number,
    itemsCount: number,
): { startIndex: number; endIndex: number } {
    if (itemHeight <= 0 || itemsCount <= 0) {
        return { startIndex: 0, endIndex: 0 };
    }
    const sliceLength = Math.ceil(containerHeight / itemHeight);
    const startIndex = Math.min(Math.floor(scrollTop / itemHeight), itemsCount);
    const endIndex = Math.min(startIndex + sliceLength, itemsCount);
    return { startIndex, endIndex };
}

function columnWidthsKey(viewId: string): string {
    return `columnWidths:${viewId}`;
}

/** Overlays widths persisted under `viewId` onto `defaults` by index. Falls
 * back to `defaults` entirely if nothing is stored, storage is unavailable,
 * or the stored array's length doesn't match (e.g. the column set changed,
 * as happens switching Browse's Cards/Notes mode). */
export function loadColumnWidths(viewId: string, defaults: number[]): number[] {
    try {
        const raw = localStorage.getItem(columnWidthsKey(viewId));
        if (!raw) {
            return defaults.slice();
        }
        const stored = JSON.parse(raw);
        if (!Array.isArray(stored) || stored.length !== defaults.length) {
            return defaults.slice();
        }
        return stored.map((width, index) => typeof width === "number" && width > 0 ? width : defaults[index]);
    } catch {
        return defaults.slice();
    }
}

export function saveColumnWidths(viewId: string, widths: number[]): void {
    try {
        localStorage.setItem(columnWidthsKey(viewId), JSON.stringify(widths));
    } catch {
        // storage may be unavailable (e.g. private browsing) - widths just
        // won't persist across reloads.
    }
}
