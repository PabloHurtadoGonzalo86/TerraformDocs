# Módulo 6 · Trabajando con Terraform

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
