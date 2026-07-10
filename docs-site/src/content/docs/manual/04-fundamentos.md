---
title: "Módulo 4 · Fundamentos de Terraform"
description: "Providers, directorio de configuración, variables, atributos, dependencias y outputs."
---

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

## 4.4 Variables de entrada (input variables)

**¿Qué vas a aprender?** Hasta ahora has escrito todos los valores directamente dentro de los bloques `resource`, "a fuego". En esta lección vas a descubrir las variables de entrada: cómo declararlas en un fichero `variables.tf` y cómo consumirlas con la expresión `var.nombre`, para que tu configuración deje de ser un guion rígido y se convierta en una plantilla reutilizable.

Piensa en una receta de cocina. Si la receta dice "añade 200 g de harina de trigo", solo sirve para ese bizcocho concreto. Pero si dice "añade `<cantidad>` de `<tipo de harina>`", la misma receta te vale para veinte bizcochos distintos: solo cambias los ingredientes, no las instrucciones. Las variables de entrada son exactamente eso: los huecos rellenables de tu receta de infraestructura. La lógica (los bloques `resource`) no cambia; los datos (nombres de fichero, contenidos, longitudes...) sí.

Una variable se declara con un bloque `variable`. Por convención se agrupan en un fichero llamado `variables.tf`, aunque Terraform lee **todos** los ficheros `.tf` del directorio y le da igual cómo los llames: es una convención para humanos, no una regla del intérprete.

```hcl
# variables.tf — declaración de las variables
variable "nombre_fichero" {
  default = "./mascotas.txt"
}

variable "contenido" {
  default = "Los gatos duermen unas 16 horas al día"
}

variable "prefijo" {
  default = "señor"
}

variable "separador" {
  default = "."
}

variable "longitud" {
  default = 2
}
```

Para usar una variable dentro de un recurso, la referencias con `var.` seguido del nombre que le diste:

```hcl
# main.tf — uso de las variables
resource "local_file" "mascota" {
  filename = var.nombre_fichero  # sustituye al valor escrito a mano
  content  = var.contenido
}

resource "random_pet" "mi_mascota" {
  prefix    = var.prefijo
  separator = var.separador
  length    = var.longitud
}
```

Al ejecutar `terraform plan`, Terraform resuelve cada `var.x` con su valor y te enseña el resultado ya sustituido:

```text
  # local_file.mascota will be created
  + resource "local_file" "mascota" {
      + content              = "Los gatos duermen unas 16 horas al día"
      + filename             = "./mascotas.txt"
      + file_permission      = "0777"
      + id                   = (known after apply)
    }

Plan: 2 to add, 0 to change, 0 to destroy.
```

La gran ventaja: si mañana quieres otro contenido, editas **solo** `variables.tf` (o pasas el valor por otra vía, como verás en la lección 4.6) sin tocar la lógica de `main.tf`.

> 🔄 **Actualización:** en versiones antiguas de Terraform (0.11 y anteriores) toda referencia a una variable debía envolverse en `"${var.contenido}"`. Desde Terraform 0.12, y por supuesto en todo Terraform 1.x, escribes `var.contenido` a secas; la sintaxis `${...}` solo se usa **dentro de cadenas de texto**, como verás en la lección 4.7.

> ⚠️ **Errores comunes:**
> - Escribir `filename = nombre_fichero` sin el prefijo `var.`. Terraform interpreta el identificador suelto como el comienzo de una referencia a un recurso y falla con *"Invalid reference"*. La referencia siempre es `var.<nombre>`.
> - Usar una variable que no has declarado en ningún bloque `variable`: obtendrás *"Reference to undeclared input variable"*. Declara primero, usa después.
> - Poner comillas alrededor de la referencia (`filename = "var.nombre_fichero"`): eso es la cadena literal `var.nombre_fichero`, no el valor de la variable.

> 💡 **Buenas prácticas:**
> - Agrupa todas las declaraciones en `variables.tf`: cualquiera que abra tu proyecto sabrá de un vistazo qué es configurable.
> - Da nombres descriptivos en minúsculas con guiones bajos (`nombre_fichero`, no `nf1`).
> - Convierte en variable todo valor que preveas cambiar entre entornos o ejecuciones; deja fijo lo que sea realmente constante.

### 🧪 Laboratorio

**Enunciado:** crea un directorio `lab-variables` con una configuración que genere un fichero local cuyo nombre y contenido vengan de variables. Declara `ruta` (con valor por defecto `./cita.txt`) y `cita` (con una cita que te guste). Ejecuta el ciclo completo.

