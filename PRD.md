# TutorFlow AI - Product Requirements Document

**Version:** 1.0
**Date:** 2025-02-20
**Status:** Draft
**Product Owner:** TutorFlow Team

---

## Brand Identity

**Primary Colors:**
- **Sky Blue**: `#C7EAE4` - 주요 배경, 헤더, 넓은 영역
- **Mint Green**: `#A7E8BD` - 강조 색상, 버튼, 카드, 하이라이트

These colors reflect trust, growth, and learning - fitting for an education platform.

---

## 1. Product Vision & Objectives

### 1.1 Vision Statement
프리랜서 강사와 소규모 학원을 위한 **배달의민족 모델**의 교육 플랫폼으로, 예약·결제·정산 자동화와 **실결제자 기반 인증 리뷰 시스템**을 통해 강사는 학생을 모으고, 학부모는 신뢰할 수 있는 강사를 찾을 수 있다.

### 1.2 Problem Statement
**강사/학원 입장:**
- **행정 업무 부담**: 예약 관리, 결제 확인, 출결 체크, 환불 계산 등에 주 5-10시간 소요
- **노쇼 손실**: 사전 연락 없는 결석으로 인한 수입 손실 (월 평균 10-15%)
- **정산 복잡도**: 수업별, 학생별 결제 금액, 잔여 수업, 환불액 계산의 번거로움
- **환불 분쟁**: 잔여 수업일 계산 오류로 인한 학부모와의 갈등
- **신규 학생 확보 어려움**: 카카오톡 채널만으로는 신뢰도를 전달하기 어렵고, 입소문 전파 속도가 느림

**학부모 입장:**
- **강사 선택의 어려움**: 네이버 카페, 맘카페, 블로그 뒤지며 후기 찾아야 함
- **후기 신뢰도 문제**: 광고성 후기와 실제 후기를 구별하기 어려움
- **정보 비대칭**: 강사의 실력, 교육 스타일, 커리큘럼을 사전에 파악하기 어려움

### 1.3 Solution Objectives
1. 예약부터 정산까지 엔드투엔드 자동화로 행정 시간 80% 감소
2. 자동 리마인드 알림으로 노쇼율 50% 감소
3. 잔여 수업일 기반 스마트 환불 가이드로 분쟁 70% 감소
4. **실결제자 기반 인증 리뷰 시스템**으로 강사의 신뢰도 구축, 학부모의 강사 선택 시간 70% 감소
5. 리뷰와 평점이 쌓이면 자연스럽게 신규 학생 유입되는 선순환 구조 창출

### 1.4 Business Model
- **수익 모델**: 결제 금액의 3~5% 수수료 (MVP는 5% 시작)
- **타겟 세그먼트**: 프리랜서 강사 (1차) → 소규모 학원 (2차)
- **결제 방식**: 선불 (Prepaid) 모델
- **성장 전략 (배달의민족 모델)**:
  1. 초기: 프리랜서 강사를 무료/저수수료로 모아 리뷰 데이터 확보
  2. 리뷰가 쌓이면 학부모가 검색하러 방문 (학부모 트래픽 유입)
  3. 학부모 트래픽이 생기면 강사/학원이 "여기 안 올리면 손해" 인식
  4. 플랫폼 의존도가 높아진 후 수수료 인상 가능
- **핵심 해자 (Moat)**: 실결제자 기반 인증 리뷰 시스템 (결제 완료한 사람만 리뷰 작성 가능)

---

## 2. User Personas & Jobs-To-Be-Done

### 2.1 Primary Persona: 프리랜서 강사 (Tutor)

**Demographics:**
- 연령: 25-40세
- 경력: 1-10년
- 수업 형태: 1:1 개인 레슨 또는 소그룹 (2-5명)
- 월 수입: 200-500만 원
- 주당 수업: 20-40시간

**Goals:**
- 행정 업무 시간을 줄이고 수업에 집중하고 싶다
- 노쇼로 인한 손실을 방지하고 싶다
- 환불 요청 시 명확한 근거를 제시하고 싶다
- 월말 정산을 간단히 끝내고 싶다

**Pain Points:**
- 카카오톡으로 예약을 받다가 중복/누락이 발생
- 수업 전날 학생이 연락 없이 안 오는 경우가 잦음
- 수업 환불 시 잔여 횟수 계산을 직접 해야 해서 번거로움
- 월말마다 엑셀로 수업별 정산표 만드는 것에 지침

**JTBD (Jobs-To-Be-Done):**
1. "나는 학생의 수업 예약 요청을 빠르게 확인하고 승인/거절하고 싶다"
2. "나는 수업 24시간 전에 학생에게 자동으로 리마인드 알림을 보내고 싶다"
3. "나는 학생이 수업에 출석/결석했는지 한 번의 클릭으로 기록하고 싶다"
4. "나는 환불 요청 시 잔여 수업일에 따른 환불액을 자동으로 계산하고 싶다"
5. "나는 월간 수입, 수업 횟수, 노쇼 횟수 등을 한눈에 보고 싶다"

### 2.2 Secondary Persona: 학생/학부모 (Student/Parent)

**Demographics:**
- 학생 연령: K-12 (초등~고등학생)
- 학부모 연령: 35-50세
- 지역: 서울/경기 등 대도시
- 과외 경험: 1-5년

**Goals:**
- 강사의 가능한 시간을 쉽게 확인하고 예약하고 싶다
- 수업 시간을 잊지 않고 알림을 받고 싶다
- 환불 시 공정하게 처리되는지 확인하고 싶다
- 나의 수업 현황(잔여 횟수, 출결)을 실시간으로 확인하고 싶다
- **실제 수강한 학부모의 리뷰를 보고 신뢰할 수 있는 강사를 선택하고 싶다**

