<template>
  <div class="flex-1 flex flex-col relative overflow-hidden bg-slate-50 h-full">

    <div class="px-8 py-4 bg-white border-b border-slate-200 flex flex-wrap gap-4 items-end shadow-sm z-0">
      <div class="w-40">
        <label class="block text-xs font-bold text-slate-500 uppercase mb-1">Buscar ID</label>
        <div class="relative">
          <Search class="absolute left-3 top-2.5 text-slate-400 w-4 h-4" />
          <input 
            v-model="filters.id" 
            @input="debouncedSearch"
            type="text" 
            placeholder="#INSP..." 
            class="w-full pl-9 pr-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-orange-500 outline-none"
          >
        </div>
      </div>

      <div class="w-56">
        <label class="block text-xs font-bold text-slate-500 uppercase mb-1">Rango de Fechas</label>
        <div class="relative">
          <Calendar class="absolute left-3 top-2.5 text-slate-400 w-4 h-4 z-10" />
          <input 
            ref="datePickerRef"
            type="text" 
            placeholder="Seleccionar..." 
            class="w-full pl-9 pr-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-orange-500 outline-none cursor-pointer"
          >
        </div>
      </div>

      <div class="w-40">
        <label class="block text-xs font-bold text-slate-500 uppercase mb-1">Sucursal</label>
        <select 
            v-model="filters.locacion" 
            @change="applyFilters"
            class="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-orange-500 outline-none">
            <option value="">Todas</option>
            <option v-for="loc in locaciones" :key="loc" :value="loc">
              {{ loc }}
            </option>
        </select>
      </div>
      

      <div class="w-40">
        <label class="block text-xs font-bold text-slate-500 uppercase mb-1">Estado</label>
        <select v-model="filters.estado" @change="applyFilters" class="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-orange-500 outline-none">
          <option value="">Todos</option>
          <option value="FAIL">FAIL</option>
          <option value="PASS">PASS</option>
        </select>
      </div>

      <div class="w-40 ml-auto">
        <label class="block text-xs font-bold text-slate-500 uppercase mb-1">Mostrar</label>
        <select v-model="itemsPerPage" @change="changeItemsPerPage" class="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-orange-500 outline-none">
          <option :value="10">10</option>
          <option :value="25">25</option>
          <option :value="50">50</option>
          <option :value="100">100</option>
          <option :value="999999">Todos</option>
        </select>
      </div>

      <button
        @click="clearFilters" 
        v-if="hasActiveFilters"
        class="px-4 py-2 text-slate-600 text-sm font-medium rounded-lg hover:bg-slate-100 transition-colors ml-auto flex items-center gap-2"
      >
        <X class="w-4 h-4" /> Limpiar filtros
      </button>
    </div>

    <div class="flex-1 overflow-auto p-8 relative">
      <div v-if="loading" class="absolute inset-0 bg-white/50 backdrop-blur-sm flex items-center justify-center z-10">
        <Loader2 class="w-8 h-8 animate-spin text-orange-500" />
      </div>

      <div class="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
        <table class="w-full text-left border-collapse">
          <thead class="bg-slate-50 text-slate-500 text-xs uppercase font-semibold border-b border-slate-200">
            <tr>
              <th class="p-4 w-20 text-center">Img</th>
              <th 
                @click="toggleSort('id')" 
                class="p-4 cursor-pointer hover:bg-slate-100 transition-colors select-none"
              >
                <div class="flex items-center gap-1">
                  ID / Fecha
                  <ArrowUpDown v-if="sortBy !== 'id'" class="w-3 h-3 text-slate-300" />
                  <ArrowUp v-else-if="sortOrder === 'asc'" class="w-3 h-3 text-orange-500" />
                  <ArrowDown v-else class="w-3 h-3 text-orange-500" />
                </div>
              </th>
              <th 
                @click="toggleSort('locacion')" 
                class="p-4 cursor-pointer hover:bg-slate-100 transition-colors select-none"
              >
                <div class="flex items-center gap-1">
                  Sucursal
                  <ArrowUpDown v-if="sortBy !== 'locacion'" class="w-3 h-3 text-slate-300" />
                  <ArrowUp v-else-if="sortOrder === 'asc'" class="w-3 h-3 text-orange-500" />
                  <ArrowDown v-else class="w-3 h-3 text-orange-500" />
                </div>
              </th>
              <th class="p-4">Defectos Detectados</th>
              <th 
                @click="toggleSort('puntaje_total')" 
                class="p-4 text-center cursor-pointer hover:bg-slate-100 transition-colors select-none"
              >
                <div class="flex items-center justify-center gap-1">
                  Score
                  <ArrowUpDown v-if="sortBy !== 'puntaje_total'" class="w-3 h-3 text-slate-300" />
                  <ArrowUp v-else-if="sortOrder === 'asc'" class="w-3 h-3 text-orange-500" />
                  <ArrowDown v-else class="w-3 h-3 text-orange-500" />
                </div>
              </th>
              <th class="p-4 text-center">Estado</th>
              <th class="p-4 text-right">Acción</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100 text-sm">
            <tr v-for="insp in sortedInspections" :key="insp.id" class="hover:bg-slate-50 transition-colors group">
              
              <td class="p-4 text-center relative">
                <div 
                  @click="openImageModal(insp)"
                  class="w-12 h-10 rounded overflow-hidden border border-slate-200 cursor-zoom-in relative group-hover:border-orange-200 hover:ring-2 hover:ring-orange-300 transition-all"
                >
                  <img 
                    v-if="insp.aws_link" 
                    :src="insp.aws_link" 
                    class="w-full h-full object-cover"
                    @error="handleImageError"
                  >
                  <div v-else class="w-full h-full bg-slate-100 flex items-center justify-center">
                    <ImageOff class="w-4 h-4 text-slate-300" />
                  </div>
                </div>
              </td>

              <td class="p-4">
                <div class="font-mono font-bold text-slate-700">#{{ insp.id }}</div>
                <div class="text-xs text-slate-400">
                  {{ formatDate(insp.fecha_hora) }}
                </div>
              </td>

              <td class="p-4 text-slate-600">{{ insp.locacion || 'N/A' }}</td>

              <td class="p-4">
                <div class="flex gap-2 flex-wrap">
                  <span v-if="insp.bordes_sucios" class="px-2 py-0.5 rounded text-[10px] font-bold bg-red-100 text-red-600 border border-red-200">Bordes</span>
                  <span v-if="insp.tiene_burbujas" class="px-2 py-0.5 rounded text-[10px] font-bold bg-red-100 text-red-600 border border-red-200">Burbujas</span>
                  <span v-if="insp.tiene_grasa" class="px-2 py-0.5 rounded text-[10px] font-bold bg-orange-100 text-orange-600 border border-orange-200">Grasa</span>
                  <span v-if="insp.horneado_clase && insp.horneado_clase !== 'correcto'" class="px-2 py-0.5 rounded text-[10px] font-bold bg-orange-100 text-orange-600 border border-orange-200">
                    Horno {{ insp.horneado_clase }}
                  </span>
                  <span v-if="insp.distribucion_clase && insp.distribucion_clase !== 'correcto'" class="px-2 py-0.5 rounded text-[10px] font-bold bg-yellow-100 text-yellow-700 border border-yellow-200">
                    Dist. {{ insp.distribucion_clase }}
                  </span>
                  <span v-if="!hasDefects(insp)" class="text-xs text-slate-400 italic">
                    Ninguno
                  </span>
                </div>
              </td>

              <td class="p-4 text-center font-bold text-lg" :class="getScoreColor(insp.puntaje_total)">
                {{ insp.puntaje_total ?? 'N/A' }}
              </td>

              <td class="p-4 text-center">
                <span :class="['px-2 py-1 rounded-full text-xs font-bold', (insp.veredicto || '').toUpperCase() === 'PASS' ? 'bg-emerald-100 text-emerald-600' : 'bg-red-100 text-red-600']">
                  {{ (insp.veredicto || 'N/A').toUpperCase() }}
                </span>
              </td>

              <td class="p-4 text-right">
                <button @click="openEditModal(insp)" class="p-2 text-slate-400 hover:text-orange-600 hover:bg-orange-50 rounded-lg transition-colors" title="Corregir IA">
                  <Pencil class="w-4 h-4" />
                </button>
              </td>
            </tr>
            
            <tr v-if="inspections.length === 0 && !loading">
              <td colspan="7" class="p-12 text-center text-slate-400">
                No se encontraron inspecciones con estos filtros.
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="flex justify-between items-center mt-6">
        <span class="text-xs text-slate-500">Página {{ currentPage }}</span>
        <div class="flex gap-2">
          <button 
            @click="currentPage > 1 && changePage(currentPage - 1)" 
            :disabled="currentPage === 1"
            class="px-3 py-1 border border-slate-300 rounded text-xs text-slate-500 hover:bg-slate-100 disabled:opacity-50"
          >Anterior</button>
          
          <button 
            @click="changePage(currentPage + 1)"
            :disabled="!hasMorePages"
            class="px-3 py-1 border border-slate-300 rounded text-xs text-slate-500 hover:bg-slate-100 disabled:opacity-50"
          >Siguiente</button>
        </div>
      </div>
    </div>

    <!-- MODAL: Ver Imagen Grande -->
    <Teleport to="body">
      <div v-if="isImageModalOpen" class="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4" @click.self="closeImageModal">
        <div class="relative max-w-4xl max-h-[90vh]">
          <button @click="closeImageModal" class="absolute -top-10 right-0 text-white/70 hover:text-white transition-colors">
            <X class="w-8 h-8" />
          </button>
          <img 
            v-if="viewingImage" 
            :src="viewingImage.aws_link" 
            class="max-w-full max-h-[85vh] object-contain rounded-lg shadow-2xl"
          >
          <div class="absolute bottom-4 left-4 bg-black/60 text-white px-4 py-2 rounded-lg text-sm backdrop-blur-md">
            <span class="font-mono font-bold">#{{ viewingImage?.id }}</span>
            <span class="mx-2">•</span>
            <span>{{ viewingImage?.locacion }}</span>
            <span class="mx-2">•</span>
            <span :class="viewingImage?.puntaje_total >= 80 ? 'text-emerald-400' : 'text-red-400'">
              {{ viewingImage?.puntaje_total }} pts
            </span>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- MODAL: Edición de Inspección -->
    <Teleport to="body">
      <div v-if="isEditModalOpen && editingInspection" class="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-50 flex items-center justify-center px-4" @click.self="closeEditModal">
        
        <div class="bg-white w-full max-w-4xl rounded-2xl shadow-2xl overflow-hidden flex animate-in zoom-in-95 duration-200 max-h-[90vh]">
            
            <div class="w-1/2 bg-slate-900 relative flex items-center justify-center p-4">
                <img 
                  v-if="editingInspection.aws_link" 
                  :src="editingInspection.aws_link" 
                  class="max-h-[500px] w-auto object-contain rounded shadow-lg"
                >
                <div v-else class="w-64 h-48 bg-slate-800 rounded flex items-center justify-center">
                  <ImageOff class="w-12 h-12 text-slate-600" />
                </div>
                <div class="absolute bottom-4 left-4 bg-black/60 text-white px-3 py-1 rounded-full text-xs backdrop-blur-md">
                    Original ID: <span class="font-mono">#{{ editingInspection.id }}</span>
                </div>
            </div>

            <div class="w-1/2 p-6 flex flex-col overflow-y-auto">
                <div class="flex justify-between items-start mb-4">
                    <div>
                        <h3 class="text-lg font-bold text-slate-800">Corrección Humana</h3>
                        <p class="text-sm text-slate-500">Ajusta los hallazgos de la IA.</p>
                    </div>
                    <button @click="closeEditModal" class="text-slate-400 hover:text-slate-600">
                        <X class="w-6 h-6" />
                    </button>
                </div>

                <div class="space-y-3 flex-1">
                    
                    <!-- Burbujas -->
                    <div class="flex items-center justify-between p-3 bg-slate-50 rounded-lg border border-slate-100">
                        <div class="flex items-center gap-3">
                            <div class="p-2 bg-blue-100 text-blue-600 rounded-lg"><CircleDashed class="w-4 h-4" /></div>
                            <div>
                                <p class="text-sm font-bold text-slate-700">Burbujas</p>
                                <p class="text-[10px] text-slate-400">Penalización variable</p>
                            </div>
                        </div>
                        <div class="relative inline-block w-12 mr-2 align-middle select-none">
                            <input type="checkbox" v-model="form.tiene_burbujas" id="toggleBurbujas" class="peer sr-only"/>
                            <label for="toggleBurbujas" class="block overflow-hidden h-6 rounded-full bg-slate-300 cursor-pointer peer-checked:bg-red-500 peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all"></label>
                        </div>
                    </div>

                    <!-- Bordes Sucios -->
                    <div class="flex items-center justify-between p-3 bg-slate-50 rounded-lg border border-slate-100">
                        <div class="flex items-center gap-3">
                            <div class="p-2 bg-orange-100 text-orange-600 rounded-lg"><Flame class="w-4 h-4" /></div>
                            <div>
                                <p class="text-sm font-bold text-slate-700">Bordes Sucios</p>
                                <p class="text-[10px] text-slate-400">Penalización variable</p>
                            </div>
                        </div>
                        <div class="relative inline-block w-12 mr-2 align-middle select-none">
                            <input type="checkbox" v-model="form.bordes_sucios" id="toggleBordes" class="peer sr-only"/>
                            <label for="toggleBordes" class="block overflow-hidden h-6 rounded-full bg-slate-300 cursor-pointer peer-checked:bg-red-500 peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all"></label>
                        </div>
                    </div>

                    <!-- Grasa -->
                    <div class="flex items-center justify-between p-3 bg-slate-50 rounded-lg border border-slate-100">
                        <div class="flex items-center gap-3">
                            <div class="p-2 bg-yellow-100 text-yellow-600 rounded-lg"><Droplets class="w-4 h-4" /></div>
                            <div>
                                <p class="text-sm font-bold text-slate-700">Grasa Visible</p>
                                <p class="text-[10px] text-slate-400">Penalización variable</p>
                            </div>
                        </div>
                        <div class="relative inline-block w-12 mr-2 align-middle select-none">
                            <input type="checkbox" v-model="form.tiene_grasa" id="toggleGrasa" class="peer sr-only"/>
                            <label for="toggleGrasa" class="block overflow-hidden h-6 rounded-full bg-slate-300 cursor-pointer peer-checked:bg-red-500 peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all"></label>
                        </div>
                    </div>

                    <!-- Horneado -->
                    <div class="flex items-center justify-between p-3 bg-slate-50 rounded-lg border border-slate-100">
                        <div class="flex items-center gap-3">
                            <div class="p-2 bg-red-100 text-red-600 rounded-lg"><ThermometerSun class="w-4 h-4" /></div>
                            <div>
                                <p class="text-sm font-bold text-slate-700">Horneado</p>
                                <p class="text-[10px] text-slate-400">+{{ horneadoScores[form.horneado_clase] || 0 }} pts</p>
                            </div>
                        </div>
                        <select 
                          v-model="form.horneado_clase" 
                          class="px-3 py-1.5 bg-white border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-orange-500 outline-none"
                        >
                          <option value="correcto">✓ Correcto</option>
                          <option value="alto">↑ Alto</option>
                          <option value="bajo">↓ Bajo</option>
                          <option value="insuficiente">⚠ Insuficiente</option>
                          <option value="excesivo">⚠ Excesivo</option>
                        </select>
                    </div>

                    <!-- Distribución -->
                    <div class="flex items-center justify-between p-3 bg-slate-50 rounded-lg border border-slate-100">
                        <div class="flex items-center gap-3">
                            <div class="p-2 bg-purple-100 text-purple-600 rounded-lg"><LayoutGrid class="w-4 h-4" /></div>
                            <div>
                                <p class="text-sm font-bold text-slate-700">Distribución</p>
                                <p class="text-[10px] text-slate-400">+{{ distribucionScores[form.distribucion_clase] || 0 }} pts</p>
                            </div>
                        </div>
                        <select 
                          v-model="form.distribucion_clase" 
                          class="px-3 py-1.5 bg-white border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-orange-500 outline-none"
                        >
                          <option value="correcto">✓ Correcta</option>
                          <option value="aceptable">◉ Aceptable</option>
                          <option value="media">~ Media</option>
                          <option value="mala">✗ Mala</option>
                          <option value="deficiente">⚠ Deficiente</option>
                        </select>
                    </div>

                    <div class="mt-3 p-3 bg-indigo-50 border border-indigo-100 rounded-lg text-xs text-indigo-700 flex gap-2">
                        <Sparkles class="w-4 h-4 flex-shrink-0" />
                        <p>El puntaje se actualiza en tiempo real. Al guardar, se sincroniza con la base de datos.</p>
                    </div>
                </div>

                <div class="mt-4 pt-4 border-t border-slate-100 flex items-center justify-between">
                    <div>
                        <p class="text-xs text-slate-400 uppercase font-bold">Nuevo Score</p>
                        <p class="text-2xl font-bold transition-all duration-300" :class="getScoreColor(calculatedScore)">{{ calculatedScore }}</p>
                        <p class="text-[10px] mt-1" :class="calculatedScore >= 75 ? 'text-emerald-500' : 'text-red-500'">{{ calculatedScore >= 75 ? 'PASS' : 'FAIL' }}</p>
                    </div>
                    <button 
                      @click="saveChanges" 
                      :disabled="isSaving"
                      class="px-6 py-3 bg-slate-900 text-white font-bold rounded-xl shadow-lg hover:bg-slate-800 transition-colors flex items-center gap-2 disabled:opacity-70"
                    >
                      <Loader2 v-if="isSaving" class="w-4 h-4 animate-spin" />
                      <Save v-else class="w-4 h-4" />
                      {{ isSaving ? 'Guardando...' : 'Guardar Corrección' }}
                    </button>
                </div>
            </div>
        </div>
      </div>
    </Teleport>

  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue';
