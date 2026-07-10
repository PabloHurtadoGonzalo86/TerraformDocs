#!/usr/bin/env python3
"""Vigia de obsolescencia: compara el estado guardado en freshness-state.json
contra fuentes OFICIALES en vivo (HashiCorp, Terraform Registry, AWS docs) y
produce una lista de hallazgos citando siempre el texto original de la fuente.
No genera ni reformula texto explicativo por su cuenta: cada hallazgo es una
cita literal (version, fecha, titulo, enlace) de la fuente oficial.
"""
import datetime
import html.parser
import json
import os
import re
import sys
import urllib.request

STATE_PATH = os.environ.get("FRESHNESS_STATE_PATH", "freshness-state.json")
OUTPUT_PATH = os.environ.get("FRESHNESS_OUTPUT_PATH", "freshness-findings.json")
DOCS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "manual-terraform-basics-training-course")
UA = "TerraformDocs-freshness-watch (+https://github.com/PabloHurtadoGonzalo86/TerraformDocs)"

DEFAULT_STATE = {
    "terraform": {"last_checked_version": "1.11.0"},
    "aws_provider": {"last_checked_version": "6.0.0"},
    "aws_docs": {
        "iam_last_seen": "2026-07-02",
        "s3_last_seen": "2026-07-02",
        "dynamodb_last_seen": "2026-07-02",
    },
}

UPGRADE_KEYWORDS = ["deprecat", "no longer", "removed in", "has been removed", "removed the"]


