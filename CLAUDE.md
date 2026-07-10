# TerraformDocs

Manual de estudio en español del curso Terraform Basics Training Course (KodeKloud), verificado contra la documentación oficial de Terraform y AWS.

## Estructura

- `manual-terraform-basics-training-course/` — fuente de verdad en Markdown plano, un archivo por bloque temático.
- `docs-site/` — proyecto Astro + Starlight que publica ese contenido en `docs-site/src/content/docs/manual/` (una página por módulo del curso, 13 en total). Se despliega a GitHub Pages con `.github/workflows/deploy-docs.yml`.

## Convenciones

- Todo el contenido está en español (de España), con tono didáctico y cercano, tuteando al lector.
- Cada lección sigue esta estructura: "¿Qué vas a aprender?", explicación con analogía, ejemplos HCL completos, caja de errores comunes (⚠️), buenas prácticas (⭐/💡), un laboratorio (🧪) y preguntas de repaso (❓).
- Cualquier afirmación técnica (comandos, flags, argumentos de recursos, comportamiento de versiones) debe verificarse contra `developer.hashicorp.com/terraform`, `registry.terraform.io` o `docs.aws.amazon.com` antes de darla por buena — no inventar sintaxis ni comportamientos.
- Las páginas de `docs-site/src/content/docs/manual/` requieren frontmatter `title` y `description`, y no deben contener ningún encabezado `# ` (H1) en el cuerpo — Starlight ya renderiza el H1 a partir del `title`.
- Antes de dar por buena cualquier modificación en `docs-site/`, ejecuta `npm run build` dentro de esa carpeta y confirma que termina sin errores ni warnings.