**Solución:**

1. Crea `main.tf`:

```hcl
terraform {
  required_providers {
    local = {
      source = "hashicorp/local"
    }
  }
}

resource "local_file" "cita" {
  filename = var.ruta
  content  = var.cita
}
```

2. Crea `variables.tf`:

```hcl
variable "ruta" {
  default = "./cita.txt"
}

variable "cita" {
  default = "La simplicidad es la máxima sofisticación"
}
```

3. Ejecuta `terraform init`, `terraform plan` y `terraform apply`. Comprueba con `cat cita.txt` que el fichero contiene tu cita. Cambia el valor de `cita` en `variables.tf`, vuelve a ejecutar `terraform apply` y observa que Terraform detecta el cambio y reemplaza el fichero sin que hayas tocado `main.tf`.

> ❓ **Preguntas de repaso:**
> - **¿Es obligatorio que las variables estén en `variables.tf`?** No. Terraform carga todos los `.tf` del directorio; es una convención de organización muy recomendable, pero no un requisito.
> - **¿Cómo se referencia una variable llamada `region`?** Con `var.region` (sin comillas, salvo que la interpoles dentro de una cadena con `"${var.region}"`).
> - **¿Qué gana tu configuración al usar variables?** Reutilización y seguridad: separas datos de lógica y evitas editar los recursos cada vez que cambia un valor.

## 4.5 El bloque variable en profundidad

**¿Qué vas a aprender?** El bloque `variable` admite mucho más que un `default`. Aquí verás sus argumentos principales —`default`, `type`, `description`, `sensitive` y `validation`— y recorrerás todos los tipos de datos de Terraform: `string`, `number`, `bool`, `any`, `list`, `set`, `map`, `object` y `tuple`, incluyendo cómo acceder a sus elementos por índice o por clave.

Si una variable es un hueco rellenable de la receta, los argumentos del bloque son las **normas del hueco**: qué forma tiene (tipo), qué pone en la etiqueta (descripción), qué valor trae de serie (default) y qué rellenos se rechazan (validación). Es como el formulario de un banco: el campo "IBAN" no acepta cualquier garabato; tiene formato, longitud y una nota explicando qué esperan de ti.

Un bloque completo tiene esta pinta:

```hcl
variable "longitud" {
  type        = number
  default     = 2
  description = "Número de palabras del nombre de la mascota"

  validation {
    condition     = var.longitud >= 1 && var.longitud <= 5
    error_message = "La longitud debe estar entre 1 y 5 palabras."
  }
}
```

- `type` restringe el tipo de dato aceptado. Si alguien pasa `"dos"` donde esperas un `number`, Terraform falla antes de tocar nada.
- `default` es el valor de respaldo si nadie proporciona otro.
- `description` documenta la variable: aparece en el prompt interactivo (el aviso con el que Terraform te pide un valor por consola) y en la documentación generada.
- `validation` define una `condition` (expresión que debe ser verdadera) y un `error_message` que se muestra si no lo es.
- `sensitive = true` oculta el valor en las salidas de `plan` y `apply`:

```hcl
variable "token_api" {
  type      = string
  sensitive = true
}
```

```text
  + resource "local_file" "secreto" {
      + content   = (sensitive value)
      + filename  = "./secreto.txt"
    }
```

Ojo: `sensitive` oculta el valor en pantalla, pero **sigue almacenándose en claro en el fichero de estado**.

### Los tipos de datos, uno a uno

Los tres tipos **primitivos** son `string` (texto), `number` (enteros y decimales) y `bool` (`true`/`false`). El comodín `any` acepta cualquier tipo y es el valor implícito cuando no declaras `type`; úsalo solo cuando de verdad no puedas concretar más.

Los tipos de **colección** agrupan valores del mismo tipo:

```hcl
# list: secuencia ordenada, acceso por índice empezando en 0
variable "prefijos" {
  type    = list(string)
  default = ["don", "doña", "lady"]
}

# set: colección de valores únicos, SIN orden ni índices
variable "entornos" {
  type    = set(string)
  default = ["dev", "staging", "prod"]
}

# map: pares clave-valor, acceso por clave
variable "contenido_por_entorno" {
  type = map(string)
  default = {
    dev  = "Fichero de pruebas: se puede borrar"
    prod = "Fichero de producción: NO tocar"
  }
}
```

