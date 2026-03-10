# Jorise Mobile — Checklist de Desarrollo

**Stack:** Java + Kotlin + Jetpack Compose (ecosistema Java completo disponible)  
**Target:** Usuarios vulnerables — adultos mayores, entornos corporativos  
**Cerebro de detección:** Jorise AI — el modelo ML entrenado en `E:\Datasets\training\`  
**Leyenda:** ✅ Ya existe en `jorise_mobile/` · 🔧 Parcial (TODO interno) · ⬜ Pendiente

---

## Arquitectura General

```
[Dispositivo Android]
  Telemetría → SignalCollector → ContextSnapshot
                                       ↓
                          RiskEngine (reglas locales rápidas)
                                       ↓ si score ≥ 50 o evento crítico
                          Jorise Core API (Django)
                                       ↓
                          JORISE AI — modelo XGBoost entrenado
                          (CIC-IDS2017 + UNSW-NB15 + jorise_lab)
                                       ↓
                          RiskScore + Categoría + Explicación
                                       ↓
                    Alerta local  |  Incidente en SOC Dashboard
```

**El dispositivo móvil es un sensor.** La inteligencia vive en Jorise Core.  
Las reglas locales (`RiskEngine.kt`) actúan rápido sin conexión.  
Jorise AI hace el análisis profundo cuando hay conectividad.

---

## Base existente (`jorise_mobile/android/`)

- ✅ `SignalCollector.kt` — recolecta WiFi, VPN, developer options, hora inusual
- ✅ `ContextSnapshot.kt` — modelo de datos con 11 señales de contexto
- ✅ `RiskEngine.kt` — motor de reglas local, 12 reglas, scoring 0–100
- ✅ `GuardianApiClient.kt` — cliente HTTP (`POST /api/v1/evaluate`, `POST /api/v1/report`)
- ✅ `KnownNetworksStore.kt` — whitelist de redes WiFi (SharedPreferences)
- ✅ `MainActivity.kt` — dashboard Compose con `RiskCard` y botón "Verificar ahora"
- 🔧 `AccessibilityService` — declarado en Manifest + config XML, lógica pendiente
- 🔧 Backend Python en `jorise_mobile/backend/` (protótipo, reemplazar con Jorise Core)

---

## Fase 1 — Telemetría

- ✅ `SignalCollector.kt` — WiFi, VPN, developer options, hora inusual
- ✅ `ContextSnapshot.kt` — modelo de datos canónico
- 🔧 `AccessibilityService` — declarado, falta implementar lógica de detección
- 🔧 `UsageStatsManager` → `unknownAppForeground` (TODO en SignalCollector)
- 🔧 `PackageManager` → `newSensitivePermission` (TODO en SignalCollector)
- 🔧 `LinkProperties` → leer DNS activo real (`dnsStandard` siempre true ahora)
- 🔧 Contador persistido de login fallidos (`recentFailedLogins`)
- ⬜ `BroadcastReceiver` — instalar/desinstalar apps, boot, cambios de permisos
- ⬜ `NotificationListenerService` — metadata de notificaciones (sin leer contenido)
- ⬜ `VpnService` — inspección de tráfico de red local
- ⬜ Detectar acceso a micrófono, cámara, almacenamiento por app
- ⬜ Detectar lectura/escritura de clipboard
- ⬜ Hash APK + detección de sideload vs Play Store

---

## Fase 2 — Motor Local de Reglas (pre-Jorise)

Detección rápida sin conexión. No necesita Jorise AI — actúa en < 5ms.

- ✅ `RiskEngine.kt` — 12 reglas con scoring acumulativo 0–100
- ✅ `KnownNetworksStore.kt` — whitelist WiFi
- 🔧 Regla overlay (40pts) — depende de AccessibilityService (pendiente)
- 🔧 Regla TLS inválido (35pts) — depende de AccessibilityService (pendiente)
- ⬜ Lista negra de IPs/dominios offline (asset bundled en el APK)
- ⬜ Buffer circular por app — últimos N eventos (default 50)
- ⬜ Correlación temporal en ventana 1min / 5min / 1h
- ⬜ Room DB — historial de eventos e incidentes
- ⬜ Regla: app sideloaded + solicita accesibilidad
- ⬜ Regla: app < 24h instalada conectándose a IP desconocida
- ⬜ Regla: OVERLAY + ACCESSIBILITY activos simultáneamente
- ⬜ Regla: overlay activo durante app bancaria → crítico inmediato

---

## Fase 3 — Jorise AI Engine (cerebro de detección)

El modelo ML entrenado en `E:\Datasets\training\` es quien toma la decisión final.  
El móvil envía el `ContextSnapshot` → Jorise Core corre inferencia → retorna categoría + score.

### 3.1 Integración con Jorise Core

- ✅ `GuardianApiClient.kt` apunta a `POST /api/v1/evaluate` — estructura compatible
- ⬜ Endpoint `/api/mobile/analyze` en Jorise Core (Django) que recibe el snapshot
- ⬜ Jorise Core traduce `ContextSnapshot` → 25 universal features del modelo
- ⬜ Jorise modelo XGBoost retorna: clase + probabilidad por clase
- ⬜ Mapeo de clases del modelo a categorías móviles:

| Clase Jorise | Categoría móvil |
|---|---|
| DDoS | Red comprometida / C2 activo |
| Bot | App maliciosa / spyware |
| WebAttack | Phishing / inyección |
| BruteForce | Intento de acceso no autorizado |
| Infiltration | APT / acceso persistente |
| PortScan | Reconocimiento de red |
| DoS | Consumo anormal de red |

### 3.2 Flujo de análisis

```
ContextSnapshot (móvil)
        ↓
