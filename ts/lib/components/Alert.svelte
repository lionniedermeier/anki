<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<script lang="ts">
    import type { Snippet } from "svelte";
    import { slide } from "svelte/transition";

    interface AlertProps {
        variant?: "warning" | "danger" | "info";
        class?: string;
        children?: Snippet;
    }

    let { variant = "warning", class: className = "", children }: AlertProps = $props();
</script>

<div class="alert alert-{variant} {className}" in:slide out:slide>
    {@render children?.()}
</div>

<style lang="scss">
    .alert {
        position: relative;
        width: 100%;
        padding: 1rem;
        margin-bottom: 0;
        border: 1px solid;
        border-radius: var(--border-radius);
    }

    .alert-danger {
        color: var(--accent-danger);
        background-color: color-mix(in srgb, var(--accent-danger) 15%, var(--canvas));
        border-color: color-mix(in srgb, var(--accent-danger) 40%, var(--canvas));
    }

    .alert-warning {
        color: var(--flag-2);
        background-color: color-mix(in srgb, var(--flag-2) 15%, var(--canvas));
        border-color: color-mix(in srgb, var(--flag-2) 40%, var(--canvas));
    }

    .alert-info {
        color: var(--accent-card);
        background-color: color-mix(in srgb, var(--accent-card) 15%, var(--canvas));
        border-color: color-mix(in srgb, var(--accent-card) 40%, var(--canvas));
    }
</style>
