# JORISE Precision Risk Framework (Banking Grade)

## 1) Objetivo estrategico

Disenar una capacidad de gestion de riesgos que permita a JORISE:

- detectar patrones de ataque en tiempo real con alta precision,
- entender el contexto del negocio y del proceso afectado,
- priorizar riesgos por impacto operativo y financiero,
- ejecutar respuesta automatica con trazabilidad para auditoria,
- demostrar gobernanza alineada a entorno regulado (banca).

Meta operativa principal:

- Precision alta sin perder recall en amenazas criticas.
- Menos falsos positivos en operaciones sensibles.
- Tiempo de deteccion y contencion medible y auditable.

---

## 2) Principios de diseno

1. Risk-first, not alert-first:
	Cada evento se transforma en riesgo de proceso, no solo en alerta tecnica.

2. Multi-capa de decision:
	Reglas deterministicas + modelos ML + correlacion temporal + contexto de negocio.

3. Explicabilidad obligatoria:
	Cada score debe incluir por que subio, con evidencia verificable.

4. Gobernanza desde el inicio:
	Versionado de reglas/modelos, aprobacion de cambios, y control de drift.

5. Seguridad y privacidad por defecto:
	Minimizacion de datos, cifrado, pseudonimizacion, y retencion controlada.

---

## 3) Arquitectura de precision (end-to-end)

```text
[Fuentes de senales]
Mobile + API + WAF + SIEM + EDR + procesos internos
		  |
		  v
[Ingestion + normalizacion]
Schema canonico de evento y proceso
		  |
		  v
[Feature & Context Engine]
Features tecnicas + features de proceso + criticidad de activo
		  |
		  +----> [Reglas rapidas] (latencia minima)
		  |
		  +----> [Modelos ML] (clasificacion + anomalia + secuencia)
		  |
		  +----> [Motor de correlacion temporal]
						 |
						 v
			 [Risk Fusion Engine]
			 Score unico + categoria + confianza + explicacion
						 |
		  +----------+-----------+
		  |                      |
		  v                      v
[Decision Orchestrator]   [Case Manager]
Acciones automaticas       Evidencia, auditoria, SLA
		  |
		  v
  SOC / Riesgo Operativo / Cumplimiento
```

---

## 4) Modelo unificado de riesgo

### 4.0 Enfasis SIB: riesgo dinamico, no estatico

Para entorno regulado bancario, JORISE adopta una vision anticipativa:

$$
Riesgo = (SuperficieDeAtaque \times Vulnerabilidad) \times (IncentivoAtacante + ContextoExterno)
$$

Esto reemplaza el enfoque estatico de solo `probabilidad x impacto` y habilita deteccion temprana cuando cambia el entorno economico, politico o mediatico.

Componentes SIB:

- Superficie de ataque: APIs, portales, integraciones, canales moviles.
- Vulnerabilidad: CVEs, configuracion, IAM, deuda de parches.
- Incentivo del atacante: valor economico del objetivo, oportunidad, presion de mercado.
- Contexto externo: variables macro, eventos politicos, noticias sectoriales.

### 4.1 Entidad principal: Risk Case

Cada incidente se representa como un `RiskCase` con:

- `risk_case_id`
- `timestamp_inicio`, `timestamp_ultima_actividad`
- `attack_pattern` (ej: phishing, takeover, fraude transaccional)
- `asset_criticidad` (bajo, medio, alto, critico)
- `processo_impactado` (pagos, onboarding, transferencias, etc)
- `likelihood_score` (0-100)
- `impact_score` (0-100)
- `control_strength_score` (0-100)
- `residual_risk_score` (0-100)
- `confidence` (0-1)
- `explainability_payload` (top features, reglas, correlaciones)
- `recommended_action`
- `status` (open, triage, contained, closed)

### 4.2 Formula de riesgo residual

Usar una formula estable y auditable:

$$
ResidualRisk = (w_l \cdot Likelihood + w_i \cdot Impact) \cdot (1 - ControlStrength/100)
$$

Sugerencia inicial:

- $w_l = 0.45$
- $w_i = 0.55$

Razon: en banca, impacto de negocio suele pesar mas.

### 4.4 Cyber Risk Score dinamico (motor anticipativo)

Score operativo diario/semanal para anticipacion:

$$
DynamicRisk = 0.4 \cdot (Exposicion \times Vulnerabilidad) + 0.3 \cdot IncentivoAtacante + 0.3 \cdot ContextoExterno
$$

Notas de implementacion:

- Normalizar cada componente a escala 0-100.
- Calcular por entidad y por proceso (no solo score global).
- Ajustar pesos por segmento (`retail`, `corporate`, `mobile`) tras calibracion historica.

Lectura operacional sugerida:

- 0-29: Bajo
- 30-49: Medio
- 50-69: Alto
- 70-84: Muy alto
- 85-100: Critico anticipado

