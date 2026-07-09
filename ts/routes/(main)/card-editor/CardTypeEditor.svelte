<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<script lang="ts">
    import type { Notetype, NotetypeNameId } from "@generated/anki/notetypes_pb";
    import { Notetype_Template_Config } from "@generated/anki/notetypes_pb";
    import { getNotetype, updateNotetype } from "@generated/backend";
    import * as tr from "@generated/ftl";
    import { untrack } from "svelte";
    import { writable } from "svelte/store";

    import CodeMirrorEditor from "$lib/components/CodeMirror/CodeMirrorEditor.svelte";
    import SplitPane from "$lib/components/SplitView/SplitPane.svelte";
    import SplitView from "$lib/components/SplitView/SplitView.svelte";
    import Tab from "$lib/components/TabView/Tab.svelte";
    import TabView from "$lib/components/TabView/TabView.svelte";

    import { htmlanki } from "../../editor/code-mirror";
    import CardPreviewPane from "./CardPreviewPane.svelte";
    import CardTypeSidebar from "./CardTypeSidebar.svelte";

    interface Props {
        notetypeNames: NotetypeNameId[];
    }

    let { notetypeNames }: Props = $props();

    // Default the selection to the first notetype; read untracked because this
    // only seeds the initial value.
    let selectedNotetypeId = $state<bigint | null>(
        untrack(() => notetypeNames[0]?.id ?? null),
    );
    let notetype = $state<Notetype | null>(null);
    let selectedOrd = $state<number | null>(null);

    // The card template currently being edited.
    const template = $derived(
        notetype?.templates.find((t) => t.ord?.val === selectedOrd) ?? null,
    );

    // Editor contents. Kept as stores so CodeMirrorEditor can bind to them and
    // edits survive the editor being recreated on tab switches. The front/back
    // are per-template; the CSS is shared across the whole notetype.
    const frontCode = writable("");
    const backCode = writable("");
    const cssCode = writable("");

    // Seed the editors whenever the selected template or notetype changes.
    $effect(() => {
        frontCode.set(template?.config?.qFormat ?? "");
        backCode.set(template?.config?.aFormat ?? "");
        cssCode.set(notetype?.config?.css ?? "");
    });

    // Fetch the full notetype (fields + card templates + css) whenever the
    // selected notetype changes. The fetch is async, so a stale response is
    // discarded when the selection moves on before it resolves.
    $effect(() => {
        const ntid = selectedNotetypeId;
        if (ntid === null) {
            notetype = null;
            selectedOrd = null;
            return;
        }
        let cancelled = false;
        getNotetype({ ntid }).then((fetched) => {
            if (cancelled) {
                return;
            }
            notetype = fetched;
            selectedOrd = fetched.templates[0]?.ord?.val ?? null;
        });
        return () => {
            cancelled = true;
        };
    });

    // Whether the editor contents differ from the loaded notetype. Store reads
    // are reactive inside `$derived`, so this recomputes as the user types and
    // resets to false once `notetype` is reassigned after a save.
    const dirty = $derived(
        !!notetype &&
            !!template &&
            ($frontCode !== (template.config?.qFormat ?? "") ||
                $backCode !== (template.config?.aFormat ?? "") ||
                $cssCode !== (notetype.config?.css ?? "")),
    );
    let saving = $state(false);
    let justSaved = $state(false);

    // Persist the current editor contents to the selected card template + CSS.
    // `Notetype` is a protobuf message (a class instance), which Svelte does not
    // deep-proxy, so we clone + reassign rather than mutating in place — that is
    // what makes `template`/`dirty` recompute afterwards.
    async function save() {
        if (!notetype || selectedOrd === null || !dirty || saving) {
            return;
        }
        const updated = notetype.clone();
        const tmpl = updated.templates.find((t) => t.ord?.val === selectedOrd);
        if (!tmpl) {
            return;
        }
        tmpl.config ??= new Notetype_Template_Config();
        tmpl.config.qFormat = $frontCode;
        tmpl.config.aFormat = $backCode;
        if (updated.config) {
            updated.config.css = $cssCode;
        }
        saving = true;
        try {
            await updateNotetype(updated);
            notetype = updated;
            justSaved = true;
            setTimeout(() => (justSaved = false), 2000);
        } catch (err) {
            // Surface template/validation errors instead of silently dropping.
            alert(String(err));
        } finally {
            saving = false;
        }
    }

    function onKeydown(event: KeyboardEvent): void {
        if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "s") {
            event.preventDefault();
            save();
        }
    }

    // Selection changes are routed through here so unsaved edits can be saved or
    // discarded before the reseed effect above overwrites the editor contents.
    async function guardedSwitch(apply: () => void): Promise<void> {
        if (dirty) {
            if (confirm(tr.cardTemplatesSaveChanges())) {
                await save();
            }
            // Otherwise the edits are discarded; either way we proceed.
        }
        apply();
    }
    const requestSelectNotetype = (id: bigint) =>
        guardedSwitch(() => (selectedNotetypeId = id));
    const requestSelectTemplate = (ord: number | null) =>
        guardedSwitch(() => (selectedOrd = ord));
