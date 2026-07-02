## 6.5 Meta-argumentos

**¿Qué vas a aprender?** En esta lección descubrirás qué son los meta-argumentos: un pequeño grupo de argumentos especiales que Terraform pone a tu disposición en **cualquier** recurso, sea del provider que sea. Ya has usado alguno sin saberlo (`depends_on`, `lifecycle`); aquí les pondremos nombre de familia y prepararemos el terreno para los dos más potentes: `count` y `for_each`.

### Argumentos del recurso vs. argumentos del lenguaje

Cuando escribes un bloque `resource`, la mayoría de los argumentos los define el provider: `filename` y `content` existen porque el provider `local` los ha declarado para `local_file`. Pero hay unos pocos argumentos que **no pertenecen a ningún provider**, sino al propio lenguaje de Terraform, y por eso funcionan igual en un `local_file`, en una instancia de AWS o en un bucket de Google Cloud. Son los **meta-argumentos**, y no describen *qué es* el recurso, sino *cómo debe gestionarlo* Terraform.

Piensa en un pedido a domicilio: los ingredientes de la pizza (masa, tomate, queso) son los argumentos del recurso, distintos para cada plato. Pero las instrucciones del pedido —"tráeme 3 unidades", "entrégalo después de la bebida", "usa el local del centro"— valen para cualquier plato de la carta. Eso son los meta-argumentos.

Según la documentación oficial, los meta-argumentos disponibles en bloques `resource` son cinco:

| Meta-argumento | Qué controla |
|---|---|
| `depends_on` | Dependencias explícitas entre recursos |
| `count` | Crear N instancias casi idénticas, indexadas por número |
| `for_each` | Crear una instancia por cada elemento de un mapa o set |
| `provider` | Usar una configuración alternativa de provider (p. ej., otra región) |
| `lifecycle` | Reglas de ciclo de vida (`create_before_destroy`, `prevent_destroy`...) |

```hcl
# main.tf — dos meta-argumentos conviviendo con argumentos normales
resource "local_file" "datos" {
  filename = "datos.txt"          # argumento del provider "local"
  content  = "Datos de origen"
}

resource "local_file" "informe" {
  filename = "informe.txt"        # argumento del provider
  content  = "Informe generado"

  depends_on = [local_file.datos] # meta-argumento: dependencia explícita

  lifecycle {                     # meta-argumento: ciclo de vida
    create_before_destroy = true
  }
}
```

> 🔄 **Actualización:** cuando se grabó el curso (Terraform 0.13), `count` y `for_each` acababan de llegar a los bloques `module`. En el Terraform 1.x actual es algo totalmente asentado: los meta-argumentos funcionan tanto en recursos como en módulos y bloques `data`.

> ⚠️ **Errores comunes:**
> - Buscar `count` o `for_each` en la documentación del provider y no encontrarlos: no están ahí porque son del lenguaje, no del provider. Búscalos en la documentación del lenguaje de Terraform.
> - Intentar usar `count` **y** `for_each` en el mismo bloque: Terraform lo prohíbe expresamente y la validación fallará.
> - Confundir `provider` (meta-argumento, en singular, dentro del recurso) con el bloque `provider` de nivel superior donde configuras credenciales o región.

> 💡 **Buenas prácticas:**
> - Coloca los meta-argumentos siempre en el mismo sitio del bloque (al principio o al final) para que se distingan a simple vista de los argumentos del provider.
> - Usa `depends_on` solo cuando la dependencia no pueda expresarse con una referencia (`local_file.datos.filename`); las dependencias implícitas son más mantenibles.

### 🧪 Laboratorio

**Enunciado:** copia el ejemplo anterior en un directorio vacío y, sin ejecutar nada todavía, subraya qué argumentos son del provider y cuáles del lenguaje. Después ejecuta `terraform init`, `terraform validate` y `terraform apply` para comprobar que valida y crea ambos ficheros.

**Solución:** `filename` y `content` son del provider `local`; `depends_on` y `lifecycle` son meta-argumentos del lenguaje. Tras `terraform apply` verás `Apply complete! Resources: 2 added, 0 changed, 0 destroyed.` y los ficheros `datos.txt` e `informe.txt` en el directorio.

