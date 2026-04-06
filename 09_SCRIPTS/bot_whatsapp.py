"""
Bot de WhatsApp para Electricista
Recibe mensajes y crea notas de trabajo automáticamente

Requiere:
    pip install flask requests python-dateutil

Uso:
    python bot_whatsapp.py
"""

import os
import re
import json
from datetime import datetime
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# ==================== CONFIGURACIÓN ====================
VAULT_PATH = "/storage/emulated/0/Documents/Obsidian trabajo optimizado 2"

# Obtener token de whapi.cloud (configúralo en la variable o como variable de entorno)
WHAPI_TOKEN = os.environ.get("WHAPI_TOKEN", "")

# Webhook endpoint de whapi (para recibir mensajes)
WEBHOOK_URL = "https://gate.whapi.cloud/webhook"

# ==================== FUNCIONES ====================

def limpiar_nombre(nombre):
    """Limpia el nombre para usar como nombre de archivo válido"""
    nombre = re.sub(r'[^\w\s\-]', '', nombre)
    nombre = nombre.strip()
    return nombre

def extraer_direccion(texto):
    """Intenta extraer una dirección del texto"""
    patrones = [
        r'(\d+\s*(?:y|&\s*)?\s*\d+)',  # 123 y 45
        r'(?:en|calles?|dirección|dir)\s*[:\-]?\s*(.+?)(?:\.|$)',  # en calle...
        r'(?:dirección|dir)\s*[:\-]?\s*(.+?)(?:\.|$)',
    ]
    
    for patron in patrones:
        match = re.search(patron, texto, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return ""

def detectar_prioridad(texto):
    """Detecta la prioridad según palabras clave"""
    texto_lower = texto.lower()
    
    if any(p in texto_lower for p in ['urgente', 'emergencia', 'ahora', 'pronto']):
        return "🔴 Alta"
    elif any(p in texto_lower for p in ['cuando puedas', 'no hay apuro', 'despacio']):
        return "🟢 Baja"
    return "🔵 Media"

def crear_nota_trabajo(cliente, direccion, descripcion, prioridad, telefono=""):
    """Crea una nota de trabajo en el vault"""
    
    # Limpiar nombre del cliente
    nombre_limpio = limpiar_nombre(cliente)
    fecha = datetime.now().strftime("%Y-%m-%d")
    
    # Nombre del archivo
    nombre_archivo = f"Trabajo {nombre_limpio} - {fecha}.md"
    
    # Verificar si ya existe
    trabajos_dir = os.path.join(VAULT_PATH, "01_TRABAJOS")
    os.makedirs(trabajos_dir, exist_ok=True)
    
    ruta_archivo = os.path.join(trabajos_dir, nombre_archivo)
    
    if os.path.exists(ruta_archivo):
        # Agregar序号
        nombre_archivo = f"Trabajo {nombre_limpio} - {fecha} ({datetime.now().strftime('%H%M')}).md"
        ruta_archivo = os.path.join(trabajos_dir, nombre_archivo)
    
    # Crear cliente si no existe
    crear_nota_cliente(nombre_limpio, telefono, direccion)
    
    # Contenido de la nota
    contenido = f"""---
tipo: trabajo
cliente: "[[Cliente {nombre_limpio}]]"
dirección: {direccion if direccion else "Sin registrar"}
prioridad: {prioridad}
fecha: {fecha}
estado: 🛠️ Pendiente
pagado: false
teléfono: {telefono if telefono else ""}
---

# 📋 {nombre_limpio}

## Descripción
{descripcion}

## Notas
- Recibido via WhatsApp: "{descripcion[:100]}..."

## Tareas
- [ ] Confirmar turno
- [ ] Visitar lugar
- [ ] Realizar trabajo
- [ ] Cobrar

---
*Creado automáticamente el {datetime.now().strftime('%d/%m/%Y %H:%M')}*
"""
    
    with open(ruta_archivo, 'w', encoding='utf-8') as f:
        f.write(contenido)
    
    return ruta_archivo

def crear_nota_cliente(nombre, telefono, direccion):
    """Crea o actualiza la nota de cliente"""
    
    clientes_dir = os.path.join(VAULT_PATH, "02_CLIENTES")
    os.makedirs(clientes_dir, exist_ok=True)
    
    nombre_archivo = f"Cliente {nombre}.md"
    ruta_archivo = os.path.join(clientes_dir, nombre_archivo)
    
    if os.path.exists(ruta_archivo):
        # Actualizar existente
        with open(ruta_archivo, 'r', encoding='utf-8') as f:
            contenido = f.read()
        
        # Agregar teléfono si no está
        if telefono and "teléfono:" in contenido:
            contenido = re.sub(r'teléfono:\s*\n', f'teléfono: {telefono}\n', contenido)
        
        with open(ruta_archivo, 'w', encoding='utf-8') as f:
            f.write(contenido)
    else:
        # Crear nuevo
        contenido = f"""---
tipo: cliente
nombre: {nombre}
teléfono: {telefono if telefono else ""}
dirección_fija: {direccion if direccion else ""}
zona: 
categoría: 🟢 Particular
---

# Cliente {nombre}

## Datos
- **Teléfono:** {telefono if telefono else "Sin registrar"}
- **Dirección:** {direccion if direccion else "Sin registrar"}

## Trabajos
-

## Notas
-

## Historial
- {datetime.now().strftime('%d/%m/%Y')}: Primer contacto via WhatsApp
"""
        with open(ruta_archivo, 'w', encoding='utf-8') as f:
            f.write(contenido)
    
    return ruta_archivo

def responder_whatsapp(telefono, mensaje):
    """Envía respuesta por WhatsApp usando whapi"""
    if not WHAPI_TOKEN:
        print("⚠️ WHAPI_TOKEN no configurado")
        return False
    
    url = "https://gate.whapi.cloud/messages/text"
    headers = {
        "Authorization": f"Bearer {WHAPI_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "to": telefono,
        "body": mensaje
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        return response.status_code == 200
    except Exception as e:
        print(f"Error enviando WhatsApp: {e}")
        return False

def notificar_telegram(mensaje):
    """Envía notificación a Telegram si está configurado"""
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
    
    if not bot_token or not chat_id:
        return False
    
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": mensaje,
        "parse_mode": "HTML"
    }
    
    try:
        response = requests.post(url, json=data)
        return response.status_code == 200
    except Exception as e:
        print(f"Error enviando Telegram: {e}")
        return False

def procesar_mensaje(mensaje, telefono, nombre_remitente):
    """Procesa el mensaje y crea el trabajo"""
    
    print(f"\n📱 Mensaje recibido de {nombre_remitente}:")
    print(f"   {mensaje[:100]}...")
    
    # Extraer información
    direccion = extraer_direccion(mensaje)
    prioridad = detectar_prioridad(mensaje)
    
    # El cliente es el nombre del remitente por defecto
    cliente = nombre_remitente if nombre_remitente else "Cliente WhatsApp"
    
    # Crear la nota
    try:
        ruta = crear_nota_trabajo(
            cliente=cliente,
            direccion=direccion,
            descripcion=mensaje,
            prioridad=prioridad,
            telefono=telefono
        )
        
        nombre_archivo = os.path.basename(ruta)
        print(f"   ✅ Nota creada: {nombre_archivo}")
        
        # Responder
        respuesta = f"""¡Hola {cliente}! 👋

Recibí tu mensaje. Ya creé la nota de trabajo 📋

📍 {f'Dirección: {direccion}' if direccion else 'Dirección: Pendiente'}
⚡ Prioridad: {prioridad}

Te contactaré pronto para confirmar el turno.

¡Saludos! ⚡"""
        
        responder_whatsapp(telefono, respuesta)
        
        # Notificar por Telegram
        notif = f"""🆕 <b>Nuevo Trabajo de WhatsApp</b>

👤 {cliente}
📍 {direccion if direccion else 'Sin dirección'}
⚡ {prioridad}

📝 {mensaje[:100]}..."""
        notificar_telegram(notif)
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        responder_whatsapp(telefono, "Hubo un error procesando tu mensaje. Intenta de nuevo.")
        return False

# ==================== WEBHOOK ====================

@app.route('/webhook', methods=['POST'])
def webhook():
    """Recive mensajes de WhatsApp via whapi.cloud"""
    try:
        data = request.json
        
        # Verificar si es un mensaje de texto
        if data.get('type') == 'text':
            message = data.get('text', {}).get('body', '')
            from_num = data.get('from', '')
            
            # Obtener nombre del contacto (si está disponible)
            contact_name = data.get('contact', {}).get('name', '')
            
            procesar_mensaje(message, from_num, contact_name)
        
        return jsonify({"status": "ok"})
    
    except Exception as e:
        print(f"Error en webhook: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({"status": "ok", "bot": "electricista-whatsapp"})

@app.route('/test', methods=['GET'])
def test():
    """Endpoint de prueba"""
    cliente_test = "Juan Pérez"
    direccion_test = "123 y 45"
    
    crear_nota_trabajo(
        cliente=cliente_test,
        direccion=direccion_test,
        descripcion="Test de mensaje automático",
        prioridad="🔵 Media",
        telefono="+5491160000000"
    )
    
    return jsonify({
        "status": "test_created",
        "cliente": cliente_test,
        "path": VAULT_PATH
    })

# ==================== MAIN ====================

if __name__ == "__main__":
    print("""
⚡ Bot WhatsApp - Electricista ⚡
================================
    """)
    
    if not WHAPI_TOKEN:
        print("⚠️  ATENCIÓN: WHAPI_TOKEN no configurado")
        print("    Configura la variable de entorno WHAPI_TOKEN")
        print("    O edita el archivo y coloca tu token en WHAPI_TOKEN")
    
    print(f"📁 Vault: {VAULT_PATH}")
    print("🌐 Servidor iniciando en http://0.0.0.0:5000")
    print("\nPara recibir mensajes, configura el webhook en whapi.cloud:")
    print("   https://tu-servidor.ngrok.io/webhook")
    print("\n" + "="*40 + "\n")
    
    # Usar ngrok para exponer el servidor
    app.run(host='0.0.0.0', port=5000, debug=True)
