# Tier B triage, group 20 (49 papers)

Counts: eligible 11, maybe 4, ineligible 34.

Records: one JSON per paper in this directory (`<wid>.json`), schema in `SCHEMA.md`. Order follows `data/tierb_triage/group_20.csv` (rank).

| wid | verdict | resolved live model | role | prompt | task_type | metric=value (n) | cost | blockers | title |
|---|---|---|---|---|---|---|---|---|---|
| W4416035030 | eligible | gpt-4.1-nano-2025-04-14 | S | full | mcq | odds ratio H1(5x)=9.96 (1703) | low | - | Conflicting Needles in a Haystack: How LLMs behave when face… |
| W7166803750 | ineligible | o4-mini-2025-04-16 | S | partial | agentic | NAR (figure only) | low | no_number | Your LLM Agents are Temporally Blind: The Misalignment Betwe… |
| W7164447259 | ineligible | gpt-4.1-nano-2025-04-14 | S | none | generation | doc score=3.15 (n/a) | low | no_prompt | LLM-Based Code Documentation Generation and Multi-Judge Eval… |
| W7124967256 | ineligible | gpt-4.1-nano-2025-04-14 | S | none | agentic | Faithfulness=0.86 (50) | low | no_prompt | MARAG-Fin: An Intelligent Multi-agent RAG-LLM Architecture I… |
| W7106782500 | maybe | gpt-4.1-nano-2025-04-14 | S | full | agentic | net gain TruthfulQA=7.85 (n/a) | low | - | From Competition to Coordination: Market Making as a Scalabl… |
| W7129180728 | ineligible | gpt-4.1-nano-2025-04-14 | C | none | other | none (cited judge) | low | no_number | Asynchronous Verified Semantic Caching for Tiered LLM Archit… |
| W7167746866 | ineligible | gpt-4.1-nano-2025-04-14 | A | none | classification | none (4-judge avg only) | low | no_number | MIRAGE: Defending Long-Form RAG Against Misinformation Pollu… |
| W7158423340 | ineligible | gpt-5-2025-08-07 | S | none | classification | macro-F1=80.8 (701) | mid | no_prompt | DeepImagine: Clinical Trial Outcome Prediction via Stepwise … |
| W4414585650 | eligible | o3-mini-2025-01-31 | S | full | agentic | cooperation=46.9 (160) | mid | - | When Ethics and Payoffs Diverge: LLM Agents in Morally Charg… |
| W4414580759 | eligible | o4-mini-2025-04-16 | S | full | classification | F1=47.85 (4519) | high | - | AppealCase: A Dataset and Benchmark for Civil Case Appeal Sc… |
| W4415772780 | eligible | o4-mini-2025-04-16 | S | partial | other | Spearman=0.804 (545) | low | - | Bridging Behavioral Gaps: Automatic Extrapolation of Concret… |
| W4403365377 | eligible | o4-mini-2025-04-16 | S | full | classification | accuracy=68.9 (1000) | mid | - | Chain-of-Sketch: Enabling Global Visual Reasoning |
| W7158423432 | eligible | o3-2025-04-16 | S | partial | generation | expert score=29.8 (21) | high | - | Expert Evaluation of LLM's Open-Ended Legal Reasoning on the… |
| W7202230881 | ineligible | gpt-5-2025-08-07 | S | none | generation | EX%=76.92 (1785) | high | no_prompt | MIRA: Evidence-Verified Repair Memory for Text-to-SQL Correc… |
| W7166819306 | ineligible | gpt-5-2025-08-07 | S | full | extraction | none (qualitative only) | low | no_number | Exploring Novel Drug Research Area using Large Language Mode… |
| W7196972652 | maybe | gpt-5-nano-2025-08-07 | S | partial | extraction | overlap score=2.0 (144) | low | - | Artificial intelligence can match domain experts in evidence… |
| W7140103084 | ineligible | gpt-5-mini-2025-08-07 | S | none | extraction | F1=0.4882 (n/a) | low | no_prompt | Who Plays Which Role? Protagonist Detection and Classificati… |
| W4416378581 | ineligible | o3-2025-04-16 | A | none | other | none (adjudicator only) | low | no_number, no_prompt | Cost-Effective Communication: An Auction-based Method for La… |
| W4406309654 | ineligible | gpt-4-turbo-2024-04-09 | A | partial | other | quality score (figure only) | low | no_number | Publicly-Detectable Watermarking for Language Models |
| W4416035019 | ineligible | gpt-4o-2024-05-13 | A | partial | generation | none (judge, not isolated) | low | no_number | PersonaGym: Evaluating Persona Agents and LLMs |
| W4411119350 | ineligible | gpt-4-turbo-2024-04-09 | C | none | other | none (cited comparison) | low | no_number | LLaMA-Berry: Pairwise Optimization for Olympiad-level Mathem… |
| W4385889917 | ineligible | gpt-4o-2024-05-13 | S | partial | generation | RTTR/Maas (figure only) | low | no_number | Playing with words: Comparing the vocabulary and lexical div… |
| W4406936034 | ineligible | gpt-4-turbo-2024-04-09 | S | none | classification | none (never reported) | low | no_number, no_prompt | From deliberation to acclamation: how did Twitter's algorith… |
| W4417153375 | ineligible | gpt-4-turbo-2024-04-09 | C | none | other | none (writing aid) | low | webui, no_number | Medicine-food homology bioactives in Parkinson's disease: mu… |
| W4404938063 | ineligible | unresolved | C | none | other | none (writing aid) | low | webui, no_number | Evaluating the impact of cell-penetrating motif position on … |
| W4414713350 | ineligible | gpt-4-turbo-2024-04-09 | C | none | other | none (writing aid) | low | webui, no_number | Lab-scale production of postbiotic proteins from Bifidobacte… |
| W4412945367 | eligible | o4-mini-2025-04-16 | S | full | generation | human eval=4.00 (100) | mid | - | AbGen: Evaluating Large Language Models in Ablation Study De… |
| W4412945558 | eligible | gpt-4o-2024-05-13 | S | full | generation | Perfect rate=0.51 (3000) | mid | - | Beyond Facts: Evaluating Intent Hallucination in Large Langu… |
| W4401246245 | eligible | gpt-4o-2024-05-13 | S | full | generation | expert score=27/40 (20) | low | - | Imaging protocol suggested by large language model depends o… |
| W4404573318 | eligible | gpt-4-turbo-2024-04-09 | S | full | agentic | misalign. rate=0.41 (600) | mid | - | Chat Bankman-Fried: an Exploration of LLM Alignment in Finan… |
| W4399401121 | ineligible | gpt-4o-2024-05-13 | S | partial | mcq | RoCA=0.776 (200) | mid | data_closed | Superhuman performance in urology board questions by an expl… |
| W4406072163 | ineligible | gpt-4o-2024-05-13 | S | none | classification | macro F1=63.1 (n/a) | low | no_prompt | Economy Watchers Survey Provides Datasets and Tasks for Japa… |
| W4416034780 | eligible | gpt-4-turbo-2024-04-09 | S | partial | mcq | TAR=92.5 (120) | mid | - | CAPE: Context-Aware Personality Evaluation Framework for Lar… |
| W4411120066 | ineligible | gpt-4-turbo-2024-04-09 | S | partial | other | RDC (figure only) | low | tos | A Comparative Analysis of Ethical and Safety Gaps in LLMs us… |
| W4411119916 | ineligible | dead-preview | B | none | other | none (dead preview) | low | dead_alias | Stronger Models are Not Always Stronger Teachers for Instruc… |
| W7134897214 | ineligible | o3-mini-2025-01-31 | S | none | classification | concordance=65.4 (971) | high | data_closed, no_prompt | Comparison of large language models and expert multidiscipli… |
| W7164446663 | ineligible | unresolved | S | none | agentic | delta=0.13 (n/a) | low | alias_unpinned, no_prompt | The Shibboleth Effect: Auditing the Cross-Lingual Distributi… |
| W7204485613 | ineligible | gpt-4-turbo-2024-04-09 | S | none | generation | ROUGE-S F1=0.85 (n/a) | low | no_prompt | Analysing Anti-Vaccine Concerns on the Gab and Twitter Socia… |
| W7160186164 | ineligible | gpt-4-turbo-2024-04-09 | S | none | classification | none (abstract only) | low | no_number, no_prompt | So Many Opinions, So Many LLMs: Comparing Large Language Mod… |
| W7166859602 | ineligible | gpt-4-turbo-2024-04-09 | S | none | agentic | accuracy=83.2 (250) | mid | no_prompt | Attribution-Based Analysis and Optimization of Modular Agent… |
| W7131731763 | maybe | gpt-4-turbo-2024-04-09 | S | full | other | corr. rho=0.69 (27) | low | - | Language Models Exhibit Inconsistent Biases Towards Algorith… |
| W7155154988 | ineligible | gpt-4-turbo-2024-04-09 | C | none | other | none (survey) | low | no_number | A Survey on Multi-Agent Systems for AI-Driven Data Automatio… |
| W7162218515 | ineligible | gpt-4-turbo-2024-04-09 | S | full | generation | success prob (figure only) | low | no_number | Reinforced Graph of Thoughts: RL-Driven Adaptive Prompting f… |
| W7165658898 | maybe | gpt-4-turbo-2024-04-09 | S | partial | generation | accuracy=92.0 (20) | low | - | Avaliação de Modelos de Linguagem para o Suporte à Decisão M… |
| W7168369105 | ineligible | gpt-4-turbo-2024-04-09 | S | none | agentic | Nc=1600 (n/a) | low | no_prompt | Poor Man's Agentic Modeling: Simulating Large LLM-Agent Soci… |
| W7165378143 | ineligible | gpt-4-turbo-2024-04-09 | C | none | other | none (cited only) | low | no_number | Embodied GPT-5.1: Evidence of a World Model? |
| W4413684652 | ineligible | gpt-4-turbo-2024-04-09 | S | full | classification | none (qualitative only) | low | webui, no_number | Vieses Sociais e Raciais da IA interpretando Clássicos da Li… |
| W4410973253 | ineligible | gpt-4-turbo-2024-04-09 | S | none | classification | none (filter count only) | low | no_prompt, no_number | Enhancing supply chain resilience with artificial intelligen… |
| W7133961658 | ineligible | gpt-4-turbo-2024-04-09 | C | none | other | none (cited only) | low | no_number | Overview of AI Agent Applications in Hospital Pharmacy Opera… |

