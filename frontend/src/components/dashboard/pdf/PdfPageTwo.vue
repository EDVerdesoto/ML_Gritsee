<template>
  <div class="bg-white text-slate-800 font-sans relative flex flex-col p-10" style="width: 794px; height: 1123px;">
    
    <PdfHeader :locacion="locacion" :periodo="periodo" />

    <!-- Insights de Puntos Clave -->
    <div style="margin-bottom: 12px;">
      <h3 style="font-size: 18px; font-weight: 800; margin-bottom: 12px;">Insights de Puntos Clave</h3>
      
      <div style="display: flex; justify-content: space-around; width: 100%;">
        <!-- Pizzas con Burbujas -->
        <div style="text-align: center; width: 200px;">
          <p style="font-size: 14px; font-weight: 600; color: #334155; margin-bottom: 8px;">Pizzas con Burbujas:</p>
          <!-- AJUSTE PDF: margin-top del cuadro azul (aumentar = más abajo) -->
          <div style="background-color: #1A4C7C; color: white; font-size: 30px; font-weight: 700; border-radius: 8px; width: 80px; height: 48px; line-height: 48px; text-align: center; margin: 10px auto 4px auto;">
            {{ resumen?.pizzas_con_burbujas || 0 }}
          </div>
          <p style="font-size: 12px; color: #64748b; margin-bottom: 12px; height: 16px;">{{ calcPct(resumen?.pizzas_con_burbujas) }}%</p>
          <div style="width: 176px; height: 176px; background-color: #f1f5f9; border-radius: 4px; border: 1px solid #e2e8f0; overflow: hidden; margin: 0 auto;">
            <img :src="burbujasImg || '/img/placeholder_pizza.jpg'" style="width: 176px; height: 176px; object-fit: cover;" crossorigin="anonymous">
          </div>
        </div>

        <!-- Bordes Incorrectos -->
        <div style="text-align: center; width: 200px;">
          <p style="font-size: 14px; font-weight: 600; color: #334155; margin-bottom: 8px;">Bordes Incorrectos:</p>
          <!-- AJUSTE PDF: margin-top del cuadro azul (aumentar = más abajo) -->
          <div style="background-color: #1A4C7C; color: white; font-size: 30px; font-weight: 700; border-radius: 8px; width: 80px; height: 48px; line-height: 48px; text-align: center; margin: 10px auto 4px auto;">
            {{ resumen?.pizzas_bordes_sucios || 0 }}
          </div>
          <p style="font-size: 12px; color: #64748b; margin-bottom: 12px; height: 16px;">{{ calcPct(resumen?.pizzas_bordes_sucios) }}%</p>
          <div style="width: 176px; height: 176px; background-color: #f1f5f9; border-radius: 4px; border: 1px solid #e2e8f0; overflow: hidden; margin: 0 auto;">
            <img :src="bordesImg || '/img/placeholder_pizza.jpg'" style="width: 176px; height: 176px; object-fit: cover;" crossorigin="anonymous">
          </div>
        </div>

        <!-- Exceso de Grasa -->
        <div style="text-align: center; width: 200px;">
          <p style="font-size: 14px; font-weight: 600; color: #334155; margin-bottom: 8px;">Exceso de Grasa:</p>
          <!-- AJUSTE PDF: margin-top del cuadro azul (aumentar = más abajo) -->
          <div style="background-color: #1A4C7C; color: white; font-size: 30px; font-weight: 700; border-radius: 8px; width: 80px; height: 48px; line-height: 48px; text-align: center; margin: 10px auto 4px auto;">
            {{ resumen?.pizzas_con_grasa || 0 }}
          </div>
          <p style="font-size: 12px; color: #64748b; margin-bottom: 12px; height: 16px;">{{ calcPct(resumen?.pizzas_con_grasa) }}%</p>
          <div style="width: 176px; height: 176px; background-color: #f1f5f9; border-radius: 4px; border: 1px solid #e2e8f0; overflow: hidden; margin: 0 auto;">
            <img :src="grasaImg || '/img/placeholder_pizza.jpg'" style="width: 176px; height: 176px; object-fit: cover;" crossorigin="anonymous">
          </div>
        </div>
      </div>
    </div>

    <!-- Ranking: 10 Pizzas con Calificación más Baja -->
    <div class="flex-1">
      <h3 class="text-lg font-bold text-slate-800 mb-4">Ranking: 10 Pizzas con Calificación más Baja</h3>
      
      <!-- Primera fila: 4 pizzas -->
      <div class="grid grid-cols-4 gap-3 mb-3">
        <div v-for="(pizza, index) in peoresLimitadas.slice(0, 4)" :key="index" class="flex flex-col items-center">
          <div class="w-28 h-28 bg-slate-100 rounded border border-slate-200 overflow-hidden mb-1">
            <img :src="pizza.aws_link || '/img/placeholder_pizza.jpg'" class="w-full h-full object-cover" crossorigin="anonymous">
          </div>
          <p class="text-xs text-center">
            <span class="font-bold text-orange-600">{{ pizza.puntaje_total }}/100 </span>
            <span class="text-slate-500">{{ formatFecha(pizza.fecha_hora) }}</span>
          </p>
          <a :href="pizza.aws_link" target="_blank" class="text-[10px] text-blue-600 hover:underline">(Link)</a>
        </div>
      </div>

      <!-- Segunda fila: 4 pizzas -->
      <div class="grid grid-cols-4 gap-3 mb-3">
        <div v-for="(pizza, index) in peoresLimitadas.slice(4, 8)" :key="index + 4" class="flex flex-col items-center">
          <div class="w-28 h-28 bg-slate-100 rounded border border-slate-200 overflow-hidden mb-1">
            <img :src="pizza.aws_link || '/img/placeholder_pizza.jpg'" class="w-full h-full object-cover" crossorigin="anonymous">
          </div>
          <p class="text-xs text-center">
            <span class="font-bold text-orange-600">{{ pizza.puntaje_total }}/100 </span>
            <span class="text-slate-500"> {{ formatFecha(pizza.fecha_hora) }}</span>
          </p>
          <a :href="pizza.aws_link" target="_blank" class="text-[10px] text-blue-600 hover:underline">(Link)</a>
        </div>
      </div>

      <!-- Tercera fila: 2 pizzas centradas -->
      <div class="flex justify-center gap-3">
        <div v-for="(pizza, index) in peoresLimitadas.slice(8, 10)" :key="index + 8" class="flex flex-col items-center">
          <div class="w-28 h-28 bg-slate-100 rounded border border-slate-200 overflow-hidden mb-1">
            <img :src="pizza.aws_link || '/img/placeholder_pizza.jpg'" class="w-full h-full object-cover" crossorigin="anonymous">
          </div>
          <p class="text-xs text-center">
            <span class="font-bold text-orange-600">{{ pizza.puntaje_total }}/100 </span>
            <span class="text-slate-500"> {{ formatFecha(pizza.fecha_hora) }}</span>
          </p>
          <a :href="pizza.aws_link" target="_blank" class="text-[10px] text-blue-600 hover:underline">(Link)</a>
        </div>
      </div>
    </div>

    <footer class="text-[10px] text-slate-400 font-mono text-right border-t border-slate-100 pt-2">
      Página 2 de 3
    </footer>

  </div>
