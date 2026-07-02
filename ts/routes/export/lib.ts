// Copyright: Ankitects Pty Ltd and contributors
// License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import * as tr from "@generated/ftl";

export interface ExportFormat {
    id: number;
    extension: string;
    name: () => string;
    showDeckList: boolean;
    showIncludeScheduling: boolean;
    showIncludeDeckConfigs: boolean;
    showIncludeMedia: boolean;
    showIncludeTags: boolean;
    showIncludeHtml: boolean;
    showIncludeDeck: boolean;
    showIncludeNotetype: boolean;
    showIncludeGuid: boolean;
    showLegacySupport: boolean;
}

/**
 * Keep in sync with the exporter_classes list and Exporter subclasses in
 * qt/aqt/import_export/exporting.py. Order matters: formatId is used as an
 * index into this list on both sides of the bridge.
 */
export const EXPORT_FORMATS: ExportFormat[] = [
    {
        id: 0,
        extension: "apkg",
        name: () => tr.exportingAnkiDeckPackage(),
        showDeckList: true,
        showIncludeScheduling: true,
        showIncludeDeckConfigs: true,
        showIncludeMedia: true,
        showIncludeTags: false,
        showIncludeHtml: false,
        showIncludeDeck: false,
        showIncludeNotetype: false,
        showIncludeGuid: false,
        showLegacySupport: true,
    },
    {
        id: 1,
        extension: "colpkg",
        name: () => tr.exportingAnkiCollectionPackage(),
        showDeckList: false,
        showIncludeScheduling: false,
        showIncludeDeckConfigs: false,
        showIncludeMedia: true,
        showIncludeTags: false,
        showIncludeHtml: false,
        showIncludeDeck: false,
        showIncludeNotetype: false,
        showIncludeGuid: false,
        showLegacySupport: true,
    },
    {
        id: 2,
        extension: "txt",
        name: () => tr.exportingNotesInPlainText(),
        showDeckList: true,
        showIncludeScheduling: false,
        showIncludeDeckConfigs: false,
        showIncludeMedia: false,
        showIncludeTags: true,
        showIncludeHtml: true,
        showIncludeDeck: true,
        showIncludeNotetype: true,
        showIncludeGuid: true,
        showLegacySupport: false,
    },
    {
        id: 3,
        extension: "txt",
        name: () => tr.exportingCardsInPlainText(),
        showDeckList: true,
        showIncludeScheduling: false,
        showIncludeDeckConfigs: false,
        showIncludeMedia: false,
        showIncludeTags: false,
        showIncludeHtml: true,
        showIncludeDeck: false,
        showIncludeNotetype: false,
        showIncludeGuid: false,
        showLegacySupport: false,
    },
];

/** Mirrors ExportDialog._setup_ui()'s default_exporter_idx logic: a bare
 * File>Export defaults to the collection package; exporting a specific deck
 * or a note selection defaults to the deck package. */
export function defaultFormatId(hasDid: boolean, hasNids: boolean): number {
    return !hasDid && !hasNids ? 1 : 0;
}

export interface ExportOptionsState {
    includeScheduling: boolean;
    includeDeckConfigs: boolean;
    includeMedia: boolean;
    includeHtml: boolean;
    includeTags: boolean;
    includeDeck: boolean;
    includeNotetype: boolean;
    includeGuid: boolean;
    legacySupport: boolean;
}

/** Mirrors the checkbox defaults in qt/aqt/forms/exporting.ui, including the
 * scheduling override applied when exporting a single deck. */
export function defaultOptions(hasDid: boolean): ExportOptionsState {
    return {
        includeScheduling: !hasDid,
        includeDeckConfigs: false,
        includeMedia: true,
        includeHtml: true,
        includeTags: true,
        includeDeck: false,
        includeNotetype: false,
        includeGuid: false,
        legacySupport: false,
    };
}
