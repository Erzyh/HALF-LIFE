"""Hook for W4403758464 (LLMs Still Can't Plan; Can LRMs?, Table 1 Blocksworld zero-shot, GPT-4 Turbo 241/600).

load_items() reads the two PlanBench plan-generation files (blocksworld: 500 four/five-block instances,
blocksworld_3: 100 three-block instances = the paper's static test set of 600 three-to-five-block
problems) and cuts the target [STATEMENT] (initial conditions + goal) out of the one-shot query, so the
runner renders the Appendix D.1 zero-shot prompt. parse() mirrors the repository's rule-based
text_to_plan_blocksworld (action word + ordered '<colour> block' mentions per line, lines with the wrong
object count skipped) after stripping markdown emphasis. score() replaces VAL with an exact simulation of
the four-operator Blocksworld domain from the natural-language initial state: a plan is correct when every
action is applicable in turn and the goal holds afterwards.
"""
import json, re, urllib.request
from pathlib import Path

WID = "W4403758464"
CACHE = Path(__file__).resolve().parents[3] / "external" / "data" / "tierb_items" / WID
BASE = "https://raw.githubusercontent.com/karthikv792/LLMs-Planning/main/plan-bench/prompts/"
FILES = [("bw", "blocksworld/task_1_plan_generation.json"), ("bw3", "blocksworld_3/task_1_plan_generation.json")]
UA = {"User-Agent": "Mozilla/5.0 (compatible; halflife-tierb/0.1; academic research)"}
COLOURS = ["red", "blue", "orange", "yellow", "white", "magenta", "black", "cyan", "green", "violet", "silver", "gold"]
ACTIONS = {"pick-up": 1, "put-down": 1, "stack": 2, "unstack": 2}          # domain-file order, arity


def load_items(cfg):
    CACHE.mkdir(parents=True, exist_ok=True)
    rows = []
    for tag, rel in FILES:
        p = CACHE / rel.replace("/", "_")
        if not p.exists():
            p.write_bytes(urllib.request.urlopen(urllib.request.Request(BASE + rel, headers=UA), timeout=300).read())
        for inst in json.loads(p.read_text(encoding="utf-8"))["instances"]:
            stmt = inst["query"][inst["query"].rfind("[STATEMENT]"):]
            init = re.search(r"(As initial conditions I have that,.*?\.)\s*\n", stmt, re.S)
            goal = re.search(r"(My goal is to have that.*?\.)\s*\n", stmt, re.S)
            if not init or not goal:
                raise RuntimeError(f"{tag}-{inst['instance_id']}: statement not found")
            rows.append({"id": f"{tag}-{inst['instance_id']}", "initial_conditions": init.group(1), "goal": goal.group(1),
                         "gold": {"init": init.group(1), "goal": goal.group(1), "gt_plan": inst["ground_truth_plan"]}})
    return rows


def parse(text, cfg):
    if text is None:
        return None
    t = re.sub(r"[*_`]+", "", text.lower()).replace("pick up", "pick-up").replace("put down", "put-down")
    plan = []
    for line in t.splitlines():
        if "[cost]" in line:
            break
        toks = line.strip().split()
        act = next((a for a in ACTIONS if a in toks), None)
        if act is None:
            continue
        objs = sorted(((line.find(f"{c} block"), c) for c in COLOURS if f"{c} block" in line))
        if len(objs) != ACTIONS[act]:
            continue
        plan.append((act, [c for _, c in objs]))
    return plan


def _state(init):
    s = {"on": {}, "table": set(), "clear": set(), "holding": None}
    for a, b in re.findall(r"the (\w+) block is on top of the (\w+) block", init):
        s["on"][a] = b
    s["table"] = set(re.findall(r"the (\w+) block is on the table", init))
    s["clear"] = set(re.findall(r"the (\w+) block is clear", init))
    return s


def _apply(s, act, objs):
    hand_empty = s["holding"] is None
    if act == "pick-up":
        (x,) = objs
        if not (hand_empty and x in s["clear"] and x in s["table"]):
            return False
        s["table"].discard(x); s["clear"].discard(x); s["holding"] = x
    elif act == "unstack":
        x, y = objs
        if not (hand_empty and x in s["clear"] and s["on"].get(x) == y):
            return False
        del s["on"][x]; s["clear"].discard(x); s["clear"].add(y); s["holding"] = x
    elif act == "put-down":
        (x,) = objs
        if s["holding"] != x:
            return False
        s["table"].add(x); s["clear"].add(x); s["holding"] = None
    elif act == "stack":
        x, y = objs
        if not (s["holding"] == x and y in s["clear"] and x != y):
            return False
        s["on"][x] = y; s["clear"].discard(y); s["clear"].add(x); s["holding"] = None
    return True


def _goal_holds(s, goal):
    ok = all(s["on"].get(a) == b for a, b in re.findall(r"the (\w+) block is on top of the (\w+) block", goal))
    ok = ok and all(x in s["table"] for x in re.findall(r"the (\w+) block is on the table", goal))
    return ok and all(x in s["clear"] for x in re.findall(r"the (\w+) block is clear", goal))


def valid(plan, gold):
    s = _state(gold["init"])
    return bool(plan) and all(_apply(s, a, o) for a, o in plan) and _goal_holds(s, gold["goal"])


def score(preds, golds, cfg):
    per = [1.0 if p and valid(p, g) else 0.0 for p, g in zip(preds, golds)]
    print(f"[{WID}] {int(sum(per))} of {len(per)} plans valid; empty extractions {sum(1 for p in preds if not p)}")
    return sum(per) / max(1, len(per)), per


if __name__ == "__main__":
    g = {"init": "As initial conditions I have that, the red block is clear, the blue block is clear, the yellow block is clear, the hand is "
                 "empty, the blue block is on top of the orange block, the red block is on the table, the orange block is on the table and "
                 "the yellow block is on the table.", "goal": "My goal is to have that the orange block is on top of the blue block."}
    r1 = "1. **Unstack** the blue block from on top of the orange block.\n2. **Put down** the blue block.\n3. Pick up the orange block.\n4. Stack the orange block on top of the blue block."
    r2 = "pick up the orange block\nstack the orange block on top of the blue block"          # orange is not clear
    r3 = "The hand is empty and the blue block is on top of the orange block, so I unstack it.\nput down the blue block\npick up the orange block\nstack the orange block on top of the blue block"
    assert parse(r1, {}) == [("unstack", ["blue", "orange"]), ("put-down", ["blue"]), ("pick-up", ["orange"]), ("stack", ["orange", "blue"])]
    assert valid(parse(r1, {}), g) and not valid(parse(r2, {}), g) and valid(parse(r3, {}), g) and not valid([], g)
    assert parse("I would stack it somewhere.", {}) == []                                    # wrong object count -> skipped
    v, per = score([parse(r1, {}), parse(r2, {}), None], [g, g, g], {})
    assert abs(v - 1 / 3) < 1e-9
    print("ok")
