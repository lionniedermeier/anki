<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<script lang="ts">
    interface Props {
        title: string;
        value: number;
        buried?: string;
        buriedTooltip?: string;
        color?: string;
    }

    let { title, value, buried = "", buriedTooltip, color }: Props = $props();
</script>

<div class="stat">
    <div class="stat-value" style:color>
        {value}
        <span class="bury-count" title={buriedTooltip}>{buried}</span>
    </div>
    <span class="stat-title">{title}</span>
</div>

<style lang="scss">
    .stat {
        padding: 16px;
        background-color: rgb(236, 236, 236);
        border-radius: 8px;
        width: 120px;
    }

    .stat-title {
        display: block;
        font-size: 10px;
        margin-bottom: 8px;
        text-transform: uppercase;
    }

    .stat-value {
        font-size: 30px;
        font-weight: bold;
    }

    .bury-count {
        color: var(--fg-disabled);
        font-weight: bold;
        font-size: 16px;
        margin-inline-start: 2px;

        &:empty {
            display: none;
        }
    }
</style>
