<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<script lang="ts" generics="T extends BreadcrumbItem">
    import type { Snippet } from "svelte";

    import type { BreadcrumbItem } from "./Breadcrums";

    interface Props {
        items: T[];
        delimiter?: string;
        item?: Snippet<[T, boolean]>;
        class?: string;
    }

    let { items, delimiter = ">", item, class: className = "" }: Props = $props();
</script>

<nav class="breadcrums {className}" aria-label="breadcrumb">
    <ul>
        {#each items as entry, i (i)}
            {@const isLast = i === items.length - 1}
            <li>
                {#if item}
                    {@render item(entry, isLast)}
                {:else if entry.href && !isLast}
                    <a href={entry.href}>{entry.label}</a>
                {:else}
                    <span aria-current={isLast ? "page" : undefined}>
                        {entry.label}
                    </span>
                {/if}
            </li>
            {#if !isLast}
                <li class="separator" aria-hidden="true">{delimiter}</li>
            {/if}
        {/each}
    </ul>
</nav>

<style lang="scss">
    .breadcrums {
        ul {
            display: flex;
            flex-flow: row wrap;
            align-items: center;
            gap: 0.4rem;
            margin: 0;
            padding: 0;
            list-style: none;
        }

        li {
            display: flex;
            align-items: center;
        }

        a {
            color: var(--fg-link);
        }

        span {
            color: var(--fg);
        }

        .separator {
            color: var(--fg-subtle);
            user-select: none;
        }
    }
</style>