**Pain Points:**
- 강사의 가능한 시간을 카톡으로 일일이 물어봐야 함
- 수업 시간을 잊어버려 노쇼가 되는 경우가 있음
- 환불 시 잔여 수업 계산이 불투명해 억울할 때가 있음
- 현재까지 몇 회 수업을 들었는지 확인하기 어려움
- **강사 선택 시 네이버 카페, 맘카페 뒤지며 후기 찾아야 하는데 광고인지 진짜인지 구별 안 됨**

**JTBD:**
1. "나는 강사의 가능한 시간대를 달력에서 보고 예약하고 싶다"
2. "나는 수업 전날 알림을 받아 시간을 잊지 않고 싶다"
3. "나는 예약 취소/환불 시 환불액을 미리 확인하고 싶다"
4. "나는 나의 출결 현황과 잔여 수업 횟수를 언제든 확인하고 싶다"
5. "나는 **실제 수강한 학부모가 쓴 리뷰**를 보고 신뢰할 수 있는 강사를 찾고 싶다"

---

## 3. Functional Requirements (MVP Scope)

### 3.1 Module 1: 인증 & 프로필 관리

**FR-1.1 카카오 로그인**
- 시스템: 카카오 OAuth 2.0
- 필수 정보: 닉네임, 이메일, 프로필 이미지
- 추가 정보: 전화번호 (알림톡 발송용)
- JWT 토큰 발행 (Access Token: 1시간, Refresh Token: 30일)

**FR-1.2 강사 프로필**
- 기본 정보: 이름, 소개, 프로필 이미지
- 수업 정보: 과목, 지역, 수업료 (시간당/회당)
- 노쇼 정책 설정:
  - 노쇼 시 전액 차감 / 1회 면제 / 설정 안함
  - 당일 취소 기준 (N시간 전까지 무료 취소)
- 가능한 시간대 설정: 요일별 시간대 (월~일, 09:00-21:00)

**FR-1.3 학생 프로필**
- 기본 정보: 학생 이름, 학년, 학부모 연락처
- 수업 정보: 현재 수업 중인 강사 목록

### 3.2 Module 2: 예약 관리

**FR-2.1 예약 가능 시간대 조회**
- 강사의 설정된 가능 시간대를 달력으로 표시
- 이미 예약된 시간대는 예약 불가 표시
- 최소 예약 기간: 당일 예약 불가, 최소 24시간 전

**FR-2.2 예약 요청 (학생)**
- 수업 일시, 횟수, 과목 선택
- 선불 결제: 예약 승인 전 결제 진행
- 결제 대기 상태로 전환

**FR-2.3 예약 승인/거절 (강사)**
- 예약 요청 목록 조회
- 승인 시: 수업 확정, 알림톡 발송
- 거절 시: 결제 금액 자동 환불, 사유 입력

**FR-2.4 예약 취소**
- 학생 요청 취소:
  - 수업 24시간 전: 전액 환불
  - 24시간 이내: 강사 설정에 따라 (노쇼 정책 참조)
- 강사 취소: 전액 환불, 사유 입력

### 3.3 Module 3: 결제 & 정산

**FR-3.1 결제 처리 (토스페이먼츠)**
- 결제 수단: 카드 (MVP)
- 결제 금액: (시간당 수업료 × 횟수) + 수수료(5%)
- 결제 대기 → 승인 완료 → 정산 대기

**FR-3.2 정산 자동화**
- 정산 주기: 매월 1일
- 정산 대상: 전월 완료된 수업
- 정산 금액: (수업료 총액) - (수수료 5%) - (PG사 수수료 약 3%)
- 강사 계좌로 자동 입금 (에스크로 거쳐서)
- 정산 내역 이메일 발송

**FR-3.3 환불 처리**
- 환불 기준: 잔여 수업일 × 회당 수업료
- 환불 가이드 자동 계산:
  - 총 결제 금액: 500,000원 (10회 × 50,000원)
  - 완료된 수업: 3회 = 150,000원
  - 환불 대상: 7회 × 50,000원 = 350,000원
- 환불 요청 시 환불액 미리 보여주기
- 실제 환불 처리는 수동 (강사 확인 후 관리자 처리)

### 3.4 Module 4: 출결 관리

**FR-4.1 출석 체크 (강사)**
- 수업 완료 후 출석/결석 선택
- 출석: 수업 1회 완료로 처리, 정산 대상
- 결석: 노쇼 정책에 따라 처리
- 출석체크 마감: 수업일 익일 23:59까지 (이후 자동 출석)

**FR-4.2 노쇼 처리**
- 강사 설정에 따른 자동 처리:
  - 전액 차감: 결석으로 처리, 수업 횟수 차감
  - 1회 면제: 월 1회 결석 무료, 이후 차감
  - 설정 안함: 수동 처리 필요

**FR-4.3 출결 현황 조회**
- 학생: 본인의 출결 현황, 잔여 횟수
- 강사: 전체 학생 출결 현황, 월간 출석률

### 3.5 Module 5: 알림 시스템

**FR-5.1 수업 리마인드 알림**
- 발송 시점: 수업 24시간 전
- 발송 대상: 학생/학부모
- 내용: 수업 일시, 장소, 취소/연락처

**FR-5.2 예약 승인 알림**
- 발송 시점: 강사가 예약 승인 시
- 발송 대상: 학생/학부모
- 내용: 예약 확정 일시, 수업 횟수

**FR-5.3 결제/환불 알림**
- 결제 완료, 환불 완료 시 알림톡 발송

**FR-5.4 출석 체크 리마인더**
- 발송 시점: 수업일 익일 12:00 (미체크 시)
- 발송 대상: 강사
- 내용: 출석 체크 요청

### 3.6 Module 6: 리뷰 시스템 (MVP 필수)

**FR-6.1 리뷰 작성 권한**
- **실결제자 기반 인증**: 결제를 완료하고 수업 1회 이상 완료한 학부모만 리뷰 작성 가능
- 1개의 예약(Booking)당 1회 리뷰 작성 가능
- 익명 작성 지원 (학생 이름 노출 X)
- 별점 평가: 1~5점 (강사 친절도, 수업 만족도, 성과 improvement)

