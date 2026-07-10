---
title: "Módulo 12 · Funciones, condicionales y workspaces"
description: "Funciones de HCL, expresiones condicionales y gestión de entornos con workspaces."
---

Hasta ahora has escrito configuraciones bastante "estáticas": valores fijos, algún `count` y poco más. En este módulo vas a darle a tu HCL el músculo que le faltaba: **funciones** para transformar datos, **expresiones condicionales** para tomar decisiones y **workspaces** para reutilizar la misma configuración en varios entornos. Todo se practica en local con los providers `local` y `random`, sin gastar un céntimo.

## 12.1 Funciones de Terraform

**¿Qué vas a aprender?** En esta lección vas a conocer el catálogo de funciones integradas de Terraform: qué categorías existen, cómo se usan las más importantes (numéricas, de cadenas, de colecciones, de ficheros y de codificación) y, sobre todo, cómo experimentar con ellas sin miedo usando `terraform console`. Al terminar sabrás transformar casi cualquier dato dentro de una configuración.

### Un lenguaje con pilas incluidas

Ya has usado alguna función sin darle importancia, como `file()` para leer una clave pública. Terraform trae **más de cien funciones integradas**, y aquí hay un detalle importante que como desarrollador te va a chocar: **no puedes definir tus propias funciones** en HCL. Solo puedes usar las que vienen de serie. Piensa en ellas como en las fórmulas de una hoja de cálculo: no puedes inventarte `=MIFORMULA()`, pero combinando `SUM`, `IF` y `VLOOKUP` resuelves casi cualquier cosa. Con Terraform pasa lo mismo: la potencia está en la combinación.

> 🔄 **Actualización:** desde Terraform 1.8 los *providers* pueden exponer sus propias funciones (las llamadas *provider-defined functions*), que se invocan con la sintaxis `provider::nombre_provider::funcion()`. Sigue sin ser posible definir funciones en tu propio código HCL, pero el ecosistema ya no se limita a las funciones integradas. Para este curso nos basta con las de serie.

### Tu laboratorio de pruebas: terraform console

Antes de meter una función en un `.tf` y cruzar los dedos, pruébala en la **consola interactiva**. Ejecuta esto en cualquier directorio con (o sin) configuración:

```text
$ terraform console
> max(5, 12, 9)
12
> exit
```

La consola evalúa expresiones al vuelo, tiene acceso a las variables y al estado de tu configuración actual (si lo hay), y se cierra con `exit`, `Ctrl+C` o `Ctrl+D`. Un detalle a tener en cuenta: mientras está abierta, la consola **bloquea el fichero de estado**, así que no podrás ejecutar `terraform apply` en otra terminal hasta salir.

### Funciones numéricas

```text
> max(-1, 2, 99)
99
> min(-1, 2, 99)
-1
> ceil(10.1)
11
> floor(10.9)
10
> abs(-12.4)
12.4
```

`ceil` redondea hacia arriba, `floor` hacia abajo y `abs` devuelve el valor absoluto. Un truco útil: si tienes los números en una lista, expándela con `...` → `max([1, 5, 3]...)` devuelve `5`.

### Funciones de cadenas

```text
> split(",", "ana,juan,lucia")
tolist([
  "ana",
  "juan",
  "lucia",
])
> join("-", ["ana", "juan", "lucia"])
"ana-juan-lucia"
> lower("PABLO")
"pablo"
> upper("pablo")
"PABLO"
> title("curso de terraform")
"Curso De Terraform"
> substr("hello world", 1, 4)
"ello"
> replace("hola mundo", "mundo", "Terraform")
"hola Terraform"
```

Fíjate en que `split` y `join` son inversas: una convierte cadena en lista y la otra lista en cadena. En `substr(cadena, offset, longitud)` el `offset` empieza en 0, admite valores negativos (cuenta desde el final) y una longitud de `-1` significa "hasta el final".

### Funciones de colecciones

Son las que más usarás en el día a día, porque listas y mapas están por todas partes en Terraform:

