#!/usr/bin/env python3
"""
Generador de Presupuestos PDF - Electricista
Lee la lista de precios del vault y genera presupuestos profesionales en PDF.

Uso:
    python generar_presupuesto.py --cliente "Juan Pérez" --direccion "123 y 45" \
        --item "Boca completa" 5 --item "Cable 2.5mm (metro)" 50 \
        --mano_de_obra 150000 --output "presupuesto_juan.pdf"

También puede usarse interactivamente:
    python generar_presupuesto.py
"""

import argparse
import os
import sys
import json
import re
import math
from datetime import datetime, timedelta
from fpdf import FPDF

# ==================== CONFIGURACIÓN ====================
VAULT_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRECIOS_PATH = os.path.join(VAULT_PATH, "08_PRECIOS", "Lista de precios maestra.md")
OUTPUT_DIR = VAULT_PATH  # Guarda en la raíz del vault

FONT_PATH_REGULAR = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
FONT_PATH_BOLD = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
FONT_PATH_ITALIC = "/usr/share/fonts/truetype/liberation/LiberationSans-Italic.ttf"
FONT_PATH_BOLD_ITALIC = "/usr/share/fonts/truetype/liberation/LiberationSans-BoldItalic.ttf"

# Colores
AZUL_OSCURO = (15, 60, 110)
AZUL_MEDIO = (30, 120, 190)
AZUL_CLARO = (220, 237, 250)
GRIS_CLARO = (240, 240, 240)
NEGRO = (30, 30, 30)
GRIS_MEDIO = (100, 100, 100)

# ==================== LISTA DE PRECIOS ====================

def cargar_precios(ruta=PRECIOS_PATH):
    """Carga la lista de precios del vault"""
    precios = {
        "materiales": {},
        "mano_obra": {},
        "dolar_blue": 1400,
        "factores": {}
    }

    if not os.path.exists(ruta):
        print(f"⚠️ No se encontró {ruta}, se usan precios por defecto")
        return precios

    with open(ruta, "r", encoding="utf-8") as f:
        contenido = f.read()

    # Frontmatter YAML
    yaml_match = re.match(r'^---\n(.*?)\n---', contenido, re.DOTALL)
    if yaml_match:
        try:
            for line in yaml_match.group(1).split('\n'):
                if ':' in line:
                    key, val = line.split(':', 1)
                    key = key.strip()
                    val = val.strip()
                    if key == 'dolar_blue':
                        try:
                            precios["dolar_blue"] = int(val)
                        except ValueError:
                            pass
        except Exception:
            pass

    # Materiales - extraer precio_unitario::
    materiales_seccion = re.findall(r'\*\*(.+?)\*\*.*?precio_unitario::\s*(\d+)', contenido)
    for nombre, precio in materiales_seccion:
        precios["materiales"][nombre.strip().lower()] = int(precio)

    # Mano de obra - extraer precio_mo::
    mo_seccion = re.findall(r'\*\*(.+?)\*\*.*?precio_mo::\s*(\d+)', contenido)
    for nombre, precio in mo_seccion:
        precios["mano_obra"][nombre.strip().lower()] = int(precio)

    # Factores de ajuste (tabla)
    factores_seccion = re.findall(r'\|(.+?)\|\s*([\dx.]+)\s*\|', contenido)
    for factor, valor in factores_seccion:
        if "x" in valor and valor.strip() != "x1.0":
            try:
                mult = float(valor.strip().replace("x", ""))
                precios["factores"][factor.strip().lower()] = mult
            except ValueError:
                pass

    return precios


def buscar_precio(nombre, precios_dict):
    """Busca un precio por nombre (parcial)"""
    nombre = nombre.strip().lower()

    # Búsqueda exacta
    if nombre in precios_dict:
        return precios_dict[nombre]

    # Búsqueda parcial
    for key, val in precios_dict.items():
        if nombre in key or key in nombre:
            return val

    return None


# ==================== PDF ====================

