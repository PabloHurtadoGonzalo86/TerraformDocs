# Módulo 4 · Fundamentos de Terraform

**Parte 1: providers y configuración.** En este módulo entramos en el motor de Terraform: entenderás qué es exactamente un provider, cómo `terraform init` lo descarga e instala, cómo se organiza un directorio de configuración y cómo combinar varios providers en un mismo proyecto. Todo lo que hagas aquí se practica **en local**, sin cuenta en ninguna nube: solo necesitas Terraform instalado y una terminal.

## 4.1 Providers de Terraform

**¿Qué vas a aprender?** En esta lección descubrirás qué es un provider (el plugin que conecta Terraform con cada plataforma), qué papel juega el Terraform Registry y qué hace exactamente `terraform init` entre bambalinas: dónde descarga los plugins, cómo se identifican con su dirección `hashicorp/local` y cómo se controla su versión.

### Terraform core y los plugins

El binario `terraform` que instalaste (el *core*) es sorprendentemente "tonto" a propósito: sabe leer HCL, construir el grafo de dependencias, gestionar el estado y calcular planes… pero **no sabe hablar con ninguna plataforma**. No sabe crear una máquina en AWS, ni un fichero en tu disco, ni un repositorio en GitHub.

De eso se encargan los **providers**: plugins (binarios independientes) que traducen los recursos que declaras en HCL a llamadas a la API de cada plataforma. Piensa en Terraform como un **mando a distancia universal**: el mando (el core) tiene los botones y la lógica, pero para controlar cada aparato —la tele, el aire acondicionado, la barra de sonido— necesita cargar el "perfil" de ese fabricante. Cada perfil es un provider: `aws` para Amazon, `azurerm` para Azure, `local` para ficheros de tu disco, `random` para generar valores aleatorios.

