# Tier B triage, group 23 (49 papers)

Counts: eligible 6, maybe 9, ineligible 34.

Records: one JSON per paper in this directory (`<wid>.json`), schema in `SCHEMA.md` (plus the `no_prompt` blocker, used when role is S/B and a number is reported but the exact prompt text is never printed). Order follows `data/tierb_triage/group_23.csv` (rank).
| wid | verdict | resolved live model | role | prompt | task_type | metric=value (n) | cost | blockers | title |
|---|---|---|---|---|---|---|---|---|---|
| W7166902139 | ineligible | gpt-5-2025-08-07 | S | none | agentic | OS (no-align GPT-5 baseline)=0.889 (n/a) | high | no_prompt | TrafficAlign: Aligning Large Language Models for Traffic Sce… |
| W4416033558 | eligible | gpt-4.1-nano | S | full | classification | brown-response %=85 (20) | low | - | Brown Like Chocolate: How Vision-Language Models Associate S… |
| W4414381808 | ineligible | o3-mini-2025-01-31 | A | full | other | none (judge only) | low | no_number | Evaluating AI Recruitment Sourcing Tools by Human Preference |
| W4404328565 | ineligible | gpt-4-turbo-2024-04-09 | C | none | other | none (writing aid) | low | no_number | Association between different GLP-1 receptor agonists and ac… |
| W4405914919 | ineligible | unresolved | C | none | other | none (citation) | low | no_number | Natural Language Processing and Machine Learning Application… |
| W4411113116 | ineligible | gpt-4o-2024-05-13 | S | full | generation | bypass rate=0.0 (120) | high | tos | Multilingual Blending: Large Language Model Safety Alignment… |
| W4404188593 | maybe | gpt-4o-2024-05-13 | S | partial | classification | failure rate=3 (38) | low | - | Enhancing Fairness in LLM Evaluations: Unveiling and Mitigat… |
| W4416091719 | ineligible | gpt-4.1-nano | A | partial | classification | none (jury only) | low | no_number | Frame In, Frame Out: Measuring Framing Bias in LLM-Generated… |
| W7128972666 | ineligible | unresolved | C | none | other | none (survey table) | low | no_number | A systematic literature review (SLR) on the adoption of arti… |
| W4414586796 | ineligible | unresolved | A | partial | generation | none (dual-snapshot) | low | no_number | Select, Read, and Write: A Multi-Agent Framework of Full-Tex… |
| W7127959504 | ineligible | gpt-4-turbo-2024-04-09 | A | none | other | none (grader only) | low | no_number | Clinical Validation of Medical-based Large Language Model Ch… |
| W4407631943 | ineligible | gpt-4-turbo-2024-04-09 | A | none | other | none (AlpacaEval ref.) | low | no_number | Principled Data Selection for Alignment: The Hidden Risks of… |
| W4411119985 | eligible | gpt-4-turbo-2024-04-09 | S | full | classification | ADA-Met (CONF)=0.92 (100) | mid | - | How Inclusively do LMs Perceive Social and Moral Norms? |
| W4416573512 | ineligible | unresolved | C | none | other | none (survey) | low | no_number | GenAI in the Military: Trends and Opportunities |
| W4416729473 | ineligible | gpt-4-turbo-2024-04-09 | C | none | other | none (writing aid) | low | no_number | Stem cell activity shapes the pleiotropic effects of IFN-γ a… |
| W4414359167 | ineligible | gpt-4o-2024-05-13 | S | full | generation | Assessment/Cognitive score (human-rated) (20) | low | human_outcome | Taking STEPS Forward: Enhancing Online Peer-Counseling with… |
| W4403581937 | ineligible | gpt-4o-2024-05-13 | A | none | extraction | none (word extractor) | low | no_number | Cross-Modal Safety Mechanism Transfer in Large Vision-Langua… |
| W7166857806 | ineligible | unresolved | C | none | other | none (anecdote) | low | no_number | Reflections and Their Owners: The Identity Crisis in the Age… |
| W4403575183 | maybe | gpt-4-turbo-2024-04-09 | S | full | generation | CDT weighted score=4 (1) | low | - | Evidence of Cognitive Deficits andDevelopmental Advances in… |
| W7166821360 | maybe | gpt-4-turbo-2024-04-09 | S | full | other | -β/λ (switching sens.)=27.56 (n/a) | high | - | Modeling and Solving Stable Matching under Probabilistic Pre… |
| W4406975432 | eligible | gpt-4-turbo-2024-04-09 | S | full | classification | implicit-bias DPD=0.513 (1200) | high | - | Actions Speak Louder than Words: Agent Decisions Reveal Impl… |
| W4411530883 | ineligible | gpt-4-turbo-2024-04-09 | C | none | other | none (writing aid) | low | no_number | Editorial: The role of foods, diet, and dietary patterns in… |
| W4410477347 | ineligible | gpt-4-turbo-2024-04-09 | S | none | agentic | none (no_prompt) | mid | no_prompt | Maestro: Multi-Agent Enhanced System for Task Recognition an… |
| W7165893280 | ineligible | gpt-4-turbo-2024-04-09 | S | none | generation | none (cluster labeling) | low | no_number | Tracking the narrative: A data-driven analysis of media cove… |
| W7140088470 | ineligible | unresolved | C | none | other | none (citation) | low | no_number | Feedback-Aware Prompt Optimization Framework for Generating… |
| W7172068041 | ineligible | unresolved | C | none | other | none (illustrative example) | low | no_number | The Age of AI Agents Demands A New Scientific Paradigm To Su… |
| W7168086100 | ineligible | unresolved | C | none | other | none (speculative) | low | no_number | Smart Apps Creator as Digital Media in Arabic Language Learn… |
| W7124872485 | ineligible | unresolved | C | none | other | none (historical narrative) | low | no_number | Incorporação do ChatGPT em Ambientes Educacionais: Oportunid… |
| W4403964218 | ineligible | gpt-4-turbo-2024-04-09 | C | none | other | none (discontinued design) | low | no_number | As Simple as Fine-tuning: LLM Alignment via Bidirectional Ne… |
| W4416385811 | ineligible | unresolved | C | none | agentic | none (cited baseline) | low | no_number | BLAZER: Bootstrapping LLM-based Manipulation Agents with Zer… |
| W4416416845 | ineligible | gpt-4-turbo-2024-04-09 | A | none | extraction | none (lexicon filter) | low | no_number | The Effects of Artificial Intelligence Adoption in the Roman… |
| W4412888001 | ineligible | unresolved | C | none | other | none (citation) | low | no_number | “I understand your perspective”: LLM Persuasion through the… |
| W7165551962 | maybe | gpt-4-turbo-2024-04-09 | S | full | generation | none (multi-metric, n/a table) | low | - | Writing creativity, cohesion, and formal linguistic competen… |
| W7162395757 | ineligible | gpt-4-turbo-2024-04-09 | C | none | other | none (writing aid) | low | no_number | Revolutionizing medical physiology education: a narrative re… |
| W7140142791 | ineligible | gpt-4-turbo-2024-04-09 | A | none | other | none (data utility) | low | no_number | Transformação Digital e Desigualdades Regionais |
| W7160427237 | ineligible | gpt-4.1-nano | S | none | classification | flip rate=n/a (374275) | high | data_closed | EQUITRIAGE: A Fairness Audit of Gender Bias in LLM-Based Eme… |
| W4417163360 | maybe | gpt-4.1-nano | S | partial | other | R² (NMR, chart only)=n/a (n/a) | mid | - | Platonic Representations for Poverty Mapping: Unified Vision… |
| W7154539559 | maybe | gpt-5-nano-2025-08-07 | S | partial | other | avg sycophancy=2.96 (384) | high | - | Intersectional Sycophancy: How Perceived User Demographics S… |
| W7166872685 | eligible | o3-mini-2025-01-31 | S | full | classification | Preport (Moral Rightness)=0.53 (144) | high | - | Machine Behavior in Relational Moral Dilemmas: Moral Rightne… |
| W4415137654 | ineligible | unresolved | C | none | other | none (energy estimate) | low | no_number | How Hungry is AI? Benchmarking Energy, Water, and Carbon Foo… |
| W4404781208 | ineligible | gpt-4o-2024-05-13 | A | none | other | none (judge only) | low | no_number | Cactus: Towards Psychological Counseling Conversations using… |
| W4412887799 | maybe | gpt-4-turbo-2024-04-09 | S | partial | other | CPT alpha (Openness)=n/a (n/a) | mid | - | How Personality Traits Shape LLM Risk-Taking Behaviour |
| W4403346616 | ineligible | unresolved | S | none | other | none (off-list snapshots) | low | no_number | Stereotype or Personalization? User Identity Biases Chatbot… |
| W4412886689 | maybe | o1-2024-12-17 | S | partial | generation | Analytical Score (Env.)=60.5 (n/a) | high | - | DeepSolution: Boosting Complex Engineering Solution Design v… |
| W4405766313 | maybe | gpt-4-turbo-2024-04-09 | S | full | other | trait alignment (fig. only) (n/a) | mid | - | Assessing Social Alignment: Do Personality-Prompted Large La… |
| W4410627635 | eligible | gpt-4-turbo-2024-04-09 | S | full | classification | automation-horizon %=72 (1136) | high | - | Analysis of automation and retraining opportunities for the… |
| W4412886932 | eligible | gpt-4-turbo-2024-04-09 | S | partial | classification | avg accuracy (M-RewardBench)=83.5 (n/a) | high | - | M-RewardBench: Evaluating Reward Models in Multilingual Sett… |
| W4414631693 | ineligible | unresolved | C | none | other | none (market data) | low | no_number | Demand for LLMs: Descriptive Evidence on Substitution, Marke… |
| W7162322542 | ineligible | gpt-4-turbo-2024-04-09 | S | full | generation | none (webui) | low | webui | 生成AIによる認識モダリティ形式の（不）使用 : ChatGPT のモデル更新に伴う変化に着目して |
