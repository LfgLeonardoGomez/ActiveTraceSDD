# Admin Usuarios

## Purpose
Manage tenant users.

## Requirements

| ID | Requirement | Scenarios |
|---|---|---|
| R1 | User List: The UI MUST list users with nombre, email, roles, estado. | GIVEN an ADMIN user, WHEN the page loads, THEN a table shows all users. |
| R2 | User Detail: The UI MUST show a panel with DNI, CUIL, CBU, banco, regional. | GIVEN a user row, WHEN clicked, THEN a panel shows fields. |
| R3 | Edit User: The UI MUST allow editing nombre, email, regional, banco, estado. | GIVEN a user, WHEN edited and saved, THEN the list updates. |
| R4 | Roles: The UI MUST display roles from Asignaciones as badges. | GIVEN a user with multiple roles, WHEN viewed, THEN badges show all roles. |
