# Mastery-First LMS Backend Plan

## Context
- Web-first, single-tenant LMS with Django and DRF.
- Architecture uses a service layer for business logic, separated from views and serializers.
- Existing base includes authentication, courses, modules, and lessons.
- Product focus is mastery-based learning, skill tracking, and adaptive progression.

## Core Domain Entities

### Enrollment
- Responsibilities: represent the user-course lifecycle, gate access to learning content, and anchor progress and grading.
- State machine: `INVITED -> ACTIVE -> COMPLETED` with exits to `WITHDRAWN` or `SUSPENDED`.
- Invariants: one active enrollment per user-course, no progress or attempts without enrollment, and no `COMPLETED -> ACTIVE` without explicit admin override.
- Relationships: FK to `User` and `Course`, one-to-many to `Progress`, one-to-many to `Attempt`, one-to-many to `Mastery`.

### Progress
- Responsibilities: track lesson-level completion and time-on-task with a stable audit trail.
- State machine: `NOT_STARTED -> IN_PROGRESS -> COMPLETED` with optional `RESET -> IN_PROGRESS` by instructor or admin.
- Invariants: `completed_at` only when `COMPLETED`, `time_spent_seconds` is non-decreasing, progress belongs to a single `Enrollment` and `Lesson`.
- Relationships: FK to `Enrollment`, FK to `Lesson`, optional FK to `Attempt` when lesson completion is assessment-based.

### Assessment
- Responsibilities: define evaluatable learning objects with scoring rules and item structure.
- State machine: `DRAFT -> PUBLISHED -> ARCHIVED`.
- Invariants: published assessments are immutable except metadata, total points are positive, and item order is stable.
- Relationships: FK to `Course`, optional FK to `Lesson`, one-to-many to `AssessmentItem`, one-to-many to `Attempt`, optional M2M to `Skill`.

### Attempt
- Responsibilities: capture learner submission lifecycle and grading results.
- State machine: `STARTED -> SUBMITTED -> GRADED`, with `RESUBMITTED` if the assessment allows it.
- Invariants: one active attempt per enrollment-assessment unless explicitly configured, `GRADED` requires score and grader, submission payload is immutable after `SUBMITTED`.
- Relationships: FK to `Enrollment`, FK to `Assessment`, one-to-many to `AttemptAnswer`, optional FK to `Grader`.

### Skill
- Responsibilities: represent competency definitions and mastery thresholds within a course.
- State machine: `DRAFT -> ACTIVE -> ARCHIVED`.
- Invariants: active skills cannot be deleted if referenced by mastery or assessments, threshold structure is valid and complete.
- Relationships: FK to `Course`, optional M2M to `Assessment`.

### Mastery
- Responsibilities: track an enrollment's competency level and evidence.
- State machine: `NOT_EVALUATED -> EMERGING -> PROFICIENT -> MASTERED` with upward-only transitions unless overridden by instructor or admin.
- Invariants: level is monotonic by default, evidence must reference a valid attempt or portfolio artifact, and mastery thresholds are consistent per skill.
- Relationships: FK to `Enrollment`, FK to `Skill`, optional FK to `Attempt` or `PortfolioArtifact`.

## Service Layer Architecture
- Enrollment service: owns invites, activation, withdrawal, suspension, and access gating for course content.
- Progress service: owns lesson start, completion, time tracking, and course completion computation.
- Assessment service: owns assessment authoring, publish lifecycle, and item validation.
- Attempt service: owns attempt creation, submission validation, and resubmission rules.
- Grading service: owns auto-grading, rubric application, manual grading, and gradebook aggregation.
- Skill service: owns skill definitions, mastery evaluation, and evidence linking.
- Recommendation service: owns adaptive release rules and next-lesson selection.
- Analytics service: owns precomputed metrics, dashboards, and exports as read models.
- Notification service: owns in-app notifications derived from domain events.

