<script setup>
import { ref, onMounted, watch, computed, inject } from 'vue';
import { Activity, Award, CheckCircle, AlertTriangle } from 'lucide-vue-next';
import KpiCard from '../components/dashboard/KpiCard.vue';
import DoughnutChart from '../components/dashboard/DoughnutChart.vue';
import BarChart from '../components/dashboard/BarChart.vue';
import PdfReportTemplate from '../components/dashboard/PdfReportTemplate.vue';
import html2canvas from 'html2canvas';
import jsPDF from 'jspdf';
import api from '../api/axios';

const props = defineProps({ locacion: String });
const emit = defineEmits(['periodo-loaded', 'export-pdf']);
const data = ref(null);
const loading = ref(true);
const mejoresInspecciones = ref([]);
const peoresInspecciones = ref([]);
const pdfTemplateRef = ref(null);
const periodoTexto = ref('Cargando...');

// Inyectar función para registrar el exportador de PDF
const registerPdfExporter = inject('registerPdfExporter', null);

const calcPct = (val, total) => total > 0 ? ((val / total) * 100).toFixed(1) : '0.0';

// Colores exactos del HTML
const distColors = {
  mala: { hex: '#64748b', tailwind: 'bg-slate-500' },
  deficiente: { hex: '#94a3b8', tailwind: 'bg-slate-400' },
  media: { hex: '#6366f1', tailwind: 'bg-indigo-500' },
  aceptable: { hex: '#14b8a6', tailwind: 'bg-teal-500' },
  correcto: { hex: '#10b981', tailwind: 'bg-emerald-500' }
};

const hornColors = {
  insuficiente: { hex: '#94a3b8', tailwind: 'bg-slate-400' },
  bajo: { hex: '#fb923c', tailwind: 'bg-orange-400' },
  correcto: { hex: '#00b579', tailwind: 'bg-emerald-500' },
  alto: { hex: '#64748b', tailwind: 'bg-slate-500' },
  excesivo: { hex: '#991b1b', tailwind: 'bg-red-800' }
};

// --- DATA COMPUTADA ---
const estadoGeneralData = computed(() => {
  if (!data.value) return null;
  const correctas = data.value.resumen_general.porcentaje_correctas;
  return {
    chart: {
      labels: ['Pizzas Correctas', 'Pizzas Incorrectas'],
      datasets: [{
        data: [correctas, 100 - correctas],
        backgroundColor: ['#00b8a2', '#516786'],
        borderWidth: 0,
        cutout: '85%'
      }]
    },
    actual: correctas,
    anterior: data.value.comparacion_semanal?.semana_anterior?.porcentaje_correctas || 0
  };
});

const distribucionData = computed(() => {
  if (!data.value) return null;
  const d = data.value.distribucion_clases;
  const total = Object.values(d).reduce((a, b) => a + b, 0);
  const items = [
    { label: 'Mala', val: d.mala, color: distColors.mala },
    { label: 'Deficiente', val: d.deficiente, color: distColors.deficiente },
    { label: 'Regular', val: d.media, color: distColors.media },
    { label: 'Aceptable', val: d.aceptable, color: distColors.aceptable },
    { label: 'Correcta', val: d.correcto, color: distColors.correcto },
  ];
  return {
    chart: {
      labels: items.map(i => i.label),
      datasets: [{
        data: items.map(i => i.val),
        backgroundColor: items.map(i => i.color.hex),
        borderWidth: 0,
        cutout: '70%'
      }]
    },
    legendItems: items.map(i => ({ ...i, pct: calcPct(i.val, total) }))
  };
});

