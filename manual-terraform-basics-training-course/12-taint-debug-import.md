# Módulo 10 · Taint, debugging e import

Hasta ahora has creado infraestructura desde cero y la has gestionado con `plan` y `apply`. En este módulo aprenderás tres habilidades de "mantenimiento" que todo practicante de Terraform necesita: forzar la recreación de un recurso que se ha quedado en mal estado, activar los logs internos de Terraform para diagnosticar problemas, y adoptar bajo gestión de Terraform recursos que se crearon a mano.

## 10.1 terraform taint: forzar la recreación de un recurso

**¿Qué vas a aprender?** En esta lección verás qué significa que un recurso esté *tainted* (marcado como "contaminado" o defectuoso), cómo Terraform aplica esa marca automáticamente cuando falla un provisioner, y cómo forzar tú mismo la recreación de un recurso. También verás por qué el comando `terraform taint` está deprecado y cuál es la forma moderna de hacer lo mismo.

### El problema: un recurso "vivo pero enfermo"

Terraform compara tu configuración con el estado. Si ambos coinciden, `terraform plan` dice "sin cambios"... aunque el recurso real esté hecho polvo por dentro. Imagina una máquina virtual en la que alguien ha borrado ficheros a mano, o un servidor cuyo script de arranque falló a medias: para Terraform todo cuadra sobre el papel, pero tú sabes que ese recurso necesita nacer de nuevo.

Piensa en la pegatina de "AVERIADO" que pegan en una máquina de vending: la máquina sigue ahí, enchufada y con luces, pero la pegatina avisa al técnico de que en su próxima ronda debe sustituirla. Eso es exactamente *taint*: una **marca en el estado** que le dice a Terraform "este objeto está degradado; en el próximo `apply`, destrúyelo y créalo de nuevo". No modifica nada en el momento: solo deja la marca.

Terraform también pone esa pegatina **automáticamente**: si un provisioner de creación falla a mitad (lo viste en el módulo de provisioners), el recurso puede quedar a medio configurar, así que Terraform lo marca como tainted para destruirlo y recrearlo en el siguiente `apply`. Si estás seguro de que el recurso está bien pese al fallo, puedes retirar la marca con `terraform untaint direccion.recurso`.

### Ejemplo práctico en local

Prepara este proyecto (solo necesita los providers `random` y `local`, sin cuenta cloud):

```hcl
# main.tf — un "servidor" simulado y su fichero de configuración
terraform {
  required_providers {
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
    local = {
      source  = "hashicorp/local"
      version = "~> 2.5"
    }
  }
}

# Genera un nombre aleatorio, p. ej. "neat-koala"
resource "random_pet" "servidor" {
  length = 2
}

# Fichero que DEPENDE del nombre: si el nombre cambia, el fichero cambia
resource "local_file" "config" {
  filename = "${path.module}/config.txt"
  content  = "hostname=${random_pet.servidor.id}\n"
}
```

Tras `terraform init` y `terraform apply`, marca el recurso y observa el plan:

```text
$ terraform taint random_pet.servidor
Resource instance random_pet.servidor has been marked as tainted.

$ terraform plan
random_pet.servidor: Refreshing state... [id=neat-koala]
local_file.config: Refreshing state... [id=8b5f2a...]

Terraform will perform the following actions:

  # random_pet.servidor is tainted, so must be replaced
-/+ resource "random_pet" "servidor" {
      ~ id     = "neat-koala" -> (known after apply)
        length = 2
        # (2 unchanged attributes hidden)
    }

  # local_file.config must be replaced
-/+ resource "local_file" "config" {
      ~ content  = "hostname=neat-koala\n" -> (known after apply)
        ...
    }

Plan: 2 to add, 0 to change, 2 to destroy.
```

Fíjate en dos cosas: el símbolo `-/+` (destruir y crear el reemplazo) y el **efecto cascada**: como `local_file.config` usa el `id` del nombre, también se reemplaza. Marcar un recurso puede arrastrar a sus dependientes.