Los providers se distribuyen a través del **Terraform Registry** ([registry.terraform.io](https://registry.terraform.io)), el catálogo público donde hay miles de ellos. Cada provider documenta ahí sus recursos y argumentos: esa documentación será tu mejor amiga a partir de ahora.

En el Registry, los providers se clasifican por niveles según quién los mantiene:

| Nivel | ¿Quién lo mantiene? | Ejemplos |
|---|---|---|
| **Official** | HashiCorp directamente | `hashicorp/aws`, `hashicorp/local`, `hashicorp/random` |
| **Partner** | Empresas del programa de partners de HashiCorp, sobre sus propias APIs | los providers de Datadog, MongoDB Atlas… |
| **Community** | Personas u organizaciones de la comunidad | publicados bajo cuentas personales |

> 🔄 **Actualización:** cuando se grabó el curso (Terraform 0.13–1.x), al nivel intermedio se le llamaba *verified*. Hoy la documentación oficial habla de *partner* y añade dos niveles más: **Partner Premier** (partners que cumplen requisitos adicionales) y **Archived** (providers *official* o *partner* que ya no se mantienen).

### Qué hace exactamente `terraform init`

Cuando escribes tu primera configuración y ejecutas `terraform init`, el comando hace tres cosas: inicializa el *backend* (donde se guardará el estado), instala los módulos hijos si los hay, y —lo que nos interesa ahora— **descarga e instala los plugins de los providers** que tu configuración necesita.

Vamos a verlo con un ejemplo mínimo. Crea un directorio vacío con este fichero:

```hcl
# main.tf

terraform {
  required_providers {
    local = {
      # Dirección del provider en el Registry: NAMESPACE/TIPO
      source  = "hashicorp/local"
      # Acepta 2.5, 2.6, 2.7… pero nunca saltará a 3.0
      version = "~> 2.5"
    }
  }
}

# Un recurso del provider local: crea un fichero en tu disco
resource "local_file" "saludo" {
  filename = "${path.module}/saludo.txt"
  content  = "¡Hola, Pablo! Este fichero lo ha creado Terraform.\n"
}
```

Al ejecutar `terraform init` verás algo así:

```text
$ terraform init

Initializing the backend...
Initializing provider plugins...
- Finding hashicorp/local versions matching "~> 2.5"...
- Installing hashicorp/local v2.9.0...
- Installed hashicorp/local v2.9.0 (signed by HashiCorp)

Terraform has created a lock file .terraform.lock.hcl to record the provider
selections it made above. Include this file in your version control repository
so that Terraform can guarantee to make the same selections by default when
you run "terraform init" in the future.

Terraform has been successfully initialized!
```

Terraform ha descargado el plugin dentro de un directorio oculto `.terraform` en tu directorio de trabajo. Su estructura refleja la dirección completa del provider:

```text
.terraform/
└── providers/
    └── registry.terraform.io/          # hostname del registro
        └── hashicorp/                  # namespace (organización)
            └── local/                  # tipo de provider
                └── 2.9.0/              # versión instalada
                    └── windows_amd64/  # tu sistema operativo y arquitectura
                        └── terraform-provider-local_v2.9.0_x5.exe
```

Fíjate en la **dirección del provider**: su formato completo es `[hostname/]namespace/tipo`. Si escribes `hashicorp/local`, Terraform lo expande a `registry.terraform.io/hashicorp/local`, porque el registro público es el hostname por defecto. El *namespace* identifica a la organización que lo publica y el *tipo* a la plataforma. Si en tu configuración escribes un recurso de un provider que no has declarado en `required_providers`, Terraform asume la dirección implícita `hashicorp/<nombre>`; funciona con los providers oficiales, pero es mejor declararlo siempre de forma explícita.

### Versionado de plugins

El argumento `version` acepta operadores de restricción: `>= 1.0` (mínimo), `~> 2.5` (permite incrementar solo el componente más a la derecha: 2.5, 2.6, 2.7… pero no 3.0; si quieres limitarte a parches de 2.5, usa `~> 2.5.0`). Si lo omites, `init` instala la versión más reciente disponible, lo que puede romper tu configuración el día que el provider publique un cambio incompatible. Además, `init` genera el fichero **`.terraform.lock.hcl`** (el *lock file* o fichero de bloqueo), que registra exactamente qué versión se seleccionó (con sus sumas de verificación) para que todo tu equipo use la misma. Para actualizar a versiones más nuevas dentro de tus restricciones, usa `terraform init -upgrade`.

> ⚠️ **Errores comunes:**
> - **Olvidar ejecutar `terraform init`** tras crear o clonar una configuración. Verás el error `Error: Inconsistent dependency lock file` (con el detalle `required by this configuration but no version is selected`). Solución: `init` siempre es el primer comando en un directorio nuevo.
> - **No fijar la versión del provider.** Sin restricción, cada `init` en una máquina nueva puede traer una versión distinta. Usa siempre `version` en `required_providers`.
> - **Subir `.terraform/` al repositorio.** Contiene binarios pesados y específicos de tu sistema; añádelo a `.gitignore`. En cambio, `.terraform.lock.hcl` **sí** debe ir al control de versiones.
> - **Confundir dirección y nombre local.** `hashicorp/local` es la dirección global; `local` (la clave del bloque) es el nombre con el que te refieres a él dentro de tu configuración.

> 💡 **Buenas prácticas:**
> - Declara siempre tus providers en un bloque `terraform { required_providers { ... } }` con `source` y `version` explícitos.
> - Usa el operador pesimista `~>` para permitir parches sin arriesgarte a cambios de versión mayor.
> - Confirma el fichero `.terraform.lock.hcl` en Git: garantiza instalaciones reproducibles en todo el equipo y en CI (integración continua).

### 🧪 Laboratorio

**Enunciado:** crea un directorio `lab-providers`, escribe una configuración que use el provider `hashicorp/local` con restricción `~> 2.5` para crear un fichero `notas.txt` con el texto que quieras. Inicializa, inspecciona qué ha descargado `init` y aplica.

**Solución paso a paso:**

1. Crea `lab-providers/main.tf` con el contenido del ejemplo anterior (cambia `saludo.txt` por `notas.txt` y el `content` a tu gusto).
2. Ejecuta `terraform init`. Observa la línea `Installing hashicorp/local v...` con la versión concreta que satisface `~> 2.5`.
3. Explora lo descargado: `ls -R .terraform` (o `dir /s .terraform` en CMD). Verás la ruta `providers/registry.terraform.io/hashicorp/local/<versión>/<so_arquitectura>/`.
4. Abre `.terraform.lock.hcl` y localiza la versión fijada y sus `hashes`.
5. Ejecuta `terraform plan` (debe anunciar `1 to add`) y luego `terraform apply` confirmando con `yes`.
6. Comprueba que `notas.txt` existe. Limpieza opcional: `terraform destroy`.

> ❓ **Preguntas de repaso:**
> - **¿Qué tres tareas realiza `terraform init`?** Inicializa el backend, instala los módulos hijos y descarga e instala los plugins de los providers en `.terraform/`.
> - **¿Qué significa la dirección `hashicorp/local`?** Es la forma corta de `registry.terraform.io/hashicorp/local`: hostname del registro (implícito), namespace `hashicorp` y tipo `local`.
> - **¿Para qué sirve `.terraform.lock.hcl` y qué haces si quieres versiones más nuevas?** Fija las versiones exactas seleccionadas para que sean reproducibles; se actualiza con `terraform init -upgrade`.

## 4.2 El directorio de configuración

**¿Qué vas a aprender?** Aquí entenderás cómo lee Terraform tus ficheros: por qué da igual que todo esté en un solo `main.tf` o repartido en varios ficheros, y cuáles son las convenciones de nombres que usa toda la comunidad (`main.tf`, `variables.tf`, `outputs.tf`, `providers.tf`).

### Terraform lee el directorio, no el fichero

Hasta ahora has metido todo en `main.tf`, pero ese nombre no tiene nada de mágico. Cuando ejecutas cualquier comando, Terraform carga **todos los ficheros `.tf`** (y `.tf.json`, la variante JSON) del directorio de trabajo y los evalúa como si fueran **un único documento**. Ese directorio es tu **módulo raíz** (*root module*). Dos matices importantes: no entra en subdirectorios (un subdirectorio es un módulo distinto, que habría que invocar explícitamente), y el orden de los bloques entre ficheros es irrelevante, porque Terraform resuelve las dependencias por referencias, no por posición.

La analogía: tu configuración es como un **archivador de fichas de cocina**. Da igual si escribes toda la receta en una ficha enorme o la repartes en fichas separadas ("ingredientes", "pasos", "presentación"): el plato final es el mismo. Las fichas separadas existen para que *tú* encuentres las cosas rápido, no para Terraform.

Por eso la comunidad ha adoptado convenciones de nombres. Las que recomienda la guía de estilo oficial de HashiCorp:

| Fichero | Contenido habitual |
|---|---|
| `main.tf` | Bloques `resource` y `data` (los recursos en sí) |
| `variables.tf` | Todos los bloques `variable` |
| `outputs.tf` | Todos los bloques `output` |
| `providers.tf` | Los bloques `provider` y su configuración |
| `terraform.tf` | El bloque `terraform` con `required_version` y `required_providers` |

Cuando el proyecto crece, es habitual dividir además por función: `network.tf`, `storage.tf`, `compute.tf`… La regla de oro: que cualquiera sepa dónde buscar cada cosa.

### Ejemplo: reorganizar una configuración

Partimos de un `main.tf` monolítico y lo repartimos así:

```hcl
# terraform.tf — requisitos de versión y providers
terraform {
  required_providers {
    local = {
      source  = "hashicorp/local"
      version = "~> 2.5"
    }
  }
}
```

```hcl
# main.tf — solo los recursos
resource "local_file" "receta" {
  filename = "${path.module}/receta.txt"
  content  = "Tortilla de patatas: patatas, huevos, aceite y (polémica) cebolla.\n"
}
```

```hcl
# outputs.tf — valores que queremos ver tras el apply
output "ruta_receta" {
  description = "Ruta del fichero generado"
  value       = local_file.receta.filename
}
```

Si ejecutas `terraform plan`, el resultado es **idéntico** al que tendrías con todo en un solo fichero:

```text
Plan: 1 to add, 0 to change, 0 to destroy.

Changes to Outputs:
  + ruta_receta = "./receta.txt"
```

> ⚠️ **Errores comunes:**
> - **Ejecutar Terraform desde el directorio equivocado.** Si `terraform plan` te dice que no hay configuración, comprueba con `pwd` (o `Get-Location`) que estás en el directorio de los `.tf`.
> - **Esperar que Terraform lea subdirectorios.** No lo hace: `./modules/red/red.tf` no existe para tu módulo raíz salvo que lo llames con un bloque `module`.
> - **Definir el mismo recurso en dos ficheros.** Como todo se fusiona, dos `resource "local_file" "receta"` en ficheros distintos provocan un error de duplicado (`Duplicate resource ... configuration`).

> 💡 **Buenas prácticas:**
> - Sigue las convenciones de la tabla aunque tu proyecto sea pequeño: te acostumbras desde el principio y cualquier compañero se orientará al instante.
> - Ejecuta `terraform fmt` antes de confirmar cambios: formatea todos los `.tf` del directorio con el estilo canónico.
> - Un directorio = un propósito. No mezcles en el mismo directorio configuraciones que se despliegan por separado.

### 🧪 Laboratorio

**Enunciado:** este vídeo del curso no tiene laboratorio propio, así que haremos un miniejercicio: toma la configuración del laboratorio 4.1 y divídela en `terraform.tf`, `main.tf` y `outputs.tf` (añadiendo un output con la ruta del fichero), y demuestra que nada cambia.

**Solución:** 1) Crea los tres ficheros como en el ejemplo anterior. 2) Ejecuta `terraform validate` para confirmar que la sintaxis es correcta. 3) Ejecuta `terraform plan`: si ya habías aplicado antes y no cambiaste argumentos, verás `No changes. Your infrastructure matches the configuration.` — prueba de que dividir ficheros no altera nada. 4) `terraform apply` y comprueba que el output `ruta_receta` aparece al final.

