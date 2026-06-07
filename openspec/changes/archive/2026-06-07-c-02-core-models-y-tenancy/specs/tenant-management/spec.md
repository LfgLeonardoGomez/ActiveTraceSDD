## ADDED Requirements

### Requirement: Tenant model exists and is queryable
The system SHALL provide a `Tenant` entity with at least: `id` (UUID PK), `nombre` (text, non-empty), `slug` (text, unique per system), `activo` (boolean, default true), `configuracion` (JSONB, nullable), `created_at`, `updated_at`.

#### Scenario: Tenant creation
- **WHEN** a new tenant is created with valid `nombre` and `slug`
- **THEN** the tenant is persisted with a generated UUID `id` and current timestamps

#### Scenario: Tenant slug uniqueness
- **WHEN** a tenant is created with a `slug` that already exists
- **THEN** the system rejects the creation with a uniqueness violation error

### Requirement: Tenant seed on bootstrap
The system SHALL ensure at least one default tenant exists in the database after migration and application startup.

#### Scenario: Fresh database bootstrap
- **WHEN** the application starts against an empty database
- **THEN** a default tenant is present in the `tenants` table

## ADDED Requirements

### Requirement: Base model mixin provides core fields
The system SHALL provide a `BaseModelMixin` that adds `id` (UUID PK), `tenant_id` (UUID FK → tenants.id), `created_at` (timestamp), `updated_at` (timestamp), and `deleted_at` (nullable timestamp) to every domain model.

#### Scenario: Model instantiation with mixin
- **WHEN** a domain model inheriting from `BaseModelMixin` is instantiated
- **THEN** it contains `id`, `tenant_id`, `created_at`, `updated_at`, and `deleted_at` attributes

#### Scenario: Timestamp auto-population
- **WHEN** a record is inserted into the database
- **THEN** `created_at` and `updated_at` are set to the current UTC time

#### Scenario: Soft delete field is nullable by default
- **WHEN** a record is created
- **THEN** `deleted_at` is NULL
