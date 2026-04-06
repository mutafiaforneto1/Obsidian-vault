#!/usr/bin/env python3
"""
Limpieza de datos - Electricista Vault
Arregla inconsistencias en los archivos de trabajo del vault de Obsidian.

Problemas que arregla:
- Estados inconsistentes (Pendiente → Presupuesto, pendiente → 🛠️ Pendiente)
- Archivos sin campo "pagado" → se agrega false si terminado, null si pending
- Prioridad sin emoji "media" → 🔵 Media
- Fechas con placeholders templater sin resolver {{date}} {{time}}
- Links de clientes mal formados
"""

import os
import re
import sys
from datetime import datetime

VAULT_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRABAJOS_DIR = os.path.join(VAULT_PATH, "01_TRABAJOS")


def leer_frontmatter(archivo):
    """Extrae y parsea el frontmatter de un archivo markdown"""
    with open(archivo, 'r', encoding='utf-8') as f:
        contenido = f.read()

    match = re.match(r'^---\n(.*?)\n---', contenido, re.DOTALL)
    if not match:
        return None, contenido

    frontmatter_text = match.group(1)
    body = contenido[match.end():]

    # Parsear lineas simples (key: value)
    frontmatter = {}
    for line in frontmatter_text.split('\n'):
        if ':' in line:
            key, val = line.split(':', 1)
            frontmatter[key.strip()] = val.strip()

    return frontmatter, contenido, body


def guardar(archivo, contenido):
    """Guarda el contenido en el archivo"""
    with open(archivo, 'w', encoding='utf-8') as f:
        f.write(contenido)


def reconstruir_frontmatter(frontmatter):
    """Reconstruye el frontmatter como texto"""
    lines = ['---']
    for key, val in frontmatter.items():
        lines.append(f"{key}: {val}")
    lines.append('---')
    return '\n'.join(lines), '\n'


# ============= Correcciones =============

def corregir_estado(frontmatter, cambios):
    """Normaliza el campo estado"""
    estado = frontmatter.get('estado', '')

    estado_map = {
        '🛠️ pendiente': '🛠️ Pendiente',
        '🛠️ pendiente': '🛠️ Pendiente',
        'pendiente': '🛠️ Pendiente',
        'Pendiente': '🛠️ Pendiente',
        '🛠️ presupuesto': '🛠️ Presupuesto',
        'Presupuesto': '🛠️ Presupuesto',
        '🛠️ Presupuesto': '🛠️ Presupuesto',
        '🛠️ en curso': '🛠️ En curso',
        'En curso': '🛠️ En curso',
        '🛠️ En curso': '🛠️ En curso',
        '🛠️ terminado': '🛠️ Terminado',
        'Terminado': '🛠️ Terminado',
        '🛠️ Terminado': '🛠️ Terminado',
    }

    if estado in estado_map and estado_map[estado] != estado:
        nuevo = estado_map[estado]
        cambios.append(f"  estado '{estado}' → '{nuevo}'")
        frontmatter['estado'] = estado_map[estado]
        return True
    return False


def corregir_prioridad(frontmatter, cambios):
    """Normaliza prioridad con emoji"""
    prioridad = frontmatter.get('prioridad', '')
    if prioridad and prioridad not in ['🔴 Alta', '🔵 Media', '🟢 Baja']:
        cambios.append(f"  prioridad '{prioridad}' → '🔵 Media'")
        frontmatter['prioridad'] = '🔵 Media'
        return True
    return False


def corregir_fecha(frontmatter, cambios):
    """Arregla fechas con placeholders sin resolver"""
    fecha = frontmatter.get('fecha', '')
    if '{{date}}' in fecha or '{{time}}' in fecha:
        nueva_fecha = datetime.now().strftime("%Y-%m-%d %H:%M")
        cambios.append(f"  fecha '{fecha}' → '{nueva_fecha}'")
        frontmatter['fecha'] = nueva_fecha
        return True
    return False


def agregar_pagado(frontmatter, contenido, cambios):
    """Agrega campo pagado si no existe"""
    if 'pagado' not in frontmatter:
        estado = frontmatter.get('estado', '').lower()
        if 'terminado' in estado:
            frontmatter['pagado'] = 'false'
            cambios.append("  agregado pagado: false (terminado sin cobrar)")
        elif 'presupuesto' in estado or 'pendiente' in estado:
            frontmatter['pagado'] = 'false'
            cambios.append("  agregado pagado: false (pendiente/presupuesto)")
        else:
            frontmatter['pagado'] = 'false'
            cambios.append("  agregado pagado: false")
        return True
    return False


def corregir_mano_obra(frontmatter, cambios):
    """Corregir mano_de_obra: 0 → campo ausente o valor estimado"""
    mo = frontmatter.get('mano_de_obra', '')
    if mo == '0':
        estado = frontmatter.get('estado', '')
        # Si es en curso o presupuesto y tiene 0, lo dejamos como 0 pero marcamos
        # Si es terminado y tiene 0, probablemente fue gratis o no se registró
        cambios.append(f"  ⚠️ mano_de_obra: 0 ({estado})")
    return False


def verificar_link_cliente(frontmatter, cambios, nombre_archivo):
    """Verifica que el link del cliente tenga formato consistente"""
    cliente = frontmatter.get('cliente', '')
    if not cliente:
        cambios.append("  ❌ No tiene campo cliente")
        return True

    # Detectar links mal formados como "[[02_CLIENTES/Cliente X|Cliente X]]"
    if '02_CLIENTES/' in cliente:
        nuevo = re.sub(r'\[\[02_CLIENTES/([^|]+)\|([^]]+)\]\]', r'[[\2]]', cliente)
        cambios.append(f"  link cliente fix: '{cliente}' → '{nuevo}'")
        frontmatter['cliente'] = nuevo
        return True

    # Detectar link a trabajo en vez de cliente
    if 'Trabajo ' in cliente and cliente.startswith('[['):
        cambios.append(f"  ⚠️ cliente apunta a un trabajo: {cliente}")

    return False


def main():
    print("🔧 Limpieza de datos - Electricista Vault")
    print("=" * 50)

    if not os.path.exists(TRABAJOS_DIR):
        print(f"❌ No existe {TRABAJOS_DIR}")
        sys.exit(1)

    archivos = [f for f in os.listdir(TRABAJOS_DIR) if f.endswith('.md')]
    total_corregidos = 0

    for archivo in sorted(archivos):
        ruta = os.path.join(TRABAJOS_DIR, archivo)
        fm, contenido, body = leer_frontmatter(ruta)

        if fm is None:
            print(f"⚠️ {archivo}: Sin frontmatter")
            continue

        cambios = []
        corregido = False

        corregido |= corregir_estado(fm, cambios)
        corregido |= corregir_prioridad(fm, cambios)
        corregido |= corregir_fecha(fm, cambios)
        corregido |= agregar_pagado(fm, contenido, cambios)
        corregido |= corregir_mano_obra(fm, cambios)
        corregido |= verificar_link_cliente(fm, cambios, archivo)

        if corregido:
            print(f"\n📄 {archivo}")
            for c in cambios:
                print(c)

            # Reconstruir archivo completo
            fm_text, nl = reconstruir_frontmatter(fm)
            nuevo_contenido = fm_text + nl + body
            save(ruta, nuevo_contenido)
            total_corregidos += 1

    print(f"\n✅ {total_corregidos} archivos corregidos de {len(archivos)}")


if __name__ == "__main__":
    main()
