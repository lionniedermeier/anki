<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<script lang="ts">
    import { buildPreviewSrcdoc } from "./card-preview";

    interface Props {
        /** Rendered card HTML (question or answer). */
        html: string;
        /** The notetype's (possibly unsaved) CSS. */
        css: string;
        /** Zero-based card template ordinal, for the `.cardN` body class. */
        ord: number;
        /** Add the night-mode classes to the preview. */
        nightMode: boolean;
        /** Add the `mobile` class to the preview's `<html>`. */
        mobile: boolean;
    }

    let { html, css, ord, nightMode, mobile }: Props = $props();

    const srcdoc = $derived(buildPreviewSrcdoc(html, css, ord, nightMode, mobile));
</script>

<!-- allow-same-origin (no allow-scripts) keeps relative media resolving against
     the page URL while template JS stays disabled. -->
<iframe
    class="card-preview"
    title="card preview"
    {srcdoc}
    sandbox="allow-same-origin"
></iframe>

<style lang="scss">
    .card-preview {
        display: block;
        width: 100%;
        height: 100%;
        border: none;
        background: var(--canvas);
    }
</style>
