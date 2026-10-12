# Tier B run configs, group 3 (32 papers)

Source list: `halflife/data/tierb_triage/config_3.csv`. Configs: `halflife/harness/tierb/configs/<wid>.json` (schema: `CONFIG_SCHEMA.md`).

## Counts by status

- ready: 16
- needs_download_check: 5
- needs_human: 11
- total estimated cost: about $2,393 for all 32 ($573 for the ready set; PILOT-Bench alone is $929 and the NLG correlation study $344)

## Table

| wid | status | model | task | n_items | seeds | est_usd | items source | title |
|---|---|---|---|---|---|---|---|---|
| W4399317891 | ready | gpt-4-turbo-2024-04-09 | classification | 1,319 | 3 | 79 | hf: bench-llm/or-bench | OR-Bench: An Over-Refusal Benchmark for Large Lang... |
| W4399911276 | ready | gpt-4o-2024-05-13 | classification | 250 | 3 | 4 | hf: tasksource/bigbench | Whiteboard-of-Thought: Thinking Step-by-Step Acros... |
| W4401545735 | ready | gpt-4o-2024-05-13 | classification | 2,264 | 3 | 34 | hf: takala/financial_phrasebank | Designing Heterogeneous LLM Agents for Financial S... |
| W4403322813 | needs_download_check | gpt-4-turbo-2024-04-09 | mcq | 2,000 | 3 | 60 | hf: intronhealth/afrimedqa_v2 | KGARevion: An AI Agent for Knowledge-Intensive Bio... |
| W4403556032 | ready | gpt-4-turbo-2024-04-09 | mcq | 1,272 | 3 | 57 | hf: bigbio/med_qa | Enhancing Healthcare LLM Trust with Atypical Prese... |
| W4403786592 | needs_human | gpt-4-turbo-2024-04-09 | classification | 1,000 | 3 | 30 | github: github.com/usmaann/Depression_Severity_Dataset | A Comprehensive Evaluation of Large Language Model... |
| W4403885225 | ready | gpt-4-turbo-2024-04-09 | classification | 500 | 1 | 10 | github: github.com/Y0oMu/LLM-Judge-Bias-Dataset | Justice or Prejudice? Quantifying Biases in LLM-as... |
| W4404352371 | ready | gpt-4-turbo-2024-04-09 | mcq | 2,860 | 1 | 59 | hf: afdsafas/EEE-Bench | EEE-Bench: A Comprehensive Multimodal Electrical A... |
| W4404781531 | needs_human | gpt-4o-2024-05-13 | mcq | 807 | 3 | 12 | github: github.com/luffycodes/MalAlgoQA-Dataset | MalAlgoQA: Pedagogical Evaluation of Counterfactua... |
| W4404782941 | needs_human | gpt-4-turbo-2024-04-09 | classification | 742 | 3 | 22 | github: github.com/Prasoon1207/llm-science-miscommunication | Can LLMs replace Neil deGrasse Tyson? Evaluating t... |
| W4404970691 | needs_human | gpt-4-turbo-2024-04-09 | classification | 800 | 3 | 36 | hf: aharley/rvl_cdip | Zero-Shot Prompting and Few-Shot Fine-Tuning: Revi... |
| W4405355440 | needs_human | gpt-4o-2024-05-13 | mcq | 3,268 | 1 | 98 | github: github.com/google-deepmind/neptune -> https://storage.mtls.c... | Neptune: The Long Orbit to Benchmarking Long Video... |
| W4406058562 | needs_download_check | gpt-4-turbo-2024-04-09 | generation | 100 | 1 | 23 | zenodo: https://zenodo.org/record/7152317 | Applicability of Large Language Models and Generat... |
| W4407374917 | ready | gpt-4o-2024-05-13 | classification | 100 | 3 | 2 | github: github.com/filipgdorm/eco-llm: task_data/task1/task1_coordin... | Large language models possess some ecological know... |
| W4410280647 | needs_download_check | o3-mini-2025-01-31 | other | 2,150 | 1 | 108 | hf: cais/hle | Humanity's Last Exam |
| W4411119226 | needs_human | gpt-4-turbo-2024-04-09 | generation | 120 | 3 | 4 | in_paper: Table 1 | AI with Emotions: Exploring Emotional Expressions ... |
| W4411120175 | needs_human | gpt-4o-2024-05-13 | generation | 166 | 3 | 20 | zenodo: https://zenodo.org/records/11299894 | Large Language Models Reflect Human Citation Patte... |
| W4411120447 | needs_human | gpt-4-turbo-2024-04-09 | other | 34,416 | 1 | 344 | url: SummEval | Analyzing and Evaluating Correlation Measures in N... |
| W4412888351 | ready | gpt-4-turbo-2024-04-09 | generation | 164 | 3 | 5 | hf: CodeEval-Pro/humaneval-pro | HumanEval Pro and MBPP Pro: Evaluating Large Langu... |
| W4412944996 | ready | gpt-4-turbo-2024-04-09 | other | 3,000 | 1 | 45 | hf: OpenStellarTeam/Chinese-SimpleQA | Chinese SimpleQA: A Chinese Factuality Evaluation ... |
| W4414992335 | ready | o3-2025-04-16 | mcq | 2,548 | 1 | 127 | hf: anvo25/vmmu | VMMU: A Vietnamese Multitask Multimodal Understand... |
| W4416034223 | ready | gpt-4o-2024-05-13 | other | 216 | 3 | 3 | github: github.com/kenoharada/Multiple-Instructions-Following | When Instructions Multiply: Measuring and Estimati... |
| W4416035248 | ready | gpt-4-turbo-2024-04-09 | classification | 10,342 | 1 | 103 | github: github.com/SCUNLP/CANDY | CANDY: Benchmarking LLMs' Limitations and Assistiv... |
| W4416157016 | needs_human | gpt-4.1-nano-2025-04-14 | generation | 15 | 3 | 1 | github: github.com/Favour-Yahdii/lllms_dont_see_age | LLMs Do Not See Age: Assessing Demographic Bias in... |
| W7104384491 | needs_human | o3-2025-04-16 | classification | 15,481 | 1 | 929 | hf: Yehoon/pilot-bench | PILOT-Bench: A Benchmark for Legal Reasoning in th... |
| W7134885605 | ready | gpt-5-2025-08-07 | classification | 200 | 3 | 24 | github: github.com/JuliaWy/Full-text-vs-Abstract | More Signal vs. More Noise - Comparing Full Text a... |
| W7140084705 | ready | gpt-4.1-nano-2025-04-14 | classification | 138 | 3 | 1 | github: github.com/holi-lab/psychometric-contamination | Quantifying Data Contamination in Psychometric Eva... |
| W7140147579 | needs_human | o3-2025-04-16 | classification | 100 | 3 | 24 | hf: sma1-rmarud/plat-kor-mc | Taxation Perspectives from Large Language Models: ... |
| W7159577685 | ready | gpt-4-turbo-2024-04-09 | other | 25 | 3 | 1 | in_paper: Sec. 3.2 | Breaking the Chains of Probability: Neutrosophic L... |
| W7164614711 | ready | gpt-4.1-nano-2025-04-14 | classification | 12,780 | 3 | 19 | github: github.com/zihaurpang/Multilingual-Emotional-Validation | I Understand How You Feel: Enhancing Deeper Emotio... |
| W7166837475 | needs_download_check | o3-mini-2025-01-31 | classification | 6,137 | 1 | 61 | zenodo: https://doi.org/10.5281/zenodo.17693220 | Large Language Models Require Curated Context for ... |
| W7197053912 | needs_download_check | gpt-5-mini-2025-08-07 | extraction | 3,211 | 3 | 48 | github: github.com/COMBINI-Hub/Multi_Agent_Relation_Extraction | ANCHOR-RE: An Agentic Neuro-Symbolic Framework for... |

