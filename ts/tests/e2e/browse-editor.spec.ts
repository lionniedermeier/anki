// Copyright: Ankitects Pty Ltd and contributors
// License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

/**
 * Browse view editor pane.
 *
 * Selecting exactly one row reveals a third pane hosting the note editor;
 * selecting several hides it again. Edits are persisted straight to the
 * backend via updateNotes.
 *
 * The pane is hidden rather than unmounted, so the editor is asserted on
 * visibility, not presence.
 *
 * This test mutates the collection - two notes are persisted on every run.
 */

import type { Locator, Page } from "@playwright/test";

import { UpdateNotesRequest } from "@generated/anki/notes_pb";

import { expect, test } from "./fixtures";
import { decodeRequestBody, editableField, isRpc } from "./helpers";

/** Adds a note through the add editor the fixture already has open. */
async function addNote(page: Page, front: string): Promise<void> {
    const field0 = editableField(page, 0);
    await field0.click();
    await field0.pressSequentially(front);
    const added = page.waitForRequest(isRpc("addNote"), { timeout: 10_000 });
    await page.getByRole("button", { name: "Add", exact: true }).click();
    await added;
    await expect(field0).toHaveText("", { timeout: 5_000 });
}

function bodyRows(page: Page): Locator {
    return page.locator(".vg-body .vg-row");
}

function editor(page: Page): Locator {
    return page.locator(".note-editor");
}

test("browse editor pane follows the row selection", async ({ editor: page }) => {
    await addNote(page, "First");
    await addNote(page, "Second");

    await page.goto("/browse", { waitUntil: "domcontentloaded" });

    const rows = bodyRows(page);
    await expect(rows).toHaveCount(2, { timeout: 15_000 });

    // Nothing selected, so the pane is hidden.
    await expect(editor(page)).not.toBeVisible();

    // A single selection reveals the editor, loaded with that note.
    await rows.first().click();
    await expect(editor(page)).toBeVisible({ timeout: 15_000 });
    const field0 = editableField(page, 0);
    await expect(field0).toHaveText("First", { timeout: 15_000 });

    // Editing a field writes straight through to the backend.
    const updated = page.waitForRequest(isRpc("updateNotes"), { timeout: 15_000 });
    await field0.click();
    await field0.pressSequentially(" edited");
    const decoded = decodeRequestBody(await updated, UpdateNotesRequest);
    expect(decoded.notes[0]?.fields[0]).toBe("First edited");

    // Selecting a second row hides the pane.
    await rows.nth(1).click({ modifiers: ["ControlOrMeta"] });
    await expect(editor(page)).not.toBeVisible({ timeout: 10_000 });

    // Back to a single selection: the editor returns, showing the other note.
    await rows.nth(1).click();
    await expect(editor(page)).toBeVisible({ timeout: 10_000 });
    await expect(editableField(page, 0)).toHaveText("Second", { timeout: 15_000 });
});