const horneadoData = computed(() => {
  if (!data.value) return null;
  const h = data.value.horneado_clases;
  const total = Object.values(h).reduce((a, b) => a + b, 0);
  const items = [
    { label: 'Insuficiente', val: h.insuficiente, color: hornColors.insuficiente },
    { label: 'Bajo', val: h.bajo, color: hornColors.bajo },
    { label: 'Correcto', val: h.correcto, color: hornColors.correcto },
    { label: 'Alto', val: h.alto, color: hornColors.alto },
    { label: 'Excesivo', val: h.excesivo, color: hornColors.excesivo },
  ];
  return {
    chart: {
      labels: items.map(i => i.label),
      datasets: [{
        data: items.map(i => i.val),
        backgroundColor: items.map(i => i.color.hex),
        borderWidth: 0,
        cutout: '70%'
      }]
    },
    legendItems: items.map(i => ({ ...i, pct: calcPct(i.val, total) }))
  };
});

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: { legend: { display: false }, tooltip: { enabled: true }, datalabels: { display: false } }
};

const fetchDashboardData = async () => {
  loading.value = true;
  try {
    const url = props.locacion 
      ? `/api/v1/dashboard/resumen?locacion=${encodeURIComponent(props.locacion)}` 
      : '/api/v1/dashboard/resumen';
    const response = await api.get(url);
    data.value = response.data;

    // Capturar el periodo del backend
    if (response.data.periodo_semana) {
      periodoTexto.value = response.data.periodo_semana;
      emit('periodo-loaded', response.data.periodo_semana);
    }
  } catch (error) {
    console.error('Error cargando dashboard:', error);
  } finally {
    loading.value = false;
  }
};
const incidentesBarData = computed(() => {
  if (!data.value || !data.value.top_5_dias_incidentes) return null;

  const rawData = data.value.top_5_dias_incidentes;

  // Función auxiliar para formatear fecha 
  const formatDate = (isoString) => {
    const d = new Date(isoString);
    return d.toLocaleDateString('es-ES', { day: '2-digit', month: 'short' });
  };

  return {

    labels: rawData.map(item => [
      formatDate(item.fecha), 
      item.hora_critica !== null ? `(${item.hora_critica}:00)` : ''
    ]),
    datasets: [{
      label: 'Incidentes',
      data: rawData.map(item => item.total_incidentes),
      backgroundColor: '#f59e0b', 
      borderRadius: 4,            
      barThickness: 24,           
      hoverBackgroundColor: '#d97706'
    }]
  };
});

const barOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: { 
    legend: { display: false }, 
    tooltip: { 
      backgroundColor: '#1e293b',
      padding: 12,
      cornerRadius: 8,
      displayColors: false 
    }
  },
  scales: {
    y: { 
      beginAtZero: true, 
      grid: { color: 'rgba(148, 163, 184, 0.1)' }, 
      border: { display: false } 
    },
    x: { 
      grid: { display: false }, 
      border: { display: false }, 
      ticks: { font: { size: 10 } } 
    }
  }
};

//para lista de defectos

const defectosList = computed(() => {
  if (!data.value) return [];
  
  const g = data.value.resumen_general;
  const total = g.total_muestras || 1; 
  const prev = data.value.comparacion_semanal?.semana_anterior || {};

  const getPct = (val) => ((val / total) * 100);
  
  const getPrevPct = (key) => {
    if (!prev.total_muestras) return null;
    return ((prev[key] / prev.total_muestras) * 100);
  };

  return [
    {
      label: 'Exceso de Grasa',
      pct: getPct(g.pizzas_con_grasa),
      prevPct: getPrevPct('pizzas_con_grasa'),
      color: 'bg-indigo-500', // Color exacto imagen
    },
    {
      label: 'Bordes Sucios',
      pct: getPct(g.pizzas_bordes_sucios),
      prevPct: getPrevPct('pizzas_bordes_sucios'),
      color: 'bg-indigo-400', 
    },
    {
      label: 'Burbujas',
      pct: getPct(g.pizzas_con_burbujas),
      prevPct: getPrevPct('pizzas_con_burbujas'),
      color: 'bg-teal-400', 
    },
    {
      label: 'Distribución Mala',
      pct: getPct(data.value.distribucion_clases.mala),
      prevPct: null, 
      color: 'bg-slate-500',
    },
    {
      label: 'Distribución Deficiente',
      pct: getPct(data.value.distribucion_clases.deficiente),
      prevPct: null,
      color: 'bg-slate-400',
    }
  ];
});

