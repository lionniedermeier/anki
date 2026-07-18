<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<script lang="ts">
    import { goto } from "$app/navigation";
    import { page } from "$app/state";
    import * as tr from "@generated/ftl";
    import { bridgeCommand } from "@tslib/bridgecommand";

    import ActivityBar from "$lib/components/ActivityBar/ActivityBar.svelte";
    import ActivityBarItem from "$lib/components/ActivityBar/ActivityBarItem.svelte";
    import Icon from "$lib/components/Icon.svelte";
    import {
        cardsOutlineIcon,
        chartBarIcon,
        formTextboxIcon,
        magnifyIcon,
        mdiRefresh,
        plusIcon,
        mdiCodeBlockTags,
    } from "$lib/components/icons";
    import IconConstrain from "$lib/components/IconConstrain.svelte";

    let { children } = $props();

    const inReview = $derived(page.url.pathname === "/reviewer");
    let revealed = $state(false);
    let hideTimeout: number | undefined;

    function reveal(): void {
        if (hideTimeout !== undefined) {
            clearTimeout(hideTimeout);
            hideTimeout = undefined;
        }
        revealed = true;
    }

    function scheduleHide(): void {
        if (hideTimeout !== undefined) {
            clearTimeout(hideTimeout);
        }
        hideTimeout = window.setTimeout(() => {
            revealed = false;
        }, 500);
    }

    function openDecks(): void {
        goto("/deck-browser");
        bridgeCommand("decks");
    }

    function addCard(): void {
        bridgeCommand("add");
    }

    function browse(): void {
        goto("/browse");
        bridgeCommand("browse");
    }

    function stats(): void {
        goto("/graphs");
        bridgeCommand("stats");
    }

    function sync(): void {
        bridgeCommand("sync");
    }
</script>

<div class="main-view" class:in-review={inReview}>
    <!-- svelte-ignore a11y_no_static_element_interactions -->
    <div
        class="activity-bar-wrapper"
        class:revealed
        onmouseenter={reveal}
        onmouseleave={scheduleHide}
    >
        <ActivityBar vertical>
            <ActivityBarItem
                active={page.url.pathname === "/deck-browser"}
                tooltip={tr.actionsDecks()}
                onclick={openDecks}
            >
                <IconConstrain>
                    <Icon icon={cardsOutlineIcon} />
                </IconConstrain>
            </ActivityBarItem>
            <ActivityBarItem tooltip={tr.actionsAdd()} onclick={addCard}>
                <IconConstrain>
                    <Icon icon={plusIcon} />
                </IconConstrain>
            </ActivityBarItem>
            <ActivityBarItem
                active={page.url.pathname === "/browse"}
                tooltip={tr.qtMiscBrowse()}
                onclick={browse}
            >
                <IconConstrain>
                    <Icon icon={magnifyIcon} />
                </IconConstrain>
            </ActivityBarItem>
            <ActivityBarItem
                active={page.url.pathname === "/graphs"}
                tooltip={tr.qtMiscStats()}
                onclick={stats}
            >
                <IconConstrain>
                    <Icon icon={chartBarIcon} />
                </IconConstrain>
            </ActivityBarItem>
            <ActivityBarItem tooltip={tr.qtMiscSync()} onclick={sync}>
                <IconConstrain>
                    <Icon icon={mdiRefresh} />
                </IconConstrain>
            </ActivityBarItem>
            <ActivityBarItem
                active={page.url.pathname === "/card-editor"}
                onclick={() => goto("/card-editor")}
            >
                <IconConstrain>
                    <Icon icon={mdiCodeBlockTags} />
                </IconConstrain>
            </ActivityBarItem>
            <ActivityBarItem
                active={page.url.pathname.startsWith("/manage-notetypes")}
                tooltip={tr.notetypesNoteTypes()}
                onclick={() => goto("/manage-notetypes")}
            >
                <IconConstrain>
                    <Icon icon={formTextboxIcon} />
                </IconConstrain>
            </ActivityBarItem>
        </ActivityBar>
    </div>
    {#if inReview}
        <!-- svelte-ignore a11y_no_static_element_interactions -->
        <div class="edge-hover-zone" onmouseenter={reveal}></div>
    {/if}
    <div class="router-outlet">
        {@render children?.()}
    </div>
</div>

<style lang="scss">
    .main-view {
        display: flex;
        height: 100vh;
        align-items: stretch;
        position: relative;
    }

    .activity-bar-wrapper {
        flex-shrink: 0;
        display: flex;
    }

    .router-outlet {
        flex: 1 1 auto;
        min-width: 0;
        overflow: auto;
    }

    .main-view.in-review .activity-bar-wrapper {
        position: absolute;
        inset-block: 0;
        inset-inline-start: 0;
        z-index: 20;
        transform: translateX(-100%);
        transition: transform 0.15s ease;

        &.revealed {
            transform: translateX(0);
        }
    }

    .edge-hover-zone {
        position: absolute;
        inset-block: 0;
        inset-inline-start: 0;
        width: 10px;
        z-index: 10;
    }
</style>