## needs_human reasons (first open point of each)

- W4403786592: The exact SEV-4 zero-shot prompt is only in Figure 1 (image); copy it from the PDF before running (the template above is a reconstruction).
- W4404781531: The dataset is distributed only on request via a Google Form linked from github.com/luffycodes/MalAlgoQA-Dataset; someone must request and receive it.
- W4404782941: Table 3 abbreviates three exemplar 'Reason' passages; the verbatim prompt needs them (the repo's codes/ folder should hold the prompt) or the run must use a shortened prompt.
- W4404970691: OCR engine: the paper used Amazon Textract (paid AWS service, account required); the Tesseract fallback changes the model input.
- W4405355440: Annotation JSON sits behind a Google sign-in wall (storage.mtls link) and the 2,405 YouTube videos must be downloaded (availability drift, ToS).
- W4411119226: Verify the decoded Figure 1 system prompt against the PDF (font-shifted extraction; numeric bounds and punctuation uncertain).
- W4411120175: Step 4 post-processing was run with GPT-4-0613 (retired); choose a substitute (e.g. gpt-4o-2024-05-13 with the printed post-processing prompt) or a rule-based reference parser.
- W4411120447: Assemble the 30 meta-evaluation subsets (texts + human scores) from six source datasets; the released data.csv contains scores only.
- W4416157016: The per-review primary-study sets are not released; reconstruct them from each review's reference list via PubMed/PMC identifiers (Sec. 3.1) with the repo pipeline.
- W7104384491: Copy the Issue Type prompt (Figure 8, Appendix D.3) from the PDF; the text extraction does not contain it.
- W7140147579: Language: the paper ran Korean prompts on Korean precedents (Figure 3 is a GPT-4o translation); decide between plat-kor-mc with a back-translated prompt and plat-eng-mc with the printed English prompt.

## Recurring difficulties

- Prompts that exist only as figures or glyph-shifted text (SEV-4 in Figure 1 of W4403786592, Figure 1 of W4411119226, the Issue Type prompt of W7104384491) cannot be copied from the extracted text; these need the PDF.
- Datasets behind gates or above the 50 MB limit (AfriMed-QA gated CSV, HLE 274 MB parquet, UK-Abs 98 MB zip, OSoMe and citation-pattern Zenodo tarballs >1 GB, PILOT-Bench 55 MB tarball) leave column names, subset ids or counts unverified, hence needs_download_check.
- Prompts printed with abbreviated or translated parts (SCiPS-QA exemplar reasons '...', RVL-CDIP class list '[...]', PLAT's English translation of a Korean prompt, CANDY's Chinese vs English versions) force a reconstruction decision that the runner cannot make on its own.
- Inputs that must be regenerated (Textract OCR for RVL-CDIP, YouTube frames + ASR for Neptune, PubMed abstract sets for W4416157016, Semantic Scholar matching plus a retired post-processing model for W4411120175) turn a prompt-only re-execution into a pipeline job.
- Reasoning models (o3, o3-mini, gpt-5 family) ignore temperature and the schema's params object has no reasoning_effort slot, so the effort level is recorded in params_source. Two claim records disagree with the paper's own metric definition (SCiPS-QA MACC covers all 742 questions, not the 510 closed ones; W4403786592 defines BA in two ways).
