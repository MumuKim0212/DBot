# DBot (Data Assistant)

자연어 질의를 통해 데이터베이스(MySQL)의 데이터를 조회하고 분석할 수 있는 **LLM 기반 SQL Agent 시스템**입니다. 
대규모 데이터베이스 환경에서도 높은 정확도를 보장하고 API 비용을 최소화하기 위해 **시맨틱 검색(Semantic Search)**, **스키마 필터링(Schema Filtering)**, 그리고 **LLM**을 결합한 하이브리드(Hybrid) 아키텍처로 설계되었습니다.

## ✨ 주요 기능 (Features)

- **자연어 기반 데이터 조회 (Text-to-SQL)**
  - 사용자가 자연어로 질문하면 LLM이 의도를 파악하여 적절한 SQL 쿼리를 생성하고 데이터를 반환합니다.
- **RAG 기반 테이블 스키마 최적화**
  - 전체 DB 스키마를 LLM에 전달하지 않고, **임베딩(OpenAI Embeddings API) 기반 시맨틱 검색**을 통해 질문과 연관된 핵심 테이블만 1차 선별합니다.
  - 선별된 테이블의 관계(Relations)를 분석하여 JOIN에 필요한 테이블을 자동으로 확장(Relation Expansion)합니다.
- **안전한 SQL 실행 엔진 (SQL Validator)**
  - `SELECT` 외의 데이터 조작(UPDATE, DELETE, DROP 등) 쿼리는 정규식과 키워드 매칭을 통해 실행 전 철저히 차단합니다.
  - 서버 측에서 `LIMIT`를 강제하여 대량의 데이터 조회로 인한 DB 부하를 방지합니다.
- **유연한 LLM Provider 전환**
  - OpenAI(GPT 모델)와 Anthropic(Claude 모델)을 지원하며, 환경변수 변경만으로 간편하게 API를 교체할 수 있습니다.
- **채팅형 Web UI**
  - 직관적인 웹 인터페이스를 통해 사용자가 메신저를 사용하듯 간편하게 데이터를 질의하고 결과를 확인할 수 있습니다.
- **Rule-based 캐싱 엔진 (비용 최적화)**
  - 자주 묻는 특정 패턴의 질문은 LLM을 거치지 않고 정의된 SQL을 즉시 반환(Early Return)하여 응답 속도를 높이고 API 비용을 절감합니다.
- **비즈니스 지표 사전 (Metric Registry)**
  - 사내 표준 분석 기준과 필수 파라미터를 중앙화하여 LLM이 일관되고 정확한 비즈니스 로직의 SQL을 생성하도록 보장합니다.
- **모호한 질문 방지 (Gate Checker)**
  - 필수 조건이 누락된 모호한 질문은 사전에 차단하고 사용자에게 되묻는 기능을 통해 환각(Hallucination)과 불필요한 DB 조회를 방지합니다.
- **결과 시각화 추천 (Visualizer)**
  - 대량의 로우(Row) 데이터를 LLM에 보내지 않고, 결과 컬럼 메타데이터만으로 가장 적합한 차트 형태(Bar, Line, Pie 등)를 추천하여 API 비용과 응답 속도를 최적화합니다.
- **멀티 턴(Multi-turn) 대화 컨텍스트 유지**
  - 세션 매니저를 통해 이전 질의의 테이블 문맥을 기억하여, "거기서 상위 5개만 보여줘"와 같은 주어가 생략된 후속 질문(Fallback)도 자연스럽게 처리합니다.
- **안전한 쿼리 로깅 및 모니터링**
  - 사용자의 자연어 질의, 생성된 SQL, 성공/에러 여부를 `logs/query_log.jsonl`에 회전(Rotating) 방식으로 자동 기록합니다.

## 🛠 기술 스택 (Tech Stack)

- **Backend**: Python 3.10+, FastAPI, OpenAI Embeddings API (text-embedding-3-small)
- **Database**: MySQL (단일 서버 및 Multi-Server 커넥션 풀 라우팅 지원)
- **AI / LLM**: OpenAI API, Anthropic API
- **Frontend**: React (CDN), Vanilla CSS

## 🚀 시작하기 (Getting Started)

### 1. 사전 요구 사항
- Python 3.10 이상
- MySQL 서버 접속 정보

### 2. 설치

```bash
# 1. 저장소 클론
git clone https://github.com/MumuKim0212/DBot.git
cd DBot

# 2. 파이썬 패키지 설치
pip install -r requirements.txt

# 3. 환경변수 파일 설정
cp sample.env .env
```

### 3. 환경 변수 설정 (`.env`)

`.env` 파일을 열어 다음 정보를 상황에 맞게 수정합니다. 단일 서버 환경뿐만 아니라 다중 서버 라우팅 환경도 지원합니다.

```env
LLM_PROVIDER=openai  # openai 또는 claude
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key

# 1. 단일 DB 서버 연결 시
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DB=your_database_name

# 2. (옵션) 다중 DB 서버 환경 구성 시 (DB_SERVERS JSON 배열 사용)
# DB_SERVERS={"default": {"host": "...", "user": "...", "password": "...", "db": "..."}, "log_db": {...}}
```

### 4. RAG 기반 테이블 스키마 데이터 파이프라인