## Observations

- Alias resolution: this group is dominated by bare `gpt-4-turbo` (18 rows) and `gpt-4.1-nano`/o-series ids that resolve on their own (single-snapshot aliases). Only two papers carried an explicit preview string next to the alias: W4411119916 ("GPT-4-Turbo (1106)", used as the AlpacaEval2/Arena-Hard baseline model) resolved to `dead-preview` (blocker `dead_alias`); every other undated `gpt-4-turbo` mention postdates 2024-07-01 with no preview string and resolved to `gpt-4-turbo-2024-04-09` by the date rule. One undated `gpt-4o` (W7164446663) could not be pinned because only its abstract survived extraction and the paper is clearly post-2024-10-02 (blocker `alias_unpinned`).
- `no_prompt` is the single largest ineligibility reason (13 papers): several of these are otherwise strong candidates (W7202230881's MIRA gives exact call/token counts; W7168369105 and W7134897214 give clean per-model numbers; W7140103084 and W4406072163 have exemplary public-data pipelines) but the prompt text lives only in a GitHub repository, "Supplementary Material," or "online supplemental methods" rather than in the paper itself.
- Mention-only and judge-only roles account for 10 ineligible verdicts: 6 are role C (cited comparison tables or survey summaries: W7129180728, W4411119350, W7155154988, W7165378143, W7133961658, plus W4416378581's Vanilla baseline) and 4 are role A (an auxiliary judge/adjudicator/generator rather than the evaluated subject: W7167746866, W4406309654, W4416035019, W4416378581 doubles as both).
- Three papers (W4417153375, W4404938063, W4414713350) use ChatGPT only for manuscript proofreading/translation per a journal's mandatory Generative-AI disclosure; none contains an experiment, and all three used the consumer web app rather than the API (blocker `webui`). W4413684652 similarly ran the free ChatGPT web UI in a real (if informal) experiment but reported only qualitative per-model descriptions, no counts.
- `data_closed` blocked two otherwise well-documented medical papers: W4399401121 (UroBot)'s EBU board-exam questions must be purchased, and W7134897214's colorectal-cancer MDT records are real hospital patient data. `tos` blocked one paper (W4411120066's hate-speech/self-harm/weapons red-teaming).
- Figure-only results (no exact number in text or a table) blocked 6 papers outright (W7166803750, W4406309654, W4385889917, W4411120066, W7162218515) even though several of them (W7162218515 especially) had exemplary full prompts and explicit `n=100`-per-condition sample sizes.
- Two rows (W7204485613, W7160186164) reflect a corpus limitation rather than the paper's own quality: the scraped `.txt` is a Zenodo/journal abstract-only landing page, so no method, prompt, or full results table was available to judge.
- All 11 eligible papers pair a role-S run with a prompt genuinely reproduced in the paper's own text (full or partial) and a table-based numeric claim; the 4 `maybe` verdicts each carry exactly one soft gap (W7106782500 and W7165658898: n_items/prompt wording not pinned down; W7196972652: prompt only in supplementary material plus an indirect headline metric; W7131731763: the model's own point value sits in a figure, so a secondary in-text correlation statistic is used instead).
