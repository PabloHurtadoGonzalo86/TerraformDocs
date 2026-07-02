# TerraformDocs

[![Deploy documentation to GitHub Pages](https://github.com/PabloHurtadoGonzalo86/TerraformDocs/actions/workflows/deploy-docs.yml/badge.svg)](https://github.com/PabloHurtadoGonzalo86/TerraformDocs/actions/workflows/deploy-docs.yml)

📖 **Sitio publicado:** https://pablohurtadogonzalo86.github.io/TerraformDocs/

Manual completo en español del curso [Terraform Basics Training Course](https://kodekloud.com/courses/terraform-for-beginners) (KodeKloud), publicado como sitio de documentación navegable con [MkDocs](https://www.mkdocs.org/) y el tema [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/).

El contenido del manual vive en [`manual-terraform-basics-training-course/`](manual-terraform-basics-training-course/); ese mismo directorio es la fuente que MkDocs convierte en el sitio publicado, sin copias intermedias.

## Despliegue automático

Cada `push` a `main` dispara el workflow [`deploy-docs.yml`](.github/workflows/deploy-docs.yml), que:

1. Construye el sitio con `mkdocs build --strict` (el build falla ante cualquier warning: enlaces rotos, páginas huérfanas sin incluir en la navegación, etc.).
2. Publica el resultado en GitHub Pages mediante `actions/deploy-pages`.

Es decir: en cuanto se añade o edita un capítulo del manual, la web se reconstruye y republica sola, sin pasos manuales.

## Desarrollo local

```bash
pip install -r requirements.txt
mkdocs serve       # sirve el sitio en http://127.0.0.1:8000 con recarga en caliente
mkdocs build --strict   # build de verificación, igual que en CI
```
