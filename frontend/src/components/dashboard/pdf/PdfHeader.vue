<template>
  <header style="margin-bottom: 24px;">
    <!-- Fila superior: logos y info -->
    <div style="display: flex; justify-content: space-between; align-items: flex-start; padding-bottom: 8px;">
      <div style="display: flex; align-items: center; gap: 12px;">
        <img src="/logo_lc_icon.png" style="height: 56px; width: 56px; object-fit: contain;" crossorigin="anonymous" /> 
        <div>
          <img src="/logo_lc_text.png" style="height: 28px; object-fit: contain;" crossorigin="anonymous" />
          <div style="font-size: 12px; font-weight: 700; color: #334155; line-height: 1.25; margin-top: 4px;">
            <p style="margin: 0;">Locación: <span style="color: #ea580c; text-transform: uppercase;">{{ locacion || 'General' }}</span></p>
            <p style="margin: 0;">Periodo: <span style="font-weight: 400; color: #64748b;">{{ periodo }}</span></p>
          </div>
        </div>
      </div>

      <div style="text-align: right; display: flex; flex-direction: column; align-items: flex-end;">
        <span style="font-size: 9px; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 4px;">Elaborado por</span>
        <img src="https://cdn.prod.website-files.com/630dfafcb284c6e437ab4f4a/630dfd5da3b28475ea041458_logo-color-top.svg" style="height: 28px;" crossorigin="anonymous" />
      </div>
    </div>
    
    <!-- Título abajo con borde -->
    <!-- AJUSTE PDF: margin-top para mover hacia abajo (aumentar valor = más abajo) -->
    <div style="margin-top: 18px; padding-bottom: 4px;">
      <h1 style="font-size: 20px; font-weight: 800; color: #0b5394; text-transform: uppercase; letter-spacing: 0.05em; margin: 0;">Reporte de Calidad de Pizzas</h1>
      <!-- AJUSTE PDF: margin-top de la línea (aumentar = más abajo) -->
      <div style="height: 2px; background-color: #cbd5e1; margin-top: 14px; width: 100%;"></div>
    </div>
  </header>
</template>

<script setup>
defineProps({
  locacion: String,
  periodo: String
});
</script>