Y los tipos **estructurales** agrupan valores de tipos distintos:

```hcl
# object: atributos con nombre, cada uno con su tipo
variable "gato" {
  type = object({
    nombre       = string
    edad         = number
    esterilizado = bool
    juguetes     = list(string)
  })
  default = {
    nombre       = "Trufa"
    edad         = 3
    esterilizado = true
    juguetes     = ["ratón", "pluma"]
  }
}

# tuple: secuencia con un tipo fijo por posición
variable "ficha" {
  type    = tuple([string, number, bool])
  default = ["Trufa", 3, true]
}
```

El acceso a los elementos depende del tipo:

```hcl
resource "local_file" "demo" {
  filename = "./demo.txt"
  content  = <<-EOT
    Prefijo elegido: ${var.prefijos[0]}
    Aviso: ${var.contenido_por_entorno["prod"]}
    Mascota: ${var.gato.nombre}, ${var.gato.edad} años
    Primer valor de la tupla: ${var.ficha[0]}
  EOT
}
```

Es decir: `list` y `tuple` por índice (`[0]`, `[1]`...), `map` por clave (`["prod"]`), `object` por atributo (`.nombre`). Un `set` no admite acceso por índice porque no tiene orden; se recorre o se convierte a lista con funciones.

> 🔄 **Actualización:** el bloque `validation` llegó en Terraform 0.13 y `sensitive` en 0.14; en Terraform 1.x actual ambos son estándar. Además, desde Terraform 1.9 la `condition` de una validación puede referenciar **otras** variables del módulo, no solo la propia. Existe también el argumento `nullable` (desde 1.1) para controlar si la variable admite `null`.

> ⚠️ **Errores comunes:**
> - Confundir `list` y `set`: si intentas `var.entornos[0]` sobre un `set`, Terraform da error porque los sets no están indexados.
> - Olvidar una clave obligatoria en un `object`: el mensaje *"attribute ... is required"* te dirá cuál falta; el `default` debe ajustarse exactamente al esquema del tipo.
> - Confiar en que `sensitive = true` protege el secreto: solo lo oculta en la consola. El estado lo contiene en claro; protégelo aparte.
> - Usar `any` por pereza: pierdes la detección temprana de errores de tipo, que es media gracia de declarar variables.

> 💡 **Buenas prácticas:**
> - Declara siempre `type` y `description`, incluso cuando haya `default`: son la documentación viva de tu módulo.
> - Usa `validation` para reglas de negocio (rangos, formatos, valores permitidos) y escribe mensajes de error que expliquen cómo corregir.
> - Prefiere `object` a varios `string` sueltos cuando un grupo de valores viaja siempre junto.

### 🧪 Laboratorio

**Enunciado:** crea una configuración con una variable `mascotas` de tipo `map(object({ prefijo = string, longitud = number }))` con dos claves, `casa` y `oficina`. Genera un `random_pet` para la clave `casa` y valida que `longitud` de cada entrada esté entre 1 y 4.

**Solución:**

1. `variables.tf`:

```hcl
variable "mascotas" {
  type = map(object({
    prefijo  = string
    longitud = number
  }))
  default = {
    casa    = { prefijo = "sr", longitud = 2 }
    oficina = { prefijo = "srta", longitud = 3 }
  }

  validation {
    condition     = alltrue([for m in values(var.mascotas) : m.longitud >= 1 && m.longitud <= 4])
    error_message = "Cada mascota debe tener una longitud entre 1 y 4 palabras."
  }
}
```

2. `main.tf`:

```hcl
resource "random_pet" "casa" {
  prefix = var.mascotas["casa"].prefijo
  length = var.mascotas["casa"].longitud
}
```

3. Ejecuta `terraform init` y `terraform apply`. Después cambia `longitud = 9` en `casa` y lanza `terraform plan`: verás tu mensaje de validación en el error. Fíjate en la cadena de acceso `var.mascotas["casa"].prefijo`: clave de map + atributo de object.

> ❓ **Preguntas de repaso:**
> - **¿Qué tipo asume Terraform si no declaras `type`?** `any`: acepta cualquier valor.
> - **¿En qué se diferencian `list` y `tuple`?** En una `list` todos los elementos son del mismo tipo; en una `tuple` cada posición tiene su propio tipo declarado.
> - **¿`sensitive = true` cifra el valor en el estado?** No. Solo evita mostrarlo en la salida de CLI; en `terraform.tfstate` está en claro.

