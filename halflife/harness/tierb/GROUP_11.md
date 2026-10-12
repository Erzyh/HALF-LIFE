# Tier B triage, group 11 (50 papers)

Counts: eligible 5, maybe 9, ineligible 36.

| wid | verdict | resolved live model | role | prompt | task_type | metric=value (n) | cost tier | blockers | title |
|---|---|---|---|---|---|---|---|---|---|
| W4412944900 | ineligible | gpt-4-turbo-2024-04-09 | A | partial | agentic | SoPR (solvable pass rate, judged by gpt-4-turbo-2024-04-09)=71.05 (n=765) | mid | dead_alias, no_number | CodeTool: Enhancing Programmatic Tool Invocation of LLMs ... |
| W7164447651 | maybe | o3-mini-2025-01-31 | B | full | classification | AUROC, false-success vs true-success detection by the o3-mini judge, 'no closing' condi... | high | - | From Confident Closing to Silent Failure: Characterizing ... |
| W7133951874 | maybe | o1-2024-12-17 | S | full | mcq | accuracy=0.795 (n=400) | high | - | Performance of ChatGPT-o1 and DeepSeek-R1 on the health l... |
| W7130236882 | ineligible | o4-mini-2025-04-16 | C | none | agentic | none=n/a (n=?) | low | no_number | WebWorld: A Large-Scale World Model for Web Agent Training |
| W4411120534 | ineligible | gpt-4o-2024-05-13 | A | full | generation | win rate of original vs translated queries (judge score 1-10)=n/a (n=?) | low | dead_alias, no_number | Is Translation All You Need? A Study on Solving Multiling... |
| W4407629603 | ineligible | dead-preview | S | full | mcq | accuracy, Remember category=0.83 (n=60) | low | webui, dead_alias, data_closed | Chinese Generative AI Models Challenge Western AI in Clin... |
| W4406778839 | ineligible | gpt-4-turbo-2024-04-09 | S | partial | agentic | task-solving accuracy, SR tasks (0-1 tools)=0.8571 (n=?) | low | data_closed, no_prompt, human_outcome | Empowering AIOps: Leveraging Large Language Models for IT... |
| W4404314294 | eligible | gpt-4-turbo-2024-04-09 | S | full | mcq | accuracy, 1st-index answer, No Prompting=0.817 (n=707) | mid | - | DisasterQA: A Benchmark for Assessing the performance of ... |
| W4415169525 | ineligible | unresolved | S | full | generation | author-assigned points (0-3) for correct term meaning=n/a (n=8) | low | webui, human_outcome | Decolonizing Archival Narratives: Exploring Digital Bias ... |
| W4403345821 | maybe | gpt-4-turbo-2024-04-09 | B | partial | other | VQAv2 exact-match score=0.738 (n=1000) | high | - | VHELM: A Holistic Evaluation of Vision Language Models |
| W4404310870 | maybe | gpt-4-turbo-2024-04-09 | S | full | generation | exact-match accuracy, Direct, GSM8K original questions ('Before')=45.43 (n=1121) | mid | - | ReasonAgain: Using Extractable Symbolic Programs to Evalu... |
| W7155246944 | ineligible | unresolved | C | none | other | none=n/a (n=?) | low | no_number | Architecture Matters More Than Scale: A Comparative Study... |
| W7127203938 | ineligible | unresolved | C | none | other | none=n/a (n=?) | low | no_number | A Structured Approach to Safety Case Construction for AI ... |
| W4416157016 | eligible | gpt-4.1-nano-2025-04-14 | S | full | generation | BERTScore, regular prompt, child reviews=0.84 (n=15) | low | - | LLMs Do Not See Age: Assessing Demographic Bias in Automa... |
| W4404355620 | ineligible | o3-mini-2025-01-31 | S | none | mcq | NeoSQuAD accuracy score curve s(p)=n/a (n=?) | low | data_closed, no_number, no_prompt | Enhancing LLM Evaluations: The Garbling Trick |
| W4417438236 | maybe | gpt-5-2025-08-07 | S | full | classification | accuracy=0.76 (n=100) | mid | - | Evaluating Multimodal Large Language Model (LLM) (Generat... |
| W4416036248 | maybe | gpt-4-turbo-2024-04-09 | S | partial | other | sample-level Spearman rho with human scores, SummEval average over 4 dimensions (CheckE... | high | - | CheckEval: A reliable LLM-as-a-Judge framework for evalua... |
| W4411119258 | ineligible | dead-preview | A | full | other | none=n/a (n=?) | low | dead_alias, no_number | FollowIR: Evaluating and Teaching Information Retrieval M... |
| W4416036278 | ineligible | gpt-4-turbo-2024-04-09 | B | partial | generation | Hits@1 accuracy, IO baseline, AdvHotpotQA=46.4 (n=308) | mid | no_prompt | HydraRAG: Structured Cross-Source Enhanced Large Language... |
| W4411119753 | ineligible | gpt-4-turbo-2024-04-09 | S | none | classification | accuracy, Movie Review, unobfuscated prompts=0.957 (n=?) | low | no_prompt | EmojiPrompt: Generative Prompt Obfuscation for Privacy-Pr... |
| W4411119835 | ineligible | dead-preview | S | partial | generation | GPT-4-judged role-playing score, mean over 8 metrics, English scenes=3.926 (n=?) | low | dead_alias, aux_model_dead | CharacterBox: Evaluating the Role-Playing Capabilities of... |
| W4411120447 | maybe | gpt-4-turbo-2024-04-09 | B | full | other | global Pearson correlation with human scores (GPT4_T=0_1_5), averaged over 10 meta-eval... | high | - | Analyzing and Evaluating Correlation Measures in NLG Meta... |
| W4403573504 | ineligible | gpt-4-turbo-2024-04-09 | S | partial | classification | accuracy, Baseline prompting=0.58 (n=256) | mid | no_prompt | Athena: Retrieval-augmented Legal Judgment Prediction wit... |
| W7138319054 | ineligible | gpt-4.1-nano-2025-04-14 | B | partial | classification | macro F1 of the full amc pipeline=0.84 (n=?) | low | no_prompt | amc: The Automated Mission Classifier for Telescope Bibli... |
| W7197054169 | ineligible | o4-mini-2025-04-16 | C | partial | other | none=n/a (n=?) | low | no_number | JudgeArena: A Unified Framework for Reproducible LLM-Judg... |
| W4405432557 | maybe | gpt-4-turbo-2024-04-09 | S | full | generation | mixed-effects coefficient b of phenotypicality on standardized cosine similarity, GPT-4... | high | - | Vision-Language Models Generate More Homogeneous Stories ... |
| W4414376709 | ineligible | gpt-4-turbo-2024-04-09 | C | none | other | none=n/a (n=?) | low | no_number | Case Analysis of Generative AI Adoption and Application B... |
| W4407423562 | ineligible | unresolved | S | full | classification | accuracy, zero-shot, MRI + cognitive tests, 75% confidence threshold=0.744 (n=?) | low | webui, data_closed | Can ChatGPT Diagnose Alzheimer's Disease? |
| W4416036514 | ineligible | gpt-4-turbo-2024-04-09 | B | partial | classification | p-value of reasonableness contingency (copy-correct items judged reasonable vs unreason... | low | human_outcome | Humans Hallucinate Too: Language Models Identify and Corr... |
| W7167980616 | ineligible | gpt-4.1-nano-2025-04-14 | S | none | classification | accuracy, baseline (unperturbed), averaged over 3 datasets=66.0 (n=300) | low | no_prompt | Evaluating LLM Robustness Under Domain-Specific Prompt Pe... |
| W7166847291 | ineligible | gpt-4.1-nano-2025-04-14 | B | partial | other | sub-concept matching system accuracy, without background (-BG)=0.46 (n=400) | low | no_prompt | Teaching Through Analogies: A Modular Pipeline for Educat... |
| W7166837475 | eligible | o3-mini-2025-01-31 | S | full | classification | macro F1, zero-shot (k=0), six PolitiFact labels=0.27 (n=6137) | high | - | Large Language Models Require Curated Context for Reliabl... |
| W4414580657 | eligible | o4-mini-2025-04-16 | S | full | classification | misleading-intent detection accuracy, text-modified split, implication-oriented (I), av... | high | - | Seeing Through Deception: Uncovering Misleading Creator I... |
| W7204180844 | ineligible | gpt-5-mini-2025-08-07 | B | none | agentic | EKB completeness / exploration cost per scene=n/a (n=6) | low | no_prompt, data_closed | ExploreAI: Agentic Exploration Knowledge Bases for Reprod... |
| W4403280389 | ineligible | unresolved | C | full | generation | ROUGE-1, PubMed=n/a (n=?) | low | dead_alias, no_number | Enhancing abstractive summarization of scientific papers ... |
| W4412888351 | eligible | gpt-4-turbo-2024-04-09 | S | full | generation | pass@1 (greedy), HumanEval Pro, 0-shot=72.0 (n=164) | mid | - | HumanEval Pro and MBPP Pro: Evaluating Large Language Mod... |
| W4404781673 | ineligible | gpt-4o-2024-05-13 | A | full | other | ROC accuracy of the trained SimLLM detector on GPT-4o-generated sentences=0.816 (n=?) | low | no_number | SimLLM: Detecting Sentences Generated by Large Language M... |
| W4411119967 | ineligible | dead-preview | S | partial | other | AUROC, verbalized confidence, GPT-4=69.28 (n=?) | low | dead_alias | MAQA: Evaluating Uncertainty Quantification in LLMs Regar... |
| W4401202726 | ineligible | gpt-4-turbo-2024-04-09 | B | partial | generation | 5-shot accuracy on iGSM-med_pq per op=n/a (n=30) | low | no_number | Physics of Language Models: Part 2.1, Grade-School Math a... |
| W4404783276 | ineligible | gpt-4-turbo-2024-04-09 | C | none | generation | none=n/a (n=?) | low | no_number | How Do Your Code LLMs perform? Empowering Code Instructio... |
| W4404345923 | maybe | gpt-4-turbo-2024-04-09 | B | partial | mcq | action prediction accuracy, overall, 5-shot, 'Mini' test=39.6 (n=117) | low | - | LogiCity: Advancing Neuro-Symbolic AI with Abstract Urban... |
| W4409363588 | ineligible | gpt-4-turbo-2024-04-09 | C | none | generation | pass@1 HumanEval(+)=90.2 (n=164) | low | no_number | InverseCoder: Self-improving Instruction-Tuned Code LLMs ... |
| W4412888298 | ineligible | gpt-4-turbo-2024-04-09 | S | full | generation | neutrality score ntr_gen, EnBBG, mean over 5 evaluation sets=0.6362 (n=464) | high | aux_model_dead | Social Bias Benchmark for Generation: A Comparison of Gen... |
| W4414586612 | ineligible | gpt-4-turbo-2024-04-09 | S | none | mcq | accuracy disparity, Male vs Female, FairMedQA=16.85 (n=801) | high | no_prompt | FairMedQA: Benchmarking Bias in Large Language Models for... |
| W4406233392 | ineligible | gpt-4-turbo-2024-04-09 | S | partial | classification | Cohen kappa vs expert diagnosis, primary prompt=0.95 (n=969) | mid | data_closed, no_prompt | Artificial intelligence for detecting anaphylaxis in elec... |
| W4404649393 | ineligible | gpt-4-turbo-2024-04-09 | S | partial | generation | Frama-C WP proved goals, ACSL-only specification, case study 1=33 (n=33) | low | data_closed | Towards Specification-Driven LLM-Based Generation of Embe... |
| W4415722963 | ineligible | unresolved | S | partial | mcq | accuracy on TYT questions=0.425 (n=120) | low | webui | Performance of Generative Artificial Intelligence Models ... |
| W4415974738 | ineligible | unresolved | S | full | classification | exact-diagnosis concordance with Hologic diagnosis=0.47 (n=100) | low | webui | Evaluating Large Language Models in Interpreting Cervical... |
| W7127629951 | ineligible | unresolved | C | none | classification | none=n/a (n=?) | low | no_number | Psychological distance and efficacy: analyzing the framin... |
| W4405562439 | ineligible | unresolved | C | none | other | none=n/a (n=?) | low | no_number | A Survey of Calibration Process for Black-Box LLMs |

## Observations

- gpt-4-turbo is the live ID in 36 of the 50 papers, but only 10 of them print the 2024-04-09 snapshot (or 'April 2024'); the others are resolved by the date rule, and 4 turn out to be dead previews (1106/0125) or the April-2023 Bing Chat build.
- Role C (citation-only) accounts for 10 papers: a survey, a systematic review, a UTAUT case study, a Frontiers content-analysis paper, code-LLM papers that copy leaderboard numbers for GPT-4-Turbo-2024-04-09 (XCoder, InverseCoder), and related-work tables (WebWorld, JudgeArena, financial QA).
- Judge/parser-only usage (role A) appears in 4 papers (CodeTool, translation study, FollowIR, SimLLM); in each case the actual subject is a dead preview or a trained detector, so no re-runnable number attaches to the live model. CharacterBox additionally has a dead 1106 evaluator (aux_model_dead), as does BBG (gpt-4-0613 as MRC scorer).
- The most frequent blocker is the missing prompt (11 papers), and in 8 of them everything else is in place (HydraRAG IO baseline, EmojiPrompt, Athena, amc, public-health perturbations, analogy pipeline, FairMedQA, anaphylaxis). Several state that prompts live in a GitHub repository rather than in the paper.
- Five papers used consumer interfaces (Bing Chat, ChatGPT Plus with file upload, ChatGPT image upload, Copilot, chat apps for archival terms) and are blocked by webui, usually together with closed or unlisted items; the two API-based medical papers (o1 health-law MCQs, GPT-5 MRNet) are 'maybe' only because the exact item set is not printed.
- The five eligible papers split into cheap (age-bias summarization with gpt-4.1-nano; HumanEval Pro with gpt-4-turbo-2024-04-09; DisasterQA MCQs) and expensive (political fact-checking with o3-mini on 6,137 claims; DeceptionDecoded with o4-mini on 6,000 multimodal instances), the latter two exceeding $30 at three seeds because of reasoning-model pricing and image inputs.
