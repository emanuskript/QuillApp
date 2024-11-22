import { createApp } from "vue";
import App from "./App.vue";
import router from "./router"; // Import the router
import '@fortawesome/fontawesome-free/css/all.css';
import '@fortawesome/fontawesome-free/js/all.js';


createApp(App).use(router).mount("#app");
