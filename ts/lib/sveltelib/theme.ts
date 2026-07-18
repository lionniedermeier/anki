// Copyright: Ankitects Pty Ltd and contributors
// License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import { registerPackage } from "@tslib/runtime-require";
import { get, readable } from "svelte/store";

interface ThemeInfo {
    isDark: boolean;
}

function getThemeFromRoot(): ThemeInfo {
    return {
        isDark: document.documentElement.classList.contains("night-mode"),
    };
}

let setPageTheme: ((theme: ThemeInfo) => void) | null = null;
/** The current theme that applies to this document/shadow root. When
previewing cards in the card layout screen, this may not match the
theme Anki is using in its UI. */
export const pageTheme = readable(getThemeFromRoot(), (set) => {
    setPageTheme = set;
});
// ensure setPageTheme is set immediately
get(pageTheme);

// Update theme when root element's class changes.
const observer = new MutationObserver((_mutationsList, _observer) => {
    setPageTheme!(getThemeFromRoot());
});
observer.observe(document.documentElement, { attributeFilter: ["class"] });

export interface PrimitiveValues {
    light: string;
    dark: string;
}

const overriddenPrimitives = new Set<string>();

function primitiveVarNames(token: string): [string, string] {
    return [`--p-${token}-l`, `--p-${token}-d`];
}

function setPrimitive(token: string, values: PrimitiveValues): void {
    const [lightVar, darkVar] = primitiveVarNames(token);
    document.documentElement.style.setProperty(lightVar, values.light);
    document.documentElement.style.setProperty(darkVar, values.dark);
    overriddenPrimitives.add(token);
}

function setOverrides(overrides: Record<string, PrimitiveValues>): void {
    for (const token in overrides) {
        setPrimitive(token, overrides[token]);
    }
}

function clearOverride(token: string): void {
    const [lightVar, darkVar] = primitiveVarNames(token);
    document.documentElement.style.removeProperty(lightVar);
    document.documentElement.style.removeProperty(darkVar);
    overriddenPrimitives.delete(token);
}

function resetOverrides(): void {
    for (const token of [...overriddenPrimitives]) {
        clearOverride(token);
    }
}

function applyTheme(colors: Record<string, PrimitiveValues>): void {
    resetOverrides();
    setOverrides(colors);
}

export const ThemeManager = {
    setPrimitive,
    setOverrides,
    clearOverride,
    resetOverrides,
    applyTheme,
};

registerPackage("anki/theme", {
    pageTheme,
    ThemeManager,
});
