## Why

El equipo de FINANZAS no tiene hoy una forma sistematizada de calcular y cerrar los honorarios docentes del período: el cálculo Base + Plus se ejecuta manualmente por fuera del sistema, sin trazabilidad, sin inmutabilidad de los períodos cerrados, sin separación contable entre docentes en relación de dependencia y facturantes, y sin auditoría de cierres. Además, las grillas salariales no están versionadas: un cambio retroactivo en el monto de un rol o de un plus rompe la consistencia histórica. Este change incorpora el módulo de Liquidaciones y Honorarios — el dominio contable núcleo del producto — cerrando previamente las preguntas abiertas **PA-22** (mapeo materia → grupo de Plus) y **PA-23** (acumulación y tope de Plus) que lo bloqueaban.

## What Changes

- **Nuevos modelos** (con `tenant_id`, soft delete, vigencia temporal donde aplica):
  - `SalarioBase`: monto base por rol (`PROFESOR | TUTOR | NEXO | COORDINADOR`) con `desde / hasta` (RN-31, RN-32).
  - `SalarioPlus`: monto plus por `(grupo, rol)` con `desde / hasta` y **`tope_acumulacion DECIMAL NULLABLE`** (PA-23: NULL = sin tope; valor = máximo de acumulaciones permitidas) (RN-31, RN-33).
  - **`MateriaGrupoPlus`** (PA-22): mapeo histórico `(materia_id → grupo)` con vigencia `desde / hasta`. Vive en el módulo de liquidaciones (no en estructura-academica) para preservar el historial ante recategorización de la materia.
  - `Liquidacion`: `(tenant_id, cohorte_id, periodo AAAA-MM, usuario_id, rol)` con `monto_base`, `monto_plus`, `total`, `es_nexo`, `excluido_por_factura`, `estado ∈ {Abierta, Cerrada}` (RN-21, RN-22, RN-37).
  - `Factura`: ABM de comprobantes de docentes facturantes con `estado ∈ {Pendiente, Abonada}` y archivo adjunto (RN-35, RN-39, RN-40).
- **Cálculo de liquidación del período (FL-08, RN-34)**:
  - Base por rol vigente en `(periodo)` (RN-32, RN-31).
  - Plus por cada `(grupo × rol)` aplicable según las `MateriaGrupoPlus` activas para las materias de las comisiones asignadas en el período.
  - Acumulación: `N × Plus(grupo, rol)` donde `N = min(N_comisiones_del_grupo, tope_acumulacion)` (PA-23). Si `tope_acumulacion` es NULL, acumula sin tope.
  - Total = `monto_base + Σ(monto_plus)`.
  - Segmentación tripartita en la vista (RN-36, RN-38, F10.6): general (PROFESOR / TUTOR / COORDINADOR), NEXO (separado pero suma), facturantes (excluidos del total).
- **Endpoints REST** bajo `/api/liquidaciones/*` y `/api/facturas/*`, todos guarded por `require_permission("liquidaciones:*")` y restringidos al rol FINANZAS (con ADMIN solo lectura donde aplique).
- **Cierre inmutable** (RN-22): al cerrar una liquidación, sus filas pasan a `Cerrada` y el sistema rechaza toda mutación (409). Se emite un evento de auditoría `LIQUIDACION_CERRAR`.
- **Facturas** (F10.5): ABM con filtros por docente / estado / período, transición `Pendiente → Abonada`, archivo adjunto persistido vía `referencia_archivo` (storage opaco) y tamaño registrado.
- **Migración Alembic única** que crea las cinco tablas (`salario_base`, `salario_plus`, `materia_grupo_plus`, `liquidacion`, `factura`).
- **Audit events**: `LIQUIDACION_CERRAR`, `LIQUIDACION_CALCULAR`, `SALARIO_BASE_MODIFICAR`, `SALARIO_PLUS_MODIFICAR`, `MATERIA_GRUPO_PLUS_MODIFICAR`, `FACTURA_CARGAR`, `FACTURA_ABONAR`.

## Capabilities

### New Capabilities
- `grilla-salarial`: ABM de grilla salarial (Base + Plus + mapeo Materia → Grupo) con vigencia temporal y reglas de no superposición. Cubre F10.4, RN-31, RN-32, RN-33 y las decisiones PA-22 / PA-23.
- `liquidaciones`: cálculo, vista, cierre inmutable, historial y segmentación contable de las liquidaciones del período `(cohorte × mes)`. Cubre F10.1, F10.2, F10.3, F10.6, FL-08, RN-21, RN-22, RN-34, RN-36, RN-37, RN-38.
- `facturas-docentes`: ABM de comprobantes de docentes facturantes con transición `Pendiente → Abonada` y archivo adjunto. Cubre F10.5, RN-35, RN-39, RN-40.

### Modified Capabilities
<!-- Ninguna. Este change introduce dominio nuevo y solo agrega códigos al catálogo de auditoría (E-AUD ya existe en C-05). -->

## Impact

- **Código nuevo**: módulo `app/modules/liquidaciones/` (routers, services, repositories, schemas, models) siguiendo la estructura unidireccional Routers → Services → Repositories → Models.
- **Base de datos**: cinco tablas nuevas con FKs a `tenant`, `cohorte`, `materia`, `usuario` y `comision`. Una sola migración Alembic.
- **RBAC**: nuevos permisos en el catálogo (no requiere migración del módulo C-04, solo seed): `liquidaciones:calcular`, `liquidaciones:ver`, `liquidaciones:exportar`, `liquidaciones:cerrar`, `liquidaciones:configurar-salarios`, `facturas:cargar`, `facturas:abonar`, `facturas:ver`. Asignados por defecto al rol FINANZAS; ADMIN obtiene lectura. Fail-closed.
- **Audit log (C-05)**: nuevos códigos `LIQUIDACION_*`, `SALARIO_*`, `MATERIA_GRUPO_PLUS_*`, `FACTURA_*` agregados al catálogo cerrado de acciones (RN-24).
- **Dependencias resueltas** (precondiciones): C-01 foundation, C-02 multi-tenancy, C-03 auth, C-04 RBAC, C-05 audit-log, C-06 estructura-academica (Materia, Carrera, Cohorte, Comision), modelo `Usuario` con `facturador: bool` y datos bancarios cifrados (de C-03 / C-04).
- **Frontend** (C-22 o posterior, fuera del scope de este change backend): consumirá `/api/liquidaciones/*` y `/api/facturas/*` para F10.1–F10.6.
- **Sin impacto en Moodle / N8N**: este dominio no integra con sistemas externos.
- **Governance**: este change es **CRÍTICO** (liquidaciones es dominio contable y de pagos). Todos los artefactos requieren revisión humana antes de `/opsx:apply`.
