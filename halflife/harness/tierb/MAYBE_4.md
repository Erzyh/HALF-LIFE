# Tier B maybe-pass 1, group 4 (34 records)

Source: `halflife/data/tierb_triage/maybe_4.csv`. Each record now carries a top-level `resolution` object (`resolved_by: maybe-pass-1`) and an updated `verdict`; no other field was changed except `blockers` on the two downgraded records (`data_closed` added).

## Counts

| outcome | n |
|---|---|
| upgraded to eligible | 15 |
| still maybe (needs_repo) | 15 |
| still maybe (needs_pdf_figure) | 2 |
| downgraded to ineligible | 2 |
| total | 34 |

## Records

| wid | new verdict | gap | needs_repo | cost tier | title |
|---|---|---|---|---|---|
| W4399317891 | eligible | other | no | mid | OR-Bench: An Over-Refusal Benchmark for Large Language Model |
| W4400023054 | maybe | evaluator_in_repo | yes | high | BigCodeBench: Benchmarking Code Generation with Diverse Func |
| W4400518691 | maybe | other | yes | high | InsightBench: Evaluating Business Analytics Agents Through M |
| W4402426686 | eligible | other | no | low | SAFETY-J: Evaluating Safety with Critique |
| W4402954433 | maybe | items_in_repo | yes | mid | Beyond ChatGPT: Enhancing Software Quality Assurance Tasks w |
| W4403345821 | maybe | prompt_in_repo | yes | high | VHELM: A Holistic Evaluation of Vision Language Models |
| W4403666370 | maybe | prompt_as_image | no | high | United in Diversity? Contextual Biases in LLM-Based Predicti |
| W4403786592 | eligible | subset_unlisted | no | mid | A Comprehensive Evaluation of Large Language Models on Menta |
| W4403885480 | eligible | other | no | low | AutoML-Agent: A Multi-Agent LLM Framework for Full-Pipeline  |
| W4404304526 | maybe | items_in_repo | yes | low | AskBeacon -- Performing genomic data exchange and analytics  |
| W4404342653 | maybe | evaluator_in_repo | yes | mid | Constructing Multimodal Datasets from Scratch for Rapid Deve |
| W4404470015 | eligible | subset_unlisted | no | low | Comparative Performance of Claude and GPT Models in Basic Ra |
| W4404781910 | maybe | prompt_in_repo | yes | low | OffsetBias: Leveraging Debiased Data for Tuning Evaluators |
| W4404783148 | eligible | placeholder_prompt | no | mid | VIVA: A Benchmark for Vision-Grounded Decision-Making with H |
| W4404970691 | eligible | subset_unlisted | no | mid | Zero-Shot Prompting and Few-Shot Fine-Tuning: Revisiting Doc |
| W4405355440 | eligible | other | no | high | Neptune: The Long Orbit to Benchmarking Long Video Understan |
| W4405433067 | ineligible | unreleased | no | low | Atomic Learning Objectives Labeling: A High-Resolution Appro |
| W4406840430 | maybe | prompt_as_image | no | high | Can OpenAI o1 Reason Well in Ophthalmology? A 6,990-Question |
| W4410417118 | eligible | other | no | low | ChatGPT Is Still Not Good Enough at Giving Care-Seeking Advi |
| W4411119839 | maybe | other | yes | high | IrokoBench: A New Benchmark for African Languages in the Age |
| W4411120447 | eligible | other | no | high | Analyzing and Evaluating Correlation Measures in NLG Meta-Ev |
| W4412887747 | maybe | prompt_in_repo | yes | mid | Rethinking Table Instruction Tuning |
| W4414494504 | eligible | other | no | mid | PGxRAG: A Retrieval Augmented Generation supported Pharmacog |
| W4415145303 | maybe | prompt_in_repo | yes | high | Toward Scientific Reasoning in LLMs: Training from Expert Di |
| W4416034538 | eligible | other | no | high | FinEval-KR: A Financial Domain Evaluation Framework for Larg |
| W4416037849 | eligible | other | no | mid | CRAB: A Benchmark for Evaluating Curation of Retrieval-Augme |
| W4417210220 | maybe | prompt_in_repo | yes | mid | PRISM: Prompt-Refined In-Context System Modelling for Financ |
| W7125352815 | maybe | evaluator_in_repo | yes | high | SciCoQA: Quality Assurance for Scientific Paper--Code Alignm |
| W7134094238 | eligible | other | no | low | BioLLMAgent: A Hybrid Framework with Enhanced Structural Int |
| W7140099019 | eligible | other | no | high | When Does Auxiliary Modality Matter in Solving Geometric Pro |
| W7141772025 | maybe | evaluator_in_repo | yes | high | Qworld: Question-Specific Evaluation Criteria for LLMs |
| W7161451968 | maybe | other | yes | high | ViMU: Benchmarking Video Metaphorical Understanding |
| W7166799387 | ineligible | unreleased | no | low | Diagnosing and Mitigating Sycophancy and Skepticism in LLM C |
| W7170989516 | maybe | prompt_in_repo | yes | high | Auto-Fill: Learning to Predict Missing Values Accurately wit |

## Recurring gap types

- Repository-only pieces are the largest group (15/34): prompt wording that the text only describes or exemplifies (Genome-Bench, Auto-Fill, AIT-QA in TAMA, PRISM's FinanceBench baseline, OffsetBias's GPT-4o template), execution harnesses or agent scaffolds (BigCodeBench, InsightBench, SciCoQA, HELM run specs, the official HealthBench grader, Heron-Bench's judge protocol), and author-built item sets or auxiliary inputs (AskBeacon questions, FuseFL SBFL/test inputs, IrokoBench's snapshot logs, ViMU's unextracted links). None of these can be closed from the PDF alone.
- Unlisted subsets of public datasets (DepSeverity 1,000 posts, ROCOv2 100 images, RVL-CDIP 160x5, CRAB's 40/60 reference draws) close with a seeded re-sample and a set-level comparison; the `approximation` field records the expected spread.
- Several 'n unclear' gaps were extraction misses, not real gaps: OR-Bench's 1,319 (Appendix U), FinEval-KR's 9,782 (Sec. 3), and the correlation paper's 34,416 scorings derivable from Table 1; VIVA's Level-1 prompt was likewise present in the Figure 10 text dump.
- Judges were under-read in the first pass: SAFETY-J names Qwen-72B-Chat (open weights) as the AIU judge; OR-Bench's undated 'GPT-4' judge and the geometry paper's Gemini-2.0-flash-lite equivalence check are substitutable with a documented approximation.
- Two prompts exist only as figure images (EU elections Figure 1, o1 ophthalmology Figure 1) and two datasets were never released (expert LO labels; CausalT3-Seed vignettes); multimodal preprocessing (Neptune, ViMU frame sampling) is the remaining unspecified detail that has to be assumed or read from code.
