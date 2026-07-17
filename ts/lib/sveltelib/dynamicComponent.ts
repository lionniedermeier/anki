// Copyright: Ankitects Pty Ltd and contributors
// License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

/* eslint
@typescript-eslint/no-explicit-any: "off",
 */

import type { Component, SvelteComponent } from "svelte";

/** Add-ons may supply either a legacy class-style component or a Svelte 5
 * (runes) one, so both are accepted here. */
type AnyComponent = typeof SvelteComponent<any> | Component<any, any, any>;

export interface DynamicSvelteComponent<T extends AnyComponent = AnyComponent> {
    component: T;
    [k: string]: unknown;
}