## 4.6 Formas de pasar valores a las variables

**¿Qué vas a aprender?** Declarar una variable y darle valor son cosas distintas. Aquí verás las cinco vías para asignar valores — valor por defecto, modo interactivo, flag `-var`, ficheros de definición (`terraform.tfvars`, `*.auto.tfvars`, `-var-file`) y variables de entorno `TF_VAR_` — y, lo más importante, el orden de precedencia exacto cuando varias vías compiten.

Imagina que quedas a cenar con amigos y hay que decidir el restaurante. Hay una opción por defecto ("el italiano de siempre"), sugerencias por el grupo de WhatsApp, un correo previo y, al final, alguien que decide en persona en el último momento. Todas son formas válidas de "dar un valor", pero cuando se contradicen, gana la más inmediata. En Terraform pasa igual, y las reglas de quién gana están escritas.

**1. Valor por defecto.** El `default` del bloque `variable`. Se usa solo si ninguna otra vía proporciona valor.

**2. Modo interactivo.** Si una variable no tiene `default` ni recibe valor por ningún medio, Terraform te la pregunta al ejecutar `plan` o `apply`:

```text
$ terraform apply
var.cita
  Cita que se escribirá en el fichero

  Enter a value:
```

Útil para probar; inviable para automatizar.

**3. Flag `-var`.** Directamente en el comando, tantas veces como necesites:

```text
terraform apply -var "cita=La constancia vence al talento" -var "ruta=./frase.txt"
```

**4. Ficheros de definición de variables.** Ficheros con pares `nombre = valor` (sintaxis HCL, sin bloques `variable`):

```hcl
# terraform.tfvars
cita = "La constancia vence al talento"
ruta = "./frase.txt"
```

Terraform los carga automáticamente si se llaman `terraform.tfvars`, `terraform.tfvars.json`, o terminan en `.auto.tfvars` / `.auto.tfvars.json`. Cualquier otro nombre (por ejemplo `pruebas.tfvars`) requiere pasarlo explícitamente: `terraform apply -var-file "pruebas.tfvars"`.

**5. Variables de entorno.** Cualquier variable de entorno con el prefijo `TF_VAR_` seguido del nombre exacto de la variable:

```text
# Linux / macOS / Git Bash
export TF_VAR_cita="La constancia vence al talento"

# PowerShell (Windows)
$env:TF_VAR_cita = "La constancia vence al talento"
```

Terraform ignora las variables `TF_VAR_` que no tengan un bloque `variable` correspondiente.

### El orden de precedencia

Cuando la misma variable recibe valor por varias vías, Terraform las carga en este orden, y **las fuentes posteriores pisan a las anteriores**:

| Orden | Fuente | Nota |
|---|---|---|
| 1 (pierde) | Variables de entorno `TF_VAR_` | La fuente de menor prioridad |
| 2 | `terraform.tfvars` | Cargado automáticamente |
| 3 | `terraform.tfvars.json` | Cargado automáticamente |
| 4 | `*.auto.tfvars` / `*.auto.tfvars.json` | En orden alfabético de nombre de fichero |
| 5 (gana) | `-var` y `-var-file` en la línea de comandos | En el orden en que aparezcan en el comando |

El `default` no compite: es solo el último recurso si ninguna fuente da valor. Y si tampoco hay `default`, llega el prompt interactivo.

> ⚠️ **Errores comunes:**
> - Llamar al fichero `variables.tfvars` o `dev.tfvars` y esperar que se cargue solo: solo se cargan automáticamente `terraform.tfvars(.json)` y `*.auto.tfvars(.json)`. Para el resto, `-var-file`.
> - Olvidar que `-var` gana a todo: si un `apply` no respeta tu `terraform.tfvars`, revisa el comando (o el pipeline de CI) por si alguien pasa `-var`.
> - Errar el nombre en la variable de entorno: `TF_VAR_Cita` no es `TF_VAR_cita`; el sufijo debe coincidir exactamente con el nombre declarado.
> - Confundir `variables.tf` (declaraciones, bloques `variable`) con `terraform.tfvars` (asignaciones, pares `nombre = valor`).

> 💡 **Buenas prácticas:**
> - Un fichero `.tfvars` por entorno (`dev.tfvars`, `prod.tfvars`) pasado con `-var-file` es un patrón limpio y explícito.
> - Reserva `TF_VAR_` para secretos en CI/CD: no quedan escritos en ficheros del repositorio.
> - No subas al control de versiones ficheros `.tfvars` con datos sensibles; añádelos a `.gitignore`.

