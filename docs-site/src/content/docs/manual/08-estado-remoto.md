---
title: "Módulo 8 · Estado remoto"
description: "Bloqueo de estado, backend S3 y comandos terraform state."
---

Hasta ahora tu fichero `terraform.tfstate` ha vivido tranquilamente en tu disco duro. Eso funciona mientras trabajas solo, pero en cuanto entra en juego un equipo (o un *pipeline* de CI/CD, la cadena automática de integración y despliegue continuos), el estado local se convierte en el eslabón más frágil de todo el flujo. En este módulo vas a aprender por qué, cómo lo resuelve un **backend remoto** como Amazon S3 y cómo operar sobre el estado con seguridad usando los comandos `terraform state`.

## 8.1 Estado remoto y bloqueo de estado (state locking)

**¿Qué vas a aprender?** En esta lección entenderás por qué guardar el estado en local es un problema serio cuando varias personas trabajan sobre la misma infraestructura, qué desastres concretos puede provocar (desincronización y corrupción del estado) y cómo los backends remotos y el *state locking* los evitan. También verás qué backends ofrece Terraform de serie.

### El problema: un estado, muchas manos

Recuerda qué es el estado: el fichero JSON donde Terraform apunta la correspondencia entre tu configuración y los objetos reales que existen en el proveedor. Es su única fuente de verdad. Si el estado miente, Terraform actúa a ciegas.

Imagina que compartes piso y lleváis las cuentas en una libreta. Si solo hay **una** libreta en la cocina, todo va bien. Pero si cada compañero se hace una fotocopia y apunta sus gastos en la suya, al final del mes tenéis cuatro versiones distintas de la realidad y ninguna es completa. Eso es exactamente lo que pasa con `terraform.tfstate` en local: cada miembro del equipo tiene *su* copia, y cada `apply` la desactualiza para todos los demás.

Los dos fallos concretos son:

1. **Desincronización.** Ana ejecuta `terraform apply` y crea una instancia EC2; su estado local lo refleja, pero el de Bruno no. Cuando Bruno ejecuta `apply` con su copia antigua, Terraform no sabe que esa instancia existe y puede intentar crearla de nuevo o, peor, destruir cambios de Ana.
2. **Corrupción por operaciones simultáneas.** Si dos personas (o dos pipelines) lanzan `apply` a la vez contra el mismo estado, ambas escrituras se pisan. El resultado puede ser un estado a medio escribir, recursos huérfanos que existen en AWS pero que ningún estado registra, o atributos inconsistentes.

¿Y si guardamos `terraform.tfstate` en Git, junto al código? Mala idea, por tres razones: el estado contiene **datos sensibles en texto plano** (contraseñas de bases de datos, IPs, claves), Git **no impide dos `apply` simultáneos** (no hay bloqueo), y depende de la disciplina humana: basta con que alguien olvide hacer `push` o `pull` una vez para volver al escenario de la libreta fotocopiada.

### La solución: backend remoto + bloqueo

Un **backend** es el componente de Terraform que decide *dónde* se guarda el estado y *cómo* se realizan las operaciones sobre él. Por defecto usas el backend `local` (el fichero en disco). Un **backend remoto** guarda el estado en un almacenamiento compartido: cada `plan` descarga la última versión y cada `apply` sube la nueva. Vuelve a haber una sola libreta en la cocina.

El **state locking** (bloqueo de estado) resuelve el segundo problema: antes de cualquier operación que pueda escribir el estado, Terraform adquiere un **candado**; si otra persona ya lo tiene, la operación falla inmediatamente en lugar de corromper nada. Es el pestillo del cuarto de baño: no impide que quieras entrar, solo que entréis dos a la vez. El bloqueo es automático en todas las operaciones que pueden escribir estado, y puedes desactivarlo con `-lock=false` (no lo hagas salvo emergencia). Ojo: **no todos los backends soportan bloqueo**; consulta la documentación de cada uno.

