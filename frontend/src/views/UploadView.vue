<template>
  <div class="flex-1 flex flex-col relative overflow-hidden bg-slate-50 h-full">

    <div class="flex-1 overflow-auto p-4 md:p-8 relative scroll-smooth" ref="scrollContainer">
      <div class="max-w-3xl mx-auto flex flex-col items-center pb-20">
        
        <div :class="['w-full transition-all duration-500 mb-8', isProcessing ? 'opacity-50 pointer-events-none' : '']">
          
          <div class="bg-white p-8 rounded-2xl border border-slate-200 shadow-sm relative z-0">
            
            <div class="mb-8 relative z-50">
              <label class="block text-sm font-semibold text-slate-700 mb-2">1. Selecciona o Escribe la Sucursal</label>
              
              <div class="relative" ref="dropdownRef">
                <div class="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                  <MapPin class="h-5 w-5 text-slate-400" />
                </div>

                <input 
                  type="text"
                  v-model="searchQuery"
                  @focus="isDropdownOpen = true"
                  @input="handleInput"
                  @keydown.enter.prevent="validateSelection"
                  placeholder="Ej: Molino, Cardenas..."
                  class="w-full pl-11 pr-10 py-3.5 bg-white border border-slate-300 rounded-xl text-slate-700 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-orange-500/20 focus:border-orange-500 transition-all shadow-sm text-sm font-medium"
                />

                <div 
                  @click="toggleDropdown"
                  class="absolute inset-y-0 right-0 pr-3 flex items-center cursor-pointer hover:text-orange-600 text-slate-400 transition-colors"
                >
                  <ChevronDown :class="['h-5 w-5 transition-transform duration-200', isDropdownOpen ? 'rotate-180' : '']" />
                </div>

                <transition 
                  enter-active-class="transition duration-100 ease-out"
                  enter-from-class="transform scale-95 opacity-0"
                  enter-to-class="transform scale-100 opacity-100"
                  leave-active-class="transition duration-75 ease-in"
                  leave-from-class="transform scale-100 opacity-100"
                  leave-to-class="transform scale-95 opacity-0"
                >
                  <ul v-if="isDropdownOpen && filteredLocations.length > 0" 
                      class="absolute w-full mt-2 bg-white border border-slate-100 rounded-xl shadow-xl max-h-60 overflow-auto z-50 py-1 text-sm">
                    
                    <li v-for="loc in filteredLocations" :key="loc"
                        @click="selectLocation(loc)"
                        class="px-4 py-3 hover:bg-orange-50 hover:text-orange-700 cursor-pointer text-slate-600 transition-colors flex items-center justify-between group">
                      <span>{{ loc }}</span>
                      <Check v-if="location === loc" class="w-4 h-4 text-orange-500" />
                    </li>
                  </ul>
                </transition>

                <div v-if="searchQuery && filteredLocations.length === 0 && isDropdownOpen" 
                     class="absolute w-full mt-2 bg-white border border-orange-200 rounded-xl shadow-lg p-3 z-50">
                    <p class="text-xs text-slate-500">
                      Presiona <span class="font-bold text-slate-700">Enter</span> para agregar "<span class="text-orange-600 font-bold">{{ searchQuery }}</span>" como nueva sucursal.
                    </p>
                </div>
              </div>
            </div>
            
            <div class="mb-8 relative z-0">
              <label class="block text-sm font-semibold text-slate-700 mb-2">2. Sube el archivo CSV de AppSheet</label>
              <div 
                @dragover.prevent="isDragging = true"
                @dragleave.prevent="isDragging = false"
                @drop.prevent="handleDrop"
                @click="triggerFileInput"
                :class="[
                  'relative border-2 border-dashed rounded-2xl p-10 text-center cursor-pointer transition-all duration-300 group',
                  isDragging ? 'border-orange-500 bg-orange-50/50 scale-[1.01]' : 'border-slate-300 hover:border-orange-400 hover:bg-slate-50/50',
                  selectedFile ? 'border-emerald-500 bg-emerald-50/30' : ''
                ]"
              >
                <input 
                  type="file" 
                  ref="fileInputRef"
                  accept=".csv,.xlsx,.xls" 
                  @change="handleFileSelect"
                  class="hidden"
                >
                
                <div v-if="!selectedFile" class="flex flex-col items-center gap-4 py-2">
                  <div class="w-14 h-14 bg-white border border-slate-100 rounded-full flex items-center justify-center shadow-sm group-hover:scale-110 transition-transform">
                     <FileSpreadsheet class="w-7 h-7 text-orange-500" />
                  </div>
                  <div>
                    <h3 class="text-base font-semibold text-slate-700 mb-1">Arrastra tu CSV aquí</h3>
                    <p class="text-sm text-slate-400">o haz clic para explorar archivos</p>
                  </div>
                </div>

                <div v-else class="flex items-center justify-center gap-4 py-2">
                  <div class="w-12 h-12 bg-emerald-100 rounded-full flex items-center justify-center">
                    <FileSpreadsheet class="w-6 h-6 text-emerald-600" />
                  </div>
                  <div class="text-left">
                    <p class="text-sm font-bold text-slate-700 truncate max-w-[200px]">{{ selectedFile.name }}</p>
                    <p class="text-xs text-slate-500 font-mono">{{ formatFileSize(selectedFile.size) }}</p>
                  </div>
                  <button 
                    @click.stop="clearFile" 
                    class="ml-2 p-2 rounded-full hover:bg-red-50 text-slate-400 hover:text-red-500 transition-colors"
                    title="Eliminar archivo"
                  >
                    <X class="w-5 h-5" />
                  </button>
                </div>
              </div>
            </div>

            <div v-if="errorMessage" class="mb-6 p-4 bg-red-50 border border-red-100 rounded-xl flex items-start gap-3 animate-in fade-in slide-in-from-top-2">
              <AlertCircle class="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
              <div class="text-sm">
                <p class="font-bold text-red-700">Error en el archivo</p>
                <p class="text-red-600">{{ errorMessage }}</p>
              </div>
            </div>

            <button 
              @click="startProcessing" 
              :disabled="!isValid || isProcessing"
              :class="[
                'w-full bg-slate-900 text-white font-bold py-4 rounded-xl transition-all flex items-center justify-center gap-3 shadow-lg hover:shadow-xl transform active:scale-[0.99]',
                isValid && !isProcessing ? 'hover:bg-slate-800' : 'opacity-50 cursor-not-allowed grayscale'
              ]"
            >
              <Loader2 v-if="isProcessing" class="w-5 h-5 animate-spin" />
              <Play v-else class="w-5 h-5" />
              <span class="text-base">{{ isProcessing ? 'Analizando Imágenes...' : (isCompleted ? 'Análisis Completado' : 'Iniciar Análisis con IA') }}</span>
            </button>

          </div>
        </div>

        <div v-if="results.length > 0" class="w-full animate-in fade-in slide-in-from-bottom-4 duration-500">
          <div class="flex items-center justify-between mb-4 sticky top-0 bg-slate-50 py-2 z-10 backdrop-blur-sm">
            <h3 class="text-xs font-bold text-slate-500 uppercase flex items-center gap-2 tracking-wider">
              <span v-if="!isCompleted" class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse shadow-[0_0_10px_rgba(16,185,129,0.5)]"></span>
              <span v-else class="w-2 h-2 rounded-full bg-slate-400"></span>
              {{ isCompleted ? 'Reporte Final' : 'Procesando en vivo' }}
            </h3>
            <span class="text-xs font-mono bg-white px-2 py-1 rounded border border-slate-200 text-slate-600">{{ results.length }} items</span>
          </div>

          <div class="space-y-4 mb-8">
            <div v-for="(item, index) in results" :key="index" class="bg-white p-5 rounded-xl border border-slate-200 shadow-sm hover:shadow-md transition-all duration-300">
              <div class="flex items-center justify-between mb-4">
                <div class="flex items-center gap-3">
                  <div :class="['w-8 h-8 rounded-lg flex items-center justify-center font-bold text-sm', item.score >= 80 ? 'bg-emerald-100 text-emerald-600' : 'bg-red-100 text-red-600']">
                    {{ item.score >= 80 ? 'OK' : 'NO' }}
                  </div>
                  <div>
                    <p class="text-sm font-bold text-slate-800">Pizza #{{ index + 1 }}</p>
                    <p class="text-[10px] text-slate-400 uppercase font-bold">{{ location }}</p>
                  </div>
                </div>
                <div class="text-right">
                  <span :class="['block text-xl font-bold font-mono leading-none', item.score >= 80 ? 'text-emerald-600' : 'text-red-500']">{{ item.score }}</span>
                  <span class="text-[10px] text-slate-400 font-medium">PUNTAJE</span>
                </div>
              </div>
              
              <div class="grid grid-cols-2 gap-2 text-xs font-mono bg-slate-50 p-3 rounded-lg border border-slate-100">
                 <div class="text-slate-500">Horneado: <span class="text-slate-700 font-semibold">{{ item.horneado }}</span></div>
                 <div class="text-slate-500">Distrib: <span class="text-slate-700 font-semibold">{{ item.dist }}</span></div>
                 <div class="text-slate-500">Burbujas: <span :class="item.burbujas === 'True' ? 'text-red-600 font-bold' : 'text-slate-400'">{{ item.burbujas }}</span></div>
                 <div class="text-slate-500">Bordes: <span :class="item.bordes === 'True' ? 'text-red-600 font-bold' : 'text-slate-400'">{{ item.bordes }}</span></div>
              </div>
            </div>
          </div>
           
           <div v-if="isCompleted" class="animate-in fade-in duration-500 pb-20">
            <router-link to="/" class="group block w-full bg-emerald-600 text-white font-bold py-4 rounded-xl hover:bg-emerald-700 transition-colors shadow-lg text-center relative overflow-hidden">
               <span class="relative z-10 flex items-center justify-center gap-2">
                 Ir al Dashboard General <Check class="w-5 h-5" />
               </span>
            </router-link>
          </div>
        </div>
      </div>
    </div>

    <Teleport to="body">
      <div v-if="showNewBranchModal" class="fixed inset-0 z-[100] flex items-center justify-center px-4">
        <div class="absolute inset-0 bg-slate-900/60 backdrop-blur-sm transition-opacity" @click="cancelNewBranch"></div>
        
        <div class="bg-white rounded-2xl shadow-2xl w-full max-w-md p-6 relative z-10 animate-in zoom-in-95 duration-200">
          <div class="w-12 h-12 bg-orange-100 rounded-full flex items-center justify-center mb-4">
            <AlertTriangle class="w-6 h-6 text-orange-600" />
          </div>
          
          <h3 class="text-lg font-bold text-slate-900 mb-2">¿Agregar nueva sucursal?</h3>
          <p class="text-slate-600 text-sm mb-6">
            La sucursal <span class="font-bold text-slate-900">"{{ pendingLocation }}"</span> no existe en nuestros registros. 
            <br><br>
            ¿Estás seguro de que deseas crearla? Esto afectará los reportes futuros.
          </p>
          
          <div class="flex gap-3">
            <button 
              @click="cancelNewBranch"
              class="flex-1 px-4 py-2.5 bg-slate-100 text-slate-700 font-semibold rounded-xl hover:bg-slate-200 transition-colors"
            >
              Cancelar
            </button>
            <button 
              @click="confirmNewBranch"
              class="flex-1 px-4 py-2.5 bg-slate-900 text-white font-bold rounded-xl hover:bg-slate-800 transition-colors"
            >
              Sí, crear sucursal
            </button>
          </div>
        </div>
      </div>
    </Teleport>

  </div>
