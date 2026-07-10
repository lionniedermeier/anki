<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<script lang="ts">
    import { getCard, getNote } from "@generated/backend";
    import { uiResolve } from "@tslib/ui";
    import { onMount } from "svelte";

    import NoteEditor from "../../editor/NoteEditor.svelte";

    interface Props {
        /** The selected row's id: a card id in cards mode, a note id in notes
         * mode. `null` when the selection isn't a single row, in which case the
         * editor is hidden and keeps showing whatever it last loaded. */
        rowId: bigint | null;
        notesMode: boolean;
    }

    let { rowId, notesMode }: Props = $props();

    /** `loadNote` is not a component export - NoteEditor only publishes it on
     * `globalThis` from its `onMount`. There is a single editor instance here,
     * so reading it off the global is unambiguous. */
    interface EditorGlobals {
        loadNote(args: {
            nid: bigint;
            notetypeId: bigint;
            initial: boolean;
        }): Promise<void>;
    }

    // NoteEditor is a child, so its onMount (and the globalThis registration it
    // performs) has already run by the time ours does.
    let ready = $state(false);
    onMount(() => {
        ready = true;
    });

    // Selections can change faster than the lookups below resolve; only the
    // newest one may drive the editor.
    let loadToken = 0;

    async function load(id: bigint, notes: boolean): Promise<void> {
        const token = ++loadToken;
        try {
            const nid = notes ? id : (await getCard({ cid: id })).noteId;
            // The editor needs the notetype up front: in browser mode it has no
            // notetype chooser to fall back on.
            const notetypeId = (await getNote({ nid }, { alertOnError: false }))
                .notetypeId;
            if (token !== loadToken) {
                return;
            }
            // `initial: true` records the args as the editor's reload baseline,
            // which it uses when a backend operation reports the note changed.
            await (globalThis as unknown as EditorGlobals).loadNote({
                nid,
                notetypeId,
                initial: true,
            });
        } catch {
            // Note or card deleted between selection and lookup.
        }
    }

    $effect(() => {
        const id = rowId;
        const notes = notesMode;
        if (!ready || id === null) {
            return;
        }
        void load(id, notes);
    });
</script>

<div class="browse-editor">
    <NoteEditor {uiResolve} mode="browser" isLegacy={false} />
</div>

<style lang="scss">
    .browse-editor {
        display: flex;
        flex-direction: column;
        height: 100%;
        min-height: 0;
        overflow: hidden;
    }
</style>
