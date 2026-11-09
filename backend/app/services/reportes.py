"""Exportación de reportes de asistencia a Excel y PDF.

Ejemplo de POO (herencia + polimorfismo): `GeneradorReporte` define la interfaz
y cada formato la implementa. La ruta HTTP no sabe qué formato está generando;
solo pide `GENERADORES[formato]` y llama a `.generar(reporte)`.
"""
import io
from abc import ABC, abstractmethod
from datetime import date

from fpdf import FPDF
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill

from .estadisticas import ReporteSeccion


class GeneradorReporte(ABC):
    extension: str
    tipo_mime: str

    @abstractmethod
    def generar(self, reporte: ReporteSeccion) -> bytes: ...

    def nombre_archivo(self, reporte: ReporteSeccion) -> str:
        return f"asistencia_{reporte.resumen.codigo}_{date.today():%Y%m%d}.{self.extension}"


class GeneradorExcel(GeneradorReporte):
    extension = "xlsx"
    tipo_mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    def generar(self, reporte: ReporteSeccion) -> bytes:
        r = reporte.resumen
        libro = Workbook()
        hoja = libro.active
        hoja.title = "Estudiantes"
        negrita = Font(bold=True)
        rojo = PatternFill("solid", fgColor="F8D7DA")

        hoja.append([f"Sección {r.codigo} — {r.asignatura}"])
        hoja["A1"].font = Font(bold=True, size=14)
        hoja.append([f"Docente: {r.docente or '—'}", f"Clases: {r.total_clases}",
                     f"Promedio: {r.promedio_asistencia}%"])
        hoja.append([])
        hoja.append(["Cédula", "Apellidos", "Nombres", "Asistencias", "Inasistencias", "% Asistencia"])
        for celda in hoja[4]:
            celda.font = negrita
        for e in reporte.estudiantes:
            hoja.append([e.cedula, e.apellidos, e.nombres, e.asistencias, e.inasistencias, e.porcentaje])
            if e.en_riesgo:
                for celda in hoja[hoja.max_row]:
                    celda.fill = rojo
        for col, ancho in zip("ABCDEF", (14, 24, 24, 13, 14, 13)):
            hoja.column_dimensions[col].width = ancho

        hoja2 = libro.create_sheet("Clases")
        hoja2.append(["Fecha", "Tema", "Presentes", "% Asistencia"])
        for celda in hoja2[1]:
            celda.font = negrita
        for c in reporte.clases:
            hoja2.append([c.fecha.isoformat(), c.tema, c.presentes, c.porcentaje])
        hoja2.column_dimensions["B"].width = 40

        buffer = io.BytesIO()
        libro.save(buffer)
        return buffer.getvalue()


class GeneradorPDF(GeneradorReporte):
    extension = "pdf"
    tipo_mime = "application/pdf"

    def generar(self, reporte: ReporteSeccion) -> bytes:
        r = reporte.resumen
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 15)
        pdf.cell(0, 9, f"Reporte de asistencia - Sección {r.codigo}", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 11)
        for linea in (
            f"Asignatura: {r.asignatura}",
            f"Docente: {r.docente or '-'}",
            f"Estudiantes: {r.total_estudiantes}   Clases: {r.total_clases}   "
            f"Promedio: {r.promedio_asistencia}%   En riesgo (<75%): {r.estudiantes_en_riesgo}",
            f"Generado: {date.today():%d/%m/%Y}",
        ):
            pdf.cell(0, 6, linea, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)

        anchos = (28, 52, 52, 20, 20, 18)
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_fill_color(220, 220, 220)
        for titulo, ancho in zip(("Cédula", "Apellidos", "Nombres", "Asist.", "Inasist.", "%"), anchos):
            pdf.cell(ancho, 7, titulo, border=1, fill=True)
        pdf.ln()
        pdf.set_font("Helvetica", "", 10)
        for e in reporte.estudiantes:
            pdf.set_fill_color(248, 215, 218)
            valores = (e.cedula, e.apellidos[:28], e.nombres[:28], str(e.asistencias),
                       str(e.inasistencias), f"{e.porcentaje}")
            for valor, ancho in zip(valores, anchos):
                pdf.cell(ancho, 6, valor, border=1, fill=e.en_riesgo)
            pdf.ln()
        return bytes(pdf.output())


GENERADORES: dict[str, GeneradorReporte] = {
    "excel": GeneradorExcel(),
    "pdf": GeneradorPDF(),
}
