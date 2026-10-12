r"""Hook for W4403882451 (PlanBench Blocksworld zero-shot, GPT-4 Turbo; also the W4403758464 cell).

load_items: the paper's own zero-shot query files llm_planning_analysis/results/{blocksworld,blocksworld_3}/
            gpt-4-turbo_chat/task_1_plan_generation_zero_shot.json (500 four/five-block + 100 three-block instances
            = the paper's 600; the queries ARE the zero-shot prompts, identical to the printed Appendix H.1
            template). gold = {"init": {...}, "goal": [...]} parsed from the NL statement.
render:     [user: query] verbatim.
parse:      repository rule-based text_to_plan_blocksworld replica -> list of PDDL actions (used when no judge stage).
score:      Blocksworld simulator (= VAL on the 4-op domain): every action applicable and the goal reached.
judge_requests / score_with_judge: the paper's evaluation path - gpt-4o translation of the raw reply into a PDDL
            plan with the repository's TRANSLATION_PROMPT (side file W4403882451_translation_prompt.txt), then
            the same validation. Validated on the released files: 600/600 llm_correct flags reproduced.
"""
import json, re, urllib.request
from pathlib import Path

BASE = "https://raw.githubusercontent.com/karthikv792/LLMs-Planning/main/llm_planning_analysis/results/"
URLS = [("", BASE + "blocksworld/gpt-4-turbo_chat/task_1_plan_generation_zero_shot.json"),          # 500 x 4-5 blocks
        ("bw3_", BASE + "blocksworld_3/gpt-4-turbo_chat/task_1_plan_generation_zero_shot.json")]   # 100 x 3 blocks
UA = {"User-Agent": "Mozilla/5.0 (compatible; halflife-tierb/0.1; academic research)"}
COLORS = {"a": "red", "b": "blue", "c": "orange", "d": "yellow", "e": "white", "f": "magenta", "g": "black", "h": "cyan",
          "i": "green", "j": "violet", "k": "silver", "l": "gold"}
LETTER = {v: k for k, v in COLORS.items()}
JUDGE_MODEL = "gpt-4o-2024-08-06"      # repository default translator_engine='gpt-4o' (alias at the time of the paper)
ACTIONS = ("pick-up", "put-down", "stack", "unstack")
N_ARGS = {"pick-up": 1, "put-down": 1, "stack": 2, "unstack": 2}


def parse_statement(text):
    """'As initial conditions I have that, ... My goal is to have that ...' -> (init, goal)."""
    st = text[text.rfind("[STATEMENT]"):] if "[STATEMENT]" in text else text
    m = re.search(r"As initial conditions I have that,?\s*(.*?)\.\s*My goal is to have that\s*(.*?)\.", st, re.S)
    if not m:
        raise ValueError("statement not found")
    def facts(s):
        out = {"clear": set(), "ontable": set(), "on": set(), "handempty": False, "holding": None}
        for part in re.split(r",|\band\b", s.replace("\n", " ")):
            part = part.strip()
            mm = re.match(r"the (\w+) block is on top of the (\w+) block", part)
            if mm: out["on"].add((mm.group(1), mm.group(2))); continue
            mm = re.match(r"the (\w+) block is on the table", part)
            if mm: out["ontable"].add(mm.group(1)); continue
            mm = re.match(r"the (\w+) block is clear", part)
            if mm: out["clear"].add(mm.group(1)); continue
            if "hand is empty" in part: out["handempty"] = True; continue
            mm = re.match(r"the hand is currently holding (\w+)", part)
            if mm: out["holding"] = mm.group(1)
        return out
    init, goal = facts(m.group(1)), facts(m.group(2))
    return init, goal