> ❓ **Preguntas de repaso:**
> - **¿Qué ficheros carga Terraform al ejecutar un comando?** Todos los `.tf` y `.tf.json` del directorio de trabajo (el módulo raíz), tratados como un único documento; los subdirectorios no se incluyen.
> - **¿Es obligatorio el nombre `main.tf`?** No; es pura convención. Terraform leería igual un fichero llamado `patata.tf`.
> - **¿Qué recomienda la guía de estilo poner en `variables.tf` y `outputs.tf`?** Todos los bloques `variable` y todos los bloques `output`, respectivamente (idealmente en orden alfabético).

## 4.3 Trabajar con múltiples providers

**¿Qué vas a aprender?** Una configuración real casi nunca usa un solo provider. Aquí combinarás `local` y `random` en el mismo proyecto, verás cómo `terraform init` descarga varios plugins de una tacada y cómo los recursos de un provider pueden alimentar a los de otro.

### Varios especialistas, un mismo proyecto

Terraform no te limita a un provider por configuración: puedes declarar tantos como necesites, y sus recursos convivirán en el mismo grafo de dependencias. Es como una **reforma de casa**: contratas a un fontanero y a un electricista (dos gremios distintos, cada uno con sus herramientas), pero trabajan sobre el mismo plano y de forma coordinada: el electricista no pone el enchufe hasta que el fontanero decide dónde va la lavadora.

