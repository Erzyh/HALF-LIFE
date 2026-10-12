"""Hook W4410627635 (Brazilian federal service automation, GPT-4 Turbo, 72% immediate/short-term horizon).

load_items -> sheet 'nova' of cargo_atividade_ni_prompt.xlsx (1,136 job duties, 142 position ids) joined with
              sheet 'cargos' (the 142 position names; its header cell is itself the first name, ADERECISTA).
              Row: {row_no (1-based, the number the released prompt uses), cargo, atividade}.
render     -> system = the released script's triple-quoted string, read verbatim from system_prompt_extracted.txt;
              user   = "\n<row_no>;<CARGO>;<atividade>\n\n", the exact shape of that script's user message.
parse      -> the automation horizon: split the returned CSV row on ';' and take the LAST field that is a bare
              integer 0-3. This lands on 'horizonte' under both layouts the prompt describes - the twelve-column
              specification of instruction 5 and the ten-column rows of its own worked example - because the
              horizon is the last standalone number before the closing free-text justification.
score      -> share of duties whose horizon is 0 (imediata) or 1 (curto prazo). There is no gold label; golds
              are ignored, and unparsed replies are dropped from the denominator.
"""
import re
from pathlib import Path

DATA = Path(__file__).resolve().parents[3] / "external" / "data" / "tierb_items" / "W4410627635"
XLSX = DATA / "cargo_atividade_ni_prompt.xlsx"
SYSTEM = DATA / "system_prompt_extracted.txt"
NEAR_TERM = {0, 1}


def _system():
    if not SYSTEM.exists():
        raise NeedsHuman(f"missing {SYSTEM}; re-extract the triple-quoted string of Prompt GPT-4-gov-v4.py")  # noqa: F821
    return SYSTEM.read_text(encoding="utf-8")


def load_items(cfg):
    import pandas as pd
    if not XLSX.exists():
        raise NeedsHuman(f"missing {XLSX} (Google Drive folder 1kYqUzCRbaFB3YpfJij8KSOeiy-5thLr-)")  # noqa: F821
    x = pd.ExcelFile(XLSX)
    nova = x.parse("nova")
    col = x.parse("cargos").columns[0]
    cargos = [col] + x.parse("cargos")[col].tolist()          # the header cell is the first position name
    if len(nova) != 1136 or len(cargos) != 142:
        raise NeedsHuman(f"expected 1136 duties and 142 positions, got {len(nova)} and {len(cargos)}")  # noqa: F821
    rows = []
    for i, r in enumerate(nova.itertuples(index=False), start=1):
        rows.append({"row_no": i, "cargo": cargos[int(r.id) - 1], "atividade": str(r.atividade_proposta).strip()})
    return rows


def render(cfg, row):
    return [{"role": "system", "content": _system()},
            {"role": "user", "content": f"\n{row['row_no']};{row['cargo']};{row['atividade']}\n\n"}]


def parse(text, cfg=None):
    if not text:
        return None
    best = None
    for line in str(text).splitlines():
        fields = [f.strip() for f in line.split(";")]
        if len(fields) < 5:
            continue                                   # not a data row (header, prose, fences)
        hits = [int(f) for f in fields if re.fullmatch(r"[0-3]", f)]
        if hits:
            best = hits[-1]
    return best


def score(preds, golds=None, cfg=None):
    per = [1.0 if p in NEAR_TERM else 0.0 for p in preds if p is not None]
    return (sum(per) / len(per) if per else 0.0), per


if __name__ == "__main__":
    class NeedsHuman(Exception):
        pass
    rows = load_items({})
    assert rows[580] == {"row_no": 581, "cargo": "RECREACIONISTA",
                         "atividade": "Organizar eventos e festividades com foco em atividades de lazer e entretenimento"}, rows[580]
    msgs = render({}, rows[580])
    assert msgs[1]["content"] == ("\n581;RECREACIONISTA;Organizar eventos e festividades com foco em "
                                  "atividades de lazer e entretenimento\n\n")
    print(len(rows), "duties | system", len(msgs[0]["content"]), "chars | user ==", repr(msgs[1]["content"]))
    # rows copied from the worked example inside the released system prompt (ten-column layout)
    ten = [("1;1;IMP;Impressoras 3D FDM;AD;Data Visualization;RE;Realidade Aumentada (AR);2;A combinacao ...;", 2),
           ("6;1;RE;Realidade Aumentada (AR);0;0;0;0;0;Integracao de aderecos ...;", 0),
           ("28;2;IOT;Sensores Inteligentes;0;0;0;0;1;Inspecao do estado ...;", 1),
           ("35;1;RBO;Drones;IOT;Sensores Inteligentes;0;0;3;O uso de drones ...;", 3)]
    for line, want in ten:
        assert parse(line) == want, (line, parse(line), want)
    # twelve-column layout of instruction 5: horizonte is eleventh, justificativa3 last
    twelve = "12;3;Justificativa um;IOT;Plataformas;0;0;0;0;Justificativa dois;1;Justificativa tres"
    assert parse(twelve) == 1, parse(twelve)
    assert parse("Desculpe, nao posso responder.") is None and parse(None) is None
    v, per = score([p for p, _ in [(parse(l), w) for l, w in ten]])
    print("ok | parsed horizons", [parse(l) for l, _ in ten], "| near-term share", round(v, 4), "of", len(per))
