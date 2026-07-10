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
        magnifyIcon,
        mdiRefresh,
        plusIcon,
        mdiEarth,
        mdiCodeBlockTags,
    } from "$lib/components/icons";
    import IconConstrain from "$lib/components/IconConstrain.svelte";

    function openDecks(): void {
        bridgeCommand("decks");
    }

    function addCard(): void {
        bridgeCommand("add");
    }

    function browse(): void {
        bridgeCommand("browse");
    }

    function stats(): void {
        bridgeCommand("stats");
    }

    function sync(): void {
        bridgeCommand("sync");
    }
</script>

<div class="main-view">
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
    </ActivityBar>
    <div class="router-outlet">
        <slot />
    </div>
</div>

<style lang="scss">
    .main-view {
        display: flex;
        height: 100vh;
        align-items: stretch;
    }

    .router-outlet {
        flex: 1 1 auto;
        min-width: 0;
        overflow: auto;
    }
</style>
