# TutorFlow AI - Implementation Todo List

이 문서는 PRD의 Implementation Roadmap (Phase 1-5)를 기반으로 한 구체적인 할 일 목록입니다.

---

## Brand Identity

**Primary Colors:**
- **Sky Blue**: `#C7EAE4` - 주요 배경, 헤더, 넓은 영역
- **Mint Green**: `#A7E8BD` - 강조 색상, 버튼, 카드, 하이라이트

---

## Phase 1: Foundation (Week 1-4)
**Goal:** 인프라 구축, 기본 기능 구현

### Backend
- [x] 프로젝트 초기 세팅 (FastAPI, PostgreSQL)
- [ ] 카카오 로그인 구현
  - [ ] 카카오 OAuth 2.0 연동
  - [ ] JWT Access Token 발행 (1시간 만료)
  - [ ] JWT Refresh Token 발행 (30일 만료, Rotation)
  - [ ] Token 저장 (HttpOnly Cookie)
- [ ] JWT 인증/인가 구현
  - [ ] 로그인된 사용자 확인 미들웨어
  - [ ] Role-based access control (TUTOR, STUDENT, ADMIN)
- [ ] User, Tutor, Student 모델
  - [ ] users 테이블 (공통)
  - [ ] tutors 테이블 (강사 추가 정보)
  - [ ] students 테이블 (학생 추가 정보)
  - [ ] available_slots 테이블 (강사 가능 시간대)
- [ ] API 스펙 작성 (OpenAPI/Swagger)

### Frontend
- [ ] Next.js 14 프로젝트 세팅 (App Router)
- [ ] 로그인 페이지
  - [ ] 카카오 로그인 버튼
  - [ ] OAuth 콜백 처리
- [ ] 레이아웃 및 공통 컴포넌트
  - [ ] Header (네비게이션)
  - [ ] Footer
  - [ ] Button, Input 등 기본 UI 컴포넌트

### Infrastructure
- [ ] AWS EC2 세팅 (Ubuntu 22.04)
- [ ] PostgreSQL 16 배포
  - [ ] DB 생성
  - [ ] 사용자 및 권한 설정
  - [ ] 백업 스크립트
- [ ] CI/CD 파이프라인 (GitHub Actions)
  - [ ] 테스트 자동 실행
  - [ ] 배포 자동화

---

## Phase 2: Booking & Payment (Week 5-8)
**Goal:** 예약 및 결제 기능 구현 + **리뷰 시스템 (MVP 필수)**

### Backend
- [ ] 예약 API
  - [ ] 예약 생성 (POST /api/v1/bookings)
  - [ ] 예약 목록 조회 (GET /api/v1/bookings)
  - [ ] 예약 상세 조회 (GET /api/v1/bookings/:id)
  - [ ] 예약 승인 (PATCH /api/v1/bookings/:id/approve)
  - [ ] 예약 거절 (PATCH /api/v1/bookings/:id/reject)
  - [ ] 예약 취소 (DELETE /api/v1/bookings/:id)
- [ ] 토스페이먼츠 연동
  - [ ] 결제 요청 API 연동
  - [ ] 결제 검증 API 연동
  - [ ] 웹훅 수신 처리
- [ ] 결제 검증 로직
  - [ ] payment_key 검증
  - [ ] 결제 금액 확인
  - [ ] 예약 상태 업데이트
- [ ] 예약 가능 시간대 관리
  - [ ] 요일별 시간대 설정
  - [ ] 중복 예약 방지
  - [ ] 최소 24시간 전 예약 규칙

### Backend - **리뷰 시스템 (MVP 필수)**
- [ ] 리뷰 API
  - [ ] 리뷰 작성 (POST /api/v1/reviews)
    - [ ] 실결제자 권한 검증 (결제 완료 AND 수업 1회 이상)
    - [ ] 1 예약당 1 리뷰 제한
  - [ ] 리뷰 조회 (GET /api/v1/reviews)
    - [ ] 강사별 리뷰 목록
    - [ ] 평점 필터 (높은 순, 많은 리뷰 순)
    - [ ] 사진 있는 리뷰 필터
  - [ ] 리뷰 수정 (PATCH /api/v1/reviews/:id) - 작성 후 7일 이내
  - [ ] 리뷰 삭제 (DELETE /api/v1/reviews/:id)