```text
> length(["a", "b", "c"])
3
> index(["a", "b", "c"], "b")
1
> element(["a", "b", "c"], 3)
"a"
> contains(["a", "b", "c"], "z")
false
> keys({entorno = "dev", region = "eu"})
tolist([
  "entorno",
  "region",
])
> values({entorno = "dev", region = "eu"})
tolist([
  "dev",
  "eu",
])
> lookup({dev = "pequeño", prod = "grande"}, "prod", "mediano")
"grande"
> lookup({dev = "pequeño", prod = "grande"}, "qa", "mediano")
"mediano"
> merge({a = 1}, {b = 2}, {a = 99})
{
  "a" = 99
  "b" = 2
}
> concat(["a"], ["b", "c"])
tolist([
  "a",
  "b",
  "c",
])
> distinct(["a", "b", "a", "c"])
tolist([
  "a",
  "b",
  "c",
])
> toset(["a", "b", "a"])
toset([
  "a",
  "b",
])
```

Tres matices que merecen atención. Primero, `element` "da la vuelta" si el índice se pasa de largo: en una lista de 3 elementos, el índice 3 vuelve al 0 (aritmética modular); con una lista vacía, da error. Segundo, `index` hace lo contrario que `element`: le das el valor y te devuelve la posición (y falla si no existe). Tercero, `merge` fusiona mapas y, en caso de conflicto de claves, **gana el mapa de más a la derecha**.

### Filesystem (sistema de ficheros) y codificación

```text
> file("${path.module}/saludo.txt")
"Hola desde un fichero"
> jsonencode({nombre = "pablo", admin = true})
"{\"admin\":true,\"nombre\":\"pablo\"}"
```

`file()` lee el contenido de un fichero como cadena (el fichero debe existir **antes** de ejecutar Terraform; no sirve para leer ficheros que crea la propia configuración). `jsonencode()` convierte un valor HCL en una cadena JSON, imprescindible para políticas, configuraciones embebidas o APIs que esperan JSON.

### Tabla resumen

| Categoría | Funciones vistas | Para qué sirven |
|---|---|---|
| Numéricas | `max`, `min`, `ceil`, `floor`, `abs` | Cálculos y redondeos |
| Cadenas | `split`, `join`, `lower`, `upper`, `title`, `substr`, `replace` | Transformar texto |
| Colecciones | `length`, `index`, `element`, `contains`, `keys`, `values`, `lookup`, `merge`, `concat`, `distinct` | Manipular listas y mapas |
| Conversión de tipos | `toset` | Convertir lista en conjunto (elimina duplicados) |
| Filesystem | `file` | Leer ficheros del disco |
| Codificación | `jsonencode` | Generar JSON desde HCL |

### Un ejemplo completo en local

```hcl
# main.tf — practica con providers locales, sin cuenta cloud
variable "usuarios" {
  type        = string
  description = "Usuarios separados por comas (puede haber duplicados)"
  default     = "ana,juan,ana,lucia"
}

locals {
  # split convierte la cadena en lista; toset elimina duplicados
  lista_usuarios = toset(split(",", var.usuarios))
}

resource "local_file" "ficha" {
  for_each = local.lista_usuarios

  filename = "${path.module}/fichas/${lower(each.value)}.txt"
  content = jsonencode({
    nombre  = title(each.value)          # "ana" -> "Ana"
    inicial = upper(substr(each.value, 0, 1))
    total   = length(local.lista_usuarios)
  })
}

output "usuarios_procesados" {
  value = join(" | ", [for u in local.lista_usuarios : title(u)])
}
```

```text
$ terraform apply -auto-approve
...
Apply complete! Resources: 3 added, 0 changed, 0 destroyed.

Outputs:

usuarios_procesados = "Ana | Juan | Lucia"
```

Observa que aunque la variable traía cuatro nombres, `toset` dejó tres: los conjuntos no admiten duplicados.

> ⚠️ **Errores comunes:**
> - **Usar `lookup` sin tercer argumento.** Está desaprobado desde hace años: sin `default` equivale a `mapa[clave]` y falla si la clave no existe. Si la clave es opcional, pasa siempre un valor por defecto.
> - **Confundir `index` y `element`.** `index(lista, valor)` devuelve una posición; `element(lista, posicion)` devuelve un valor. Si los cruzas, obtendrás errores de tipo desconcertantes.
> - **Esperar que `element` falle con índices grandes.** No falla: envuelve con módulo. Si quieres un error ante un índice fuera de rango, usa la indexación nativa `lista[3]`.
> - **Olvidar que `length` cuenta cosas distintas según el tipo:** caracteres en una cadena, elementos en una lista, pares clave-valor en un mapa.

