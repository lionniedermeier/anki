<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<script lang="ts">
    import "codemirror/mode/css/css";

    import type CodeMirrorLib from "codemirror";
    import { promiseWithResolver } from "@tslib/promise";
    import { onMount } from "svelte";
    import type { Writable } from "svelte/store";

    import { pageTheme } from "$lib/sveltelib/theme";

    import {
        baseOptions,
        darkTheme,
        lightTheme,
        openCodeMirror,
        setupCodeMirror,
    } from "../../../routes/editor/code-mirror";

    interface CodeMirrorEditorProps {
        /** Two-way bound editor contents. Kept as a store so the existing
         * `setupCodeMirror` contract works and edits survive the editor being
         * torn down and recreated (e.g. when its tab is switched away). */
        code: Writable<string>;
        /** CodeMirror mode, e.g. `htmlanki` or `"css"`. */
        mode?: CodeMirrorLib.EditorConfiguration["mode"];
        class?: string;
    }

    let { code, mode, class: className = "" }: CodeMirrorEditorProps = $props();

    const [editorPromise, resolve] = promiseWithResolver<CodeMirrorLib.Editor>();

    const configuration = $derived<CodeMirrorLib.EditorConfiguration>({
        ...baseOptions,
        mode,
        theme: $pageTheme.isDark ? darkTheme : lightTheme,
        // `baseOptions` disables Tab (Tab: false) so it moves focus, which suits
        // the note editor. In the template editor we want Tab to indent
        // instead: indent the selection, or insert a soft tab at the caret.
        extraKeys: {
            Tab: (cm) => {
                if (cm.somethingSelected()) {
                    cm.execCommand("indentMore");
                } else {
                    cm.execCommand("insertSoftTab");
                }
            },
            "Shift-Tab": (cm) => cm.execCommand("indentLess"),
        },
    });

    onMount(async () => {
        const editor = await editorPromise;
        setupCodeMirror(editor, code);
        // `setupCodeMirror` only syncs the store into the editor; mirror edits
        // back out so the contents are captured even before a blur.
        editor.on("change", () => code.set(editor.getValue()));
    });
</script>

<div class="code-mirror {className}">
    <textarea
        tabindex="-1"
        hidden
        use:openCodeMirror={{ configuration, resolve, hidden: false }}
    ></textarea>
</div>

<style lang="scss">
    .code-mirror {
        height: 100%;

        :global(.CodeMirror) {
            height: 100%;
            font-family: Consolas, monospace;
        }

        :global(.CodeMirror-wrap pre) {
            word-break: break-word;
        }
    }
</style>