**FR-6.2 리뷰 내용**
- 별점: 전체 평점 (1-5점)
- 항목별 평가 (선택):
  - 강사 친절도
  - 수업 준비성
  - 성과 개선도
  - 시간 준수
- 텍스트 리뷰 (최소 10자, 최대 500자)
- 사진 첨부 (선택, 최대 3장)

**FR-6.3 리뷰 관리 (강사)**
- 리뷰 조회: 본인 강사에 대한 모든 리뷰
- 리뷰 신고: 부적절한 리뷰 관리자에게 신고 가능
- 리뷰 댓글: 학부모 리뷰에 강사가 답변 가능 (1회)

**FR-6.4 리뷰 검증 & 모더레이션**
- 자동 필터링: 비속어, 연락처, 광고성 내용 자동 차단
- 신고 처리: 관리자가 신고된 리뷰 검토 후 삭제/보존 결정
- 리뷰 수정: 작성 후 7일 이내에만 수정 가능

**FR-6.5 강사 평점 및 뱃지**
- 누적 평점: 전체 리뷰의 평균 별점
- 리뷰 수: 총 리뷰 개수 표시
- 뱃지 시스템:
  - 신규 강사: 리뷰 0개
  - 인기 강사: 리뷰 10개 이상 AND 평균 4.5점 이상
  - 베스트 강사: 리뷰 30개 이상 AND 평균 4.8점 이상
  - 답변 왕: 리뷰 댓글 80% 이상 응답

**FR-6.6 리뷰 검색 및 필터**
- 평점 순 정렬: 높은 평점 순, 많은 리뷰 순
- 최신 리뷰 우선 표시
- 사진 있는 리뷰만 보기
- 항목별 필터: "성과 개선도 좋은 리뷰" 등

---

## 4. Non-Functional Requirements

### 4.1 Architecture Requirements

**NFR-4.1.1 Stateless Design**
- 세션 서버 사용 금지
- JWT 기반 인증 only
- 서버 인스턴스 간 상태 공유 없이 확장 가능

**NFR-4.1.2 Clean Architecture**
```
┌─────────────────────────────────────────────────────────────┐
│                   Presentation Layer                        │
│  (Next.js Pages, Components, API Route Handlers)           │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   Application Layer                         │
│  (UseCases: BookingUseCase, PaymentUseCase, ...)           │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                      Domain Layer                           │
│  (Entities: Tutor, Student, Booking, Payment, Attendance)  │
│  (Value Objects: Money, Schedule, NoShowPolicy)            │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   Infrastructure Layer                      │
│  (Adapters: DB, TossPayments, KakaoAPI, EmailService)      │
└─────────────────────────────────────────────────────────────┘
```

**NFR-4.1.3 Port & Adapter Pattern**
- Domain Layer는 외부 의존성 없이 순수 Python
- Interface(Protocol)를 통한 의존성 역전
```python
# Domain Layer
class PaymentPort(Protocol):
    def process_payment(self, amount: Money, card_info: CardInfo) -> PaymentResult: ...

# Infrastructure Layer
class TossPaymentAdapter(PaymentPort):
    def process_payment(self, amount: Money, card_info: CardInfo) -> PaymentResult:
        # 토스페이먼츠 API 호출
```

**NFR-4.1.4 SOLID Principles**
- **SRP**: 각 클래스/함수는 단 하나의 책임만
- **OCP**: 기능 확장은 열려있고, 수정은 닫혀있음
- **LSP**: 자식 클래스는 부모 클래스를 대체 가능
- **ISP**: 클라이언트는 사용하지 않는 인터페이스에 의존하지 않음
- **DIP**: 상위 모듈은 하위 모듈에 의존하지 않음 (추상화에 의존)

**NFR-4.1.5 ADR (Architecture Decision Record)**
- 모든 기술적 의사결정은 코드 작성 전에 ADR 문서화
- ADR 위치: `/docs/adr/`
- 형식:
  - [ADR-001] 카카오 OAuth 2.0 선택 (vs 네이버, 구글)
  - [ADR-002] 토스페이먼츠 선택 (vs KG이니시스, 나이스페이)
  - [ADR-003] PostgreSQL 선택 (vs MySQL, MongoDB)
  - [ADR-004] Clean Architecture 적용
  - [ADR-005] JWT Refresh Token Rotation

### 4.2 Performance Requirements

**NFR-4.2.1 Response Time**
- API 응답: p95 < 200ms, p99 < 500ms
- 페이지 로드: p95 < 2s (3G)
- 예약 조회: 캐시 적용, p95 < 100ms

**NFR-4.2.2 Throughput**
- 동시 예약 처리: 100 req/s
- 월간 예약 건수: 10,000건 (단일 서버)

**NFR-4.2.3 Database**
- 인덱스: 자주 조회하는 필드 (tutor_id, student_id, booking_date)
- 쿼리 최적화: N+1 방지, JOIN 최적화
- 커넥션 풀: SQLAlchemy (max_overflow=20, pool_size=10)

### 4.3 Security Requirements

**NFR-4.3.1 Authentication & Authorization**
- JWT Access Token: 1시간 만료
- JWT Refresh Token: 30일 만료, Rotation 방식
- Token 저장: HttpOnly Cookie (CSRF 방지)
- 권한: Role-based access control (TUTOR, STUDENT, ADMIN)

**NFR-4.3.2 Data Protection**
- HTTPS only (TLS 1.3)
- 민감 정보 암호화: 전화번호, 계좌번호 (AES-256)
- DB 접근: 환경변수로 관리, .gitignore에 .env 포함
- SQL Injection: SQLAlchemy ORM 사용만으로 방지

**NFR-4.3.3 Payment Security**
- 결제 정보 직접 저장 금지
- 토스페이먼츠가 결제 정보 관리
- PCI-DSS 준수 (토스페이먼츠 인증)
- 웹훅 signature 검증

