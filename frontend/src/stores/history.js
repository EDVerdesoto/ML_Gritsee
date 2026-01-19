import { defineStore } from 'pinia';
import { ref } from 'vue';

export const useHistoryStore = defineStore('history', () => {
  // Estado de los filtros 
  const filters = ref({
    id: '',
    locacion: '',
    estado: '', // 'PASS' o 'FAIL'
    fecha_inicio: null,
    fecha_fin: null
  });

  // Acción para actualizar filtros desde la vista
  const setFilters = (newFilters) => {
    filters.value = { ...filters.value, ...newFilters };
  };

  // Acción para limpiar todos los filtros
  const clearFilters = () => {
    filters.value = {
      id: '',
      locacion: '',
      estado: '',
      fecha_inicio: null,
      fecha_fin: null
    };
  };

  return { filters, setFilters, clearFilters };
});