import { Search, Calendar, Loader2, Pencil, X, CircleDashed, Flame, Sparkles, Save, ArrowUpDown, ArrowUp, ArrowDown, ImageOff, Droplets, ThermometerSun, LayoutGrid } from 'lucide-vue-next';
import flatpickr from "flatpickr";
import { Spanish } from "flatpickr/dist/l10n/es.js";
import api from '../api/axios';
import "flatpickr/dist/flatpickr.css";
import { useToast } from "vue-toastification";
import { useHistoryStore } from '../stores/history';

// --- ESTADO ---
const inspections = ref([]);
const loading = ref(false);
const currentPage = ref(1);
const itemsPerPage = ref(10);
let searchTimeout = null;
const toast = useToast();
const historyStore = useHistoryStore();

// Ordenamiento
const sortBy = ref('id');
const sortOrder = ref('desc'); // 'asc' o 'desc'

// Filtros
const filters = ref({
  id: '',
  locacion: '',
  estado: '',
  fechas: []
});
const datePickerRef = ref(null);
const locaciones = ref([]);

// Modal Imagen
const isImageModalOpen = ref(false);
const viewingImage = ref(null);

// Modal Edición
const isEditModalOpen = ref(false);
const editingInspection = ref(null);
const isSaving = ref(false);
const form = ref({
  tiene_burbujas: false,
  bordes_sucios: false,
  tiene_grasa: false,
  horneado_clase: 'correcto',
  distribucion_clase: 'correcto'
});