Nuestro segundo "gremio" será el provider **`random`** (también de nivel *official*, de HashiCorp), que genera valores aleatorios *gestionados como recursos*: una vez creados, quedan guardados en el estado y no cambian en cada ejecución. Usaremos dos de sus recursos:

- `random_pet`: genera un nombre memorable tipo `mighty-panda` (argumentos: `length` —número de palabras a combinar, por defecto 2—, `prefix` y `separator` —por defecto `-`—). Exporta el nombre en su atributo `id`.
- `random_integer`: genera un entero entre `min` y `max` (ambos inclusive y obligatorios). Exporta el número en `result`.

### Ejemplo completo: local + random

```hcl
# terraform.tf — declaramos AMBOS providers
terraform {
  required_providers {
    local = {
      source  = "hashicorp/local"
      version = "~> 2.5"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.7"
    }
  }
}
```

```hcl
# main.tf — recursos de los dos providers, encadenados

# Nombre aleatorio memorable para nuestro "servidor" ficticio
resource "random_pet" "servidor" {
  prefix    = "srv"   # el nombre empezará por "srv"
  separator = "-"
  length    = 2       # dos palabras aleatorias
}

# Puerto aleatorio entre 8000 y 8999 (inclusive)
resource "random_integer" "puerto" {
  min = 8000
  max = 8999
}

# Fichero local que usa los valores generados por el provider random
resource "local_file" "inventario" {
  filename = "${path.module}/inventario.txt"
  content  = <<-EOT
    Servidor: ${random_pet.servidor.id}
    Puerto:   ${random_integer.puerto.result}
  EOT
}
```

```hcl
# outputs.tf
output "nombre_servidor" {
  value = random_pet.servidor.id
}
```

Al inicializar, `init` resuelve e instala **los dos plugins**, cada uno con su propia entrada en `.terraform/providers/` y en el *lock file*:

```text
$ terraform init

Initializing provider plugins...
- Finding hashicorp/local versions matching "~> 2.5"...
- Finding hashicorp/random versions matching "~> 3.7"...
- Installing hashicorp/local v2.9.0...
- Installed hashicorp/local v2.9.0 (signed by HashiCorp)
- Installing hashicorp/random v3.9.0...
- Installed hashicorp/random v3.9.0 (signed by HashiCorp)

Terraform has been successfully initialized!
```

Y al aplicar, Terraform respeta el orden que dictan las referencias: primero los recursos `random` (no dependen de nada) y después el fichero, que interpola sus valores:

```text
$ terraform apply -auto-approve

random_integer.puerto: Creating...
random_pet.servidor: Creating...
random_integer.puerto: Creation complete after 0s [id=8437]
random_pet.servidor: Creation complete after 0s [id=srv-obviously-legal-mole]
local_file.inventario: Creating...
local_file.inventario: Creation complete after 0s [id=b41c1e...]

Apply complete! Resources: 3 added, 0 changed, 0 destroyed.

Outputs:

nombre_servidor = "srv-obviously-legal-mole"
```

Si vuelves a ejecutar `terraform plan`, verás `No changes`: los valores aleatorios **no** se regeneran, porque viven en el estado. Solo cambiarían si destruyes el recurso o modificas sus argumentos.

> ⚠️ **Errores comunes:**
> - **Añadir un provider nuevo y no volver a ejecutar `terraform init`.** El plugin no está instalado y `plan` fallará. Regla: provider nuevo → `init` de nuevo.
> - **Usar `.result` con `random_pet` o `.id` esperando el número de `random_integer`.** Cada recurso exporta atributos distintos: el nombre de `random_pet` está en `id`; el entero de `random_integer` está en `result`. Consulta siempre la pestaña de atributos en el Registry.
> - **Esperar que los valores aleatorios cambien en cada `apply`.** No lo hacen (¡y es lo deseable!). Si necesitas forzar la regeneración cuando cambie algo, usa el argumento `keepers`, un mapa de valores cuyo cambio recrea el recurso.

> 💡 **Buenas prácticas:**
> - Declara todos los providers juntos en un único bloque `required_providers` (en `terraform.tf`): de un vistazo se ven las dependencias del proyecto.
> - Usa `random_pet` para dar nombres únicos y legibles a recursos que exigen unicidad: mucho más amigable que un hash.
> - Cuando encadenes providers, referencia atributos (`random_pet.servidor.id`) en vez de copiar valores a mano: así Terraform deduce el orden de creación correcto.

### 🧪 Laboratorio

**Enunciado:** crea un directorio `lab-multi` con una configuración que: (1) genere una contraseña ficticia con `random_integer` de 4 cifras (1000–9999), (2) genere un alias con `random_pet` de 3 palabras con prefijo `pablo`, y (3) escriba ambos en un fichero `credenciales.txt` con permisos `0700`. Añade un output con el alias. Inicializa, aplica y verifica.

**Solución paso a paso:**

1. Crea `terraform.tf` con `required_providers` declarando `hashicorp/local` (`~> 2.5`) y `hashicorp/random` (`~> 3.7`).
2. Crea `main.tf`:

```hcl
resource "random_integer" "pin" {
  min = 1000
  max = 9999
}

resource "random_pet" "alias" {
  prefix = "pablo"
  length = 3
}

resource "local_file" "credenciales" {
  filename        = "${path.module}/credenciales.txt"
  content         = "Alias: ${random_pet.alias.id}\nPIN: ${random_integer.pin.result}\n"
  file_permission = "0700"  # por defecto sería "0777"
}
```

3. Crea `outputs.tf` con `output "alias" { value = random_pet.alias.id }`.
4. Ejecuta `terraform init` y comprueba en la salida que instala **dos** providers; mira `.terraform/providers/registry.terraform.io/hashicorp/` y verás las carpetas `local` y `random`.
5. `terraform plan` debe anunciar `3 to add`. Ejecuta `terraform apply`, escribe `yes` y abre `credenciales.txt`.
6. Ejecuta `terraform plan` otra vez: `No changes`, los valores aleatorios persisten en el estado. Limpieza: `terraform destroy`.

📌 Nota: en Windows los permisos tipo Unix (`file_permission`) tienen efecto limitado; el ejercicio funciona igual, pero no esperes ver `0700` reflejado como en Linux.

> ❓ **Preguntas de repaso:**
> - **¿Cuántos bloques `required_providers` necesitas para usar tres providers?** Uno solo: dentro de él se declara cada provider con su `source` y `version`.
> - **¿Cómo sabe Terraform que debe crear `random_pet` antes que `local_file`?** Porque `local_file` referencia el atributo del recurso `random_pet` (por ejemplo, `random_pet.servidor.id` en el ejemplo teórico, o `random_pet.alias.id` en este laboratorio); esa referencia crea una dependencia implícita en el grafo.
> - **¿Qué hace `terraform init` cuando hay varios providers declarados?** Resuelve las restricciones de versión de cada uno, descarga cada plugin a su ruta dentro de `.terraform/providers/` y registra todos en `.terraform.lock.hcl`.

---

**Siguiente parada:** en la parte 2 de este módulo trabajaremos con variables de entrada, atributos de recursos y dependencias, profundizando en cómo fluye la información entre bloques.
