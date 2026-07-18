<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<script lang="ts">
    import { onMount } from "svelte";

    import { bridgeCommand } from "@tslib/bridgecommand";

    import * as reviewer from "../../../reviewer/index";
    import BottomToolbar from "./BottomToolbar.svelte";
    import { setBottom } from "./bottom";
    import "./reviewer.scss";

    function loadScript(src: string): Promise<void> {
        return new Promise((resolve) => {
            const script = document.createElement("script");
            script.src = src;
            script.addEventListener("load", () => resolve());
            script.addEventListener("error", () => resolve());
            document.head.appendChild(script);
        });
    }

    function selectedAnswerButton(): string | undefined {
        const node = document.activeElement as HTMLElement | null;
        return node?.dataset.ease;
    }

    onMount(async () => {
        Object.assign(window, reviewer);
        Object.assign(window, { __ankiSetBottom: setBottom, selectedAnswerButton });
        reviewer._blockDefaultDragDropBehavior();

        await loadScript("/_anki/js/mathjax.js");
        await loadScript("/_anki/js/vendor/mathjax/tex-chtml-full.js");

        bridgeCommand("reviewerReady");
    });
</script>

<div class="reviewer">
    <div class="reviewer-card">
        <div id="_mark" hidden>&#x2605;</div>
        <div id="_flag" hidden>&#x2691;</div>
        <div id="qa" dir="auto"></div>
    </div>
    <BottomToolbar />
</div>

<style lang="scss">
    .reviewer {
        display: flex;
        flex-direction: column;
        height: 100vh;
        width: 100%;
    }

    .reviewer-card {
        flex: 1 1 auto;
        min-height: 0;
        overflow: auto;
    }
</style>
