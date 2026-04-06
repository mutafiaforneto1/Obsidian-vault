# Bot WhatsApp - Electricista

## Requisitos
- Python 3.8+
- Teléfono con Termux
- Cuenta en [whapi.cloud](https://whapi.cloud) (gratis)

## Instalación

### 1. Instalar dependencias en Termux
```bash
pkg update && pkg upgrade
pkg install python nodejs

# Crear carpeta del bot
mkdir -p ~/bot_whatsapp
cd ~/bot_whatsapp

# Copiar archivos desde GitHub (o clonar repo)
git clone https://github.com/mutafiaforneto1/Obsidian-vault.git .
cd "Obsidian trabajo optimizado 2"

# Instalar Python packages
pip install flask requests python-dateutil
```

### 2. Crear cuenta en whapi.cloud

1. Ve a https://whapi.cloud
2. Regístrate gratis
3. Crea un nuevo proyecto (Channel → WhatsApp)
4. Conecta tu WhatsApp escaneando el QR
5. Copia tu **Webhook URL** de la configuración

### 3. Configurar variables de entorno

```bash
# Token de whapi
export WHAPI_TOKEN="tu_token_de_whapi"

# Opcional: Telegram para notificaciones
export TELEGRAM_BOT_TOKEN="tu_token_de_bot"
export TELEGRAM_CHAT_ID="tu_chat_id"
```

### 4. Obtener ngrok (para recibir mensajes)

```bash
pkg install termux-api
pkg install openssh
pkg install termux-boot

# Descargar ngrok
curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | tee ngrok.asc | head -n 2
wget https://bin.equinox.io/c/4VmDzA7iaHb/ngrok-stable-linux-arm64.tgz
tar xzf ngrok-stable-linux-arm64.tgz
./ngrok authtoken tu_token_ngrok
```

### 5. Ejecutar

```bash
cd ~/bot_whatsapp

# Terminal 1: Iniciar ngrok
./ngrok http 5000

# Terminal 2: Iniciar bot
export WHAPI_TOKEN="tu_token"
python bot_whatsapp.py
```

### 6. Configurar webhook en whapi.cloud

En la configuración de tu canal en whapi.cloud, configura el webhook:
```
https://tu-url-ngrok.ngrok.io/webhook
```

## Uso

Cuando un cliente te escriba por WhatsApp, el bot:

1. 📱 Recibe el mensaje
2. 📝 Crea automáticamente una nota en `01_TRABAJOS/`
3. 👤 Registra/actualiza el cliente en `02_CLIENTES/`
4. 💬 Responde al cliente confirmando
5. 📢 (Opcional) Te notifica por Telegram

## Comandos especiales

Envía desde WhatsApp:
- `TRABAJO: [descripción]` - Crear trabajo
- `STATUS` - Ver tus trabajos pendientes
- `AYUDA` - Ver comandos disponibles

## Troubleshooting

### El bot no responde
- Verifica que ngrok esté corriendo
- Verifica que el webhook en whapi esté configurado correctamente
- Revisa los logs del bot

### No se crea la nota
- Verifica que la ruta del vault sea correcta
- Verifica permisos de escritura

### Error de conexión
- Reinicia ngrok: `./ngrok http 5000`
- Verifica tu token de whapi