> 💡 **Buenas prácticas:**
> - **Prueba primero en `terraform console`** y pega la expresión en tu `.tf` solo cuando devuelva lo que esperas. Te ahorra ciclos de plan/apply.
> - **Extrae expresiones complejas a un bloque `locals`** con un nombre descriptivo, en lugar de anidar cinco funciones dentro de un argumento.
> - **Usa `mapa[clave]` cuando la clave deba existir sí o sí** (así el error salta pronto) y `lookup(mapa, clave, default)` cuando sea legítimamente opcional.

### 🧪 Laboratorio

**Enunciado:** crea una configuración que reciba la variable `equipos = "backend,frontend,backend,datos"` y genere un fichero `resumen.txt` que contenga, en una sola línea, los equipos **sin duplicados**, en **mayúsculas** y unidos por `" / "`. Añade un output `numero_equipos` con el total de equipos únicos. Antes de escribir el recurso, valida la expresión en `terraform console`.

**Solución paso a paso:**

1. Crea un directorio vacío con este `main.tf`:

```hcl
variable "equipos" {
  type    = string
  default = "backend,frontend,backend,datos"
}

locals {
  equipos_unicos = distinct(split(",", var.equipos))
}

resource "local_file" "resumen" {
  filename = "${path.module}/resumen.txt"
  content  = join(" / ", [for e in local.equipos_unicos : upper(e)])
}

output "numero_equipos" {
  value = length(local.equipos_unicos)
}
```

2. Ejecuta `terraform init` y valida la lógica en la consola:

```text
$ terraform console
> distinct(split(",", var.equipos))
tolist([
  "backend",
  "frontend",
  "datos",
])
> exit
```

3. Aplica y comprueba:

```text
$ terraform apply -auto-approve
Apply complete! Resources: 1 added, 0 changed, 0 destroyed.

Outputs:

numero_equipos = 3
```

El fichero `resumen.txt` contiene `BACKEND / FRONTEND / DATOS`. Aquí usé `distinct` (que devuelve lista y conserva el orden) en vez de `toset`; ambas eliminan duplicados, pero los conjuntos no garantizan orden.

> ❓ **Preguntas de repaso:**
> - **¿Puedes definir tus propias funciones en HCL?** No. Solo existen las funciones integradas y, desde Terraform 1.8, las que exponen los providers. La personalización se consigue combinando funciones, `locals` y módulos.
> - **¿Qué devuelve `element(["a", "b", "c"], 5)`?** Devuelve `"c"`: el índice se calcula módulo la longitud de la lista (5 % 3 = 2).
> - **¿Qué diferencia hay entre `lookup(m, "k", "x")` y `m["k"]`?** La primera devuelve `"x"` si la clave no existe; la segunda produce un error. Usa cada una según si la clave es opcional u obligatoria.

## 12.2 Operadores y expresiones condicionales

**¿Qué vas a aprender?** Aquí vas a repasar los operadores aritméticos, de comparación y lógicos de HCL, y a dominar la expresión condicional `condicion ? valor_si : valor_no`, la herramienta que permite que una misma configuración se comporte distinto según variables de entrada, entornos o resultados intermedios.

### Los operadores de HCL

HCL soporta los operadores que ya conoces de cualquier lenguaje. Puedes comprobarlos todos en `terraform console`:

```text
> 1 + 2          # aritméticos: + - * / %
3
> 9 / 2          # la división devuelve decimales, no trunca
4.5
> 10 % 3
1
> 8 == 8         # igualdad: == y !=
true
> 5 > 7          # comparación: < <= > >=
false
> 8 > 7 && 4 < 5 # lógicos: && (y), || (o), ! (negación)
true
> !true
false
```

