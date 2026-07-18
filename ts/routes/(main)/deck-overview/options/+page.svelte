<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<script lang="ts">
    import { beforeNavigate, goto } from "$app/navigation";
    import * as tr from "@generated/ftl";
    import { onMount } from "svelte";

    import DeckOptionsPage from "../../../deck-options/DeckOptionsPage.svelte";
    import { commitEditing } from "../../../deck-options/lib";
    import type { PageData } from "./$types";

    interface Props {
        data: PageData;
    }

    let { data }: Props = $props();
    let page: DeckOptionsPage;
    let allowNav = false;

    onMount(() => {
        globalThis.$deckOptions = new Promise((resolve, _reject) => {
            resolve(page);
        });
        data.state.resolveOriginalConfigs();
    });

    beforeNavigate((navigation) => {
        if (allowNav || !navigation.to) {
            return;
        }
        navigation.cancel();
        const target = navigation.to.url;
        (async () => {
            await commitEditing();
            if (
                !(await data.state.isModified()) ||
                confirm(tr.cardTemplatesDiscardChanges())
            ) {
                allowNav = true;
                goto(target);
            }
        })();
    });

    function onSaved(): void {
        allowNav = true;
        goto("/deck-overview", { invalidateAll: true });
    }
</script>

<DeckOptionsPage state={data.state} bind:this={page} {onSaved} />
