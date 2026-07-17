<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<script lang="ts">
    import { withoutUnicodeIsolation } from "@tslib/i18n";
    import { slide } from "svelte/transition";

    import Row from "$lib/components/Row.svelte";

    interface Props {
        warning: string;
        className?: string;
    }

    let { warning, className = "alert-warning" }: Props = $props();
</script>

{#if warning}
    <Row>
        <div class="col-12 alert {className} mb-0" in:slide out:slide>
            {withoutUnicodeIsolation(warning)}
        </div>
    </Row>
{/if}