class PresupuestoPDF(FPDF):
    def __init__(self):
        super().__init__('P', 'mm', 'Letter')
        self.add_font('LiberationSans', '', FONT_PATH_REGULAR)
        self.add_font('LiberationSans', 'B', FONT_PATH_BOLD)
        self.add_font('LiberationSans', 'I', FONT_PATH_ITALIC)
        self.add_font('LiberationSans', 'BI', FONT_PATH_BOLD_ITALIC)
        self.set_auto_page_break(auto=True, margin=25)

    def header(self):
        if self.page_no() == 1:
            self.set_fill_color(*AZUL_OSCURO)
            self.rect(0, 0, 216, 42, 'F')

            self.set_text_color(255, 255, 255)
            self.set_font('LiberationSans', 'B', 22)
            self.set_xy(10, 10)
            self.cell(0, 10, 'PRESUPUESTO')
            self.ln(8)

            self.set_font('LiberationSans', '', 11)
            self.set_xy(10, 22)
            self.cell(0, 7, 'Servicios Eléctricos - La Plata')
            self.ln(8)

            self.set_font('LiberationSans', 'I', 9)
            self.set_xy(10, 32)
            self.cell(0, 6, 'Presupuesto sin cargo - Válido por 15 días')

            # Línea decorativa
            self.set_fill_color(*AZUL_MEDIO)
            self.rect(0, 42, 216, 2, 'F')

            self.ln(25)  # Espacio después del header

    def footer(self):
        self.set_y(-20)
        self.set_draw_color(*AZUL_CLARO)
        self.set_fill_color(*AZUL_CLARO)
        self.rect(0, self.get_y() - 2, 216, 18, 'F')

        self.set_text_color(*GRIS_MEDIO)
        self.set_font('LiberationSans', 'I', 7)
        self.set_xy(10, self.get_y() + 1)
        self.cell(0, 5, 'Presupuesto sin compromiso de compra. Válido por 15 días corridos.')
        self.ln(4)
        self.set_xy(10, self.get_y() + 1)
        self.cell(0, 5, 'Los precios pueden variar sin previo aviso. No incluye tareas no detalladas.')
        self.set_x(10)
        self.set_font('LiberationSans', '', 7)
        self.set_text_color(*AZUL_MEDIO)
        self.cell(0, 5, f'Página {self.page_no()}/{{nb}}', 0, 0, 'R')

    def set_bold(self):
        self.set_font('LiberationSans', 'B', 10)

    def set_regular(self):
        self.set_font('LiberationSans', '', 10)

    def set_italic(self):
        self.set_font('LiberationSans', 'I', 10)

    def add_cliente_section(self, cliente, direccion, telefono="", fecha_presupuesto=""):
        """Sección datos del cliente"""
        self.set_fill_color(*AZUL_CLARO)
        self.set_text_color(*AZUL_OSCURO)
        self.set_font('LiberationSans', 'B', 11)
        self.cell(0, 8, 'DATOS DEL CLIENTE', 0, 1, 'L', fill=True)

        self.ln(2)
        self.set_text_color(*NEGRO)
        self.set_regular()

        datos = [
            ("Cliente:", cliente),
            ("Dirección:", direccion or "No especificada"),
            ("Teléfono:", telefono or "No proporcionado"),
            ("Fecha:", fecha_presupuesto or datetime.now().strftime("%d/%m/%Y")),
        ]

        for etiqueta, valor in datos:
            self.set_bold()
            self.cell(30, 6, etiqueta)
            self.set_regular()
            self.cell(0, 6, valor)
            self.ln(6)

        self.ln(4)

    def add_materiales_table(self, materiales):
        """Tabla de materiales"""
        self.set_fill_color(*AZUL_CLARO)
        self.set_text_color(*AZUL_OSCURO)
        self.set_font('LiberationSans', 'B', 11)
        self.cell(0, 8, 'MATERIALES', 0, 1, 'L', fill=True)

        self.ln(2)

        if not materiales:
            self.set_italic()
            self.set_text_color(*GRIS_MEDIO)
            self.cell(0, 6, 'No se incluyen materiales en este presupuesto.')
            self.ln(8)
            return

        # Headers
        self.set_fill_color(*AZUL_MEDIO)
        self.set_text_color(255, 255, 255)
        self.set_font('LiberationSans', 'B', 8)

        col_w = [80, 20, 30, 30]
        headers = ["Concepto", "Cant.", "P. Unit.", "Subtotal"]
        for i, h in enumerate(headers):
            self.cell(col_w[i], 7, h, 1, 0, 'C', fill=True)
        self.ln()

        # Datos
        self.set_text_color(*NEGRO)
        self.set_regular()
        fill = False
        total = 0

        for mat in materiales:
            nombre = mat["nombre"]
            cantidad = mat["cantidad"]
            precio_u = mat["precio_unitario"]
            subtotal = cantidad * precio_u
            total += subtotal

            if fill:
                self.set_fill_color(*GRIS_CLARO)
            else:
                self.set_fill_color(255, 255, 255)

            self.cell(col_w[0], 7, f"  {nombre}", 1, 0, 'L', fill=True)
            self.cell(col_w[1], 7, str(cantidad), 1, 0, 'C', fill=True)
            self.cell(col_w[2], 7, f"$ {precio_u:,.0f}", 1, 0, 'R', fill=True)
            self.cell(col_w[3], 7, f"$ {subtotal:,.0f}", 1, 0, 'R', fill=True)
            self.ln()
            fill = not fill

        self.ln(2)
        self.set_bold()
        self.set_font('LiberationSans', 'B', 10)
        self.cell(sum(col_w) - col_w[2], 7, "TOTAL MATERIALES", 1, 0, 'R')
        self.cell(col_w[2], 7, f"$ {total:,.0f}", 1, 0, 'R')
        self.ln(8)

    def add_mano_obra_table(self, mano_de_obra_total):
        """Sección mano de obra"""
        self.set_fill_color(*AZUL_CLARO)
        self.set_text_color(*AZUL_OSCURO)
        self.set_font('LiberationSans', 'B', 11)
        self.cell(0, 8, 'MANO DE OBRA', 0, 1, 'L', fill=True)

        self.ln(2)

        if mano_de_obra_total is None:
            self.set_italic()
            self.set_text_color(*GRIS_MEDIO)
            self.cell(0, 6, 'Se coordinará al momento de la visita.')
            self.ln(8)
            return

        col_w = [80, 20, 30, 30]
        self.set_fill_color(*AZUL_MEDIO)
        self.set_text_color(255, 255, 255)
        self.set_font('LiberationSans', 'B', 8)
        headers = ["Concepto", "Cant.", "P. Unit.", "Subtotal"]
        for i, h in enumerate(headers):
            self.cell(col_w[i], 7, h, 1, 0, 'C', fill=True)
        self.ln()

        self.set_text_color(*NEGRO)
        self.set_fill_color(255, 255, 255)
        self.set_regular()
        self.cell(col_w[0], 7, "  Trabajo eléctrico", 1, 0, 'L', fill=True)
        self.cell(col_w[1], 7, "1", 1, 0, 'C', fill=True)
        self.cell(col_w[2], 7, f"$ {mano_de_obra_total:,.0f}", 1, 0, 'R', fill=True)
        self.cell(col_w[3], 7, f"$ {mano_de_obra_total:,.0f}", 1, 0, 'R', fill=True)
        self.ln()

        self.ln(2)
        self.set_bold()
        self.cell(sum(col_w) - col_w[2], 7, "TOTAL MANO DE OBRA", 1, 0, 'R')
        self.cell(col_w[2], 7, f"$ {mano_de_obra_total:,.0f}", 1, 0, 'R')
        self.ln(8)

    def add_tareas_list(self, tareas):
        """Lista de tareas a realizar"""
        self.set_fill_color(*AZUL_CLARO)
        self.set_text_color(*AZUL_OSCURO)
        self.set_font('LiberationSans', 'B', 11)
        self.cell(0, 8, 'DETALLE DEL TRABAJO', 0, 1, 'L', fill=True)

        self.ln(2)

        if not tareas:
            self.ln(4)
            return

        self.set_regular()
        self.set_text_color(*NEGRO)

        for tarea in tareas:
            self.set_bullet_point()
            self.cell(0, 6, f"{tarea}", 0, 1)

        self.ln(4)

    def set_bullet_point(self):
        """Dibuja un bullet point"""
        x = self.get_x()
        y = self.get_y()
        self.set_fill_color(*AZUL_MEDIO)
        self.ellipse(x + 2, y + 2.5, 2, 2, 'F')
        self.set_x(x + 7)

    def add_resumen_final(self, total_materiales, total_mo):
        """Resumen final del presupuesto"""
        self.ln(5)
        self.set_fill_color(*AZUL_OSCURO)
        self.rect(10, self.get_y(), 196, 3, 'F')
        self.ln(5)

        self.set_text_color(*AZUL_OSCURO)
        self.set_font('LiberationSans', 'B', 14)
        self.cell(0, 10, 'RESUMEN DEL PRESUPUESTO', 0, 1, 'C')

        self.ln(3)

        lineas = []
        if total_materiales > 0:
            lineas.append(("Materiales", f"$ {total_materiales:,.0f}"))
        if total_mo and total_mo > 0:
            lineas.append(("Mano de obra", f"$ {total_mo:,.0f}"))

        total = total_materiales + (total_mo or 0)

        self.set_bold()
        for concepto, monto in lineas:
            self.set_font('LiberationSans', '', 11)
            self.set_text_color(*NEGRO)
            self.cell(106, 8, f"  {concepto}", 0, 0, 'L')
            self.cell(90, 8, monto, 0, 1, 'R')

        self.set_fill_color(*AZUL_CLARO)
        self.rect(10, self.get_y(), 196, 10, 'F')
        self.set_font('LiberationSans', 'B', 14)
        self.set_text_color(*AZUL_OSCURO)
        self.cell(106, 10, "  TOTAL PRESUPUESTO", 0, 0, 'L')
        self.cell(90, 10, f"$ {total:,.0f}", 0, 1, 'R')

        self.ln(12)

        # Observaciones
        self.set_fill_color(*GRIS_CLARO)
        self.set_text_color(*AZUL_OSCURO)
        self.set_font('LiberationSans', 'B', 10)
        self.cell(0, 8, 'OBSERVACIONES', 0, 1, 'L', fill=True)
        self.set_regular()
        self.set_text_color(*NEGRO)
        self.set_font('LiberationSans', '', 9)

        obs = "Los precios pueden variar sin previo aviso. Este presupuesto no incluye tareas no detalladas. El cliente queda notificado de cualquier cambio en materiales o alcance."

        w = 196
        self.multi_cell(w, 5, obs, 0, 'L', fill=False)