Estos son los backends disponibles de serie en Terraform 1.x actual:

| Backend | Almacenamiento | ¿Bloqueo? |
|---|---|---|
| `local` | Fichero en disco | Sí (fichero de bloqueo local) |
| `s3` | Amazon S3 | Sí (lockfile nativo o DynamoDB) |
| `azurerm` | Azure Blob Storage | Sí |
| `gcs` | Google Cloud Storage | Sí |
| `remote` | HCP Terraform / Terraform Enterprise (desde Terraform 1.1 se recomienda el bloque `cloud` en su lugar) | Sí |
| `consul` | HashiCorp Consul | Sí |
| `kubernetes` | Secret de Kubernetes | Sí |
| `http`, `pg`, `oss`, `cos`, `oci` | Varios | Según implementación |

Fíjate en un detalle curioso: el backend `local` **también** bloquea. Si lanzas dos operaciones a la vez en tu máquina, la segunda fallará. Lo vas a comprobar en el laboratorio.

> ⚠️ **Errores comunes:**
> - **Subir `terraform.tfstate` a Git.** Expone secretos y no soluciona la concurrencia. Añade `*.tfstate*` a tu `.gitignore` desde el primer día.
> - **Usar `-lock=false` para "quitarse el error de en medio".** Si el estado está bloqueado, casi siempre es porque otra operación está en curso. Saltarte el candado es la receta para corromperlo.
> - **Hacer `force-unlock` sin investigar.** `terraform force-unlock <ID>` existe para liberar un candado huérfano (por ejemplo, tras un corte de red), pero solo debes usarlo con **tu propio** candado y cuando estés seguro de que no hay ninguna operación viva.

> 💡 **Buenas prácticas:**
> - En cuanto haya más de una persona (o un pipeline) tocando la infraestructura, migra a un backend remoto con bloqueo. No esperes al primer susto.
> - Trata el estado como un secreto: cifrado en reposo, acceso restringido y nunca en el repositorio.
> - Deja el bloqueo siempre activado. Por defecto, si el candado está ocupado la operación falla al instante; con `-lock-timeout=30s` puedes pedirle a Terraform que reintente durante ese tiempo antes de rendirse.

### 🧪 Laboratorio

**Objetivo:** provocar (sin riesgo) un conflicto de bloqueo para ver el *state locking* en acción con el backend local.

1. Crea una carpeta `lab-locking` con este `main.tf`:

```hcl
# main.tf — proyecto mínimo en AWS para observar el bloqueo de estado
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

provider "aws" {
  region = "eu-west-1" # Irlanda
}

# Un bucket S3: recurso gratuito y rápido de crear
resource "aws_s3_bucket" "demo" {
  bucket = "pablo-lab-locking-2026" # los nombres de bucket son globales: cámbialo
}
```

2. Ejecuta `terraform init` y luego, en una **primera terminal**, `terraform apply`. **No respondas** todavía a la pregunta `Do you want to perform these actions?`: mientras espera tu confirmación, Terraform mantiene el candado del estado.
3. Abre una **segunda terminal** en la misma carpeta y lanza `terraform plan`. Verás algo así:

```text
╷
│ Error: Error acquiring the state lock
│
│ Error message: resource temporarily unavailable
│ Lock Info:
│   ID:        b7a41895-3de2-41d3-b6b2-0e1c2f9a7c31
│   Path:      terraform.tfstate
│   Operation: OperationTypeApply
│   Who:       pablo@portatil
│   Created:   2026-07-02 10:14:03 UTC
╵
```

4. Vuelve a la primera terminal, responde `yes` y deja que termine. Repite el `plan` en la segunda: ahora funciona, porque el candado se ha liberado.
5. Limpia con `terraform destroy`.

**Qué has aprendido:** el bloqueo actúa *antes* de tocar el estado y el error te dice quién tiene el candado, desde cuándo y con qué operación. Con un backend remoto el mecanismo es idéntico, pero protege a todo el equipo, no solo a tu máquina.