Dos avisos para desarrolladores: la igualdad es `==` (usar `=` dentro de una expresión es un error de sintaxis, porque `=` es asignación de argumentos), y la división entre números enteros produce decimales (`9 / 2` es `4.5`, no `4`), porque en Terraform solo existe el tipo `number`.

### La expresión condicional

Terraform no tiene `if/else` como sentencia; en su lugar usa el **operador ternario**, idéntico al de JavaScript o C:

```hcl
condicion ? valor_si_verdadero : valor_si_falso
```

La analogía perfecta es la receta de cocina con plan B: "si tienes mantequilla, usa mantequilla; si no, usa aceite". La receta (tu configuración) es la misma; el ingrediente concreto se decide en el momento según lo que haya en la despensa (tus variables). Una regla importante: **ambos resultados deben ser del mismo tipo**, porque Terraform necesita saber qué tipo devuelve la expresión completa. Si mezclas tipos, Terraform intentará convertirlos automáticamente (por ejemplo, un número a cadena), pero la documentación oficial recomienda hacer la conversión explícita con funciones como `tostring()` para que no haya sorpresas.

### Ejemplo 1: imponer una longitud mínima

Un caso clásico: generar una contraseña cuya longitud nunca baje de un mínimo de seguridad, pida lo que pida el usuario.

```hcl
variable "longitud" {
  type        = number
  description = "Longitud deseada de la contraseña"
  default     = 5
}

resource "random_password" "app" {
  # Si piden menos de 12 caracteres, forzamos 12
  length  = var.longitud < 12 ? 12 : var.longitud
  special = true
}

output "longitud_real" {
  value = random_password.app.length
}
```

```text
$ terraform apply -auto-approve -var="longitud=5"
...
Outputs:

longitud_real = 12

$ terraform apply -auto-approve -var="longitud=20"
...
Outputs:

longitud_real = 20
```

### Ejemplo 2: dimensionar según el entorno

El ejemplo canónico en el mundo cloud es elegir el tamaño de instancia según el entorno: grande en producción, pequeño en desarrollo. Puedes practicar el patrón exacto en local sin tocar AWS:

```hcl
variable "entorno" {
  type    = string
  default = "dev"
}

locals {
  # En AWS esto sería el instance_type de un aws_instance:
  # instance_type = var.entorno == "prod" ? "t3.large" : "t3.micro"
  tamano = var.entorno == "prod" ? "t3.large" : "t3.micro"

  # Los condicionales también deciden CUÁNTAS copias crear
  replicas = var.entorno == "prod" ? 3 : 1
}

resource "local_file" "servidor" {
  count    = local.replicas
  filename = "${path.module}/servidores/servidor-${count.index}.txt"
  content  = "entorno=${var.entorno} tamano=${local.tamano}"
}
```

```text
$ terraform plan -var="entorno=prod"

Terraform will perform the following actions:

  # local_file.servidor[0] will be created
  # local_file.servidor[1] will be created
  # local_file.servidor[2] will be created

Plan: 3 to add, 0 to change, 0 to destroy.
```

Con `entorno=dev` el plan solo crearía un fichero. Este patrón —un condicional alimentando `count`— es además la forma idiomática de crear **recursos opcionales**: `count = var.crear_backup ? 1 : 0`.

Los operadores lógicos permiten condiciones compuestas:

```hcl
locals {
  # Alta disponibilidad solo en producción Y en la región europea
  alta_disponibilidad = var.entorno == "prod" && var.region == "eu" ? true : false
}
```

(De hecho, ese ternario es redundante: `var.entorno == "prod" && var.region == "eu"` ya devuelve un booleano por sí solo).

> ⚠️ **Errores comunes:**
> - **Mezclar tipos en las dos ramas** (`var.x ? "3" : 5`). Terraform puede convertir automáticamente, pero el tipo resultante quizá no sea el que esperas. Haz conversiones explícitas con `tostring()` o `tonumber()`.
> - **Escribir `=` en lugar de `==`** en la condición. Error de sintaxis inmediato, pero el mensaje puede despistar a un principiante.
> - **Comparar un número con una cadena** (`var.puerto == "80"` cuando `puerto` es `number`). Declara bien los tipos de tus variables y compara con el tipo correcto.
> - **Anidar ternarios sin piedad** (`a ? x : b ? y : z`). Funciona, pero es ilegible; a partir de dos casos, plantéate un mapa con `lookup`.

