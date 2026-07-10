# TerraformDocs

Manual de estudio completo y 100% original del curso [Terraform Basics Training Course](https://kodekloud.com/courses/terraform-for-beginners) de KodeKloud, redactado siguiendo su temario oficial (13 módulos) y verificado contra la documentación oficial de [Terraform](https://developer.hashicorp.com/terraform) y [AWS](https://docs.aws.amazon.com/).

## 📖 Léelo online

**[pablohurtadogonzalo86.github.io/TerraformDocs](https://pablohurtadogonzalo86.github.io/TerraformDocs/)** — sitio de documentación con búsqueda, construido con [Astro Starlight](https://starlight.astro.build/).

También disponible como Google Docs en [Drive](https://drive.google.com/drive/folders/1K505AeT5C7tYg2OQUDuMYG5EuRvB93hL).

## Estructura del repositorio

| Carpeta | Contenido |
|---|---|
| [`manual-terraform-basics-training-course/`](manual-terraform-basics-training-course/) | Los 15 documentos en Markdown "plano", fuente de verdad del contenido. |
| [`docs-site/`](docs-site/) | Proyecto Astro + Starlight que publica ese contenido como sitio web navegable, desplegado en GitHub Pages. |
| [`.github/workflows/`](.github/workflows/) | `deploy-docs.yml` (build y despliegue a Pages) y `claude.yml` (integración de Claude Code, responde a menciones `@claude` de colaboradores en issues/PRs). |

## Cómo se elaboró

1. Temario extraído de las páginas oficiales de KodeKloud (curso y notas), sin acceder a contenido de pago.
2. Redacción original por bloques temáticos, con analogías, ejemplos HCL completos, laboratorios y preguntas de repaso en cada lección.
3. Verificación técnica adversarial de cada afirmación, comando y argumento contra `developer.hashicorp.com/terraform`, `registry.terraform.io` y `docs.aws.amazon.com`.
4. Revisión de estilo y estructura en español, y auditoría final de cobertura del 100% del temario oficial.
5. Publicación en Google Docs y como sitio Starlight desplegado en GitHub Pages.
