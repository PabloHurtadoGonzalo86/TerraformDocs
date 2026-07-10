#!/usr/bin/env python3
"""Regenera las paginas de Starlight (docs-site/src/content/docs/manual/) a
partir de la fuente de verdad en manual-terraform-basics-training-course/.

Se ejecuta como paso previo al build en deploy-docs.yml, y tambien la usa
draft_and_verify.py para comprobar que un parche del vigia de obsolescencia
sigue produciendo un sitio valido antes de proponerlo. Existe para que un
parche al manual (automatico o humano) se propague siempre al sitio publicado
sin tener que editar dos copias a mano.

Cada pagina de salida puede combinar uno o dos archivos fuente (algunos
modulos del curso se partieron o fusionaron al adaptarlos a Starlight); el
mapeo esta fijado aqui porque refleja como se escribio el manual, no algo que
deba inferirse en cada ejecucion.
"""
import os
import re
import sys

REPO_ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
SRC_DIR = os.path.join(REPO_ROOT, "manual-terraform-basics-training-course")
OUT_DIR = os.path.join(REPO_ROOT, "docs-site", "src", "content", "docs", "manual")

MODULO_2_MARKER = "# Módulo 2 · Introducción a Infrastructure as Code"

DESCRIPTIONS = {
    "01-introduccion.md": "Presentación del manual, mapa completo del curso y recursos para seguir el aprendizaje.",
    "02-introduccion-iac.md": "Qué problemas resuelve IaC, tipos de herramientas y por qué Terraform.",
    "03-primeros-pasos.md": "Instalación de Terraform, fundamentos de HCL y tu primer flujo init/plan/apply/destroy.",
    "04-fundamentos.md": "Providers, directorio de configuración, variables, atributos, dependencias y outputs.",
    "05-estado.md": "Qué es el archivo de estado, para qué sirve y qué precauciones tomar con él.",
    "06-trabajando-con-terraform.md": "Comandos esenciales, infraestructura mutable vs inmutable, lifecycle, data sources, meta-argumentos, count, for_each y restricciones de versión.",
    "07-terraform-con-aws.md": "Primeros pasos con AWS, IAM, S3 y DynamoDB gestionados con Terraform.",
    "08-estado-remoto.md": "Bloqueo de estado, backend S3 y comandos terraform state.",
    "09-provisioners-ec2.md": "EC2 con Terraform, provisioners remote-exec/local-exec y sus alternativas recomendadas.",
    "10-taint-debug-import.md": "terraform apply -replace, TF_LOG y cómo importar infraestructura existente.",
    "11-modulos.md": "Crear módulos propios y usar módulos del Terraform Registry.",
    "12-funciones-workspaces.md": "Funciones de HCL, expresiones condicionales y gestión de entornos con workspaces.",
    "13-conclusion.md": "Recapitulación del curso, chuleta de comandos, glosario y siguientes pasos.",
}

# out_filename -> lista de (fuente, "full" | "before_modulo_2" | "from_modulo_2")
PAGE_MAP = [
    ("01-introduccion.md", [("01-intro-y-iac.md", "before_modulo_2")]),
    ("02-introduccion-iac.md", [("01-intro-y-iac.md", "from_modulo_2")]),
    ("03-primeros-pasos.md", [("02-primeros-pasos.md", "full")]),
    ("04-fundamentos.md", [("03-basics-providers.md", "full"), ("04-basics-variables.md", "full")]),
    ("05-estado.md", [("05-estado.md", "full")]),
    ("06-trabajando-con-terraform.md", [("06-working-comandos.md", "full"), ("07-working-meta.md", "full")]),
    ("07-terraform-con-aws.md", [("08-aws-iam.md", "full"), ("09-aws-s3-dynamo.md", "full")]),
    ("08-estado-remoto.md", [("10-remote-state.md", "full")]),
    ("09-provisioners-ec2.md", [("11-provisioners-ec2.md", "full")]),
    ("10-taint-debug-import.md", [("12-taint-debug-import.md", "full")]),
    ("11-modulos.md", [("13-modulos.md", "full")]),
    ("12-funciones-workspaces.md", [("14-funciones-workspaces.md", "full")]),
    ("13-conclusion.md", [("15-conclusion.md", "full")]),
]


def read_source(name):
    with open(os.path.join(SRC_DIR, name), encoding="utf-8-sig") as f:
        return f.read()


def extract_title(h1_line):
    return h1_line.lstrip("#").strip()


def strip_h1(text):
    """Quita la primera linea H1 (y la linea en blanco duplicada que deje) de
    un fragmento que va a pasar a formar parte del cuerpo (el H1 lo pone el
    frontmatter de Starlight)."""
    lines = text.split("\n")
    if lines and lines[0].startswith("# "):
        lines = lines[1:]
        while lines and lines[0].strip() == "":
            lines.pop(0)
    return "\n".join(lines)


def slice_source(name, mode):
    content = read_source(name)
    if mode == "full":
        return content
    idx = content.index(MODULO_2_MARKER)
    if mode == "before_modulo_2":
        return content[:idx].rstrip() + "\n"
    if mode == "from_modulo_2":
        return content[idx:]
    raise ValueError(f"modo desconocido: {mode}")


def build_page(out_name, parts):
    first_source, first_mode = parts[0]
    first_content = slice_source(first_source, first_mode)
    first_lines = first_content.split("\n", 1)
    title = extract_title(first_lines[0])
    body_parts = [strip_h1(first_content)]

    for src_name, mode in parts[1:]:
        body_parts.append(slice_source(src_name, mode))

    body = "\n\n".join(p.strip("\n") for p in body_parts) + "\n"
    description = DESCRIPTIONS[out_name].replace('"', '\\"')
    title_escaped = title.replace('"', '\\"')
    frontmatter = f'---\ntitle: "{title_escaped}"\ndescription: "{description}"\n---\n\n'
    return frontmatter + body


def main():
    check_only = "--check" in sys.argv[1:]
    os.makedirs(OUT_DIR, exist_ok=True)

    stale = []
    for out_name, parts in PAGE_MAP:
        generated = build_page(out_name, parts)
        out_path = os.path.join(OUT_DIR, out_name)
        existing = None
        if os.path.exists(out_path):
            with open(out_path, encoding="utf-8") as f:
                existing = f.read()
        if existing == generated:
            continue
        stale.append(out_name)
        if not check_only:
            with open(out_path, "w", encoding="utf-8", newline="\n") as f:
                f.write(generated)

    if check_only:
        if stale:
            print(
                "Desincronizado con manual-terraform-basics-training-course/, "
                "regenera con `python .github/scripts/sync_manual_to_docs_site.py`: "
                + ", ".join(stale),
                file=sys.stderr,
            )
            return 1
        print("docs-site/src/content/docs/manual/ esta sincronizado con el manual.")
        return 0

    if stale:
        print("Regenerado a partir del manual: " + ", ".join(stale))
    else:
        print("docs-site/src/content/docs/manual/ ya estaba sincronizado, sin cambios.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