> 💡 **Buenas prácticas:**
> - **Mueve los condicionales a `locals`** con nombres expresivos (`local.replicas`, `local.tamano`): la intención queda documentada y reutilizas el valor.
> - **Para más de dos opciones, usa un mapa + `lookup`** en lugar de encadenar ternarios: escala mejor y se lee de un vistazo.
> - **Recuerda el patrón `count = condicion ? 1 : 0`** para recursos opcionales: es de los más usados en módulos reales.

### 🧪 Laboratorio

**Enunciado (equivalente al lab "Functions and Conditional Expressions" del curso):** crea una configuración con una variable `entorno` (por defecto `"dev"`) y una variable `longitud` (por defecto `8`). Genera con `random_password` una contraseña cuya longitud sea la pedida, pero **nunca inferior a 16 si el entorno es `prod`**. Escribe la contraseña en un fichero cuyo nombre sea `credenciales-<entorno>.txt`. Comprueba ambos entornos.

**Solución paso a paso:**

1. `main.tf`:

```hcl
variable "entorno" {
  type    = string
  default = "dev"
}

variable "longitud" {
  type    = number
  default = 8
}

locals {
  # En prod exigimos un mínimo de 16; en el resto, lo que pidan
  longitud_final = var.entorno == "prod" && var.longitud < 16 ? 16 : var.longitud
}

resource "random_password" "credencial" {
  length  = local.longitud_final
  special = false
}

resource "local_file" "credenciales" {
  filename        = "${path.module}/credenciales-${var.entorno}.txt"
  content         = random_password.credencial.result
  file_permission = "0600" # solo lectura/escritura para el propietario
}

output "longitud_aplicada" {
  value = local.longitud_final
}
```

2. Prueba en desarrollo (respeta los 8 caracteres pedidos):

```text
$ terraform init && terraform apply -auto-approve
...
Outputs:

longitud_aplicada = 8
```

3. Prueba en producción (fuerza el mínimo):

```text
$ terraform apply -auto-approve -var="entorno=prod"
...
Outputs:

longitud_aplicada = 16
```

Verifica que existen `credenciales-dev.txt` y `credenciales-prod.txt`, cada uno con su contraseña.

> ❓ **Preguntas de repaso:**
> - **¿Qué devuelve `9 / 2` en Terraform?** `4.5`. HCL tiene un único tipo numérico y la división no trunca.
> - **¿Por qué las dos ramas de un ternario deben ser del mismo tipo?** Porque Terraform necesita determinar el tipo de la expresión completa en tiempo de plan. Si difieren, intenta una conversión automática que conviene evitar haciendo la conversión explícita.
> - **¿Cómo crearías un recurso solo cuando `var.debug` sea `true`?** Con `count = var.debug ? 1 : 0` en el bloque del recurso.

## 12.3 Workspaces

**¿Qué vas a aprender?** En esta lección descubrirás los **workspaces de la CLI de Terraform**: qué son, cómo permiten reutilizar una misma configuración para varios entornos con estados independientes, cómo se gestionan (`new`, `list`, `select`, `show`), dónde guarda Terraform cada estado y —tan importante como lo anterior— cuándo NO conviene usarlos.

### Un código, muchos estados

Imagina que quieres el mismo conjunto de recursos para desarrollo y para producción. Podrías copiar el directorio entero... y mantener dos copias del código para siempre. Los workspaces resuelven esto: **una única configuración con varios ficheros de estado**, uno por workspace. La mejor analogía son los **perfiles de Netflix**: la aplicación es la misma para toda la familia (tu código HCL), pero cada perfil recuerda sus propias series y su progreso (su estado). Cambiar de workspace es cambiar de perfil: mismo código, memoria distinta.

Todo proyecto de Terraform tiene siempre al menos un workspace llamado `default`, que no se puede borrar. Si nunca has tocado los workspaces, has estado trabajando en `default` sin saberlo.

### Los comandos