본격적인 서비스 구동 전, DBot이 데이터베이스 구조를 이해하고 시맨틱 검색을 수행할 수 있도록 데이터 파이프라인을 실행해야 합니다. (미리 생성된 파일이 있다면 생략 가능)

```bash
# 1. DB 스키마 자동 추출 (DB -> schema_full.json)
python schema_extractor.py

# 2. 스키마 요약 및 키워드 생성 (schema_full.json -> schema_index.json)
python app/utils/schema_summarizer.py

# 3. 요약된 텍스트를 벡터로 임베딩 (schema_index.json -> table_embeddings.json)
python app/utils/embeddings.py
```
*완료되면 프로젝트 내에 테이블/컬럼/관계 정보와 LLM 검색용 벡터 임베딩 데이터가 모두 준비됩니다.*

### 5. 서버 실행 (로컬 개발용)

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
- **웹 UI 접속**: 브라우저에서 `http://localhost:8000/` 로 접속하여 바로 서비스를 이용할 수 있습니다.

### 6. Docker를 이용한 배포 (프로덕션/외부 서버용)

Docker를 사용하면 환경 설정 없이 손쉽게 외부 서버에 프로젝트를 띄워둘 수 있습니다. 서버의 방화벽 설정에서 포트(예: 8000)를 미리 열어주어야 합니다.

```bash
# 1. Docker 이미지 빌드
docker build -t dbot-app .

# 2. 백그라운드에서 컨테이너 실행 (8000 포트로 포워딩)
docker run -d -p 8000:8000 --env-file .env --name dbot-container dbot-app
```
- **웹 UI 접속**: 외부 서버의 공인 IP와 포트를 통해 브라우저에서 접속합니다. (예: `http://123.45.67.89:8000/`)

## ⚙️ 정확도 향상 옵션 (Optional Tuning)

기본 설정만으로도 동작하지만, 아래 항목을 추가로 설정하면 SQL 생성 정확도와 안전성을 높일 수 있습니다.

### 1. 비즈니스 지표 사전 (`metrics_dictionary.json`)

**파일 위치**: `app/data/metrics_dictionary.json`

사내 표준 분석 기준을 정의하면 두 가지 효과가 생깁니다.
- **Gate**: 필수 조건(기간, 플랫폼 등)이 빠진 모호한 질문을 사전에 차단하고 되묻기
- **SQL 생성**: 관련 지표의 비즈니스 로직(`description`)이 프롬프트에 자동 주입되어 취소 제외, 특정 상태 필터 등을 LLM이 직접 반영

키워드 매칭으로 질문과 관련된 지표만 골라서 전송하므로 불필요한 토큰 낭비가 없습니다.

```json
{
  "metrics": [
    {
      "name": "매출액",
      "keywords": ["매출", "결제금액", "revenue"],
      "description": "취소·환불 상태의 결제는 반드시 제외한다. status = 'completed' 조건을 WHERE 절에 포함해야 한다.",
      "required_parameters": ["조회 시작일과 종료일"]
    }
  ]
}
```

| 필드 | 설명 |
|------|------|
| `name` | 지표 이름. LLM이 질문과 매칭할 때 참고 |
| `keywords` | 동의어·유사어 목록. 넉넉히 채울수록 매칭 정확도 상승 |
| `description` | **핵심.** SQL 로직 규칙을 자연어로 기술 — 이 내용이 프롬프트에 그대로 주입됨 |
| `required_parameters` | 없으면 `[]`. 명시된 조건이 질문에 빠지면 Gate가 되묻기 발동 |

### 2. 대용량 테이블 강제 조건 (`mandatory_where_columns`)

**파일 위치**: `app/data/schema_index.json`

파티셔닝이 걸려 있거나 풀스캔이 위험한 테이블의 메타데이터에 `mandatory_where_columns`를 추가하면, Gate 및 프롬프트 단에서 해당 컬럼이 `WHERE` 절에 포함됐는지 검사하는 로직을 강화할 수 있습니다.

```json
"user_login_log": {
  "summary": "유저의 접속 로그",
  "keywords": ["로그인", "접속"],
  "mandatory_where_columns": ["log_date", "server_id"]
}
```

## 📝 시스템 아키텍처 흐름

1. **사용자 질의 (User Query)**: Web UI를 통해 자연어로 질문 입력
2. **사전 검증 (Gate Checker)**: 지표 사전(Metric Registry)을 참고하여 질문의 필수 조건 포함 여부 확인 (부족할 경우 되묻기 반환)
3. **시맨틱 테이블 검색 (Semantic Table Selection)**: 질문의 임베딩 벡터와 테이블 메타데이터의 유사도를 비교해 관련성이 높은 테이블 선별
4. **관계 확장 (Relation Expansion)**: 선별된 테이블과 조인(JOIN) 관계가 있는 주변 테이블 추가 포함
5. **프롬프트 생성 (Prompt Building)**: 축소된 스키마 정보와 안전 제약 조건, 사용자 질의를 융합하여 LLM 프롬프트 조립
6. **SQL 생성 및 검증 (SQL Gen & Validation)**: LLM이 생성한 SQL의 문법 및 안전성을 검사 (데이터 수정/삭제 쿼리 차단)
7. **DB 조회 및 시각화 구성 (Visualization)**: 검증된 쿼리를 실행한 후, 결과 데이터와 함께 최적의 차트 설정값(Visualizer)을 생성하여 Web UI로 전송
