# Tier B maybe-resolution, group 3 (35 papers)

Source list: `data/tierb_triage/maybe_3.csv`. Each record now carries a top-level `resolution` object (gap category, plan, approximation, needs_repo, repo_url, needs_pdf_figure, resolved_by = maybe-pass-1).

Counts: upgraded to eligible 12, still maybe (needs_repo) 15, still maybe (needs_pdf_figure) 4, downgraded to ineligible 4.

| wid | new verdict | gap | needs_repo | cost tier | title |
|---|---|---|---|---|---|
| W4398865217 | maybe | prompt_as_image | no | low | Evaluating Large Language Models for Public Health Classifi… |
| W4399912745 | eligible | placeholder_prompt | no | high | ALiiCE: Evaluating Positional Fine-grained Citation Generat… |
| W4400480600 | maybe | prompt_as_image | no | low | Enhancing Computer Programming Education with LLMs: A Study… |
| W4402385945 | maybe | prompt_in_repo | yes | low | PLUGH: A Benchmark for Spatial Understanding and Reasoning… |
| W4402952718 | eligible | other | no | mid | Evaluating Large Language Models on Spatial Tasks: A Multi-… |
| W4403345251 | maybe | evaluator_in_repo | yes | low | ING-VP: MLLMs cannot Play Easy Vision-based Games Yet |
| W4403663202 | maybe | items_in_repo | yes | high | DSBench: How Far Are Data Science Agents from Becoming Data… |
| W4403783611 | maybe | prompt_in_repo | yes | high | Enhancing LLM-based Autonomous Driving Agents to Mitigate P… |
| W4403882451 | eligible | other | no | mid | Planning in Strawberry Fields: Evaluating and Improving the… |
| W4404261523 | maybe | items_in_repo | yes | mid | An Eye for an AI: Evaluating GPT-4o's Visual Perception Ski… |
| W4404313190 | maybe | items_in_repo | yes | mid | ControlAgent: Automating Control System Design via Novel In… |
| W4404370652 | ineligible | other | no | low | Data Fusion of Synthetic Query Variants With Generative Lar… |
| W4404781158 | eligible | other | no | low | MultiPragEval: Multilingual Pragmatic Evaluation of Large L… |
| W4404782629 | maybe | items_in_repo | yes | high | TopViewRS: Vision-Language Models as Top-View Spatial Reaso… |
| W4404792825 | eligible | other | no | low | Will LLMs Sink or Swim? Exploring Decision-Making Under Pre… |
| W4405090298 | maybe | prompt_as_image | no | mid | AI-Driven Day-to-Day Route Choice |
| W4405432557 | eligible | other | no | high | Vision-Language Models Generate More Homogeneous Stories fo… |
| W4406604156 | maybe | evaluator_in_repo | yes | high | ComplexFuncBench: Exploring Multi-Step and Constrained Func… |
| W4410274161 | maybe | figure_only_number | no | low | Implementing a context-augmented large language model to gu… |
| W4411119617 | maybe | prompt_in_repo | yes | low | MedEthicEval: Evaluating Large Language Models Based on Chi… |
| W4411120335 | eligible | other | no | mid | Does Liking Yellow Imply Driving a School Bus? Semantic Lea… |
| W4411549654 | maybe | items_in_repo | yes | mid | Comparative Analysis of Multimodal Large Language Models GP… |
| W4412944996 | eligible | other | no | high | Chinese SimpleQA: A Chinese Factuality Evaluation for Large… |
| W4414823918 | maybe | evaluator_in_repo | yes | high | Dr. Bench: A Multidimensional Evaluation for Deep Research… |
| W4416033907 | eligible | other | no | low | Challenging the Evaluator: LLM Sycophancy Under User Rebutt… |
| W4416036577 | eligible | placeholder_prompt | no | low | Cross-domain Rumor Detection via Test-Time Adaptation and L… |
| W4416437629 | maybe | items_in_repo | yes | mid | EngTrace: A Symbolic Benchmark for Verifiable Process Super… |
| W4417438236 | eligible | subset_unlisted | no | mid | Evaluating Multimodal Large Language Model (LLM) (Generativ… |
| W7133951874 | ineligible | unreleased | no | high | Performance of ChatGPT-o1 and DeepSeek-R1 on the health law… |
| W7139147531 | eligible | other | no | low | LLMs learn scientific taste from institutional traces acros… |
| W7140225398 | ineligible | unreleased | no | low | Large language model scoring of medical student reflection… |
| W7158422658 | maybe | evaluator_in_repo | yes | high | IntrAgent: An LLM Agent for Content-Grounded Information Re… |
| W7166528822 | ineligible | unreleased | no | low | Identifying Implicit Research Data References in Paper Cita… |
| W7167625526 | maybe | items_in_repo | yes | low | Mapping the otoactive landscape: an LLM-aided extraction of… |
| W7203709730 | maybe | prompt_in_repo | yes | low | Class Imbalance and Batch Effects in LLM-Based Screening fo… |

## Recurring gap types

- Repository-only pieces dominate the residual maybes (15 of 35): the exact prompt string (PLUGH, MedEthicEval, HUDSON driving agent, the Zenodo artifact of the screening study), the evaluator (ING-VP simulators, ComplexFuncBench replay harness, Dr. Bench annotation pipeline, IntrAgent loop) or hand-curated items that the paper only describes (ControlEval systems, EngTrace seeds, DSBench serialization, TopViewRS partial release, Medscape scrape, the 350 otoactive abstracts, the CG answer keys).
- Prompts and numbers locked in PDF figures (4 records): three prompt templates exist only as figure images (Figures 4-5, Figure 2, Figure 8) and one value is only a bar in Figure 3A; all are closable once the PDF is read.
- Human judging was the soft gap in three records (spatial tasks, MultiPragEval, otoactive curation); two of them upgrade because the released items carry answer keys, so automatic option matching or an LLM judge on the printed rubric gives an approximate set-level comparison.
- Unstated protocol details that the text itself resolves (n from repetition counts, snapshot by the alias rule, a prompt variant, a public prompt file, an external judge template, a stated embedding model) account for the other upgrades; each plan states the residual approximation.
- Four downgrades are data that never left the authors' hands or a licence: a purchased exam guidebook, Gemini-fabricated essays, unreleased citation labels, and an LDC-licensed retrieval corpus (recorded as data_closed).
