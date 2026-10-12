# 주장 카드(claim card) 스키마 v1

카드 하나 = 논문 하나의 핵심 주장 하나를 재실행하기 위한 완전한 사양. T1(`T1_bia_codegen.json`)이 참조 예시.
상태(status)는 `draft`(초안) → `needs-user-check`(사용자 확인 필요 항목 있음) → `approved`(실행 승인) → `blocked`(재실행 불가, 사유 기록).

| 필드 | 내용 | 확인 방법 |
|---|---|---|
| `card_id`, `openalex_id`, `title`, `doi` | 식별자 | p0_pool.csv |
| `paper.repo`, `repo_commit`, `repo_license` | 논문 자체 저장소, 클론 시점 커밋, 라이선스 | scaffold 감사 + README |
| `dependence.type` / `strength` | 주석자·심사자·모의피험자·대상·구성요소 / 핵심·보조 | 초록·방법 절 |
| `claim.statement` | 재실행 목표인 핵심 주장 한 문장 (원 논문의 표·그림 번호 명시) | 논문 본문 |
| `claim.claim_type` | capability_level / capability_limit / bias_or_behavior / method_effect / tool_validity | 판정용 분류 (H2) |
| `claim.metric`, `claim.original_values` | 지표 정의와 원 보고값(가능하면 표에서 정확히) | 논문 표 또는 저장소 결과 파일 |
| `protocol.model`(live arm), `endpoint`, `prompt_source`, `params`, `n_items`, `samples_per_item` | 원 프로토콜을 그대로 복제할 수 있는 수준의 사양 | 저장소 코드·노트북 |
| `artifacts.prompts_path`, `data_path`, `eval_path` | 저장소 내 경로. 없으면 `null` + 사유 | scaffold 감사 |
| `artifacts.data_public`, `data_license`, `redistributable` | 데이터 공개·라이선스·재배포 가능 여부 | LICENSE, 데이터 출처 |
| `blockers` | 재실행을 막는 요인 목록 (비공개 데이터, 저작권 문항, 환경 의존, 인간 평가 필요 등) | 종합 |
| `arms` | baseline_alive(살아있는 모델) + successors(GPT-5.x, Claude, Gemini, Llama, Qwen) | target_models.json |
| `budget.est_calls`, `est_tokens_in/out`, `est_cost_usd` | 파일럿 단가 기반 견적 (배치 API −50% 미적용 보수치) | n_items × samples × 토큰 |
| `judgment.rule` | ANALYSIS_PLAN §1 적용 방식 (어떤 수치의 방향·CI를 볼지) | 카드 작성자 |
| `status`, `user_checks` | 사용자가 확인해야 할 질문 목록 (예: "핵심 주장을 표3 대신 표2로 잡아도 되나") | 카드 작성자 |

비용 견적 규칙(파일럿 실측): gpt-4-turbo 호출당 평균 130 in / 300 out 토큰 ≈ $0.0105. MCQ형은 out 50~150 토큰으로 더 싸고, 생성형은 out 400~800, 에이전트형은 턴당 누적.
