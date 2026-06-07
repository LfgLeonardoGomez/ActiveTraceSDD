## ADDED Requirements

### Requirement: Soft delete is the default deletion strategy
The system SHALL implement soft delete via a `deleted_at` timestamp. When a record is "deleted", the system MUST set `deleted_at` to the current UTC time. No record shall be physically deleted by application code.

#### Scenario: Soft delete a record
- **WHEN** a delete operation is performed on an existing record
- **THEN** the record's `deleted_at` is set to the current UTC time and the record remains in the database

#### Scenario: Excluded from default queries
- **WHEN** a default repository query is executed after a record is soft deleted
- **THEN** the soft-deleted record is not included in the results

### Requirement: Soft delete is transparent to domain logic
The system SHALL ensure that domain services and routers are unaware of the soft delete mechanism; it is handled entirely at the repository and model mixin level.

#### Scenario: Service layer obliviousness
- **WHEN** a service calls `repository.delete(id)`
- **THEN** the service does not need to know whether the operation is a soft or hard delete

### Requirement: Soft-deleted records are preserved for audit
The system SHALL guarantee that soft-deleted records remain in the database indefinitely (no automatic purge) to support audit and historical analysis.

#### Scenario: Historical query with deleted records
- **WHEN** an explicit query for deleted records is executed
- **THEN** the soft-deleted records are available with their `deleted_at` timestamp
