# AI 평가 데이터 분석 시스템 PRD

## 📋 **시스템 개요**

AI 모델의 다양한 벤치마크 성능을 동적으로 분석하고 메타데이터별 groupby 집계를 제공하는 FastAPI 기반 분석 시스템

### **핵심 가치 제안**
핵심 설계 포인트들

✅ Connection Pool: 매번 연결하지 않고 효율적으로 재사용
✅ Context Manager: 리소스 누수 걱정 없는 안전한 DB 관리
✅ 동적 SQL 쿼리 생성성: 하드코딩 없이 유연한 groupby 조합 (동적 SQL 쿼리를 통한 API 설계)
✅ Modern Python: Enum, Dataclass, Type Hints로 안전한 코드
✅ 확장 가능: 새 벤치마크/모델 추가가 쉬운 구조
---

## 🎯 **기능 명세**

### **Core Features**

| 기능 | 엔드포인트 | 설명 |
|------|------------|------|
| **동적 메타데이터 분석** | `POST /analysis` | Level1/Level2 조합으로 유연한 groupby 분석 |
| **메타데이터 옵션 제공** | `POST /benchmarks/{}/metadata/options` | 선택된 Level1에 따른 Level2 옵션 동적 제공 |
| **벤치마크 메타데이터 조회** | `GET /benchmarks/{}/metadata` | 벤치마크별 사용 가능한 전체 메타데이터 |
| **전체 데이터 요약** | `GET /analysis/summary` | 벤치마크별 통계 요약 |

### **지원 벤치마크**
- **AIME**: 수학 경시대회 (연도, 문제번호, 풀이단계수)
- **MMLU**: 다분야 객관식 (주제, 카테고리, 지식출처)  
- **MMLU-Redux**: 문화적 맥락 포함 MMLU
- **HLE**: 철학적 초고난이도 (합의수준, 복잡도 breakdown)
- **DS-MMLU**: 반도체 전문 (산업연관성)
- **Math500**: 수학 문제 (증명 필요성, 정리 의존성)

### **지원 모델**
15개 최신 LLM (GPT-4o, Claude-3.5-Sonnet, DeepSeek-R1, Llama-4 등)

---

## 🏗️ **기술 아키텍처**

### **Backend Stack**
- **FastAPI**: 비동기 API 프레임워크
- **MySQL**: 벤치마크별 테이블 구조
- **Connection Pool**: 동시 사용자 처리 최적화
- **Pydantic**: 타입 안전성 및 자동 검증

### **핵심 설계 패턴**

#### **1. Connection Pool 관리**
```python
# 성능 최적화 핵심
pool_config = {
    'pool_size': 20,        # 기본 연결 수
    'max_overflow': 30,     # 피크 시 확장
    'connection_timeout': 10 # 대기 시간
}
```
- **동시 사용자**: 50-200명 처리 가능
- **연결 재사용**: 매 요청마다 연결 생성/해제 방지
- **자동 관리**: Context Manager로 연결 누수 방지

#### **2. 동적 메타데이터 시스템**
- **Level1 선택** → **Level2 옵션 자동 필터링**
- **pandas groupby 스타일**: NULL 값 자동 제외
- **타입 안전성**: Enum 기반 모델/벤치마크 검증

#### **3. Modern Python 패턴**
- **Config 클래스**: 중앙화된 설정 관리
- **Dataclass**: 불변 설정 객체
- **Type Hints**: 전체 코드베이스 타입 안전성
- **Context Manager**: 자동 리소스 관리

---

## 📊 **성능 명세**

### **처리 능력**
| 메트릭 | 목표 | 비고 |
|--------|------|------|
| **동시 사용자** | 100-200명 | Connection Pool 기반 |
| **응답 시간** | < 500ms | 단순 쿼리 기준 |
| **복잡 분석** | < 2초 | 3단계 groupby 기준 |
| **가용성** | 99.5% | Health check 포함 |

### **확장성 설계**
- **수평 확장**: Load Balancer + 다중 인스턴스
- **DB 확장**: Read Replica, 샤딩 가능
- **벤치마크 추가**: Config 수정만으로 확장

---

## 🔧 **운영 가이드**

### **환경 설정**
```bash
# 필수 환경변수
MYSQL_HOST=localhost
MYSQL_USER=ai_user  
MYSQL_PASSWORD=secure_password
DB_POOL_SIZE=20
ENVIRONMENT=production
```

### **모니터링 포인트**
- **Connection Pool 상태**: `/health` 엔드포인트
- **쿼리 성능**: 로그 기반 모니터링
- **에러율**: HTTP 500 에러 추적

### **확장 가이드**
```python
# 새 API 추가 시
# 1. Router 분리
routers/
├── analysis.py      # 기존 분석 API
├── comparison.py    # 모델 비교 API (신규)
└── export.py        # 데이터 내보내기 (신규)

# 2. 서비스 레이어 
services/
├── analysis_service.py
├── model_service.py     # 신규
└── export_service.py    # 신규
```

---

## 🚀 **향후 로드맵**

### **Phase 1: 고급 분석 기능**
- **모델 간 비교 API**: 벤치마크별 성능 차이 분석
- **시계열 분석**: 모델 버전별 성능 변화 추적
- **통계적 유의성**: A/B 테스트 결과 분석

### **Phase 2: 데이터 시각화**
- **대시보드 API**: 차트 데이터 제공
- **리포트 생성**: PDF/Excel 내보내기
- **실시간 업데이트**: WebSocket 기반 라이브 데이터

### **Phase 3: 머신러닝 통합**
- **성능 예측**: 새 모델 성능 예측 API
- **이상 탐지**: 벤치마크 결과 이상값 감지
- **추천 시스템**: 최적 모델 추천 엔진

---

## 📋 **기술 부채 및 주의사항**

### **현재 제약사항**
- **단일 DB**: MySQL 단일 인스턴스 의존
- **동기 쿼리**: 복잡한 분석 시 블로킹 가능
- **메모리 사용**: 대용량 결과셋 처리 최적화 필요

### **마이그레이션 고려사항**
- **벤치마크 추가**: 테이블 스키마 일관성 유지
- **Config 변경**: 타입 안전성 보장 필요
- **API 버전 관리**: 하위 호환성 고려

---

## ✅ **Success Metrics**

- **기술 메트릭**: 응답시간 < 500ms, 가용성 > 99.5%
- **사용성 메트릭**: API 에러율 < 1%, 문서 완성도 > 95%
- **확장성 메트릭**: 새 벤치마크 추가 < 1일, 새 API 개발 < 3일