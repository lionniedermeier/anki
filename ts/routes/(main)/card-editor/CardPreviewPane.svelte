<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<script lang="ts">
    import type { RenderedTemplateNode } from "@generated/anki/card_rendering_pb";
    import { Note } from "@generated/anki/notes_pb";
    import type { Notetype } from "@generated/anki/notetypes_pb";
    import { Notetype_Template_Config } from "@generated/anki/notetypes_pb";
    import { renderUncommittedCard } from "@generated/backend";
    import * as tr from "@generated/ftl";
    import { get } from "svelte/store";

    import CardPreview from "./CardPreview.svelte";
    import { Toolbar, ToolbarGroup, ToolbarItem } from "$lib/components/Toolbar";
    import { pageTheme } from "$lib/sveltelib/theme";

    interface Props {
        notetype: Notetype | null;
        ord: number | null;
        /** Edited front template (config.qFormat). */
        front: string;
        /** Edited back template (config.aFormat). */
        back: string;
        /** Edited notetype CSS. */
        css: string;
    }

    let { notetype, ord, front, back, css }: Props = $props();

    type Mode = "front" | "back" | "both";
    let mode = $state<Mode>("front");

    // Preview options mirroring the legacy Qt card layout editor. Night mode is
    // seeded from the current app theme (read once) but can be overridden here.
    let nightMode = $state(get(pageTheme).isDark);
    let mobile = $state(false);
    // Fields are always empty in this editor, so default to showing
    // `(FieldName)` placeholders rather than a blank card.
    let fillEmpty = $state(true);

    let questionHtml = $state("");
    let answerHtml = $state("");

    /** Join rendered nodes into an HTML string. With partialRender=false every
     * node is a `text` node; a `replacement` only appears if a filter was left
     * unhandled, so fall back to its current text. */
    function nodesToHtml(nodes: RenderedTemplateNode[]): string {
        return nodes
            .map((node) => {
                switch (node.value.case) {
                    case "text":
                        return node.value.value;
                    case "replacement":
                        return node.value.value.currentText;
                    default:
                        return "";
                }
            })
            .join("");
    }

    // Re-render the card whenever the notetype, ordinal, or template text
    // changes. CSS is intentionally excluded: it only affects display and is
    // applied by CardPreview directly, so editing it needs no backend call.
    // Debounced (~200ms) like the Qt card-layout editor.
    $effect(() => {
        const nt = notetype;
        const cardOrd = ord;
        const qfmt = front;
        const afmt = back;
        const fill = fillEmpty;

        const template = nt?.templates.find((t) => t.ord?.val === cardOrd) ?? null;
        if (!nt || cardOrd === null || !template) {
            questionHtml = "";
            answerHtml = "";
            return;
        }

        let cancelled = false;
        const handle = setTimeout(async () => {
            const note = new Note({
                notetypeId: nt.id,
                fields: nt.fields.map(() => ""),
            });
            const tmpl = template.clone();
            tmpl.config ??= new Notetype_Template_Config();
            tmpl.config.qFormat = qfmt;
            tmpl.config.aFormat = afmt;

            const res = await renderUncommittedCard({
                note,
                cardOrd,
                template: tmpl,
                fillEmpty: fill,
                partialRender: false,
            });
            if (cancelled) {
                return;
            }
            questionHtml = nodesToHtml(res.questionNodes);
            answerHtml = nodesToHtml(res.answerNodes);
        }, 200);

        return () => {
            cancelled = true;
            clearTimeout(handle);
        };
    });
</script>

