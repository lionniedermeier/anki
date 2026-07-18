<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<script lang="ts">
    import { goto, invalidateAll } from "$app/navigation";
    import { page } from "$app/state";
    import * as tr from "@generated/ftl";
    import { bridgeCommand } from "@tslib/bridgecommand";
    import type { Snippet } from "svelte";
    import { onMount } from "svelte";

    import Breadcrums from "$lib/components/Breadcrums/Breadcrums.svelte";
    import type { BreadcrumbItem } from "$lib/components/Breadcrums/Breadcrums";

    import type { LayoutData } from "./$types";

    interface Props {
        data: LayoutData;
        children?: Snippet;
    }

    let { data, children }: Props = $props();

    interface OverviewBreadcrumb extends BreadcrumbItem {
        deckName?: string;
        isOptions?: boolean;
    }

    const inOptions = $derived(page.url.pathname === "/deck-overview/options");

    const breadcrumbs = $derived<OverviewBreadcrumb[]>([
        { label: tr.browsingSidebarDecks() },
        ...data.deckName.split("::").map((part, i, arr) => ({
            label: part,
            deckName: arr.slice(0, i + 1).join("::"),
        })),
        ...(inOptions ? [{ label: tr.actionsOptions(), isOptions: true }] : []),
    ]);

    function openDecks(): void {
        goto("/deck-browser");
        bridgeCommand("decks");
    }

    function openDeck(name: string): void {
        bridgeCommand(`open:${name}`);
    }

    onMount(() => {
        (window as any).refreshDeckOverview = () => invalidateAll();
        return () => {
            delete (window as any).refreshDeckOverview;
        };
    });
</script>

<div class="deck-overview-layout">
    <Breadcrums items={breadcrumbs} class="breadcrumb">
        {#snippet item(entry, isLast)}
            {#if entry.isOptions}
                <span class="crumb crumb-options" aria-current="page">
                    {entry.label}
                </span>
            {:else if isLast}
                <span class="crumb" aria-current="page">{entry.label}</span>
            {:else if entry.deckName}
                <button
                    type="button"
                    class="crumb crumb-link"
                    onclick={() => openDeck(entry.deckName!)}
                >
                    {entry.label}
                </button>
            {:else}
                <button type="button" class="crumb crumb-link" onclick={openDecks}>
                    {entry.label}
                </button>
            {/if}
        {/snippet}
    </Breadcrums>

    {@render children?.()}
</div>

<style lang="scss">
    .deck-overview-layout {
        display: flex;
        flex-direction: column;
        height: 100%;
        padding: 0.5rem 1rem;
    }

    :global(.breadcrumb) {
        margin-top: 16px;
        margin-bottom: 16px;
    }

    .crumb {
        padding: 2px 4px;
    }

    .crumb-link {
        appearance: none;
        border: none;
        background: none;
        cursor: pointer;
        border-radius: 2px;
        font: inherit;

        &:hover {
            color: var(--fg);
            background-color: gainsboro;
        }
    }

    .crumb-options {
        color: var(--fg-subtle);
    }
</style>