// Scores por categoría (según reglas de negocio)
const horneadoScores = {
  correcto: 15,
  alto: 5,
  bajo: 5,
  insuficiente: 0,
  excesivo: 0
};

const distribucionScores = {
  correcto: 30,
  aceptable: 20,
  media: 15,
  mala: 5,
  deficiente: 0
};

// Penalizaciones por defectos
const PENALIZACION_BURBUJAS = 30;
const PENALIZACION_BORDES = 15;
const PENALIZACION_GRASA = 10;

// Valores originales de la inspección antes de editar
const originalValues = ref({
  tiene_burbujas: false,
  bordes_sucios: false,
  tiene_grasa: false,
  horneado_clase: 'correcto',
  distribucion_clase: 'correcto',
  puntaje_original: 0
});

// Cálculo del score en tiempo real
const calculatedScore = computed(() => {
  if (!editingInspection.value) return 0;
  
  // Partir del puntaje original de la inspección
  let score = originalValues.value.puntaje_original;
  
  // REVERTIR los valores originales (quitar su efecto)
  // Revertir horneado original
  score -= horneadoScores[originalValues.value.horneado_clase] || 0;
  
  // Revertir distribución original
  score -= distribucionScores[originalValues.value.distribucion_clase] || 0;
  
  // Revertir penalizaciones originales
  if (originalValues.value.tiene_burbujas) score += PENALIZACION_BURBUJAS;
  if (originalValues.value.bordes_sucios) score += PENALIZACION_BORDES;
  if (originalValues.value.tiene_grasa) score += PENALIZACION_GRASA;
  
  // APLICAR los valores nuevos del formulario
  // Sumar puntos por horneado nuevo
  score += horneadoScores[form.value.horneado_clase] || 0;
  
  // Sumar puntos por distribución nueva
  score += distribucionScores[form.value.distribucion_clase] || 0;
  
  // Restar penalizaciones nuevas
  if (form.value.tiene_burbujas) score -= PENALIZACION_BURBUJAS;
  if (form.value.bordes_sucios) score -= PENALIZACION_BORDES;
  if (form.value.tiene_grasa) score -= PENALIZACION_GRASA;
  
  return Math.max(0, Math.min(100, score));
});