**NFR-4.3.4 API Security**
- Rate Limiting: 100 req/min per IP
- CORS: 프론트엔드 도메인만 허용
- Request Validation: Pydantic v2 모델로 엄격한 검증
- Error Response: 민감 정보 노출 금지

### 4.4 Reliability Requirements

**NFR-4.4.1 Availability**
- 가동률 목표: 99.5% (월간 약 3.6시간 다운타임 허용)
- 장애 복구: 1시간 이내

**NFR-4.4.2 Data Consistency**
- ACID 트랜잭션: 결제, 예약, 출결 변경 시
- 감사 트레일: 모든 상태 변경 이력 기록
- 정산 배치: 트랜잭션으로 원자성 보장

**NFR-4.4.3 Backup & Recovery**
- DB 백업: 일일 1회 (새벽 2시)
- 백업 보관: 30일
- 복구 테스트: 월 1회

### 4.5 Scalability Requirements

**NFR-4.5.1 Horizontal Scaling**
- Stateless 서버: EC2 인스턴스 추가만으로 확장
- Load Balancer: AWS ALB (Round-robin)

**NFR-4.5.2 Database Scaling**
- Read Replica: 조회 쿼리 분리 (추후)
- Partitioning: 예약 테이블을 월별로 파티셔닝 (추후)

**NFR-4.5.3 Caching**
- Redis: 예약 가능 시간대 캐시 (TTL 10분)
- 정산 결과 캐시 (TTL 1시간)

---

## 5. Technical Architecture

### 5.1 System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         Client Layer                           │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │              Next.js 14 (App Router)                      │  │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────────┐  │  │
│  │  │ Tutor   │  │ Student │  │ Login   │  │ Admin       │  │  │
│  │  │ Dashboard│  │ Dashboard│  │ (Kakao) │  │ Dashboard   │  │  │
│  │  └─────────┘  └─────────┘  └─────────┘  └─────────────┘  │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                             ↓ HTTPS (REST API)
┌─────────────────────────────────────────────────────────────────┐
│                       API Gateway                               │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │              AWS ALB + CloudFront (CDN)                    ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                    Application Layer                           │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │              FastAPI (Python 3.12+)                        ││
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐ ││
│  │  │ Auth Router  │  │ Booking API  │  │ Payment API      │ ││
│  │  └──────────────┘  └──────────────┘  └──────────────────┘ ││
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐ ││
│  │  │ Attendance   │  │ Notification │  │ Settlement API   │ ││
│  │  │ API          │  │ API          │  │                   │ ││
│  │  └──────────────┘  └──────────────┘  └──────────────────┘ ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                    External Services                           │
│  ┌───────────────┐  ┌───────────────┐  ┌─────────────────────┐ │
│  │ Toss Payments │  │ Kakao         │  │ Kakao Alimtalk     │ │
│  │ (PG)          │  │ (OAuth/Login) │  │ (Notifications)    │ │
│  └───────────────┘  └───────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                      Data Layer                                │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │              PostgreSQL 16 (on AWS EC2)                    ││
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐ ││
│  │  │ Users        │  │ Bookings     │  │ Payments         │ ││
│  │  │ (Tutors,     │  │ (Lessons)    │  │ (Transactions)   │ ││
│  │  │  Students)   │  │              │  │                   │ ││
│  │  └──────────────┘  └──────────────┘  └──────────────────┘ ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

### 5.2 Backend Architecture (FastAPI)

**Directory Structure:**
```
backend/
├── main.py                 # FastAPI app entry point
├── config.py               # 환경별 설정 (dev, prod)
├── deps.py                 # Dependency injection (get_db, get_current_user)
│
├── domain/                 # Domain Layer (순수 비즈니스 로직)
│   ├── entities/
│   │   ├── user.py         # User, Tutor, Student
│   │   ├── booking.py      # Booking, Schedule
│   │   ├── payment.py      # Payment, Settlement
│   │   └── attendance.py   # Attendance, NoShowPolicy
│   ├── value_objects/
│   │   ├── money.py        # Money (KRW)
│   │   ├── schedule.py     # TimeRange, DayOfWeek
│   │   └── no_show_policy.py
│   └── ports/
│       ├── payment_port.py     # PaymentPort Protocol
│       ├── notification_port.py
│       └── auth_port.py
│
├── application/            # Application Layer (UseCase)
│   ├── use_cases/
│   │   ├── auth/
│   │   │   ├── login_use_case.py
│   │   │   └── refresh_token_use_case.py
│   │   ├── booking/
│   │   │   ├── create_booking_use_case.py
│   │   │   ├── approve_booking_use_case.py
│   │   │   └── cancel_booking_use_case.py
│   │   ├── payment/
│   │   │   ├── process_payment_use_case.py
│   │   │   └── calculate_refund_use_case.py
│   │   ├── attendance/
│   │   │   ├── mark_attendance_use_case.py
│   │   │   └── handle_no_show_use_case.py
│   │   └── settlement/
│   │       └── monthly_settlement_use_case.py
│   └── dto/
│       ├── booking_dto.py
│       ├── payment_dto.py
│       └── attendance_dto.py
│
├── infrastructure/         # Infrastructure Layer (External)
│   ├── persistence/
│   │   ├── models/         # SQLAlchemy ORM
│   │   │   ├── user_model.py
│   │   │   ├── booking_model.py
│   │   │   └── payment_model.py
│   │   └── repositories/   # Repository implementation
│   │       ├── user_repository.py
│   │       └── booking_repository.py
│   ├── external/
│   │   ├── payment/
│   │   │   └── toss_payment_adapter.py
│   │   ├── auth/
│   │   │   └── kakao_auth_adapter.py
│   │   └── notification/
│   │       └── kakao_alimtalk_adapter.py
│   └── database.py         # DB connection, Session
│
├── api/                    # Presentation Layer (API Routes)
│   ├── v1/
│   │   ├── auth.py         # /api/v1/auth/*
│   │   ├── bookings.py     # /api/v1/bookings/*
│   │   ├── payments.py     # /api/v1/payments/*
│   │   ├── attendance.py   # /api/v1/attendance/*
│   │   └── settlements.py  # /api/v1/settlements/*
│   └── middleware/
│       ├── auth_middleware.py
│       └── error_handler.py
│
├── tasks/                  # Background tasks (Celery/RQ)
│   ├── notification_tasks.py
│   └── settlement_tasks.py
│
├── tests/
│   ├── unit/               # Domain, UseCase 테스트
│   ├── integration/        # API 테스트
│   └── e2e/                # End-to-end 테스트
│
└── docs/
    ├── adr/                # Architecture Decision Records
    ├── api/                # OpenAPI (Swagger 자동 생성)
    └── deployment/
```

