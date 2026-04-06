#!/usr/bin/env python3
"""
Normaliza todos los archivos de 01_TRABAJOS del vault de Obsidian.
- Agrega frontmatter faltante a archivos que no lo tienen
- Corrige estados inconsistentes
- Normaliza campos vacíos o incompletos
"""

import os
import re
import json
from datetime import datetime

VAULT_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRABAJOS_DIR = os.path.join(VAULT_PATH, "01_TRABAJOS")
BACKUP_DIR = os.path.join(TRABAJOS_DIR, ".backup_normalizacion")

# Crear backup
os.makedirs(BACKUP_DIR, exist_ok=True)
print(f"📁 Vault: {VAULT_PATH}")
print(f"📁 Trabajos: {TRABAJOS_DIR}")
print()

def clean_frontmatter(fm):
    """Normaliza campos del frontmatter"""
    cambios = []

    # 1. Normalizar estado
    estado = fm.get("estado", "").strip()
    if "🛠️" not in estado:
        estado_lower = estado.lower()
        if "terminado" in estado_lower or "terminada" in estado_lower:
            fm["estado"] = "🛠️ Terminado"
            cambios.append(f"estado: '{estado}' → '🛠️ Terminado'")
        elif "en curso" in estado_lower or "encurso" in estado_lower or "trabajando" in estado_lower:
            fm["estado"] = "🛠️ En curso"
            cambios.append(f"estado: '{estado}' → '🛠️ En curso'")
        elif "pendiente" in estado_lower:
            fm["estado"] = "🛠️ Pendiente"
            cambios.append(f"estado: '{estado}' → '🛠️ Pendiente'")
        elif "presupuesto" in estado_lower or "pendiente" in estado_lower:
            fm["estado"] = "🛠️ Presupuesto"
            cambios.append(f"estado: '{estado}' → '🛠️ Presupuesto'")
        else:
            fm["estado"] = "🛠️ Pendiente"
            cambios.append(f"estado: '{estado}' → '🛠️ Pendiente' (por defecto)")

    # 2. Normalizar pagado - Terminado sin pagado field
    if fm.get("estado") == "🛠️ Terminado" and "pagado" not in fm:
        fm["pagado"] = "false"
        cambios.append("agregado pagado: false (por defecto)")

    # 3. Si no tiene pagado y no está terminado
    if "pagado" not in fm:
        fm["pagado"] = "false"
        cambios.append("agregado pagado: false (por defecto)")

    # 4. Normalizar prioridad
    prioridad = str(fm.get("prioridad", "")).strip()
    if prioridad not in ["🔴 Alta", "🔵 Media", "🟢 Baja"]:
        fm["prioridad"] = "🔵 Media"
        if prioridad and prioridad != "":
            cambios.append(f"prioridad: '{prioridad}' → '🔵 Media'")

    # 5. Normalizar dirección
    direccion = str(fm.get("dirección", "")).strip()
    if not direccion or direccion == "Sin registrar" or direccion == "":
        fm["dirección"] = "Sin registrar"
    if fm.get("dirección") == "Sin registrar":
        pass  # no es error

    # 6. Limpiar fecha con templates
    fecha = str(fm.get("fecha", "")).strip()
    if "{{" in fecha:
        fm["fecha"] = "2026-01-20"  # Default razonable, archivo creado ~enero 2026
        cambios.append(f"fecha: '{fecha}' → '2026-01-20' (template sin render, corregido)")

    # 7. Agregar tipo si falta
    if "tipo" not in fm:
        fm["tipo"] = "trabajo"
        cambios.append("agregado tipo: trabajo")

    return cambios

def parse_existing_frontmatter(content):
    """Parsea el frontmatter existente de un archivo"""
    match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
    if match:
        fm_text = match.group(1)
        fm = {}
        for line in fm_text.split('\n'):
            line = line.strip()
            if ':' in line:
                key, val = line.split(':', 1)
                key = key.strip()
                val = val.strip()
                # Convertir valores
                if val == 'true' or val == 'True':
                    val = True
                elif val == 'false' or val == 'False':
                    val = False
                elif val.startswith('"') and val.endswith('"'):
                    val = val[1:-1]
                else:
                    try:
                        val = int(val)
                    except ValueError:
                        pass
                fm[key] = val
        return fm, match
    return None, None

