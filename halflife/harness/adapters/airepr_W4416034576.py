"""Card W4416034576 - AIRepr: An Analyst-Inspector Framework for Evaluating Reproducibility of LLMs in Data Science
(Zeng, Jin, Wang, Zheng, Li; Findings of EMNLP 2025, 10170-10201; doi 10.18653/v1/2025.findings-emnlp.539).
Repo Anonymous-2025-Repr/LLM-DS-Reproducibility @ 3b4a5a8f, MIT.

Claim re-measured (Table 6, DiscoveryBench, analyst o3-mini-2025-01-31, 239 tasks): adding the single reproducibility
sentence to the CoT prompt (RoT) raises Overall Reproducibility 55.23 -> 60.25 (+5.02 pp), accuracy 31.80 -> 33.05,
inexecutable code 13.81 -> 15.90. o3-mini is the analyst under test AND - by the decision below - the inspector.

Decisions 2026-09-19 (card key "decisions_2026_09_19", decided_by "project default, user delegated"): DiscoveryBench
only, the card's ~USD 65 option (QRData and StatQA neither run nor downloaded); the core claim is the within-model
RoT-vs-CoT method effect, not the cross-model ranking (three of the five analysts are dead or open-weight); the
inspector is o3-mini-2025-01-31 itself rather than the paper's gpt-4o-2024-11-20, per Section 5.6 / Figure 7
(r = 0.98 between the two inspectors), so nothing in the pipeline outlives the retiring model - with the caveat that
that r was measured on QRData and the paper reports "only minor score increases" for the o3-mini inspector, a level
shift that cancels in the within-model difference but not in the +/-10 pp level check; DiscoveryBench is ODC-By
(attribution only, verified from the allenai/discoverybench LICENSE at fetch time) so prompts embedding dataset
descriptions and column metadata are archived in full; per-paper cap USD 80 (analyst 45 / inspector 35).

Protocol, read out of the repository at run time (never copied): the analyst prompt is agents/prompt_template.py
cot_template rendered by the repo's own CoTPromptTemplate over utils/prepare_prompt.prepare_discoverybench_prompt and
the python_repl_ast tool description, with agent_instruction from experiments/get_agent.get_agent_instruction (CoT and
RoT differ by exactly one sentence); two calls per task (round 1 -> Workflow/Action/Action Input, local execution,
round 2 -> "Final Answer:"). The inspector prompts are eval/eval_prompt.py plus the generate_conclusion f-string, the
("system", ...) messages and the DiscoveryBench 1%-tolerance rider, all pulled out of eval/*.py with ast; scores are
parsed by the repo's own ScoreParser. Params: reasoning_effort "low", max_completion_tokens 4000 (paper Appendix H);
no temperature is sent - the original passed temperature=1 only because LangChain's AzureChatOpenAI demands a value
and 1 is the only value o3-mini accepts. Model-written code runs in a FRESH isolated interpreter (python -I -X utf8,
sockets blocked, wall-clock timeout); the repository itself exec()s in-process with no timeout and no isolation.

  --fetch-data  DiscoveryBench files listed in the repo's download_data.sh   --check    offline: tasks, prompts, scorer
  --dry-run     request lists, tokens, USD; no API calls                     --run      analyst -> code -> inspector
  --analyze     repr% per method, bootstrap CIs, judgment, run_meta.json     (only --run spends money)

Findings of --check (2026-09-19): all 239 tasks load and every referenced data file is present; the CoT and RoT prompts
differ by exactly the 140-character RoT sentence and nothing else; the sandbox, the repo's CoTOutputParser/ScoreParser
and the -1 inexecutable path behave as the repository's eval expects. Frictions are listed in FRICTIONS below and
repeated into environment_check.json and run_meta.json; the load-bearing one for scoring is that the published
"Overall Reproducibility" is the share of tasks scored 1, NOT the repository's own mean over {1, 0, -1} (41.42 for
the CoT row), and that ScoreParser's unparseable-similarity sentinel is also -1.
"""
import argparse, ast, functools, hashlib, io, json, os, posixpath, subprocess, sys, tempfile, time, types
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from battery import load_results, pricing_for, run_battery  # noqa: E402

CARD = "W4416034576"
HALF = HERE.parent.parent
REPO = HALF / "external" / "repos" / CARD / "Anonymous-2025-Repr__LLM-DS-Reproducibility"
DATA = HALF / "external" / "data" / CARD
RUNROOT = HALF / "runs" / CARD
BASE = RUNROOT / "baseline_alive"
ANA1, ANA2 = BASE / "analyst_r1", BASE / "analyst_r2"
INS = {k: BASE / f"inspector_{k}" for k in ("acc", "w2c", "concl", "sim")}
EXEC_LOG, CHECK_JSON = BASE / "executions.jsonl", RUNROOT / "environment_check.json"

MODEL = "o3-mini-2025-01-31"
PARAMS = {"reasoning_effort": "low", "max_completion_tokens": 4000}
INSPECTOR_ROLE = "developer"          # o3-mini takes developer, not system; the repo sent ("system", ...) to gpt-4o
METHODS = ("COT", "ROT")
SEEDS, BOOT, SEED0, WORKERS = 3, 2000, 20260907, 4
JUDGE_NOISE_N, JUDGE_NOISE_SEED = 100, 90      # inspector repeated on the seed-0 analyst outputs (card judgment.notes)
CAP, ANALYST_CAP, INSPECTOR_CAP = 80.0, 45.0, 35.0
EXEC_TIMEOUT_S, N_TASKS, LEVEL_TOL_PP, REPR_FLOOR = 180, 239, 10.0, 55.0
TABLE6 = {"COT": {"acc": 31.80, "repr": 55.23, "inexec": 13.81}, "ROT": {"acc": 33.05, "repr": 60.25, "inexec": 15.90}}
# token model for --dry-run: measured wherever the text is known offline, card budget assumptions elsewhere
EST = {"r1_out": 2800, "r2_in_add": 800, "r2_out": 1200, "pred_answer": 300, "acc_out": 400, "workflow": 200,
       "w2c_out": 1200, "code2": 700, "out2": 300, "concl_out": 500, "code1": 300, "out1": 250, "concl1": 300,
       "concl2": 200, "sim_out": 700}
