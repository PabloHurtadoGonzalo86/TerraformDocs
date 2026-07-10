---
title: "Módulo 6 · Trabajando con Terraform"
description: "Comandos esenciales, infraestructura mutable vs inmutable, lifecycle, data sources, meta-argumentos, count, for_each y restricciones de versión."
---

Hasta ahora has escrito configuraciones y las has aplicado con el trío `init`, `plan` y `apply`. En este módulo vas a dar un salto de calidad: conocerás el resto de comandos que usarás a diario, entenderás la filosofía de **infraestructura inmutable** que explica por qué Terraform a veces destruye y recrea recursos, aprenderás a modular ese comportamiento con las **reglas de ciclo de vida**, y descubrirás los **data sources**, la puerta para leer información que Terraform no gestiona. Todo el módulo se practica en local con los providers `local` y `random`, sin necesidad de una cuenta en la nube (salvo un ejemplo ilustrativo de AWS en 6.4).

## 6.1 Comandos esenciales de Terraform

**¿Qué vas a aprender?** En esta lección vas a ampliar tu caja de herramientas más allá de `init`, `plan` y `apply`: aprenderás a validar y formatear tu código, a inspeccionar el estado y el plan, a listar providers, a consultar outputs, a sincronizar el estado con la realidad y a dibujar el grafo de dependencias de tu configuración.

Piensa en tu configuración de Terraform como en un documento importante que vas a entregar. Antes de entregarlo pasas el corrector ortográfico (`validate`), lo maquetas con un estilo uniforme (`fmt`), relees la versión final (`show`), revisas la bibliografía que has citado (`providers`), extraes el resumen ejecutivo (`output`), compruebas que lo que dice el documento sigue coincidiendo con la realidad (`apply -refresh-only`) y, si el documento es complejo, dibujas un mapa mental de cómo se relacionan sus partes (`graph`). Cada comando tiene su momento; veámoslos uno a uno.

### terraform validate: ¿es correcta mi configuración?

`terraform validate` comprueba que tus ficheros `.tf` son **sintácticamente válidos e internamente coherentes**: nombres de argumentos correctos, tipos de valores adecuados, referencias que existen. Necesita un directorio inicializado (si no quieres configurar el backend, te vale `terraform init -backend=false`). Ojo: **no** contacta con APIs remotas ni valida el estado remoto; para eso ya está `terraform plan`, que incluye una validación implícita.

```text
$ terraform validate
Success! The configuration is valid.
```

Si te equivocas en un argumento (por ejemplo, escribes `filenme` en vez de `filename`), te lo dirá con línea y fichero exactos:

```text
$ terraform validate
╷
│ Error: Unsupported argument
│
│   on main.tf line 3, in resource "local_file" "saludo":
│    3:   filenme = "saludo.txt"
│
│ An argument named "filenme" is not expected here.
╵
```

### terraform fmt: estilo canónico sin discusiones

`terraform fmt` reescribe tus ficheros con el formato canónico de HCL: indentación, alineado de `=`, espaciado. Es deliberadamente **no configurable**: así todos los proyectos de Terraform del mundo se leen igual. Por defecto actúa solo sobre el directorio actual e imprime los nombres de los ficheros que ha modificado. Flags útiles (un *flag* es una opción que modifica el comportamiento de un comando): `-recursive` (baja a subdirectorios), `-check` (no escribe, devuelve código de salida distinto de 0 si hay ficheros mal formateados: perfecto para la integración continua o CI) y `-diff` (muestra qué cambiaría).

```text
$ terraform fmt
main.tf
```

### terraform show: inspeccionar estado y planes

`terraform show` muestra en formato legible el **último snapshot (instantánea) del estado** o, si le pasas la ruta de un fichero de plan guardado (`terraform plan -out=plan.tfplan`), el contenido de ese plan. Con `-json` obtienes una salida legible por máquina, ideal para integrar con herramientas como `jq`. Cuidado: con `-json`, **los valores sensibles del estado se muestran en texto plano**.

```text
$ terraform show
# local_file.saludo:
resource "local_file" "saludo" {
    content              = "¡Hola, Pablo!"
    content_md5          = "0d5f6...."
    directory_permission = "0777"
    file_permission      = "0777"
    filename             = "saludo.txt"
    id                   = "a1b2c3d4e5..."
}
```

