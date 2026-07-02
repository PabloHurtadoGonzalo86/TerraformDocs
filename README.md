# TerraformDocs

[![Deploy documentation to GitHub Pages](https://github.com/PabloHurtadoGonzalo86/TerraformDocs/actions/workflows/deploy-docs.yml/badge.svg)](https://github.com/PabloHurtadoGonzalo86/TerraformDocs/actions/workflows/deploy-docs.yml)
[![Vigia de obsolescencia](https://github.com/PabloHurtadoGonzalo86/TerraformDocs/actions/workflows/freshness-watch.yml/badge.svg)](https://github.com/PabloHurtadoGonzalo86/TerraformDocs/actions/workflows/freshness-watch.yml)

📖 **Sitio publicado:** https://pablohurtadogonzalo86.github.io/TerraformDocs/

Manual completo en español del curso [Terraform Basics Training Course](https://kodekloud.com/courses/terraform-for-beginners) (KodeKloud), publicado como sitio de documentación navegable con [MkDocs](https://www.mkdocs.org/) y el tema [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/).

El contenido del manual vive en [`manual-terraform-basics-training-course/`](manual-terraform-basics-training-course/); ese mismo directorio es la fuente que MkDocs convierte en el sitio publicado, sin copias intermedias.

## Despliegue automático

Cada `push` a `main` dispara el workflow [`deploy-docs.yml`](.github/workflows/deploy-docs.yml), que:

1. Construye el sitio con `mkdocs build --strict` (el build falla ante cualquier warning: enlaces rotos, páginas huérfanas sin incluir en la navegación, etc.).
2. Publica el resultado en GitHub Pages mediante `actions/deploy-pages`.

Es decir: en cuanto se añade o edita un capítulo del manual, la web se reconstruye y republica sola, sin pasos manuales.

## Vigia de obsolescencia (Terraform y AWS)

Un manual estático se queda obsoleto en cuanto HashiCorp o AWS cambian algo. El workflow
[`freshness-watch.yml`](.github/workflows/freshness-watch.yml) comprueba eso automáticamente,
sin ninguna acción manual, el día 1 de cada mes (y bajo demanda con "Run workflow" en la pestaña
Actions). Combina tres señales, todas trazables a una fuente oficial o al propio binario de
Terraform — nunca a una IA sin verificar:

1. **Notas de versión oficiales de Terraform CLI** ([`releases` de hashicorp/terraform](https://github.com/hashicorp/terraform/releases)): compara la última versión estable con la última revisada, y cita textualmente cualquier `UPGRADE NOTES` o mención de `deprecat(ed)` entre medias.
2. **Versión del provider `hashicorp/aws`** ([Terraform Registry](https://registry.terraform.io/providers/hashicorp/aws)): igual, con enlace directo al changelog oficial del provider.
3. **Validación real contra el binario de Terraform actual**: extrae los bloques de código del manual que son configuraciones completas (empiezan por `terraform {`) y ejecuta `terraform init` + `terraform validate` de verdad con la versión estable vigente. Cualquier diagnóstico de obsolescencia que aparezca es el que emite el propio Terraform, citado tal cual — el script solo distingue eso de los fragmentos pedagógicos incompletos (variables no declaradas en el propio extracto), que se descartan como ruido esperado.
4. **Historial de documentación oficial de AWS** (IAM, S3, DynamoDB — las tres páginas de *document history* oficiales que cubre el manual).

Si hay algo nuevo, se abre (o actualiza) un [issue con la etiqueta `obsolescencia`](https://github.com/PabloHurtadoGonzalo86/TerraformDocs/issues?q=is%3Aissue+label%3Aobsolescencia)
listando cada hallazgo con su cita y enlace oficial, y los capítulos del manual donde ese mismo
término aparece (pista mecánica, no un diagnóstico). Deliberadamente **no** reescribe el
contenido del manual por su cuenta: la redacción del manual está verificada línea a línea contra
la documentación oficial, y dejar que una IA la reescriba sin supervisión en un cron reintroduciría
justo el riesgo de alucinación que este manual evita. El issue es la señal automática; la edición
la revisa un humano (o una sesión de Claude Code dirigida explícitamente a resolver ese issue).

El estado (`freshness-state.json`) se versiona en el repo y el propio workflow lo actualiza en
cada ejecución — así cada comprobación mensual solo informa de lo que cambió *desde la anterior*,
no de todo el historial.

## Desarrollo local

```bash
pip install -r requirements.txt
mkdocs serve       # sirve el sitio en http://127.0.0.1:8000 con recarga en caliente
mkdocs build --strict   # build de verificación, igual que en CI
```