> 🔄 **Actualización:** el comando `terraform taint` está **deprecado desde Terraform 0.15.2**. La forma recomendada hoy es planificar el reemplazo directamente: `terraform apply -replace="random_pet.servidor"` (también funciona con `terraform plan -replace=...` para revisarlo antes). La diferencia es importante: `-replace` te enseña el impacto completo en un plan **antes** de tocar nada, mientras que `taint` modifica el estado al instante, y un compañero podría lanzar un plan contra ese objeto marcado antes de que tú revises las consecuencias. En el plan verás la anotación `# random_pet.servidor will be replaced, as requested`. El comando `terraform untaint` sigue vigente para retirar marcas automáticas (por ejemplo, tras un provisioner fallido).

> ⚠️ **Errores comunes:**
> - Usar `taint` (o `-replace`) para "arreglar" un recurso que en realidad tiene mal la configuración: recrearás el problema idéntico. Primero corrige el `.tf`; recrea solo si el recurso está degradado de verdad.
> - Olvidar el efecto cascada: reemplazar un recurso base (una red, un nombre) puede forzar el reemplazo de todo lo que depende de él. Lee el `Plan: X to add, Y to destroy` antes de confirmar.
> - Escribir mal la dirección del recurso: es `tipo.nombre` (p. ej. `random_pet.servidor`), y con `count`/`for_each` necesitas el índice: `-replace="aws_instance.web[0]"`.
> - Pensar que `taint` destruye el recurso en el acto: no, solo lo marca; la destrucción ocurre en el siguiente `apply`.

> 💡 **Buenas prácticas:**
> - Prefiere siempre `terraform apply -replace="..."`: todo pasa por un plan revisable y no dejas estado "envenenado" a medias para el resto del equipo.
> - Antes de forzar un reemplazo, ejecuta `terraform plan -replace="..."` y guarda la salida como evidencia de lo que va a pasar.
> - Si Terraform marcó algo como tainted por un fallo transitorio (red, timeout) y verificaste a mano que el recurso está sano, usa `terraform untaint` en lugar de recrear por recrear.

### 🧪 Laboratorio

**Enunciado:** con el proyecto `random_pet` + `local_file` de arriba: (1) aplica la configuración; (2) simula que el "servidor" está degradado y fuérzalo a recrearse con el método moderno; (3) comprueba que el nombre y el fichero han cambiado; (4) marca el recurso con el comando clásico `taint`, arrepiéntete y retira la marca.

**Solución:**

1. `terraform init && terraform apply -auto-approve`. Anota el nombre: `terraform state show random_pet.servidor`.
2. `terraform apply -replace="random_pet.servidor"`. El plan mostrará `will be replaced, as requested` y `Plan: 2 to add, 0 to change, 2 to destroy`. Confirma con `yes`.
3. Abre `config.txt`: el `hostname=` tiene un nombre nuevo. El reemplazo arrastró al fichero.
4. `terraform taint random_pet.servidor` → mensaje `...has been marked as tainted`. Ahora `terraform untaint random_pet.servidor` → `...has been successfully untainted`. Un `terraform plan` final debe decir `No changes`.

> ❓ **Preguntas de repaso:**
> 1. **¿Qué hace exactamente `terraform taint`?** Marca un objeto en el estado como tainted; en el siguiente plan/apply, Terraform propondrá destruirlo y recrearlo. No toca la infraestructura en el momento.
> 2. **¿Cuándo marca Terraform un recurso como tainted sin que tú hagas nada?** Cuando falla una acción de creación en varios pasos, típicamente un provisioner de creación (salvo que uses `on_failure = continue`).
> 3. **¿Por qué es preferible `-replace` a `taint`?** Porque el reemplazo se decide dentro de un plan que revisas antes de aplicar, mientras que `taint` altera el estado inmediatamente y otro usuario podría planificar contra ese objeto antes de que revises el efecto.

## 10.2 Debugging: los logs de Terraform

