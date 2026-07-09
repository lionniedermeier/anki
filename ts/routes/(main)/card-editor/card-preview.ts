// Copyright: Ankitects Pty Ltd and contributors
// License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

/**
 * Build the `srcdoc` for a card-preview iframe.
 *
 * Mirrors pylib's `question_and_style()` + `qt/aqt/theme.py`'s
 * `body_classes_for_card_ord()`: the notetype CSS is global and expects a
 * `.card`/`.cardN` body, so it is carried inline in a `<style>` block and the
 * body gets the matching classes (`nightMode night_mode` when night mode is on).
 * The `mobile` class is toggled on `<html>`, matching the reviewer's
 * `_emulateMobile()`.
 *
 * Lives in a `.ts` file rather than inline in the Svelte component because a
 * literal `<style>` tag in a component's `<script>` confuses the Svelte style
 * preprocessor.
 */
export function buildPreviewSrcdoc(
    html: string,
    css: string,
    ord: number,
    nightMode: boolean,
    mobile: boolean,
): string {
    const bodyClass = `card card${ord + 1}${nightMode ? " nightMode night_mode" : ""}`;
    const htmlClass = [nightMode ? "night-mode" : "", mobile ? "mobile" : ""]
        .filter(Boolean)
        .join(" ");
    const styleTag = `<style>${css}</style>`;
    return (
        `<!DOCTYPE html><html class="${htmlClass}"><head><meta charset="utf-8">${styleTag}</head>`
        + `<body class="${bodyClass}">${html}</body></html>`
    );
}