### 5.3 Frontend Architecture (Next.js)

**Directory Structure (App Router):**
```
frontend/
├── app/
│   ├── (auth)/
│   │   └── login/
│   │       └── page.tsx
│   ├── (tutor)/
│   │   ├── dashboard/
│   │   ├── bookings/
│   │   ├── students/
│   │   └── settings/
│   ├── (student)/
│   │   ├── dashboard/
│   │   ├── my-bookings/
│   │   └── profile/
│   ├── api/                # API Route Handlers (Proxy)
│   └── layout.tsx
│
├── components/
│   ├── ui/                 # Reusable UI components
│   ├── booking/
│   ├── payment/
│   └── attendance/
│
├── lib/
│   ├── api/                # API client functions
│   ├── hooks/              # Custom React hooks
│   └── utils/
│
├── stores/                 # Zustand (상태 관리)
│   ├── auth_store.ts
│   └── booking_store.ts
│
├── types/                  # TypeScript 타입 정의
│   └── api.ts
│
└── styles/
```

### 5.4 Database Schema

```sql
-- Users (강사, 학생 통합)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    kakao_id BIGINT UNIQUE NOT NULL,
    email VARCHAR(255),
    nickname VARCHAR(50) NOT NULL,
    profile_url VARCHAR(500),
    phone VARCHAR(20),
    role UserRole NOT NULL, -- 'TUTOR' | 'STUDENT' | 'ADMIN'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tutors (강사 추가 정보)
CREATE TABLE tutors (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    bio TEXT,
    subjects TEXT[], -- ['수학', '영어']
    region VARCHAR(100), -- '서울 강남구'
    hourly_rate INTEGER NOT NULL, -- 시간당 수업료 (KRW)
    no_show_policy VARCHAR(20) NOT NULL, -- 'FULL_DEDUCTION' | 'ONE_FREE' | 'NONE'
    cancellation_hours INTEGER NOT NULL DEFAULT 24, -- N시간 전까지 무료 취소
    bank_name VARCHAR(50),
    bank_account VARCHAR(50),
    bank_holder VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Students (학생 추가 정보)
CREATE TABLE students (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    grade INTEGER, -- 학년 (1-12)
    parent_name VARCHAR(50),
    parent_phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Available Slots (강사 가능 시간대)
CREATE TABLE available_slots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tutor_id UUID NOT NULL REFERENCES tutors(user_id) ON DELETE CASCADE,
    day_of_week INTEGER NOT NULL, -- 0(월) ~ 6(일)
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(tutor_id, day_of_week, start_time, end_time)
);

-- Bookings (예약)
CREATE TABLE bookings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tutor_id UUID NOT NULL REFERENCES tutors(user_id),
    student_id UUID NOT NULL REFERENCES students(user_id),
    subject VARCHAR(50) NOT NULL,
    total_sessions INTEGER NOT NULL, -- 총 수업 횟수
    completed_sessions INTEGER DEFAULT 0, -- 완료된 수업
    status BookingStatus NOT NULL, -- 'PENDING' | 'APPROVED' | 'CANCELLED' | 'COMPLETED'
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Booking Sessions (개별 수업)
CREATE TABLE booking_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    booking_id UUID NOT NULL REFERENCES bookings(id) ON DELETE CASCADE,
    session_date DATE NOT NULL,
    session_time TIME NOT NULL,
    status SessionStatus NOT NULL, -- 'SCHEDULED' | 'ATTENDED' | 'NO_SHOW' | 'CANCELLED'
    attendance_marked_at TIMESTAMP,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(booking_id, session_date, session_time)
);

-- Payments (결제)
CREATE TABLE payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    booking_id UUID NOT NULL REFERENCES bookings(id),
    amount INTEGER NOT NULL, -- 결제 금액 (KRW)
    fee_rate DECIMAL(4,3) NOT NULL, -- 수수료율 (0.05 = 5%)
    fee_amount INTEGER NOT NULL, -- 수수료 (KRW)
    pg_payment_key VARCHAR(100) UNIQUE, -- 토스페이먼츠 payment_key
    status PaymentStatus NOT NULL, -- 'PENDING' | 'PAID' | 'FAILED' | 'REFUNDED'
    payment_method VARCHAR(50), -- 'CARD'
    paid_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Settlements (정산)
CREATE TABLE settlements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tutor_id UUID NOT NULL REFERENCES tutors(user_id),
    year_month INTEGER NOT NULL, -- 202502 (2025년 2월)
    total_amount INTEGER NOT NULL, -- 총 수업료
    platform_fee INTEGER NOT NULL, -- 플랫폼 수수료
    pg_fee INTEGER NOT NULL, -- PG사 수수료
    net_amount INTEGER NOT NULL, -- 실제 입금액
    status SettlementStatus NOT NULL, -- 'PENDING' | 'COMPLETED' | 'FAILED'
    paid_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Reviews (리뷰)
CREATE TABLE reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    booking_id UUID NOT NULL REFERENCES bookings(id) ON DELETE CASCADE,
    tutor_id UUID NOT NULL REFERENCES tutors(user_id),
    student_id UUID NOT NULL REFERENCES students(user_id),
    overall_rating INTEGER NOT NULL CHECK (overall_rating BETWEEN 1 AND 5),
    kindness_rating INTEGER CHECK (kindness_rating BETWEEN 1 AND 5), -- 강사 친절도
    preparation_rating INTEGER CHECK (preparation_rating BETWEEN 1 AND 5), -- 수업 준비성
    improvement_rating INTEGER CHECK (improvement_rating BETWEEN 1 AND 5), -- 성과 개선도
    punctuality_rating INTEGER CHECK (punctuality_rating BETWEEN 1 AND 5), -- 시간 준수
    content TEXT NOT NULL CHECK (LENGTH(content) >= 10 AND LENGTH(content) <= 500),
    images TEXT[], -- 첨부 이미지 URL (최대 3장)
    is_anonymous BOOLEAN DEFAULT TRUE, -- 익명 여부
    status ReviewStatus NOT NULL DEFAULT 'ACTIVE', -- 'ACTIVE' | 'HIDDEN' | 'DELETED'
    tutor_reply TEXT, -- 강사의 댓글
    tutor_reply_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(booking_id) -- 1 예약당 1 리뷰
);

-- Review Reports (리뷰 신고)
CREATE TABLE review_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    review_id UUID NOT NULL REFERENCES reviews(id) ON DELETE CASCADE,
    reporter_id UUID REFERENCES users(id), -- 신고자 (학부모 또는 강사)
    reason VARCHAR(50) NOT NULL, -- 'SPAM' | 'ABUSE' | 'FALSE_INFO' | 'OTHER'
    description TEXT,
    status ReportStatus NOT NULL DEFAULT 'PENDING', -- 'PENDING' | 'APPROVED' | 'REJECTED'
    reviewed_by UUID REFERENCES users(id), -- 처리한 관리자
    reviewed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Audit Log (감사 기록)
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type VARCHAR(50) NOT NULL, -- 'BOOKING' | 'PAYMENT' | 'ATTENDANCE'
    entity_id UUID NOT NULL,
    action VARCHAR(50) NOT NULL, -- 'CREATE' | 'UPDATE' | 'DELETE'
    old_value JSONB,
    new_value JSONB,
    actor_id UUID REFERENCES users(id),
    ip_address INET,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_bookings_tutor ON bookings(tutor_id);
CREATE INDEX idx_bookings_student ON bookings(student_id);
CREATE INDEX idx_bookings_status ON bookings(status);
CREATE INDEX idx_sessions_date ON booking_sessions(session_date);
CREATE INDEX idx_payments_booking ON payments(booking_id);
CREATE INDEX idx_payments_status ON payments(status);
CREATE INDEX idx_settlements_tutor_month ON settlements(tutor_id, year_month);
CREATE INDEX idx_reviews_tutor ON reviews(tutor_id);
CREATE INDEX idx_reviews_student ON reviews(student_id);
CREATE INDEX idx_reviews_rating ON reviews(overall_rating);
CREATE INDEX idx_reviews_created ON reviews(created_at DESC);
CREATE INDEX idx_review_reports_review ON review_reports(review_id);
CREATE INDEX idx_audit_entity ON audit_logs(entity_type, entity_id);
```