> ❓ **Preguntas de repaso:**
> - **¿Por qué `count` funciona igual con cualquier provider?** Porque es un meta-argumento: lo define el lenguaje de Terraform, no el provider.
> - **¿Puedes combinar `count` y `for_each` en el mismo recurso?** No; son mutuamente excluyentes y Terraform devuelve un error de validación.
> - **Nombra los cinco meta-argumentos de un recurso.** `depends_on`, `count`, `for_each`, `provider` y `lifecycle`.

## 6.6 count: crear varios recursos con un índice

**¿Qué vas a aprender?** Aprenderás a crear varias instancias de un recurso con un solo bloque gracias a `count`, a personalizar cada instancia con `count.index` y a dimensionarlo dinámicamente con `length()`. También verás, paso a paso, el problema clásico de `count` con listas: por qué borrar un elemento intermedio provoca que Terraform destruya recursos que no querías tocar.

### El problema: repetir bloques a mano

Imagina que necesitas tres ficheros. Sin `count`, escribirías tres bloques `resource` casi idénticos: código duplicado y difícil de mantener. Con `count`, un solo bloque basta:

```hcl
# main.tf — tres instancias de un mismo recurso
resource "local_file" "pet" {
  count    = 3                          # crea 3 instancias: pet[0], pet[1], pet[2]
  filename = "pet-${count.index}.txt"   # count.index empieza en 0
  content  = "Soy la mascota número ${count.index}"
}
```

Cuando un recurso usa `count`, deja de ser un recurso único y se convierte en una **lista de instancias**. Ya no puedes referirte a `local_file.pet` a secas: tienes que usar el índice, como `local_file.pet[0]`, o toda la lista con la expresión *splat* `local_file.pet[*]` (el asterisco que representa "todos los elementos").

```text
$ terraform plan
  # local_file.pet[0] will be created
  # local_file.pet[1] will be created
  # local_file.pet[2] will be created

Plan: 3 to add, 0 to change, 0 to destroy.
```

### Dimensionar count con una variable de lista

Lo habitual no es un número fijo, sino derivar el tamaño de una lista con la función `length()`:

```hcl
# variables.tf
variable "filenames" {
  type    = list(string)
  default = ["pets.txt", "dogs.txt", "cats.txt"]
}
```

```hcl
# main.tf
resource "local_file" "pet" {
  count    = length(var.filenames)        # 3 elementos -> 3 instancias
  filename = var.filenames[count.index]   # cada instancia toma su elemento
  content  = "Fichero gestionado por Terraform"
}
```

Así, añadir un cuarto nombre a la lista crea un cuarto fichero sin tocar el bloque. Un detalle importante de la documentación oficial: el valor de `count` **debe conocerse en tiempo de plan**; no puede depender de atributos que solo se conocen tras el apply.

### El problema del índice: cuando borrar uno destruye dos

Aquí viene la trampa. Con `count`, la **identidad** de cada instancia es su posición: `pet[0]`, `pet[1]`, `pet[2]`. Es como una cola numerada del supermercado: si la persona del turno 2 se marcha, todos los de detrás cambian de número. Para Terraform, "cambiar de número" significa que la instancia ya no coincide con lo guardado en el estado y hay que recrearla.

Veámoslo paso a paso. Estado inicial tras el apply:

- `local_file.pet[0]` → `pets.txt`
- `local_file.pet[1]` → `dogs.txt`
- `local_file.pet[2]` → `cats.txt`

Ahora eliminas `"dogs.txt"` de la lista, que queda en `["pets.txt", "cats.txt"]`. Tú esperarías que Terraform borre solo `dogs.txt`. Pero al recalcular índices, `cats.txt` pasa a ocupar la posición 1, y la posición 2 desaparece:

```text
$ terraform plan
  # local_file.pet[1] must be replaced
-/+ resource "local_file" "pet" {
      ~ filename = "dogs.txt" -> "cats.txt" # forces replacement
        ...
    }

  # local_file.pet[2] will be destroyed
  - resource "local_file" "pet" {
      - filename = "cats.txt" -> null
        ...
    }

Plan: 1 to add, 0 to change, 2 to destroy.
```

