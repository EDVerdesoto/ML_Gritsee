<template>
  <div class="relative h-full w-full flex items-center justify-center">
    <Doughnut :data="chartData" :options="options" />
  </div>
</template>

<script setup>
import { Doughnut } from 'vue-chartjs';
import { Chart as ChartJS, Title, Tooltip, Legend, ArcElement, CategoryScale } from 'chart.js';
ChartJS.register(Title, Tooltip, Legend, ArcElement, CategoryScale);

defineProps({
  chartData: { type: Object, required: true },
  options: { type: Object, default: () => ({}) } 
});
</script>