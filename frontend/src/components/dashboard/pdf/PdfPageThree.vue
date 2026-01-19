<template>
  <div class="bg-white text-slate-800 font-sans relative flex flex-col p-10" style="width: 794px; height: 1123px;">
    
    <PdfHeader :locacion="locacion" :periodo="periodo" />

    <!-- Ranking: 10 Pizzas con Calificación más Alta -->
    <div class="mb-8">
      <h3 class="text-lg font-bold text-slate-800 mb-4">Ranking: 10 Pizzas con Calificación más Alta</h3>
      
      <!-- Primera fila: 4 pizzas -->
      <div class="grid grid-cols-4 gap-3 mb-3">
        <div v-for="(pizza, index) in mejoresLimitadas.slice(0, 4)" :key="index" class="flex flex-col items-center">
          <div class="w-28 h-28 bg-slate-100 rounded border border-slate-200 overflow-hidden mb-1">
            <img :src="pizza.aws_link || '/img/placeholder_pizza.jpg'" class="w-full h-full object-cover" crossorigin="anonymous">
          </div>
          <p class="text-xs text-center">
            <span class="font-bold text-emerald-600">{{ pizza.puntaje_total }}/100 </span>
            <span class="text-slate-500"> {{ formatFecha(pizza.fecha_hora) }}</span>
          </p>
          <a :href="pizza.aws_link" target="_blank" class="text-[10px] text-blue-600 hover:underline">(Link)</a>
        </div>
      </div>

      <!-- Segunda fila: 4 pizzas -->
      <div class="grid grid-cols-4 gap-3 mb-3">
        <div v-for="(pizza, index) in mejoresLimitadas.slice(4, 8)" :key="index + 4" class="flex flex-col items-center">
          <div class="w-28 h-28 bg-slate-100 rounded border border-slate-200 overflow-hidden mb-1">
            <img :src="pizza.aws_link || '/img/placeholder_pizza.jpg'" class="w-full h-full object-cover" crossorigin="anonymous">
          </div>
          <p class="text-xs text-center">
            <span class="font-bold text-emerald-600">{{ pizza.puntaje_total }}/100 </span>
            <span class="text-slate-500"> {{ formatFecha(pizza.fecha_hora) }}</span>
          </p>
          <a :href="pizza.aws_link" target="_blank" class="text-[10px] text-blue-600 hover:underline">(Link)</a>
        </div>
      </div>

      <!-- Tercera fila: 2 pizzas centradas -->
      <div class="flex justify-center gap-3">
        <div v-for="(pizza, index) in mejoresLimitadas.slice(8, 10)" :key="index + 8" class="flex flex-col items-center">
          <div class="w-28 h-28 bg-slate-100 rounded border border-slate-200 overflow-hidden mb-1">
            <img :src="pizza.aws_link || '/img/placeholder_pizza.jpg'" class="w-full h-full object-cover" crossorigin="anonymous">
          </div>
          <p class="text-xs text-center">
            <span class="font-bold text-emerald-600">{{ pizza.puntaje_total }}/100 </span>
            <span class="text-slate-500"> {{ formatFecha(pizza.fecha_hora) }}</span>
          </p>
          <a :href="pizza.aws_link" target="_blank" class="text-[10px] text-blue-600 hover:underline">(Link)</a>
        </div>
      </div>
    </div>

    <!-- Resumen Comparativo -->
    <div class="mb-8">
      <h3 class="text-lg font-bold mb-4">Resumen Comparativo</h3>
      
      <table class="w-full text-sm border-collapse">
        <thead>
          <tr class="border-b-2 border-slate-300">
            <th class="text-left py-2 px-3 font-semibold text-slate-700"></th>
            <th class="text-center py-2 px-3 font-semibold text-slate-700">Semana Actual</th>
            <th class="text-center py-2 px-3 font-semibold text-slate-700">Semana Anterior</th>
            <th class="text-center py-2 px-3 font-semibold text-slate-700">Diferencial</th>
          </tr>
        </thead>
        <tbody>
          <tr class="border-b border-slate-200">
            <td class="py-2 px-3 font-semibold text-slate-700">Pizzas Correctas</td>
            <td class="py-2 px-3 text-center">{{ formatPct(resumen?.porcentaje_correctas) }}%</td>
            <td class="py-2 px-3 text-center">{{ formatPct(comparacion?.semana_anterior?.porcentaje_correctas) }}%</td>
            <td class="py-2 px-3 text-center" :class="getDiffColor(comparacion?.diferencial_correctas)">
              {{ formatDiff(comparacion?.diferencial_correctas) }}%
            </td>
          </tr>
          <tr class="border-b border-slate-200">
            <td class="py-2 px-3 font-semibold text-slate-700">Calificación Promedio</td>
            <td class="py-2 px-3 text-center">{{ resumen?.calificacion_promedio || 0 }}</td>
            <td class="py-2 px-3 text-center">{{ comparacion?.semana_anterior?.calificacion_promedio || 0 }}</td>
            <td class="py-2 px-3 text-center" :class="getDiffColor(comparacion?.diferencial_promedio)">
              {{ formatDiff(comparacion?.diferencial_promedio) }}
            </td>
          </tr>
          <tr class="border-b border-slate-200">
            <td class="py-2 px-3 font-semibold text-slate-700">Pizzas con Burbuja</td>
            <td class="py-2 px-3 text-center">{{ calcPct(resumen?.pizzas_con_burbujas) }}%</td>
            <td class="py-2 px-3 text-center">{{ calcPctAnterior(comparacion?.semana_anterior?.pizzas_con_burbujas, comparacion?.semana_anterior?.total_muestras) }}%</td>
            <td class="py-2 px-3 text-center" :class="getDiffColorInverse(calcDiffPct(resumen?.pizzas_con_burbujas, comparacion?.semana_anterior?.pizzas_con_burbujas, comparacion?.semana_anterior?.total_muestras))">
              {{ formatDiff(calcDiffPct(resumen?.pizzas_con_burbujas, comparacion?.semana_anterior?.pizzas_con_burbujas, comparacion?.semana_anterior?.total_muestras)) }}%
            </td>
          </tr>
          <tr class="border-b border-slate-200">
            <td class="py-2 px-3 font-semibold text-slate-700">Distribución Deficiente</td>
            <td class="py-2 px-3 text-center">{{ calcPctDist(distribucion?.deficiente) }}%</td>
            <td class="py-2 px-3 text-center">{{ calcPctAnterior(comparacion?.semana_anterior_distribucion?.deficiente, comparacion?.semana_anterior?.total_muestras) }}%</td>
            <td class="py-2 px-3 text-center" :class="getDiffColorInverse(calcDiffPctDist(distribucion?.deficiente, comparacion?.semana_anterior_distribucion?.deficiente, comparacion?.semana_anterior?.total_muestras))">
              {{ formatDiff(calcDiffPctDist(distribucion?.deficiente, comparacion?.semana_anterior_distribucion?.deficiente, comparacion?.semana_anterior?.total_muestras)) }}%
            </td>
          </tr>
          <tr class="border-b border-slate-200">
            <td class="py-2 px-3 font-semibold text-slate-700">Distribución Mala</td>
            <td class="py-2 px-3 text-center">{{ calcPctDist(distribucion?.mala) }}%</td>
            <td class="py-2 px-3 text-center">{{ calcPctAnterior(comparacion?.semana_anterior_distribucion?.mala, comparacion?.semana_anterior?.total_muestras) }}%</td>
            <td class="py-2 px-3 text-center" :class="getDiffColorInverse(calcDiffPctDist(distribucion?.mala, comparacion?.semana_anterior_distribucion?.mala, comparacion?.semana_anterior?.total_muestras))">
              {{ formatDiff(calcDiffPctDist(distribucion?.mala, comparacion?.semana_anterior_distribucion?.mala, comparacion?.semana_anterior?.total_muestras)) }}%
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Link final -->
    <div class="mt-auto mb-6">
      <p class="text-base text-slate-700">
        <span class="font-semibold">Imágenes y Calificaciones Completas:</span>
        <a href="#" target="_blank" class="text-blue-600 hover:underline ml-1">Aquí</a>
      </p>
    </div>

    <footer class="text-[10px] text-slate-400 font-mono text-right border-t border-slate-100 pt-2">
      Página 3 de 3
    </footer>

  </div>