</template>

<script setup>
import { ref, computed, nextTick, onMounted, onUnmounted } from 'vue';
import { Play, Loader2, Check, Upload, FileSpreadsheet, X, AlertCircle, MapPin, ChevronDown, AlertTriangle } from 'lucide-vue-next';
import api from '../api/axios';
import { useToast } from "vue-toastification";

// --- ESTADO ---
const location = ref('');
const searchQuery = ref('');
const locaciones = ref([]); 
const isDropdownOpen = ref(false);
const dropdownRef = ref(null);
const toast = useToast();

// Modal Estado
const showNewBranchModal = ref(false);
const pendingLocation = ref('');

// Archivo y Proceso
const selectedFile = ref(null);
const isProcessing = ref(false);
const isCompleted = ref(false);
const results = ref([]);
const scrollContainer = ref(null);
const fileInputRef = ref(null);
const isDragging = ref(false);
const errorMessage = ref('');

// --- LOGICA DE SUCURSALES (DROPDOWN + VALIDACIÓN) ---

// Filtrar locaciones basado en lo que escribe el usuario
const filteredLocations = computed(() => {
  if (!searchQuery.value) return locaciones.value;
  return locaciones.value.filter(loc => 
    loc.toLowerCase().includes(searchQuery.value.toLowerCase())
  );
});