def generar_presupuesto(cliente, direccion, materiales=None, mano_de_obra=None,
                        tareas=None, telefono="", output_path=None):
    """Genera el PDF del presupuesto"""

    pdf = PresupuestoPDF()
    pdf.alias_nb_pages()
    pdf.add_page()

    # Secciones
    fecha_presupuesto = datetime.now().strftime("%d/%m/%Y")
    pdf.add_cliente_section(cliente, direccion, telefono, fecha_presupuesto)

    if tareas:
        pdf.add_tareas_list(tareas)

    total_mat = 0
    if materiales:
        for mat in materiales:
            mat["subtotal"] = mat["cantidad"] * mat["precio_unitario"]
            total_mat += mat["subtotal"]
        pdf.add_materiales_table(materiales)

    total_mo = mano_de_obra if mano_de_obra else None
    pdf.add_mano_obra_table(total_mo)

    pdf.add_resumen_final(total_mat, total_mo)

    # Guardar
    if not output_path:
        nombre_archivo = f"Presupuesto {cliente} - {datetime.now().strftime('%Y-%m-%d')}.pdf"
        nombre_archivo = re.sub(r'[^\w\s\-\.\(\)]', '', nombre_archivo)
        output_path = os.path.join(OUTPUT_DIR, nombre_archivo)

    pdf.output(output_path)
    return output_path


