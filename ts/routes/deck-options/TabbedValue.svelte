<!--
    Copyright: Ankitects Pty Ltd and contributors
    License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<script lang="ts">
    /* This component accepts an array of tabs and a value. Whenever a tab is
    activated, its last used value is applied to its provided setter and the
    component's value. Whenever it's deactivated, its setter is called with its
    disabledValue. */
    import { untrack } from "svelte";

    import type { ValueTab } from "./lib";

    interface Props {
        tabs: ValueTab[];
        value: number;
    }

    let { tabs, value = $bindable() }: Props = $props();

    function lastSetTab(): number {
        const revIdx = tabs
            .slice()
            .reverse()
            .findIndex((tab) => tab.value !== null);
        return revIdx === -1 ? 0 : tabs.length - revIdx - 1;
    }

    let activeTab = $state(lastSetTab());

    // The tabs are deeply reactive, so every read/write of tab.value is tracked.
    // Untracking the tab internals keeps these effects depending on tabs,
    // activeTab and value alone, and stops them from re-triggering each other on
    // every keystroke into the spinbox.
    $effect(() => {
        const currentTab = activeTab;
        untrack(() => onTabChanged(currentTab));
    });
    $effect(() => {
        const tab = tabs[activeTab];
        value = untrack(() => tab.value) ?? 0;
    });
    $effect(() => {
        const tab = tabs[activeTab];
        const newValue = value;
        untrack(() => tab.setValue(newValue));
    });

    function onTabChanged(newTab: number) {
        for (const [idx, tab] of tabs.entries()) {
            if (newTab === idx) {
                tab.enable(value);
            } else if (newTab > idx) {
                /* antecedent tabs are obscured, so we can preserve their original values */
                tab.reset();
            } else {
                /* but subsequent tabs would obscure, so they must be nulled */
                tab.disable();
            }
        }
    }

    const handleClick = (tabValue: number) => () => (activeTab = tabValue);
</script>

<ul>
    {#each tabs as tab, idx}
        <li class:active={activeTab === idx}>
            <button onclick={handleClick(idx)}>{tab.title}</button>
        </li>
    {/each}
</ul>

<style lang="scss">
    ul {
        width: 100%;
        display: flex;
        flex-wrap: nowrap;
        &:has(li:nth-child(3)) {
            justify-content: space-between;
        }
        justify-content: space-around;
        padding-inline: 0;
        margin-bottom: 0.5rem;
        list-style: none;
    }

    button {
        display: block;
        white-space: nowrap;
        cursor: pointer;
        color: var(--fg-subtle);
        border: 1px solid transparent;
        background-color: transparent;
        /* remove default macOS styling */
        box-shadow: none;
        font-size: smaller;
    }

    li.active > button {
        color: var(--fg);
        border-bottom: 4px solid var(--border-focus);
        border-radius: 0;
    }
    button:hover {
        color: var(--fg);
    }
</style>