- [ ] 리뷰 신고 API
  - [ ] 신고 생성 (POST /api/v1/reviews/:id/report)
  - [ ] 관리자 신고 목록 조회
  - [ ] 신고 처리 (승인/거절)
- [ ] 강사 댓글 API
  - [ ] 댓글 작성 (POST /api/v1/reviews/:id/reply)
- [ ] 강사 평점 계산 배치
  - [ ] 매일 전체 강사 평점 재계산
  - [ ] 뱃지 자동 부여 로직
    - [ ] 인기 강사 (리뷰 10+ AND 4.5+)
    - [ ] 베스트 강사 (리뷰 30+ AND 4.8+)
    - [ ] 답변 왕 (댓글 80%+ 응답)
- [ ] 리뷰 테이블
  - [ ] reviews 테이블 생성
  - [ ] review_reports 테이블 생성
  - [ ] 인덱스 생성

### Frontend
- [ ] 강사 프로필 페이지
  - [ ] 강사 기본 정보 표시
  - [ ] **평점, 리뷰 개수 표시**
  - [ ] **뱃지 표시 (인기 강사, 베스트 강사 등)**
  - [ ] 가능한 시간대 표시
- [ ] 예약 페이지
  - [ ] 달력 UI (date picker)
  - [ ] 시간대 선택
  - [ ] 수업 횟수 입력
  - [ ] 결제 금액 계산
- [ ] 결제 페이지
  - [ ] 토스페이먼츠 SDK 연동
  - [ ] 카드 결제 UI
- [ ] 예약 관리 대시보드
  - [ ] 예약 요청 목록 (강사)
  - [ ] 예약 현황 (학생)
- [ ] **리뷰 시스템 UI**
  - [ ] **강사 상세 페이지**
    - [ ] 리뷰 탭
    - [ ] 평점 필터
    - [ ] 사진 있는 리뷰 필터
    - [ ] 항목별 평가 그래프 (친절도, 준비성 등)
  - [ ] **리뷰 작성 페이지**
    - [ ] 별점 선택 (1-5점)
    - [ ] 항목별 평가 (친절도, 준비성, 성과, 시간준수)
    - [ ] 텍스트 리뷰 입력 (10-500자)
    - [ ] 사진 첨부 (최대 3장)
    - [ ] 익명 여부 선택
  - [ ] **리뷰 관리 페이지 (강사)**
    - [ ] 내 리뷰 목록
    - [ ] 리뷰 신고하기
    - [ ] 리뷰에 댓글 달기

---

## Phase 3: Attendance & Notification (Week 9-12)
**Goal:** 출결 관리 및 알림 기능

### Backend
- [ ] 출결 API
  - [ ] 출석 체크 (PATCH /api/v1/attendance/:session_id)
  - [ ] 결석 처리 (PATCH /api/v1/attendance/:session_id/no-show)
  - [ ] 출결 현황 조회
- [ ] 노쇼 정책 처리 로직
  - [ ] 전액 차감 정책
  - [ ] 1회 면제 정책
  - [ ] 설정 안함 정책
- [ ] 카카오 알림톡 연동
  - [ ] 템플릿 등록
    - [ ] 수업 리마인드 (24시간 전)
    - [ ] 예약 승인 알림
    - [ ] 결제/환불 알림
    - [ ] 출석 체크 리마인더
  - [ ] 발송 API 구현
- [ ] 배치 jobs (Celery/RQ)
  - [ ] 수업 24시간 전 리마인더 발송
  - [ ] 출석 체크 리마인더 발송 (익일 12시)

### Frontend
- [ ] 출석 체크 페이지
  - [ ] 오늘의 수업 목록
  - [ ] 출석/결석 버튼
  - [ ] 노쇼 정책 안내
- [ ] 출결 현황 페이지
  - [ ] 학생: 본인 출결, 잔여 횟수
  - [ ] 강사: 전체 학생 출결, 월간 출석률
- [ ] 알림 설정 페이지
  - [ ] 알림 수신 동의

---

## Phase 4: Settlement & Refund (Week 13-16)
**Goal:** 정산 및 환불 기능

### Backend
- [ ] 월간 정산 배치
  - [ ] 매월 1일 자동 실행
  - [ ] 전월 완료 수업 집계
  - [ ] 정산 금액 계산 (수업료 - 수수료 5% - PG사 3%)
- [ ] 환불 계산 API
  - [ ] 잔여 수업일 기반 환불액 계산
  - [ ] 환불 가이드 제공
