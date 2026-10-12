# Tier B maybe-pass 1, group maybe_2 (35 papers)

Source: `data/tierb_triage/maybe_2.csv`. Each record in this directory now carries a top-level `resolution` object (`gap`, `plan`, `approximation`, `needs_repo`, `repo_url`, `needs_pdf_figure`, `resolved_by: maybe-pass-1`). Decisions use only the extracted paper text and the public datasets it names; nothing was fetched and no model was called.

Counts: upgraded to eligible 15, still maybe (needs_repo) 19, still maybe (needs_pdf_figure only) 0, downgraded to ineligible 1.

Gap categories: other 11, items_in_repo 8, prompt_in_repo 5, placeholder_prompt 4, subset_unlisted 3, evaluator_in_repo 3, unreleased 1. W4404783604 needs both the repository and Figure 3 (counted under needs_repo).

| wid | new verdict | gap | needs_repo | cost tier | title |
|---|---|---|---|---|---|
| W4392822190 | maybe | prompt_in_repo | yes | high | LiveCodeBench: Holistic and Contamination Free Evaluation o… |
| W4399911276 | eligible | subset_unlisted | no | low | Whiteboard-of-Thought: Thinking Step-by-Step Across Modalit… |
| W4400141990 | maybe | evaluator_in_repo | yes | mid | AI Benchmark Half-Life in Recursive Corpora: A Theory of Va… |
| W4402345509 | eligible | other | no | low | LAB-Bench: Measuring Capabilities of Language Models for Bi… |
| W4402712721 | maybe | items_in_repo | yes | mid | Prompting Large Language Models for Supporting the Differen… |
| W4403322813 | eligible | other | no | mid | KGARevion: An AI Agent for Knowledge-Intensive Biomedical QA |
| W4403370432 | eligible | other | no | low | An Evaluation of Requirements Modeling for Cyber-Physical S… |
| W4403758464 | eligible | other | no | mid | LLMs Still Can't Plan; Can LRMs? A Preliminary Evaluation o… |
| W4403882351 | eligible | other | no | high | RLEF: Grounding Code LLMs in Execution Feedback with Reinfo… |
| W4404260877 | maybe | other | yes | high | VipAct: Visual-Perception Enhancement via Specialized VLM A… |
| W4404311505 | maybe | items_in_repo | yes | high | MaCTG: Multi-Agent Collaborative Thought Graph for Automati… |
| W4404352371 | eligible | other | no | high | EEE-Bench: A Comprehensive Multimodal Electrical And Electr… |
| W4404781124 | maybe | items_in_repo | yes | low | ValueScope: Unveiling Implicit Norms and Values via Return … |
| W4404782619 | maybe | items_in_repo | yes | low | Words Matter: Reducing Stigma in Online Conversations about… |
| W4404783604 | maybe | items_in_repo | yes | high | LogicAsker: Evaluating and Improving the Logical Reasoning … |
| W4404990976 | eligible | other | no | low | Thai Financial Domain Adaptation of THaLLE -- Technical Rep… |
| W4405425991 | eligible | subset_unlisted | no | mid | ProteinGPT: Multimodal LLM for Protein Property Prediction … |
| W4406489787 | maybe | other | yes | high | MALADE: Orchestration of LLM-powered Agents with Retrieval … |
| W4409361799 | eligible | placeholder_prompt | no | high | Knowledge Tagging with Large Language Model Based Multi-Age… |
| W4411113098 | maybe | items_in_repo | yes | low | TESTEVAL: Benchmarking Large Language Models for Test Case … |
| W4411120327 | eligible | placeholder_prompt | no | mid | Investigating the Shortcomings of LLMs in Step-by-Step Lega… |
| W4411120604 | maybe | other | yes | mid | Do LLMs Have Distinct and Consistent Personality? TRAIT: Pe… |
| W4412889923 | maybe | evaluator_in_repo | yes | high | ASPERA: A Simulated Environment to Evaluate Planning for Co… |
| W4414789220 | ineligible | unreleased | no | mid | Application of Large Language Models (LLM) for Automatic Cl… |
| W4415332119 | maybe | evaluator_in_repo | yes | mid | Non-Collaborative User Simulators for Tool Agents |
| W4416036248 | maybe | items_in_repo | yes | high | CheckEval: A reliable LLM-as-a-Judge framework for evaluati… |
| W4416339332 | eligible | other | no | high | "As Eastern Powers, I will veto." : An Investigation of Nat… |
| W4417409739 | maybe | prompt_in_repo | yes | mid | ProMQA-Assembly: Multimodal Procedural QA Dataset on Assemb… |
| W7125760104 | maybe | prompt_in_repo | yes | low | SycoEval-EM: Sycophancy Evaluation of Large Language Models… |
| W7135428876 | eligible | placeholder_prompt | no | mid | Large Language Models for Biomedical Article Classification |
| W7140134105 | maybe | prompt_in_repo | yes | low | RoD-TAL: A Benchmark for Answering Questions in Romanian Dr… |
| W7150802891 | eligible | subset_unlisted | no | high | Are large pre-trained vision language models effective cons… |
| W7164614711 | eligible | placeholder_prompt | no | low | I Understand How You Feel: Enhancing Deeper Emotional Suppo… |
| W7166826703 | maybe | prompt_in_repo | yes | mid | COMPASS: A Framework for Evaluating Organization-Specific P… |
| W7197053618 | maybe | items_in_repo | yes | high | AI-Assisted Peer Review Across Research Communities: From R… |

Recurring gap types

- Inputs that exist only in the authors' repository (items_in_repo 8, prompt_in_repo 5, evaluator_in_repo 3): benchmark items, checklists, scenario strings or the execution/simulation harness are cited to a GitHub link rather than printed. All 16 stay "maybe"; three of them (VipAct, COMPASS, the peer-review paper) mention a release but give no URL in the extracted text, and TRAIT only promises a release, so those four have `repo_url` empty.
- Unlisted random subsets or exemplars (subset_unlisted 3, plus the few-shot slots in placeholder_prompt 4): the paper draws 250 items, 35 proteins, five in-context images or two demonstrations per concept at random without a seed. These upgrade to eligible with a seeded re-draw and a set-level, explicitly approximate comparison.
- n unstated but derivable (4 of the 11 "other" cases: KGARevion, CPSBench, the UNSC-veto paper, LAB-Bench private split): the text defines the evaluated set ("all expert-level MCQs", "2,633 sentences", "only the 66 non-adopted resolutions", "public 80% split"), so the count comes from the public dataset and the record is eligible; call counts can differ from the first-pass estimate (veto: ~200 per persona; AfriMed-QA: likely several thousand).
- Execution-based scoring with a generic harness (RLEF/CodeContests, EEE-Bench answer extraction, PlanBench/VAL): eligible when the tests or validator are part of the public dataset; still maybe when the runner is the authors' own (TESTEVAL, MaCTG, ASPERA, LiveBench).
- Snapshot or prompt-variant ambiguity that the text resolves indirectly (PlanBench "GPT-4 Turbo" with no version; THaLLE's three system prompts, settled by the Appendix C example; LogicAsker headline only in a figure): recorded as an approximation rather than a blocker.
- One dead end: the work-accident classification paper scores against expert labels from an in-press prior study that are not released anywhere, so it is ineligible with `data_closed`.