<div class="preview-pane">
    <div class="preview-toolbar">
        <Toolbar role="toolbar" wrap>
            <ToolbarGroup>
                <ToolbarItem id="front">
                    {#snippet children(disabled)}
                        <button
                            type="button"
                            class="toggle"
                            class:active={mode === "front"}
                            aria-pressed={mode === "front"}
                            {disabled}
                            onclick={() => (mode = "front")}
                        >
                            {tr.cardTemplatesFrontPreview()}
                        </button>
                    {/snippet}
                </ToolbarItem>
                <ToolbarItem id="back">
                    {#snippet children(disabled)}
                        <button
                            type="button"
                            class="toggle"
                            class:active={mode === "back"}
                            aria-pressed={mode === "back"}
                            {disabled}
                            onclick={() => (mode = "back")}
                        >
                            {tr.cardTemplatesBackPreview()}
                        </button>
                    {/snippet}
                </ToolbarItem>
                <!-- The combined view needs a card to render; hide it until one
                 is available to exercise id-based control. -->
                <ToolbarItem id="both" hidden={notetype === null}>
                    {#snippet children(disabled)}
                        <button
                            type="button"
                            class="toggle"
                            class:active={mode === "both"}
                            aria-pressed={mode === "both"}
                            {disabled}
                            onclick={() => (mode = "both")}
                        >
                            {tr.cardTemplatesBothPreview()}
                        </button>
                    {/snippet}
                </ToolbarItem>
            </ToolbarGroup>

            <!-- Preview options matching the legacy Qt card layout editor. -->
            <ToolbarGroup>
                <ToolbarItem id="fill-empty">
                    {#snippet children(disabled)}
                        <button
                            type="button"
                            class="toggle"
                            class:active={fillEmpty}
                            aria-pressed={fillEmpty}
                            {disabled}
                            onclick={() => (fillEmpty = !fillEmpty)}
                        >
                            {tr.cardTemplatesFillEmpty()}
                        </button>
                    {/snippet}
                </ToolbarItem>
                <ToolbarItem id="night-mode">
                    {#snippet children(disabled)}
                        <button
                            type="button"
                            class="toggle"
                            class:active={nightMode}
                            aria-pressed={nightMode}
                            {disabled}
                            onclick={() => (nightMode = !nightMode)}
                        >
                            {tr.cardTemplatesNightMode()}
                        </button>
                    {/snippet}
                </ToolbarItem>
                <ToolbarItem id="mobile">
                    {#snippet children(disabled)}
                        <button
                            type="button"
                            class="toggle"
                            class:active={mobile}
                            aria-pressed={mobile}
                            {disabled}
                            onclick={() => (mobile = !mobile)}
                        >
                            {tr.cardTemplatesAddMobileClass()}
                        </button>
                    {/snippet}
                </ToolbarItem>
            </ToolbarGroup>
        </Toolbar>
    </div>

    <div class="preview-body" class:split={mode === "both"}>
        {#if mode === "front"}
            <CardPreview
                html={questionHtml}
                {css}
                ord={ord ?? 0}
                {nightMode}
                {mobile}
            />
        {:else if mode === "back"}
            <CardPreview html={answerHtml} {css} ord={ord ?? 0} {nightMode} {mobile} />
        {:else}
            <div class="section">
                <div class="section-label">{tr.cardTemplatesFrontPreview()}</div>
                <div class="section-body">
                    <CardPreview
                        html={questionHtml}
                        {css}
                        ord={ord ?? 0}
                        {nightMode}
                        {mobile}
                    />
                </div>
            </div>
            <div class="section">
                <div class="section-label">{tr.cardTemplatesBackPreview()}</div>
                <div class="section-body">
                    <CardPreview
                        html={answerHtml}
                        {css}
                        ord={ord ?? 0}
                        {nightMode}
                        {mobile}
                    />
                </div>
            </div>
        {/if}
    </div>
</div>

<style lang="scss">
    .preview-pane {
        display: flex;
        flex-direction: column;
        height: 100%;
        min-height: 0;
    }

    // Mirror the TabView tab bar for a consistent look.
    .preview-toolbar {
        flex: 0 0 auto;
        padding: 0.25rem;
        border-bottom: 1px solid var(--border-subtle);
        background: var(--canvas);
    }

    .toggle {
        box-sizing: border-box;
        appearance: none;
        margin: 0;
        padding: 0.4rem 0.8rem;
        border: 1px solid transparent;
        border-radius: 0.35rem;
        background: transparent;
        color: var(--fg-subtle);
        line-height: 1.2;
        white-space: nowrap;
        cursor: pointer;

        &:hover {
            color: var(--fg);
            background: var(--canvas-inset);
        }

        &.active {
            color: var(--fg);
            background: var(--canvas-elevated);
            border-color: var(--border-subtle);
        }
    }

    .preview-body {
        flex: 1 1 auto;
        min-height: 0;

        &.split {
            display: flex;
            flex-direction: column;
        }
    }

    .section {
        display: flex;
        flex: 1 1 0;
        flex-direction: column;
        min-height: 0;

        & + .section {
            border-top: 1px solid var(--border-subtle);
        }
    }

    .section-label {
        flex: 0 0 auto;
        padding: 0.25rem 0.5rem;
        font-size: 0.8em;
        color: var(--fg-subtle);
        background: var(--canvas);
    }

    .section-body {
        flex: 1 1 auto;
        min-height: 0;
    }
</style>
