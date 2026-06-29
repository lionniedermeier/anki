<script lang="ts">
    export let title: string;
</script>

<div class="config-container">
    <h4 class="title">{title}</h4>
    <div class="body">
        <slot />
    </div>
</div>

<style lang="scss">
    .config-container {
        // Grow to fill the flex column in +page.svelte; min-height: 0 lets the
        // body shrink below its content size so it can scroll instead of pushing
        // the footer off-screen.
        flex: 1;
        min-height: 0;
        display: flex;
        flex-direction: column;
    }

    .title {
        margin: 0 0 0.5rem;
        flex: none;
    }

    .body {
        flex: 1;
        min-height: 0;
        // overflow-x: hidden is required: setting only overflow-y to a
        // non-visible value makes the browser compute overflow-x to auto,
        // which would add an unwanted horizontal scrollbar.
        overflow-x: hidden;
        overflow-y: auto;
    }
</style>