// TABLA DE INSPECCIONES - Top 10 mejores y peores desde el backend
const fetchInspections = async () => {
  try {
    const url = props.locacion 
      ? `/api/v1/dashboard/top-inspecciones?top=10&locacion=${encodeURIComponent(props.locacion)}` 
      : '/api/v1/dashboard/top-inspecciones?top=10';
      
    const response = await api.get(url);
    
    // Backend devuelve { mejores: [...], peores: [...] }
    mejoresInspecciones.value = response.data?.mejores || [];
    peoresInspecciones.value = response.data?.peores || [];
  } catch (error) {
    console.error("Error cargando tabla:", error);
    mejoresInspecciones.value = [];
    peoresInspecciones.value = [];
  }
};

// Helper para color del score en la tabla
const getScoreColor = (score) => {
  if (score >= 80) return 'text-emerald-600';
  if (score >= 60) return 'text-amber-600';
  return 'text-red-500';
};

const allInspections = computed(() => {
  return [...mejoresInspecciones.value, ...peoresInspecciones.value];
});

// Función para exportar PDF usando el template oculto
const exportToPDF = async () => {
  if (!pdfTemplateRef.value || !data.value) {
    console.error('Template PDF o datos no disponibles');
    return false;
  }

  try {
    const element = pdfTemplateRef.value.$el;
    
    if (!element) {
      console.error('No se encontró el elemento del template');
      return false;
    }

    // Obtener todas las páginas del template
    const pages = element.querySelectorAll(':scope > div');
    
    if (pages.length === 0) {
      console.error('No se encontraron páginas en el template');
      return false;
    }

    const pdf = new jsPDF('p', 'mm', 'a4');
    const imgWidth = 210;
    const pageHeight = 297;

    for (let i = 0; i < pages.length; i++) {
      const page = pages[i];
      
      // Recolectar links antes de capturar
      const links = [];
      page.querySelectorAll('a[href]').forEach(link => {
        const rect = link.getBoundingClientRect();
        const pageRect = page.getBoundingClientRect();
        links.push({
          href: link.href,
          x: rect.left - pageRect.left,
          y: rect.top - pageRect.top,
          width: rect.width,
          height: rect.height
        });
      });

      // Capturar cada página individualmente
      const canvas = await html2canvas(page, {
        scale: 2,
        useCORS: true,
        allowTaint: true,
        backgroundColor: '#ffffff',
        width: 794,
        height: 1123,
        windowWidth: 794,
        logging: false,
        onclone: (clonedDoc) => {
          // Forzar que los elementos estén completamente renderizados
          const clonedPage = clonedDoc.body.querySelector(':scope > div');
          if (clonedPage) {
            clonedPage.style.position = 'relative';
            clonedPage.style.transform = 'none';
          }
        }
      });

      // Agregar nueva página si no es la primera
      if (i > 0) {
        pdf.addPage();
      }

      // Agregar imagen de la página
      pdf.addImage(canvas.toDataURL('image/png'), 'PNG', 0, 0, imgWidth, pageHeight);

      // Agregar links como anotaciones PDF
      const scaleX = imgWidth / 794;
      const scaleY = pageHeight / 1123;
      
      links.forEach(link => {
        if (link.href && link.href !== '#' && !link.href.endsWith('#')) {
          const x = link.x * scaleX;
          const y = link.y * scaleY;
          const w = link.width * scaleX;
          const h = link.height * scaleY;
          
          // Agregar link clickeable al PDF
          pdf.link(x, y, w, h, { url: link.href });
        }
      });
    }

    // Generar nombre de archivo
    const fecha = new Date().toISOString().split('T')[0];
    const locacionTexto = props.locacion || 'Todas';
    const fileName = `Dashboard_Gritsee_${locacionTexto}_${fecha}.pdf`;
    
    pdf.save(fileName);
    
    return true;
  } catch (error) {
    console.error('Error generando PDF:', error);
    return false;
  }
};