// Computed para saber si hay filtros activos
const hasActiveFilters = computed(() => {
  return filters.value.id || filters.value.locacion || filters.value.estado || filters.value.fechas.length > 0;
});

// Computed para saber si hay más páginas disponibles
const hasMorePages = computed(() => {
  // Si se devolvieron menos items que el límite, no hay más páginas
  // Si itemsPerPage es 999999 (Todos), nunca hay más páginas
  if (itemsPerPage.value >= 999999) return false;
  return inspections.value.length === itemsPerPage.value;
});

// Computed para ordenar inspecciones localmente
const sortedInspections = computed(() => {
  const sorted = [...inspections.value];
  sorted.sort((a, b) => {
    let valA = a[sortBy.value];
    let valB = b[sortBy.value];
    
    // Manejar strings
    if (typeof valA === 'string') valA = valA.toLowerCase();
    if (typeof valB === 'string') valB = valB.toLowerCase();
    
    // Manejar nulls
    if (valA == null) valA = sortOrder.value === 'asc' ? Infinity : -Infinity;
    if (valB == null) valB = sortOrder.value === 'asc' ? Infinity : -Infinity;
    
    if (sortOrder.value === 'asc') {
      return valA > valB ? 1 : valA < valB ? -1 : 0;
    } else {
      return valA < valB ? 1 : valA > valB ? -1 : 0;
    }
  });
  return sorted;
});