> ❓ **Preguntas de repaso:**
> 1. **¿Por qué Git no es un backend remoto válido para el estado?** Porque no ofrece bloqueo (dos `apply` simultáneos seguirían pisándose), depende de que las personas recuerden sincronizar, y expondría los datos sensibles del estado en el historial del repositorio.
> 2. **¿Qué hace exactamente el state locking?** Antes de cualquier operación que pueda escribir el estado, Terraform adquiere un candado exclusivo; si ya está cogido, la operación falla al instante en vez de ejecutarse en paralelo y corromper el estado.
> 3. **¿Todos los backends soportan bloqueo?** No. Es una capacidad de cada backend; `s3`, `azurerm`, `gcs` o `remote` la tienen, pero debes verificarlo en la documentación del backend que elijas.

## 8.2 Backend remoto con S3

**¿Qué vas a aprender?** Aquí configurarás tu primer backend remoto real: un bucket de Amazon S3. Verás la sintaxis del bloque `backend "s3"`, cómo `terraform init` migra tu estado local al bucket y, muy importante, las **dos** formas de activar el bloqueo: la clásica con DynamoDB (la que enseña el curso) y la moderna con *lockfile* (fichero de bloqueo) nativo de S3.

### El bloque backend

El backend se declara dentro del bloque `terraform`, junto a `required_providers`. Piensa en ello como cambiar la libreta de la cocina por una **caja fuerte compartida en el banco**: todos los compañeros de piso acceden a la misma, el banco la protege, y solo puede abrirla una persona a la vez.

Los tres argumentos esenciales del backend `s3` son:

- `bucket`: nombre del bucket S3 donde vivirá el estado.
- `key`: ruta (clave del objeto) del fichero de estado dentro del bucket.
- `region`: región AWS del bucket.

```hcl
# main.tf — configuración con backend remoto en S3
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }

  backend "s3" {
    bucket       = "pablo-terraform-estado"    # el bucket debe existir ANTES del init
    key          = "proyectos/web/terraform.tfstate"
    region       = "eu-west-1"
    encrypt      = true                        # cifrado en reposo del objeto de estado
    use_lockfile = true                        # bloqueo nativo de S3 (Terraform >= 1.10)
  }
}
```

Dos detalles importantes. Primero, el clásico problema del huevo y la gallina: **el bucket tiene que existir antes** de ejecutar `terraform init`, así que se crea aparte (consola, AWS CLI o un mini-proyecto Terraform independiente). Segundo, en el bloque `backend` **no puedes usar variables ni referencias**: solo valores literales, porque Terraform lo lee antes de evaluar nada más. Y nunca escribas credenciales AWS dentro del bloque: usa variables de entorno (`AWS_ACCESS_KEY_ID`, etc.), porque lo que pongas ahí acaba copiado en el directorio `.terraform/` en texto plano.

### Migrar el estado con terraform init

Si el proyecto ya tenía estado local, al añadir el bloque backend y ejecutar `terraform init`, Terraform detecta el cambio y **te pregunta si quieres copiar el estado existente al nuevo backend**:

```text
Initializing the backend...
Do you want to copy existing state to the new backend?
  Pre-existing state was found while migrating the previous "local" backend
  to the newly configured "s3" backend. No existing state was found in the
  newly configured "s3" backend. Do you want to copy this state to the new
  "s3" backend? Enter "yes" to copy and "no" to start with an empty state.

  Enter a value: yes

Successfully configured the backend "s3"! Terraform will automatically
use this backend unless the backend configuration changes.
```

Responde `yes`: Terraform sube tu `terraform.tfstate` al bucket y, a partir de ahí, todas las operaciones leen y escriben en S3. El fichero local deja de usarse y puedes borrarlo. En entornos no interactivos (CI/CD) puedes automatizar la respuesta con `terraform init -force-copy`, que contesta `yes` a las preguntas de migración (y activa automáticamente `-migrate-state`, que por sí solo aún puede pedir confirmación interactiva); si lo que quieres es apuntar a un backend nuevo **sin** migrar nada, existe `-reconfigure`.