POST /api/mobile/analyze (Jorise Core)
        ↓
Feature extraction: ContextSnapshot → 25 universal features
        ↓
Jorise XGBoost model → predict_proba()
        ↓
{class, confidence, risk_score, explanation}
        ↓
Response al dispositivo → alerta + acción recomendada
```

### 3.3 Casos de detección objetivo (para jorise_lab_mobile)

- ⬜ App sideload + accesibilidad + overlay → overlay attack / banking trojan
- ⬜ READ_SMS + SEND_SMS + IP extranjera → SMS stealer
- ⬜ Notificación con URL acortada + urgencia → phishing
- ⬜ App nueva + conexión a IP desconocida → posible C2
- ⬜ Clipboard activo durante sesión bancaria → credential harvesting
- ⬜ Múltiples apps nuevas en < 10 min → posible root comprometido

### 3.4 Reentrenamiento continuo con datos móviles

- ⬜ Eventos móviles confirmados → CSV en `media/training/datasets/jorise_lab_mobile/`
- ⬜ Mismo pipeline: `lab_pipeline.py retrain --sources cicids2017,unsw,jorise_lab,jorise_lab_mobile`
- ⬜ Modelo actualizado se distribuye OTA al dispositivo (si implementamos inferencia local)

---

## Fase 4 — Pipeline en Tiempo Real

```
Evento Android
     ↓
  SignalCollector (< 10ms)
     ↓
  RiskEngine reglas locales (< 5ms) → score < 50: solo alerta local
     ↓ score ≥ 50 o evento de alto riesgo
  POST /api/mobile/analyze → Jorise AI (< 500ms en WiFi)
     ↓
  Categoría + score + explicación
     ↓
  score ≥ 50  → Notificación al usuario
  score ≥ 80  → Incidente en SOC + acción automática
