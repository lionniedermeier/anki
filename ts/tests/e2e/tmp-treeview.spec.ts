// Copyright: Ankitects Pty Ltd and contributors
// License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

// TEMPORARY verification spec - delete before committing.

import { expect, test } from "./fixtures";

test("treeview rows fill the sidebar width and own selection", async ({ page }) => {
    await page.goto("/browse", { waitUntil: "domcontentloaded" });

    const tree = page.locator(".browse-sidebar .tree-view");
    await expect(tree).toBeVisible({ timeout: 15_000 });

    const rows = page.locator(".browse-sidebar .tree-row");
    const count = await rows.count();
    expect(count).toBeGreaterThan(1);

    const treeBox = (await tree.boundingBox())!;

    // Every row, at every depth, spans the full width of the tree.
    for (let i = 0; i < count; i++) {
        const box = (await rows.nth(i).boundingBox())!;
        expect(Math.abs(box.x - treeBox.x)).toBeLessThan(1);
        expect(Math.abs(box.width - treeBox.width)).toBeLessThan(1);
    }

    // No row is a button-chrome LabelButton any more.
    await expect(page.locator(".browse-sidebar .label-button")).toHaveCount(0);

    // Expanding via the chevron must not select the row.
    const chevronRow = rows
        .filter({ has: page.locator(".tree-chevron.interactive") })
        .first();
    const chevron = chevronRow.locator(".tree-chevron.interactive");

    // The chevron carries no button chrome (it is a plain <div>), so hovering
    // it must not add a border that shifts its box.
    const before = (await chevron.boundingBox())!;
    await chevron.hover();
    const after = (await chevron.boundingBox())!;
    expect(Math.abs(after.x - before.x)).toBeLessThan(0.5);
    expect(Math.abs(after.width - before.width)).toBeLessThan(0.5);

    await chevron.click();
    await expect(chevronRow).not.toHaveClass(/selected/);

    // Clicking the row body selects it, and the highlight spans the tree width.
    await chevronRow.click({ position: { x: 120, y: 8 } });
    await expect(chevronRow).toHaveClass(/selected/);

    const selectedBox = (await chevronRow.boundingBox())!;
    expect(Math.abs(selectedBox.width - treeBox.width)).toBeLessThan(1);

    // A deeper row also fills the width, and selecting it moves the highlight.
    const deep = rows.nth(1);
    await deep.click({ position: { x: 120, y: 8 } });
    await expect(deep).toHaveClass(/selected/);
    await expect(chevronRow).not.toHaveClass(/selected/);
});