```text
$ terraform workspace list
* default

$ terraform workspace new dev
Created and switched to workspace "dev"!

You're now on a new, empty workspace. Workspaces isolate their state,
so if you run "terraform plan" Terraform will not see any existing state
for this configuration.

$ terraform workspace new prod
Created and switched to workspace "prod"!

$ terraform workspace list
  default
  dev
* prod

$ terraform workspace select dev
Switched to workspace "dev".

$ terraform workspace show
dev
```

En resumen: `new` crea (y selecciona), `list` enumera marcando el actual con `*`, `select` cambia, `show` muestra el actual y `delete` elimina un workspace (nunca `default`, y solo si su estado está vacío, salvo que fuerces con `-force`). Las versiones modernas de Terraform añaden además `terraform workspace select -or-create NOMBRE`, que crea el workspace si no existe antes de seleccionarlo, muy útil en scripts de CI.

### terraform.workspace: el nombre como valor

Dentro de la configuración dispones del valor `terraform.workspace`, que contiene el nombre del workspace activo. Combinado con `lookup`, es la pieza que hace que un mismo código se adapte a cada entorno:

```hcl
locals {
  # Configuración por entorno en un solo mapa
  replicas_por_entorno = {
    default = 1
    dev     = 1
    prod    = 3
  }

  replicas = lookup(local.replicas_por_entorno, terraform.workspace, 1)
}

resource "random_pet" "servidor" {
  # El prefijo delata a qué entorno pertenece cada recurso
  prefix = terraform.workspace
}

resource "local_file" "inventario" {
  count    = local.replicas
  filename = "${path.module}/inventario/${terraform.workspace}-${count.index}.txt"
  content  = "Servidor ${random_pet.servidor.id} del entorno ${terraform.workspace}"
}
```

En el workspace `dev` este código crea un fichero; en `prod`, tres, y todos los nombres llevan el entorno incorporado. Mismo `.tf`, resultados distintos.

### ¿Dónde vive cada estado?

Con el backend local, el estado del workspace `default` sigue siendo el `terraform.tfstate` de toda la vida, en la raíz del directorio de trabajo. Los demás workspaces guardan su estado en un directorio llamado **`terraform.tfstate.d`**, con un subdirectorio por workspace:

```text
$ tree -a
.
├── main.tf
├── terraform.tfstate            # estado del workspace "default"
└── terraform.tfstate.d
    ├── dev
    │   └── terraform.tfstate    # estado del workspace "dev"
    └── prod
        └── terraform.tfstate    # estado del workspace "prod"
```

Trata `terraform.tfstate.d` igual que tratarías `terraform.tfstate`: contiene información sensible y no debe subirse a Git.

### Cuándo usarlos... y cuándo no

Los workspaces brillan cuando necesitas **varias copias de una misma configuración dentro del mismo backend y con las mismas credenciales**: por ejemplo, levantar una copia temporal de la infraestructura para probar una rama antes de fusionarla. La propia documentación oficial es tajante con el caso contrario: los workspaces **no son un mecanismo adecuado** para separar entornos que exigen aislamiento fuerte, credenciales distintas o controles de acceso diferentes (el típico dev/prod serio, con cuentas cloud separadas). Para eso, usa configuraciones raíz separadas —idealmente compartiendo módulos— cada una con su propio backend. La razón es de sentido común: todos los workspaces comparten el mismo backend y las mismas credenciales, así que un error de permisos o un `apply` en el workspace equivocado puede tocar producción.

> 🔄 **Actualización:** no confundas los **workspaces de la CLI** (los de esta lección, también llamados a veces "OSS workspaces") con los **workspaces de HCP Terraform** (antes Terraform Cloud). Comparten nombre, pero los de HCP Terraform son entidades mucho más ricas: cada uno actúa como un directorio de trabajo completamente independiente, con sus propias variables, credenciales, permisos e historial de ejecuciones. La documentación actual de HashiCorp los trata como conceptos distintos; cuando leas "workspace" en un artículo, comprueba primero de cuál de los dos habla.