**¿Qué vas a aprender?** Cuando Terraform falla con un mensaje críptico, necesitas ver qué está pasando por dentro. Aquí aprenderás a activar los logs internos con la variable de entorno `TF_LOG`, a elegir el nivel de detalle adecuado, a guardarlos en un fichero con `TF_LOG_PATH` y a separar los logs del núcleo de los del provider.

### La caja negra de Terraform

Terraform lleva una "caja negra" como la de los aviones: registra todo lo que hace (qué providers arranca, qué peticiones API envía, qué respuestas recibe), pero por defecto no te lo enseña. La variable de entorno `TF_LOG` es el dial que sube el volumen de esa grabación: basta con darle **cualquier valor** para activar los logs detallados, que se escriben por `stderr`. Los niveles válidos, de más a menos ruidoso, son:

| Nivel | Qué obtienes |
|---|---|
| `TRACE` | Absolutamente todo, línea a línea (el más verboso y el más útil para bugs raros) |
| `DEBUG` | Detalle técnico abundante sin llegar al extremo |
| `INFO` | Hitos generales de la ejecución |
| `WARN` | Solo advertencias |
| `ERROR` | Solo errores |

Además, `TF_LOG=JSON` activa el nivel TRACE con salida en formato JSON (fácil de analizar con herramientas automáticas), útil si quieres procesar los logs de forma programática.

Cómo activarlo (en tu Windows con PowerShell y su equivalente en Bash):

```powershell
# PowerShell (Windows) — vale para la sesión actual
$env:TF_LOG = "DEBUG"
$env:TF_LOG_PATH = "terraform.log"   # persistir a fichero
terraform plan
# Para desactivar:
Remove-Item Env:TF_LOG; Remove-Item Env:TF_LOG_PATH
```

```bash
# Bash (Linux/macOS/Git Bash)
export TF_LOG=DEBUG
export TF_LOG_PATH=terraform.log
terraform plan
unset TF_LOG TF_LOG_PATH
```

Dos detalles que la documentación oficial deja claros y que conviene grabarse:

- `TF_LOG_PATH` **solo funciona si `TF_LOG` también está definida**. Poner la ruta sin nivel no registra nada.
- Puedes afinar el foco con `TF_LOG_CORE=nivel` (solo el núcleo de Terraform: grafo, estado, planificación) y `TF_LOG_PROVIDER=nivel` (solo los plugins de provider: llamadas a las API). Aceptan los mismos niveles que `TF_LOG` pero activan solo ese subconjunto. Si sospechas del provider AWS, `TF_LOG_PROVIDER=TRACE` te da su conversación completa sin ahogarte en el ruido del núcleo.

### Cómo leer un log sin ahogarse

Un fragmento típico de `terraform.log` tiene esta pinta:

```text
2026-07-02T10:14:03.512+0200 [INFO]  Terraform version: 1.9.5
2026-07-02T10:14:03.514+0200 [INFO]  CLI args: []string{"terraform", "plan"}
2026-07-02T10:14:03.812+0200 [DEBUG] provider: starting plugin: path=.terraform/providers/registry.terraform.io/hashicorp/random/3.6.2/...
2026-07-02T10:14:04.021+0200 [TRACE] provider.terraform-provider-random: Received request: tf_rpc=PlanResourceChange
2026-07-02T10:14:04.145+0200 [ERROR] provider.terraform-provider-random: Response contains error diagnostic: ...
```

La estrategia es siempre la misma: no leas de arriba abajo. **Busca `[ERROR]`** (con `Select-String "ERROR" terraform.log` en PowerShell o `grep ERROR terraform.log`) y luego lee hacia arriba unas cuantas líneas para ver qué petición lo provocó. Las marcas de tiempo te ayudan a correlacionar, y el prefijo (`provider.terraform-provider-x` frente a líneas sin prefijo de provider) te dice si el problema vive en el plugin o en el núcleo.

