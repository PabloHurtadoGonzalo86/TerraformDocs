# TerraformDocs

[![Deploy documentation to GitHub Pages](https://github.com/PabloHurtadoGonzalo86/TerraformDocs/actions/workflows/deploy-docs.yml/badge.svg)](https://github.com/PabloHurtadoGonzalo86/TerraformDocs/actions/workflows/deploy-docs.yml)
[![Vigia de obsolescencia](https://github.com/PabloHurtadoGonzalo86/TerraformDocs/actions/workflows/freshness-watch.yml/badge.svg)](https://github.com/PabloHurtadoGonzalo86/TerraformDocs/actions/workflows/freshness-watch.yml)
[![Ventana de veto y fusion](https://github.com/PabloHurtadoGonzalo86/TerraformDocs/actions/workflows/merge-sweeper.yml/badge.svg)](https://github.com/PabloHurtadoGonzalo86/TerraformDocs/actions/workflows/merge-sweeper.yml)

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
listando cada hallazgo con su cita y enlace oficial.

El estado (`freshness-state.json`) se versiona en el repo y el propio workflow lo actualiza en
cada ejecución — así cada comprobación mensual solo informa de lo que cambió *desde la anterior*,
no de todo el historial.

### Resolución automática del issue (con el mismo rigor que una revisión de código humana)

En el mismo run, el job `draft-and-verify` de `freshness-watch.yml` intenta resolver cada
hallazgo por su cuenta, con las mismas comprobaciones que se le exigirían a cualquier PR de una
persona antes de fusionarlo:

1. **Triaje conservador**: solo se procesan hallazgos con una coincidencia mecánica (grep) contra
   contenido real de algún capítulo. Un aviso sobre requisitos para *compilar* el propio Terraform,
   por ejemplo, no toca ningún capítulo y se descarta sin gastar ni una llamada a la API.
2. **Redacción acotada**: para cada hallazgo con capítulo afectado, [`draft_and_verify.py`](.github/scripts/draft_and_verify.py)
   llama a la API de Claude (`claude-sonnet-5`) con salida JSON estructurada, pidiendo un cambio
   *mínimo* y anclado a un fragmento **exacto y único** del capítulo. La cita oficial se marca
   explícitamente como dato a analizar, nunca como instrucción. Si el fragmento propuesto no se
   localiza de forma única en el capítulo, se descarta sin aplicarse.
3. **Verificación real**: `mkdocs build --strict` y la misma validación de HCL contra el Terraform
   real de antes, ahora sobre el árbol ya parcheado.
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
tienen ≥48h abiertos, siguen teniendo exactamente el commit original del bot (nadie ha añadido
commits), nadie ha comentado, y nadie ha dejado una revisión. Si detecta cualquier rastro humano,
lo marca `auto-fix-vetoed` y nunca lo fusiona solo. Esto da una ventana real para cerrar o editar
el PR si algo no convence, sin necesidad de revisar activamente cada uno — el mismo patrón que usan
Dependabot/Renovate para auto-merge, adaptado a contenido en prosa en vez de a un número de versión.

### Único paso manual real: la API key

Todo lo anterior requiere un secreto `ANTHROPIC_API_KEY` en el repo — no hay forma de que yo (ni
ningún workflow) genere una credencial de facturación en tu cuenta de Anthropic por ti. Sin ese
secreto, `draft-and-verify` no falla: detecta su ausencia, no hace nada, y dejas el issue como
antes (solo detección, sin auto-resolución) hasta que lo configures:

```bash
# 1. Crea una clave en https://console.anthropic.com/settings/keys
# 2. Guárdala como secreto del repo (te pedirá pegarla de forma segura, no queda en el historial de shell):
gh secret set ANTHROPIC_API_KEY --repo PabloHurtadoGonzalo86/TerraformDocs
```

Coste esperado: como mucho un puñado de llamadas a la API una vez al mes (cuando `freshness-watch`
encuentra algo que revisar), no una factura recurrente por uso constante.

## Desarrollo local

```bash
pip install -r requirements.txt
mkdocs serve       # sirve el sitio en http://127.0.0.1:8000 con recarga en caliente
mkdocs build --strict   # build de verificación, igual que en CI
```
