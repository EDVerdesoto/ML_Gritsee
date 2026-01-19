<template>
  <div>
    <PdfPageOne 
      :resumen="data?.resumen_general"
      :distribucion="data?.distribucion_clases"
      :horneado="data?.horneado_clases"
      :topIncidentes="data?.top_5_dias_incidentes"
      :ejemplos="allInspections" 
      :locacion="locacion"
      :periodo="periodoFinal"
    />
    
    <PdfPageTwo 
      :resumen="data?.resumen_general"
      :peores="peores"
      :ejemplos="allInspections"
      :locacion="locacion"
      :periodo="periodoFinal"
    />

    <PdfPageThree 
      :resumen="data?.resumen_general"
      :comparacion="data?.comparacion_semanal"
      :distribucion="data?.distribucion_clases"
      :mejores="mejores"
      :locacion="locacion"
      :periodo="periodoFinal"
    />
  </div>
</template>

<script setup>
import { computed } from 'vue';
import PdfPageOne from './pdf/PdfPageOne.vue';
import PdfPageTwo from './pdf/PdfPageTwo.vue';
import PdfPageThree from './pdf/PdfPageThree.vue';

const props = defineProps({
  data: Object,
  mejores: Array,
  peores: Array,
  locacion: String,
  periodo: String 
});

// Ya no necesitamos inventar nada, usamos lo que viene o un default
const periodoFinal = computed(() => {
    return props.periodo || "Semana Actual";
});

// Combinamos mejores y peores para que PdfPageOne pueda buscar ejemplos
const allInspections = computed(() => {
    return [...(props.mejores || []), ...(props.peores || [])];
});
</script>