> ⚠️ **Errores comunes:**
> - Definir `TF_LOG_PATH` sin `TF_LOG` y concluir que "los logs no funcionan": recuerda que el nivel es obligatorio.
> - Dejar `TF_LOG=TRACE` activado permanentemente: todo se vuelve lentísimo de leer y cualquier salida útil queda enterrada. Actívalo, reproduce el fallo, desactívalo.
> - Compartir un log en un ticket o en un chat sin revisarlo: en niveles TRACE/DEBUG pueden aparecer datos sensibles de tus recursos. Límpialo antes.
> - En PowerShell, usar `export TF_LOG=...` (sintaxis de Bash): no da error visible en algunos contextos, pero no define nada. Es `$env:TF_LOG = "..."`.

> 💡 **Buenas prácticas:**
> - Empieza por `DEBUG` y sube a `TRACE` solo si no ves la causa: TRACE multiplica el tamaño del log.
> - Usa `TF_LOG_PROVIDER` cuando el error huela a API del proveedor (403, throttling, campos rechazados) y `TF_LOG_CORE` cuando huela a grafo, estado o dependencias.
> - Guarda siempre a fichero con `TF_LOG_PATH` en sesiones largas: `stderr` mezcla el log con la salida normal y es fácil perder líneas.

### 🧪 Laboratorio

**Enunciado:** con el proyecto de la lección 10.1: (1) ejecuta un `plan` con nivel `TRACE` guardando el log en `depuracion.log`; (2) localiza en el log la versión de Terraform y la línea donde arranca el plugin del provider `random`; (3) repite con `TF_LOG_PROVIDER=DEBUG` (sin `TF_LOG_CORE`) y compara el tamaño; (4) desactívalo todo.

**Solución (PowerShell):**

1. `$env:TF_LOG = "TRACE"; $env:TF_LOG_PATH = "depuracion.log"; terraform plan`
2. `Select-String "Terraform version" depuracion.log` → línea `[INFO] Terraform version: ...`. Después `Select-String "starting plugin" depuracion.log` → verás la ruta del binario de `terraform-provider-random` bajo `.terraform/providers/`.
3. Para centrarte en el provider, borra el log anterior (`Remove-Item depuracion.log`), añade `$env:TF_LOG_PROVIDER = "DEBUG"` y baja el ruido del núcleo con `$env:TF_LOG_CORE = "ERROR"` (mantén `TF_LOG` definida: sin ella no se escribe nada en `TF_LOG_PATH`). Ejecuta `terraform plan` de nuevo y compara tamaños con `(Get-Content depuracion.log).Count`: verás muchas menos líneas, casi todas con el prefijo del provider.
4. `Remove-Item Env:TF_LOG, Env:TF_LOG_PATH, Env:TF_LOG_PROVIDER, Env:TF_LOG_CORE -ErrorAction SilentlyContinue`

> ❓ **Preguntas de repaso:**
> 1. **¿Qué niveles acepta `TF_LOG` y cuál es el más detallado?** `TRACE`, `DEBUG`, `INFO`, `WARN` y `ERROR`; el más detallado es `TRACE` (y `JSON` emite ese mismo nivel en formato JSON).
> 2. **¿Sirve de algo `TF_LOG_PATH` por sí sola?** No: sin `TF_LOG` definida no se activa ningún log, así que el fichero ni se crea.
> 3. **¿Cómo verías solo lo que hace el provider, sin el ruido del núcleo?** Con `TF_LOG_PROVIDER=TRACE` (o `DEBUG`), que activa únicamente el subconjunto de logs de los plugins de provider.

## 10.3 terraform import: adoptar recursos existentes

**¿Qué vas a aprender?** En el mundo real casi nadie parte de cero: hay recursos creados a mano desde la consola web ("ClickOps") que Terraform no conoce. Aquí aprenderás el flujo clásico de `terraform import` (escribir el bloque, importar por ID, iterar con `plan` hasta que cuadre) con un ejemplo real de una instancia EC2, y el flujo moderno con bloques `import` declarativos y generación automática de configuración.

### Adoptar, no crear