```

- ✅ Evaluación local on-demand (`MainActivity`, botón "Verificar ahora")
- ✅ `RiskCard` Compose con colores por nivel (LOW/MEDIUM/HIGH/CRITICAL)
- ✅ `recommendedAction` en lenguaje simple — 4 niveles
- ⬜ Evaluación automática disparada por eventos (no solo manual)
- ⬜ Notificación del sistema con acción directa (fuera de la app)
- ⬜ Score global del dispositivo persistido entre sesiones
- ⬜ Push al SOC cuando score ≥ 80

---

## Fase 5 — Integración con Jorise Core (SOC)

- ✅ `GuardianApiClient.kt` — cliente HTTP base funcional, sin auth
- ⬜ Endpoint `/api/mobile/analyze` en Jorise Core (nuevo, conecta con el modelo)
- ⬜ Endpoint `/api/mobile/incident` — registrar incidente confirmado
- ⬜ Endpoint `/api/mobile/threats` — descargar lista negra actualizada
- ⬜ Autenticación JWT con device token (actualmente sin auth)
- ⬜ Cifrado AES-256-GCM del payload antes de transmitir
- ⬜ Migrar a Retrofit + OkHttp (TODO en el código)
- ⬜ Dashboard SOC: dispositivos registrados, score por device, timeline de incidentes

---

## Fase 6 — Respuesta Automática

- ⬜ Bloquear IP/dominio vía `VpnService`
- ⬜ Solicitar revocación de permiso al usuario
- ⬜ Deshabilitar app vía `DevicePolicyManager` (requiere perfil MDM)
- ⬜ Aislamiento total de red del dispositivo
- ⬜ Ticket automático en SOC con evidencia (snapshot + score + clase Jorise)
- ⬜ Alerta a familiar / cuidador (botón "Avisar a familiar")

---

## Fase 7 — Privacidad y Seguridad

- ✅ `deviceId` = hash de `ANDROID_ID` (primeros 8 chars, no PII)
- ✅ Sin leer mensajes, fotos ni datos privados
- ⬜ Cifrado AES-256-GCM en tránsito hacia Jorise Core
- ⬜ Anonimización de IPs propias antes de enviar
- ⬜ Consentimiento granular por tipo de telemetría
- ⬜ Sin almacenar contenido de notificaciones, solo metadata
- ⬜ Retención máx 30 días para eventos locales

---

## Fase 8 — UI / UX

- ✅ Dashboard con score y nivel de riesgo
- ✅ `RiskCard` con semáforo de colores
- ✅ Mensaje en lenguaje simple (`recommendedAction`)
- ✅ Botón "Verificar ahora"
- ⬜ Mostrar categoría detectada por Jorise ("Detectamos comportamiento tipo Bot")
- ⬜ Historial de incidentes con timeline
- ⬜ Botón "Avisar a familiar" en alertas críticas
- ⬜ Score numérico 0–100 visible
- ⬜ Exportar reporte de incidente (PDF)
- ⬜ Ajuste de tamaño de texto para adultos mayores

---

## Orden de Implementación

```
1. Completar TODOs en SignalCollector.kt
   ├── UsageStatsManager → unknownAppForeground
   ├── PackageManager → newSensitivePermission
   ├── LinkProperties → dnsStandard real
   └── Contador persistido de failed logins

2. Implementar AccessibilityService
   ├── overlayDetected → true cuando hay overlay activo
   ├── App en primer plano
   └── tlsValid desde WebView

3. Endpoint /api/mobile/analyze en Jorise Core
   └── ContextSnapshot → 25 features → Jorise XGBoost → respuesta

4. Conectar GuardianApiClient al nuevo endpoint
   └── Mostrar categoría Jorise en la UI

5. Room DB para historial de eventos

6. BroadcastReceiver (instalación de apps, permisos)

7. Notificaciones del sistema con acción directa

8. Reglas avanzadas en RiskEngine (sideload, bancaria, combos)

9. VpnService para inspección de tráfico

10. Auth JWT + cifrado AES en GuardianApiClient

11. Respuesta automática (bloqueo, aislamiento, ticket SOC)

12. jorise_lab_mobile → reentrenamiento de Jorise con datos móviles reales
```

**MVP ejecutable:** pasos 1–4 — reglas activas + Jorise AI analizando desde el móvil.  
**Sistema completo:** pasos 1–12 — detección, respuesta automática y aprendizaje continuo.

---

## Métricas de Éxito

| Métrica | Objetivo |
|---|---|
| Latencia reglas locales → alerta | < 50ms |
| Latencia Jorise AI (con WiFi) | < 500ms |
| False positive rate | < 5% |
| Detección de overlay attacks | > 90% recall |
| Consumo de batería adicional | < 3% diario |
| Comprensión de alertas (usuarios mayores) | > 80% en tests de usabilidad |