### 🧪 Laboratorio

**Enunciado:** partiendo del laboratorio de 4.4, da valor a la variable `cita` por cuatro vías a la vez y comprueba empíricamente quién gana.

**Solución:**

1. Deja el `default` de `cita` como `"valor por defecto"`.
2. Exporta la variable de entorno: `export TF_VAR_cita="desde entorno"` (en PowerShell: `$env:TF_VAR_cita = "desde entorno"`).
3. Crea `terraform.tfvars` con `cita = "desde tfvars"`.
4. Crea `zeta.auto.tfvars` con `cita = "desde auto tfvars"`.
5. Ejecuta `terraform plan` y observa el contenido planificado: `"desde auto tfvars"` (los `*.auto.tfvars` pisan a `terraform.tfvars`, que a su vez pisa al entorno).
6. Ahora ejecuta `terraform plan -var "cita=desde la CLI"`: gana `"desde la CLI"`.
7. Borra `zeta.auto.tfvars` y `terraform.tfvars`, ejecuta `terraform plan` sin `-var`: gana `"desde entorno"`. Quita la variable de entorno y volverá el `default`.

> ❓ **Preguntas de repaso:**
> - **Tienes la misma variable en `terraform.tfvars` y en `TF_VAR_`. ¿Quién gana?** `terraform.tfvars`: los ficheros de definición tienen más prioridad que las variables de entorno.
> - **¿Qué ficheros de variables carga Terraform sin que se lo pidas?** `terraform.tfvars`, `terraform.tfvars.json` y cualquier `*.auto.tfvars` / `*.auto.tfvars.json` (estos últimos en orden alfabético).
> - **¿Cuándo pregunta Terraform un valor de forma interactiva?** Cuando la variable no tiene `default` y ninguna fuente (entorno, ficheros, CLI) le da valor.

## 4.7 Atributos de recursos y referencias

**¿Qué vas a aprender?** Los recursos no solo consumen argumentos: también **exportan atributos** con información que a menudo solo se conoce tras crearlos. Aprenderás a leerlos con la sintaxis `tipo_recurso.nombre.atributo` y a interpolarlos dentro de cadenas con `${...}`, conectando la salida de un recurso con la entrada de otro.

Hasta ahora tus recursos vivían aislados, pero la infraestructura real es una cadena de dependencias: la base de datos genera una dirección que la aplicación necesita; el certificado genera un identificador que el balanceador consume. Es como una cadena de montaje: el puesto A produce una pieza con número de serie, y el puesto B necesita ese número exacto para continuar. Nadie lo conoce de antemano; se lee de la pieza cuando sale.

