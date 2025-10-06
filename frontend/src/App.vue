<template>
  <div id="app">
    <HomeView />
  </div>
</template>

<script>
import HomeView from './views/Home.vue'

export default {
  name: 'App',
  components: { HomeView }
}
</script>

<style>
html, body, #app {
  margin: 0;
  padding: 0;
  height: 100%;
}
</style>
