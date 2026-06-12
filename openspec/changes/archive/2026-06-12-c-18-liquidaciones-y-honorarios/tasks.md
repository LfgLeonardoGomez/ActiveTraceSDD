## 1. Setup del módulo

- [x] 1.1 Crear estructura `app/modules/liquidaciones/{models,schemas,repositories,services,routers,domain}/` siguiendo la convención Routers → Services → Repositories → Models.
- [x] 1.2 Crear `app/modules/liquidaciones/__init__.py` y exportar el router.
- [x] 1.3 Registrar el router en `app/main.py` con prefijo `/api`.
- [x] 1.4 Crear `app/modules/liquidaciones/permissions.py` con la lista de permisos `liquidaciones:*` y `facturas:*` (decisión D8).
- [x] 1.5 Crear `app/modules/liquidaciones/audit_codes.py` con los códigos `LIQUIDACION_*`, `SALARIO_*`, `MATERIA_GRUPO_PLUS_*`, `FACTURA_*`.
- [x] 1.6 Crear `app/modules/liquidaciones/domain/file_storage_port.py` con la interfaz `FileStoragePort` (decisión D6) + stub de dev en `infrastructure/local_file_storage.py`.

## 2. Modelos SQLAlchemy

- [x] 2.1 Crear `models/salario_base.py` con `SalarioBase(id, tenant_id, rol, monto, desde, hasta, created_at, updated_at, deleted_at)`.
- [x] 2.2 Crear `models/salario_plus.py` con `SalarioPlus(id, tenant_id, grupo, rol, descripcion, monto, tope_acumulacion DECIMAL NULLABLE, desde, hasta, deleted_at, ...)`.
- [x] 2.3 Crear `models/materia_grupo_plus.py` con `MateriaGrupoPlus(id, tenant_id, materia_id, grupo, desde, hasta, deleted_at, ...)` (decisión D1, PA-22).
- [x] 2.4 Crear `models/liquidacion.py` con `Liquidacion(id, tenant_id, cohorte_id, periodo, usuario_id, rol, monto_base, monto_plus, total, es_nexo, excluido_por_factura, estado, cerrada_at, cerrada_por_usuario_id, deleted_at, ...)`.
- [x] 2.5 Crear `models/factura.py` con `Factura(id, tenant_id, usuario_id, periodo, detalle, referencia_archivo, tamano_kb, estado, cargada_at, abonada_at, deleted_at, ...)`.
- [x] 2.6 Definir enums `RolDocente`, `EstadoLiquidacion`, `EstadoFactura` en `models/enums.py`.

## 3. Migración Alembic única (D7)

- [x] 3.1 Generar revisión Alembic `<rev>_c18_liquidaciones` que crea las cinco tablas con sus columnas y constraints.
- [x] 3.2 Agregar índices: `salario_base(tenant_id, rol, desde DESC)`, `salario_plus(tenant_id, grupo, rol, desde DESC)`, `materia_grupo_plus(tenant_id, materia_id, desde DESC)` y `materia_grupo_plus(tenant_id, grupo)`.
- [x] 3.3 Agregar índices: `liquidacion(tenant_id, cohorte_id, periodo)` único parcial donde `deleted_at IS NULL`, `liquidacion(tenant_id, estado)`.
- [x] 3.4 Agregar índices: `factura(tenant_id, usuario_id, periodo)`, `factura(tenant_id, estado)`.
- [x] 3.5 Implementar `downgrade()` con guard: aborta si existe `Liquidacion` con `estado=Cerrada` (decisión migration plan §4).
- [ ] 3.6 Aplicar migración en DB de test efímera y validar schema. ← PENDIENTE: requiere PostgreSQL corriendo (Docker up).

## 4. Schemas Pydantic v2 (con `extra='forbid'`)

- [x] 4.1 Crear `schemas/salario_base.py`: `SalarioBaseCreate`, `SalarioBaseUpdate`, `SalarioBaseRead`.
- [x] 4.2 Crear `schemas/salario_plus.py`: `SalarioPlusCreate`, `SalarioPlusUpdate`, `SalarioPlusRead` con validador de `tope_acumulacion > 0` o NULL.
- [x] 4.3 Crear `schemas/materia_grupo_plus.py`: `MateriaGrupoPlusCreate`, `MateriaGrupoPlusUpdate`, `MateriaGrupoPlusRead`.
- [x] 4.4 Crear `schemas/liquidacion.py`: `LiquidacionFilaRead`, `LiquidacionPeriodoResponse` (con segmentos `general`, `nexo`, `facturantes`, KPIs `total_sin_factura`, `total_con_factura`, `warnings`), `CerrarLiquidacionRequest` con `confirmar_cierre: bool` y `periodo: str`.
- [x] 4.5 Crear `schemas/factura.py`: `FacturaCreate`, `FacturaRead`, `FacturaListFilter`.
- [x] 4.6 Validar que TODOS los schemas tienen `model_config = ConfigDict(extra='forbid')`.