// Cargar locaciones iniciales
onMounted(async () => {
  try {
    const response = await api.get('/api/v1/inspecciones/opciones/metadata');
    const backendLocs = response.data.locaciones || [];
    // Ordenar y asegurar unicidad
    locaciones.value = [...new Set(backendLocs)].sort((a, b) => a.localeCompare(b));
  } catch (error) {
    console.error('Error cargando locaciones:', error);
    // Fallback por si falla el API
    locaciones.value = ['Cardenas', 'Centro', 'Molino', 'Valle'];
  }
  
  // Click outside para cerrar el dropdown manualmente (sin librería externa)
  document.addEventListener('click', handleClickOutside);
});

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside);
});

function handleClickOutside(event) {
  if (dropdownRef.value && !dropdownRef.value.contains(event.target)) {
    // Si hace click fuera, validamos lo que haya escrito
    if (isDropdownOpen.value) {
        validateSelection();
    }
    isDropdownOpen.value = false;
  }
}

const toggleDropdown = () => {
  isDropdownOpen.value = !isDropdownOpen.value;
};

const handleInput = () => {
  isDropdownOpen.value = true;
  location.value = ''; // Resetear selección real hasta que confirme
};

const selectLocation = (loc) => {
  location.value = loc;
  searchQuery.value = loc;
  isDropdownOpen.value = false;
};

