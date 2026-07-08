<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<script lang="ts">
    import type { Notetype, NotetypeNameId } from "@generated/anki/notetypes_pb";
    import { getNotetype } from "@generated/backend";
    import * as tr from "@generated/ftl";
    import { untrack } from "svelte";
    import { writable } from "svelte/store";

    import CodeMirrorEditor from "$lib/components/CodeMirror/CodeMirrorEditor.svelte";
    import SplitPane from "$lib/components/SplitView/SplitPane.svelte";
    import SplitView from "$lib/components/SplitView/SplitView.svelte";
    import Tab from "$lib/components/TabView/Tab.svelte";
    import TabView from "$lib/components/TabView/TabView.svelte";

    import { htmlanki } from "../../editor/code-mirror";
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
</script>

<SplitView id="main-split">
    <SplitPane id="sidebar">
        <CardTypeSidebar
            {notetypeNames}
            bind:selectedNotetypeId
            templates={notetype?.templates ?? []}
            bind:selectedOrd
        />
    </SplitPane>
    <SplitPane id="editor" grow>
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
    </SplitPane>
    <SplitPane id="preview">
        <div class="pane-placeholder">Preview coming soon.</div>
    </SplitPane>
</SplitView>

<style lang="scss">
    .pane-placeholder {
        padding: 1rem;
        color: var(--fg-subtle);
    }
</style>