</script>

<svelte:window onkeydown={onKeydown} />

<SplitView id="main-split">
    <SplitPane id="sidebar">
        <CardTypeSidebar
            {notetypeNames}
            {selectedNotetypeId}
            templates={notetype?.templates ?? []}
            {selectedOrd}
            onSelectNotetype={requestSelectNotetype}
            onSelectTemplate={requestSelectTemplate}
        />
    </SplitPane>
    <SplitPane id="editor" grow>
        <div class="editor-pane">
            <TabView id="card-template-tabs" grow>
                <Tab id="front" title={tr.cardTemplatesFrontTemplate()}>
                    <CodeMirrorEditor code={frontCode} mode={htmlanki} />
                </Tab>
                <Tab id="back" title={tr.cardTemplatesBackTemplate()}>
                    <CodeMirrorEditor code={backCode} mode={htmlanki} />
                </Tab>
                <Tab id="css" title={tr.cardTemplatesTemplateStyling()}>
                    <CodeMirrorEditor code={cssCode} mode="css" />
                </Tab>
            </TabView>
            <div class="save-bar">
                {#if justSaved}
                    <span class="status saved">{tr.cardTemplatesChangesSaved()}</span>
                {:else if dirty}
                    <span class="status unsaved" aria-hidden="true">●</span>
                {/if}
                <button
                    type="button"
                    class="save-button"
                    onclick={save}
                    disabled={!dirty || saving}
                >
                    {tr.actionsSave()}
                </button>
            </div>
        </div>
    </SplitPane>
    <SplitPane id="preview">
        <CardPreviewPane
            {notetype}
            ord={selectedOrd}
            front={$frontCode}
            back={$backCode}
            css={$cssCode}
        />
    </SplitPane>
</SplitView>

<style lang="scss">
    .editor-pane {
        display: flex;
        flex-direction: column;
        height: 100%;
        min-height: 0;
    }

    .save-bar {
        display: flex;
        flex: 0 0 auto;
        gap: 0.5rem;
        align-items: center;
        justify-content: flex-end;
        padding: 0.35rem 0.5rem;
        border-top: 1px solid var(--border-subtle);
        background: var(--canvas);
    }

    .status {
        font-size: 0.85em;

        &.unsaved {
            color: var(--fg-subtle);
        }

        &.saved {
            color: var(--fg-subtle);
        }
    }

    .save-button {
        appearance: none;
        padding: 0.35rem 0.9rem;
        border: 1px solid var(--border);
        border-radius: 0.35rem;
        background: var(--canvas-elevated);
        color: var(--fg);
        cursor: pointer;

        &:hover:not(:disabled) {
            background: var(--canvas-inset);
        }

        &:disabled {
            opacity: 0.5;
            cursor: default;
        }
    }
</style>
