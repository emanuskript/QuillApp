<template>
  <router-view />
</template>

<script>
export default {
  name: "App",
};
</script>

<style>
/* Full-bleed app, no default browser margins */
html, body, #app {
  height: 100%;
  margin: 0;
}
body {
  background-color: #f1f1f1; /* gray canvas behind the manuscript */
}
</style>