</template>

<script setup>
import { computed } from 'vue';
import PdfHeader from './PdfHeader.vue';

const props = defineProps({
  resumen: Object,      // Data de /dashboard/resumen -> resumen_general
  peores: Array,        // Array de las peores inspecciones
  ejemplos: Array,      // Array de inspecciones para buscar fotos representativas
  locacion: String,
  periodo: String
});

// Calcular porcentaje
const calcPct = (val) => {
  const total = props.resumen?.total_muestras || 1;
  return ((val || 0) / total * 100).toFixed(2);
};

// Limitar a 10 peores
const peoresLimitadas = computed(() => {
  return (props.peores || []).slice(0, 10);
});

// Formatear fecha: "10-Oct 6:17pm" usando fecha_hora del backend
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

// --- IMÁGENES REPRESENTATIVAS ---
// Buscar pizza con burbujas detectadas
const burbujasImg = computed(() => {
  const found = props.ejemplos?.find(p => p.burbujas === true || p.burbujas === 1);
  return found?.aws_link;
});

// Buscar pizza con bordes sucios
const bordesImg = computed(() => {
  const found = props.ejemplos?.find(p => p.bordes_sucios === true || p.bordes_sucios === 1);
  return found?.aws_link;
});

// Buscar pizza con exceso de grasa
const grasaImg = computed(() => {
  const found = props.ejemplos?.find(p => p.grasa === true || p.grasa === 1);
  return found?.aws_link;
});
</script>
