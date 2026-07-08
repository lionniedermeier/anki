<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<script lang="ts">
    import type {
        Notetype,
        NotetypeNameId,
    } from "@generated/anki/notetypes_pb";
    import { getNotetype } from "@generated/backend";
    import { untrack } from "svelte";

    import SplitPane from "$lib/components/SplitView/SplitPane.svelte";
    import SplitView from "$lib/components/SplitView/SplitView.svelte";

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
        <div class="pane-placeholder">Template editor coming soon.</div>
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
