# Comentarios de Tarea Specification

## Purpose
Comments on internal tasks.

## Requirements

### Requirement: Comment CRUD
The system MUST allow creating, reading, and soft-deleting comments on tasks.

#### Scenario: Add comment
- GIVEN a task exists
- WHEN an authorized user adds a comment
- THEN the comment is persisted and linked to the task

#### Scenario: Soft delete comment
- GIVEN a comment exists
- WHEN the author or an admin soft deletes it
- THEN deleted_at is set and the comment is excluded from listings

#### Scenario: Unauthorized delete
- GIVEN a comment by another user
- WHEN a non-admin user tries to delete it
- THEN the system returns 403

### Requirement: Comment Listing
The system MUST list non-deleted comments for a task.

#### Scenario: List comments
- GIVEN a task with comments
- WHEN a user reads the task
- THEN all non-deleted comments are returned in chronological order