def build_frontmatter(fm):
    """Construye el texto de frontmatter desde un dict"""
    lines = ["---"]
    for key in ["tipo", "cliente", "dirección", "prioridad", "fecha", "estado", "mano_de_obra", "costo_materiales", "pagado", "fecha_cierre", "teléfono"]:
        if key in fm:
            val = fm[key]
            if isinstance(val, str) and ("[[" in val or " " in val):
                lines.append(f'{key}: "{val}"')
            else:
                lines.append(f"{key}: {val}")

    # Agregar campos extra que no están en la lista estándar
    for key, val in fm.items():
        if key not in ["tipo", "cliente", "dirección", "prioridad", "fecha", "estado", "mano_de_obra", "costo_materiales", "pagado", "fecha_cierre", "teléfono"]:
            if isinstance(val, str) and ("[[" in val or " " in val):
                lines.append(f'{key}: "{val}"')
            else:
                lines.append(f"{key}: {val}")

    lines.append("---")
    return "\n".join(lines)

def infer_from_content(filename, content):
    """Infiere datos del contenido del archivo cuando no hay frontmatter"""
    # Extraer nombre del cliente del nombre del archivo
    nombre_archivo = os.path.splitext(filename)[0]
    # Eliminar prefijo "Trabajo " o "trabajo "
    nombre_inferido = re.sub(r'^(Trabajo|trabajo)\s+', '', nombre_archivo)

    fm = {"tipo": "trabajo", "cliente": nombre_inferido}

    # Si es Terminado (tiene checks marcados)
    if '- [x]' in content:
        fm["estado"] = "🛠️ Terminado"
        fm["pagado"] = "false"  # Por defecto
    elif '- [ ]' in content:
        fm["estado"] = "🛠️ En curso"
        fm["pagado"] = "false"
    else:
        fm["estado"] = "🛠️ Presupuesto"
        fm["pagado"] = "false"

    fm["prioridad"] = "🔵 Media"
    fm["dirección"] = "Sin registrar"
    fm["fecha"] = "2026-01-20"  # Default para archivos sin fecha explícita

    return fm, nombre_inferido

# ====== PROCESAR TODOS LOS ARCHIVOS ======

total = 0
arreglados = 0
archivos_sin_fm = 0

md_files = [f for f in os.listdir(TRABAJOS_DIR) if f.endswith('.md') and not f.startswith('.backup')]
print(f"🔍 Procesando {len(md_files)} archivos de trabajo...\n")

for filename in sorted(md_files):
    filepath = os.path.join(TRABAJOS_DIR, filename)

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    total += 1

    fm, match = parse_existing_frontmatter(content)

    if fm is None:
        # No tiene frontmatter - inferir del contenido
        archivos_sin_fm += 1
        fm, nombre_inferido = infer_from_content(filename, content)
        print(f"📝 SIN FRONTMATTER: {filename} → creado desde contenido")

        # Generar frontmatter nuevo
        nuevo_fm = build_frontmatter(fm)

        # Insertar al principio del archivo (después de la primera línea si tiene #)
        lines = content.split('\n')
        # Insertar después del primer bloque que tenga # si existe
        insert_idx = 0
        for i, line in enumerate(lines):
            if line.startswith('#'):
                insert_idx = i
                break

        nuevo_contenido = "\n".join(lines[:insert_idx]) + "\n" + nuevo_fm + "\n" + "\n".join(lines[insert_idx:])

        # Backupear
        backup_path = os.path.join(BACKUP_DIR, filename)
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(content)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(nuevo_contenido)

        arreglados += 1
        continue

    # Tiene frontmatter - normalizar
    cambios = clean_frontmatter(fm)

    if cambios:
        print(f"🔧 ARREGLADO: {filename}")
        for c in cambios:
            print(f"     - {c}")

        nuevo_fm = build_frontmatter(fm)

        # Reemplazar el frontmatter existente
        nuevo_contenido = re.sub(
            r'^---\n.*?\n---',
            nuevo_fm,
            content,
            count=1,
            flags=re.DOTALL
        )

        # Backupear
        backup_path = os.path.join(BACKUP_DIR, filename)
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(content)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(nuevo_contenido)

        arreglados += 1

print(f"\n✅ Listo!")
print(f"   📁 Total: {total}")
print(f"   🔧 Arreglados: {arreglados}")
print(f"   📝 Sin frontmatter: {archivos_sin_fm}")
print(f"   💾 Backup en: {BACKUP_DIR}/")