> ⚠️ **Errores comunes:**
> - **Ejecutar `apply` o `destroy` en el workspace equivocado.** Es EL accidente clásico. Ejecuta `terraform workspace show` antes de cualquier operación destructiva, o intégralo en el prompt de tu terminal.
> - **Usar workspaces para separar dev y prod "de verdad"** (con cuentas y credenciales distintas). No aíslan credenciales ni permisos; usa configuraciones y backends separados.
> - **Intentar borrar `default`.** No se puede. Y para borrar cualquier otro workspace su estado debe estar vacío (destruye antes los recursos) o tendrás que recurrir a `-force`, dejando recursos huérfanos.
> - **Olvidar que cada workspace nuevo nace con estado vacío:** el primer `plan` querrá crearlo todo de cero. Es lo esperado, no un bug.

> 💡 **Buenas prácticas:**
> - **Incluye `terraform.workspace` en los nombres de tus recursos** para evitar colisiones entre entornos y saber siempre a quién pertenece cada cosa.
> - **Centraliza las diferencias por entorno en mapas + `lookup`** dentro de `locals`, con `default` como clave de respaldo.
> - **En scripts de CI usa `terraform workspace select -or-create`** para que el pipeline no falle la primera vez que se ejecuta para un entorno nuevo.
> - **Añade `terraform.tfstate.d/` a tu `.gitignore`**, igual que `terraform.tfstate`.

### 🧪 Laboratorio

**Enunciado (equivalente al lab "terraform Workspaces" del curso):** partiendo de un directorio vacío, crea una configuración que genere un fichero `plan-<workspace>.txt` cuyo contenido indique el número de servidores del entorno: 1 en `dev`, 3 en `prod`, 1 en cualquier otro caso. Crea los workspaces `dev` y `prod`, aplica en ambos y comprueba que cada uno mantiene su propio estado en `terraform.tfstate.d`.

**Solución paso a paso:**

1. Crea `main.tf`:

```hcl
locals {
  servidores = lookup(
    {
      dev  = 1
      prod = 3
    },
    terraform.workspace,
    1 # valor por defecto para "default" o cualquier otro workspace
  )
}

resource "local_file" "plan" {
  filename = "${path.module}/plan-${terraform.workspace}.txt"
  content  = "Entorno ${terraform.workspace}: ${local.servidores} servidor(es)"
}

output "resumen" {
  value = local_file.plan.content
}
```

2. Inicializa, crea el workspace `dev` y aplica:

```text
$ terraform init
$ terraform workspace new dev
Created and switched to workspace "dev"!

$ terraform apply -auto-approve
...
Outputs:

resumen = "Entorno dev: 1 servidor(es)"
```

3. Crea `prod` y aplica de nuevo, sin tocar el código:

```text
$ terraform workspace new prod
Created and switched to workspace "prod"!

$ terraform apply -auto-approve
...
Outputs:

resumen = "Entorno prod: 3 servidor(es)"
```

4. Comprueba los estados independientes:

```text
$ terraform workspace list
  default
  dev
* prod

$ ls terraform.tfstate.d
dev  prod
```

Cada subdirectorio contiene su propio `terraform.tfstate`. Si vuelves con `terraform workspace select dev` y ejecutas `terraform plan`, verás `No changes`: el estado de `dev` recuerda su fichero y no sabe nada del de `prod`. Un código, dos memorias.

> ❓ **Preguntas de repaso:**
> - **¿Dónde guarda Terraform el estado del workspace `prod` con el backend local?** En `terraform.tfstate.d/prod/terraform.tfstate`. El workspace `default` usa el `terraform.tfstate` de la raíz.
> - **¿Es buena idea gestionar dev y prod con workspaces si cada entorno tiene su propia cuenta cloud?** No: los workspaces comparten backend y credenciales, y la documentación oficial desaconseja usarlos donde se necesita aislamiento fuerte. Usa configuraciones separadas con backends propios.
> - **¿Qué valor tiene `terraform.workspace` si nunca has creado ningún workspace?** `"default"`, el workspace inicial que existe siempre y no puede borrarse.

---

📌 **Recapitulando el módulo:** las funciones transforman datos, los condicionales toman decisiones y los workspaces multiplican una configuración en varios estados. Con estas tres piezas tu HCL deja de ser una lista estática de recursos y se convierte en código adaptable de verdad. En el próximo módulo seguiremos subiendo el nivel.