### terraform providers: ¿de quién depende mi proyecto?

`terraform providers` lista los requisitos de providers de la configuración del directorio actual y te ayuda a entender **de dónde sale cada requisito** (raíz, módulos hijos, estado). Tiene subcomandos avanzados: `providers lock` (gestiona el fichero de bloqueo de versiones), `providers mirror` (crea un espejo local de plugins para trabajar sin red) y `providers schema` (vuelca el esquema completo de los providers en JSON).

```text
$ terraform providers

Providers required by configuration:
.
├── provider[registry.terraform.io/hashicorp/local] ~> 2.5
└── provider[registry.terraform.io/hashicorp/random] ~> 3.7

Providers required by state:

    provider[registry.terraform.io/hashicorp/local]
    provider[registry.terraform.io/hashicorp/random]
```

### terraform output: consultar los valores de salida

`terraform output` lee del estado los valores de los bloques `output` del módulo raíz. Sin argumentos los muestra todos; con un nombre, solo ese. Para scripts tienes `-raw` (imprime el valor como cadena sin comillas ni formato; solo válido para strings, números y booleanos) y `-json` (para tipos complejos).

```text
$ terraform output
nombre_mascota = "eager-mole"

$ terraform output -raw nombre_mascota
eager-mole
```

### terraform apply -refresh-only: sincronizar con la realidad

Con el tiempo, la realidad puede divergir del estado (alguien borra un fichero, cambia una etiqueta a mano...). `terraform apply -refresh-only` detecta esas diferencias y te propone **actualizar solo el estado**, sin tocar la infraestructura, pidiéndote confirmación antes. Su hermano `terraform plan -refresh-only` solo te enseña la divergencia sin escribir nada.

> 🔄 **Actualización:** el comando clásico `terraform refresh` que se enseñaba en versiones antiguas del curso está **obsoleto** (*deprecated*, en la jerga). La documentación oficial recomienda usar `terraform apply -refresh-only` (o `terraform plan -refresh-only`) porque hacen lo mismo pero mostrándote los cambios detectados y pidiendo aprobación antes de escribirlos en el estado, en lugar de aplicarlos a ciegas.

### terraform graph: el mapa de dependencias

`terraform graph` imprime el grafo de dependencias de tu configuración en lenguaje **DOT**, el formato de la herramienta GraphViz. Para convertirlo en imagen necesitas tener instalado GraphViz (que aporta el ejecutable `dot`):

```text
$ terraform graph | dot -Tsvg > grafo.svg
$ terraform graph -type=plan | dot -Tpng > grafo.png
```

> 🔄 **Actualización:** en versiones antiguas, `terraform graph` mostraba por defecto un grafo enorme con nodos internos del plan. En Terraform moderno, la salida por defecto es un **grafo simplificado** que muestra solo el orden de dependencia entre bloques `resource` y `data`. Si quieres el grafo completo de una operación, usa `-type=plan`, `-type=plan-destroy`, `-type=plan-refresh-only` o `-type=apply`.

> ⚠️ **Errores comunes:**
> - Ejecutar `terraform validate` sin haber hecho `init` antes: fallará porque necesita los providers instalados. Usa `terraform init -backend=false` si solo quieres validar.
> - Creer que `validate` garantiza que el `apply` funcionará: no comprueba credenciales, cuotas ni APIs remotas. Un `validate` en verde puede acabar en un `apply` en rojo.
> - Usar `terraform output -raw` con un mapa o lista: da error. Para tipos complejos, usa `-json`.
> - Ejecutar `terraform graph | dot ...` sin GraphViz instalado: el error es del sistema (`dot: command not found`), no de Terraform. Instala GraphViz o pega la salida DOT en un visor online.

> 💡 **Buenas prácticas:**
> - Automatiza `terraform fmt -check` y `terraform validate` en tu pipeline de CI: son rápidos, seguros (no tocan infraestructura) y cazan errores antes del `plan`.
> - Acostúmbrate a `terraform plan -refresh-only` periódico en proyectos compartidos: es la forma barata de detectar drift sin riesgo.
> - Trata la salida de `terraform show -json` y `output -json` como material sensible: puede contener secretos en texto plano.