FRICTIONS = [
    "results/ in the repository contains only __init__.py: no per-task analyst output and no judge verdict was released, so analyst drift cannot be separated from inspector drift by re-scoring archived outputs",
    "the published 'Overall Reproducibility' is the share of tasks scored 1, but eval/run_reproducibility.py reports mean over {1, 0, -1}; for the CoT row the two differ by 13.81 pp (55.23 vs 41.42)",
    "utils/output_parser.ScoreParser returns -1 when a similarity reply cannot be parsed, which collides with the -1 that eval/reproducibility.py uses for inexecutable analyst code; an unparseable accuracy reply silently scores 0",
    "utils/load_data.py derives metadata ids with file_path.split('/')[-1].split('_')[1], which silently mis-parses under Windows separators for the 7 DiscoveryBench subject directories containing '_'",
    "every repository open() call omits encoding=, so the DiscoveryBench metadata JSON fails to load under a non-UTF-8 locale (cp949 here)",
    "agents/prompt_template.py and utils/output_parser.py need langchain's pre-1.0 namespace (StringPromptTemplate, AgentOutputParser), served here from langchain_classic; the tool description that enters the prompt comes from langchain_experimental's PythonAstREPLTool, an unpinned dependency",
    "the repository's sandbox exec()s model-written code in-process with os.chdir, no timeout and no network isolation; this re-run substitutes a fresh isolated interpreter per snippet",
    "the original analyst ran at temperature 1 with no seed (a LangChain constraint), so run-to-run variance of the reasoning outputs is unquantified in the paper; three seeds are used here",
    "the o3-mini inspector's r = 0.98 agreement with gpt-4o (Section 5.6) was measured on QRData, not DiscoveryBench, and the paper reports 'only minor score increases' for it",
]
JUDGED_BY = ("automatic rule per ANALYSIS_PLAN section 1 as the card instantiates it, restricted to DiscoveryBench: "
             "survived = RoT - CoT positive with a task-level bootstrap 95% CI excluding 0 AND both reproducibility "
             "levels within 10 pp of Table 6; partial = positive but the CI includes 0 or a level moved; dead = RoT "
             "lowers reproducibility. The card's 'positive on at least 2 of 3 benchmarks' clause is NOT evaluable "
             "under the DiscoveryBench-only scope and is recorded as unmet-by-design; human double-coding pending")


def now():
    return datetime.now(timezone.utc).isoformat()