// VALIDACIÓN DE NUEVA SUCURSAL
const validateSelection = () => {
  const query = searchQuery.value.trim();
  if (!query) return;

  // Verificar si existe en la lista (case insensitive)
  const exists = locaciones.value.some(loc => loc.toLowerCase() === query.toLowerCase());

  if (exists) {
    // Si existe, lo seleccionamos formalmente (usando el case original de la lista si es posible)
    const originalName = locaciones.value.find(loc => loc.toLowerCase() === query.toLowerCase());
    selectLocation(originalName || query);
  } else {
    // NO EXISTE -> ABRIR MODAL
    pendingLocation.value = query;
    showNewBranchModal.value = true;
    isDropdownOpen.value = false;
  }
};

const confirmNewBranch = () => {
  // Agregar a la lista localmente
  locaciones.value.push(pendingLocation.value);
  locaciones.value.sort();
  
  // Seleccionar
  selectLocation(pendingLocation.value);
  
  // Cerrar modal
  showNewBranchModal.value = false;
  pendingLocation.value = '';
};

const cancelNewBranch = () => {
  // Limpiar input o revertir a la última ubicación válida
  searchQuery.value = location.value || ''; 
  showNewBranchModal.value = false;
  pendingLocation.value = '';
};


// --- LÓGICA DE ARCHIVOS Y PROCESO (IGUAL QUE ANTES) ---

const isValid = computed(() => location.value.length > 0 && selectedFile.value !== null);

const triggerFileInput = () => fileInputRef.value?.click();

const handleFileSelect = (event) => {
  const file = event.target.files[0];
  if (file) validateAndSetFile(file);
};

const handleDrop = (event) => {
  isDragging.value = false;
  const file = event.dataTransfer.files[0];
  if (file) validateAndSetFile(file);
};

const validateAndSetFile = (file) => {
  errorMessage.value = '';
  const validExtensions = ['.csv', '.xlsx', '.xls'];
  const fileExt = '.' + file.name.split('.').pop().toLowerCase();
  
  if (!validExtensions.includes(fileExt)) {
    toast.warning("Solo se permiten archivos CSV o Excel");
    return;
  }
  selectedFile.value = file;
};

const clearFile = () => {
  selectedFile.value = null;
  errorMessage.value = '';
  if (fileInputRef.value) fileInputRef.value.value = '';
};

const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

const startProcessing = async () => {
  if (!isValid.value || isProcessing.value) return;
  
  isProcessing.value = true;
  isCompleted.value = false;
  results.value = [];
  errorMessage.value = '';

  try {
    toast.info("Procesando imágenes, por favor espera...");
    const formData = new FormData();
    formData.append('file', selectedFile.value);
    formData.append('locacion', location.value);

    const response = await api.post('/api/v1/inspecciones/batch-upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });

    if (response.data && response.data.detalle) {
      const detalle = response.data.detalle;
      for (let i = 0; i < detalle.length; i++) {
        const item = detalle[i];
        results.value.push({
          horneado: item.horneado || 'N/A',
          burbujas: item.burbujas ? 'True' : 'False',
          bordes: item.bordes_sucios ? 'True' : 'False',
          grasa: item.grasa ? 'True' : 'False',
          dist: item.distribucion || 'N/A',
          score: item.puntaje || 0,
        });

        await nextTick();
        if (scrollContainer.value) {
          scrollContainer.value.scrollTo({ top: scrollContainer.value.scrollHeight, behavior: 'smooth' });
        }
        if (detalle.length > 1 && i < detalle.length - 1) await new Promise(r => setTimeout(r, 100));
      }
    }
    isCompleted.value = true;
    toast.success("¡Análisis exitoso!");
  } catch (error) {
    console.error(error);
    toast.error("Hubo un problema procesando el archivo")
  } finally {
    isProcessing.value = false;
  }
};
</script>