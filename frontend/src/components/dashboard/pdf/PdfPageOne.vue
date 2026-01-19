<template>
  <div class="bg-white text-slate-800 font-sans relative flex flex-col p-10" style="width: 794px; height: 1123px;">
    
    <PdfHeader :locacion="locacion" :periodo="periodo" />

    <div class="flex gap-8 mb-8 items-start">
      <div class="w-1/2 pt-2">
        <h3 class="text-sm font-bold text-slate-700 mb-3 border-b border-slate-200 pb-1">Resumen General</h3>
        <table class="w-full text-xs font-medium">
          <tbody class="divide-y divide-slate-100">
            <tr><td class="py-2 text-slate-500">Muestras Tomadas:</td><td class="py-2 text-right font-bold text-slate-900">{{ resumen.total_muestras }}</td></tr>
            <tr><td class="py-2 text-slate-500">Pizzas Correctas:</td><td class="py-2 text-right font-bold text-emerald-600">{{ resumen.pizzas_correctas }}</td></tr>
            <tr><td class="py-2 text-slate-500">Pizzas Incorrectas:</td><td class="py-2 text-right font-bold text-red-600">{{ resumen.pizzas_incorrectas }}</td></tr>
            <tr><td class="py-2 text-slate-500">Calificación Promedio:</td><td class="py-2 text-right font-bold text-slate-900 text-sm">{{ resumen.calificacion_promedio }}</td></tr>
            <tr><td class="py-2 text-slate-500">Día con Más incidentes:</td><td class="py-2 text-right font-bold text-orange-600">{{ diaCritico }}</td></tr>
            <tr><td class="py-2 text-slate-500">Hora Más Crítica:</td><td class="py-2 text-right font-bold text-orange-600">{{ horaCritica }}</td></tr>
          </tbody>
        </table>
      </div>

      <div class="w-1/2 flex flex-col items-center">
        <div class="h-56 w-56 relative">
          <Doughnut :data="chartGeneralData" :options="chartOptionsWithLabels" />
        </div>
        <div class="flex gap-4 mt-2 text-[10px] font-bold">
           <div class="flex items-center gap-1"><span class="w-2 h-2 rounded-full bg-[#38761D]"></span> Correctas</div>
           <div class="flex items-center gap-1"><span class="w-2 h-2 rounded-full bg-[#C00000]"></span> Incorrectas</div>
        </div>
      </div>
    </div>

    <div class="mb-6">
      <h3 class="text-sm font-bold text-slate-800 mb-4 border-b border-slate-200 pb-1">Calificaciones de Distribución de Ingredientes</h3>
      <div class="grid grid-cols-12 gap-4 items-start">
        
        <div class="col-span-5 flex flex-col items-center">
          <div class="h-56 w-56 relative">
            <Doughnut :data="chartDistribucionData" :options="chartOptionsWithLabels" />
          </div>
          <!-- Leyenda debajo del chart -->
          <div class="flex flex-wrap justify-center gap-x-3 gap-y-1 mt-2 text-[8px] font-medium">
            <div class="flex items-center gap-1"><span class="w-2 h-2 rounded-full bg-[#990000]"></span> Deficiente</div>
            <div class="flex items-center gap-1"><span class="w-2 h-2 rounded-full bg-[#FF0000]"></span> Mala</div>
            <div class="flex items-center gap-1"><span class="w-2 h-2 rounded-full bg-[#FFC000]"></span> Regular</div>
            <div class="flex items-center gap-1"><span class="w-2 h-2 rounded-full bg-[#CCFFCC]"></span> Aceptable</div>
            <div class="flex items-center gap-1"><span class="w-2 h-2 rounded-full bg-[#38761D]"></span> Correcta</div>
          </div>
        </div>

        <div class="col-span-7 flex gap-6 justify-end">
          <!-- Imagen mala con X centrada abajo -->
          <div class="flex flex-col items-center">
            <div class="w-32 h-32 bg-slate-100 rounded border border-slate-200 overflow-hidden">
              <img :src="distribucionMalaImg || '/img/placeholder_pizza.jpg'" class="w-full h-full object-cover" crossorigin="anonymous">
            </div>
            <span class="text-2xl mt-1">❌</span>
          </div>

          <!-- Imagen buena con check centrada abajo -->
          <div class="flex flex-col items-center">
            <div class="w-32 h-32 bg-slate-100 rounded border border-slate-200 overflow-hidden">
              <img :src="distribucionBuenaImg || '/img/placeholder_pizza.jpg'" class="w-full h-full object-cover" crossorigin="anonymous">
            </div>
            <span class="text-2xl mt-1">✅</span>
          </div>
        </div>
      </div>
    </div>

    <div class="mt-auto mb-10">
      <h3 class="text-sm font-bold text-slate-800 mb-4 border-b border-slate-200 pb-1">Calificaciones de Nivel de Horneado</h3>
      <div class="grid grid-cols-12 gap-4 items-start">
        
        <div class="col-span-5 flex flex-col items-center">
          <div class="h-56 w-56 relative">
            <Doughnut :data="chartHorneadoData" :options="chartOptionsWithLabels" />
          </div>
          <!-- Leyenda debajo del chart -->
          <div class="flex flex-wrap justify-center gap-x-3 gap-y-1 mt-2 text-[8px] font-medium">
            <div class="flex items-center gap-1"><span class="w-2 h-2 rounded-full bg-[#FF9900]"></span> Insuficiente</div>
            <div class="flex items-center gap-1"><span class="w-2 h-2 rounded-full bg-[#FFE599]"></span> Bajo</div>
            <div class="flex items-center gap-1"><span class="w-2 h-2 rounded-full bg-[#38761D]"></span> Correcto</div>
            <div class="flex items-center gap-1"><span class="w-2 h-2 rounded-full bg-[#FF0000]"></span> Alto</div>
            <div class="flex items-center gap-1"><span class="w-2 h-2 rounded-full bg-[#990000]"></span> Excesivo</div>
          </div>
        </div>

        <div class="col-span-7 flex gap-6 justify-end">
          <!-- Imagen mala con X centrada abajo -->
          <div class="flex flex-col items-center">
            <div class="w-32 h-32 bg-slate-100 rounded border border-slate-200 overflow-hidden">
              <img :src="horneadoMaloImg || '/img/placeholder_pizza.jpg'" class="w-full h-full object-cover" crossorigin="anonymous">
            </div>
            <span class="text-2xl mt-1">❌</span>
          </div>

          <!-- Imagen buena con check centrada abajo -->
          <div class="flex flex-col items-center">
            <div class="w-32 h-32 bg-slate-100 rounded border border-slate-200 overflow-hidden">
              <img :src="horneadoBuenoImg || '/img/placeholder_pizza.jpg'" class="w-full h-full object-cover" crossorigin="anonymous">
            </div>
            <span class="text-2xl mt-1">✅</span>
          </div>
        </div>
      </div>
    </div>

    <footer class="text-[10px] text-slate-400 font-mono text-right border-t border-slate-100 pt-2">
      Página 1 de 3
    </footer>

  </div>
