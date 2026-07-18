#!/usr/bin/env python3
# Copyright: Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

"""Generates the SCSS token partial, Qt color/prop constants, and the theme
schema from ts/lib/sass/tokens.json, which is the single source of truth for
Anki's semantic design tokens.
"""

import json
import re
import sys

tokens_json = sys.argv[1]
tokens_scss_out = sys.argv[2]
colors_py_out = sys.argv[3]
props_py_out = sys.argv[4]
theme_schema_out = sys.argv[5]

with open(tokens_json) as f:
    tokens = json.load(f)

props: dict[str, dict[str, str]] = tokens["props"]
colors: dict[str, dict[str, str]] = tokens["colors"]

copyright_notice = """\
# Copyright: Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html\n
"""


def to_qt_name(token: str) -> str:
    return token.replace("-", "_").upper()


def scss_entry(comment: str, values: str) -> str:
    return f'("{comment}", {values})'


with open(tokens_scss_out, "w") as buf:
    buf.write(
        "/* Copyright: Ankitects Pty Ltd and contributors\n"
        " * License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html */\n\n"
        "// This file was automatically generated from tokens.json\n\n"
    )

    buf.write("$token-colors: (\n")
    for name, val in colors.items():
        values = f"(light: {val['light']}, dark: {val['dark']})"
        buf.write(f'    "{name}": {scss_entry(val["comment"], values)},\n')
    buf.write(");\n\n")

    buf.write("$token-props: (\n")
    for name, val in props.items():
        buf.write(f'    "{name}": {scss_entry(val["comment"], val["value"])},\n')
    buf.write(");\n")


with open(colors_py_out, "w") as buf:
    buf.write(copyright_notice)
    buf.write("# This file was automatically generated from tokens.json\n")

    for name, val in colors.items():
        entry = {"comment": val["comment"], "light": val["light"], "dark": val["dark"]}
        buf.write(
            re.sub(
                r"\"\n", '",\n', f"{to_qt_name(name)} = {json.dumps(entry, indent=4)}\n"
            )
        )


with open(props_py_out, "w") as buf:
    buf.write(copyright_notice)
    buf.write("# This file was automatically generated from tokens.json\n")

    for name, val in props.items():
        # remove trailing ms from time props, matching Qt's expectations
        value = re.sub(r"^(\d+)ms$", r"\1", val["value"])
        entry = {"comment": val["comment"], "light": value, "dark": value}
        buf.write(
            re.sub(
                r"\"\n", '",\n', f"{to_qt_name(name)} = {json.dumps(entry, indent=4)}\n"
            )
        )


schema = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$comment": "Generated from tokens.json. Describes the shape of a theme "
    "JSON file, and the semantic color tokens it may override.",
    "title": "Anki color theme",
    "type": "object",
    "required": ["name", "type", "colors"],
    "properties": {
        "id": {
            "type": "string",
            "description": "Unique id for the theme; defaults to the filename if omitted.",
        },
        "name": {
            "type": "string",
            "description": "Display name shown in the theme picker.",
        },
        "type": {
            "type": "string",
            "enum": ["light", "dark"],
            "description": "Whether this theme should be offered as a light or dark theme.",
        },
        "colors": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                name: {"type": "string", "description": val["comment"]}
                for name, val in colors.items()
            },
        },
    },
}
with open(theme_schema_out, "w") as buf:
    json.dump(schema, buf, indent=2)
    buf.write("\n")