> 🔄 **Actualización:** el curso enseña el bloqueo del backend S3 con una **tabla de DynamoDB** (argumento `dynamodb_table`, apuntando a una tabla cuya clave de partición debe llamarse `LockID`, de tipo `String`). Esto ha cambiado: **Terraform 1.10** (noviembre de 2024) introdujo de forma experimental el **bloqueo nativo con lockfile en S3** (`use_lockfile = true`), que crea un objeto `.tflock` junto al estado usando escrituras condicionales de S3; en **Terraform 1.11** la función pasó a ser estable y `dynamodb_table` quedó oficialmente **deprecado** (se eliminará en una versión futura). La variante clásica sigue funcionando y ambas pueden coexistir durante una migración gradual:
>
> ```hcl
> backend "s3" {
>   bucket         = "pablo-terraform-estado"
>   key            = "proyectos/web/terraform.tfstate"
>   region         = "eu-west-1"
>   use_lockfile   = true                     # bloqueo moderno (recomendado)
>   dynamodb_table = "terraform-state-lock"   # bloqueo clásico (deprecado)
> }
> ```
>
> Para proyectos nuevos usa solo `use_lockfile = true`: te ahorras crear (y pagar) la tabla DynamoDB. Recuerda los permisos: además de `s3:ListBucket`, `s3:GetObject` y `s3:PutObject` sobre el estado, el lockfile requiere `s3:GetObject`, `s3:PutObject` y `s3:DeleteObject` sobre la ruta `.tflock`.

> ⚠️ **Errores comunes:**
> - **Ejecutar `init` sin que el bucket exista.** Obtendrás un error del backend. Crea el bucket primero y, ya que estás, actívale el versionado.
> - **Usar variables o expresiones en el bloque `backend`.** No está permitido; solo literales. Si necesitas parametrizarlo, usa configuración parcial con `terraform init -backend-config=...`.
> - **Responder `no` a la pregunta de copia por las prisas.** Empezarías con un estado vacío en S3 mientras tus recursos reales siguen registrados en el fichero local: el siguiente `apply` intentaría duplicar toda tu infraestructura.
> - **Dejar el `terraform.tfstate` local rondando tras la migración.** Ya no se usa, pero contiene secretos y confunde. Bórralo (y su `terraform.tfstate.backup`) una vez verificada la migración.

> 💡 **Buenas prácticas:**
> - Activa el **versionado** del bucket: cada escritura del estado queda guardada como versión recuperable, tu seguro de vida ante corrupciones.
> - Añade `encrypt = true` y bloquea el acceso público del bucket; el estado es información sensible.
> - Usa una `key` distinta por proyecto/entorno (`proyectos/web/prod/terraform.tfstate`) para aislar estados en un mismo bucket.
> - En proyectos nuevos con Terraform ≥ 1.11, elige `use_lockfile = true` y olvídate de DynamoDB.

### 🧪 Laboratorio

**Objetivo:** migrar el estado del proyecto del laboratorio anterior a un backend S3 con bloqueo nativo.

1. Crea el bucket para el estado (fuera de Terraform) con versionado activado:

```text
$ aws s3api create-bucket --bucket pablo-terraform-estado \
    --region eu-west-1 \
    --create-bucket-configuration LocationConstraint=eu-west-1
$ aws s3api put-bucket-versioning --bucket pablo-terraform-estado \
    --versioning-configuration Status=Enabled
```

2. En el proyecto `lab-locking` de la lección 8.1 (con su bucket `demo` ya aplicado), añade al bloque `terraform` el backend del ejemplo de arriba (con `use_lockfile = true` y `key = "labs/locking/terraform.tfstate"`).
3. Ejecuta `terraform init` y responde `yes` a la pregunta de copiar el estado. Verifica que el objeto existe:

```text
$ aws s3 ls s3://pablo-terraform-estado/labs/locking/
2026-07-02 11:02:41       4207 terraform.tfstate
```

4. Borra el estado local (`terraform.tfstate` y `terraform.tfstate.backup`) y ejecuta `terraform plan`: debe responder `No changes. Your infrastructure matches the configuration.` — la prueba de que Terraform ya lee de S3.
5. Repite el experimento de las dos terminales de 8.1: verás el mismo `Error acquiring the state lock`, pero esta vez el candado es un objeto `.tflock` en el bucket, visible para todo el equipo.
6. Limpia con `terraform destroy` (el bucket del estado puedes conservarlo para los próximos laboratorios).

> ❓ **Preguntas de repaso:**
> 1. **¿Qué tres argumentos mínimos necesita el backend `s3`?** `bucket` (nombre del bucket), `key` (ruta del fichero de estado dentro del bucket) y `region` (región AWS del bucket).
> 2. **¿Qué ocurre al ejecutar `terraform init` tras añadir un backend a un proyecto con estado local?** Terraform detecta el cambio y pregunta si quieres copiar el estado existente al nuevo backend; respondiendo `yes` lo migra y desde entonces opera contra S3.
> 3. **¿Qué diferencia hay entre `dynamodb_table` y `use_lockfile`?** Ambos activan el bloqueo del estado: el primero usa una tabla DynamoDB externa (método clásico, deprecado desde Terraform 1.11) y el segundo crea un lockfile `.tflock` en el propio bucket S3 mediante escrituras condicionales (nativo desde 1.10, estable en 1.11).

## 8.3 Comandos terraform state

**¿Qué vas a aprender?** Terraform trae una familia de subcomandos para inspeccionar y modificar el estado **sin editarlo a mano jamás**. Aprenderás a listar y examinar recursos (`list`, `show`), a renombrarlos sin destruirlos (`mv`), a sacar recursos de la gestión de Terraform (`rm`) y a descargar o subir el estado completo (`pull`, `push`), con sus riesgos.

### Cirugía sobre el estado, con guantes

Editar `terraform.tfstate` con un editor de texto es como corregir el registro civil con típex: aunque aciertes con el dato, rompes la integridad del documento (números de serie, checksums internos, formato). Los comandos `terraform state` son el procedimiento oficial: cada comando que modifica el estado adquiere el candado, valida lo que haces y **escribe automáticamente un fichero de backup** que no se puede desactivar. Además funcionan igual con backend local o remoto: con S3 descargan, modifican y suben el estado por ti.

| Comando | Qué hace | ¿Modifica el estado? |
|---|---|---|
| `terraform state list` | Lista las direcciones de los recursos del estado | No |
| `terraform state show DIRECCIÓN` | Muestra los atributos de un recurso | No |
| `terraform state mv ORIGEN DESTINO` | Mueve/renombra un recurso dentro del estado | Sí |
| `terraform state rm DIRECCIÓN` | "Olvida" un recurso (no lo destruye) | Sí |
| `terraform state pull` | Descarga el estado y lo imprime por stdout | No |
| `terraform state push FICHERO` | Sobrescribe el estado remoto con un fichero local | Sí (¡peligro!) |

**`terraform state list`** lista las direcciones de todos los recursos (o de los que coincidan con un filtro). Es tu mapa rápido del proyecto:

```text
$ terraform state list
aws_s3_bucket.demo
aws_s3_object.config
```

**`terraform state show DIRECCIÓN`** muestra todos los atributos de **un** recurso tal y como están registrados, incluidos los que calcula el proveedor (IDs, ARNs...). Su salida es para humanos; para procesarla con scripts usa `terraform show -json`.