Importar es como adoptar un gato callejero: el gato ya existe y se las apaña solo; lo que haces es llevarlo al veterinario, ponerle el chip y darlo de alta en el registro. A partir de ahí, es *tu* gato y tú respondes por él. `terraform import` no crea ni modifica infraestructura: **solo escribe en el estado** la ficha del recurso real, asociándola a una dirección de tu configuración. Y ojo con la letra pequeña de la adopción: una vez dentro del estado, un `terraform destroy` (o un `apply` desafortunado) también lo destruye a él.

El comando clásico tiene esta forma: `terraform import [opciones] DIRECCION ID`, donde `DIRECCION` es la dirección del recurso en tu configuración (`aws_instance.webserver`) e `ID` es el identificador que usa el proveedor real (el ID de instancia en EC2, el nombre del bucket en S3...). Cada tipo de recurso documenta en el Registry qué ID espera.

### Ejemplo completo: importar una instancia EC2 creada a mano

Supón que un compañero creó desde la consola de AWS una instancia `t3.micro` llamada `webserver-manual`, con ID `i-0a1b2c3d4e5f67890`. Vamos a adoptarla.

**Paso 1 — Escribe primero el bloque `resource`.** El comando importa *hacia* una dirección de tu configuración, así que esa dirección debe existir. Si la omites, Terraform te frena con un error explícito:

```text
$ terraform import aws_instance.webserver i-0a1b2c3d4e5f67890
Error: resource address "aws_instance.webserver" does not exist in the configuration.

Before importing this resource, please create its configuration in main.tf. For example:

resource "aws_instance" "webserver" {
  # (resource arguments)
}
```

Crea el bloque, de momento casi vacío (aún no sabemos sus atributos exactos):

```hcl
# main.tf
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "eu-west-1" # la región donde vive la instancia
}

# Cascarón vacío: lo rellenaremos con los datos reales tras importar
resource "aws_instance" "webserver" {
}
```

**Paso 2 — Importa con el ID real:**

```text
$ terraform import aws_instance.webserver i-0a1b2c3d4e5f67890
aws_instance.webserver: Importing from ID "i-0a1b2c3d4e5f67890"...
aws_instance.webserver: Import prepared!
  Prepared aws_instance for import
aws_instance.webserver: Refreshing state... [id=i-0a1b2c3d4e5f67890]

Import successful!

The resources that were imported are shown above. These resources are now in
your Terraform state and will henceforth be managed by Terraform.
```

**Paso 3 — Rellena la configuración hasta que el plan cuadre.** El recurso ya está en el estado, pero tu bloque está vacío: `terraform plan` mostrará diferencias. Inspecciona la ficha real con `terraform state show aws_instance.webserver` y copia a tu `.tf` los argumentos relevantes:

```hcl
resource "aws_instance" "webserver" {
  ami           = "ami-0c1234567890abcde" # cópialo del state show
  instance_type = "t3.micro"
  key_name      = "clave-web"

  tags = {
    Name = "webserver-manual"
  }
}
```

Repite `terraform plan` y ajusta hasta ver el mensaje mágico:

```text
No changes. Your infrastructure matches the configuration.
```

Ese bucle plan → ajustar → plan es la parte artesanal del import clásico: hasta que no cuadre, no has terminado.

> 🔄 **Actualización:** desde **Terraform 1.5** existe una alternativa declarativa: los **bloques `import`**. En lugar de un comando imperativo, describes la importación en el propio código y ocurre durante el `apply`, dentro del flujo normal plan → apply (el `id` debe conocerse en tiempo de plan):
>
> ```hcl
> import {
>   to = aws_instance.webserver          # dirección de destino
>   id = "i-0a1b2c3d4e5f67890"           # ID real en AWS
> }
> ```
>
> Y lo mejor: puedes pedir a Terraform que **genere el bloque `resource` por ti** con `terraform plan -generate-config-out="generated.tf"` (la ruta debe ser un fichero nuevo; si existe, Terraform da error). Revisa el fichero generado, ajústalo y aplica. La generación de configuración se introdujo en 1.5 como funcionalidad experimental, así que revisa siempre el resultado antes de aplicar. Este flujo es reproducible y automatizable en CI/CD, cosa imposible con el comando imperativo.

