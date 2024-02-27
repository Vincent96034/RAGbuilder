<template>
    <div id="test-item">
        <p> Item </p>
        <p> . </p>
    </div>
</template>

<script>
    export default {
        name: 'TestItem'    }
</script>

<style scoped>
    /* set color to accent */
    p {
        color: var(--text-color);
    }

    .test-item {
        margin: 10px;
        padding: 10px;
        border: 1px solid var(--accent-color);
    }
</style>