// Toggle ordenamiento
const toggleSort = (column) => {
  if (sortBy.value === column) {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc';
  } else {
    sortBy.value = column;
    sortOrder.value = 'desc';
  }
  currentPage.value = 1;
  fetchInspections();
};

// Cambiar items por página
const changeItemsPerPage = () => {
  currentPage.value = 1;
  fetchInspections();
};

// Debounce para búsqueda por ID
const debouncedSearch = () => {
  if (searchTimeout) clearTimeout(searchTimeout);
  searchTimeout = setTimeout(() => {
    applyFilters();
  }, 400);
};

// Limpiar todos los filtros
const clearFilters = () => {
  filters.value.id = '';
  filters.value.locacion = '';
  filters.value.estado = '';
  filters.value.fechas = [];
  if (datePickerRef.value && datePickerRef.value._flatpickr) {
    datePickerRef.value._flatpickr.clear();
  }
  applyFilters();
};

// Sincronizar filtros locales con el store global (para MainLayout)
watch(filters, (newFilters) => {
  historyStore.setFilters({
    id: newFilters.id,
    locacion: newFilters.locacion,
    estado: newFilters.estado,
    fecha_inicio: newFilters.fechas[0] ? newFilters.fechas[0].toISOString().split('T')[0] : null,
    fecha_fin: newFilters.fechas[1] ? newFilters.fechas[1].toISOString().split('T')[0] : null
  });
}, { deep: true });