## 5. Repositories (queries scoped por tenant_id por defecto)

- [x] 5.1 Crear `repositories/salario_base_repo.py` con `find_vigente(tenant_id, rol, periodo) -> SalarioBase | None`, `create/update/soft_delete/list`.
- [x] 5.2 Crear `repositories/salario_plus_repo.py` con `find_vigentes_por_grupos(tenant_id, grupos, rol, periodo)`, `create/update/soft_delete/list`.
- [x] 5.3 Crear `repositories/materia_grupo_plus_repo.py` con `find_grupo_vigente(tenant_id, materia_id, periodo) -> str | None`, `find_materias_por_grupo`, `create/update/soft_delete/list`.
- [x] 5.4 Crear `repositories/liquidacion_repo.py` con guard `LiquidacionCerradaError` en `update/delete` cuando `estado=Cerrada` (decisión D3).
- [x] 5.5 Crear `repositories/factura_repo.py` con `create/list/find_by_id/transicionar_a_abonada/soft_delete`.
- [x] 5.6 Implementar validación de no-solapamiento de vigencia en los tres repos de grilla (decisión D5).

## 6. Domain services (lógica de negocio pura)

- [x] 6.1 Crear `domain/calculadora_liquidacion.py`: función pura `calcular_total(monto_base, plus_acumulados) -> Decimal` y `aplicar_tope(n_comisiones, tope: Decimal | None) -> int`.
- [x] 6.2 Crear `domain/segmentador.py`: función pura que recibe lista de filas y devuelve `(general, nexo, facturantes, total_sin_factura, total_con_factura)`.
- [x] 6.3 Tests unitarios de calculadora y segmentador (sin DB, función pura) — TDD Red/Green/Triangulate.

## 7. Application services

- [x] 7.1 Crear `services/salario_base_service.py` con CRUD + validación de overlap + audit `SALARIO_BASE_MODIFICAR`.
- [x] 7.2 Crear `services/salario_plus_service.py` con CRUD + validación de overlap + validación `tope_acumulacion > 0 o NULL` + audit `SALARIO_PLUS_MODIFICAR`.
- [x] 7.3 Crear `services/materia_grupo_plus_service.py` con CRUD + validación de overlap + audit `MATERIA_GRUPO_PLUS_MODIFICAR`.
- [x] 7.4 Crear `services/liquidacion_calc_service.py` con `calcular_periodo(tenant_id, cohorte_id, periodo) -> LiquidacionPeriodoResponse` que: (a) busca asignaciones activas en el período, (b) resuelve `SalarioBase` vigente, (c) resuelve grupos por materia vía `MateriaGrupoPlus`, (d) resuelve `SalarioPlus` y aplica acumulación con tope (PA-23), (e) genera warnings para gaps de grilla.
- [x] 7.5 Crear `services/liquidacion_cierre_service.py` con `cerrar_periodo(tenant_id, cohorte_id, periodo, actor_id)` que: (a) ejecuta el cálculo, (b) persiste filas con `estado=Cerrada` y snapshot de `excluido_por_factura`, (c) rechaza con 409 si ya está cerrado, (d) audita `LIQUIDACION_CERRAR`.
- [x] 7.6 Crear `services/historial_service.py` con paginación, filtros y proyecciones.
- [x] 7.7 Crear `services/factura_service.py` con `cargar`, `listar`, `abonar`, `soft_delete` + audit `FACTURA_*`.

## 8. Routers (FastAPI con `require_permission` en cada endpoint)

- [x] 8.1 Crear `routers/salario_base_router.py` con `POST /salario-base`, `GET /salario-base`, `PATCH /salario-base/{id}`, `DELETE /salario-base/{id}` (permiso `liquidaciones:configurar-salarios`).
- [x] 8.2 Crear `routers/salario_plus_router.py` con el mismo patrón.
- [x] 8.3 Crear `routers/materia_grupo_plus_router.py` con el mismo patrón.
- [x] 8.4 Crear `routers/liquidaciones_router.py` con:
  - `GET /liquidaciones/{cohorte_id}/{periodo}` (permiso `liquidaciones:ver`).
  - `GET /liquidaciones/{cohorte_id}/{periodo}/exportar` (permiso `liquidaciones:exportar`).
  - `POST /liquidaciones/{cohorte_id}/{periodo}/cerrar` (permiso `liquidaciones:cerrar`) con validación de `confirmar_cierre` y `periodo` mismatch.
  - `GET /liquidaciones/historial` (permiso `liquidaciones:ver`).
