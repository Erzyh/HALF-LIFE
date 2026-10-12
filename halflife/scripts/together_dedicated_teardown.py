"""Stop and delete the Together dedicated endpoint of the BF16 check and log its hours (2026-09-28).

python scripts/together_dedicated_teardown.py [--dry-run]

Reads runs/p3_bf16_endpoint.json (ids written when the endpoint was created), scales the deployment to 0/0 replicas
(the API's stop), waits for DEPLOYMENT_STATE_STOPPED, clears the endpoint's traffic split, deletes the deployment and then
the endpoint, and appends one row to budget_log.csv with the running minutes x the instance price (billing is per minute
per running replica). The key comes from ../.env (TOGETHER_API_KEY); nothing is printed that contains it.
"""
import csv
import json
import sys
import time
from datetime import date, datetime
from pathlib import Path

import together

HALF = Path(__file__).resolve().parents[1]
DRY = "--dry-run" in sys.argv


def key():
    for line in open(HALF.parent / ".env", encoding="utf-8"):
        if line.startswith("TOGETHER_API_KEY="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit("TOGETHER_API_KEY not in .env")


def main():
    rec = json.load(open(HALF / "runs" / "p3_bf16_endpoint.json", encoding="utf-8"))
    ep, dep = rec["endpoint_id"], rec["deployment_id"]
    c = together.Together(api_key=key(), project_id="proj_CfEFVZM1XjqpQ7dEbeA3s")
    d = c.beta.endpoints.deployments.retrieve(id=dep, endpoint_id=ep).model_dump()
    state = (d.get("status") or {}).get("state") or d.get("state")
    print("deployment", dep, "state", state, "desired", d.get("desired_replicas"))
    if DRY:
        print("dry run: no change"); return
    t_stop = datetime.now()
    if state not in ("DEPLOYMENT_STATE_STOPPED",):
        c.beta.endpoints.deployments.update(id=dep, endpoint_id=ep, autoscaling={"min_replicas": 0, "max_replicas": 0}, update_mask="autoscaling")
        print("stop requested", t_stop.strftime("%H:%M:%S"))
        for _ in range(60):
            time.sleep(20)
            d = c.beta.endpoints.deployments.retrieve(id=dep, endpoint_id=ep).model_dump()
            state = (d.get("status") or {}).get("state") or d.get("state")
            print("  ", time.strftime("%H:%M:%S"), state, (d.get("status") or {}).get("message"))
            if state == "DEPLOYMENT_STATE_STOPPED":
                break
    e = c.beta.endpoints.retrieve(id=ep)
    if e.traffic_split:
        c.beta.endpoints.update(id=ep, traffic_split=[], update_mask="trafficSplit", etag=e.etag or together.omit)
        print("traffic split cleared")
    c.beta.endpoints.deployments.delete(id=dep, endpoint_id=ep)
    print("deployment deleted")
    c.beta.endpoints.delete(id=ep)
    print("endpoint deleted")
    left = [x.id for x in c.beta.endpoints.list()] if hasattr(c.beta.endpoints, "list") else []
    print("endpoints remaining in the project:", left)
    t0 = datetime.strptime(rec["created_at_local"], "%Y-%m-%d %H:%M:%S")
    minutes = round((t_stop - t0).total_seconds() / 60)
    cost = round(minutes / 60 * rec["price_usd_per_hour"], 2)
    rec.update(stopped_at_local=t_stop.strftime("%Y-%m-%d %H:%M:%S"), deleted=True, running_minutes_from_creation=minutes, endpoint_cost_usd=cost)
    json.dump(rec, open(HALF / "runs" / "p3_bf16_endpoint.json", "w", encoding="utf-8"), indent=1)
    log = HALF / "budget_log.csv"
    rows = list(csv.reader(open(log, encoding="utf-8")))
    prev = float(rows[-1][6]) if rows and rows[-1][6] else 0.0
    with open(log, "a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow([str(date.today()), "endpoint", "tierb_p3", rec["endpoint_name"], "", cost, round(prev + cost, 2),
                                f"dedicated endpoint hours for the BF16 check (arm=open70b_bf16): {minutes} min from creation to stop x {rec['price_usd_per_hour']} USD/h, 4x H100 BF16"])
    print(f"logged {minutes} min = {cost} USD (cumulative {round(prev + cost, 2)})")


if __name__ == "__main__":
    main()
