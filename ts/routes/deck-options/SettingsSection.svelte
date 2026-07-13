<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<script lang="ts">
    import type { Snippet } from "svelte";

    interface SettingsSectionProps {
        id?: string;
        class?: string;
        title: string;
        tooltip?: Snippet;
        children?: Snippet;
    }

    let {
        id = undefined,
        class: className = "",
        title,
        tooltip,
        children,
    }: SettingsSectionProps = $props();
</script>

<!-- The two custom properties are read by the Row/ConfigInput descendants of
every section for their spacing. -->
<section
    {id}
    class="settings-section {className}"
    style:--gutter-block="2px"
    style:--container-margin="0"
>
    <div class="header">
        <h2>{title}</h2>
        <div class="help-badge">
            {@render tooltip?.()}
        </div>
    </div>
    {@render children?.()}
</section>

<style lang="scss">
    .settings-section {
        width: 100%;
        padding-block: 0.5rem 1.5rem;
        word-break: break-word;
        margin-bottom: 0.75rem;
    }

    .header {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin-bottom: 0.75rem;
        padding-bottom: 0.25rem;
        border-bottom: 1px solid var(--border-subtle);
    }

    h2 {
        flex: 1 1 auto;
        min-width: 0;
        margin: 0;
        font-size: 1.6rem;
        font-weight: 600;
    }

    .help-badge {
        flex: none;
        color: var(--fg-subtle);
    }
</style>