Querías eliminar **un** fichero y Terraform va a destruir **dos** y crear uno: `pet[1]` se reemplaza (de `dogs.txt` a `cats.txt`) y `pet[2]` se destruye. Con ficheros locales es inofensivo; con bases de datos en producción, es un incidente. Este desplazamiento de índices es la razón de ser de `for_each`, que verás en la siguiente lección.

> ⚠️ **Errores comunes:**
> - Referenciar `local_file.pet.filename` cuando el recurso usa `count`: obtendrás un error porque ahora es una lista; usa `local_file.pet[0].filename` o la expresión *splat* `local_file.pet[*].filename`.
> - Escribir `count = length(filenames)` olvidando el prefijo `var.`: las variables siempre se referencian como `var.nombre`.
> - Eliminar o reordenar elementos intermedios de la lista sin revisar el plan: lee siempre la línea `Plan:` antes de aplicar y sospecha de cualquier `must be replaced` inesperado.
> - Basar `count` en un atributo que solo se conoce tras el apply: Terraform exige conocer el valor durante el plan.

> 💡 **Buenas prácticas:**
> - Reserva `count` para instancias **realmente intercambiables** (N réplicas idénticas) o como interruptor condicional (`count = var.crear ? 1 : 0`).
> - Si cada instancia tiene identidad propia (un nombre, una configuración distinta), usa `for_each` desde el principio.
> - Tras cambiar una lista usada con `count`, ejecuta `terraform plan` y verifica que el número de destrucciones coincide con tu intención.

### 🧪 Laboratorio

**Enunciado:** en un directorio nuevo, crea la variable `filenames` con `["pets.txt", "dogs.txt", "cats.txt"]` y el recurso `local_file.pet` con `count`. Aplica, comprueba con `terraform state list` las tres instancias, elimina `"dogs.txt"` de la lista y analiza el plan resultante. ¿Cuántos recursos se destruyen?

**Solución paso a paso:**
1. Crea `variables.tf` y `main.tf` con el código de la sección anterior.
2. `terraform init` y `terraform apply` (confirma con `yes`). Salida: `Resources: 3 added`.
3. `terraform state list` muestra:
   ```text
   local_file.pet[0]
   local_file.pet[1]
   local_file.pet[2]
   ```
4. Edita el `default` de la variable dejando `["pets.txt", "cats.txt"]`.
5. `terraform plan` muestra `Plan: 1 to add, 0 to change, 2 to destroy.`: se destruyen **dos** instancias (`pet[1]` reemplazada y `pet[2]` eliminada) aunque solo querías quitar un fichero. Ese es el problema del índice.

> ❓ **Preguntas de repaso:**
> - **¿Qué valor toma `count.index` en la primera instancia?** `0`; los índices empiezan en cero.
> - **¿Por qué eliminar un elemento intermedio de la lista recrea recursos?** Porque la identidad de cada instancia es su posición en la lista; al desplazarse los índices, las instancias dejan de coincidir con su estado y Terraform las reemplaza.
> - **¿Cómo harías que el número de instancias siga automáticamente al tamaño de una lista?** Con `count = length(var.lista)`.

## 6.7 for_each: crear recursos a partir de mapas y conjuntos

**¿Qué vas a aprender?** Vas a dominar `for_each`, el meta-argumento que crea una instancia por cada elemento de un **mapa** o un **set de cadenas**, identificada por clave en lugar de por posición. Entenderás `each.key` y `each.value`, la conversión con `toset()`, y por qué `for_each` elimina de raíz el problema de los índices de `count`.

### Identidad por clave, no por posición

Si `count` es una cola numerada, `for_each` es un **guardarropa con etiquetas**: cada abrigo cuelga de una percha con el nombre de su dueño. Da igual cuántos abrigos entren o salgan; el tuyo sigue en la percha "Pablo". Con `for_each`, cada instancia se identifica por su clave —`local_file.pet["cats.txt"]`—, así que eliminar un elemento solo afecta a ese elemento.

`for_each` acepta dos tipos de valor: un **mapa** o un **set de cadenas** (las listas no valen directamente; se convierten con `toset()`). Dentro del bloque dispones del objeto `each`:

- `each.key`: la clave del mapa o el miembro del set.
- `each.value`: el valor del mapa (con sets, es idéntico a `each.key`).