### 🧪 Laboratorio

**Enunciado:** crea un proyecto local con un nombre aleatorio de mascota y un fichero que lo use. Después: (1) formatea el código, (2) provoca y corrige un error de validación, (3) aplica, (4) inspecciona estado, providers y outputs, (5) simula drift borrando el fichero a mano y detéctalo con `-refresh-only`, y (6) genera el grafo.

**Solución paso a paso:**

1. Crea un directorio `lab-comandos` con este `main.tf` (fíjate en que la indentación está hecha aposta de cualquier manera):

```hcl
# main.tf — versión inicial, mal formateada a propósito
resource "random_pet" "mascota" {
      length = 2      # número de palabras del nombre
separator = "-"       # separador entre palabras
}

resource "local_file" "saludo" {
  filenme = "saludo.txt"                       # ¡typo intencionado!
  content = "Mi mascota se llama ${random_pet.mascota.id}"
}

output "nombre_mascota" {
  value = random_pet.mascota.id # nombre generado
}
```

2. Ejecuta `terraform fmt`: verás que imprime `main.tf` y deja la indentación perfecta.
3. Ejecuta `terraform init` y luego `terraform validate`: fallará con `Unsupported argument ... "filenme"`. Corrige el typo a `filename` y vuelve a validar hasta ver `Success! The configuration is valid.`
4. `terraform apply` y confirma con `yes`. Comprueba el resultado con `terraform show` (verás los dos recursos), `terraform providers` (verás `local` y `random`) y `terraform output -raw nombre_mascota`.
5. Borra el fichero a mano (`del saludo.txt` en Windows, `rm saludo.txt` en Linux/macOS) y ejecuta `terraform plan -refresh-only`: Terraform te dirá que `local_file.saludo` ha sido eliminado fuera de Terraform. Ejecuta después un `terraform apply` normal para recrearlo.
6. Genera el grafo: `terraform graph | dot -Tsvg > grafo.svg` y ábrelo en el navegador. Verás la flecha de dependencia de `local_file.saludo` hacia `random_pet.mascota`.

> ❓ **Preguntas de repaso:**
> 1. *¿Qué comprueba `terraform validate` y qué no comprueba?* — Comprueba sintaxis y coherencia interna (argumentos, tipos, referencias), pero no valida servicios remotos, credenciales ni el estado remoto.
> 2. *¿Cuál es el sucesor moderno de `terraform refresh` y por qué es más seguro?* — `terraform apply -refresh-only` (y `plan -refresh-only`): hace lo mismo, pero muestra los cambios detectados y pide confirmación antes de escribirlos en el estado.
> 3. *¿Qué necesitas para convertir la salida de `terraform graph` en una imagen?* — La herramienta GraphViz, cuyo comando `dot` convierte el lenguaje DOT en SVG, PNG, etc.

## 6.2 Infraestructura mutable vs inmutable

**¿Qué vas a aprender?** Aquí vas a entender una idea de fondo que explica gran parte del comportamiento de Terraform: la diferencia entre **modificar** infraestructura existente (enfoque mutable) y **reemplazarla** por una versión nueva (enfoque inmutable), qué es el *configuration drift* y por qué Terraform, por defecto, destruye y recrea un recurso cuando cambias ciertos atributos.

### Parches in-place: el enfoque mutable

Imagina que administras tres servidores web con nginx 1.17 y quieres subir a 1.18. El enfoque tradicional (mutable) es entrar en cada servidor y actualizar el software **in situ**: la máquina es la misma, pero su contenido cambia. Es como reformar una casa habitada: haces obra en la cocina sin mudarte. El problema es que cada reforma sale un poco distinta: en un servidor la actualización falla por una dependencia, en otro alguien instaló hace meses una herramienta "temporal" que sigue ahí... Con el tiempo, tres servidores que nacieron idénticos son tres copos de nieve únicos. A esa divergencia gradual entre la configuración que *crees* tener y la que *realmente* tienes se le llama **configuration drift** (deriva de configuración), y convierte cada incidencia en una investigación arqueológica.

### Reemplazo completo: el enfoque inmutable