// --- INICIALIZACIÓN ---
onMounted(async () => {
  flatpickr(datePickerRef.value, {
    mode: "range",
    locale: Spanish,
    dateFormat: "Y-m-d",
    onChange: (selectedDates) => {
      filters.value.fechas = selectedDates;
    },
    onClose: (selectedDates) => {
      if (selectedDates.length === 2) {
        applyFilters();
      }
    }
  });
  
  // Cargar locaciones del backend
  try {
    const response = await api.get('/api/v1/inspecciones/opciones/metadata');
    locaciones.value = (response.data.locaciones || []).slice().sort((a,b) => a.localeCompare(b));
  } catch (error) {
    console.error("Error cargando metadata:", error);
  }
  
  fetchInspections();
});

// --- API ---
const fetchInspections = async () => {
  loading.value = true;
  try {
    const params = {
      skip: (currentPage.value - 1) * itemsPerPage.value,
      limit: itemsPerPage.value,
      sort_by: sortBy.value,
      sort_order: sortOrder.value
    };

    if (filters.value.id) params.id = filters.value.id;
    if (filters.value.locacion) params.locacion = filters.value.locacion;
    if (filters.value.estado === 'PASS') params.veredicto = 'PASS';
    if (filters.value.estado === 'FAIL') params.veredicto = 'FAIL';
    
    if (filters.value.fechas.length === 2) {
      params.fecha_inicio = filters.value.fechas[0].toISOString().split('T')[0];
      params.fecha_fin = filters.value.fechas[1].toISOString().split('T')[0];
    }

    const response = await api.get('/api/v1/inspecciones/', { params });
    inspections.value = Array.isArray(response.data) ? response.data : (response.data.items || []);

  } catch (error) {
    console.error("Error fetching historial:", error);
    inspections.value = [];
  } finally {
    loading.value = false;
  }
};

