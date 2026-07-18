<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<script lang="ts">
    import * as tr from "@generated/ftl";
    import { onEnterOrSpace } from "@tslib/keys";

    import AlertBox from "$lib/components/Alert.svelte";
    import Badge from "$lib/components/Badge.svelte";
    import Icon from "$lib/components/Icon.svelte";
    import { minusIcon, plusIcon } from "$lib/components/icons";

    import { MapContext } from "./lib";

    export let unused: string[];
    export let ctx: MapContext;

    let unusedMsg: string;
    $: unusedMsg =
        ctx === MapContext.Field
            ? tr.changeNotetypeWillDiscardContent()
            : tr.changeNotetypeWillDiscardCards();

    const maxItems: number = 3;
    let collapsed: boolean = true;
    $: collapseMsg = collapsed
        ? tr.changeNotetypeExpand()
        : tr.changeNotetypeCollapse();
    $: icon = collapsed ? plusIcon : minusIcon;
</script>

<AlertBox variant="warning">
    {#if unused.length > maxItems}
        <div
            class="clickable"
            on:click={() => (collapsed = !collapsed)}
            on:keydown={onEnterOrSpace(() => (collapsed = !collapsed))}
            role="button"
            tabindex="0"
            aria-expanded={!collapsed}
        >
            <Badge iconSize={80}>
                <Icon {icon} />
            </Badge>
            {collapseMsg}
        </div>
    {/if}
    {unusedMsg}
    {#if collapsed}
        <div>
            {unused.slice(0, maxItems).join(", ")}
            {#if unused.length > maxItems}
                ... (+{unused.length - maxItems})
            {/if}
        </div>
    {:else}
        <ul>
            {#each unused as entry}
                <li>{entry}</li>
            {/each}
        </ul>
    {/if}
</AlertBox>

<style lang="scss">
    .clickable {
        cursor: pointer;
        font-weight: bold;
    }
</style>
