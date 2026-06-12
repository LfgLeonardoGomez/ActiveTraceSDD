# Mensajería Inbox Specification

## Purpose
Internal messaging between registered users via an inbox. Threads are tree-structured via `parent_id` on a single `Mensaje` table. Tenant-scoped and independent from the outbound email system (`Comunicacion`).

## Requirements

### Requirement: Inbox thread listing
The authenticated user MUST list root messages (`parent_id IS NULL`) where the user is the recipient, ordered by the most recent reply timestamp.

#### Scenario: List inbox threads
- GIVEN an authenticated user with permission `mensajeria:leer`
- WHEN `GET /api/v1/inbox`
- THEN 200 with root messages scoped to the user's tenant

#### Scenario: Empty inbox
- GIVEN an authenticated user with no messages
- WHEN `GET /api/v1/inbox`
- THEN 200 with empty list

#### Scenario: Tenant isolation in inbox
- GIVEN a root message in tenant A
- WHEN a user from tenant B requests `GET /api/v1/inbox`
- THEN the message is not present (404 if accessed by ID directly)

### Requirement: Read thread with replies
The user MUST read a thread by ID, returning the root message and all descendant replies ordered by `created_at` ascending.

#### Scenario: Read thread successfully
- GIVEN an authenticated user with `mensajeria:leer` who is the recipient or sender of the root
- WHEN `GET /api/v1/inbox/{id}`
- THEN 200 with root message and all replies

#### Scenario: Thread not addressed to user
- GIVEN a thread where the user is neither recipient nor sender
- WHEN `GET /api/v1/inbox/{id}`
- THEN 403 forbidden

### Requirement: Reply in thread
The user MUST reply to a thread by creating a new `Mensaje` with `parent_id` pointing to the root message. The reply inherits the same `tenant_id`.

#### Scenario: Reply to thread
- GIVEN an authenticated user with permission `mensajeria:responder` who is recipient or sender of the root
- WHEN `POST /api/v1/inbox/{id}/responder` with `{"asunto": "...", "cuerpo": "..."}`
- THEN 201 with new message, `parent_id = root.id`, audit `MENSAJE_RESPONDER` logged

#### Scenario: Reply to non-existent thread
- GIVEN an authenticated user
- WHEN `POST /api/v1/inbox/{nonexistent}/responder`
- THEN 404 not found

#### Scenario: Reply to thread from another tenant
- GIVEN a root message in tenant A
- WHEN a user from tenant B attempts to reply
- THEN 404 not found

### Requirement: Soft delete of messages
Messages MUST support soft delete via `deleted_at`. A deleted message and its replies MUST NOT appear in inbox or thread responses.

#### Scenario: Deleted thread hidden
- GIVEN a root message with `deleted_at` set
- WHEN any user requests `GET /api/v1/inbox` or `GET /api/v1/inbox/{id}`
- THEN the thread is excluded from results

## Permissions
- `mensajeria:leer` — granted to all authenticated users
- `mensajeria:responder` — granted to all authenticated users

## Audit Codes
- `MENSAJE_RESPONDER` — logged on every successful reply