```hcl
# main.tf — for_each sobre un set construido desde una lista
variable "filenames" {
  type    = list(string)
  default = ["pets.txt", "dogs.txt", "cats.txt"]
}

resource "local_file" "pet" {
  for_each = toset(var.filenames)  # lista -> set de cadenas
  filename = each.value            # con sets, each.value == each.key
  content  = "Fichero gestionado por Terraform"
}
```

Y con un mapa puedes dar a cada instancia datos distintos, no solo el nombre:

```hcl
# main.tf — for_each sobre un mapa: clave = fichero, valor = contenido
variable "files" {
  type = map(string)
  default = {
    "pets.txt" = "Me encantan los animales"
    "dogs.txt" = "Los perros son geniales"
    "cats.txt" = "Los gatos mandan en casa"
  }
}

resource "local_file" "pet" {
  for_each = var.files
  filename = each.key    # la clave del mapa
  content  = each.value  # el valor asociado
}
```

### La prueba de fuego: eliminar un elemento

Repite el experimento de la lección anterior: aplica el ejemplo del set y luego borra `"dogs.txt"` de la lista.

```text
$ terraform plan
  # local_file.pet["dogs.txt"] will be destroyed
  - resource "local_file" "pet" {
      - filename = "dogs.txt" -> null
        ...
    }

Plan: 0 to add, 0 to change, 1 to destroy.
```

Exactamente lo que querías: una destrucción y cero daños colaterales. `pets.txt` y `cats.txt` ni se mencionan, porque sus claves no han cambiado.

### ¿count o for_each? Tabla comparativa

| Aspecto | `count` | `for_each` |
|---|---|---|
| Entrada | Número entero | Mapa o set de cadenas |
| Identidad de la instancia | Posición: `pet[0]` | Clave: `pet["cats.txt"]` |
| Variable interna | `count.index` | `each.key` / `each.value` |
| Borrar un elemento intermedio | Desplaza índices y recrea recursos | Solo destruye ese elemento |
| Uso ideal | Réplicas idénticas; condicionales (`? 1 : 0`) | Instancias con identidad y datos propios |

La recomendación oficial va en la misma línea: usa `count` para instancias casi idénticas y `for_each` cuando algún argumento necesite valores distintos que no se deriven de un simple índice.

> ⚠️ **Errores comunes:**
> - Pasar una lista directamente a `for_each`: obtendrás un error de tipo (`The given "for_each" argument value is unsuitable`). Conviértela con `toset(var.lista)`.
> - Usar valores sensibles (variables `sensitive`, atributos sensibles) como claves: está prohibido porque Terraform muestra las claves en la salida del plan.
> - Referenciar la instancia con índice numérico (`pet[0]`) cuando usas `for_each`: la dirección correcta lleva la clave entre comillas, `pet["pets.txt"]`.
> - Construir claves con funciones impuras como `uuid()` o `timestamp()`: las claves deben conocerse en tiempo de plan y ser estables.

> 💡 **Buenas prácticas:**
> - Ante la duda, elige `for_each`: un plan que dice `pet["cats.txt"] will be destroyed` es infinitamente más legible que `pet[2] must be replaced`.
> - Elige claves estables y descriptivas (nombres, no números ni valores que cambien con el tiempo).
> - Para migrar un recurso existente de `count` a `for_each` sin destruirlo, en producción se renombran las instancias en el estado con `terraform state mv` (o con bloques `moved`).

### 🧪 Laboratorio

**Enunciado:** partiendo del laboratorio de 6.6 (versión con `count` ya aplicada y la lista completa de tres ficheros), migra el recurso a `for_each` con `toset()`, aplica, y repite la eliminación de `"dogs.txt"`. Compara el plan con el que obtuviste usando `count`.

**Solución paso a paso:**
1. Restaura la lista a `["pets.txt", "dogs.txt", "cats.txt"]` y sustituye en `main.tf` las líneas de `count` por `for_each = toset(var.filenames)` y `filename = each.value`.
2. `terraform apply`: como cambian las direcciones (de `pet[0]` a `pet["pets.txt"]`), Terraform destruirá las instancias indexadas y creará las nuevas con clave. En este ejercicio local es aceptable; en producción usarías `terraform state mv`.
3. `terraform state list` ahora muestra:
   ```text
   local_file.pet["cats.txt"]
   local_file.pet["dogs.txt"]
   local_file.pet["pets.txt"]
   ```