</template>

<script setup>
import { computed } from 'vue';
import PdfHeader from './PdfHeader.vue';

const props = defineProps({
  resumen: Object,        // Data de resumen_general
  comparacion: Object,    // Data de comparacion_semanal
  distribucion: Object,   // Data de distribucion_clases
  mejores: Array,         // Array de las mejores inspecciones
  locacion: String,
  periodo: String
});

// Limitar a 10 mejores
const mejoresLimitadas = computed(() => {
  return (props.mejores || []).slice(0, 10);
});

// Formatear fecha: "10-Oct 6:17pm"
const formatFecha = (fechaHora) => {
  if (!fechaHora) return '';
  const d = new Date(fechaHora);
  const dia = d.getDate();
  const mes = d.toLocaleDateString('es-ES', { month: 'short' });
  const hora = d.getHours();
  const minutos = d.getMinutes().toString().padStart(2, '0');
  const ampm = hora >= 12 ? 'pm' : 'am';
  const hora12 = hora % 12 || 12;
  return `${dia}-${mes} ${hora12}:${minutos}${ampm}`;
};

// Formatear porcentaje
const formatPct = (val) => {
  return val != null ? val.toFixed(2) : '0.00';
};

// Formatear diferencial con signo
const formatDiff = (val) => {
  if (val == null || isNaN(val)) return '0.00';
  const num = parseFloat(val);
  return num > 0 ? `+${num.toFixed(2)}` : num.toFixed(2);
};

