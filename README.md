# EXEM 기업연계 프로젝트 | AI 워크플로우·LOOP 백엔드 개선

**2026.07~2026.10 · EXEM × ASAC · 5인 팀**

보이스피싱·스미싱 자료를 검증하고, 유사 사례 검색부터 시나리오 생성과 결과 검수까지 이어지는 AI 서비스를 팀으로 개발했습니다. 그 과정에서 기존 eXemble 플랫폼의 **LOOP 회차 간 데이터 전달 문제**를 발견해 Python 백엔드 개선을 담당했습니다.

이 저장소는 **문제 → 설계 판단 → 구현 → 검증** 순서로 실제 담당 작업을 설명합니다. 회사 내부 코드를 공개하지 않고, 핵심 동작을 확인할 수 있는 독립 예제를 함께 구성합니다.

## 실제 맡은 역할과 증거

| 역할 | 해결한 문제 | 확인 자료 |
| --- | --- | --- |
| **LOOP 백엔드 개선** | 내부 노드의 여러 출력을 다음 회차에 구분해서 전달하기 어려움 | [개선 과정](docs/loop-improvement.md), [독립 코드](backend/loop_demo/engine.py), [테스트](backend/tests/test_loop_engine.py) |
| **AI 데이터 품질 검수** | 음성인식 오류가 후속 검색·분류·생성에 영향을 줌 | [STT 검수 파이프라인](https://github.com/Westzer00/voice-phishing-stt-qc-pipeline) |
| **PHISIGHT UI 공동 개발** | 입력부터 분석·검수까지 사용자가 결과를 확인하는 과정 설계 | [UI 개인 기여](docs/ui-participation.md) |
| **AI 워크플로우 구현 참여** | 유사사례를 그대로 생성에 쓰면 부적절한 근거가 혼합될 수 있음 | [팀 워크플로우와 설계 판단](docs/team-workflow.md) |

> **개인·팀 구분:** LOOP 입출력 개선은 내부 배분안에 명시된 개인 담당 기능입니다. PHISIGHT 초기 화면·사용자 흐름 설계와 상세 UI 공동 개발에 참여했습니다. 워크플로우 전체와 데이터셋은 팀 성과이며 모든 노드를 단독 개발한 것은 아닙니다.

## 1. LOOP에서 무엇을 개선했나

기존 LOOP는 내부 그래프를 반복했지만 **대표 결과 하나**를 중심으로 값을 전달했습니다. 내부 초안·검수 결과·근거를 다음 회차에 구분해 사용하기 어려워, 프롬프트보다 실행 구조의 문제를 먼저 해결해야 했습니다.

- 입력값을 한곳에서 지정하고 반복 중 공통으로 참조
- 필요한 내부 노드 결과에 이름을 붙여 출력
- **직전 성공 회차의 출력값**을 다음 회차에 전달
- 회차별 기록·최종 결과 저장, 출력값을 이용한 종료 조건
- 기존 기능 호환, 잘못된 참조·하위 노드 실패 및 중첩 데이터의 변경 방지 고려

상세 근거와 설계상 제약은 [LOOP 개선 문서](docs/loop-improvement.md)에 정리했습니다.

## 2. 팀 워크플로우의 설계 판단

단순한 ‘검색 → 생성’에서 **검색 결과 검수 → 생성 계획 → 생성 → 두 차례 검증**으로 개선했습니다. 비슷한 사례를 찾았다고 해서 생성에 적합한 근거인 것은 아니기 때문입니다.

[보이스피싱·스미싱 팀 워크플로우 정리](docs/team-workflow.md)

## 3. PHISIGHT 화면 개발

파일 등록부터 분석 요청·결과 검수까지의 사용자 흐름을 설계하고 상세 UI 구현에 공동 참여했습니다. 실제 엔진의 단계별 진행률이나 제품 전체의 인증·배포 완료를 주장하지 않습니다.

[담당 영역과 당시 구현·미검증 항목](docs/ui-participation.md)

## 4. 실행 가능한 공개 예제

회사 제품 소스를 복제하지 않고 Python으로 **입출력 지정, 이전 회차 결과, 종료 조건**을 독립 재현한 예제입니다. 실제 모델 대신 합성 노드를 사용합니다.

```bash
python -m pip install pytest
python -m pytest -q
python -m backend.examples.run_demo
python -m backend.server --port 8080
```

브라우저에서 http://127.0.0.1:8080 을 열면 합성 데이터 기반 웹 예제가 실행됩니다.

- [LOOP 코드](backend/loop_demo/engine.py)
- [JSON 경로 처리](backend/loop_demo/bindings.py)
- [API와 웹 화면](backend/server.py)
- [자동 테스트](backend/tests/) — 독립 예제의 테스트만 해당

## 5. 파일 구조

```text
exem-ai-workflow/
├── README.md
├── backend/
│   ├── loop_demo/          # 독립 LOOP·출력 참조 로직
│   ├── examples/           # 합성 입력·실행 예시
│   ├── tests/              # 정상·예외·HTTP 검증
│   └── server.py           # 공개용 로컬 HTTP 서버
├── ui-demo/                # PHISIGHT 원본이 아닌 LOOP 설명용 화면
├── docs/
│   ├── loop-improvement.md
│   ├── team-workflow.md
│   ├── ui-participation.md
│   ├── contribution.md
│   └── release-scope.md
└── .github/workflows/python-tests.yml
```

## 6. 공개 원칙

실제 EXEM 플랫폼 코드, 비공개 워크플로우 화면과 프롬프트, 팀 공동 UI·서버 원본, 실제 통화·문자 데이터와 내부 주소·계정은 공개하지 않았습니다. **독립 예제의 테스트 성공이 제품 전체의 배포·운영 검증을 뜻하지는 않습니다.**

[기여 범위](docs/contribution.md) · [공개 기준](docs/release-scope.md)
