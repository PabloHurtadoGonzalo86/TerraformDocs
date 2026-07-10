#!/usr/bin/env python3
"""Combina freshness-findings.json y hcl-validate-findings.json en un
informe Markdown. Cada linea del informe es una cita textual de una fuente
oficial (release de Terraform, pagina de historial de AWS, o diagnostico
real de `terraform validate`) o el resultado mecanico de un grep/comparacion
de versiones. No se redacta ninguna valoracion nueva sobre si algo es
"grave" o "hay que arreglarlo": eso lo decide quien revise el issue.
"""
import json
import os

FRESHNESS_PATH = "freshness-findings.json"
HCL_PATH = "hcl-validate-findings.json"


def load(path, default):
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return default


def render_terraform_section(findings):
    tf = findings.get("terraform_core", [])
    if not tf:
        return ""
    lines = ["## Terraform CLI: notas de version desde la ultima revision\n"]
    for f in tf:
        lines.append(f"### [{f['version']}]({f['url']}) — {f['published_at']}\n")
        if f["upgrade_notes"]:
            lines.append("**UPGRADE NOTES (texto oficial del release):**\n")
            lines.append("```\n" + f["upgrade_notes"].strip() + "\n```\n")
        for dep in f["deprecation_lines"]:
            lines.append(f"- {dep}")
        lines.append("")
    return "\n".join(lines)


def render_aws_provider_section(findings):
    prov = findings.get("aws_provider")
    if not prov:
        return ""
    return (
        "## Provider `hashicorp/aws`: nueva version\n\n"
        f"`{prov['old_version']}` -> `{prov['new_version']}`. "
        f"Changelog oficial: {prov['changelog_url']}\n"
    )


def render_aws_docs_section(findings):
    aws_docs = findings.get("aws_docs", {})
    names = {"iam": "IAM", "s3": "S3", "dynamodb": "DynamoDB"}
    parts = []
    for key, data in aws_docs.items():
        entries = data.get("entries")
        if not entries:
            continue
        parts.append(f"### {names.get(key, key)} — historial de documentacion oficial\n")
        for e in entries[:15]:
            parts.append(f"- **{e['date']}** — [{e['title']}]({e['url']})")
        if len(entries) > 15:
            parts.append(f"- _(+{len(entries) - 15} entradas mas antiguas, ver la pagina oficial)_")
        parts.append("")
    if not parts:
        return ""
    return "## AWS (IAM / S3 / DynamoDB): novedades en la documentacion oficial\n\n" + "\n".join(parts)


def render_affected_chapters(findings):
    hits = findings.get("possibly_affected_chapters", {})
    if not hits:
        return ""
    lines = [
        "## Capitulos posiblemente afectados (coincidencia mecanica de texto, no analisis semantico)\n"
    ]
    for term, chapters in hits.items():
        chs = ", ".join(f"`{c}`" for c in chapters)
        lines.append(f"- Termino `{term}` mencionado en las notas oficiales, tambien aparece en: {chs}")
    lines.append("")
    return "\n".join(lines)


def render_hcl_section(hcl):
    if not hcl:
        return "## Validacion de HCL del manual contra Terraform actual\n\nNo se pudo ejecutar (sin datos).\n"
    total = hcl.get("total_blocks_checked", 0)
    ok = hcl.get("ok", 0)
    incomplete = hcl.get("incomplete_fragment", 0)
    stale = hcl.get("possible_staleness", 0)
    other = hcl.get("other_diagnostics", 0)
    failed = hcl.get("init_failed", 0) + hcl.get("unparseable", 0)

    lines = [
        "## Validacion de HCL del manual contra Terraform actual\n",
        f"Se extrajeron y validaron {total} bloques de codigo completos (los que empiezan por `terraform {{`) "
        f"con la version estable actual de Terraform: {ok} sin problemas, {incomplete} son fragmentos "
        f"pedagogicos incompletos (variable no declarada en el propio bloque, esperado), "
        f"{stale} con posibles señales de obsolescencia, {other} con otros diagnosticos, {failed} sin poder evaluarse.\n",
    ]
    if stale or other:
        for r in hcl.get("results", []):
            if r["status"] not in ("possible_staleness", "other_diagnostics"):
                continue
            lines.append(f"### `{r['chapter']}` (bloque #{r['index']})\n")
            for d in r.get("real_findings", []) + r.get("other", []):
                lines.append(f"- **{d.get('severity', '?')}**: {d.get('summary', '')} — {d.get('detail', '')}")
            lines.append("")
    return "\n".join(lines)


def main():
    findings = load(FRESHNESS_PATH, {})
    hcl = load(HCL_PATH, {})

    sections = [
        render_terraform_section(findings),
        render_aws_provider_section(findings),
        render_aws_docs_section(findings),
        render_affected_chapters(findings),
        render_hcl_section(hcl),
    ]
    body_sections = [s for s in sections if s.strip()]

    has_real_news = bool(
        findings.get("terraform_core")
        or findings.get("aws_provider")
        or any(v.get("entries") for v in findings.get("aws_docs", {}).values())
        or hcl.get("possible_staleness")
        or hcl.get("other_diagnostics")
    )

    intro = (
        "Comprobacion automatica y programada (sin intervencion humana) de si el manual ha quedado "
        "desactualizado frente a fuentes oficiales de Terraform y AWS. Cada dato de este informe es una "
        "cita literal de la fuente oficial enlazada, o el resultado de ejecutar el binario real de "
        "Terraform — nada de este texto ha sido redactado o interpretado por una IA sin verificacion.\n"
    )

    body = intro + "\n" + "\n".join(body_sections) if body_sections else intro + "\nNo se ha detectado ninguna novedad desde la ultima comprobacion.\n"

    with open("issue_body.md", "w", encoding="utf-8") as f:
        f.write(body)

    with open("issue_title.txt", "w", encoding="utf-8") as f:
        f.write("Vigia de obsolescencia: posibles novedades de Terraform/AWS que revisar")

    gh_out = os.environ.get("GITHUB_OUTPUT")
    if gh_out:
        with open(gh_out, "a", encoding="utf-8") as f:
            f.write(f"has_news={'true' if has_real_news else 'false'}\n")

    step_summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if step_summary:
        with open(step_summary, "a", encoding="utf-8") as f:
            f.write(body)

    print("has_real_news:", has_real_news)


if __name__ == "__main__":
    main()
