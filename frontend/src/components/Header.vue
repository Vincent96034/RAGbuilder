<template>
    <header>
        <nav>
            <router-link to="/">Home</router-link>
            <router-link to="/about">About</router-link>
            <router-link to="/login">Login</router-link>
        </nav>
    </header>
</template>

<script>
    export default {
        name: 'Header'
    }
</script>

<style scoped>
    header {
        color: var(--text-color);
        padding: 4px;
        text-align: center;
    }
    nav {
        margin-top: 4px;
        margin-bottom: 10px;
    }
    nav a {
        margin: 0 5px;
        color: var(--text-color);
        text-decoration: none;
    }
    nav a:hover {
        color: var(--accent-color);
    }

</style>