4. Elimina `"dogs.txt"` de la lista y ejecuta `terraform plan`: `Plan: 0 to add, 0 to change, 1 to destroy.` Frente al `1 to add, 2 to destroy` de `count`, la mejora es evidente.

> ❓ **Preguntas de repaso:**
> - **¿Qué tipos acepta `for_each`?** Un mapa o un set de cadenas; las listas deben convertirse con `toset()`.
> - **¿Qué contiene `each.value` cuando iteras sobre un set?** Lo mismo que `each.key`: el propio miembro del set.
> - **¿Por qué `for_each` no sufre el problema del desplazamiento de índices?** Porque cada instancia se identifica por una clave única y estable, no por su posición en una secuencia.

## 6.8 Restricciones de versión

**¿Qué vas a aprender?** Terraform, los providers y los módulos evolucionan por separado, y una versión nueva puede romper tu configuración. Aquí aprenderás a controlar qué versiones se usan mediante los operadores de restricción (`=`, `!=`, `>`, `<`, `>=`, `<=`, `~>`) en `required_providers` y `required_version`, y las buenas prácticas de *pinning* (fijar una versión concreta o un rango estrecho para que no cambie sola) para que tu infraestructura sea reproducible.

### Por qué fijar versiones

Por defecto, `terraform init` instala **la versión más reciente** de cada provider. Hoy funciona; dentro de seis meses, la versión más reciente puede haber renombrado un argumento y tu `terraform plan` fallará sin que hayas tocado una línea. Fijar versiones es como dar la lista de la compra con marca y formato exactos: "leche desnatada de la marca X, brik de litro". Si dejas solo "leche", cada día puede volver a casa una cosa distinta.

Las restricciones se declaran en el bloque `terraform`:

```hcl
# terraform.tf — versiones del CLI y de los providers
terraform {
  required_version = ">= 1.5.0"        # versión mínima del binario de Terraform

  required_providers {
    local = {
      source  = "hashicorp/local"      # dirección en el Registry
      version = "~> 2.4"               # 2.4, 2.5, 2.10... pero nunca 3.0
    }
    random = {
      source  = "hashicorp/random"
      version = ">= 3.5.0, < 4.0.0"    # varias condiciones separadas por comas
    }
  }
}
```

`required_version` restringe la versión del **CLI de Terraform** (no la de los providers): si tu binario no cumple la restricción, Terraform imprime un error y se detiene sin ejecutar ninguna acción.

### Los operadores, uno a uno

| Operador | Ejemplo | Significado |
|---|---|---|
| `=` (o nada) | `version = "2.4.0"` | Exactamente la 2.4.0, ninguna otra |
| `!=` | `version = "!= 2.4.1"` | Cualquiera excepto la 2.4.1 (útil si una versión concreta tiene un fallo conocido) |
| `>` | `version = "> 2.1.0"` | Posterior a la 2.1.0, sin incluirla |
| `>=` | `version = ">= 2.1.0"` | La 2.1.0 o posterior |
| `<` | `version = "< 3.0.0"` | Anterior a la 3.0.0, sin incluirla |
| `<=` | `version = "<= 2.5.2"` | La 2.5.2 o anterior |
| `~>` | `version = "~> 2.4.0"` | Solo puede crecer el último componente: 2.4.1, 2.4.9... pero no 2.5.0 |

El operador estrella es `~>`, el **operador pesimista**: permite incrementar únicamente el componente situado más a la derecha. Ojo al matiz: `~> 2.4.0` acepta 2.4.5 pero no 2.5.0, mientras que `~> 2.4` acepta 2.5 y 2.10 pero no 3.0. Es la forma compacta de decir "parches sí, sorpresas no". Un detalle fino de la documentación: las versiones *prerelease* (versiones preliminares o de prueba, como `3.0.0-beta1`) solo se seleccionan indicando la versión exacta con `=` (o sin operador); los operadores de comparación las ignoran.

