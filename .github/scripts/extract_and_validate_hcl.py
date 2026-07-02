#!/usr/bin/env python3
"""Extrae los bloques HCL del manual que son configuraciones completas
(empiezan por 'terraform {') y los valida contra el binario de Terraform
instalado en el runner (la version estable actual). Clasifica cada
diagnostico devuelto por `terraform validate -json` usando exclusivamente
el propio texto que emite Terraform -- nunca se inventa ni se reformula
ninguna evaluacion de obsolescencia.
"""
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

DOCS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "manual-terraform-basics-training-course")
FENCE_RE = re.compile(r"```([a-zA-Z]*)\r?\n(.*?)```", re.DOTALL)

# Fragmentos de diagnostico que indican que el bloque es un extracto
# pedagogico incompleto (variable/recurso definido en otra parte del
# capitulo, no en el bloque autonomo), no un problema real de Terraform.
INCOMPLETE_MARKERS = [
    "Reference to undeclared input variable",
    "Reference to undeclared resource",
    "configuration for import target does not exist",
]

DEPRECATION_MARKERS = ["deprecat", "no longer", "removed in", "has been removed"]


def find_complete_blocks():
    blocks = []
    for path in sorted(glob.glob(os.path.join(DOCS_DIR, "*.md"))):
        text = open(path, encoding="utf-8-sig").read()
        for idx, (_lang, body) in enumerate(FENCE_RE.findall(text)):
            stripped = body.strip()
            if re.match(r"^terraform\s*\{", stripped):
                blocks.append(
                    {
                        "chapter": os.path.basename(path),
                        "index": idx,
                        "content": stripped,
                    }
                )
    return blocks


def classify(diagnostics):
    real_findings = []
    incomplete = []
    other = []
    for d in diagnostics:
        text = f"{d.get('summary', '')} {d.get('detail', '')}"
        if any(marker.lower() in text.lower() for marker in INCOMPLETE_MARKERS):
            incomplete.append(d)
        elif any(marker in text.lower() for marker in DEPRECATION_MARKERS):
            real_findings.append(d)
        else:
            other.append(d)
    return real_findings, incomplete, other


def validate_block(block, terraform_bin):
    workdir = tempfile.mkdtemp(prefix="tfcheck_")
    fake_home = tempfile.mkdtemp(prefix="tfcheck_home_")
    try:
        # HOME aislado y desechable: algunos bloques del manual usan
        # file("~/.ssh/id_rsa.pub") a modo ilustrativo. Nunca debe
        # tocarse el ~/.ssh real de quien ejecute este script.
        os.makedirs(os.path.join(fake_home, ".ssh"), exist_ok=True)
        with open(os.path.join(fake_home, ".ssh", "id_rsa.pub"), "w", encoding="utf-8") as f:
            f.write("ssh-ed25519 AAAAstubkeyfortfvalidateonly stub@ci\n")

        env = dict(os.environ)
        env["HOME"] = fake_home
        env["USERPROFILE"] = fake_home  # Windows

        with open(os.path.join(workdir, "main.tf"), "w", encoding="utf-8") as f:
            f.write(block["content"] + "\n")

        init = subprocess.run(
            [terraform_bin, "init", "-backend=false", "-input=false", "-no-color"],
            cwd=workdir,
            capture_output=True,
            text=True,
            timeout=120,
            env=env,
        )
        if init.returncode != 0:
            return {
                "chapter": block["chapter"],
                "index": block["index"],
                "status": "init_failed",
                "detail": init.stdout[-2000:] + init.stderr[-2000:],
            }

        validate = subprocess.run(
            [terraform_bin, "validate", "-json", "-no-color"],
            cwd=workdir,
            capture_output=True,
            text=True,
            timeout=60,
            env=env,
        )
        try:
            result = json.loads(validate.stdout)
        except json.JSONDecodeError:
            return {
                "chapter": block["chapter"],
                "index": block["index"],
                "status": "unparseable",
                "detail": validate.stdout[-2000:] + validate.stderr[-2000:],
            }

        diagnostics = result.get("diagnostics", [])
        real_findings, incomplete, other = classify(diagnostics)

        if result.get("valid") and not diagnostics:
            status = "ok"
        elif real_findings:
            status = "possible_staleness"
        elif incomplete and not other:
            status = "incomplete_fragment"
        else:
            status = "other_diagnostics"

        return {
            "chapter": block["chapter"],
            "index": block["index"],
            "status": status,
            "terraform_version": subprocess.run(
                [terraform_bin, "version", "-json"], capture_output=True, text=True, env=env
            ).stdout,
            "real_findings": real_findings,
            "incomplete": incomplete,
            "other": other,
        }
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


def main():
    terraform_bin = sys.argv[1] if len(sys.argv) > 1 else "terraform"
    blocks = find_complete_blocks()
    results = [validate_block(b, terraform_bin) for b in blocks]

    summary = {
        "total_blocks_checked": len(results),
        "ok": sum(1 for r in results if r["status"] == "ok"),
        "incomplete_fragment": sum(1 for r in results if r["status"] == "incomplete_fragment"),
        "possible_staleness": sum(1 for r in results if r["status"] == "possible_staleness"),
        "other_diagnostics": sum(1 for r in results if r["status"] == "other_diagnostics"),
        "init_failed": sum(1 for r in results if r["status"] == "init_failed"),
        "unparseable": sum(1 for r in results if r["status"] == "unparseable"),
        "results": results,
    }

    out_path = os.environ.get("HCL_VALIDATE_OUTPUT", "hcl-validate-findings.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(json.dumps({k: v for k, v in summary.items() if k != "results"}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
