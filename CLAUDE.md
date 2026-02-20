# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TutorFlow AI is a platform for freelance tutors and small academies in South Korea, inspired by the "Baemin" (delivery marketplace) model. The platform automates booking, payment, and settlement processes while providing a **verified-payment review system** as the core moat.

### Key Business Logic

- **Revenue Model**: 3-5% commission on payments (MVP starts at 5%)
- **Growth Strategy**:
  1. Initially onboard freelance tutors with low/no commission to build review data
  2. Reviews attract parent traffic (parents search for verified tutors)
  3. Parent traffic creates "must be on this platform" necessity for tutors
  4. Increase commission once platform dependency is established

- **Core Moat**: Verified-payment review system (only users who completed payment can write reviews)

### Target Users

- **Primary**: Freelance tutors (ages 25-40, 1-10 years experience, 1:1 or small group 2-5 students)
- **Secondary**: Parents of K-12 students

## Architecture

### Tech Stack (Planned per PRD)

**Backend:**
- FastAPI (Python 3.12+)
- PostgreSQL 16
- SQLAlchemy ORM
- JWT-based stateless authentication (Access Token: 1 hour, Refresh Token: 30 days with rotation)

**Frontend:**
- Next.js 14 (App Router)
- Zustand for state management
- TypeScript

**Infrastructure:**
- AWS EC2 (Ubuntu 22.04)
- GitHub Actions for CI/CD

**External Services:**
- Kakao OAuth 2.0 (login)
- Toss Payments (PG)
- Kakao Alimtalk (notifications)

### Clean Architecture Structure

```
backend/
├── domain/                 # Pure business logic, no external dependencies
│   ├── entities/           # User, Tutor, Student, Booking, Payment, Attendance, Review
│   ├── value_objects/      # Money, Schedule, NoShowPolicy
│   └── ports/              # Protocol interfaces (PaymentPort, NotificationPort, etc.)
├── application/            # UseCases
│   ├── use_cases/          # Business logic orchestration
│   └── dto/                # Data transfer objects
├── infrastructure/         # External implementations
│   ├── persistence/        # SQLAlchemy models, repositories
│   ├── external/           # Adapters for external services
│   └── database.py         # DB connection
└── api/                    # FastAPI route handlers (Presentation Layer)
```

**Key Principles:**
- Port & Adapter Pattern: Domain layer defines interfaces (Protocols), Infrastructure implements them
- SOLID principles strictly followed
- Stateless design: No session servers, JWT only
- All technical decisions require ADR (Architecture Decision Record) in `/docs/adr/`

### Database Schema Highlights

**Core Tables:**
- `users`: Unified table for tutors, students, admins (role-based)
- `tutors`: Extended tutor info (subjects, hourly_rate, no_show_policy, bank info)
- `students`: Extended student info (grade, parent contacts)
- `available_slots`: Tutor available times (day_of_week, start_time, end_time)
- `bookings`: Booking records (total_sessions, completed_sessions, status)
- `booking_sessions`: Individual sessions (session_date, session_time, status)
- `payments`: Payment records (amount, fee_rate, pg_payment_key, status)
- `settlements`: Monthly settlement (year_month, total_amount, net_amount)
- **`reviews`**: Review system (MVP core feature)
  - Verified-payment only: one review per booking
  - Overall rating 1-5 + itemized ratings (kindness, preparation, improvement, punctuality)
  - Anonymous by default
  - Tutor reply support
- **`review_reports`**: Review moderation (spam, abuse, false info reports)

## MVP Scope (Phase 1-2)

### Phase 1: Foundation (Week 1-4)
- Kakao OAuth login
- JWT authentication/authorization
- User, Tutor, Student models
- Basic project setup

### Phase 2: Booking, Payment & Review System (Week 5-8) - MVP CORE
- Booking API (create, read, approve, reject, cancel)
- Toss Payments integration
- **Review System (MVP Essential)**:
  - Verified-payment review creation (only users with completed payment + 1+ session)
  - Review listing with filters (rating, photo reviews)
  - Review reporting/moderation
  - Tutor reply to reviews
  - Daily badge calculation batch (Popular Tutor: 10+ reviews & 4.5+ rating, Best Tutor: 30+ & 4.8+)

## Important Constraints

1. **Review System is NOT Optional**: The verified-payment review system is the core moat. Without it, the platform has no network effect. This is MVP-critical, not a nice-to-have.

2. **Stateless Design**: No session servers. All authentication via JWT tokens stored in HttpOnly cookies.

3. **Payment Security**: Never store card information. Toss Payments handles all sensitive payment data. We only store the `payment_key` for verification.

4. **Prepaid Model**: Students pay upfront before tutor approval. Refunds happen automatically on rejection/cancellation.

5. **No-Show Policies**: Tutors can set policies:
   - FULL_DEDUCTION: Absence counts as a paid session
   - ONE_FREE: One free absence per month, then deduction
   - NONE: Manual handling required

6. **Audit Trail**: All state changes must be logged to `audit_logs` table (entity_type, entity_id, action, old_value, new_value, actor_id, ip_address)

## API Design Standards

**URL Convention:**
```
GET    /api/v1/bookings           # List
GET    /api/v1/bookings/:id       # Detail
POST   /api/v1/bookings           # Create
PATCH  /api/v1/bookings/:id       # Update
DELETE /api/v1/bookings/:id       # Delete
```

**Response Format:**
```json
{
  "success": true,
  "data": { ... },
  "error": null
}
```

**Error Response:**
```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "BOOKING_NOT_FOUND",
    "message": "예약을 찾을 수 없습니다.",
    "details": {}
  }
}
```

## Testing Strategy

- Unit tests: Domain entities and UseCases
- Integration tests: API endpoints
- E2E tests: Playwright for critical flows (login → book → pay → review)
- Load tests: Target 100 req/s for booking API, p95 < 200ms

## Documentation

- **PRD.md**: Full Product Requirements Document with 6 modules
- **Todo.md**: Detailed task list based on 5-phase implementation roadmap
- **market_research.md**: Korean EdTech market analysis
- **ADRs**: All major technical decisions must be documented in `/docs/adr/`

## Development Notes

- Korean language primary (all user-facing text in Korean)
- All currency in KRW (원)
- Timezone: Asia/Seoul
- Minimum booking: 24 hours in advance (no same-day bookings)
- Attendance check deadline: Next day 23:59 (auto-attendance after deadline)
- Monthly settlement: 1st of each month for previous month's completed sessions
