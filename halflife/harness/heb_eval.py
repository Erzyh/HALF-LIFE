"""Evaluate samples against human-eval-bia unit tests (execution enabled).

Run inside the paper's environment (halflife/external/venv-heb, Python 3.10):
  python heb_eval.py <samples.jsonl> [--timeout 300] [--workers 8] [--k 1 5 10]
  python heb_eval.py --reference      # canonical solutions -> environment sanity check

Self-contained re-implementation of human_eval/execution.py + evaluation.py from
github.com/haesleinhuepf/human-eval-bia (MIT; itself a fork of openai/human-eval).
The shipped execution.py does not parse (exec line commented out leaves an empty
`with` block), so the helpers are reproduced here with the exec line enabled.
Only human_eval.data (pure stdlib) is imported from the repo.
WARNING: executes model-generated code in subprocesses with a temp working dir.
"""
import argparse, contextlib, io, itertools, json, multiprocessing, os, shutil, sys, tempfile, threading
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
EXTERNAL = HERE.parent / "external" / "human-eval-bia"
sys.path.insert(0, str(EXTERNAL))
from human_eval.data import read_problems, stream_jsonl, write_jsonl  # noqa: E402

PROBLEMS = str(EXTERNAL / "data" / "human-eval-bia.jsonl")
EXAMPLE_DATA = EXTERNAL / "example_data"


class TimeoutException(Exception):
    pass


class WriteOnlyStringIO(io.StringIO):
    def read(self, *a, **k): raise IOError
    def readline(self, *a, **k): raise IOError
    def readlines(self, *a, **k): raise IOError
    def readable(self): return False


class redirect_stdin(contextlib._RedirectStream):  # type: ignore
    _stream = "stdin"


@contextlib.contextmanager
def swallow_io():
    stream = WriteOnlyStringIO()
    with contextlib.redirect_stdout(stream), contextlib.redirect_stderr(stream), redirect_stdin(stream):
        yield


@contextlib.contextmanager
def time_limit(seconds):
    # Windows variant from the repo: a timer thread cannot interrupt the main thread,
    # so the hard limit is enforced by the parent via Process.join/kill.
    timer = threading.Timer(seconds, lambda: None)
    timer.start()
    try:
        yield
    finally:
        timer.cancel()


@contextlib.contextmanager
def chdir(root):
    cwd = os.getcwd()
    os.chdir(root)
    try:
        yield
    finally:
        os.chdir(cwd)


@contextlib.contextmanager
def create_tempdir(copy_examples=False):
    with tempfile.TemporaryDirectory() as dirname:
        os.mkdir(dirname + "/test")
        if copy_examples:
            shutil.copytree(EXAMPLE_DATA, dirname + "/example_data")
        with chdir(dirname + "/test"):
            yield dirname


def unsafe_execute(problem, completion, result, timeout):
    with create_tempdir("file" in problem["prompt"] or "folder" in problem["prompt"]):
        rmtree, rmdir, chdir_ = shutil.rmtree, os.rmdir, os.chdir
        check_program = (problem["prompt"] + completion + "\n" + problem["test"] + "\n"
                         + f"check({problem['entry_point']})")
        try:
            exec_globals = {}
            with swallow_io():
                with time_limit(timeout):
                    exec(check_program, exec_globals)
            result.append("passed")
        except TimeoutException:
            result.append("timed out")
        except BaseException as e:
            result.append(f"failed: {type(e).__name__}: {str(e)[:300]}")
        shutil.rmtree, os.rmdir, os.chdir = rmtree, rmdir, chdir_


def check_correctness(problem, completion, timeout, completion_id):
    manager = multiprocessing.Manager()
    result = manager.list()
    p = multiprocessing.Process(target=unsafe_execute, args=(problem, completion, result, timeout))
    p.start()
    p.join(timeout=timeout + 1)
    if p.is_alive():
        p.kill()
    if not result:
        result.append("timed out")
    return dict(task_id=problem["task_id"], passed=result[0] == "passed",
                result=result[0], completion_id=completion_id)


def estimate_pass_at_k(num_samples, num_correct, k):
    def estimator(n, c, k):
        if n - c < k:
            return 1.0
        return 1.0 - np.prod(1.0 - k / np.arange(n - c + 1, n + 1))
    it = itertools.repeat(num_samples, len(num_correct)) if isinstance(num_samples, int) else iter(num_samples)
    return np.array([estimator(int(n), int(c), k) for n, c in zip(it, num_correct)])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("samples", nargs="?")
    ap.add_argument("--reference", action="store_true")
    ap.add_argument("--timeout", type=float, default=300.0)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--k", type=int, nargs="+", default=[1, 5, 10])
    a = ap.parse_args()

    problems = read_problems(PROBLEMS)
    if a.reference:
        out_dir = HERE.parent / "runs" / "reference"
        out_dir.mkdir(parents=True, exist_ok=True)
        sample_file = out_dir / "samples.jsonl"
        write_jsonl(str(sample_file), [{"task_id": t, "completion": p["canonical_solution"],
                                        "full_response": ""} for t, p in problems.items()])
    else:
        sample_file = Path(a.samples)

    results = defaultdict(list)
    cid = Counter()
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        futs = []
        for s in stream_jsonl(str(sample_file)):
            futs.append(ex.submit(check_correctness, problems[s["task_id"]], s["completion"],
                                  a.timeout, cid[s["task_id"]]))
            cid[s["task_id"]] += 1
        for i, f in enumerate(as_completed(futs), 1):
            r = f.result()
            results[r["task_id"]].append((r["completion_id"], r))
            if i % 50 == 0:
                print(f"  evaluated {i}/{len(futs)}", flush=True)

    total, correct, per_task = [], [], {}
    for tid, rs in results.items():
        rs.sort()
        passed = [r[1]["passed"] for r in rs]
        total.append(len(passed)); correct.append(sum(passed))
        per_task[tid] = {"n": len(passed), "c": sum(passed),
                         "results": [r[1]["result"][:120] for r in rs]}
    total, correct = np.array(total), np.array(correct)
    passk = {f"pass@{k}": float(estimate_pass_at_k(total, correct, k).mean())
             for k in a.k if (total >= k).all()}

    def combine():
        for s in stream_jsonl(str(sample_file)):
            r = results[s["task_id"]].pop(0)[1]
            s["result"], s["passed"] = r["result"], r["passed"]
            yield s
    write_jsonl(str(sample_file) + "_results.jsonl", list(combine()))
    Path(str(sample_file) + "_passk.json").write_text(
        json.dumps({"passk": passk, "n_tasks": len(per_task), "n_samples": int(total.sum()),
                    "per_task": per_task}, indent=2), encoding="utf-8")
    print(json.dumps(passk), flush=True)
    failed = [t for t, v in per_task.items() if v["c"] < v["n"]]
    if a.reference and failed:
        print(f"ENVIRONMENT: {len(failed)} canonical solutions failed:", flush=True)
        for t in failed:
            print(f"  {Path(t).stem}: {per_task[t]['results'][0]}", flush=True)


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