# ==================== INTERACTIVO ====================

def main_interactiva():
    print("\n⚡ Generador de Presupuestos - Electricista ⚡")
    print("=" * 50)

    precios = cargar_precios()
    print(f"\n📋 Lista de precios cargada ({len(precios['materiales'])} materiales, {len(precios['mano_obra'])} servicios)")

    # Datos del cliente
    cliente = input("\n👤 Nombre del cliente: ").strip()
    if not cliente:
        print("❌ Se necesita un nombre de cliente.")
        sys.exit(1)

    direccion = input("📍 Dirección: ").strip()
    telefono = input("📱 Teléfono (opcional): ").strip()

    # Materiales
    materiales = []
    print("\n📦 Materiales (deja en blanco para terminar):")
    print("   Podrás buscar por nombre. Precios disponibles:")
    for nombre, precio in precios["materiales"].items():
        print(f"   - {nombre}: ${precio:,.0f}")

    while True:
        item = input("\n   Item (nombre): ").strip()
        if not item:
            break

        precio = buscar_precio(item, precios["materiales"])
        if precio:
            print(f"   💰 Precio: ${precio:,.0f}")
        else:
            precio_str = input("   💰 Precio no encontrado. Ingresar precio: ").strip()
            try:
                precio = int(precio_str.replace(".", "").replace(",", ""))
            except ValueError:
                precio = 0
                print("   ⚠️ Precio no válido, se usa $0")

        try:
            cantidad = int(input("   📊 Cantidad: ").strip() or "1")
        except ValueError:
            cantidad = 1

        materiales.append({
            "nombre": item,
            "cantidad": cantidad,
            "precio_unitario": precio
        })
        print(f"   ✅ Agregado: {cantidad} x {item} = ${cantidad * precio:,.0f}")

    # Mano de obra
    print("\n🔧 Mano de obra:")
    for nombre, precio in precios["mano_obra"].items():
        print(f"   - {nombre}: ${precio:,.0f}")

    mo_str = input("\n   💰 Total mano de obra (número, o Enter): ").strip()
    mano_de_obra = None
    if mo_str:
        try:
            mano_de_obra = int(mo_str.replace(".", "").replace(",", ""))
        except ValueError:
            print("⚠️ No válido, se deja sin mano de obra")

    # Tareas
    tareas = []
    print("\n📋 Tareas (una por línea, Enter vacío para terminar):")
    while True:
        tarea = input("   Tarea: ").strip()
        if not tarea:
            break
        tareas.append(tarea)

    # Generar
    nombre_archivo = f"Presupuesto_{cliente.replace(' ', '_')}_{datetime.now().strftime('%Y-%m-%d')}.pdf"
    output = os.path.join(OUTPUT_DIR, nombre_archivo)

    path = generar_presupuesto(
        cliente=cliente,
        direccion=direccion,
        materiales=materiales if materiales else None,
        mano_de_obra=mano_de_obra,
        tareas=tareas if tareas else None,
        telefono=telefono,
        output_path=output
    )

    print(f"\n✅ Presupuesto generado: {path}")


