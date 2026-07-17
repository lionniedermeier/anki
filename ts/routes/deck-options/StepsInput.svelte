<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<script lang="ts">
    import { stepsToString, stringToSteps } from "./steps";

    interface Props {
        value: number[];
    }

    let { value = $bindable() }: Props = $props();

    const stringValue = $derived(stepsToString(value));

    function update(this: HTMLInputElement): void {
        value = stringToSteps(this.value);
    }
</script>

<input type="text" value={stringValue} onblur={update} />

<style lang="scss">
    input {
        width: 100%;
    }
</style>