</template>

<script setup>
import { computed } from 'vue';
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js';
import ChartDataLabels from 'chartjs-plugin-datalabels';
import { Doughnut } from 'vue-chartjs';
import PdfHeader from './PdfHeader.vue';

ChartJS.register(ArcElement, Tooltip, Legend, ChartDataLabels);

const props = defineProps({
  resumen: Object,      // Data de /dashboard/resumen
  distribucion: Object, // Data de distribucion_clases
  horneado: Object,     // Data de horneado_clases
  topIncidentes: Array, // Data de top_5_dias
  ejemplos: Array,      // Array completo de inspecciones (mejores + peores) para buscar fotos
  locacion: String,
  periodo: String
});

// --- LÓGICA INTELIGENTE DE FOTOS ---
// Buscamos en el array de ejemplos las pizzas que cumplan la condición
const distribucionMalaImg = computed(() => {
  const found = props.ejemplos?.find(p => ['mala', 'deficiente'].includes(p.distribucion_clase));
  return found?.aws_link;
});

const distribucionBuenaImg = computed(() => {
  const found = props.ejemplos?.find(p => ['correcta', 'aceptable'].includes(p.distribucion_clase));
  // Si no encuentra una perfecta, busca cualquiera con score > 80
  return found?.aws_link || props.ejemplos?.find(p => p.puntaje_total > 80)?.aws_link;
});