def main_cli(cliente, direccion, materiales_list=None, mano_de_obra=None,
             tareas_list=None, telefono="", output=None):
    """Modo línea de comandos"""
    precios = cargar_precios()
    materiales = []

    if materiales_list:
        i = 0
        while i < len(materiales_list):
            nombre = materiales_list[i]
            cantidad = 1
            # Si el siguiente argumento es un número, es la cantidad
            if i + 1 < len(materiales_list) and materiales_list[i + 1].replace(".", "", 1).isdigit():
                cantidad = int(materiales_list[i + 1])
                i += 2
            else:
                i += 1

            precio = buscar_precio(nombre, precios["materiales"])
            if not precio:
                print(f"⚠️ No se encontró precio para '{nombre}', se usa $0")
                precio = 0

            materiales.append({
                "nombre": nombre,
                "cantidad": cantidad,
                "precio_unitario": precio
            })

    path = generar_presupuesto(
        cliente=cliente,
        direccion=direccion,
        materiales=materiales if materiales else None,
        mano_de_obra=mano_de_obra,
        tareas=tareas_list if tareas_list else None,
        telefono=telefono,
        output_path=output
    )

    print(f"✅ Presupuesto generado: {path}")
    return path


# ==================== ENTRY POINT ====================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generador de Presupuestos PDF para Electricista')
    parser.add_argument('--cliente', type=str, help='Nombre del cliente')
    parser.add_argument('--direccion', type=str, default='', help='Dirección del trabajo')
    parser.add_argument('--telefono', type=str, default='', help='Teléfono del cliente')
    parser.add_argument('--item', action='append', nargs='+', help='Material y cantidad pares (ej: "Cable 2.5mm" 5)')
    parser.add_argument('--mano_de_obra', type=int, default=None, help='Monto mano de obra')
    parser.add_argument('--tarea', action='append', help='Tarea a realizar')
    parser.add_argument('--output', type=str, default=None, help='Ruta de salida del PDF')

    args = parser.parse_args()

    if args.cliente:
        # Modo CLI
        materiales = []
        if args.item:
            for grupo in args.item:
                nombre = grupo[0]
                cantidad = int(grupo[1]) if len(grupo) > 1 else 1
                materiales.append((nombre, cantidad))

            precios = cargar_precios()
            materiales_parsed = []
            for nombre, cantidad in materiales:
                precio = buscar_precio(nombre, precios["materiales"])
                if not precio:
                    print(f"⚠️ No se encontró precio para '{nombre}', seusa $0")
                    precio = 0
                materiales_parsed.append({
                    "nombre": nombre,
                    "cantidad": cantidad,
                    "precio_unitario": precio
                })

            path = generar_presupuesto(
                cliente=args.cliente,
                direccion=args.direccion,
                materiales=materiales_parsed if materiales_parsed else None,
                mano_de_obra=args.mano_de_obra,
                tareas=args.tarea if args.tarea else None,
                telefono=args.telefono,
                output_path=args.output
            )
            print(f"✅ Presupuesto generado: {path}")
    else:
        # Modo interactivo
        main_interactiva()
