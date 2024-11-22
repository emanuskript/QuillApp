import { createRouter, createWebHistory } from "vue-router";
import IIIFInput from "@/components/IIIFInput.vue";
import IIIFViewer from "@/components/IIIFViewer.vue";

const routes = [
    {
        path: "/",
        name: "IIIFInput",
        component: IIIFInput,
    },
    {
        path: "/viewer/:source", // Include the param in the path
        name: "IIIFViewer",
        component: IIIFViewer,
        props: true, // Automatically pass route params as props
    },
];


const router = createRouter({
    history: createWebHistory(),
    routes,
});

export default router;