const horneadoMaloImg = computed(() => {
  const found = props.ejemplos?.find(p => ['alto', 'excesivo', 'insuficiente'].includes(p.horneado_clase));
  return found?.aws_link;
});

const horneadoBuenoImg = computed(() => {
  const found = props.ejemplos?.find(p => p.horneado_clase === 'correcto');
  return found?.aws_link || props.ejemplos?.find(p => p.puntaje_total > 80)?.aws_link;
});

// --- DATOS DUROS ---
const diaCritico = computed(() => {
  const top = props.topIncidentes?.[0];
  if(!top) return "N/A";
  const d = new Date(top.fecha);
  return `${d.getDate()}-${d.toLocaleDateString('es-ES', {month:'short'})} (${top.total_incidentes})`;
});

const horaCritica = computed(() => {
  const top = props.topIncidentes?.[0];
  return top ? `${top.hora_critica}:00 hrs (${top.total_incidentes})` : "N/A";
});

// --- CHART CONFIGS (COLORES EXACTOS) ---
const chartOptionsSimple = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: { 
    legend: { display: false }, 
    tooltip: { enabled: false },
    datalabels: { display: false }
  },
  cutout: '0%'
};

// Opciones con porcentajes visibles dentro del chart
const chartOptionsWithLabels = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: { 
    legend: { display: false }, 
    tooltip: { enabled: false },
    datalabels: {
      color: 'black',
      font: {
        weight: 'bold',
        size: 13
      },
      formatter: (value, context) => {
        const total = context.dataset.data.reduce((a, b) => a + b, 0);
        const percentage = ((value / total) * 100).toFixed(1);
        return percentage > 4 ? `${percentage}%` : ''; 
      },
    }
  },
  cutout: '0%'
};

const chartOptionsComplex = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: { 
    legend: { 
        display: true, 
        position: 'right',
        labels: { font: { size: 9 }, boxWidth: 10 } 
    } 
  }
};

const chartGeneralData = computed(() => ({
  labels: ['Incorrectas', 'Correctas'],
  datasets: [{
    data: [props.resumen.pizzas_incorrectas, props.resumen.pizzas_correctas],
    backgroundColor: ['#C00000', '#38761D'], // ROJO, VERDE (Tus colores)
    borderWidth: 0
  }]
}));

const chartDistribucionData = computed(() => ({
  labels: ['Deficiente', 'Mala', 'Regular', 'Aceptable', 'Correcta'],
  datasets: [{
    data: [
        props.distribucion.deficiente, 
        props.distribucion.mala, 
        props.distribucion.media, 
        props.distribucion.aceptable, 
        props.distribucion.correcto
    ],
    // Colores extraidos de image_a53b2f.png
    backgroundColor: ['#990000', '#FF0000', '#FFC000', '#CCFFCC', '#38761D'], 
    borderWidth: 0
  }]
}));

const chartHorneadoData = computed(() => ({
  labels: ['Insuficiente', 'Bajo', 'Correcto', 'Alto', 'Excesivo'],
  datasets: [{
    data: [
        props.horneado.insuficiente, 
        props.horneado.bajo, 
        props.horneado.correcto, 
        props.horneado.alto, 
        props.horneado.excesivo
    ],
    // Colores extraidos de image_a54230.png
    backgroundColor: ['#FF9900', '#FFE599', '#38761D', '#FF0000', '#990000'],
    borderWidth: 0
  }]
}));
</script>