<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<script lang="ts">
    import { goto } from "$app/navigation";
    import type { Notetype } from "@generated/anki/notetypes_pb";
    import { getNotetype, updateNotetype } from "@generated/backend";
    import * as tr from "@generated/ftl";
    import { untrack } from "svelte";

    import Breadcrums from "$lib/components/Breadcrums/Breadcrums.svelte";
    import type { BreadcrumbItem } from "$lib/components/Breadcrums/Breadcrums";
    import Tab from "$lib/components/TabView/Tab.svelte";
    import TabView from "$lib/components/TabView/TabView.svelte";

    import FieldOptions from "./FieldOptions.svelte";

    interface Props {
        notetype: Notetype;
    }

    let { notetype: initialNotetype }: Props = $props();

    // The parent wraps this component in `{#key data.notetype.id}`, so a new
    // instance (with a fresh initial value) is created whenever the route's
    // notetype id changes - read untracked because this only seeds the state.
    let notetype = $state(untrack(() => initialNotetype.clone()));
    let error = $state<string | null>(null);

    const breadcrumbs = $derived<BreadcrumbItem[]>([
        { label: tr.notetypesNoteTypes(), href: "/manage-notetypes" },
        { label: notetype.name },
    ]);

    // Persist a mutation against the last-saved notetype. The backend assigns
    // canonical field ordinals on write (they identify which stored note data
    // a field's contents come from - see rslib's `update_notes_for_changed_fields`),
    // so after saving we refetch rather than trust our locally cloned copy;
    // otherwise a newly added field would keep looking "ordinal-less" and a
    // later unrelated edit would be interpreted as adding it again, blanking
    // out any data entered into it in between.
    async function save(mutate: (nt: Notetype) => void): Promise<void> {
        const updated = notetype.clone();
        mutate(updated);
        error = null;
        try {
            await updateNotetype(updated);
            notetype = await getNotetype({ ntid: updated.id });
        } catch (err) {
            error = String(err);
        }
    }
</script>

<div class="notetype-detail">
    <div class="header">
        <Breadcrums items={breadcrumbs}>
            {#snippet item(entry, isLast)}
                {#if isLast}
                    <span aria-current="page">{entry.label}</span>
                {:else}
                    <button
                        type="button"
                        class="crumb-link"
                        onclick={() => goto(entry.href!)}
                    >
                        {entry.label}
                    </button>
                {/if}
            {/snippet}
        </Breadcrums>
        <h1>{notetype.name}</h1>
    </div>
    {#if error}
        <div class="error" role="alert">{error}</div>
    {/if}
    <div class="tabs-wrapper">
        <TabView id="notetype-detail-tabs" grow>
            <Tab id="latex" title={tr.notetypesOptions()}>
                <div class="latex-tab">
                    <label class="textarea-label">
                        <span>{tr.notetypesHeader()}</span>
                        <textarea
                            value={notetype.config?.latexPre ?? ""}
                            onchange={(e) => {
                                const value = e.currentTarget.value;
                                save((nt) => {
                                    if (nt.config) {
                                        nt.config.latexPre = value;
                                    }
                                });
                            }}
                        ></textarea>
                    </label>
                    <label class="textarea-label">
                        <span>{tr.notetypesFooter()}</span>
                        <textarea
                            value={notetype.config?.latexPost ?? ""}
                            onchange={(e) => {
                                const value = e.currentTarget.value;
                                save((nt) => {
                                    if (nt.config) {
                                        nt.config.latexPost = value;
                                    }
                                });
                            }}
                        ></textarea>
                    </label>
                    <label class="checkbox-label">
                        <input
                            type="checkbox"
                            checked={notetype.config?.latexSvg ?? false}
                            onchange={(e) => {
                                const checked = e.currentTarget.checked;
                                save((nt) => {
                                    if (nt.config) {
                                        nt.config.latexSvg = checked;
                                    }
                                });
                            }}
                        />
                        {tr.notetypesCreateScalableImagesWithDvisvgm()}
                    </label>
                </div>
            </Tab>
            <Tab id="fields" title={tr.notetypesFields()}>
                <FieldOptions {notetype} {save} />
            </Tab>
            <Tab id="cards" title={tr.notetypesCards()}>
                <div class="cards-tab">
                    <button
                        type="button"
                        class="open-cards"
                        onclick={() => goto(`/card-editor?ntid=${notetype.id}`)}
                    >
                        {tr.notetypesCards()}
                    </button>
                </div>
            </Tab>
        </TabView>
    </div>
</div>

<style lang="scss">
    .notetype-detail {
        display: flex;
        flex-direction: column;
        height: 100%;
        min-height: 0;
        padding: 1rem 1.5rem;
    }

    .header {
        flex: 0 0 auto;
        margin-block-end: 0.5rem;

        h1 {
            font-size: 1.2rem;
            margin: 0.25rem 0 0;
        }
    }

    .crumb-link {
        appearance: none;
        border: none;
        background: none;
        color: var(--fg-link);
        cursor: pointer;
        padding: 0;
        font: inherit;

        &:hover {
            color: var(--fg);
        }
    }

    .error {
        flex: 0 0 auto;
        color: var(--fg-danger, #d33);
        margin-block-end: 0.5rem;
    }

    .tabs-wrapper {
        flex: 1 1 auto;
        min-height: 0;
    }

    .latex-tab {
        display: flex;
        flex-direction: column;
        gap: 0.75rem;
        padding: 0.75rem;
        max-width: 40rem;
    }

    .textarea-label {
        display: flex;
        flex-direction: column;
        gap: 0.25rem;

        textarea {
            min-height: 6rem;
            font-family: monospace;
            resize: vertical;
        }
    }

    .checkbox-label {
        display: flex;
        align-items: center;
        gap: 0.4rem;
    }

    .cards-tab {
        padding: 0.75rem;
    }

    .open-cards {
        appearance: none;
        padding: 0.4rem 0.9rem;
        border: 1px solid var(--border);
        border-radius: 0.35rem;
        background: var(--canvas-elevated);
        color: var(--fg);
        cursor: pointer;

        &:hover {
            background: var(--canvas-inset);
        }
    }
</style>