- [ ] 정산 내역 조회
  - [ ] 월간 정산 내역 (강사)
  - [ ] 수익 대시보드
- [ ] 입금 처리 (은행 API)
  - [ ] 강사 계좌로 자동 입금
  - [ ] 입금 결과 이메일 발송

### Frontend
- [ ] 환불 요청 페이지
  - [ ] 환불 가능 금액 표시
  - [ ] 환불 사유 입력
- [ ] 정산 내역 페이지
  - [ ] 월간 수입
  - [ ] 수수료 내역
  - [ ] 입금 상태
- [ ] 수익 대시보드
  - [ ] 월간/연간 수입 그래프
  - [ ] 예약 통계

---

## Phase 5: Beta Launch & Optimization (Week 17-20)
**Goal:** 베타 런칭 및 안정화

### QA
- [ ] E2E 테스트 작성 (Playwright)
  - [ ] 회원가입/로그인
  - [ ] 예약부터 결제까지
  - [ ] 출결 체크
  - [ ] 리뷰 작성/조회
- [ ] 부하 테스트 (Locust)
  - [ ] 예약 동시 요청 100 req/s
  - [ ] API 응답시간 p95 < 200ms 검증
- [ ] 보안 audit
  - [ ] JWT 토큰 보안
  - [ ] SQL Injection 테스트
  - [ ] XSS 방지

### Launch
- [ ] 베타 테스터 모집 (20명)
  - [ ] 프리랜서 강사 15명
  - [ ] 학부모 5명
- [ ] 피드백 수집 및 개선
  - [ ] 주간 피드백 세션
  - [ ] 버그 픽스
- [ ] 마케팅 준비
  - [ ] 랜딩 페이지
  - [ ] SNS 계정 생성

### Metrics
- [ ] Analytics 연동
  - [ ] Google Analytics 4
  - [ ] Mixpanel (이벤트 트래킹)
- [ ] 대시보드 구축 (Grafana)
  - [ ] API 모니터링
  - [ ] DB 모니터링
  - [ ] 서버 리소스 모니터링

---

## 리뷰 시스템 관련 추가 작업 (전 Phase)

### Database
- [x] reviews 테이블 설계
- [x] review_reports 테이블 설계
- [ ] 리뷰 관련 인덱스 생성
- [ ] 리뷰 마이그레이션 스크립트

### Backend - Domain Layer
- [ ] Review 엔티티 (domain/entities/review.py)
- [ ] ReviewReport 엔티티
- [ ] Rating 값 객체 (1-5점 제한)

### Backend - Application Layer
- [ ] CreateReviewUseCase
- [ ] GetReviewsUseCase (필터 포함)
- [ ] UpdateReviewUseCase
- [ ] DeleteReviewUseCase
- [ ] ReportReviewUseCase
- [ ] ReplyToReviewUseCase
- [ ] CalculateTutorRatingUseCase

### Backend - Infrastructure Layer
- [ ] ReviewRepository (SQLAlchemy)
- [ ] ReviewReportRepository

### Frontend - Components
- [ ] ReviewCard 컴포넌트
- [ ] ReviewForm 컴포넌트
- [ ] RatingStars 컴포넌트
- [ ] ReviewFilter 컴포넌트
- [ ] Badge 컴포넌트

### Moderation
- [ ] 비속어 필터링 (Python profanity 라이브러리)
- [ ] 연락처 감지 (정규식)
- [ ] 광고성 텍스트 감지
- [ ] 관리자 리뷰 관리 페이지

---

## 향후 확장 (Post-MVP)

### 리뷰 시스템 고도화
- [ ] 리뷰 사진 라이트박스
- [ ] 리뷰 공유 기기 (SNS)
- [ ] 리뷰 베스트 선정 및 포상
- [ ] AI 기반 리뷰 분석 (감성 분석)
- [ ] 리뷰를 통한 강사 매칭 추천

### 검색 및 발견
- [ ] 강사 검색 (과목, 지역, 평점)
- [ ] 지도 기반 검색
- [ ] 추천 강사 (AI 기반)

---

**참고:** 이 Todo 리스트는 PRD의 Implementation Roadmap을 기반으로 작성되었으며, 리뷰 시스템은 MVP의 핵심 기능으로 포함되어 있습니다. 리뷰 시스템이 플랫폼의 성장을 위한 핵심 해자(Moat)가 될 것입니다.
