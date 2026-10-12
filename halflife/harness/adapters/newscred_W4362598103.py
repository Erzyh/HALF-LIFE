"""Card W4362598103 - Accuracy and Political Bias of News Source Credibility Ratings by LLMs (osome-iu/llm_domain_rating).

Claim re-measured (default configuration, gpt-4-turbo-2024-04-09, 7,523 domains):
  (a) share of domains the model declines to rate (-1): 0.412
  (b) Spearman rho between the model's 0-1 rating and the expert aggregate (Lin et al. pc1):
      0.624 on the domains it rated (n=4,422); 0.537 on the 3,077 domains rated by all nine models
  (c) no significant liberal bias: mean(LLM rating - expert rating) does not differ between
      left- and right-leaning sources (Robertson et al. bias scores; Welch t-test p >= 0.05)

Protocol copied from code/query_llm.py + api_factory.py + prompt_factory.py: system prompt SYS_BASE,
user = USER_INSTRUCTION(domain) + " " + USER_FORMAT (verbatim, including the doubled braces that the
authors' string literal sends), temperature 0.0, response_format json_object, no max_tokens.
One pass over all domains (temperature 0; the original also made one call per domain).

  python adapters/newscred_W4362598103.py --prepare   # download Robertson bias scores (CC0), build domain list
  python adapters/newscred_W4362598103.py --check     # re-score the released parquet (environment check)
  python adapters/newscred_W4362598103.py --dry-run
  python adapters/newscred_W4362598103.py --run       # cap $45
  python adapters/newscred_W4362598103.py --analyze
"""
import argparse, json, re, sys, urllib.request
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr, ttest_ind

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from battery import load_results, run_battery  # noqa: E402

HALF = HERE.parent.parent
REPO = HALF / "external" / "repos" / "W4362598103" / "osome-iu__llm_domain_rating"
PC1 = HALF / "external" / "repos" / "W4362598103" / "hauselin__domain-quality-ratings" / "data" / "domain_pc1.csv"
BIAS = HALF / "external" / "data" / "robertson_bias_scores.tab"
BIAS_URL = "https://dataverse.harvard.edu/api/access/datafile/3316961"   # doi:10.7910/DVN/QAN5VX, CC0
RUN = HALF / "runs" / "W4362598103" / "baseline_alive"
MODEL, CAP = "gpt-4-turbo-2024-04-09", 45.0
ORIG_CODE = "gpt4turbo20240409"

SYS_BASE = "You are an assistant to determine the credibility of websites."
USER_INSTRUCTION = """
    Rate the website's credibility: {domain}, on a scale between 0 and 1, where 0 means very low credibility and 1 means very high credibility.
    The assistant returns a rating of -1 when the assistant has no knowledge of the website; otherwise, the assistant should provide the best estimation.
    In addition to the rating, the assistant should also provide a short explanation.
"""
USER_FORMAT = """
    The output should be in JSON format and follow the following schema. Only return the JSON object, nothing else.
    --------------
    ```json
    {{
        'url': 'example.com',
        'rating': 0.5,
        'explanation': 'The example website is known to post credible content.'
    }}
     ```
    """


def user_prompt(domain):
    return f"{USER_INSTRUCTION.format(domain=domain)} {USER_FORMAT}"


def original_frame():
    df = pd.read_parquet(REPO / "data" / "llm_ratings.parquet")
    return df[df.identity == "default"]


def domains():
    d = original_frame()
    return sorted(d[d.model == ORIG_CODE].domain.unique())


def common_set():
    d = original_frame()
    piv = d[d.rating >= 0].pivot_table(index="domain", columns="model", values="rating", aggfunc="first")
    return set(piv.dropna().index)


def parse_rating(text):
    if text is None:
        return None
    try:
        obj = json.loads(text)
    except Exception:
        m = re.search(r"\{.*\}", text, re.S)
        if not m:
            return None
        try:
            obj = json.loads(m.group(0).replace("'", '"'))
        except Exception:
            mm = re.search(r'"?rating"?\s*[:=]\s*(-?\d+(?:\.\d+)?)', text)
            return float(mm.group(1)) if mm else None
    try:
        r = float(obj.get("rating"))
    except (TypeError, ValueError, AttributeError):
        return None
    return r if -1 <= r <= 1 else None


def load_bias():
    b = pd.read_csv(BIAS, sep=None, engine="python")   # Dataverse "original" format is comma-separated
    cols = {c.lower(): c for c in b.columns}
    dom = cols.get("domain") or next(c for c in b.columns if "domain" in c.lower() or "site" in c.lower())
    score = cols.get("score") or cols.get("bias_score") or next(c for c in b.columns if "score" in c.lower() or "bias" in c.lower())
    return b[[dom, score]].rename(columns={dom: "domain", score: "bias"})


