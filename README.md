# TerraformDocs

[![Deploy docs site to GitHub Pages](https://github.com/PabloHurtadoGonzalo86/TerraformDocs/actions/workflows/deploy-docs.yml/badge.svg)](https://github.com/PabloHurtadoGonzalo86/TerraformDocs/actions/workflows/deploy-docs.yml)
[![Vigia de obsolescencia](https://github.com/PabloHurtadoGonzalo86/TerraformDocs/actions/workflows/freshness-watch.yml/badge.svg)](https://github.com/PabloHurtadoGonzalo86/TerraformDocs/actions/workflows/freshness-watch.yml)
[![Ventana de veto y fusion](https://github.com/PabloHurtadoGonzalo86/TerraformDocs/actions/workflows/merge-sweeper.yml/badge.svg)](https://github.com/PabloHurtadoGonzalo86/TerraformDocs/actions/workflows/merge-sweeper.yml)

Manual de estudio completo y 100% original del curso [Terraform Basics Training Course](https://kodekloud.com/courses/terraform-for-beginners) (KodeKloud), redactado siguiendo su temario oficial (13 módulos) y verificado contra la documentación oficial de [Terraform](https://developer.hashicorp.com/terraform) y [AWS](https://docs.aws.amazon.com/).

## 📖 Léelo online

**[pablohurtadogonzalo86.github.io/TerraformDocs](https://pablohurtadogonzalo86.github.io/TerraformDocs/)** — sitio de documentación con búsqueda, construido con [Astro Starlight](https://starlight.astro.build/).

También disponible como Google Docs en [Drive](https://drive.google.com/drive/folders/1K505AeT5C7tYg2OQUDuMYG5EuRvB93hL).

## Estructura del repositorio

| Carpeta / archivo | Contenido |
|---|---|
| [`manual-terraform-basics-training-course/`](manual-terraform-basics-training-course/) | Los 15 documentos en Markdown "plano". **Fuente de verdad** del contenido: todo lo demás se genera a partir de aquí. |
| [`docs-site/`](docs-site/) | Proyecto Astro + Starlight que publica ese contenido como sitio web navegable en GitHub Pages. Sus páginas en `src/content/docs/manual/` se regeneran automáticamente desde el manual (ver `sync_manual_to_docs_site.py` más abajo) — no se editan a mano. |
| [`.github/workflows/`](.github/workflows/) | `deploy-docs.yml` (sincroniza, construye y despliega el sitio), `freshness-watch.yml` y `merge-sweeper.yml` (vigía de obsolescencia, ver abajo), `claude.yml` (integración de Claude Code, responde a menciones `@claude` de colaboradores en issues/PRs). |
| [`.github/scripts/`](.github/scripts/) | Scripts Python del vigía de obsolescencia y de sincronización manual → sitio. |

## Despliegue automático

Cada `push` a `main` que toque el manual o `docs-site/` dispara [`deploy-docs.yml`](.github/workflows/deploy-docs.yml), que:

1. Regenera `docs-site/src/content/docs/manual/` a partir de `manual-terraform-basics-training-course/` con [`sync_manual_to_docs_site.py`](.github/scripts/sync_manual_to_docs_site.py), para que el sitio nunca se desincronice de la fuente.
2. Construye el sitio Astro/Starlight y lo publica en GitHub Pages.

## Vigía de obsolescencia (Terraform y AWS)

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
listando cada hallazgo con su cita y enlace oficial.

El estado (`freshness-state.json`) se versiona en el repo y el propio workflow lo actualiza en
cada ejecución — así cada comprobación mensual solo informa de lo que cambió *desde la anterior*,
no de todo el historial.

### Resolución automática del issue (con el mismo rigor que una revisión de código humana)

En el mismo run, el job `draft-and-verify` de `freshness-watch.yml` intenta resolver cada
hallazgo por su cuenta, con las mismas comprobaciones que se le exigirían a cualquier PR de una
persona antes de fusionarlo:

1. **Triaje conservador**: solo se procesan hallazgos con una coincidencia mecánica (grep) contra
   contenido real de algún capítulo del manual. Un aviso sobre requisitos para *compilar* el propio
   Terraform, por ejemplo, no toca ningún capítulo y se descarta sin gastar ni una llamada a la API.
2. **Redacción acotada**: para cada hallazgo con capítulo afectado, [`draft_and_verify.py`](.github/scripts/draft_and_verify.py)
   llama a la API de Claude (`claude-sonnet-5`) con salida JSON estructurada, pidiendo un cambio
   *mínimo* y anclado a un fragmento **exacto y único** del capítulo (en `manual-terraform-basics-training-course/`,
   la fuente de verdad). La cita oficial se marca explícitamente como dato a analizar, nunca como
   instrucción. Si el fragmento propuesto no se localiza de forma única en el capítulo, se descarta
   sin aplicarse.
3. **Verificación real**: se resincroniza `docs-site/` desde el manual ya parcheado y se ejecuta
   `npm run build` (Astro/Starlight), además de la misma validación de HCL contra el Terraform real
   de antes.
4. **Revisión adversarial independiente**: una segunda llamada, con contexto nuevo y un modelo
   distinto (`claude-opus-4-8`), cuyo único trabajo es intentar refutar el cambio contra la cita —
   ante cualquier duda, se descarta. Se comprueba además que la URL citada responde de verdad.
5. Solo si **todo** lo anterior pasa se abre un PR (`auto-fix-pending`), con cada cambio listado
   junto a su cita y el resultado de cada verificación.

Si nada necesitaba cambio, o si un cambio propuesto no supera alguna verificación, el issue se
cierra o se comenta explicando el motivo — nunca se aplica nada que no haya pasado todas las
comprobaciones, y nunca se finge una resolución que no ha ocurrido.

### Fusión con ventana de veto de 48 horas

[`merge-sweeper.yml`](.github/workflows/merge-sweeper.yml) revisa cada hora los PR `auto-fix-pending`
abiertos. Un PR se fusiona automáticamente (squash) solo si **todas** estas condiciones se cumplen:
tiene ≥48h abierto, sigue teniendo exactamente el commit original del bot (nadie ha añadido
commits), nadie ha comentado, y nadie ha dejado una revisión. Si detecta cualquier rastro humano,
lo marca `auto-fix-vetoed` y nunca lo fusiona solo. Esto da una ventana real para cerrar o editar
el PR si algo no convence, sin necesidad de revisar activamente cada uno — el mismo patrón que usan
Dependabot/Renovate para auto-merge, adaptado a contenido en prosa en vez de a un número de versión.

### Poner en marcha la resolución automática

El único paso manual que falta es crear un `ANTHROPIC_API_KEY` y añadirlo como secreto del
repositorio (Settings → Secrets and variables → Actions). Sin ese secreto, el vigía sigue abriendo
issues con los hallazgos, simplemente no intenta resolverlos por su cuenta.

## Cómo se elaboró el manual

1. Temario extraído de las páginas oficiales de KodeKloud (curso y notas), sin acceder a contenido de pago.
2. Redacción original por bloques temáticos, con analogías, ejemplos HCL completos, laboratorios y preguntas de repaso en cada lección.
3. Verificación técnica adversarial de cada afirmación, comando y argumento contra `developer.hashicorp.com/terraform`, `registry.terraform.io` y `docs.aws.amazon.com`.
4. Revisión de estilo y estructura en español, y auditoría final de cobertura del 100% del temario oficial.
5. Publicación en Google Docs y como sitio Starlight desplegado en GitHub Pages, mantenido al día por el vigía de obsolescencia descrito arriba.