## Data Model Design (High-Level)
- Enrollment: `status`, `invited_at`, `activated_at`, `completed_at`, `suspended_at`; FKs to `User` and `Course`.
- Progress: `status`, `started_at`, `completed_at`, `time_spent_seconds`, `last_activity_at`; FKs to `Enrollment` and `Lesson`.
- Assessment: `type`, `status`, `title`, `total_points`, `time_limit_seconds`, `attempt_limit`; FK to `Course`, optional FK to `Lesson`.
- AssessmentItem: `prompt`, `kind`, `points`, `order`, `answer_key`; FK to `Assessment`.
- Attempt: `status`, `started_at`, `submitted_at`, `graded_at`, `score`, `feedback`; FK to `Enrollment`, FK to `Assessment`, optional FK to `Grader`.
- AttemptAnswer: `answer`, `is_correct`, `points_awarded`; FK to `Attempt`, FK to `AssessmentItem`.
- Skill: `name`, `description`, `thresholds_json`, `order`; FK to `Course`.
- Mastery: `level`, `evidence_type`, `evidence_id`, `updated_at`; FK to `Enrollment` and `Skill`.
- PortfolioArtifact: `title`, `type`, `url_or_blob`, `submitted_at`; FK to `Enrollment`.

## Workflows

### Enrollment Flow
1. Enrollment service creates `Enrollment` in `INVITED` or `ACTIVE`.
2. Activation transitions to `ACTIVE`, unlocking content access.
3. Withdrawal or suspension transitions to `WITHDRAWN` or `SUSPENDED` and revokes access.
4. Course completion transitions to `COMPLETED` and freezes progress updates.

### Lesson Completion Flow
1. Progress service creates `Progress` in `IN_PROGRESS` on lesson start.
2. Time-on-task is accumulated with monotonic updates.
3. Completion transitions to `COMPLETED` and emits a mastery evaluation event if relevant.

### Assessment Attempt Flow
1. Attempt service creates `Attempt` in `STARTED`.
2. Submission transitions to `SUBMITTED` after validation.
3. Objective items are auto-graded; subjective items wait for manual grading.

### Grading Flow
1. Grading service loads `SUBMITTED` attempts and applies rubric or auto-grading.
2. Graded attempts transition to `GRADED` with score and feedback.
3. Gradebook aggregation updates derived metrics via domain events.

### Mastery Update Flow
1. Skill service evaluates evidence from attempts or portfolio artifacts.
2. Mastery level transitions upward based on thresholds.
3. Recommendation service updates adaptive release and next-lesson suggestions.

## Phased Implementation Plan
- Phase 0: Domain modeling, service boundaries, and domain event definitions. Blocks all phases.
- Phase 1: Enrollment and Progress services with full state transitions. Blocks assessment and mastery work.
- Phase 2: Assessment and Attempt services with submission validation. Blocks grading and mastery.
- Phase 3: Grading service with gradebook aggregation. Blocks mastery-driven progression.
- Phase 4: Skill and Mastery services with adaptive release rules. Blocks personalization analytics.
- Phase 5: Recommendation and Analytics services with precomputed read models. Depends on phases 1-4.
- Phase 6: Governance and content operations (audit logs, soft deletes, versioning). Parallel after phase 1.

## Performance and Scalability
- Use transactions for enrollment creation, attempt submission, and grading to keep transitions atomic.
- Use row-level locks for concurrent attempt submissions or grade updates.
- Precompute aggregates for dashboards and gradebooks; update via domain events.
- Avoid N+1 by using `select_related` and `prefetch_related` in service queries.
- Keep derived fields (progress percent, mastery summaries) in read models, not core tables.

## Permissions Model
- DRF permissions enforce coarse access (authenticated, instructor, admin).
- Service-layer authorization enforces context rules (instructor owns course, student is enrolled, attempt is in correct state).
- Admin overrides are explicit and audited in service methods.

## Testing Strategy
- Service tests for state transitions, invariants, and authorization.
- Permission tests for DRF permission classes and context rules.
- End-to-end workflow tests for enrollment, lesson completion, attempts, grading, and mastery updates.

## Common Design Mistakes to Avoid
- Treating domain operations as CRUD without explicit transitions.
- Placing business rules in views or serializers instead of services.
- Allowing state changes that bypass invariants (for example `COMPLETED -> ACTIVE`).
- Overloading a single service file instead of domain-focused modules.