El enfoque inmutable le da la vuelta: **nunca modificas un servidor en marcha; despliegas uno nuevo** con nginx 1.18 desde una plantilla conocida, compruebas que funciona y retiras el viejo. Es como las casas prefabricadas: si quieres otra cocina, la fábrica te entrega una casa nueva con esa cocina; la tuya no se toca. Ventajas: cada despliegue parte de un estado conocido y reproducible, el drift no se acumula, y volver atrás es tan fácil como volver a la plantilla anterior. Coste: reemplazar implica destruir y crear, con la interrupción o el tiempo que eso conlleve.

### Terraform es inmutable por defecto

Terraform abraza el enfoque inmutable: cuando cambias un atributo que el provider **no puede modificar in situ**, Terraform planifica **destruir el objeto y crear uno nuevo**. Cada provider declara qué argumentos son actualizables y cuáles "fuerzan reemplazo". Lo bonito es que puedes verlo en local sin ninguna nube: en el recurso `local_file`, *todos* los argumentos (`filename`, `content`, `file_permission`...) fuerzan reemplazo. Compruébalo:

```hcl
# main.tf — el fichero como recurso inmutable
resource "local_file" "receta" {
  filename = "receta.txt"
  content  = "Gazpacho v1" # cambia luego a "Gazpacho v2"
}
```

Aplica, cambia el `content` a `"Gazpacho v2"` y ejecuta `terraform plan`:

```text
  # local_file.receta must be replaced
-/+ resource "local_file" "receta" {
      ~ content  = "Gazpacho v1" -> "Gazpacho v2" # forces replacement
      ~ id       = "3f8e2..." -> (known after apply)
        filename = "receta.txt"
        # (resto de atributos sin cambios)
    }

Plan: 1 to add, 0 to change, 1 to destroy.
```

Fíjate en tres pistas: el símbolo `-/+` (destruir y crear), el comentario `# forces replacement` junto al atributo culpable, y el resumen `1 to add ... 1 to destroy`. Durante el `apply`, el orden por defecto es **primero destruir, luego crear** (*destroy-then-create*). En la siguiente lección verás cómo invertir ese orden cuando la interrupción no es aceptable.

> ⚠️ **Errores comunes:**
> - Aprobar un `apply` sin leer el plan y llevarse la sorpresa de que un recurso crítico se ha destruido y recreado. Busca siempre `-/+` y `forces replacement` antes de decir `yes`.
> - Confundir "Terraform es inmutable" con "Terraform nunca actualiza in situ": si el provider soporta modificar un atributo (p. ej. una etiqueta en AWS), el plan mostrará `~ update in-place`. El reemplazo solo ocurre cuando el atributo lo exige.
> - Hacer cambios manuales "rapiditos" sobre recursos gestionados por Terraform: acabas de fabricar drift. La herramienta lo detectará (y quizá lo revierta) en el siguiente plan.

> 💡 **Buenas prácticas:**
> - Antes de aplicar en algo importante, guarda el plan (`terraform plan -out=plan.tfplan`), revísalo con `terraform show plan.tfplan` y aplica exactamente ese fichero.
> - Diseña pensando en el reemplazo: nombres únicos o aleatorios (provider `random`), datos persistentes fuera del recurso reemplazable.
> - Institucionaliza la detección de drift con `terraform plan -refresh-only` periódico en vez de descubrirlo en mitad de un incidente.

### 🧪 Laboratorio

Esta lección no tiene laboratorio en el curso original, así que aquí va un mini-ejercicio. **Enunciado:** con el `main.tf` de la receta de arriba: (1) aplica la v1; (2) cambia `content` a `"Gazpacho v2"` y localiza en el plan el atributo que fuerza el reemplazo; (3) aplica y observa en la salida el orden destruir→crear. **Solución:** en el paso 2 verás `content ... # forces replacement` y `Plan: 1 to add, 0 to change, 1 to destroy`; en el paso 3 la salida muestra `local_file.receta: Destroying...` seguido de `local_file.receta: Creating...`, confirmando el orden por defecto.

