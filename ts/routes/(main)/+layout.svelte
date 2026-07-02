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
    import { cardsOutlineIcon, chartBarIcon, magnifyIcon, mdiRefresh, plusIcon } from "$lib/components/icons";

    function openDecks(): void {
        goto("/deck-browser");
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
            on:click={openDecks}
        >
            <Icon icon={cardsOutlineIcon} />
        </ActivityBarItem>
        <ActivityBarItem tooltip={tr.actionsAdd()} on:click={addCard}>
            <Icon icon={plusIcon} />
        </ActivityBarItem>
        <ActivityBarItem tooltip={tr.qtMiscBrowse()} on:click={browse}>
            <Icon icon={magnifyIcon} />
        </ActivityBarItem>
        <ActivityBarItem tooltip={tr.qtMiscStats()} on:click={stats}>
            <Icon icon={chartBarIcon} />
        </ActivityBarItem>
        <ActivityBarItem tooltip={tr.qtMiscSync()} on:click={sync}>
            <Icon icon={mdiRefresh} />
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