> ⚠️ **Errores comunes:**
> - Ejecutar `terraform import` sin haber escrito el bloque `resource`: error inmediato de "resource address does not exist in the configuration".
> - Dar por terminado el import sin llegar a "No changes": si el plan aún propone cambios, el próximo `apply` modificará (¡o reemplazará!) el recurso real. Un `ami` mal copiado, por ejemplo, fuerza el reemplazo de la instancia.
> - Equivocarse de ID o de tipo de identificador: cada recurso espera el suyo (ID de instancia para `aws_instance`, nombre para `aws_s3_bucket`...). Consulta la sección *Import* de la doc del recurso en el Registry.
> - Olvidar que el recurso importado se puede destruir: tras importar, `terraform destroy` se lo lleva por delante como a cualquier otro.

> 💡 **Buenas prácticas:**
> - En Terraform ≥ 1.5, prefiere bloques `import` + `-generate-config-out`: dejan rastro en el código, pasan por revisión y funcionan en pipelines.
> - Importa de uno en uno y valida con `plan` entre importaciones; adoptar veinte recursos a la vez sin cuadrar ninguno es una receta para el desastre.
> - Tras cuadrar el plan, borra los bloques `import` ya consumidos (o consérvalos si documentan la migración: son inofensivos una vez importado).
> - Haz una copia del fichero de estado antes de una sesión de importaciones grande: es tu red de seguridad.

### 🧪 Laboratorio

**Enunciado (100 % local, sin cuenta cloud):** un proyecto antiguo generó un identificador aleatorio cuyo valor en formato `b64_url` es `p-9hUg`, y te piden adoptarlo en tu nuevo proyecto Terraform. El recurso `random_id` admite importación usando precisamente ese valor como ID. (1) Crea un proyecto nuevo con el provider `random`; (2) decláralo con un bloque `import`; (3) genera la configuración automáticamente; (4) aplica y verifica que el plan queda limpio.

**Solución:**

1. En una carpeta vacía, crea `main.tf`:

```hcl
terraform {
  required_providers {
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}

# Declaramos la adopción: aún NO existe el bloque resource
import {
  to = random_id.heredado
  id = "p-9hUg" # valor b64_url del identificador existente
}
```

2. `terraform init` y después `terraform plan -generate-config-out="generated.tf"`:

```text
Terraform will perform the following actions:

  # random_id.heredado will be imported
    resource "random_id" "heredado" {
        b64_std     = "p+9hUg=="
        b64_url     = "p-9hUg"
        byte_length = 4
        dec         = "2817483090"
        hex         = "a7ef6152"
        id          = "p-9hUg"
    }

Plan: 1 to import, 0 to add, 0 to change, 0 to destroy.
```

3. Abre `generated.tf`: contiene el bloque `resource "random_id" "heredado"` con `byte_length = 4` (Terraform lo dedujo de los 4 bytes del valor). Revísalo: es tu código a partir de ahora.
4. `terraform apply` → `Apply complete! Resources: 1 imported, 0 added, 0 changed, 0 destroyed.` Verifica con `terraform state show random_id.heredado` y confirma que `terraform plan` responde `No changes`. Como alternativa clásica, podrías haber escrito tú el bloque con `byte_length = 4` y ejecutar `terraform import random_id.heredado p-9hUg`: el resultado en el estado es el mismo.

> ❓ **Preguntas de repaso:**
> 1. **¿`terraform import` crea el recurso en el proveedor?** No: el recurso ya existe; el comando solo registra su ficha en el estado de Terraform y la asocia a una dirección de tu configuración.
> 2. **¿Qué hay que hacer antes de ejecutar el comando `terraform import` clásico?** Escribir el bloque `resource` de destino en la configuración (aunque esté vacío); si no existe, el comando falla.
> 3. **¿Qué aportan los bloques `import` de Terraform 1.5 frente al comando?** Son declarativos (viven en el código y se ejecutan en el flujo plan → apply), automatizables en CI/CD, y permiten generar la configuración del recurso con `terraform plan -generate-config-out="fichero.tf"`.