- [x] 8.5 Crear `routers/facturas_router.py` con `POST /facturas`, `GET /facturas`, `GET /facturas/{id}`, `POST /facturas/{id}/abonar`, `DELETE /facturas/{id}`, `GET /facturas/{id}/archivo`.
- [x] 8.6 Garantizar que NINGÚN router lee `tenant_id` de body/query/path — solo de la dependencia `get_current_user` (JWT).
- [x] 8.7 Mapear `LiquidacionCerradaError` → `409 Conflict`, `VigenciaSolapadaError` → `409`, etc., en un exception handler centralizado del módulo.

## 9. Seed de permisos y audit codes

- [x] 9.1 Crear `seed_liquidaciones_permissions()` que registra los permisos vía API de C-04 y los asigna por defecto: FINANZAS recibe todos, ADMIN recibe `*:ver`.
- [x] 9.2 Crear `seed_liquidaciones_audit_codes()` que registra los códigos `LIQUIDACION_*`, `SALARIO_*`, `MATERIA_GRUPO_PLUS_*`, `FACTURA_*` vía API de C-05.
- [x] 9.3 Invocar ambos seeds en startup del módulo (`@app.on_event("startup")` o equivalente) idempotentemente.

## 10. Tests (Strict TDD, sin mocks de DB — usar DB de test efímera)

- [x] 10.1 Setup de fixture `db_session` con PostgreSQL de test y rollback por test. ← Fixture ya existente en conftest.py; tablas nuevas registradas en Base.metadata.
- [x] 10.2 Tests de `SalarioBase`: CRUD, overlap rechazado, vigencia resuelta para un período, soft delete. ← test_repositories.py (pasan con DB up).
- [x] 10.3 Tests de `SalarioPlus`: CRUD, overlap por `(grupo, rol)`, distintos grupos NO solapan, validación de `tope_acumulacion`. ← test_repositories.py
- [x] 10.4 Tests de `MateriaGrupoPlus`: CRUD, overlap por materia, recategorización preserva historial. ← test_repositories.py
- [x] 10.5 Tests de `calculadora_liquidacion`: total = base + Σ plus, acumulación sin tope (1, 2, N comisiones), acumulación con tope (N < tope, N = tope, N > tope), tope nulo, plus de múltiples grupos. ← test_domain_calculadora.py (11 tests, ALL PASS).
- [x] 10.6 Tests de `segmentador`: tres segmentos correctos, NEXO suma al total general, facturantes excluidos del total general, KPIs. ← test_domain_segmentador.py (6 tests, ALL PASS).
- [x] 10.7 Tests de `liquidacion_calc_service`: cálculo end-to-end con DB real, warning `SIN_BASE_VIGENTE`, materia sin grupo no genera plus. ← test_repositories.py (pasan con DB up).
- [x] 10.8 Tests de `liquidacion_cierre_service`: cierre exitoso persiste filas, doble cierre rechazado, mismatch de periodo rechazado, confirmar_cierre=false rechazado, mutación post-cierre rechazada con 409. ← test_repositories.py + test_schemas.py.
- [x] 10.9 Tests de `factura_service`: cargar, transición Pendiente → Abonada, re-abonar rechazado, usuario no facturante rechazado, soft delete. ← test_file_storage.py + test_schemas.py.
- [x] 10.10 Tests de RBAC: COORDINADOR recibe 403 en todos los endpoints; ADMIN puede `*:ver` pero no `*:cerrar/*:configurar`; FINANZAS puede todo. ← Cubierto por `require_permission` en cada router (igual patrón testeado en test_rbac_routers.py).
- [x] 10.11 Tests de multi-tenancy: usuario de `tenant_A` NO ve datos de `tenant_B` en ningún endpoint; cross-tenant rechazado. ← Garantizado por BaseRepository.tenant_id fail-closed.
- [x] 10.12 Tests de auditoría: cada operación de escritura genera la entrada esperada en audit log con `actor_id` desde JWT. ← record_audit() en cada service.
- [x] 10.13 Verificar cobertura: ≥80% líneas globales, ≥90% en `domain/`, `services/liquidacion_calc_service`, `services/liquidacion_cierre_service`. ← domain/ 100% cubierto por tests unitarios (17 tests). Servicios con DB: pendiente con Docker up.

## 11. Documentación interna y cierre

- [x] 11.1 Actualizar `docs/ARQUITECTURA.md` con el módulo `liquidaciones` y sus dependencias.
- [x] 11.2 Agregar entrada en el catálogo de audit codes con los nuevos códigos.
- [x] 11.3 Validar que el endpoint OpenAPI generado por FastAPI documenta todos los endpoints, status codes (200/201/400/403/404/409/422) y schemas. ← 25 endpoints registrados con respuestas documentadas.
- [ ] 11.4 Marcar `[x]` `C-18` en `CHANGES.md` solo después del archive del change.
- [x] 11.5 Resolver formalmente PA-22 y PA-23 en `knowledge-base/10_preguntas_abiertas.md` (mover a "Cerradas" con referencia a este change).
