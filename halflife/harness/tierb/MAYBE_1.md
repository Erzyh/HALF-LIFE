# Tier B maybe-pass 1: group maybe_1 (35 papers)

Input: `halflife/data/tierb_triage/maybe_1.csv`. Each record in `halflife/harness/tierb/<Wid>.json` now carries a `resolution` object (gap, plan, approximation, needs_repo, repo_url, needs_pdf_figure, resolved_by = maybe-pass-1) and an updated `verdict`. Resolved from the paper text and the public record only; nothing was fetched and no model was called.

## Counts

| outcome | n |
|---|---|
| upgraded to eligible | 15 |
| still maybe (needs_repo) | 17 |
| still maybe (needs_pdf_figure) | 3 |
| downgraded to ineligible | 0 |

Gap categories: other 11, items_in_repo 10, prompt_in_repo 4, subset_unlisted 4, placeholder_prompt 2, evaluator_in_repo 2, prompt_as_image 2. W4417302310 needs both the PDF figure and the repository and is counted under needs_pdf_figure.

## Records

| wid | new verdict | gap | needs_repo | cost tier | title |
|---|---|---|---|---|---|
| W4386395478 | eligible | other | no | low | Large Language Models as Data Preprocessors |
| W4399598180 | eligible | other | no | high | HalluDial: A Large-Scale Benchmark for Automatic Dialogue... |
| W4400103831 | maybe | prompt_in_repo | yes | low | BADGE: BADminton report Generation and Evaluation with LLM |
| W4401545735 | eligible | placeholder_prompt | no | mid | Designing Heterogeneous LLM Agents for Financial Sentimen... |
| W4402670994 | maybe | other | no | mid | FinanceMATH: Knowledge-Intensive Math Reasoning in Financ... |
| W4403052068 | maybe | prompt_in_repo | yes | low | Large language models for abstract screening in systemati... |
| W4403347060 | eligible | placeholder_prompt | no | mid | Multi-Session Client-Centered Treatment Outcome Evaluatio... |
| W4403707291 | maybe | evaluator_in_repo | yes | high | CORE-Bench: Fostering the Credibility of Published Resear... |
| W4403815758 | maybe | items_in_repo | yes | low | Wait, but Tylenol is Acetaminophen... Investigating and I... |
| W4403900083 | maybe | items_in_repo | yes | mid | Context and System Fusion in Post-ASR Emotion Recognition... |
| W4404310870 | maybe | items_in_repo | yes | mid | ReasonAgain: Using Extractable Symbolic Programs to Evalu... |
| W4404345923 | maybe | items_in_repo | yes | low | LogiCity: Advancing Neuro-Symbolic AI with Abstract Urban... |
| W4404518515 | eligible | subset_unlisted | no | high | Automating Transparency Mechanisms in the Judicial System... |
| W4404782330 | eligible | other | no | high | Multi-hop Evidence Pursuit Meets the Web: Team Papelo at... |
| W4404783273 | maybe | evaluator_in_repo | yes | high | MMCode: Benchmarking Multimodal Large Language Models for... |
| W4404986534 | eligible | other | no | high | A Survey on LLM-as-a-Judge |
| W4405425460 | maybe | prompt_in_repo | yes | low | Leveraging Large Language Models for Enhanced Process Mod... |
| W4406058562 | eligible | other | no | high | Applicability of Large Language Models and Generative Mod... |
| W4407683641 | maybe | items_in_repo | yes | mid | Linking Cryptoasset Attribution Tags to Knowledge Graph E... |
| W4411112894 | eligible | other | no | mid | The Promises and Pitfalls of LLM Annotations in Dataset L... |
| W4411120249 | maybe | items_in_repo | yes | mid | From Introspection to Best Practices: Principled Analysis... |
| W4411120459 | maybe | items_in_repo | yes | mid | When2Call: When (not) to Call Tools |
| W4412889855 | eligible | subset_unlisted | no | high | Towards Robust Universal Information Extraction: Dataset,... |
| W4414758400 | eligible | other | no | low | Mitigation of Gender and Ethnicity Bias in AI-Generated S... |
| W4415161353 | maybe | prompt_as_image | no | high | Benchmarking Next-Generation Reasoning-Focused Large Lang... |
| W4416035248 | eligible | subset_unlisted | no | high | CANDY: Benchmarking LLMs' Limitations and Assistive Poten... |
| W4416259485 | maybe | items_in_repo | yes | low | Benchmarking PDF Accessibility Evaluation A Dataset and F... |
| W4417302310 | maybe | prompt_as_image | yes | high | AutoGEEval: A Multimodal and Automated Framework for Geos... |
| W7125649495 | maybe | items_in_repo | yes | low | Word-level Annotation of GDPR Transparency Compliance in... |
| W7134290865 | maybe | prompt_in_repo | yes | low | Agentic retrieval-augmented reasoning reshapes collective... |
| W7140124165 | eligible | other | no | high | MEENA (PersianMMMU): Multimodal-Multilingual Educational... |
| W7144391352 | eligible | other | no | mid | CALRK-Bench: Evaluating Context-Aware Legal Reasoning in... |
| W7164447651 | eligible | subset_unlisted | no | high | From Confident Closing to Silent Failure: Characterizing... |
| W7166809268 | maybe | other | yes | low | UNH @ Rag4Reports: A Broad Exploration of LLM-Judges for RAG |
| W7172172215 | maybe | items_in_repo | yes | low | When Specifications Conflict: A Symmetry-Based Framework... |

## Recurring gap types

- **The missing piece lives in the authors' repository (17 of 35).** Abbreviated prompts (BADGE, AIPA, radiology, the abstract-screening supplement), author-constructed item sets (LogiCity Mini test, Counting Characters, When2Call judge subset, the 67 MBPP conflict pairs, the 1,121 filtered GSM8K cases, the PERSIST drug pairs, GenSEC ASR hypotheses) and execution harnesses (CORE-Bench, MMCode) all resolve to `needs_repo`. Each is one repository visit from eligible; the paper alone does not close it.
- **n was simply not printed, but the set is fixed by the named release (5 upgrades).** HalluDial's full test split, the BABE train/development split, MEENA's 3,067-item English subset, the FPB 100%-agreement subset (identified from Table 2 class counts) and the Narayan et al. Restaurant test split. These went to eligible with n taken from the release.
- **Unlisted subsets or demonstrations drawn from public data (5 upgrades, all approximate).** Random few-shot demonstrations (RUIE), a per-model contamination-free subset defined by publish date (CANDY), a stratified judge sample rebuilt with printed regexes (false success), APM case selection plus OCR (judicial), few-shot demos for the data-preprocessing paper. The plan is a seeded reconstruction and a set-level comparison; the authors' exact items are not recoverable.
- **Human or auxiliary-model steps replaced by a stated approximation (4 records).** Manual gender coding of stories, GPT-4o-generated reference scores (psychotherapy), a retired Claude 3.5 Sonnet grader (Tylenol, still maybe for the item release), and an unspecified judge template (LLM-as-a-judge survey). Closable, but the comparison inherits a documented approximation.
- **Prompt or target number only readable from the PDF (3 records).** AutoGEEval Figure 7, the ophthalmology supplemental prompt figures, and FinanceMath Table 8 (the extraction duplicates Table 3's proprietary rows, so the dev-set target must be verified in the PDF).
- **Two records hinge on data whose release is not stated** (GDPR-Transparency-200; TREC Rag4Reports runs and NIST ranking). Both stay maybe with an explicit `data_closed` fallback in the plan rather than being downgraded on an unverified absence, so no record was downgraded.

