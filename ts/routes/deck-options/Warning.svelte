<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<script lang="ts">
    import { withoutUnicodeIsolation } from "@tslib/i18n";

    import Alert from "$lib/components/Alert.svelte";
    import Row from "$lib/components/Row.svelte";

    interface Props {
        warning: string;
        variant?: "warning" | "danger" | "info";
        class?: string;
    }

    let { warning, variant = "warning", class: className = "" }: Props = $props();
</script>

{#if warning}
    <Row>
        <Alert {variant} class={className}>
            {withoutUnicodeIsolation(warning)}
        </Alert>
    </Row>
{/if}