### 5.5 Key Integration Details

**5.5.1 카카오 로그인**
```python
# Flow:
# 1. 프론트엔드: 카카오 인증 코드 요청
# 2. 백엔드: 인증 코드로 액세스 토큰 교환
# 3. 백엔드: 액세스 토큰으로 사용자 정보 조회
# 4. 백엔드: 회원가입/로그인 처리, JWT 발행
```

**5.5.2 토스페이먼츠 결제**
```python
# Flow:
# 1. 프론트엔드: 토스 SDK로 결제 요청
# 2. 사용자: 카드 정보 입력 및 결제 승인
# 3. 토스: 결제 성공 → 프론트엔드로 payment_key 전달
# 4. 프론트엔드: payment_key를 백엔드로 전송
# 5. 백엔드: 토스 API로 결제 검증
# 6. 백엔드: 예약 상태 업데이트
```

**5.5.3 카카오 알림톡**
```python
# Templates:
# - 수업 리마인드: 수업 24시간 전
# - 예약 승인 알림
# - 결제/환불 알림
# - 출석 체크 리마인더
```

---

## 6. API Design Principles

### 6.1 RESTful API Standards

**URL Convention:**
```
GET    /api/v1/bookings           # 예약 목록 조회
GET    /api/v1/bookings/:id       # 예약 상세 조회
POST   /api/v1/bookings           # 예약 생성
PATCH  /api/v1/bookings/:id       # 예약 수정
DELETE /api/v1/bookings/:id       # 예약 취소
```

**Response Format:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "status": "APPROVED",
    ...
  },
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

### 6.2 Authentication

**JWT Token Structure:**
```python
# Access Token (1 hour)
{
  "sub": "user_id",
  "role": "TUTOR",
  "exp": 1234567890
}

# Refresh Token (30 days)
{
  "sub": "user_id",
  "token_id": "unique_id",
  "exp": 1234567890
}
```

**Token Refresh:**
- Access Token 만료 시 `/api/v1/auth/refresh` 호출
- Refresh Token Rotation: 기존 토큰 폐기, 새 토큰 발행

### 6.3 Request Validation

**Pydantic Model Example:**
```python
from pydantic import BaseModel, Field, field_validator
from datetime import date, time
from typing import Literal

class CreateBookingRequest(BaseModel):
    tutor_id: str = Field(..., min_length=1)
    subject: str = Field(..., min_length=1, max_length=50)
    total_sessions: int = Field(..., ge=1, le=100)
    start_date: date = Field(..., ge=date.today())
    preferred_times: list[PreferredTimeDTO]

    @field_validator('start_date')
    @classmethod
    def validate_start_date(cls, v: date) -> date:
        if v < date.today() + timedelta(days=1):
            raise ValueError('최소 24시간 전까지 예약 가능합니다')
        return v
```

