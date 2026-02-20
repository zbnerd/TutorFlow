# ADR 0001: Use Clean Architecture

## Status
Accepted

## Context
TutorFlow is a complex platform with multiple external integrations (Kakao OAuth, Toss Payments, Kakao Alimtalk). We need a maintainable architecture that separates business logic from external concerns.

## Decision
We adopt Clean Architecture with the following layers:
- **Domain**: Pure business logic, no external dependencies
- **Application**: Use cases orchestrating business logic
- **Infrastructure**: External implementations (database, APIs)
- **API**: FastAPI route handlers (Presentation Layer)

## Consequences
- Business logic is isolated and testable
- External dependencies can be swapped without affecting domain
- Requires more upfront design
- Clear dependency direction: outer layers depend on inner layers

## References
- Clean Architecture by Robert C. Martin
- PRD.md: Architecture section