```text
$ terraform state show aws_s3_object.config
# aws_s3_object.config:
resource "aws_s3_object" "config" {
    bucket       = "pablo-lab-locking-2026"
    content_type = "application/json"
    etag         = "9a0364b9e99bb480dd25e1f0284c8555"
    id           = "app/config.json"
    key          = "app/config.json"
    ...
}
```

**`terraform state mv ORIGEN DESTINO`** cambia la dirección con la que el estado identifica un objeto real. Su caso de uso estrella: **renombrar un recurso en la configuración sin destruirlo y recrearlo**. Si renombras el bloque en el `.tf` sin tocar el estado, Terraform cree que has borrado un recurso y creado otro (plan: `1 to add, 1 to destroy`). Con `state mv` le explicas que es el mismo objeto con otro nombre. También sirve para mover recursos dentro de un módulo (`terraform state mv aws_instance.web module.web.aws_instance.web`). Origen y destino deben ser del mismo tipo de objeto.

**`terraform state rm DIRECCIÓN`** hace que Terraform "olvide" un recurso: **el objeto real sigue existiendo** en AWS, pero deja de estar gestionado. Úsalo cuando quieras transferir un recurso a otro proyecto/equipo o gestionarlo a mano. Cuidado: si el recurso sigue declarado en tu `.tf`, el siguiente `plan` propondrá crearlo de nuevo. Ambos comandos aceptan `-dry-run` para ensayar sin tocar nada.

**`terraform state pull`** descarga el estado del backend y lo vuelca por la salida estándar: perfecto para inspeccionarlo (`terraform state pull | jq .serial`) o guardar una copia puntual antes de una operación delicada.

**`terraform state push FICHERO`** es el inverso y el más peligroso de todos: sobrescribe el estado remoto con un fichero local. Solo tiene sentido en recuperaciones manuales muy concretas. Terraform aplica dos comprobaciones de seguridad: rechaza el push si el **lineage** difiere (serían estados de proyectos distintos) o si el **serial** del destino es mayor (el remoto tiene datos más recientes). El flag `-force` desactiva ambas; si lo usas mal, machacas el estado del equipo. Trátalo como el botón rojo: saber que existe, no usarlo casi nunca.

> 🔄 **Actualización:** cuando se grabó el curso, `state mv` y `state rm` eran la única opción. El Terraform moderno ofrece alternativas declarativas y revisables: los bloques **`moved`** (desde 1.1) para renombrados/refactorizaciones y los bloques **`removed`** (desde 1.7) para sacar recursos del estado sin destruirlos. Se escriben en la configuración y el cambio se aplica en el `plan`/`apply` normal, con lo que todo el equipo lo revisa como cualquier otro cambio. La documentación oficial recomienda `removed` frente a `terraform state rm` siempre que sea posible. Los comandos siguen siendo válidos y es imprescindible conocerlos, sobre todo para operaciones puntuales e interactivas.

> ⚠️ **Errores comunes:**
> - **Editar el `.tfstate` a mano.** Nunca. Siempre a través de `terraform state` (o bloques `moved`/`removed`), que validan, bloquean y hacen backup.
> - **Renombrar el recurso en el `.tf` y olvidar el `state mv` (o al revés).** Ambos cambios van en pareja; si haces solo uno, el `plan` te propondrá destruir y recrear.
> - **Creer que `state rm` destruye el recurso.** No: solo lo saca del estado. Y si sigue en la configuración, Terraform intentará crearlo otra vez, lo que puede provocar errores de duplicado o recursos clonados.
> - **Usar `state push -force` sin entender lineage y serial.** Puedes sobrescribir el trabajo reciente de todo el equipo con un estado obsoleto.

> 💡 **Buenas prácticas:**
> - Antes de cualquier `mv`/`rm`, guarda una copia con `terraform state pull > respaldo-$(date +%F).tfstate` y ensaya con `-dry-run`.
> - Termina siempre con `terraform plan`: la operación ha ido bien cuando el plan dice `No changes`.
> - Entrecomilla las direcciones con índices (`'aws_instance.web[0]'`) para que la shell no interprete los corchetes.
> - En cambios que va a revisar el equipo, prefiere bloques `moved`/`removed` en el código antes que comandos ejecutados a mano.