> ❓ **Preguntas de repaso:**
> 1. *¿Qué es el configuration drift?* — La divergencia gradual entre la configuración documentada/esperada de la infraestructura y su estado real, típica de los parches manuales in-place.
> 2. *¿Cómo indica el plan que un recurso será reemplazado?* — Con el prefijo `-/+`, la anotación `# forces replacement` en el atributo responsable y el texto `must be replaced`.
> 3. *¿En qué orden reemplaza Terraform por defecto?* — Primero destruye el objeto antiguo y después crea el nuevo (*destroy-then-create*).

## 6.3 Reglas de ciclo de vida (lifecycle)

**¿Qué vas a aprender?** El comportamiento por defecto de Terraform (destruir antes de crear, permitir destrucciones, corregir cualquier diferencia) no siempre es lo que necesitas. En esta lección aprenderás a ajustarlo con el meta-argumento `lifecycle` y sus tres reglas estrella: `create_before_destroy`, `prevent_destroy` e `ignore_changes`, con sus casos de uso y sus trampas.

El bloque `lifecycle` es como las cláusulas especiales de un contrato de alquiler: el contrato estándar vale para casi todos, pero a veces pactas condiciones particulares ("no se puede rescindir antes de un año", "el casero no tocará la decoración"). Se escribe **dentro** del bloque `resource` y, muy importante, **solo admite valores literales**: nada de variables ni expresiones, porque Terraform lo procesa demasiado pronto en el flujo.

### create_before_destroy: primero la casa nueva, luego la mudanza

Invierte el orden de reemplazo: Terraform **crea el sustituto antes de destruir el original**, minimizando el tiempo sin servicio. Es mudarte a la casa nueva antes de vender la vieja.

```hcl
resource "local_file" "web" {
  filename = "web-${random_pet.nombre.id}.txt" # nombre único: evita colisiones
  content  = "Contenido de la web"

  lifecycle {
    create_before_destroy = true # crear el nuevo objeto antes de destruir el viejo
  }
}

resource "random_pet" "nombre" {
  length = 2
}
```

**La trampa clásica:** si el recurso nuevo y el viejo comparten "identidad" (mismo nombre, misma ruta, mismo identificador único), chocan. Con `local_file` se ve de maravilla: si el `filename` no cambia, Terraform crea el fichero nuevo (escribe en la misma ruta) y después destruye el objeto viejo... **borrando esa misma ruta**. Resultado: te quedas sin fichero. En AWS pasa igual con recursos de nombre único (un IAM role, un bucket): la creación falla con "ya existe". La solución es que la identidad dependa de lo que cambia: sufijos aleatorios, `name_prefix`, etc. Otro detalle documentado: esta regla **se propaga automáticamente a las dependencias** del recurso; no puedes ponerla a `false` en un recurso del que dependa otro que la tenga a `true`.

### prevent_destroy: el candado

Con `prevent_destroy = true`, Terraform **rechaza cualquier plan que implique destruir ese objeto**, incluido un reemplazo. Es el candado para recursos irremplazables: bases de datos de producción, buckets con históricos.

```hcl
resource "local_file" "config_produccion" {
  filename = "config-prod.txt"
  content  = "no me borres"

  lifecycle {
    prevent_destroy = true # cualquier plan que me destruya, falla
  }
}
```

```text
$ terraform destroy
╷
│ Error: Instance cannot be destroyed
│
│   on main.tf line 1:
│    1: resource "local_file" "config_produccion" {
│
│ Resource local_file.config_produccion has lifecycle.prevent_destroy set,
│ but the plan calls for this resource to be destroyed. To avoid this error
│ and continue with the plan, either disable lifecycle.prevent_destroy or
│ reduce the scope of the plan using the -target flag.
╵
```

**La trampa:** el candado vive en la configuración, no en el estado. Si **eliminas el bloque `resource` entero** del código, la regla desaparece con él y el siguiente plan propondrá destruir el objeto sin protestar. Tampoco te protege de borrados hechos fuera de Terraform. Y tiene un coste: mientras esté activo, `terraform destroy` fallará para todo el directorio, lo que molesta en entornos desechables.

### ignore_changes: el pacto de no agresión

Por defecto, si el objeto real difiere de tu configuración, Terraform planifica corregirlo. Pero a veces **otro sistema legítimo** modifica ciertos atributos (un proceso que añade etiquetas, un autoescalador que ajusta capacidad). `ignore_changes` le dice a Terraform: "estos argumentos, ni mirarlos en las actualizaciones".