const applyFilters = () => {
  currentPage.value = 1;
  fetchInspections();
};

const changePage = (newPage) => {
  currentPage.value = newPage;
  fetchInspections();
};

// --- MODAL IMAGEN ---
const openImageModal = (insp) => {
  if (!insp.aws_link) return;
  viewingImage.value = insp;
  isImageModalOpen.value = true;
};

const closeImageModal = () => {
  isImageModalOpen.value = false;
  viewingImage.value = null;
};

// --- MODAL EDICIÓN ---
const openEditModal = (insp) => {
  editingInspection.value = insp;
  
  // Guardar valores originales
  originalValues.value = {
    tiene_burbujas: Boolean(insp.tiene_burbujas),
    bordes_sucios: Boolean(insp.bordes_sucios),
    tiene_grasa: Boolean(insp.tiene_grasa),
    horneado_clase: insp.horneado_clase || 'correcto',
    distribucion_clase: insp.distribucion_clase || 'correcto',
    puntaje_original: insp.puntaje_total || 0
  };
  
  // Convertir 0/1 de la BD a booleanos para el form
  form.value = {
    tiene_burbujas: Boolean(insp.tiene_burbujas),
    bordes_sucios: Boolean(insp.bordes_sucios),
    tiene_grasa: Boolean(insp.tiene_grasa),
    horneado_clase: insp.horneado_clase || 'correcto',
    distribucion_clase: insp.distribucion_clase || 'correcto'
  };
  
  isEditModalOpen.value = true;
};

const closeEditModal = () => {
  isEditModalOpen.value = false;
  editingInspection.value = null;
};

const saveChanges = async () => {
  isSaving.value = true;
  try {
    // Enviar PATCH al backend - convertir booleanos a 0/1
    const response = await api.patch(`/api/v1/inspecciones/${editingInspection.value.id}`, {
      tiene_burbujas: form.value.tiene_burbujas ? 1 : 0,
      bordes_sucios: form.value.bordes_sucios ? 1 : 0,
      tiene_grasa: form.value.tiene_grasa ? 1 : 0,
      horneado_clase: form.value.horneado_clase,
      distribucion_clase: form.value.distribucion_clase
    });

    // Actualizar la inspección en la lista con los datos que devuelve el backend
    const index = inspections.value.findIndex(i => i.id === editingInspection.value.id);
    if (index !== -1) {
      inspections.value[index] = response.data;
    }
    
    closeEditModal();
    toast.success("Inspección corregida correctamente");
  } catch (error) {
    console.error("Error guardando:", error);
    toast.error("Error al guardar los cambios")
  } finally {
    isSaving.value = false;
  }
};

// --- UTILIDADES ---
const getScoreColor = (score) => {
  if (score == null) return 'text-slate-400';
  if (score >= 80) return 'text-emerald-500';
  if (score >= 60) return 'text-yellow-500';
  return 'text-red-500';
};

const hasDefects = (insp) => {
  return Boolean(insp.bordes_sucios) || 
         Boolean(insp.tiene_burbujas) || 
         Boolean(insp.tiene_grasa) || 
         (insp.horneado_clase && insp.horneado_clase !== 'correcto') ||
         (insp.distribucion_clase && insp.distribucion_clase !== 'correcto');
};

const formatDate = (dateStr) => {
  if (!dateStr) return 'N/A';
  const date = new Date(dateStr);
  return `${date.toLocaleDateString()} - ${date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}`;
};

const handleImageError = (event) => {
  event.target.style.display = 'none';
};
</script>

<style scoped>
/* Animación para modales */
.animate-in {
  animation: fadeIn 0.2s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; transform: scale(0.95); }
  to { opacity: 1; transform: scale(1); }
}
</style>