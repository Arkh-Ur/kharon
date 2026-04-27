# 📘 Plan de Implementación

# Kharōn — Plan de Implementación

**Empresa:** Arkh-Ur
**Versión:** 2.0
**Fecha:** 2026-04-27
**Duración Estimada:** 5 semanas (25 días hábiles)
**Equipo:** 2-3 desarrolladores Arkh-Ur

---

## 1. Visión General del Plan

```mermaid
gantt
    title Kharōn — Plan de Implementación v2.0
    dateFormat  YYYY-MM-DD
    axisFormat  %d %b
    
    section Fase 1: Infraestructura
    F1.1 Configurar WSL2 + Ubuntu       :a1, 2026-05-01, 1d
    F1.2 Instalar Airflow 3.x           :a2, after a1, 1d
    F1.3 Crear estructura dirs          :a3, after a2, 1d
    F1.4 Configurar logging base        :a4, after a3, 1d
    F1.5 Verificar Airflow UI           :a5, after a4, 1d
    
    section Fase 2: Motor de Ejecución
    F2.1 Implementar logger.py          :b1, after a5, 1d
    F2.2 Implementar constants.py       :b2, after b1, 1d
    F2.3 Implementar ScriptRunner       :b3, after b2, 2d
    F2.4 Implementar ScriptMonitor      :b4, after b3, 2d
    F2.5 Implementar KharonOperator     :b5, after b4, 2d
    F2.6 Testing unitario motor         :b6, after b5, 1d
    
    section Fase 3: DAGs Base
    F3.1 DAG template base              :c1, after b5, 1d
    F3.2 DAG 01-06 (6 DAGs)            :c2, after c1, 3d
    F3.3 Scripts de soporte             :c3, after c2, 1d
    F3.4 Scripts externos de ejemplo    :c4, after c3, 1d
    F3.5 Testing DAGs                   :c5, after c4, 1d
    
    section Fase 4: Sistema de Clientes
    F4.1 clients_registry.yaml          :d1, after c5, 1d
    F4.2 Actualizar scripts_registry    :d2, after d1, 1d
    F4.3 ClientManager module           :d3, after d2, 1d
    F4.4 Testing clientes               :d4, after d3, 1d
    
    section Fase 5: Webapp Core
    F5.1 config.py + airflow_client.py  :e1, after d3, 2d
    F5.2 Componentes UI (4)             :e2, after e1, 2d
    F5.3 Página Dashboard               :e3, after e2, 1d
    F5.4 Página Ejecutar Scripts        :e4, after e3, 1d
    F5.5 Página Ver Logs                :e5, after e4, 1d
    F5.6 Testing webapp core            :e6, after e5, 1d
    
    section Fase 6: Monitoreo + Salud
    F6.1 Página Monitoreo Global        :f1, after e6, 2d
    F6.2 Página Salud por Cliente       :f2, after f1, 2d
    F6.3 Integración historial JSON     :f3, after f2, 1d
    F6.4 Testing monitoreo              :f4, after f3, 1d
    
    section Fase 7: Auto-Creación
    F7.1 DAGGenerator module            :g1, after f4, 2d
    F7.2 Página Nuevo Script            :g2, after g1, 2d
    F7.3 Crear cliente desde webapp     :g3, after g2, 1d
    F7.4 Testing auto-creación          :g4, after g3, 1d
    
    section Fase 8: Integración + Deploy
    F8.1 start_kharon.sh                :h1, after g4, 1d
    F8.2 Testing E2E completo           :h2, after h1, 2d
    F8.3 Documentación final            :h3, after h2, 1d
    F8.4 Deploy producción              :h4, after h3, 1d
```

---

## 2. Dependencias entre Fases

```mermaid
graph TD
    F1[Fase 1<br/>Infraestructura] --> F2[Fase 2<br/>Motor Ejecución]
    F2 --> F3[Fase 3<br/>DAGs Base]
    F3 --> F4[Fase 4<br/>Clientes]
    F4 --> F5[Fase 5<br/>Webapp Core]
    F5 --> F6[Fase 6<br/>Monitoreo + Salud]
    F6 --> F7[Fase 7<br/>Auto-Creación]
    F7 --> F8[Fase 8<br/>Integración + Deploy]
    
    style F1 fill:#6c757d,color:#fff
    style F2 fill:#4a1a8a,color:#fff
    style F3 fill:#4a1a8a,color:#fff
    style F4 fill:#fd7e14,color:#fff
    style F5 fill:#198754,color:#fff
    style F6 fill:#198754,color:#fff
    style F7 fill:#6f42c1,color:#fff
    style F8 fill:#dc3545,color:#fff
```

---

## 3. Criterios de Aceptación por Fase

| Fase | Criterio de Aceptación | Verificación |
|---|---|---|
| **F1** | `airflow version` retorna 3.x, UI accesible en :8080 | Manual |
| **F2** | Script mock se ejecuta vía KharonOperator con logging y reintentos | Unit test |
| **F3** | `airflow dags list` muestra 6+ DAGs sin errores | CLI |
| **F4** | ClientManager carga 4 clientes y genera badges HTML | Unit test |
| **F5** | Kharōn Webapp muestra DAGs, ejecuta scripts, muestra logs | Manual + E2E |
| **F6** | Monitoreo muestra ejecuciones manuales y programadas | Manual |
| **F7** | Script nuevo se registra y ejecuta en < 5 minutos | E2E test |
| **F8** | `start_kharon.sh` levanta todo y queda accesible | Manual |

---

## 4. Estimación de Esfuerzo

| Fase | Días | % del Total |
|---|---|---|
| F1: Infraestructura | 5 | 10% |
| F2: Motor de Ejecución | 9 | 18% |
| F3: DAGs Base | 7 | 14% |
| F4: Clientes | 4 | 8% |
| F5: Webapp Core | 8 | 16% |
| F6: Monitoreo + Salud | 6 | 12% |
| F7: Auto-Creación | 6 | 12% |
| F8: Integración + Deploy | 5 | 10% |
| **Total** | **50** | **100%** |

### Distribución por Rol

```mermaid
pie title Kharōn — Distribución de Esfuerzo por Rol
    "Backend (Python/Airflow)" : 45
    "Full-stack (Streamlit/API)" : 30
    "DevOps (Infra/Deploy)" : 10
    "QA (Testing)" : 15
```

---