def _jd(o):
    for t, f in ((np.bool_, bool), (np.integer, int), (np.floating, float)):
        if isinstance(o, t):
            return f(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    raise TypeError(type(o))


def sha(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def tok(s):
    return len(s) / 4.0


def reply_of(rec):
    try:
        return rec["response"]["choices"][0]["message"]["content"] or ""
    except Exception:
        return ""


# ------------------------------------------------------------------ repository (read / imported, never copied)
U8OPEN = functools.partial(io.open, encoding="utf-8")       # the repo's open() calls otherwise inherit the locale codec


def shim_langchain():
    """agents/prompt_template.py and utils/output_parser.py import the pre-1.0 langchain namespace; langchain 1.x moved
    both symbols, and langchain_classic re-exports the originals, so the repo modules execute unmodified."""
    import langchain_classic.agents, langchain_classic.prompts
    assert hasattr(langchain_classic.prompts, "StringPromptTemplate") and hasattr(langchain_classic.agents, "AgentOutputParser")
    sys.modules["langchain.prompts"], sys.modules["langchain.agents"] = langchain_classic.prompts, langchain_classic.agents
    return {m: getattr(__import__(m), "__version__", "?")
            for m in ("langchain", "langchain_classic", "langchain_experimental")}


def repo_defs(rel, names, extra=None):
    """Execute named top-level defs/classes of a repo file verbatim (ast slice) without importing the module -
    experiments/get_agent.py would pull in langchain_ollama / langchain_aws for models we never call."""
    keep = [n for n in ast.parse((REPO / rel).read_text(encoding="utf-8")).body if getattr(n, "name", None) in names]
    if len(keep) != len(names):
        sys.exit(f"{rel}: expected {names}, found {[getattr(n, 'name', None) for n in keep]}")
    m = ast.Module(body=keep, type_ignores=[])
    ast.fix_missing_locations(m)
    ns = dict(extra or {})
    exec(compile(m, str(REPO / rel), "exec"), ns, ns)
    return ns


def load_tasks():
    """The DiscoveryBench block of utils/load_data.load_datasets(), executed verbatim as an ast slice so that QRData
    (CC BY-NC) and StatQA (GPL-3.0) need not be downloaded. Two shims, both recorded in environment_check.json:
    os.path.join -> posixpath.join (the block parses metadata ids with split('/') and split('_') and mis-parses under
    Windows separators) and open -> utf-8 (the block opens metadata JSON with the locale codec)."""
    import copy, pandas as pd
    from utils.data_class import DataSample, Dataset                                                       # noqa: F401
    src = (REPO / "utils" / "load_data.py").read_text(encoding="utf-8")
    fn = next(n for n in ast.parse(src).body if isinstance(n, ast.FunctionDef) and n.name == "load_datasets")
    names = [getattr(s.targets[0], "id", None) if isinstance(s, ast.Assign) else None for s in fn.body]
    m = ast.Module(body=fn.body[names.index("id_to_metadata"):names.index("DiscoveryBench_dataset") + 1], type_ignores=[])
    ast.fix_missing_locations(m)
    osx = types.SimpleNamespace(listdir=os.listdir, path=types.SimpleNamespace(join=posixpath.join))
    ns = {"os": osx, "open": U8OPEN, "json": json, "pd": pd, "copy": copy, "DataSample": DataSample,
          "Dataset": Dataset, "data_path": DATA.as_posix() + "/"}
    exec(compile(m, str(REPO / "utils" / "load_data.py"), "exec"), ns, ns)
    samples = ns["DiscoveryBench_dataset"].samples
    if len(samples) != N_TASKS:
        sys.exit(f"expected {N_TASKS} DiscoveryBench tasks, loaded {len(samples)} - run --fetch-data")
    return samples


def repo_inspector_spec():
    """The four inspector prompts taken out of eval/*.py with ast: the three module-level templates, the
    generate_conclusion f-string, each stage's ("system", ...) message and the DiscoveryBench accuracy rider."""
    tpl = {n.targets[0].id: n.value.value for n in ast.parse((REPO / "eval" / "eval_prompt.py").read_text(encoding="utf-8")).body
           if isinstance(n, ast.Assign) and isinstance(n.value, ast.Constant)}
    rsrc = ast.parse((REPO / "eval" / "reproducibility.py").read_text(encoding="utf-8"))
    cls = next(n for n in rsrc.body if isinstance(n, ast.ClassDef) and n.name == "Reproducibility")
    spec = {}
    for fn in [n for n in cls.body if isinstance(n, ast.FunctionDef)]:
        system, joined = None, []
        for n in ast.walk(fn):
            if (isinstance(n, ast.Tuple) and len(n.elts) == 2 and isinstance(n.elts[0], ast.Constant)
                    and n.elts[0].value == "system" and isinstance(n.elts[1], ast.Constant)):
                system = n.elts[1].value
            if isinstance(n, ast.JoinedStr):
                joined.append("".join(v.value if isinstance(v, ast.Constant) else "{%s}" % getattr(v.value, "id", "?")
                                      for v in n.values))
        spec[fn.name] = (system, joined[0] if joined else None)
    rider = None
    for n in ast.walk(ast.parse((REPO / "eval" / "run_reproducibility.py").read_text(encoding="utf-8"))):
        if (isinstance(n, ast.If) and isinstance(n.test, ast.Compare) and isinstance(n.test.comparators[0], ast.Constant)
                and n.test.comparators[0].value == "DiscoveryBench"):
            for st in n.body:
                if isinstance(st, ast.Assign) and getattr(st.targets[0], "id", "") == "dataset_specific_prompt":
                    rider = st.value.value
    out = {"accuracy": tpl["accuracy_prompt"], "w2c": tpl["workflow_to_code_prompt"],
           "sim": tpl["llm_reproducibility_prompt"], "concl": spec["generate_conclusion"][1], "rider": rider,
           "system": {k: spec[v][0] for k, v in (("acc", "accuracy"), ("w2c", "workflow_to_code"),
                                                 ("concl", "generate_conclusion"), ("sim", "llm_reproducibility"))}}
    for need, where in ((("{question}", "{predicted_answer}"), out["accuracy"]), (("{workflow}", "{datasets}"), out["w2c"]),
                        (("{code_1}", "{code_2}"), out["sim"]), (("{question}", "{code}", "{code_output}"), out["concl"] or "")):
        if any(k not in where for k in need):
            sys.exit(f"repository inspector prompts changed: missing {need}")
    if rider is None or "1%" not in rider:
        sys.exit("DiscoveryBench accuracy rider not found in eval/run_reproducibility.py")
    return out


class Renderer:
    """The repository's own prompt objects. Nothing here re-implements a template."""

    def __init__(self):
        from enum import Enum
        from agents.prompt_template import CoTPromptTemplate, cot_template
        from utils.code_execution import CustomPythonAstREPLTool
        from utils.output_parser import CoTOutputParser, ScoreParser, extract_python_code
        from utils.prepare_prompt import prepare_prompt
        g = repo_defs("experiments/get_agent.py", ["AgentType", "get_agent_instruction"], {"Enum": Enum})
        self.AgentType, self.instruction = g["AgentType"], g["get_agent_instruction"]
        self.tool, self.template_src, self.prepare = CustomPythonAstREPLTool(), cot_template, prepare_prompt
        self.tmpl = CoTPromptTemplate(template=cot_template, tools=[self.tool],
                                      input_variables=["file_paths", "descriptions", "question"])
        self.parser, self.scores, self.extract, self.ins = CoTOutputParser(), ScoreParser(), extract_python_code, repo_inspector_spec()

    def analyst(self, sample, method, conversation=()):
        kw = dict(self.prepare(sample))
        kw["agent_instruction"], kw["conversation"] = self.instruction(self.AgentType[method]), list(conversation)
        return self.tmpl.format(**kw).strip()


# ------------------------------------------------------------------------------------ isolated code execution
RUNNER = '''import socket, sys
repo, workdir, codefile, outfile = sys.argv[1:5]
sys.path.insert(0, repo)
from utils.code_execution import CustomPythonAstREPLTool   # the analysis stack first: it needs a live socket module
_MSG = "network disabled in the AIRepr sandbox"
class _Blocked(socket.socket):
    def connect(self, *a, **k): raise OSError(_MSG)
    def connect_ex(self, *a, **k): raise OSError(_MSG)
def _no(*a, **k): raise OSError(_MSG)
socket.socket, socket.create_connection = _Blocked, _no
out = CustomPythonAstREPLTool()._run(open(codefile, encoding="utf-8").read(), change_dir=workdir)
open(outfile, "w", encoding="utf-8").write(out)
'''


def run_code(code, workdir, timeout=EXEC_TIMEOUT_S):
    """One fresh isolated interpreter per snippet (python -I -X utf8, outbound sockets blocked, wall-clock timeout).
    The repository's CustomPythonAstREPLTool is imported inside the child, so the tool's own output shaping (captured
    stdout + 'Error [Type]: msg' + the max-runs notice) is unchanged."""
    t0 = time.time()
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        (td / "runner.py").write_text(RUNNER, encoding="utf-8")
        (td / "code.py").write_text(code, encoding="utf-8")
        args = [sys.executable, "-I", "-X", "utf8", str(td / "runner.py"), str(REPO), str(workdir),
                str(td / "code.py"), str(td / "out.txt")]
        try:
            p = subprocess.run(args, cwd=str(td), capture_output=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            return {"output": f"Error [Timeout]: no result within {timeout}s", "timeout": True, "returncode": None,
                    "elapsed_ms": int((time.time() - t0) * 1000)}
        out = (td / "out.txt").read_text(encoding="utf-8") if (td / "out.txt").exists() else ""
        if p.returncode != 0 and not out:
            out = "Error [SandboxFailure]: " + p.stderr.decode("utf-8", "replace")[-400:]
        return {"output": out, "timeout": False, "returncode": p.returncode, "elapsed_ms": int((time.time() - t0) * 1000)}


# --------------------------------------------------------------------------------------------- request builders
def body(messages):
    return {"model": MODEL, "messages": messages, **PARAMS}


def msgs(system, text):
    return ([] if not system else [{"role": INSPECTOR_ROLE, "content": system}]) + [{"role": "user", "content": text}]


def analyst_r1(tasks, r, seeds=SEEDS):
    return [{"id": f"{m}/{i:03d}/r1", "seed_idx": sd, "body": body(msgs(None, p)),
             "meta": {"method": m, "task": i, "stage": "r1", "subject": s.subject}}
            for m in METHODS for i, s in enumerate(tasks) for p in [r.analyst(s, m)] for sd in range(seeds)]


def analyst_r2(i, sample, m, r, action, action_input, workflow, observation, seed):
    conv = [(action, action_input, workflow, observation)]
    return {"id": f"{m}/{i:03d}/r2", "seed_idx": seed, "body": body(msgs(None, r.analyst(sample, m, conv))),
            "meta": {"method": m, "task": i, "stage": "r2"}}


def ins_request(stage, i, m, seed, r, s, **kw):
    t = r.ins
    if stage == "acc":
        txt = t["accuracy"].format(question=s.question, dataset_specific_prompt=t["rider"], true_answer=s.answer,
                                   predicted_answer=kw["predicted_answer"])
    elif stage == "w2c":
        txt = t["w2c"].format(question=s.question, workflow=kw["workflow"],
                              datasets=[os.path.basename(f) for f in s.file_paths])
    elif stage == "concl":
        txt = t["concl"].format(question=s.question, code=kw["code"], code_output=kw["code_output"])
    else:
        txt = t["sim"].format(question=s.question, **kw)
    return {"id": f"{m}/{i:03d}/{stage}", "seed_idx": seed, "body": body(msgs(t["system"][stage], txt)),
            "meta": {"method": m, "task": i, "stage": stage}}


# ------------------------------------------------------------------------------------------------------- check
SYNTH_REPLY = "Workflow: 1. Load the dataset with pandas. 2. Report its shape.\n\nAction: python_repl_ast\nAction Input: \n```python\nimport pandas as pd\ndf = pd.read_csv('{f}')\nprint('rows', len(df))\nprint('cols', len(df.columns))\n```\n"
SYNTH_BAD = "```python\nimport pandas as pd\ndf = pd.read_csv('no_such_file_xyz.csv')\nprint(df.shape)\n```"


def check(verbose=True, quick=False):
    versions = shim_langchain()
    sys.path.insert(0, str(REPO))
    tasks, r = load_tasks(), Renderer()
    s0, subj = tasks[0], {}
    for s in tasks:
        subj[s.subject] = subj.get(s.subject, 0) + 1
    prompts = {m: r.analyst(s0, m) for m in METHODS}
    delta = (prompts["ROT"].replace(r.instruction(r.AgentType.ROT), "")
             == prompts["COT"].replace(r.instruction(r.AgentType.COT), ""))
    lens = np.array([tok(r.analyst(s, "ROT")) for s in tasks])
    # scorer path: synthetic analyst reply -> repo parser -> isolated execution -> round-2 and inspector prompts
    wdir = os.path.dirname(s0.file_paths[0])
    parsed = r.parser.parse(SYNTH_REPLY.format(f=os.path.basename(s0.file_paths[0])))
    ex_ok = {"output": "(skipped)"} if quick else run_code(r.extract(parsed["action_input"]), wdir)
    ex_bad = {"output": "Error [FileNotFoundError]: (skipped)"} if quick else run_code(r.extract(SYNTH_BAD), wdir)
    obs = ex_ok["output"]
    r2p = r.analyst(s0, "ROT", [(parsed["action"], parsed["action_input"], parsed["workflow"], obs)])
    final = r.parser.parse("Final Answer: the dataset has 1 row per century.")["final_answer"]
    sim_text = ins_request("sim", 0, "ROT", 0, r, s0, code_1=parsed["action_input"], code_1_output=obs,
                           code_1_conclusion=final, code_2=parsed["action_input"], code_2_output=obs,
                           code_2_conclusion="same")["body"]["messages"][-1]["content"]
    sc = r.scores
    parsed_scores = {"accuracy_1": sc.extract_accuracy_score("Thoughts: yes.\n\nThe accuracy score is: 1"),
                     "accuracy_0": sc.extract_accuracy_score("Thoughts: no.\n\nThe accuracy score is: 0"),
                     "accuracy_unparseable": sc.extract_accuracy_score("no score here"),
                     "similarity_1": sc.extract_similarity_score_and_category("Thoughts: same.\n\nThe similarity score is: 1")[0],
                     "similarity_0": sc.extract_similarity_score_and_category("Thoughts: no.\n\nThe similarity score is: 0")[0],
                     "similarity_unparseable": sc.extract_similarity_score_and_category("nothing")[0]}
    man = json.loads((DATA / "discoverybench_manifest.json").read_text(encoding="utf-8")) if (DATA / "discoverybench_manifest.json").exists() else {}
    out = {
        "card_id": CARD, "checked_utc": now(), "offline": True, "api_calls": 0,
        "repo": {"path": str(REPO), "commit": "3b4a5a8f8b2fd9e78e8769036b84bd8d90da8b5e", "license": "MIT"},
        "environment": {
            "python": sys.version.split()[0], **versions,
            "packages": {m: getattr(__import__(m), "__version__", "?") for m in ("numpy", "pandas", "scipy", "statsmodels", "sklearn", "pingouin", "econml")},
            "shims": ["sys.modules['langchain.prompts'|'langchain.agents'] -> langchain_classic (langchain 1.x dropped StringPromptTemplate / AgentOutputParser from that namespace)",
                      "utils/load_data.py DiscoveryBench block executed with os.path.join -> posixpath.join: the block derives the metadata id from file_path.split('/')[-1].split('_')[1], which picks the wrong token under Windows separators for the 7 subject directories containing '_'",
                      "the same block executed with open -> utf-8: the repo opens metadata JSON with the locale codec (cp949 here) and dies on the UTF-8 punctuation in the dataset descriptions"],
            "code_execution": {"mode": "fresh isolated interpreter per snippet (subprocess.run python -I -X utf8, outbound sockets blocked)", "timeout_s": EXEC_TIMEOUT_S,
                               "repo_tool": "utils.code_execution.CustomPythonAstREPLTool, imported in the child; the repo itself exec()s in-process with os.chdir, no timeout and no isolation"}},
        "data": {"root": str(DATA), "license": "ODC-By (Open Data Commons Attribution), allenai/discoverybench LICENSE: attribution only, so prompt excerpts are archived in full",
                 "files": len(man), "bytes": sum(v["bytes"] for v in man.values()) if man else None,
                 "largest_file_mb": round(max(v["bytes"] for v in man.values()) / 1e6, 2) if man else None,
                 "answer_key_sha256": man.get("answer_key_real.csv", {}).get("sha256"),
                 "not_fetched": "QRData (CC BY-NC 4.0) and StatQA (GPL-3.0) - out of scope by decision"},
        "tasks": {"n": len(tasks), "expected": N_TASKS, "by_subject": subj,
                  "missing_files": [f for s in tasks for f in s.file_paths if not Path(f).exists()]},
        "prompts": {
            "template_sha256": sha(r.template_src), "tool_name": r.tool.name, "tool_description": r.tool.description,
            "agent_instruction": {m: r.instruction(r.AgentType[m]) for m in METHODS},
            "cot_and_rot_differ_only_by_the_instruction": bool(delta),
            "rot_extra_chars": len(r.instruction(r.AgentType.ROT)) - len(r.instruction(r.AgentType.COT)),
            "task0": {"subject": s0.subject, "question": s0.question, "files": [os.path.basename(f) for f in s0.file_paths]},
            "rendered": {m: {"chars": len(prompts[m]), "est_tokens": round(tok(prompts[m])), "sha256": sha(prompts[m]),
                             "text": prompts[m]} for m in METHODS},
            "round2_task0_ROT": {"chars": len(r2p), "sha256": sha(r2p), "conversation_add_tokens": round(tok(r2p) - tok(prompts["ROT"]))},
            "est_tokens_over_239_tasks_ROT": {"mean": round(lens.mean()), "median": round(float(np.median(lens))),
                                              "p90": round(float(np.percentile(lens, 90))), "min": int(lens.min()), "max": int(lens.max())},
            "inspector": {"sim_prompt_sha256": sha(sim_text), "sim_prompt_chars": len(sim_text), "sim_prompt_text": sim_text,
                          "template_sha256": {k: sha(r.ins[k]) for k in ("accuracy", "w2c", "sim", "concl")},
                          "dataset_specific_rider": r.ins["rider"], "system_messages": r.ins["system"], "system_role_sent": INSPECTOR_ROLE}},
        "scorer": {"parsed_action": parsed["action"], "parsed_workflow": parsed["workflow"], "parsed_final_answer": final,
                   "execution_ok": {"output": obs, "elapsed_ms": ex_ok.get("elapsed_ms"), "has_error": "Error [" in obs,
                                    "max_runs_notice": "You cannot generate code anymore." in obs},
                   "execution_failing": {"output": ex_bad["output"][:300],
                                         "maps_to_reproducibility_score": -1 if "Error [" in ex_bad["output"] else None},
                   "score_parser": parsed_scores,
                   "caveat": "ScoreParser's unparseable-similarity sentinel is also -1, the value eval/reproducibility.py uses for inexecutable analyst code; --analyze therefore takes inexecutability from the archived execution log, not from the score"},
        "metric_definition": {"published": "Overall Reproducibility (%) = share of tasks scored 1 (55.23% = 132/239 CoT, 60.25% = 144/239 RoT); Inexecutable Code (%) = share scored -1",
                              "repo_aggregate": "eval/run_reproducibility.py reports mean over {1, 0, -1}, which is NOT the published number (41.42 for the CoT row); --analyze computes both"},
        "original_values": TABLE6, "frictions": FRICTIONS,
    }
    if not quick:                              # --analyze calls check(quick=True) only for the environment block
        CHECK_JSON.parent.mkdir(parents=True, exist_ok=True)
        CHECK_JSON.write_text(json.dumps(out, indent=2, ensure_ascii=False, default=_jd), encoding="utf-8")
    if verbose:
        print(f"[{CARD} --check] tasks {len(tasks)}/{N_TASKS}, missing files {len(out['tasks']['missing_files'])}, "
              f"data {out['data']['files']} files, licence ODC-By")
        print(f"  prompts: CoT {len(prompts['COT'])} chars, RoT {len(prompts['ROT'])} chars, differ only by the RoT sentence: {delta}")
        print(f"  sandbox: {obs.splitlines()[0] if obs else '(empty)'} | failing snippet -> reproducibility {out['scorer']['execution_failing']['maps_to_reproducibility_score']}")
        print(f"  parser: action={parsed['action']!r} scores={parsed_scores}\n  -> {CHECK_JSON}")
    return out


# ----------------------------------------------------------------------------------------------------- dry-run
def dry_run(seeds=SEEDS):
    shim_langchain()
    sys.path.insert(0, str(REPO))
    tasks, r = load_tasks(), Renderer()
    reqs = analyst_r1(tasks, r, seeds)
    BASE.mkdir(parents=True, exist_ok=True)
    with open(BASE / "requests.jsonl", "w", encoding="utf-8") as f:
        for q in reqs:
            f.write(json.dumps(q, ensure_ascii=False) + "\n")
    price, E, t, per, stages = pricing_for(MODEL), EST, r.ins, {}, {}
    for m in METHODS:
        rate, n = 1.0 - TABLE6[m]["inexec"] / 100.0, len(tasks) * seeds
        r1 = sum(tok(r.analyst(s, m)) for s in tasks)
        acc = sum(tok(t["accuracy"].format(question=s.question, dataset_specific_prompt=t["rider"], predicted_answer="",
                                           true_answer=s.answer)) + tok(t["system"]["acc"]) + E["pred_answer"] for s in tasks)
        w2c = sum(tok(t["w2c"].format(question=s.question, workflow="", datasets=[os.path.basename(f) for f in s.file_paths]))
                  + tok(t["system"]["w2c"]) + E["workflow"] for s in tasks)
        cc = sum(tok(t["concl"].format(question=s.question, code="", code_output="")) + tok(t["system"]["concl"])
                 + E["code2"] + E["out2"] for s in tasks)
        sim = sum(tok(t["sim"].format(question=s.question, code_1="", code_1_output="", code_1_conclusion="", code_2="",
                                      code_2_output="", code_2_conclusion="")) + E["code1"] + E["out1"] + E["concl1"]
                  + E["code2"] + E["out2"] + E["concl2"] for s in tasks)
        ne = n * rate
        per[m] = [("analyst_r1", n, r1 * seeds, n * E["r1_out"]),
                  ("analyst_r2", n, (r1 + len(tasks) * E["r2_in_add"]) * seeds, n * E["r2_out"]),
                  ("inspector_acc", n, acc * seeds, n * E["acc_out"]),
                  ("inspector_w2c", ne, w2c * seeds * rate, ne * E["w2c_out"]),
                  ("inspector_concl", ne, cc * seeds * rate, ne * E["concl_out"]),
                  ("inspector_sim", ne, sim * seeds * rate, ne * E["sim_out"])]
        k = JUDGE_NOISE_N / len(tasks) / seeds                     # one extra inspector pass over the first N tasks, seed 0
        per[m] += [("judge_noise_" + s_, c * k, i_ * k, o_ * k) for s_, c, i_, o_ in per[m][2:]]
    for m in METHODS:
        for name, c, ti, to in per[m]:
            a = stages.setdefault(name, {"calls": 0.0, "tokens_in": 0.0, "tokens_out": 0.0, "usd": 0.0})
            a["calls"] += c
            a["tokens_in"] += ti
            a["tokens_out"] += to
            a["usd"] += ti / 1e6 * price["input"] + to / 1e6 * price["output"]
    tot = {k: round(float(sum(s[k] for s in stages.values())), 2) for k in ("calls", "tokens_in", "tokens_out", "usd")}
    ph = lambda n_: "<" + "x" * int(n_ * 4 - 2) + ">"                                                      # noqa: E731
    prov = []
    for m in METHODS:
        s = tasks[0]
        prov += [analyst_r2(0, s, m, r, "python_repl_ast", ph(E["code1"]), ph(E["workflow"]), ph(E["out1"]), 0),
                 ins_request("acc", 0, m, 0, r, s, predicted_answer=ph(E["pred_answer"])),
                 ins_request("w2c", 0, m, 0, r, s, workflow=ph(E["workflow"])),
                 ins_request("concl", 0, m, 0, r, s, code=ph(E["code2"]), code_output=ph(E["out2"])),
                 ins_request("sim", 0, m, 0, r, s, code_1=ph(E["code1"]), code_1_output=ph(E["out1"]),
                             code_1_conclusion=ph(E["concl1"]), code_2=ph(E["code2"]), code_2_output=ph(E["out2"]),
                             code_2_conclusion=ph(E["concl2"]))]
    for q in prov:
        q["meta"]["provisional"] = True
    with open(BASE / "requests_provisional.jsonl", "w", encoding="utf-8") as f:
        for q in prov:
            f.write(json.dumps(q, ensure_ascii=False) + "\n")
    out = {"card_id": CARD, "dry_run_utc": now(), "api_calls": 0, "model": MODEL, "params": PARAMS,
           "scope": f"DiscoveryBench only, {len(tasks)} tasks x 2 prompts (CoT, RoT) x {seeds} seeds",
           "pricing_usd_per_1m": price, "cap_usd": CAP, "within_cap": bool(tot["usd"] <= CAP),
           "stages": {k: {kk: round(vv, 2) for kk, vv in v.items()} for k, v in stages.items()}, "total": tot,
           "requests_written": {"analyst_round1": len(reqs), "path": str(BASE / "requests.jsonl"),
                                "provisional": len(prov), "provisional_path": str(BASE / "requests_provisional.jsonl"),
                                "note": "requests.jsonl holds the only fully determined stage (analyst round 1). Round 2 and the four inspector stages depend on replies that do not exist yet; requests_provisional.jsonl holds one exactly-shaped example of each with placeholder text of the assumed length."},
           "estimate_model": {"measured": "analyst round-1 prompts and every inspector prompt segment whose text is known offline (question, gold answer, dataset names, templates, system messages)",
                              "assumed_tokens": EST, "inexecutable_rates_used": {m: TABLE6[m]["inexec"] for m in METHODS},
                              "note": "the assumed segments come from the card's budget block and the paper's reasoning_effort=low / max_completion_tokens=4000 setting. battery.py's own generic --dry-run on requests.jsonl reports a higher figure (~$29 for round 1 alone) because it charges the full max_completion_tokens to every call."}}
    (RUNROOT / "dry_run.json").write_text(json.dumps(out, indent=2, ensure_ascii=False, default=_jd), encoding="utf-8")
    print(f"[{CARD} --dry-run] {seeds} seeds, {len(tasks)} tasks x {len(METHODS)} prompts")
    for k, v in stages.items():
        print(f"  {k:26s} {v['calls']:7.0f} calls {v['tokens_in']/1e6:6.2f}M in {v['tokens_out']/1e6:5.2f}M out ${v['usd']:7.2f}")
    print(f"  {'TOTAL':26s} {tot['calls']:7.0f} calls {tot['tokens_in']/1e6:6.2f}M in {tot['tokens_out']/1e6:5.2f}M out ${tot['usd']:7.2f}  (cap ${CAP})")
    print(f"  -> {BASE / 'requests.jsonl'} ({len(reqs)} analyst round-1 requests), {RUNROOT / 'dry_run.json'}")
    return out


# --------------------------------------------------------------------------------------------------------- run
def _exec_cached(key, code, wdir):
    cache = {}
    if EXEC_LOG.exists():
        for line in open(EXEC_LOG, encoding="utf-8"):
            if line.strip():
                rec = json.loads(line)
                cache[rec["key"]] = rec
    if key in cache:
        return cache[key]
    rec = {"key": key, "sha_code": sha(code), "ts": now(), **run_code(code, wdir)}
    EXEC_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(EXEC_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return rec


def run(seeds=SEEDS):
    """Analyst round 1 -> isolated code execution -> analyst round 2 -> inspector (accuracy, workflow-to-code, a second
    code execution, conclusion, similarity). Resumable: every stage skips (id, seed_idx) pairs already archived by
    battery, and every code execution is cached in executions.jsonl."""
    shim_langchain()
    sys.path.insert(0, str(REPO))
    tasks, r = load_tasks(), Renderer()
    run_battery(analyst_r1(tasks, r, seeds), ANA1, ANALYST_CAP * 0.6, WORKERS, label="analyst-r1")
    reqs2, step1 = [], {}
    for (rid, sd), rec in load_results(ANA1).items():
        m, i = rec["meta"]["method"], rec["meta"]["task"]
        p = r.parser.parse(reply_of(rec))
        code = r.extract(p["action_input"]) or p["action_input"]
        wdir = os.path.dirname(tasks[i].file_paths[0])
        obs = _exec_cached(f"{m}/{i:03d}/{sd}/code1", code, wdir)["output"] if code else "Error [NoCode]: empty action input"
        step1[(m, i, sd)] = {"parsed": p, "code": code, "obs": obs}
        if code:
            reqs2.append(analyst_r2(i, tasks[i], m, r, p["action"], p["action_input"], p["workflow"], obs, sd))
    run_battery(reqs2, ANA2, ANALYST_CAP * 0.4, WORKERS, label="analyst-r2")
    final = {(v["meta"]["method"], v["meta"]["task"], k[1]): r.parser.parse(reply_of(v))["final_answer"] or ""
             for k, v in load_results(ANA2).items()}
    extra = lambda i, sd: [JUDGE_NOISE_SEED + sd] if (sd == 0 and i < JUDGE_NOISE_N) else []                # noqa: E731
    run_battery([ins_request("acc", i, m, s2, r, tasks[i], predicted_answer=final.get((m, i, sd), ""))
                 for (m, i, sd) in step1 for s2 in [sd] + extra(i, sd)], INS["acc"], INSPECTOR_CAP * 0.15, WORKERS,
                label="inspector-acc")
    live = {k: v for k, v in step1.items() if "Error [" not in v["obs"]}    # score -1 = inexecutable, no inspector calls
    run_battery([ins_request("w2c", i, m, s2, r, tasks[i], workflow=step1[(m, i, sd)]["parsed"]["workflow"])
                 for (m, i, sd) in live for s2 in [sd] + extra(i, sd)], INS["w2c"], INSPECTOR_CAP * 0.3, WORKERS,
                label="inspector-w2c")
    code2 = {}
    for (rid, sd), rec in load_results(INS["w2c"]).items():
        m, i = rec["meta"]["method"], rec["meta"]["task"]
        c2 = r.extract(reply_of(rec)) or reply_of(rec)
        code2[(m, i, sd)] = (c2, _exec_cached(f"{m}/{i:03d}/{sd}/code2", c2, os.path.dirname(tasks[i].file_paths[0]))["output"])
    run_battery([ins_request("concl", i, m, sd, r, tasks[i], code=c2, code_output=o2)
                 for (m, i, sd), (c2, o2) in code2.items()], INS["concl"], INSPECTOR_CAP * 0.2, WORKERS, label="inspector-concl")
    concl = {(v["meta"]["method"], v["meta"]["task"], k[1]): reply_of(v) for k, v in load_results(INS["concl"]).items()}
    sim = []
    for (m, i, sd), (c2, o2) in code2.items():
        bsd = 0 if sd >= JUDGE_NOISE_SEED else sd                          # judge-noise repeats reuse the seed-0 analyst
        base = step1.get((m, i, bsd))
        if base is not None:
            sim.append(ins_request("sim", i, m, sd, r, tasks[i], code_1=base["code"], code_1_output=base["obs"],
                                   code_1_conclusion=final.get((m, i, bsd), ""), code_2=c2, code_2_output=o2,
                                   code_2_conclusion=concl.get((m, i, sd), "")))
    run_battery(sim, INS["sim"], INSPECTOR_CAP * 0.35, WORKERS, label="inspector-sim")
    print(f"[{CARD} --run] complete; now: python adapters/airepr_W4416034576.py --analyze")


# ----------------------------------------------------------------------------------------------------- analyze
def boot_ci(fn, arrays, rng, n=BOOT):
    k = len(arrays[0])
    vals = [fn(*[a[idx] for a in arrays]) for idx in (rng.integers(0, k, k) for _ in range(n))]
    return [round(float(np.percentile(vals, 2.5)), 4), round(float(np.percentile(vals, 97.5)), 4)]


def analyze(seeds=SEEDS):
    shim_langchain()
    sys.path.insert(0, str(REPO))
    tasks, sims, accs, execd = load_tasks(), load_results(INS["sim"]), load_results(INS["acc"]), {}
    if not sims:
        print(f"no archived inspector calls in {INS['sim']}; run --run first")
        return None
    from utils.output_parser import ScoreParser
    sp = ScoreParser()
    if EXEC_LOG.exists():
        for line in open(EXEC_LOG, encoding="utf-8"):
            if line.strip():
                rec = json.loads(line)
                m, i, sd, which = rec["key"].split("/")
                if which == "code1":
                    execd[(m, int(i), int(sd))] = "Error [" not in rec["output"]
    repr_ = {(rec["meta"]["method"], rec["meta"]["task"], sd): sp.extract_similarity_score_and_category(reply_of(rec))[0]
             for (rid, sd), rec in sims.items()}
    acc_ = {(rec["meta"]["method"], rec["meta"]["task"], sd): sp.extract_accuracy_score(reply_of(rec))
            for (rid, sd), rec in accs.items()}
    rng, rows, per_task = np.random.default_rng(SEED0), {}, {}
    med = lambda M: np.array([np.nan if all(np.isnan(v)) else float(np.nanmedian(v)) for v in M])           # noqa: E731
    for m in METHODS:
        mr, ma, mx = [], [], []
        for i in range(len(tasks)):
            ok = [execd.get((m, i, sd)) for sd in range(seeds)]
            mr.append([np.nan if o is None else (1.0 if (o and repr_.get((m, i, sd)) == 1) else 0.0) for sd, o in enumerate(ok)])
            mx.append([np.nan if o is None else (0.0 if o else 1.0) for o in ok])
            ma.append([acc_.get((m, i, sd), np.nan) for sd in range(seeds)])
        per_task[m] = {"repr": med(mr), "acc": med(ma), "inexec": med(mx),
                       "per_seed_repr": [float(np.nanmean([mr[i][s] for i in range(len(tasks))])) for s in range(seeds)]}
        v, a, x = (per_task[m][k][~np.isnan(per_task[m][k])] for k in ("repr", "acc", "inexec"))
        rows[m] = {"n_tasks_scored": int(len(v)), "repr_pct": round(100 * float(v.mean()), 2) if len(v) else None,
                   "repr_ci95": [round(100 * c, 2) for c in boot_ci(lambda z: z.mean(), [v], rng)] if len(v) else None,
                   "acc_pct": round(100 * float(a.mean()), 2) if len(a) else None,
                   "inexec_pct": round(100 * float(x.mean()), 2) if len(x) else None,
                   "per_seed_repr_pct": [round(100 * s_, 2) for s_ in per_task[m]["per_seed_repr"]],
                   "repo_mean_over_1_0_minus1": round(float(np.nanmean([1.0 if r_ == 1 else (-1.0 if x_ == 1 else 0.0)
                                                                        for r_, x_ in zip(per_task[m]["repr"], per_task[m]["inexec"])
                                                                        if not np.isnan(r_)])), 4) if len(v) else None,
                   "original": TABLE6[m],
                   "level_within_10pp": bool(abs(100 * float(v.mean()) - TABLE6[m]["repr"]) <= LEVEL_TOL_PP) if len(v) else None}
    ok = ~(np.isnan(per_task["COT"]["repr"]) | np.isnan(per_task["ROT"]["repr"]))
    c, t_ = per_task["COT"]["repr"][ok], per_task["ROT"]["repr"][ok]
    diff = {"point_pp": round(100 * float((t_ - c).mean()), 2), "n_paired_tasks": int(ok.sum()),
            "ci95_pp": [round(100 * z, 2) for z in boot_ci(lambda p, q: (q - p).mean(), [c, t_], rng)],
            "original_pp": round(TABLE6["ROT"]["repr"] - TABLE6["COT"]["repr"], 2)}
    lvl = all(rows[m]["level_within_10pp"] for m in METHODS)
    d, lo, hi = diff["point_pp"], diff["ci95_pp"][0], diff["ci95_pp"][1]
    if d < 0:
        verdict, why = "사망 (dead)", f"RoT lowers reproducibility ({d:+.2f} pp, bootstrap CI [{lo}, {hi}])"
    elif d > 0 and lo > 0 and lvl:
        verdict, why = "생존 (survived)", f"RoT - CoT = {d:+.2f} pp, bootstrap CI [{lo}, {hi}] excludes 0; both levels within {LEVEL_TOL_PP:.0f} pp of Table 6"
    else:
        verdict = "부분 생존 (partial)"
        why = (f"RoT - CoT = {d:+.2f} pp, CI [{lo}, {hi}]" + ("" if lo > 0 else " includes 0")
               + ("" if lvl else f"; a reproducibility level moved more than {LEVEL_TOL_PP:.0f} pp from Table 6"))
    noise = {}
    for m in METHODS:
        pairs = [(repr_.get((m, i, 0)), repr_.get((m, i, JUDGE_NOISE_SEED))) for i in range(min(JUDGE_NOISE_N, len(tasks)))]
        pairs = [p for p in pairs if None not in p]
        noise[m] = {"n": len(pairs), "agreement": round(float(np.mean([a_ == b_ for a_, b_ in pairs])), 4) if pairs else None}
    budget = {d_.name: (json.loads((d_ / "budget.json").read_text(encoding="utf-8")) if (d_ / "budget.json").exists() else {})
              for d_ in [ANA1, ANA2] + list(INS.values())}
    env = check(verbose=False, quick=True)
    meta = {
        "card_id": CARD, "run_date_utc": datetime.now(timezone.utc).date().isoformat(),
        "target_paper": {"title": "AIRepr: An Analyst-Inspector Framework for Evaluating Reproducibility of LLMs in Data Science",
                         "doi": "10.18653/v1/2025.findings-emnlp.539", "repo": "https://github.com/Anonymous-2025-Repr/LLM-DS-Reproducibility",
                         "repo_commit": "3b4a5a8f8b2fd9e78e8769036b84bd8d90da8b5e", "repo_license": "MIT", "original_values": TABLE6,
                         "original_source": "Table 6, DiscoveryBench rows for the o3-mini analyst (239 tasks)"},
        "generation": {"model_requested": MODEL,
                       "model_served": sorted({rec.get("model_served") for rec in list(sims.values()) + list(accs.values())} - {None}),
                       "endpoint": "POST https://api.openai.com/v1/chat/completions (harness/openai_client.py); the original used the Azure deployment o3-mini-2025-01-31, api-version 2024-12-01-preview, via LangChain AzureChatOpenAI",
                       "parameters": f"{PARAMS}; no temperature (the original's temperature=1 was a LangChain requirement and is o3-mini's only legal value); no API seed - seed_idx is a repeat index",
                       "inspector": f"{MODEL} itself instead of gpt-4o-2024-11-20 (paper Section 5.6 / Figure 7, r = 0.98 on QRData); the repo's ('system', ...) message is sent as role '{INSPECTOR_ROLE}'",
                       "battery": f"analyst 2 calls per task-seed; inspector up to 4 (accuracy always, workflow-to-code / conclusion / similarity only when the analyst code executes); {len(tasks)} tasks x {len(METHODS)} prompts x {seeds} seeds",
                       "code_execution": env["environment"]["code_execution"]},
        "results": {"rows": rows, "within_model_difference_RoT_minus_CoT": diff,
                    "judge_noise_probe": {"design": f"inspector repeated on the seed-0 analyst outputs of the first {JUDGE_NOISE_N} tasks (seed_idx {JUDGE_NOISE_SEED})",
                                          "per_method": noise},
                    "secondary_check_repr_ge_55pct": {m: bool((rows[m]["repr_pct"] or 0) >= REPR_FLOOR) for m in METHODS},
                    "cost_usd": round(sum(b.get("cost_usd", 0) for b in budget.values()), 3),
                    "calls": sum(b.get("calls", 0) for b in budget.values()),
                    "errors": sum(b.get("errors", 0) for b in budget.values()),
                    "judgment": verdict, "judged_by": JUDGED_BY, "note": why},
        "reproducibility_frictions_observed": FRICTIONS,
    }
    (RUNROOT / "run_meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False, default=_jd), encoding="utf-8")
    print(f"[{CARD} --analyze] {len(sims)} similarity calls, ${meta['results']['cost_usd']}")
    for m in METHODS:
        q = rows[m]
        print(f"  {m}: repr {q['repr_pct']}% CI {q['repr_ci95']} (paper {TABLE6[m]['repr']}), acc {q['acc_pct']}% "
              f"(paper {TABLE6[m]['acc']}), inexec {q['inexec_pct']}% (paper {TABLE6[m]['inexec']}), n={q['n_tasks_scored']}")
    print(f"  RoT - CoT = {diff['point_pp']:+.2f} pp CI {diff['ci95_pp']} (paper {diff['original_pp']:+.2f})")
    print(f"  judgment: {verdict}\n  -> {RUNROOT / 'run_meta.json'}")
    return meta


# -------------------------------------------------------------------------------------------------- fetch data
def fetch_data():
    """Download the DiscoveryBench files the repository's own download_data.sh lists (parsed from it, not re-typed).
    No LLM API call; files over 50 MB are skipped. QRData and StatQA are deliberately not fetched."""
    import re, urllib.parse, urllib.request
    sec = (REPO / "download_data.sh").read_text(encoding="utf-8")
    sec = sec[sec.index("Download DiscoveryBench data"):]
    plan = [(None, m.group(1)) for m in re.finditer(r"wget -nc (https://\S+)", sec) if "${file}" not in m.group(1)]
    for sub, lst, base in re.findall(r"cd (\S+)\nfiles=\((.*?)\)\nfor file in \"\$\{files\[@\]\}\"; do wget -nc (\S+)\$\{file\}; done", sec, re.S):
        plan += [(sub, base + n) for n in re.findall(r'"([^"]+)"', lst)]
    root = DATA / "DiscoveryBench"
    root.mkdir(parents=True, exist_ok=True)
    man = {}
    for sub, url in plan:
        dst = root / (sub or "") / urllib.parse.unquote(url.rsplit("/", 1)[1])
        dst.parent.mkdir(parents=True, exist_ok=True)
        if not dst.exists():
            data = urllib.request.urlopen(url, timeout=90).read()
            if len(data) > 50 * 1024 * 1024:
                print(f"  skipped (>50 MB): {dst.name}")
                continue
            dst.write_bytes(data)
        b = dst.read_bytes()
        man[str(dst.relative_to(root)).replace("\\", "/")] = {"url": url, "bytes": len(b), "sha256": hashlib.sha256(b).hexdigest()}
    (DATA / "discoverybench_manifest.json").write_text(json.dumps(man, indent=1), encoding="utf-8")
    print(f"[{CARD} --fetch-data] {len(man)} files, {sum(v['bytes'] for v in man.values())/1e6:.2f} MB -> {root}")


def main():
    ap = argparse.ArgumentParser(description=f"AIRepr re-execution adapter (card {CARD})")
    for f in ("fetch-data", "check", "dry-run", "run", "analyze"):
        ap.add_argument("--" + f, action="store_true")
    ap.add_argument("--seeds", type=int, default=SEEDS)
    a = ap.parse_args()
    if not REPO.exists():
        sys.exit(f"repository not found at {REPO}")
    if a.fetch_data:
        fetch_data()
    if a.check:
        check()
    if a.dry_run:
        dry_run(a.seeds)
    if a.run:
        run(a.seeds)
    if a.analyze:
        analyze(a.seeds)
    if not any((a.fetch_data, a.check, a.dry_run, a.run, a.analyze)):
        ap.print_help()


if __name__ == "__main__":
    main()
