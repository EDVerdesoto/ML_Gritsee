<template>
  <div class="relative h-full w-full">
    <Bar :data="chartData" :options="options" />
  </div>
</template>

<script setup>
import { Bar } from 'vue-chartjs';
import { Chart as ChartJS, Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale } from 'chart.js';

// Registramos los elementos necesarios para gráficos de barras
ChartJS.register(Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale);

// Configuración global de fuente para que coincida con tu "Inter"
ChartJS.defaults.font.family = "'Inter', sans-serif";
ChartJS.defaults.color = '#94a3b8';

defineProps({
  chartData: {
    type: Object,
    required: true
  },
  options: {
    type: Object,
    default: () => ({})
  }
});
</script>