### 🧪 Laboratorio

**Objetivo:** renombrar un recurso sin recrearlo y sacar otro de la gestión de Terraform, sobre el proyecto con backend S3 de 8.2.

1. Añade al proyecto un objeto S3 y aplica:

```hcl
# Objeto de configuración dentro del bucket demo
resource "aws_s3_object" "config" {
  bucket       = aws_s3_bucket.demo.id
  key          = "app/config.json"
  content      = jsonencode({ entorno = "lab" })
  content_type = "application/json"
}
```

2. Inspecciona el estado: `terraform state list` (verás `aws_s3_bucket.demo` y `aws_s3_object.config`) y `terraform state show aws_s3_object.config`.
3. **Renombrado sin recreación.** Renombra el recurso en el estado y luego en el código:

```text
$ terraform state mv aws_s3_object.config aws_s3_object.app_config
Move "aws_s3_object.config" to "aws_s3_object.app_config"
Successfully moved 1 object(s).
```

Cambia en `main.tf` `resource "aws_s3_object" "config"` por `"app_config"` y ejecuta `terraform plan`. Resultado esperado: `No changes.` Has renombrado sin destruir nada. (Prueba a hacerlo al revés en otro proyecto: solo el cambio en el `.tf` produce `Plan: 1 to add, 1 to destroy`.)

4. **Olvidar un recurso.** Saca el objeto de la gestión:

```text
$ terraform state rm aws_s3_object.app_config
Removed aws_s3_object.app_config
Successfully removed 1 resource instance(s).
```

El objeto **sigue en S3** (compruébalo: `aws s3 ls s3://pablo-lab-locking-2026/app/`), pero `terraform state list` ya no lo muestra.
5. Ejecuta `terraform plan`: como el bloque sigue en la configuración, propone `1 to add`. Aplica y observa que Terraform vuelve a "adoptarlo" creándolo de nuevo (en un objeto S3 es una sobreescritura inofensiva; con una base de datos habría sido un drama, de ahí las advertencias).
6. Guarda una copia del estado con `terraform state pull > copia.tfstate`, ábrela para curiosear los campos `lineage` y `serial`, y bórrala después (contiene datos sensibles). Termina con `terraform destroy`.

> ❓ **Preguntas de repaso:**
> 1. **¿Qué comando usarías para renombrar `aws_instance.web` a `aws_instance.frontend` sin recrear la máquina?** `terraform state mv aws_instance.web aws_instance.frontend`, acompañado del renombrado del bloque en la configuración (o, de forma declarativa, un bloque `moved`).
> 2. **¿`terraform state rm` destruye el recurso?** No. Solo elimina su registro del estado: el objeto real sigue existiendo, pero Terraform deja de gestionarlo. Si permanece declarado en la configuración, el siguiente plan intentará crearlo de nuevo.
> 3. **¿Qué dos comprobaciones hace `terraform state push` antes de sobrescribir el estado remoto?** Que el `lineage` coincida (que sea el mismo linaje de estado y no uno de otro proyecto) y que el `serial` del fichero subido no sea inferior al del destino (que no pises datos más recientes). `-force` las desactiva y por eso es tan peligroso.

---

📌 **Resumen del módulo:** el estado local no escala a equipos: se desincroniza y se corrompe con operaciones simultáneas. Un backend remoto como `s3` centraliza el estado (`bucket`, `key`, `region`) y el *state locking* serializa las operaciones — hoy con `use_lockfile = true` nativo de S3, ayer con DynamoDB. Y cuando necesites tocar el estado, nada de editor de texto: `terraform state list/show/mv/pull/rm` (y `push` solo en emergencias) son tus herramientas quirúrgicas. En el próximo módulo seguirás profundizando en el trabajo con AWS.