// Exponer la función para que MainLayout pueda llamarla
defineExpose({ exportToPDF });

onMounted(() => {
  fetchDashboardData();
  fetchInspections();
  
  // Registrar la función de exportación en MainLayout
  if (registerPdfExporter) {
    registerPdfExporter(exportToPDF);
  }
});
watch(() => props.locacion, () => {
  fetchDashboardData();
  fetchInspections();
});
</script>

<template>
  <div>
    <!-- Componente oculto para generar PDF (solo se renderiza cuando hay datos) -->
    <div v-if="data" style=" position: absolute; left:-99999px; top: 0; width: 210mm;">
        <PdfReportTemplate 
            ref="pdfTemplateRef"
            :data="data"
            :mejores="mejoresInspecciones"
            :peores="peoresInspecciones"
            :locacion="props.locacion"
            :periodo="periodoTexto" 
        />
    </div>

    <!-- Dashboard visible -->
    <div v-if="loading" class="flex flex-col justify-center items-center h-96">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-orange-500"></div>
      <p class="text-slate-400 text-sm mt-4">Cargando métricas...</p>
    </div>

    <div v-else class="space-y-8 p-8 pb-20">
    
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
      <KpiCard 
    
        title="Muestras Totales" 
        :value="data.resumen_general.total_muestras" 
        :icon="Activity"
        iconColor="text-blue-600" iconBg="bg-blue-100"
        :trendValue="data.comparacion_semanal?.semana_anterior ? Number(((data.resumen_general.total_muestras - data.comparacion_semanal.semana_anterior.total_muestras)/data.comparacion_semanal.semana_anterior.total_muestras*100).toFixed(0)) : null" 
      />
      <KpiCard 
        title="Promedio" 
        :value="data.resumen_general.calificacion_promedio" 
        :icon="Award"
        iconColor="text-purple-600" iconBg="bg-purple-100"
        :trendValue="data.comparacion_semanal?.diferencial_promedio" trendUnit=" pts"
      />
      <KpiCard 
        title="Correctas" 
        :value="data.resumen_general.porcentaje_correctas + '%'" 
        :icon="CheckCircle"
        iconColor="text-teal-600" iconBg="bg-teal-100"
        :trendValue="data.comparacion_semanal?.diferencial_correctas"
      />
      <KpiCard 
        title="Incidentes" 
        :value="data.resumen_general.pizzas_incorrectas" 
        :icon="AlertTriangle"
        iconColor="text-orange-600" iconBg="bg-orange-100"
        :trendValue="data.comparacion_semanal?.semana_anterior ? data.resumen_general.pizzas_incorrectas - data.comparacion_semanal.semana_anterior.pizzas_incorrectas : null" 
        :isInverse="true"
        :highlight="true"
      />
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
      
      <div class="glass-card rounded-2xl p-6 flex flex-col items-center justify-center relative">
        <h4 class="text-sm font-semibold text-slate-700 mb-4 w-full text-left">Estado General</h4>
        
        <div class="h-48 w-48 relative mb-4">
          <DoughnutChart :chartData="estadoGeneralData.chart" :options="chartOptions" />
          <div class="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
             <span class="text-xl font-bold text-slate-800">{{ estadoGeneralData.actual }}%</span>
             <span class="text-[10px] text-slate-400 uppercase">Aprobado</span>
          </div>
        </div>

        <div class="w-full pt-4 border-t border-slate-200 grid grid-cols-2 gap-4 text-center">
            <div>
                <p class="text-[10px] text-slate-400 uppercase">Semana Actual</p>

                <p class="text-sm font-bold text-emerald-500">{{ estadoGeneralData.actual }}%</p>
            </div>
            <div>
                <p class="text-[10px] text-slate-400 uppercase">Semana Anterior</p>
                <p class="text-sm font-bold text-slate-500">{{ estadoGeneralData.anterior }}%</p>
            </div>
        </div>
      </div>

      <div class="glass-card rounded-2xl p-6">
        <h4 class="text-sm font-semibold text-slate-700 mb-4">Calidad de Distribución</h4>
        <div class="h-40 flex justify-center">
           <DoughnutChart :chartData="distribucionData.chart" :options="chartOptions" />
        </div>
        <div class="mt-4 grid grid-cols-2 gap-y-2 gap-x-4 text-[11px] text-slate-500">
           <div v-for="(item, index) in distribucionData.legendItems" :key="index" class="flex items-center gap-2">
              <span :class="['w-2 h-2 rounded-full flex-shrink-0', item.color.tailwind]"></span>
              <span>{{ item.label }} ({{ item.pct }}%)</span>
           </div>
        </div>
      </div>

      <div class="glass-card rounded-2xl p-6">
        <h4 class="text-sm font-semibold text-slate-700 mb-4">Calidad de Horneado</h4>
        <div class="h-40 flex justify-center">
           <DoughnutChart :chartData="horneadoData.chart" :options="chartOptions" />
        </div>
        <div class="mt-4 grid grid-cols-2 gap-y-2 gap-x-4 text-[11px] text-slate-500">
           <div v-for="(item, index) in horneadoData.legendItems" :key="index" class="flex items-center gap-2">
              <span :class="['w-2 h-2 rounded-full flex-shrink-0', item.color.tailwind]"></span>
              <span>{{ item.label }} ({{ item.pct }}%)</span>
           </div>
        </div>
      </div>
      </div> 

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
      
      <div class="bg-white rounded-2xl p-6 shadow-sm border border-gray-100 col-span-1 lg:col-span-2">
        <div class="flex justify-between items-center mb-6">
           <h4 class="text-sm font-semibold text-slate-700">Días con Mayor Incidencia</h4>
        </div>
        
        <div class="h-64 w-full">
           <BarChart v-if="incidentesBarData" :chartData="incidentesBarData" :options="barOptions" />
           
           <div v-else class="h-full flex items-center justify-center text-slate-400 text-sm">
             No hay suficientes datos de incidentes esta semana
           </div>
        </div>
        
        <p class="text-xs text-center text-slate-500 mt-4 font-medium">
          * Hora crítica mostrada en etiqueta
        </p>
      </div>

      <div class="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
        <h4 class="text-sm font-semibold text-slate-700 mb-6">Defectos Específicos y Comparativa</h4>
        
        <div class="space-y-6">
          <div v-for="(item, index) in defectosList" :key="index">
            <div class="flex justify-between text-xs mb-1">
              <span class="text-slate-500 font-medium">{{ item.label }}</span>
              <div class="text-right">
                <span class="text-slate-800 font-bold block">{{ item.pct.toFixed(1) }}%</span>
                
                <span v-if="item.prevPct !== null" :class="item.pct > item.prevPct ? 'text-red-400' : 'text-emerald-500'" class="text-[10px]">
                  vs {{ item.prevPct.toFixed(1) }}% ant.
                  <span v-if="item.pct < item.prevPct">(Mejora)</span>
                </span>
                <span v-else class="text-[10px] text-slate-400">Sin datos previos</span>
              </div>
            </div>

            <div class="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
              <div 
                class="h-2 rounded-full transition-all duration-1000 ease-out" 
                :class="item.color"
                :style="{ width: `${item.pct}%` }"
              ></div>
            </div>
          </div>
        </div>

      </div>
    
    </div>

    <!-- TABLAS DE INSPECCIONES: TOP 10 MEJORES Y PEORES -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
      
      <!-- Top 10 Mejores -->
      <div class="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
        <div class="p-6 border-b border-gray-100 flex items-center gap-3">
          <span class="w-3 h-3 rounded-full bg-emerald-500"></span>
          <h3 class="font-semibold text-slate-700">Top 10 Mejores (Score/100)</h3>
        </div>
        
        <div class="overflow-x-auto">
          <table class="w-full text-left border-collapse">
            <thead class="bg-slate-50 text-slate-500 text-[11px] uppercase tracking-wider font-semibold">
              <tr>
                <th class="p-3 pl-6">Link</th>
                <th class="p-3">Score</th>
                <th class="p-3">Fecha / Hora</th>
              </tr>
            </thead>
            
            <tbody class="text-sm divide-y divide-gray-100 font-mono">
              <tr v-for="inspection in mejoresInspecciones" :key="inspection.id" 
                  class="hover:bg-slate-50 transition-colors group">
                
                <td class="p-3 pl-6">
                  <a :href="inspection.aws_link" 
                     target="_blank" 
                     rel="noopener noreferrer"
                     class="text-indigo-500 hover:text-indigo-700 hover:underline flex items-center gap-2 truncate max-w-[180px]">
                    Ver imagen
                    <span class="opacity-0 group-hover:opacity-100 transition-opacity">↗</span>
                  </a>
                </td>

                <td class="p-3 font-bold" :class="getScoreColor(inspection.puntaje_total)">
                  {{ inspection.puntaje_total }}/100
                </td>

                <td class="p-3 text-slate-500 text-xs">
                  <span v-if="inspection.fecha_hora">
                     {{ new Date(inspection.fecha_hora).toLocaleDateString('es-ES', { day: '2-digit', month: '2-digit' }) }} 
                     {{ new Date(inspection.fecha_hora).toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit', hour12: true }) }}
                  </span>
                  <span v-else>--</span>
                </td>
              </tr>
              
              <tr v-if="mejoresInspecciones.length === 0">
                <td colspan="3" class="p-6 text-center text-slate-400 italic text-xs">
                  Cargando inspecciones...
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Top 10 Peores -->
      <div class="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
        <div class="p-6 border-b border-gray-100 flex items-center gap-3">
          <span class="w-3 h-3 rounded-full bg-red-500"></span>
          <h3 class="font-semibold text-slate-700">Top 10 Peores (Score/100)</h3>
        </div>
        
        <div class="overflow-x-auto">
          <table class="w-full text-left border-collapse">
            <thead class="bg-slate-50 text-slate-500 text-[11px] uppercase tracking-wider font-semibold">
              <tr>
                <th class="p-3 pl-6">Link</th>
                <th class="p-3">Score</th>
                <th class="p-3">Fecha / Hora</th>
              </tr>
            </thead>
            
            <tbody class="text-sm divide-y divide-gray-100 font-mono">
              <tr v-for="inspection in peoresInspecciones" :key="inspection.id" 
                  class="hover:bg-slate-50 transition-colors group">
                
                <td class="p-3 pl-6">
                  <a :href="inspection.aws_link" 
                     target="_blank" 
                     rel="noopener noreferrer"
                     class="text-indigo-500 hover:text-indigo-700 hover:underline flex items-center gap-2 truncate max-w-[180px]">
                    Ver imagen
                    <span class="opacity-0 group-hover:opacity-100 transition-opacity">↗</span>
                  </a>
                </td>

                <td class="p-3 font-bold" :class="getScoreColor(inspection.puntaje_total)">
                  {{ inspection.puntaje_total }}/100
                </td>

                <td class="p-3 text-slate-500 text-xs">
                  <span v-if="inspection.fecha_hora">
                     {{ new Date(inspection.fecha_hora).toLocaleDateString('es-ES', { day: '2-digit', month: '2-digit' }) }} 
                     {{ new Date(inspection.fecha_hora).toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit', hour12: true }) }}
                  </span>
                  <span v-else>--</span>
                </td>
              </tr>
              
              <tr v-if="peoresInspecciones.length === 0">
                <td colspan="3" class="p-6 text-center text-slate-400 italic text-xs">
                  Cargando inspecciones...
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

    </div>

  </div>
  
  </div>
  
</template>