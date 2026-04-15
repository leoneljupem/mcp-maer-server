# 📱 MAER + Tasker / AutoRemote — Guía de Integración

> Conecta tu Android con MAER para automatizar tareas, enviar comandos y recibir alertas.

---

## Requisitos

| Herramienta | Descripción | Dónde obtener |
|---|---|---|
| **Tasker** | App de automatización Android | Google Play (~4 USD) |
| **AutoRemote** | Plugin de comunicación remota | Google Play (plugin de Tasker) |
| **Red local** | MAER y el teléfono en la misma WiFi | — |
| **MAER Server** | `python server.py` corriendo | Puerto 8765 |

---

## Parte 1 — Configurar el servidor MAER

El servidor ya tiene los endpoints listos en `server.py`:

```
POST http://TU_IP_LOCAL:8765/api/tasker-receive
GET  http://TU_IP_LOCAL:8765/api/tasker-messages
```

### Encontrar tu IP local

**macOS / Linux:**
```bash
ifconfig | grep "inet " | grep -v 127.0.0.1
# Ejemplo: 192.168.1.105
```

**Windows:**
```
ipconfig | findstr "IPv4"
```

### Probar desde el teléfono (navegador)

Abre en el navegador de tu Android:
```
http://192.168.1.105:8765/api/tasker-messages
```

Si ves `{"mensajes":[]}` → el servidor está accesible desde el teléfono ✅

---

## Parte 2 — Configurar AutoRemote

### En el teléfono

1. Instala **AutoRemote** desde Google Play
2. Abre AutoRemote → copia tu **URL personal** (empieza con `https://autoremotejoaomgcd.appspot.com/...`)
3. Esta URL es para que la PC envíe mensajes al teléfono (no la necesitas para lo básico)

### En Tasker — Enviar mensajes a MAER

#### Tarea: "Enviar a MAER"

1. Abre Tasker → **Tareas** → ícono `+` → nombre: `Enviar a MAER`
2. Agrega acción: **Red → HTTP Request**
   - **Método:** POST
   - **URL:** `http://192.168.1.105:8765/api/tasker-receive`
   - **Headers:** `Content-Type:application/json`
   - **Body:**
     ```json
     {"mensaje": "%par1", "fuente": "tasker", "dispositivo": "%DEVID"}
     ```
   - `%par1` es el parámetro que pasarás cuando llames la tarea

3. Guarda la tarea

---

## Parte 3 — Perfiles de Automatización

### Perfil: Batería baja → MAER alerta

**Trigger:** Batería < 20%

1. Tasker → **Perfiles** → `+` → **Estado** → **Energía** → **Nivel de Batería**
   - Desde: 0  Hasta: 20
2. Vincula a **Tarea** → `Enviar a MAER`
   - Parámetro 1: `ALERTA: Batería baja (%BATT%)`

**En MAER verás:** `📱 Tasker: ALERTA: Batería baja (18%)`

---

### Perfil: Llegaste a casa → MAER notifica

**Trigger:** WiFi conectado a tu red de casa

1. **Perfiles** → `+` → **Estado** → **Red** → **Estado WiFi**
   - SSID: `nombre_de_tu_wifi`
   - Estado: Conectado
2. Tarea: `Enviar a MAER`
   - Parámetro 1: `Llegué a casa. WiFi: %WIFII`

---

### Perfil: App abierta → registro en MAER

**Trigger:** App específica en primer plano

1. **Perfiles** → `+` → **Aplicación** → selecciona la app (ej: WhatsApp)
2. Tarea: `Enviar a MAER`
   - Parámetro 1: `App abierta: %APP`

---

### Perfil: GPS salida/llegada

**Trigger:** Zona geográfica

1. **Perfiles** → `+` → **Localización** → introduce coordenadas y radio
2. Tarea entrada: `Enviar a MAER` → `Llegué a: NOMBRE_LUGAR`
3. Tarea salida: `Enviar a MAER` → `Salí de: NOMBRE_LUGAR`

---

### Perfil: SMS importante → MAER lo lee

**Trigger:** SMS recibido

1. **Perfiles** → `+` → **Evento** → **Teléfono** → **SMS Recibido**
   - Remitente: (déjalo vacío para todos, o pon un número específico)
2. Tarea:
   - Acción HTTP Request → Body: `{"mensaje": "SMS de %SMSRF: %SMSRB", "fuente": "sms"}`

---

### Perfil: Alarm Clock → recordatorio de pensión

1. **Perfiles** → `+` → **Evento** → **Fecha/Hora** → selecciona horario
2. Tarea: `Enviar a MAER`
   - Parámetro 1: `RECORDATORIO: Revisa el estado de tu trámite IMSS hoy.`

---

## Parte 4 — Leer mensajes de MAER en el teléfono

### Tarea: "Leer mensajes MAER"

1. **Red → HTTP Request**
   - Método: GET
   - URL: `http://192.168.1.105:8765/api/tasker-messages`
   - Guardar resultado en: `%maer_resp`

2. **Código → JavaScript** (o Variable → Set):
   ```javascript
   // Parsear JSON y obtener primer mensaje
   var data = JSON.parse(local.maer_resp);
   local.primer = data.mensajes.length > 0 ? data.mensajes[0].mensaje : 'Sin mensajes';
   ```

3. **Alerta → Notificación** o **Hablar** → usa `%primer`

---

## Parte 5 — Comandos especiales que MAER entiende

Envía estos textos como `"mensaje"` en el JSON:

| Comando | Qué hace MAER |
|---|---|
| `STATUS` | Responde con estado del sistema |
| `BATERIA:%n` | Registra nivel de batería |
| `UBICACION:%lat,%lon` | Registra ubicación recibida |
| `CAPTURA:%texto` | Guarda texto en historial |
| `ALERTA:%texto` | Muestra alerta con voz en MAER |
| `RECORDATORIO:%texto` | Agrega evento al módulo Pensión |

---

## Parte 6 — Ejemplo completo de tarea Tasker avanzada

### "Buenos días MAER"

Trigger: Todos los días a las 7:00 AM

Acciones:
```
1. HTTP Request POST → {"mensaje": "Buenos días MAER, hora de inicio: %TIME, batería: %BATT%, wifi: %WIFII", "fuente": "tasker_matinal"}
2. HTTP Request GET  → http://192.168.1.105:8765/api/tasker-messages → %maer_msgs
3. Hablar → "MAER recibió tu saludo."
```

---

## Parte 7 — Solución de problemas

| Problema | Solución |
|---|---|
| `Connection refused` | Verifica que `python server.py` está corriendo |
| `Network unreachable` | Asegúrate que PC y teléfono estén en la misma WiFi |
| `404 Not Found` | La IP cambió — busca la nueva con `ifconfig` |
| Tasker no ejecuta | Verifica permisos de red en Tasker (Configuración → Android) |
| No llegan mensajes | El servidor registra todo en consola — revisa la pestaña Sistema en MAER |

---

## Endpoints disponibles

```
POST /api/tasker-receive
Body: { "mensaje": "texto", "fuente": "tasker", "dispositivo": "...", "extra": {} }
Response: { "ok": true, "id": 123 }

GET /api/tasker-messages
Response: { "mensajes": [ { "id":1, "mensaje":"...", "ts":"...", "fuente":"tasker" } ] }
```

---

*MAER Guardian registra estas conexiones en `respaldo_maer/guardian.log`*