### 4.3 Niveles de decision

- 0-29: Bajo, monitoreo.
- 30-49: Medio, verificacion automatica adicional.
- 50-69: Alto, alerta SOC + validacion humana.
- 70-84: Muy alto, contencion automatica parcial.
- 85-100: Critico, respuesta automatica completa + escalamiento ejecutivo.

---

## 5) Deteccion de patrones (cualquier situacion)

Para cubrir escenarios no vistos, combinar 4 tecnicas al mismo tiempo:

1. Reglas expertas (known-knowns)
- IOC, firmas conductuales, combinaciones de permisos/eventos.

2. ML supervisado (known attacks)
- XGBoost/LightGBM para clasificar tipo de ataque.

3. Anomalia no supervisada (unknown attacks)
- Isolation Forest / Autoencoder / clustering por segmento de cliente.

4. Deteccion secuencial (attack chains)
- Ventanas temporales + secuencias: HMM/LSTM/Transformer liviano.

Fusion recomendada:

$$
FinalScore = \alpha R_{rules} + \beta R_{ml} + \gamma R_{anomaly} + \delta R_{sequence}
$$

Con calibracion por dominio:

- retail banking,
- corporate banking,
- canales moviles,
- operaciones internas.

---

## 6) Riesgo de procesos (no solo ciber)

Crear taxonomia de procesos criticos:

- Apertura de cuentas
- Login y recuperacion
- Transferencias
- Altas de beneficiarios
- Autorizaciones corporativas
- Cambios de dispositivo
- Soporte y mesa de ayuda

Para cada proceso, mapear:

- amenazas probables,
- controles actuales,
- indicadores adelantados de falla,
- costo de interrupcion,
- impacto regulatorio.

Matriz minima por proceso:

- Probabilidad base
- Impacto financiero
- Impacto reputacional
- Impacto regulatorio
- Impacto en cliente vulnerable
- Fuerza de controles actuales
- Riesgo residual objetivo

### 6.1 Variables contextuales externas (diferencial anticipativo)

Variables que deben alimentar diariamente el `ContextoExterno`:

| Variable | Efecto esperado en riesgo |
|---|---|
| Dolar con alza sostenida | Presion presupuestaria y mayor fraude oportunista |
| Deterioro economico | Incremento de ciberdelito financiero |
| Petroleo/energia al alza | Mayor targeting a infraestructura y servicios criticos |
| Ciclo electoral | Aumento de hacktivismo y campanas de desinformacion |
| Conflictos geopolIticos | Incremento de amenazas sofisticadas/APT |
| Noticias negativas del sector bancario | Mayor probabilidad de campanas dirigidas |

Regla practica:

- Si tres o mas variables se activan en ventana corta, elevar baseline de riesgo de procesos criticos.

---

## 6.2 Triggers predictivos (antes del ataque)

Definir triggers orientados a anticipacion, no reaccion:

1. Trigger economico
- Condicion: variacion tipo de cambio > 5% en 14 dias.
- Accion: elevar riesgo base de fraude y takeover.

2. Trigger mediatico
- Condicion: noticias de filtracion/fraude bancario regional en 7 dias.
- Accion: elevar riesgo de phishing y suplantacion.

3. Trigger politico
- Condicion: periodo electoral activo.
- Accion: elevar riesgo en canales publicos/API y portales.

4. Trigger tecnico
- Condicion: CVE critica en tecnologia bancaria propia o de tercero.
- Accion: alerta critica inmediata + priorizacion de parcheo.

5. Trigger de integracion
- Condicion: alta de nueva fintech/proveedor con permisos amplios.
- Accion: elevar riesgo de cadena de suministro y abuso de API.

---

## 6.3 Escenario de referencia (uso realista)

Senales simultaneas:

- alza de dolar,
- rumores de crisis bancaria,
- nueva integracion fintech,
- proximidad electoral.

Salida esperada del modelo:

- `Riesgo anticipado ALTO/CRITICO` para phishing dirigido, fraude transaccional y ransomware,
- elevacion de monitoreo en procesos de transferencias, alta de beneficiarios y recuperacion de cuenta,
- endurecimiento temporal de controles y aprobaciones.

---

## 7) Precision engineering (subir precision real)

### 7.1 Dataset strategy

- Balance por clase y por canal.
- Etiquetado de alta calidad con doble validacion.
- Hard negatives (eventos parecidos a ataque, pero legitimos).
- Segmentacion por tipo de cliente y horario operativo.

### 7.2 Feature strategy

- Features tecnicas (red, endpoint, app behavior).
- Features transaccionales (monto, frecuencia, desviacion de patron).
- Features de proceso (paso del flujo, actor, autorizador).
- Features de historial (reincidencia, dispositivo, geografia).