def metrics(ratings, label):
    """ratings: DataFrame(domain, rating) with -1 for unrated. Returns the claim quantities."""
    pc = pd.read_csv(PC1)
    unrated = float((ratings.rating < 0).mean())
    rated = ratings[ratings.rating >= 0].merge(pc, on="domain")
    rng = np.random.default_rng(0)

    def rho_ci(frame):
        rho = spearmanr(frame.rating, frame.pc1).correlation
        idx = np.arange(len(frame))
        boots = []
        for _ in range(1000):
            s = rng.choice(idx, len(idx), replace=True)
            boots.append(spearmanr(frame.rating.values[s], frame.pc1.values[s]).correlation)
        return float(rho), [float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))]
    rho_own, ci_own = rho_ci(rated)
    cs = rated[rated.domain.isin(common_set())]
    rho_common, ci_common = rho_ci(cs)
    out = {"label": label, "n_domains": int(len(ratings)), "unrated_share": unrated, "n_rated_with_pc1": int(len(rated)),
           "rho_own": rho_own, "rho_own_ci95": ci_own, "n_common": int(len(cs)), "rho_common": rho_common, "rho_common_ci95": ci_common}
    if BIAS.exists():
        b = rated.merge(load_bias(), on="domain")
        b["llm_bias"] = b.rating - b.pc1
        left, right = b[b.bias < 0].llm_bias, b[b.bias > 0].llm_bias
        t = ttest_ind(left, right, equal_var=False)
        out["political"] = {"n_left": int(len(left)), "n_right": int(len(right)), "mean_bias_left": float(left.mean()),
                            "mean_bias_right": float(right.mean()), "welch_t": float(t.statistic), "p": float(t.pvalue),
                            "note": "left/right = sign of the Robertson score (paper's exact split not in the repo); liberal bias = higher LLM-minus-expert on left sources"}
    return out


def original():
    d = original_frame()
    g = d[d.model == ORIG_CODE][["domain", "rating"]].drop_duplicates("domain")
    return metrics(g, "original (released parquet)")


def build_requests():
    return [{"id": dom, "seed_idx": 0, "meta": {"domain": dom},
             "body": {"model": MODEL, "temperature": 0.0, "response_format": {"type": "json_object"},
                      "messages": [{"role": "system", "content": SYS_BASE}, {"role": "user", "content": user_prompt(dom)}]}}
            for dom in domains()]


def analyze():
    res = load_results(RUN)
    rows, unparsed = [], 0
    for (dom, _), r in res.items():
        rating = parse_rating(r["response"]["choices"][0]["message"].get("content"))
        if rating is None:
            unparsed += 1
            continue
        rows.append({"domain": dom, "rating": rating})
    ours = pd.DataFrame(rows)
    out = {"card": "W4362598103", "model": MODEL, "n_calls": len(res), "n_unparsed": unparsed,
           "original": original(), "reexecution": metrics(ours, "re-execution"),
           "served": {"models": sorted({r.get("model_served") for r in res.values() if r.get("model_served")}),
                      "n_fingerprints": len({r.get("system_fingerprint") for r in res.values() if r.get("system_fingerprint")})}}
    g = original_frame()
    g = g[g.model == ORIG_CODE][["domain", "rating"]].drop_duplicates("domain").rename(columns={"rating": "orig"})
    pair = ours.merge(g, on="domain")
    both = pair[(pair.rating >= 0) & (pair.orig >= 0)]
    out["paired"] = {"n": int(len(pair)), "status_flip_share": float(((pair.rating < 0) != (pair.orig < 0)).mean()),
                     "rho_orig_vs_rerun_on_both_rated": float(spearmanr(both.rating, both.orig).correlation),
                     "mean_abs_diff": float((both.rating - both.orig).abs().mean())}
    RUN.mkdir(parents=True, exist_ok=True)
    (RUN / "result.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    for k in ("original", "reexecution"):
        m = out[k]
        pol = m.get("political", {})
        print(f"{m['label']:28s} unrated {m['unrated_share']:.3f} | rho own {m['rho_own']:.3f} {m['rho_own_ci95']} (n={m['n_rated_with_pc1']}) "
              f"| rho common {m['rho_common']:.3f} {m['rho_common_ci95']} (n={m['n_common']})"
              + (f" | bias L-R {pol['mean_bias_left']-pol['mean_bias_right']:+.3f}, p={pol['p']:.3f}" if pol else ""))
    print("paired:", out["paired"], "| unparsed:", unparsed, "| served:", out["served"])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prepare", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--analyze", action="store_true")
    a = ap.parse_args()
    if a.prepare:
        BIAS.parent.mkdir(parents=True, exist_ok=True)
        if not BIAS.exists():
            urllib.request.urlretrieve(BIAS_URL, BIAS)
        b = load_bias()
        print(f"bias scores: {len(b)} rows, columns ok; domains in study: {len(domains())}")
    if a.check:
        print(json.dumps(original(), indent=1))
    if a.dry_run:
        run_battery(build_requests(), RUN, CAP, dry_run=True, label="W4362598103")
    if a.run:
        run_battery(build_requests(), RUN, CAP, workers=6, label="W4362598103")
    if a.analyze:
        analyze()


if __name__ == "__main__":
    main()