def valid_plan(actions, init, goal):
    clear, ontable, on = set(init["clear"]), set(init["ontable"]), dict((x, y) for x, y in init["on"])
    hand = init.get("holding")
    for a in actions:
        p = a.split()
        name, args = p[0], p[1:]
        if name not in N_ARGS or len(args) != N_ARGS[name]:
            return False
        if name == "pick-up":
            x = args[0]
            if not (x in clear and x in ontable and hand is None): return False
            hand = x; clear.discard(x); ontable.discard(x)
        elif name == "put-down":
            x = args[0]
            if hand != x: return False
            hand = None; clear.add(x); ontable.add(x)
        elif name == "stack":
            x, y = args
            if not (hand == x and y in clear and x != y): return False
            hand = None; clear.add(x); clear.discard(y); on[x] = y
        else:
            x, y = args
            if not (on.get(x) == y and x in clear and hand is None): return False
            hand = x; clear.discard(x); clear.add(y); del on[x]
    if goal.get("handempty") and hand is not None: return False
    return all(on.get(x) == y for x, y in goal["on"]) and goal["ontable"] <= ontable and goal["clear"] <= clear


def load_items(cfg):
    rows = []
    for prefix, url in URLS:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as r:
            data = json.loads(r.read().decode("utf-8"))
        for inst in data["instances"]:
            init, goal = parse_statement(inst["query"])
            rows.append({"id": f"{prefix}{inst['instance_id']}", "query": inst["query"], "ground_truth_plan": inst["ground_truth_plan"],
                         "gold": {"init": {k: (sorted(v) if isinstance(v, set) else v) for k, v in init.items()},
                                  "goal": {k: (sorted(v) if isinstance(v, set) else v) for k, v in goal.items()}}})
    if len(rows) != 600:
        raise RuntimeError(f"expected 600 instances (500 + 100), got {len(rows)}")
    return rows


def render(cfg, row):
    return [{"role": "user", "content": row["query"]}]


def parse(text, cfg, strip_star=True):
    """Replica of utils/text_to_pddl.text_to_plan_blocksworld (rule-based extraction) -> ['unstack blue orange', ...].
    strip_star=True mirrors the current repository (line.replace('*','')); strip_star=False is the pre-fix version that
    produced the paper's 241/600 (markdown-bold action lines are then silently dropped)."""
    if not text:
        return []
    t = text.lower().strip()
    if "### plan:" in t: t = t.split("### plan:")[1]
    if "[plan]" in t:
        t = t.split("[plan]")[1]
        if "[plan end]" in t: t = t.split("[plan end]")[0]
    t = t.replace("pick up", "pick-up").replace("put down", "put-down")
    names = [f"{c} block" for c in COLORS.values()]
    plan = []
    for line in ((l.strip().replace("*", "") if strip_star else l.strip()) for l in t.split("\n")):
        if "[COST]" in line: break
        hits = [a for a in ACTIONS if a in line.split()]
        if not hits: continue
        act = hits[0]
        objs = sorted((line.index(n), n) for n in names if n in line)
        if len(objs) != N_ARGS[act]: continue
        plan.append(act + " " + " ".join(n.replace(" block", "") for _, n in objs))
    return plan


def _goldsets(g):
    return ({**g["init"], "clear": set(g["init"]["clear"]), "ontable": set(g["init"]["ontable"]), "on": {tuple(x) for x in g["init"]["on"]}},
            {**g["goal"], "clear": set(g["goal"]["clear"]), "ontable": set(g["goal"]["ontable"]), "on": {tuple(x) for x in g["goal"]["on"]}})


def score(preds, golds, cfg):
    per = [1.0 if p and valid_plan(p, *_goldsets(g)) else 0.0 for p, g in zip(preds, golds)]
    return (sum(per) / len(per) if per else float("nan")), per


def judge_requests(cfg, items, responses):
    prompt = (Path(__file__).with_name("W4403882451_translation_prompt.txt")).read_text(encoding="utf-8")
    reqs = []
    for (iid, s), rec in sorted(responses.items()):
        text = rec["response"]["choices"][0]["message"].get("content") or ""
        reqs.append({"id": iid, "seed_idx": s, "meta": {"stage": "translation"},
                     "body": {"model": JUDGE_MODEL, "messages": [{"role": "user", "content": f"{prompt}\n\n[RAW TEXT]\n{text}\n\n[PDDL PLAN]"}]}})
    return reqs