// Calcular porcentaje actual
const calcPct = (val) => {
  const total = props.resumen?.total_muestras || 1;
  return ((val || 0) / total * 100).toFixed(2);
};

// Calcular porcentaje anterior
const calcPctAnterior = (val, total) => {
  if (!total) return '0.00';
  return ((val || 0) / total * 100).toFixed(2);
};

// Calcular porcentaje de distribución
const calcPctDist = (val) => {
  const total = props.resumen?.total_muestras || 1;
  return ((val || 0) / total * 100).toFixed(2);
};

// Calcular diferencia de porcentaje
const calcDiffPct = (valActual, valAnterior, totalAnterior) => {
  const pctActual = (valActual || 0) / (props.resumen?.total_muestras || 1) * 100;
  const pctAnterior = totalAnterior ? (valAnterior || 0) / totalAnterior * 100 : 0;
  return pctActual - pctAnterior;
};

// Calcular diferencia de porcentaje para distribución
const calcDiffPctDist = (valActual, valAnterior, totalAnterior) => {
  const pctActual = (valActual || 0) / (props.resumen?.total_muestras || 1) * 100;
  const pctAnterior = totalAnterior ? (valAnterior || 0) / totalAnterior * 100 : 0;
  return pctActual - pctAnterior;
};

// Color del diferencial (positivo = verde, negativo = rojo)
const getDiffColor = (val) => {
  if (val == null) return 'text-slate-500';
  return val > 0 ? 'text-emerald-600 font-semibold' : val < 0 ? 'text-red-600 font-semibold' : 'text-slate-500';
};

// Color inverso (para métricas donde menor es mejor, como burbujas)
const getDiffColorInverse = (val) => {
  if (val == null) return 'text-slate-500';
  return val < 0 ? 'text-emerald-600 font-semibold' : val > 0 ? 'text-red-600 font-semibold' : 'text-slate-500';
};
</script>