```hcl
resource "local_file" "notas" {
  filename = "notas.txt"
  content  = "contenido inicial" # se usará al CREAR; luego se ignorará

  lifecycle {
    # Lista de argumentos a ignorar (referencias sin comillas):
    ignore_changes = [content]
    # Alternativa extrema: ignore_changes = all  (ignora TODOS los argumentos)
  }
}
```

Matices verificados en la documentación: se aplica **solo a actualizaciones**, nunca a la creación (al crear, se usan todos los valores de la configuración); acepta una lista de referencias a argumentos del propio recurso, o la palabra clave `all`. **La trampa:** `ignore_changes = all` convierte el recurso en un zombi que Terraform crea pero ya no gestiona; y olvidar que tienes un `ignore_changes` puesto explica muchos "¿por qué no aplica mi cambio?" a las tres semanas.

> 🔄 **Actualización:** desde Terraform v1.2 el bloque `lifecycle` admite además `replace_triggered_by` (fuerza el reemplazo del recurso cuando cambia otro recurso o atributo referenciado; solo acepta direcciones de recursos, no variables) y los bloques de validación `precondition`/`postcondition`. El curso original no los cubre, pero conviene saber que existen.

> ⚠️ **Errores comunes:**
> - Usar `create_before_destroy` con recursos de identidad fija (mismo `filename`, mismo `name`): el nuevo colisiona con el viejo o, como en `local_file`, el "destroy" final se lleva por delante el objeto nuevo.
> - Confiar en `prevent_destroy` como protección absoluta: si borras el bloque de la configuración, la protección se va con él.
> - Intentar usar variables dentro de `lifecycle` (`prevent_destroy = var.es_produccion`): error; solo se admiten **valores literales**.
> - Poner `ignore_changes = all` "para que deje de molestar" y descubrir meses después que ese recurso lleva sin gestionarse desde entonces.

> 💡 **Buenas prácticas:**
> - Reserva `prevent_destroy` para recursos con datos irrecuperables, y documenta con un comentario por qué está ahí.
> - Con `create_before_destroy`, diseña identidades únicas (sufijos `random_pet`/`random_id`, `name_prefix` en AWS) para que viejo y nuevo convivan.
> - En `ignore_changes`, ignora la lista mínima de argumentos concretos; evita `all` salvo casos muy justificados y comentados.

### 🧪 Laboratorio

**Enunciado:** en un directorio nuevo: (1) demuestra la trampa de `create_before_destroy` con `local_file` y arréglala; (2) protege un fichero con `prevent_destroy` y comprueba el error; (3) usa `ignore_changes` para que un cambio de `content` en el código no genere cambios.

**Solución paso a paso:**

1. Crea y aplica esto:

```hcl
resource "local_file" "demo" {
  filename = "demo.txt"
  content  = "version 1"

  lifecycle {
    create_before_destroy = true
  }
}
```

Cambia `content` a `"version 2"` y aplica. El plan muestra `+/-` (crear antes de destruir). Al terminar... ¡`demo.txt` no existe! Terraform escribió el fichero nuevo y después, al destruir el objeto antiguo, borró la misma ruta. **Arreglo:** haz que la identidad cambie con el contenido, por ejemplo `filename = "demo-${md5(var.contenido)}.txt"` o con un sufijo de `random_pet` ligado al contenido mediante `keepers`. Vuelve a aplicar y verifica que ahora el fichero nuevo sobrevive.

2. Añade a otro recurso `lifecycle { prevent_destroy = true }`, aplica, y lanza `terraform destroy`: obtendrás `Error: Instance cannot be destroyed`. Comenta la regla y el destroy volverá a funcionar.

3. Crea un recurso con `ignore_changes = [content]`, aplica, cambia el `content` en el código y ejecuta `terraform plan`:

```text
No changes. Your infrastructure matches the configuration.
```

Terraform ignora la diferencia en `content`, exactamente lo pactado.

