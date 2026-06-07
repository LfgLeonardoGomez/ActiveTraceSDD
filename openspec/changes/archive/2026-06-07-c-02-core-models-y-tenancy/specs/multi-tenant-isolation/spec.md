## ADDED Requirements

### Requirement: BaseRepository enforces tenant scope
The system SHALL provide a `BaseRepository` that requires a `tenant_id` for all queries. If `tenant_id` is missing, the repository MUST raise an error. The repository SHALL filter by `tenant_id` automatically in every query.

#### Scenario: Query with valid tenant scope
- **WHEN** a repository query is executed with a valid `tenant_id`
- **THEN** only records belonging to that tenant are returned

#### Scenario: Query without tenant scope fails
- **WHEN** a repository query is attempted without providing a `tenant_id`
- **THEN** the repository raises a `ValueError` or equivalent exception

### Requirement: Cross-tenant data isolation
The system SHALL guarantee that a query scoped to tenant A never returns records from tenant B.

#### Scenario: Multi-tenant isolation test
- **WHEN** two records with identical business data but different `tenant_id` values exist
- **THEN** a query scoped to tenant A returns only the tenant A record

#### Scenario: No implicit cross-tenant joins
- **WHEN** a repository performs a join across tables
- **THEN** the tenant scope is applied to all joined tables automatically

### Requirement: Tenant scope is fail-closed
The system SHALL treat any query that bypasses tenant scoping as a bug. No method on `BaseRepository` shall execute a query without an explicit `tenant_id`.

#### Scenario: Explicit override required for unscoped queries
- **WHEN** an unscoped query is attempted
- **THEN** it fails unless an explicit dangerous override flag is set
