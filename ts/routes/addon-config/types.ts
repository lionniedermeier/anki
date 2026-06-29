// Copyright: Ankitects Pty Ltd and contributors
// License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

/** A JSON-Schema-style field descriptor from config.schema.json. */
export interface FieldDescriptor {
    type?: "boolean" | "integer" | "number" | "string" | "object" | "array";
    title?: string;
    description?: string;
    default?: unknown;
    enum?: unknown[];
    enumDescriptions?: string[];
    minimum?: number;
    maximum?: number;
    multipleOf?: number;
    multiline?: boolean;
}

/** Field key → descriptor (parsed from schema_json). */
export type ConfigProperties = Record<string, FieldDescriptor>;
/** Field key → value (parsed from config_json / defaults_json). */
export type ConfigValues = Record<string, unknown>;
