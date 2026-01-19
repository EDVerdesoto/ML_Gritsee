import html2canvas from 'html2canvas';
import jsPDF from 'jspdf';
import { ref } from 'vue';
import { useToast } from "vue-toastification";

export function usePdfExport() {
  const isGeneratingPdf = ref(false);
  const toast = useToast();

  const generateDashboardPdf = async (elementId, title = "Reporte") => {
    isGeneratingPdf.value = true;
    toast.info("Generando Reporte, por favor espera");

    try {
      // 1. Capturar el elemento del DOM
      const element = document.getElementById(elementId);
      if (!element) throw new Error("Elemento no encontrado");

      // 2. Crear el Canvas (La "foto")
      // scale: 2 mejora la calidad (evita que se vea borroso)
      const canvas = await html2canvas(element, {
        scale: 2,
        useCORS: true, // Importante si hay imágenes externas
        logging: false
      });

      // 3. Calcular dimensiones para A4
      const imgData = canvas.toDataURL('image/png');
      const pdf = new jsPDF('p', 'mm', 'a4'); // p = portrait (vertical), mm = milímetros
      
      const pdfWidth = pdf.internal.pageSize.getWidth();
      const pdfHeight = pdf.internal.pageSize.getHeight();
      
      const imgWidth = canvas.width;
      const imgHeight = canvas.height;
      
      // Ajustar la imagen al ancho del A4
      const ratio = imgWidth / pdfWidth;
      const imgHeightInPdf = imgHeight / ratio;

      // 4. Agregar imagen al PDF
      // (x, y, ancho, alto) -> Dejamos 10mm de margen superior
      pdf.addImage(imgData, 'PNG', 0, 10, pdfWidth, imgHeightInPdf);

      // 5. Agregar Fecha y Pie de página (Opcional)
      pdf.setFontSize(10);
      pdf.text(`Generado por Gritsee AI - ${new Date().toLocaleDateString()}`, 10, pdfHeight - 10);

      // 6. Descargar
      pdf.save(`${title}_${new Date().toISOString().slice(0,10)}.pdf`);
      
      toast.success("Reporte generado correctamente");

    } catch (error) {
      console.error("Error PDF:", error);
      toast.error("Error al generar el Reporte");
    } finally {
      isGeneratingPdf.value = false;
    }
  };

  return { generateDashboardPdf, isGeneratingPdf };
}