### 7.3 Calibration strategy

- Calibrar probabilidades (Platt o Isotonic).
- Umbrales por caso de uso, no un threshold global.
- Re-entrenamiento continuo con control de drift.

---

## 8) MLOps + RiskOps obligatorio

1. Model Registry
- version modelo,
- dataset hash,
- fecha,
- metricas,
- aprobador.

2. Rule Registry
- version de reglas,
- cambio puntual,
- motivo,
- impacto esperado.

3. Shadow deployment
- correr modelo nuevo en paralelo sin afectar produccion.

4. Drift monitoring
- drift de datos,
- drift de prediccion,
- degradacion de precision por clase.

5. Human feedback loop
- decisiones SOC alimentan nuevo etiquetado.

---

## 9) KPI/KRI para superintendencia

KPIs tecnicos:

- Precision global
- Recall en clases criticas
- F1 por tipo de ataque
- AUC-PR (mejor para clases desbalanceadas)
- Latencia p95 de inferencia

KRIs de negocio:

- Tasa de fraude no detectado
- Tasa de falsos positivos en operaciones legitimas
- Tiempo medio de contencion (MTTC)
- Perdida evitada estimada
- Incidentes criticos por proceso

SLA sugeridos:

- Deteccion critica: < 5 segundos
- Contencion automatica: < 30 segundos
- Triage humano: < 10 minutos

---

## 10) Evidencia y auditoria

Cada `RiskCase` debe guardar evidencia estandar:

- input normalizado,
- features derivadas,
- scores parciales por motor,
- score final y threshold aplicado,
- version de modelo y reglas,
- accion ejecutada,
- operador/sistema que aprobo,
- timeline de eventos.

Esto permite:

- trazabilidad regulatoria,
- reproduccion tecnica,
- defensa ante auditoria externa.

---

## 11) Roadmap de implementacion (90 dias)

### Fase A (Dia 1-30): Foundation

- Definir schema canonico de riesgo y `RiskCase`.
- Implementar `Risk Fusion Engine` inicial.
- Crear taxonomia de procesos criticos bancarios.
- Definir umbrales iniciales por proceso.

Entregable:

- Pipeline funcionando con scoring residual auditable.

### Fase B (Dia 31-60): Precision uplift

- Integrar anomalia + secuencia.
- Implementar calibracion de probabilidades.
- Ajustar thresholds por segmento.
- Dashboard KPI/KRI con cortes por proceso.

Entregable:

- Mejor precision sin caida de recall en clases criticas.

### Fase C (Dia 61-90): Governance and regulator readiness

- Model registry + rule registry + aprobaciones.
- Evidencia completa por `RiskCase`.
- Simulacro de auditoria interna.
- Documento de control para ente regulador.

Entregable:

- Paquete de cumplimiento listo para presentar.

---

## 12) Quick wins inmediatos en este repo

1. Crear endpoint unico de riesgo (backend Django):
- `/api/mobile/analyze` + `/api/risk/case`.

2. Implementar fusion de score en backend:
- reglas actuales + salida ML + contexto proceso.

3. Agregar tabla `RiskCase` y `RiskEvidence` en Django.

4. Agregar bitacora de version de modelo/regla.

5. Exponer dashboard inicial de KRIs en modulo SOC/reportes.

6. Incorporar indice `IncentivoAtacante` e `IndiceContextoExterno` con ingestiones diarias.

7. Publicar endpoint de riesgo dinamico por proceso:
- `/api/risk/dynamic-score`.

---

## 12.1 TODO MVP (enfoque anticipativo SIB)

Sprint 1:

1. Definir tabla `RiskContextSnapshot` (fecha, variable, valor, fuente, confianza).
2. Implementar `ContextoExternoService` con score 0-100.
3. Implementar `IncentivoAtacanteService` con score 0-100 por proceso.
4. Exponer `DynamicRiskEngine` con formula ponderada (0.4/0.3/0.3).

Sprint 2:

1. Implementar triggers predictivos (economico, mediatico, politico, tecnico, integracion).
2. Conectar triggers al `Decision Orchestrator` para acciones preventivas.
3. Persistir evidencia de trigger en `RiskEvidence`.
4. Exponer panel semaforo por proceso (`bajo/medio/alto/critico anticipado`).

Sprint 3:

1. Calibrar pesos por proceso con historico local.
2. Medir impacto: reduccion de tiempo de anticipacion y falsos positivos.
3. Definir paquete de evidencia para supervision.
4. Activar ciclo mensual de tuning de umbrales.

---

## 13) Mensaje ejecutivo (one-liner)

JORISE evoluciona de motor de alertas a plataforma de decision de riesgo bancario: detecta patrones de ataque, cuantifica impacto en procesos criticos, y ejecuta respuesta trazable con evidencia para supervision regulatoria.

