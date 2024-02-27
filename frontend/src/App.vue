/* Run with: npm run serve */

<template>
  <Header></Header>
  <router-view />
</template>


<style>

:root {
    --background-color: #f9f9f9;
    --text-color: #2C2C2C;
    --accent-color: #0359db;
}

body {
    background-color: var(--background-color);
    color: var(--text-color);
    font-family: 'Arial', sans-serif;
    margin: 0;
    padding: 0;
}

/* Example: Use the variables */
/* .button {
    background-color: var(--primary-color);
    color: white;
} */
</style>



<script>
  import Header from '@/components/Header.vue'
  export default {
    components: {
      Header
    }
  }
</script>