```text
$ terraform init
Initializing provider plugins...
- Finding hashicorp/local versions matching "~> 2.4"...
- Installing hashicorp/local v2.5.2...
- Installed hashicorp/local v2.5.2 (signed by HashiCorp)

Terraform has created a lock file .terraform.lock.hcl to record the provider
selections it made above. Include this file in your version control repository...
```

(La versión exacta instalada dependerá del momento en que lo ejecutes.)

> 🔄 **Actualización:** en la época del curso, la restricción `version` era el único freno. Desde Terraform 0.14 existe el **fichero de bloqueo** `.terraform.lock.hcl`: registra la versión exacta y los *checksums* (las huellas digitales que verifican que el fichero descargado no ha sido alterado) de cada provider seleccionado, y los siguientes `terraform init` reutilizan esa misma selección. Para actualizar dentro de lo que permita tu restricción, ejecuta `terraform init -upgrade`. La documentación oficial recomienda **incluir el lock file en el control de versiones** (subirlo al repositorio junto con el resto del código).

> ⚠️ **Errores comunes:**
> - No declarar ninguna versión: `init` instalará siempre la última, y una versión *major* (una versión mayor, del tipo 1.0 a 2.0, que puede incluir cambios incompatibles) puede romper la configuración meses después sin previo aviso.
> - Confundir `~> 2.4` con `~> 2.4.0`: la primera permite saltar a 2.5 o 2.10; la segunda se queda en la serie 2.4.x. Elige conscientemente.
> - Añadir `.terraform.lock.hcl` al `.gitignore`: perderías la reproducibilidad entre compañeros y entornos de CI.
> - Olvidar que `required_version` solo afecta al CLI: para los providers, la restricción va en `required_providers`.

> 💡 **Buenas prácticas:**
> - En configuraciones raíz (las que aplicas directamente), usa `~>` para acotar por abajo y por arriba, y apóyate en el lock file para la reproducibilidad exacta.
> - En módulos reutilizables, declara solo mínimos (`>= 1.5.0`) para no imponer topes artificiales a quien consuma el módulo.
> - Al depender de módulos de terceros, fija la versión exacta; con módulos internos bien versionados puedes permitir rangos.
> - Actualiza versiones de forma deliberada: cambia la restricción, ejecuta `terraform init -upgrade`, revisa el plan y sube el lock file al repositorio junto al cambio.

### 🧪 Laboratorio

**Enunciado:** crea una configuración local que (1) exija una versión de Terraform imposible para provocar el error, (2) se corrija, y (3) fije el provider `local` a la serie 2.x con `~>`. Observa el lock file y prueba `terraform init -upgrade`.

**Solución paso a paso:**
1. Crea `main.tf` con `required_version = "< 1.0.0"` dentro del bloque `terraform`, más un recurso `local_file` cualquiera.
2. Ejecuta `terraform init` o `terraform plan`:
   ```text
   │ Error: Unsupported Terraform Core version
   │
   │ This configuration does not support Terraform version 1.9.x...
   ```
   Terraform se niega a continuar: eso es exactamente lo que buscas en un equipo, fallar pronto y con un mensaje claro.
3. Cambia la restricción a `required_version = ">= 1.5.0"` y añade en `required_providers` el provider `local` con `source = "hashicorp/local"` y `version = "~> 2.4"`.
4. `terraform init`: se instala una versión 2.x igual o posterior a la 2.4 y aparece `.terraform.lock.hcl`. Ábrelo y localiza la línea `version = ...` con la selección exacta y sus checksums.
5. Ejecuta `terraform init -upgrade`: Terraform ignora la selección previa del lock y vuelve a buscar la versión más reciente que cumpla `~> 2.4`, actualizando el lock file si procede.

> ❓ **Preguntas de repaso:**
> - **¿Qué versiones acepta `version = "~> 1.2"`?** La 1.2 y cualquier 1.x posterior (1.3, 1.10...), pero nunca la 2.0: solo puede crecer el componente más a la derecha.
> - **¿Qué diferencia hay entre `required_version` y el `version` de `required_providers`?** El primero restringe la versión del CLI de Terraform; el segundo, la de cada provider.
> - **¿Para qué sirve `.terraform.lock.hcl` y qué haces con él?** Registra la versión exacta y los checksums de los providers seleccionados para que los `init` futuros repitan la misma selección; debe incluirse en el control de versiones.