def fetch(url, headers=None):
    req = urllib.request.Request(url, headers={"User-Agent": UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def fetch_json(url, headers=None):
    return json.loads(fetch(url, headers))


def load_state():
    if os.path.exists(STATE_PATH):
        with open(STATE_PATH, encoding="utf-8") as f:
            return json.load(f)
    return json.loads(json.dumps(DEFAULT_STATE))


def version_tuple(v):
    v = v.lstrip("v")
    parts = re.findall(r"\d+", v)
    return tuple(int(p) for p in parts[:3]) + (0,) * (3 - len(parts[:3]))


def github_headers():
    token = os.environ.get("GITHUB_TOKEN")
    return {"Authorization": f"Bearer {token}"} if token else {}


GENERIC_HCL_TERMS = {
    "true", "false", "variable", "output", "resource", "provider", "module",
    "data", "terraform", "locals", "local", "count", "for_each", "source",
    "version", "name", "value", "type", "default", "description",
}


def is_specific_term(term):
    """Filtra terminos demasiado genericos (ruido) de los backticks de las
    notas de version, quedandonos solo con identificadores especificos
    (nombres de recurso, argumentos con guion bajo, subcomandos)."""
    lowered = term.strip().lower()
    if lowered in GENERIC_HCL_TERMS:
        return False
    if len(term) < 6 and "_" not in term and "." not in term:
        return False
    if " " in term and len(term) < 8:
        return False
    return True


def grep_manual_for_terms(terms):
    """Busca terminos literales en el manual (busqueda mecanica, no IA) y
    devuelve la lista de capitulos donde aparecen, como pista de revision."""
    hits = {}
    for term in terms:
        if not is_specific_term(term):
            continue
        for path in sorted(os.listdir(DOCS_DIR)):
            if not path.endswith(".md"):
                continue
            full = os.path.join(DOCS_DIR, path)
            with open(full, encoding="utf-8-sig") as f:
                content = f.read()
            if term in content:
                hits.setdefault(term, set()).add(path)
    return {k: sorted(v) for k, v in hits.items()}


def check_terraform_core(state):
    releases = fetch_json(
        "https://api.github.com/repos/hashicorp/terraform/releases?per_page=100",
        headers=github_headers(),
    )
    stable = [r for r in releases if not r.get("prerelease") and not r.get("draft")]
    if not stable:
        return None, []

    latest = max(stable, key=lambda r: version_tuple(r["tag_name"]))
    last_checked = version_tuple(state["terraform"]["last_checked_version"])

    newer = [r for r in stable if version_tuple(r["tag_name"]) > last_checked]
    newer.sort(key=lambda r: version_tuple(r["tag_name"]))

    findings = []
    for r in newer:
        body = r.get("body") or ""
        upgrade_section = ""
        m = re.search(r"UPGRADE NOTES:(.*?)(?:\n#{1,6} |\n[A-Z][A-Z ]+:|\Z)", body, re.DOTALL)
        if m:
            upgrade_section = m.group(1).strip()
        keyword_lines = [
            line.strip(" *")
            for line in body.splitlines()
            if line.strip().startswith("*") and any(k in line.lower() for k in UPGRADE_KEYWORDS)
        ]
        if upgrade_section or keyword_lines:
            findings.append(
                {
                    "version": r["tag_name"],
                    "published_at": r.get("published_at"),
                    "url": r.get("html_url"),
                    "upgrade_notes": upgrade_section,
                    "deprecation_lines": keyword_lines,
                }
            )

    return latest["tag_name"].lstrip("v"), findings


def check_aws_provider(state):
    data = fetch_json("https://registry.terraform.io/v1/providers/hashicorp/aws/versions")
    versions = [v["version"] for v in data.get("versions", [])]
    if not versions:
        return None
    latest = max(versions, key=version_tuple)
    last_checked = state["aws_provider"]["last_checked_version"]
    if version_tuple(latest) > version_tuple(last_checked):
        return {
            "old_version": last_checked,
            "new_version": latest,
            "changelog_url": "https://github.com/hashicorp/terraform-provider-aws/blob/main/CHANGELOG.md",
        }
    return None


class DocHistoryTableParser(html.parser.HTMLParser):
    """Parser minimo para las tablas de 'Document history' de AWS
    (estructura: fila = [<a>titulo</a>, descripcion, fecha])."""

    def __init__(self):
        super().__init__()
        self.rows = []
        self._in_table = False
        self._in_row = False
        self._cell_index = -1
        self._current_row_text = []
        self._current_link = None
        self._current_link_text = []
        self._in_link = False
        self._depth_tr = 0

    def handle_starttag(self, tag, attrs):
        if tag == "table" and not self._in_table:
            self._in_table = True
        elif tag == "tr" and self._in_table:
            self._in_row = True
            self._cell_index = -1
            self._current_row_text = []
            self._current_link = None
        elif tag == "td" and self._in_row:
            self._cell_index += 1
            self._current_row_text.append("")
        elif tag == "a" and self._in_row and self._cell_index == 0:
            self._in_link = True
            self._current_link_text = []
            href = dict(attrs).get("href")
            self._current_link = href

    def handle_endtag(self, tag):
        if tag == "table" and self._in_table:
            self._in_table = False
        elif tag == "tr" and self._in_row:
            if len(self._current_row_text) >= 3:
                self.rows.append(
                    {
                        "title": "".join(self._current_link_text).strip() or self._current_row_text[0].strip(),
                        "href": self._current_link,
                        "date_text": self._current_row_text[-1].strip(),
                    }
                )
            self._in_row = False
        elif tag == "a" and self._in_link:
            self._in_link = False

    def handle_data(self, data):
        if self._in_row and self._cell_index >= 0:
            self._current_row_text[self._cell_index] += data
            if self._in_link:
                self._current_link_text.append(data)


def parse_aws_date(text):
    text = text.strip()
    for fmt in ("%B %d, %Y", "%b %d, %Y"):
        try:
            return datetime.datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def check_aws_doc_history(url, base_url, last_seen_str):
    raw = fetch(url)
    parser = DocHistoryTableParser()
    parser.feed(raw)
    last_seen = datetime.date.fromisoformat(last_seen_str)
    new_entries = []
    newest_seen = last_seen
    for row in parser.rows:
        d = parse_aws_date(row["date_text"])
        if d is None:
            continue
        if d > last_seen:
            href = row["href"] or ""
            if href and not href.startswith("http"):
                href = base_url.rstrip("/") + "/" + href.lstrip("/")
            new_entries.append({"title": row["title"], "date": d.isoformat(), "url": href or url})
        if d > newest_seen:
            newest_seen = d
    return new_entries, newest_seen.isoformat()


def main():
    state = load_state()
    findings = {"terraform_core": [], "aws_provider": None, "aws_docs": {}}

    latest_tf, tf_findings = check_terraform_core(state)
    if latest_tf:
        state["terraform"]["last_checked_version"] = latest_tf
    findings["terraform_core"] = tf_findings

    aws_provider_finding = check_aws_provider(state)
    if aws_provider_finding:
        findings["aws_provider"] = aws_provider_finding
        state["aws_provider"]["last_checked_version"] = aws_provider_finding["new_version"]

    aws_sources = {
        "iam": (
            "https://docs.aws.amazon.com/IAM/latest/UserGuide/document-history.html",
            "https://docs.aws.amazon.com/IAM/latest/UserGuide/",
        ),
        "s3": (
            "https://docs.aws.amazon.com/AmazonS3/latest/userguide/WhatsNew.html",
            "https://docs.aws.amazon.com/AmazonS3/latest/userguide/",
        ),
        "dynamodb": (
            "https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/DocumentHistory.html",
            "https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/",
        ),
    }
    for key, (url, base) in aws_sources.items():
        try:
            entries, newest = check_aws_doc_history(url, base, state["aws_docs"][f"{key}_last_seen"])
        except Exception as exc:  # noqa: BLE001 - se reporta, no se silencia
            findings["aws_docs"][key] = {"error": f"{type(exc).__name__}: {exc}", "source": url}
            continue
        state["aws_docs"][f"{key}_last_seen"] = newest
        if entries:
            findings["aws_docs"][key] = {"entries": entries, "source": url}

    # Referencias cruzadas puramente mecanicas: terminos citados entre
    # backticks en las notas de Terraform, buscados tal cual en el manual.
    all_terms = set()
    for f in tf_findings:
        all_terms.update(re.findall(r"`([^`]+)`", f["upgrade_notes"] + " " + " ".join(f["deprecation_lines"])))
    findings["possibly_affected_chapters"] = grep_manual_for_terms(all_terms)

    state["last_run_at"] = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False, sort_keys=True)
        f.write("\n")

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(findings, f, indent=2, ensure_ascii=False)

    has_findings = bool(
        tf_findings
        or findings["aws_provider"]
        or any("entries" in v for v in findings["aws_docs"].values())
    )
    print(json.dumps({"has_findings": has_findings, "summary": {
        "terraform_findings": len(tf_findings),
        "aws_provider_bump": bool(aws_provider_finding),
        "aws_docs_services_with_news": [k for k, v in findings["aws_docs"].items() if "entries" in v],
    }}, indent=2, ensure_ascii=False))

    gh_out = os.environ.get("GITHUB_OUTPUT")
    if gh_out:
        with open(gh_out, "a", encoding="utf-8") as f:
            f.write(f"has_findings={'true' if has_findings else 'false'}\n")


if __name__ == "__main__":
    sys.exit(main())
