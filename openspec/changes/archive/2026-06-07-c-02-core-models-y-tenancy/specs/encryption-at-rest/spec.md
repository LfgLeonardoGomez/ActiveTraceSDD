## ADDED Requirements

### Requirement: AES-256 encryption helper for PII
The system SHALL provide `encrypt_pii(plain_text: str) -> str` and `decrypt_pii(cipher_text: str) -> str` helpers that use AES-256-GCM. The encrypted output SHALL be base64-encoded and include the nonce and authentication tag. Decryption SHALL fail with a clear error if the ciphertext is tampered with.

#### Scenario: Encrypt sensitive field
- **WHEN** a PII field (e.g., DNI, CBU, email) is encrypted with `encrypt_pii`
- **THEN** the resulting ciphertext is non-deterministic (different nonce each time) and base64-encoded

#### Scenario: Decrypt sensitive field
- **WHEN** a valid ciphertext is decrypted with `decrypt_pii`
- **THEN** the original plain text is restored exactly

#### Scenario: Tamper detection
- **WHEN** a ciphertext is modified and then decrypted
- **THEN** the system raises a decryption error indicating tampering or corruption

### Requirement: Encrypted fields never appear in logs
The system SHALL ensure that encrypted PII fields are never logged or returned in API responses in plain text.

#### Scenario: Log inspection
- **WHEN** application logs are inspected after processing a record with encrypted fields
- **THEN** no plain text PII values appear in the logs