> ❓ **Preguntas de repaso:**
> 1. *¿Qué orden de operaciones impone `create_before_destroy` y qué requisito práctico tiene?* — Crear el sustituto antes de destruir el original; requiere que ambos puedan coexistir, es decir, identidades (nombres/rutas) que no colisionen.
> 2. *¿Te protege `prevent_destroy` si eliminas el bloque `resource` del código?* — No: la regla desaparece junto con el bloque, y el siguiente plan propondrá la destrucción.
> 3. *¿`ignore_changes` afecta a la creación del recurso?* — No; solo a las actualizaciones. Al crear, Terraform usa todos los valores de la configuración.

## 6.4 Data sources: leer datos externos

**¿Qué vas a aprender?** No todo lo que necesita tu configuración lo ha creado Terraform. En esta lección aprenderás a usar el bloque `data` para **leer** información definida fuera de tu configuración —un fichero creado a mano, una AMI publicada por Canonical, un recurso creado por otro equipo— y a distinguirlo con claridad del bloque `resource`.

La analogía es la biblioteca: un `resource` es como ser el **autor** de un libro: lo escribes, lo corriges y puedes retirarlo de circulación. Un `data source` es el **carnet de solo lectura**: entras, consultas el libro que necesitas y usas lo aprendido, pero no puedes cambiar ni una coma. Terraform lee los data sources durante la fase de plan/refresh (y lo pospone al apply solo si dependen de valores aún no conocidos), y jamás los crea, modifica ni destruye.

### El bloque data con local_file

Supón que un proceso externo (u otra persona) deja un fichero `mascota-favorita.txt` en tu directorio y tú quieres usar su contenido:

```hcl
# El fichero lo creó alguien fuera de Terraform; nosotros solo lo leemos.
data "local_file" "favorita" {
  filename = "mascota-favorita.txt" # único argumento; error si no existe
}

# Y usamos lo leído en un recurso nuestro:
resource "local_file" "informe" {
  filename = "informe.txt"
  content  = "La mascota favorita es: ${data.local_file.favorita.content}"
}

output "hash_md5" {
  value = data.local_file.favorita.content_md5 # también exporta checksums
}
```

Fíjate en la sintaxis de referencia: `data.TIPO.NOMBRE.ATRIBUTO` (con el prefijo `data.`, a diferencia de los recursos). El data source `local_file` exporta `content`, `content_base64` y varios checksums (`content_md5`, `content_sha256`...).

```text
$ terraform plan
data.local_file.favorita: Reading...
data.local_file.favorita: Read complete after 0s [id=9f2c1a...]

Terraform will perform the following actions:

  # local_file.informe will be created
  + resource "local_file" "informe" {
      + content  = "La mascota favorita es: gatete"
      + filename = "informe.txt"
      ...
    }

Plan: 1 to add, 0 to change, 0 to destroy.
```

Observa el `Reading.../Read complete`: la lectura ocurre ya en el plan, y el data source **no cuenta** en el resumen de añadidos/destruidos.

### Ejemplo AWS: la AMI más reciente

El caso de uso estrella en la nube: no "hardcodees" (del inglés *hardcode*: escribas el valor a fuego en el código, en lugar de obtenerlo dinámicamente) el ID de una imagen de máquina, que cambia con cada actualización; pídesela a AWS:

```hcl
# Busca la AMI de Ubuntu 22.04 más reciente publicada por Canonical
data "aws_ami" "ubuntu" {
  most_recent = true            # si hay varias, quédate con la más nueva
  owners      = ["099720109477"] # ID de cuenta de Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

resource "aws_instance" "web" {
  ami           = data.aws_ami.ubuntu.id # el ID leído, siempre actualizado
  instance_type = "t2.micro"
}
```

El data source admite `most_recent`, `owners`, bloques `filter` (pares `name`/`values`), `name_regex` y `executable_users`, y exporta entre otros `id`, `image_id`, `name` y `arn`.

### resource vs data: la tabla

| Aspecto | `resource` (recurso gestionado) | `data` (data source) |
|---|---|---|
| Verbo | Crea, actualiza y destruye | Solo lee |
| Ciclo de vida | Gestionado por Terraform de principio a fin | El objeto vive fuera; Terraform ni lo toca |
| Referencia | `TIPO.NOMBRE.atributo` | `data.TIPO.NOMBRE.atributo` |
| En el plan | Cuenta en `add/change/destroy` | Aparece como `Reading...`, no cuenta |
| `terraform destroy` | Destruye el objeto | No le afecta (solo se olvida de él) |
| Meta-argumentos | `count`, `for_each`, `provider`, `depends_on`, `lifecycle` completo | `count`, `for_each`, `provider`, `depends_on`; en `lifecycle`, solo condiciones personalizadas |