### 6.4 Error Handling

**Error Codes:**
| Code | HTTP Status | Description |
|------|-------------|-------------|
| UNAUTHORIZED | 401 | 로그인 필요 |
| FORBIDDEN | 403 | 권한 없음 |
| NOT_FOUND | 404 | 리소스 없음 |
| VALIDATION_ERROR | 400 | 요청 데이터 오류 |
| DUPLICATE_BOOKING | 409 | 중복 예약 |
| PAYMENT_FAILED | 400 | 결제 실패 |

---

## 7. User Flows

### 7.1 Flow 1: 신규 예약 (학생 → 강사)

```
┌─────────┐    ┌─────────────┐    ┌──────────┐    ┌──────────┐
│ Student │    │ Frontend    │    │ Backend  │    │ Toss     │
└────┬────┘    └──────┬──────┘    └────┬─────┘    └────┬─────┘
     │                │                │               │
     │ 1. 강사 프로필 조회               │               │
     │───────────────>│               │               │
     │                │──────────────>│               │
     │                │<──────────────│               │
     │<───────────────│                │               │
     │                │                │               │
     │ 2. 예약 요청 (시간대, 횟수)       │               │
     │───────────────>│               │               │
     │                │──────────────>│               │
     │                │ DB: Booking   │               │
     │                │ (PENDING)     │               │
     │                │<──────────────│               │
     │<───────────────│                │               │
     │                │                │               │
     │ 3. 결제 진행 (토스 SDK)          │               │
     │───────────────>│               │               │
     │                │──────────────>│──────────────>│
     │                │               │               │ [카드입력]
     │                │               │<──────────────│
     │                │<──────────────│   payment_key │
     │                │               │               │
     │ 4. 결제 검증 요청                │               │
     │───────────────>│               │               │
     │                │──────────────>│──────────────>│
     │                │               │<──────────────│
     │                │ DB: Payment   │               │
     │                │ (PAID)        │               │
     │                │<──────────────│               │
     │<───────────────│                │               │
     │                │                │               │
     │ 5. 강사 승인 대기 상태           │               │
     │<───────────────│                │               │
     │                │                │               │
     │                │                │               │
┌─────────┐    ┌─────────────┐    ┌──────────┐    ┌──────────┐
│ Tutor   │    │ Frontend    │    │ Backend  │    │ Kakao    │
└────┬────┘    └──────┬──────┘    └────┬─────┘    └────┬─────┘
     │                │                │               │
     │ 6. 예약 요청 목록 조회           │               │
     │───────────────>│               │               │
     │                │──────────────>│               │
     │                │<──────────────│               │
     │<───────────────│                │               │
     │                │                │               │
     │ 7. 예약 승인                      │               │
     │───────────────>│               │               │
     │                │──────────────>│               │
     │                │ DB: Booking   │               │
     │                │ (APPROVED)    │               │
     │                │               │──────────────>│
     │                │               │               │ [알림톡 발송]
     │                │               │<──────────────│
     │                │<──────────────│               │
     │<───────────────│                │               │
     │                │                │               │
```

### 7.2 Flow 2: 출결 체크 & 노쇼 처리

```
┌─────────┐    ┌─────────────┐    ┌──────────┐
│ Tutor   │    │ Frontend    │    │ Backend  │
└────┬────┘    └──────┬──────┘    └────┬─────┘
     │                │                │
     │ 1. 오늘 출석 체크할 목록 조회     │
     │───────────────>│               │
     │                │──────────────>│
     │                │<──────────────│
     │<───────────────│                │
     │                │                │
     │ 2. 학생 선택: 출석 / 결석         │
     │───────────────>│               │
     │                │──────────────>│
     │                │ DB: Session  │
     │                │ (ATTENDED/   │
     │                │  NO_SHOW)    │
     │                │ Audit Log    │
     │                │<──────────────│
     │<───────────────│                │
     │                │                │
     │ 3. 노쇼 정책 적용                 │
     │    - FULL_DEDUCTION: 차감       │
     │    - ONE_FREE: 월 1회 면제       │
     │    - NONE: 수동 처리             │
     │<───────────────│                │
     │                │                │
```

### 7.3 Flow 4: 월간 정산

```
┌──────────────┐    ┌──────────┐    ┌──────────┐
│ Batch Job    │    │ Backend  │    │ DB       │
│ (매월 1일)    │    └─────┬────┘    └────┬─────┘
└──────┬───────┘          │              │
       │                  │              │
       │ 1. 전월 완료 수업 조회         │
       │──────────────────>│────────────>│
       │                  │<────────────│
       │<─────────────────│              │
       │                  │              │
       │ 2. 강사별 정산 금액 계산        │
       │    - 총 수업료                 │
       │    - 플랫폼 수수료 (5%)        │
       │    - PG사 수수료 (3%)          │
       │    - 실제 입금액               │
       │                  │              │
       │ 3. 정산 내역 저장               │
       │──────────────────>│────────────>│
       │                  │              │
       │ 4. 입금 처리 (은행 API)         │
       │──────────────────>│ [은행 API] │
       │                  │              │
       │ 5. 이메일 발송                  │
       │──────────────────>│ [메일 API] │
       │                  │              │
```

---

## 8. Success Metrics & KPIs

### 8.1 Business Metrics

**MVP Goal (6개월):**
- 가입 강사 수: 100명
- 월간 예약 건수: 500건
- 월간 거래액(GMV): 2,500만 원
- 수익: 125만 원 (5% 수수료)

**Year 1 Goal:**
- 가입 강사 수: 500명
- 월간 예약 건수: 2,000건
- 월간 거래액(GMV): 1억 원
- 수익: 500만 원/월

