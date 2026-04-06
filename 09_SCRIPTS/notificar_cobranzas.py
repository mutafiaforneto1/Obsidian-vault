"""
Notificador de Cobranzas
Envía recordatorios por Telegram de trabajos pendientes de pago

Uso:
    python notificar_cobranzas.py
"""

import os
import re
from datetime import datetime, timedelta
import requests

# ==================== CONFIGURACIÓN ====================
VAULT_PATH = "/storage/emulated/0/Documents/Obsidian trabajo optimizado 2"

# Telegram
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

# ==================== FUNCIONES ====================

def obtener_trabajos_pendientes():
    """Busca todos los trabajos terminados sin cobrar"""
    trabajos = []
    
    trabajos_dir = os.path.join(VAULT_PATH, "01_TRABAJOS")
    
    if not os.path.exists(trabajos_dir):
        return []
    
    for raiz, _, archivos in os.walk(trabajos_dir):
        for archivo in archivos:
            if archivo.endswith('.md'):
                ruta = os.path.join(raiz, archivo)
                
                with open(ruta, 'r', encoding='utf-8') as f:
                    contenido = f.read()
                
                # Buscar trabajos terminados sin pagar
                if 'estado: 🛠️ Terminado' in contenido and ('pagado: false' in contenido or 'pagado: false' in contenido.lower()):
                    
                    # Extraer datos
                    cliente = re.search(r'cliente:\s*\[\[?([^]]+)\]?\]?', contenido)
                    monto = re.search(r'mano_de_obra:\s*(\d+)', contenido)
                    fecha = re.search(r'fecha:\s*(\d{4}-\d{2}-\d{2})', contenido)
                    direccion = re.search(r'dirección:\s*(.+)', contenido, re.MULTILINE)
                    telefono = re.search(r'teléfono:\s*(.+)', contenido, re.MULTILINE)
                    
                    trabajos.append({
                        'archivo': archivo,
                        'ruta': ruta,
                        'cliente': cliente.group(1) if cliente else 'Sin nombre',
                        'monto': int(monto.group(1)) if monto else 0,
                        'fecha': fecha.group(1) if fecha else 'Sin fecha',
                        'direccion': direccion.group(1).strip() if direccion else '',
                        'telefono': telefono.group(1).strip() if telefono else ''
                    })
    
    return trabajos

def calcular_dias_pendiente(fecha_str):
    """Calcula días desde la fecha del trabajo"""
    try:
        fecha = datetime.strptime(fecha_str, "%Y-%m-%d")
        dias = (datetime.now() - fecha).days
        return dias
    except:
        return 0

def enviar_telegram(mensaje):
    """Envía mensaje por Telegram"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Telegram no configurado")
        return False
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": mensaje,
        "parse_mode": "HTML"
    }
    
    try:
        response = requests.post(url, json=data)
        return response.status_code == 200
    except Exception as e:
        print(f"Error Telegram: {e}")
        return False

def enviar_recordatorio_whatsapp(telefono, cliente, monto, dias):
    """Envía recordatorio de pago por WhatsApp (requiere whapi configurado)"""
    # Esta función requiere WHAPI_TOKEN
    pass

# ==================== MAIN ====================

def main():
    print(f"[{datetime.now().strftime('%d/%m/%Y %H:%M')}] Buscando cobranzas pendientes...")
    
    trabajos = obtener_trabajos_pendientes()
    
    if not trabajos:
        print("✅ No hay trabajos pendientes de cobro")
        return
    
    # Ordenar por monto (mayor primero)
    trabajos.sort(key=lambda x: x['monto'], reverse=True)
    
    total_pendiente = sum(t['monto'] for t in trabajos)
    
    # Crear mensaje
    mensaje = f"""💸 <b>Recordatorio de Cobranzas</b>

📊 Resumen:
• Trabajos pendientes: {len(trabajos)}
• Total a cobrar: <b>${total_pendiente:,}</b>

"""
    
    for i, t in enumerate(trabajos[:10], 1):  # Máx 10 por mensaje
        dias = calcular_dias_pendiente(t['fecha'])
        
        # Emoji según antigüedad
        if dias > 30:
            emoji = "🔴"
        elif dias > 14:
            emoji = "🟡"
        else:
            emoji = "🟢"
        
        mensaje += f"""
{emoji} <b>{t['cliente']}</b>
   💵 ${t['monto']:,}
   📅 Hace {dias} días
   📍 {t['direccion'] if t['direccion'] else 'Sin dirección'}
"""
    
    if len(trabajos) > 10:
        mensaje += f"\n... y {len(trabajos) - 10} más"
    
    mensaje += """

⚡ Usa /cobranza en el bot para ver todos"""

    # Enviar
    print(f"\n📋 Enviando notificación de {len(trabajos)} cobranzas (${total_pendiente:,})...")
    
    if enviar_telegram(mensaje):
        print("✅ Notificación enviada a Telegram")
    else:
        print("❌ Error enviando a Telegram")
        print("\n📋 Vista previa del mensaje:")
        print(mensaje)

if __name__ == "__main__":
    main()
