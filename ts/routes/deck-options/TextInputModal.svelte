<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<script lang="ts">
    import Modal from "$lib/components/Modal.svelte";

    interface Props {
        title: string;
        prompt: string;
        initialValue?: string;
        onOk: (text: string) => void;
        modalKey: string;
    }

    let { title, prompt, initialValue = "", onOk, modalKey }: Props = $props();

    let value = $state("");
    $effect(() => {
        value = initialValue;
    });

    let inputRef: HTMLInputElement;
    let modal: Modal | undefined = $state();

    function onOkClicked(): void {
        onOk(inputRef.value);
        value = initialValue;
    }

    function onCancelClicked(): void {
        value = initialValue;
    }

    function onShown(): void {
        inputRef.focus();
    }
</script>

<Modal bind:this={modal} {modalKey} {onOkClicked} {onShown} {onCancelClicked}>
    {#snippet header()}
        <div class="modal-header">
            <h5 class="modal-title" id="modalLabel">{title}</h5>
            <button
                type="button"
                class="btn-close"
                data-bs-dismiss="modal"
                aria-label="Close"
            ></button>
        </div>
    {/snippet}
    {#snippet body()}
        <div class="modal-body">
            <form
                onsubmit={(event) => {
                    event.preventDefault();
                    modal!.acceptHandler();
                }}
            >
                <div class="mb-3">
                    <label for="prompt-input" class="field-label">
                        {prompt}:
                    </label>
                    <input
                        id="prompt-input"
                        bind:this={inputRef}
                        type="text"
                        class="text-input"
                        bind:value
                    />
                </div>
            </form>
        </div>
    {/snippet}
    {#snippet footer()}
        <div class="modal-footer">
            <button
                type="button"
                class="btn btn-secondary"
                onclick={modal!.cancelHandler}
            >
                Cancel
            </button>
            <button
                type="button"
                class="btn btn-primary"
                onclick={modal!.acceptHandler}
            >
                OK
            </button>
        </div>
    {/snippet}
</Modal>

<style lang="scss">
    .field-label {
        display: block;
        padding-block: calc(0.375rem + 1px);
        margin-bottom: 0;
    }

    .text-input {
        width: 100%;
        -webkit-appearance: none;
        appearance: none;
        background-color: var(--canvas-inset);
        border-color: var(--border);

        &:focus {
            background-color: var(--canvas-inset);
        }
    }
</style>