¿Cómo sabes qué "produce" cada recurso? En su documentación del [Terraform Registry](https://registry.terraform.io/) —el catálogo oficial de *providers* y módulos de Terraform—, en la sección de atributos (*Attributes Reference* / esquema *Read-Only*). Por ejemplo, `random_pet` exporta el atributo `id`, que contiene el nombre generado; y `local_file`, además de devolverte argumentos como `filename`, exporta `id` (checksum SHA1 del contenido en hexadecimal) y varios checksums más (`content_md5`, `content_sha256`...).

La sintaxis de referencia es siempre la misma: `<TIPO>.<NOMBRE>.<ATRIBUTO>`. Y cuando quieres incrustar esa referencia dentro de una cadena, usas la **interpolación** `"${...}"`:

```hcl
resource "random_pet" "mi_mascota" {
  prefix    = "señor"
  separator = "."
  length    = 1
}

resource "local_file" "ficha" {
  filename = "./ficha_mascota.txt"
  # Interpolación: incrustamos el atributo id dentro de una cadena
  content  = "¡Mi mascota se llama ${random_pet.mi_mascota.id}!"
}
```

Al aplicar:

```text
random_pet.mi_mascota: Creating...
random_pet.mi_mascota: Creation complete after 0s [id=señor.walrus]
local_file.ficha: Creating...
local_file.ficha: Creation complete after 0s [id=3f2ab...]

Apply complete! Resources: 2 added, 0 changed, 0 destroyed.
```

El fichero contendrá `¡Mi mascota se llama señor.walrus!`. Fíjate en que el `id` de `random_pet` incluye el prefijo y usa el separador configurado. Durante el `plan`, los atributos aún desconocidos aparecen como `(known after apply)`: Terraform sabe que existirán, pero no su valor hasta crear el recurso.

Si la referencia va sola (sin texto alrededor), no necesitas interpolación:

```hcl
content = random_pet.mi_mascota.id   # referencia directa, sin "${}"
```

> 🔄 **Actualización:** en Terraform 0.11 y anteriores, *toda* referencia requería `"${...}"`. En Terraform 1.x la interpolación solo tiene sentido para mezclar expresiones con texto dentro de una cadena; `"${var.x}"` a solas es una redundancia que `terraform fmt` reescribe automáticamente como `var.x`. Versiones anteriores mostraban un aviso de deprecación por escribirlo así, pero se retiró en la 0.15 precisamente porque `fmt` ya corrige el estilo por ti.

> ⚠️ **Errores comunes:**
> - Inventarse el atributo: no todos los recursos exportan lo mismo. Consulta siempre el Registry; si escribes `random_pet.mi_mascota.name`, fallará porque el atributo se llama `id`.
> - Olvidar el `${}` dentro de cadenas: `content = "Se llama random_pet.mi_mascota.id"` escribe ese texto literal en el fichero.
> - Referenciar por el tipo sin el nombre local (`random_pet.id`): la ruta completa es tipo + nombre + atributo.

> 💡 **Buenas prácticas:**
> - Prefiere referencias a copiar valores a mano: si el recurso origen cambia, la referencia se actualiza sola y, además, crea la dependencia correcta (siguiente lección).
> - Ten abierta la pestaña de documentación del provider mientras escribes: la lista de atributos exportados es tu contrato.

### 🧪 Laboratorio

**Enunciado:** crea un `random_pet` llamado `perro` con `prefix = "doña"` y `length = 2`, y un `local_file` `certificado` en `./certificado.txt` cuyo contenido sea: `Certificado de adopción de <nombre generado>`. Añade después un segundo `local_file` que guarde el checksum SHA256 del primero.

**Solución:**

```hcl
resource "random_pet" "perro" {
  prefix = "doña"
  length = 2
}

resource "local_file" "certificado" {
  filename = "./certificado.txt"
  content  = "Certificado de adopción de ${random_pet.perro.id}"
}

resource "local_file" "huella" {
  filename = "./huella.txt"
  content  = "SHA256 del certificado: ${local_file.certificado.content_sha256}"
}
```

Ejecuta `terraform apply` y comprueba ambos ficheros. Observa en la salida que Terraform crea primero `random_pet.perro`, luego `local_file.certificado` y por último `local_file.huella`: las referencias han encadenado los tres recursos.

> ❓ **Preguntas de repaso:**
> - **¿Dónde consultas qué atributos exporta un recurso?** En la documentación del provider en el Terraform Registry (sección de atributos / *Read-Only*).
> - **¿Qué significa `(known after apply)` en un plan?** Que el valor de ese atributo solo se conocerá cuando el recurso se haya creado realmente.
> - **¿Cuándo es obligatoria la sintaxis `${...}`?** Solo al incrustar una expresión dentro de una cadena de texto; fuera de cadenas se referencia directamente.

## 4.8 Dependencias entre recursos

**¿Qué vas a aprender?** Cuando un recurso usa un atributo de otro, Terraform deduce solo el orden de creación. Aquí verás cómo funcionan esas **dependencias implícitas**, cuándo necesitas declarar una **dependencia explícita** con `depends_on`, y en qué orden se crean y se destruyen los recursos.

Piensa en construir una casa: no puedes poner el tejado antes que los muros, ni los muros antes que los cimientos. Nadie escribe "primero cimientos" en un papel: el orden se deduce de que cada pieza se apoya físicamente en la anterior. Eso es una dependencia implícita. Pero a veces la relación no es visible: "no pintes hasta que el electricista haya pasado", aunque la pintura no toque ningún cable. Esa regla hay que decirla explícitamente.

**Dependencia implícita:** en el ejemplo de la lección anterior, `local_file.ficha` referencia `random_pet.mi_mascota.id`. Terraform construye internamente un grafo de dependencias a partir de esas referencias y ordena las operaciones: primero crea `random_pet`, después `local_file`. Y al destruir (`terraform destroy`) invierte el orden: **primero elimina los recursos dependientes y al final aquellos de los que dependen**.

```text
local_file.ficha: Destroying... [id=3f2ab...]
local_file.ficha: Destruction complete after 0s
random_pet.mi_mascota: Destroying... [id=señor.walrus]
random_pet.mi_mascota: Destruction complete after 0s
```

**Dependencia explícita:** a veces un recurso depende del *comportamiento* de otro sin consumir ninguno de sus datos. Para esos casos existe el meta-argumento `depends_on`, que acepta una lista de referencias a otros recursos (o módulos) del mismo módulo:

```hcl
resource "random_pet" "servidor" {
  length = 2
}

resource "local_file" "registro" {
  filename = "./registro.txt"
  content  = "Servidor bautizado correctamente"

  # No usamos ningún atributo de random_pet.servidor,
  # pero queremos garantizar que exista antes que este fichero.
  depends_on = [
    random_pet.servidor
  ]
}
```

Ahora Terraform crea `random_pet.servidor` primero aunque `local_file.registro` no lo referencie. La documentación oficial es tajante: usa `depends_on` **como último recurso**, porque obliga a Terraform a planificar de forma más conservadora (puede reemplazar más recursos de la cuenta). Si puedes expresar la relación con una referencia a un atributo, hazlo; el grafo será más preciso.

> ⚠️ **Errores comunes:**
> - Añadir `depends_on` cuando ya existe una referencia implícita: es redundante y ensucia el código.
> - Escribir el valor como cadena: `depends_on = ["random_pet.servidor"]` es sintaxis de Terraform 0.11; hoy son referencias sin comillas dentro de una lista.
> - Intentar meter expresiones arbitrarias: `depends_on` solo acepta referencias directas a recursos o módulos, conocidas antes de evaluar el grafo.

> 💡 **Buenas prácticas:**
> - Prioriza siempre las dependencias implícitas: documentan la relación y transportan el dato.
> - Cuando uses `depends_on`, acompáñalo de un comentario explicando por qué es necesario; la propia documentación oficial lo recomienda.
> - Si te descubres encadenando muchos `depends_on`, replantéate el diseño: probablemente falten referencias naturales entre recursos.

### 🧪 Laboratorio

**Enunciado:** crea dos recursos sin relación aparente: un `random_pet` llamado `base_de_datos` y un `local_file` llamado `aviso` con el texto `La base de datos ya tiene nombre`. Garantiza con una dependencia explícita que el fichero nunca se cree antes que el `random_pet`. Después verifica el orden de destrucción.

**Solución:**

```hcl
resource "random_pet" "base_de_datos" {
  prefix = "db"
  length = 2
}

resource "local_file" "aviso" {
  filename = "./aviso.txt"
  content  = "La base de datos ya tiene nombre"

  # Dependencia explícita: sin ella, Terraform podría crear ambos en paralelo
  depends_on = [random_pet.base_de_datos]
}
```

1. `terraform apply`: observa que `random_pet.base_de_datos` termina antes de que empiece `local_file.aviso`.
2. `terraform destroy`: comprueba que el orden se invierte, `local_file.aviso` cae primero.
3. Extra: elimina el `depends_on` y cambia el `content` a `"La base de datos se llama ${random_pet.base_de_datos.id}"`. El orden se mantiene, ahora por dependencia implícita: es la versión preferible.

> ❓ **Preguntas de repaso:**
> - **¿Cómo detecta Terraform una dependencia implícita?** Analizando las referencias entre recursos en las expresiones (por ejemplo, `random_pet.x.id` dentro de otro recurso) y construyendo con ellas el grafo de dependencias.
> - **¿En qué orden destruye Terraform los recursos?** En el inverso al de creación: primero los dependientes, después sus dependencias.
> - **¿Cuándo está justificado `depends_on`?** Solo cuando existe una dependencia real de comportamiento que no puede expresarse mediante referencias a atributos.

## 4.9 Variables de salida (outputs)

**¿Qué vas a aprender?** Las variables de salida son el altavoz de tu configuración: publican valores hacia fuera. Verás el bloque `output` con sus argumentos `value` y `description`, el comando `terraform output` (a secas, con nombre y con `-json` o `-raw`) y los usos reales de los outputs.

Si las variables de entrada son los huecos de un formulario, los outputs son el **resguardo** que te entregan al terminar el trámite: un papelito con los datos importantes del resultado (número de expediente, fecha, referencia) para que tú — u otra ventanilla — sigáis el proceso sin rebuscar en los archivos internos.

El bloque es sencillo: `value` acepta cualquier expresión válida (casi siempre, el atributo de un recurso) y `description` documenta para qué sirve:

```hcl
resource "random_pet" "mi_mascota" {
  prefix = "señora"
  length = 2
}

output "nombre_mascota" {
  value       = random_pet.mi_mascota.id
  description = "Nombre generado para la mascota"
}
```

Tras `terraform apply`, los outputs del módulo raíz se imprimen al final:

```text
Apply complete! Resources: 1 added, 0 changed, 0 destroyed.

Outputs:

nombre_mascota = "señora-gentle-mongoose"
```

Y puedes consultarlos en cualquier momento sin volver a aplicar, porque se guardan en el estado:

```text
$ terraform output
nombre_mascota = "señora-gentle-mongoose"

$ terraform output nombre_mascota
"señora-gentle-mongoose"

$ terraform output -raw nombre_mascota
señora-gentle-mongoose

$ terraform output -json
{
  "nombre_mascota": {
    "sensitive": false,
    "type": "string",
    "value": "señora-gentle-mongoose"
  }
}
```

`-raw` imprime el valor pelado (solo admite string, number y bool), ideal para scripts de shell; `-json` devuelve todos los outputs como objeto JSON, perfecto para procesar con herramientas como `jq`. ¿Para qué sirven los outputs, según la documentación oficial? Para mostrar valores en la CLI del módulo raíz, para que un módulo hijo exponga atributos a su módulo padre, para que otras configuraciones los lean vía *remote state* y para pasar información a herramientas de automatización. El bloque admite además `sensitive` (oculta el valor en la salida normal), `depends_on` y `precondition`.

> 🔄 **Actualización:** el flag `-raw` se añadió en Terraform 0.14.3, posterior a la grabación del curso; antes había que apañarse con `-json`. Ten en cuenta también que, con `-json` o `-raw`, Terraform muestra los valores `sensitive` **en texto plano**: la protección solo aplica a la salida normal.

> ⚠️ **Errores comunes:**
> - Ejecutar `terraform output` antes del primer `apply`: los outputs viven en el estado; sin apply, aviso de que no hay outputs.
> - Usar `-raw` con una lista o un map: solo funciona con valores primitivos; para estructuras, `-json`.
> - Tratar los outputs como secretos seguros: se almacenan en el estado y `-json`/`-raw` los muestran aunque sean `sensitive`.

> 💡 **Buenas prácticas:**
> - Añade `description` a todos los outputs: son la interfaz pública de tu configuración.
> - Expón solo lo que otros necesitan consumir; un módulo con cuarenta outputs es tan confuso como una función que devuelve cuarenta valores.
> - En scripts, usa `terraform output -raw nombre` en lugar de parsear la salida normal, que incluye comillas y formato.

### 🧪 Laboratorio

**Enunciado:** amplía el laboratorio de 4.7 con dos outputs: `nombre_perro` (el nombre generado, con descripción) y `ruta_certificado` (la ruta del fichero creado). Consulta ambos con `terraform output` y extrae el nombre "limpio" para usarlo en un script.

**Solución:**

1. Añade a la configuración:

```hcl
output "nombre_perro" {
  value       = random_pet.perro.id
  description = "Nombre generado para el perro adoptado"
}

output "ruta_certificado" {
  value       = local_file.certificado.filename
  description = "Ruta del certificado de adopción"
}
```

2. Ejecuta `terraform apply`; verás ambos outputs al final.
3. Consulta: `terraform output` (todos), `terraform output nombre_perro` (uno, con comillas) y `terraform output -raw nombre_perro` (sin comillas, listo para un script: por ejemplo `echo "Adoptado: $(terraform output -raw nombre_perro)"`).
4. Prueba `terraform output -json` y observa la estructura con `type`, `value` y `sensitive` por cada output.

> ❓ **Preguntas de repaso:**
> - **¿Qué argumentos habituales lleva un bloque `output`?** `value` (obligatorio, cualquier expresión) y `description`; opcionalmente `sensitive`, `depends_on` y `precondition`.
> - **¿Qué diferencia hay entre `terraform output -raw` y `-json`?** `-raw` imprime un único valor primitivo sin formato; `-json` devuelve todos los outputs (o el indicado) como JSON estructurado.
> - **Cita dos usos de los outputs más allá de imprimir en pantalla.** Exponer valores de un módulo hijo a su padre y compartir datos con otras configuraciones mediante *remote state* (o con herramientas externas de automatización).
