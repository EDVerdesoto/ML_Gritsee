<template>
  <div class="flex h-screen bg-slate-100 text-slate-800 overflow-hidden">
    <aside class="w-64 bg-white border-r border-slate-200 flex flex-col">
      <Sidebar />
    </aside>

    <main class="flex-1 flex flex-col overflow-hidden">
      <header class="h-16 border-b border-slate-200 bg-white/50 backdrop-blur-md flex items-center justify-between px-8 z-10 sticky top-0">
        <div class="flex items-center gap-2">
          <h2 class="font-semibold text-slate-700">{{ headerTitle }}</h2>
          <template v-if="isDashboard || isHistorial">
            <span class="text-slate-400">/</span>
            <span class="text-sm text-slate-500">Semana ({{ periodoSemana }})</span>
          </template>
        </div>
        
        <div class="flex items-center gap-4">
          <!-- Select de sucursales: solo en Dashboard -->
          <template v-if="isDashboard">
            <select 
              v-model="selectedLocacion" 
              @change="updateFilters"
              class="bg-transparent text-sm font-medium text-slate-600 outline-none cursor-pointer"
            >
              <option value="">📍 Todas las sucursales</option>
              <option v-for="loc in locaciones" :key="loc" :value="loc">
                📍 {{ loc }}
              </option>
            </select>
            <div class="h-6 w-px bg-slate-300"></div>
          </template>
          
          <!-- Botón Exportar PDF: solo en Dashboard -->
          <button 
            v-if="isDashboard"
            @click="exportToPDF"
            :disabled="exportingPDF"
            class="flex items-center gap-2 bg-slate-900 text-white px-4 py-2 rounded-lg text-sm font-medium hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Download class="w-4 h-4" :class="{ 'animate-bounce': exportingPDF }" /> 
            {{ exportingPDF ? 'Generando...' : 'Exportar PDF' }}
          </button>
          
          <!-- Botón Exportar CSV: solo en Historial -->
          <button 
            v-if="isHistorial"
            @click="exportToCSV"
            :disabled="exportingCSV"
            class="flex items-center gap-2 bg-slate-900 text-white px-4 py-2 rounded-lg text-sm font-medium hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Download class="w-4 h-4" :class="{ 'animate-bounce': exportingCSV }" /> 
            {{ exportingCSV ? 'Exportando...' : 'Exportar CSV' }}
          </button>
        </div>
      </header>
      
      <div class="flex-1 overflow-y-auto">
        <router-view 
          :locacion="selectedLocacion" 
          @periodo-loaded="periodoSemana = $event" 
        />
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, provide } from 'vue';
import { useRoute } from 'vue-router';
import { Download } from 'lucide-vue-next';
import Sidebar from '../components/shared/Sidebar.vue';
import api from '../api/axios';
import { useHistoryStore } from '../stores/history';
import { useToast } from 'vue-toastification';

const route = useRoute();
const historyStore = useHistoryStore();
const toast = useToast();

// Función de exportación que será registrada por DashboardView
const exportPdfFunction = ref(null);

// Proveer función para registrar el exportador
provide('registerPdfExporter', (fn) => {
  exportPdfFunction.value = fn;
});

const locaciones = ref([]);
const selectedLocacion = ref('');
const periodoSemana = ref('Cargando...');
const exportingPDF = ref(false);
const exportingCSV = ref(false);

// Computed para detectar la ruta actual
const isDashboard = computed(() => route.path === '/');
const isHistorial = computed(() => route.path === '/historial');
const isCarga = computed(() => route.path === '/carga');

const headerTitle = computed(() => {
  if (isDashboard.value) return 'Resumen Ejecutivo';
  if (isHistorial.value) return 'Historial de Inspecciones';
  if (isCarga.value) return 'Nueva Carga de Datos';
  return 'Dashboard';
});

onMounted(async () => {
  try {
    // Obtenemos las locaciones disponibles del backend
    const response = await api.get('/api/v1/inspecciones/opciones/metadata');
    locaciones.value = (response.data.locaciones || []).slice().sort((a,b) => a.localeCompare(b));
  } catch (error) {
    console.error("Error cargando metadata:", error);
  }
});

const updateFilters = () => {
  // Al cambiar el valor, el router-view recibirá la nueva prop automáticamente
};

// Exportar CSV para historial
const exportToCSV = async () => {
  exportingCSV.value = true;
  toast.info('Generando reporte');
  
  try {
    // 1. Obtener filtros activos del store 
    const activeFilters = historyStore.filters;
    
    // 2. Construir parámetros para el backend
    const params = {
      limit: 999999 // Traer todos los registros que coincidan con los filtros
    };
    
    // Aplicar filtros solo si tienen valores
    if (activeFilters.id) params.id = activeFilters.id;
    if (activeFilters.locacion) params.locacion = activeFilters.locacion;
    if (activeFilters.estado === 'PASS') params.veredicto = 'PASS';
    if (activeFilters.estado === 'FAIL') params.veredicto = 'FAIL';
    if (activeFilters.fecha_inicio) params.fecha_inicio = activeFilters.fecha_inicio;
    if (activeFilters.fecha_fin) params.fecha_fin = activeFilters.fecha_fin;
    
    // 3. Llamar al endpoint de exportación del backend
    const response = await api.get('/api/v1/inspecciones/exportar/excel', {
      params,
      responseType: 'blob' // CRÍTICO: Para descargar archivos binarios
    });
    
    // 4. Crear URL y descargar el archivo
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    
    // Nombre descriptivo del archivo
    const dateStr = new Date().toISOString().split('T')[0];
    const locacionText = activeFilters.locacion || 'Todas';
    link.setAttribute('download', `Reporte_Gritsee_${locacionText}_${dateStr}.xlsx`);
    
    document.body.appendChild(link);
    link.click();
    link.remove();
    
    // Limpiar URL temporal
    window.URL.revokeObjectURL(url);
    
    toast.success('Reporte descargado correctamente');
    
  } catch (error) {
    console.error('Error exportando:', error);
    toast.error('Error al descargar el reporte. Por favor intenta de nuevo.');
  } finally {
    exportingCSV.value = false;
  }
};

const exportToPDF = async () => {
  exportingPDF.value = true;
  toast.info('Generando PDF');
  
  try {
    if (exportPdfFunction.value) {
      const success = await exportPdfFunction.value();
      if (success) {
        toast.success('PDF descargado correctamente');
      } else {
        toast.error('Error al generar el PDF');
      }
    } else {
      toast.error('No se puede generar el PDF en esta vista');
    }
  } catch (error) {
    console.error('Error generando PDF:', error);
    toast.error('Error al generar el PDF. Por favor intenta de nuevo.');
  } finally {
    exportingPDF.value = false;
  }
};
</script>