> ⚠️ **Errores comunes:**
> - Olvidar el prefijo `data.` al referenciar (`local_file.favorita.content` en vez de `data.local_file.favorita.content`): Terraform buscará un *recurso* con ese nombre y fallará.
> - Apuntar el data source a algo que no existe todavía: `data "local_file"` da error si el fichero no está. Los data sources leen, no esperan.
> - En `aws_ami`, filtrar con un patrón amplio sin `most_recent = true` ni `owners`: o te llevas un error por resultados múltiples, o (peor) una AMI de un desconocido.
> - Usar un data source para leer algo que ese mismo proyecto ya gestiona como recurso: redundante y fuente de dependencias confusas; referencia el recurso directamente.

> 💡 **Buenas prácticas:**
> - Regla mental: si Terraform debe ser el *dueño* del objeto, `resource`; si solo necesita *saber* de él, `data`.
> - En `aws_ami`, fija siempre `owners` (por seguridad) y `most_recent = true` con filtros precisos.
> - Ten presente que un `data aws_ami` con `most_recent` puede devolver un ID nuevo con el tiempo y provocar el reemplazo de instancias: revisa los planes con calma.

### 🧪 Laboratorio

**Enunciado:** simula la colaboración con un sistema externo: (1) crea a mano un fichero `equipo.txt` con el texto `plataforma`; (2) haz que Terraform lo lea con un data source y genere un fichero `bienvenida.txt` que diga "Bienvenido al equipo `<contenido>`, tu mascota es `<random_pet>`"; (3) expón el contenido leído y su MD5 como outputs; (4) comprueba qué pasa con `equipo.txt` al hacer `terraform destroy`.

**Solución paso a paso:**

1. Crea el fichero fuera de Terraform: `Set-Content equipo.txt "plataforma"` (PowerShell) o `echo "plataforma" > equipo.txt`.
2. Escribe y aplica este `main.tf`:

```hcl
data "local_file" "equipo" {
  filename = "equipo.txt" # creado fuera de Terraform
}

resource "random_pet" "mascota" {
  length = 2
}

resource "local_file" "bienvenida" {
  filename = "bienvenida.txt"
  content  = "Bienvenido al equipo ${trimspace(data.local_file.equipo.content)}, tu mascota es ${random_pet.mascota.id}"
}

output "contenido_leido" {
  value = data.local_file.equipo.content
}

output "md5_equipo" {
  value = data.local_file.equipo.content_md5
}
```

(El `trimspace` elimina el salto de línea final que añaden `echo`/`Set-Content`.)

3. `terraform init` y `terraform apply`. En la salida verás `data.local_file.equipo: Reading... / Read complete` antes del plan, y `Plan: 2 to add` (solo los dos recursos; el data source no cuenta). Comprueba los outputs con `terraform output`.
4. Ejecuta `terraform destroy`: se borran `bienvenida.txt` y el `random_pet`, pero `equipo.txt` **sigue intacto**, porque Terraform nunca fue su dueño. Esa es la esencia de un data source.

> ❓ **Preguntas de repaso:**
> 1. *¿Cuál es la diferencia esencial entre `resource` y `data`?* — El `resource` crea, actualiza y destruye un objeto cuyo ciclo de vida gestiona Terraform; el `data` solo lee información de un objeto que existe fuera de la configuración.
> 2. *¿Cómo referencias el contenido de `data "local_file" "equipo"`?* — Con `data.local_file.equipo.content` (prefijo `data.` obligatorio).
> 3. *¿Para qué sirven `most_recent` y `owners` en `data "aws_ami"`?* — `most_recent` elige la imagen más nueva si el filtro devuelve varias; `owners` limita la búsqueda a cuentas concretas (p. ej. Canonical o `amazon`), evitando errores por multiplicidad y AMIs de origen dudoso.

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