### 8.2 Product Metrics

**Acquisition:**
- CAC (Customer Acquisition Cost): < 30,000원/강사
- 전환율: 가입 → 첫 예약 30% 이상

**Activation:**
- 첫 주간 예약 건수: 3건 이상
- 프로필 완성도: 80% 이상

**Retention:**
- 월간 리텐션: 70% 이상
- 3개월 생존율: 50% 이상

**Revenue:**
- ARPU (Average Revenue Per User): 50,000원/월
- LTV (Lifetime Value): 300,000원 이상

### 8.3 Technical Metrics

**Performance:**
- API 응답시간 p95: < 200ms
- 페이지 로드시간 p95: < 2s
- 가동률: 99.5% 이상

**Quality:**
- 버그 리포트: 월 10건 미만
- 결제 실패율: < 1%
- 알림 발송 성공률: > 95%

---

## 9. Implementation Roadmap

### Phase 1: Foundation (Week 1-4)
**Goal:** 인프라 구축, 기본 기능 구현

**Backend:**
- [x] 프로젝트 초기 세팅 (FastAPI, PostgreSQL)
- [ ] 카카오 로그인 구현
- [ ] JWT 인증/인가 구현
- [ ] User, Tutor, Student 모델
- [ ] API 스펙 작성 (OpenAPI)

**Frontend:**
- [ ] Next.js 프로젝트 세팅
- [ ] 로그인 페이지
- [ ] 레이아웃 및 공통 컴포넌트

**Infrastructure:**
- [ ] AWS EC2 세팅
- [ ] PostgreSQL 배포
- [ ] CI/CD 파이프라인 (GitHub Actions)

### Phase 2: Booking & Payment (Week 5-8)
**Goal:** 예약 및 결제 기능 구현

**Backend:**
- [ ] 예약 API (생성, 조회, 승인, 거절)
- [ ] 토스페이먼츠 연동
- [ ] 결제 검증 로직
- [ ] 예약 가능 시간대 관리
- [ ] **리뷰 API** (작성, 조회, 수정, 삭제)
- [ ] **리뷰 신고 API** (신고, 처리)
- [ ] **강사 뱃지 시스템** (평점 기반 자동 부여)
- [ ] **강사 평점 계산 배치** (매일 리뷰 통계 집계)

**Frontend:**
- [ ] 강사 프로필 페이지 (평점, 리뷰 개수 표시)
- [ ] 예약 페이지 (달력, 시간대 선택)
- [ ] 결제 페이지 (토스 SDK 연동)
- [ ] 예약 관리 대시보드
- [ ] **리뷰 작성 페이지** (수업 완료 후 리뷰 작성 유도)
- [ ] **강사 상세 페이지** (리뷰 탭, 평점 필터)

### Phase 3: Attendance & Notification (Week 9-12)
**Goal:** 출결 관리 및 알림 기능

**Backend:**
- [ ] 출결 API (출석, 결석)
- [ ] 노쇼 정책 처리 로직
- [ ] 카카오 알림톡 연동
- [ ] 배치 jobs (Celery/RQ)

**Frontend:**
- [ ] 출석 체크 페이지
- [ ] 출결 현황 페이지
- [ ] 알림 설정 페이지

### Phase 4: Settlement & Refund (Week 13-16)
**Goal:** 정산 및 환불 기능

**Backend:**
- [ ] 월간 정산 배치
- [ ] 환불 계산 API
- [ ] 정산 내역 조회
- [ ] 입금 처리 (은행 API)

**Frontend:**
- [ ] 환불 요청 페이지
- [ ] 정산 내역 페이지
- [ ] 수익 대시보드

### Phase 5: Beta Launch & Optimization (Week 17-20)
**Goal:** 베타 런칭 및 안정화

**QA:**
- [ ] E2E 테스트 작성
- [ ] 부하 테스트
- [ ] 보안 audit

**Launch:**
- [ ] 베타 테스터 모집 (20명)
- [ ] 피드백 수집 및 개선
- [ ] 마케팅 준비 (랜딩 페이지, SNS)

**Metrics:**
- [ ] Analytics 연동 (Google Analytics, Mixpanel)
- [ ] 대시보드 구축 (Grafana)

---

## 10. Open Questions & Risks

### 10.1 Legal & Compliance
- [ ] PG사 계약 진행 상황
- [ ] 개인정보 처리방침 검토
- [ ] 전자상거래법 준수 여부

### 10.2 Technical Risks
- [ ] 토스페이먼츠 webhook 신뢰성
- [ ] 카카오 알림톡 승인 프로세스
- [ ] EC2 단일 장애점 (RDS로 이동 필요)

### 10.3 Business Risks
- [ ] 경쟁사 동향 (클래스팅, 에듀윌)
- [ ] 강사 확장 속도 vs CAC
- [ ] 결제 수수료(5%) 수용성 테스트 필요

---

## Appendix

### A. Glossary
- **노쇼 (No-Show):** 사전 연락 없는 수업 결석
- **선불 (Prepaid):** 수업 전 미리 결제하는 방식
- **정산 (Settlement):** 일정 주기로 강사에게 수입을 입금하는 것
- **감사 트레일 (Audit Trail):** 모든 데이터 변경 이력 기록

### B. References
- [토스페이먼츠 API 문서](https://docs.tosspayments.com)
- [카카오 로그인 문서](https://developers.kakao.com)
- [카카오 알림톡 가이드](https://developers.kakao.com)

### C. ADR Index
- ADR-001: 기술 스택 선정 (Next.js + FastAPI)
- ADR-002: 카카오 로그인 선택 사유
- ADR-003: 토스페이먼츠 선택 사유
- ADR-004: Clean Architecture 적용
- ADR-005: Stateless JWT 인증 설계

---

**Document Owner:** Product Team
**Review Cycle:** Weekly (스프린트 계획 시)
**Next Review:** 2025-02-27