def translated_plan(text):
    """Repository post-processing of the gpt-4o translation -> ['unstack blue orange', ...] (colors)."""
    plan = (text.split("[PDDL PLAN]")[1] if "[PDDL PLAN]" in text else text).split("[PDDL PLAN END]")[0].strip().lower()
    out = []
    for line in plan.split("\n"):
        a = "".join(ch for ch in line.replace("(", "").replace(")", "").replace(".", "") if not ch.isdigit()).split()
        if not a or a[0] == "no": continue
        name = next((n for n in ("unstack", "stack", "pick-up", "put-down", "pickup", "putdown", "put_down", "pick_up") if n in a[0]), None)
        if name is None: continue
        name = {"pickup": "pick-up", "pick_up": "pick-up", "putdown": "put-down", "put_down": "put-down"}.get(name, name)
        objs = [next((c for c in COLORS.values() if c in o), None) for o in a[1:]]
        out.append(name + "".join(" " + o for o in objs if o))
    return out


def score_with_judge(cfg, items, responses, judge_responses):
    """Primary number = the paper's scoring path (rule-based text_to_plan extraction + validation), identical to
    score(); the gpt-4o translation is kept only as a secondary diagnostic of true plan validity.
    Triage 2026-09-09: the GPT-4 Turbo cell of Table 1 was NOT produced by the LLM translator - the released
    extracted_llm_plan fields of all 600 instances are reproduced exactly by the pre-fix rule-based extractor
    (no '*' stripping: 241/600), the current repository extractor gives 254/600 on the same replies, and the
    o1-paper footnote reserves the GPT-4o-mini translation for o1. The translator measures a different quantity
    (parenthetical-tolerant validity, 55% on the released replies too) and must not be compared with 40.1.
    Writes runs/tierb/W4403882451/judge_summary.json with all three numbers per seed."""
    per_rule, per_old, per_judge = [], [], []
    seed = None
    for it, rec in zip(items, responses):
        gs = _goldsets(it["gold"])
        seed = rec.get("seed_idx", 0)
        text = rec["response"]["choices"][0]["message"].get("content") or ""
        p = parse(text, cfg)
        per_rule.append(1.0 if p and valid_plan(p, *gs) else 0.0)
        p_old = parse(text, cfg, strip_star=False)
        per_old.append(1.0 if p_old and valid_plan(p_old, *gs) else 0.0)
        j = judge_responses.get((it["id"], seed))
        if j:
            plan = translated_plan(j["response"]["choices"][0]["message"].get("content") or "")
            per_judge.append(1.0 if plan and valid_plan(plan, *gs) else 0.0)
    mean = lambda xs: (sum(xs) / len(xs)) if xs else float("nan")
    summary = {"rule_current_repo": mean(per_rule), "rule_prefix_paper_version": mean(per_old),
               "judge_gpt4o_translation": mean(per_judge), "n": len(per_rule), "n_judge": len(per_judge)}
    print(f"[W4403882451] seed {seed}: rule (primary, current repo extractor) {summary['rule_current_repo']:.4f} | "
          f"pre-fix extractor (paper's 241/600 path) {summary['rule_prefix_paper_version']:.4f} | "
          f"judge translation {summary['judge_gpt4o_translation']:.4f}")
    side = (RUN_DIR if "RUN_DIR" in globals() else Path(__file__).resolve().parents[3] / "runs" / "tierb" / "W4403882451") / "judge_summary.json"
    try:
        allseeds = json.loads(side.read_text(encoding="utf-8")) if side.exists() else {}
        allseeds[str(seed)] = summary
        side.write_text(json.dumps(allseeds, indent=2), encoding="utf-8")
    except OSError:
        pass
    return mean(per_rule), per_rule
