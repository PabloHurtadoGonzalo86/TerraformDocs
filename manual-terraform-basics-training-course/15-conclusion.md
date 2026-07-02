# Módulo 13 · Conclusión y kit de recursos

## 13.1 Qué has aprendido: el mapa completo

**¿Qué vas a aprender?** En esta lección vas a consolidar todo el recorrido del curso: repasarás módulo a módulo qué sabías hacer al terminar cada uno y verás cómo encajan las piezas entre sí. El objetivo es que pases de "he visto muchas cosas" a "tengo un mapa mental ordenado de Terraform".

Piensa en este curso como en sacarte el carné de conducir. Al principio ni siquiera sabías qué era el embrague (módulo 1: ¿qué es la infraestructura como código?); luego practicaste en un aparcamiento vacío sin riesgo (módulos 2-6, con los providers `local` y `random`, que no cuestan dinero ni necesitan cuenta en la nube); después saliste a carretera real (módulos 7-9, con AWS); y finalmente aprendiste maniobras avanzadas: aparcar en sitios imposibles (`import`), llevar varios coches idénticos (módulos reutilizables) y leer el cuadro de mandos (funciones y expresiones). Hoy toca mirar el mapa completo del viaje.

### La narrativa del curso, módulo a módulo

Empezaste entendiendo **por qué existe Terraform**: aprovisionar infraestructura a mano es lento, propenso a errores y no deja rastro. La infraestructura como código convierte servidores, redes y ficheros en texto versionable. Después diste tus **primeros pasos**: instalaste Terraform, escribiste tu primer bloque `resource` en HCL y ejecutaste el ciclo sagrado `init → plan → apply → destroy`. En los **fundamentos** descubriste que Terraform no sabe hablar con ningún sistema por sí solo: son los *providers* (plugins) quienes traducen tus bloques HCL a llamadas de API, y aprendiste a parametrizar con variables de entrada y a exponer resultados con outputs.

Luego llegó el concepto más importante del curso: el **estado** (`terraform.tfstate`), la "memoria" donde Terraform apunta qué ha creado y con qué atributos. Sin estado no hay idempotencia. Con él en la mochila, aprendiste a **trabajar con Terraform** en serio: `validate`, `fmt`, `show`, el enfoque de infraestructura inmutable y las reglas `lifecycle`. Después dominaste los **data sources y meta-argumentos** (`count`, `for_each`, `depends_on`) y las restricciones de versión.

Con la base sólida, saltaste a la nube: **AWS con IAM, S3 y DynamoDB**, luego **EC2 y provisioners**, y el **estado remoto** con backend S3 y bloqueo, imprescindible para trabajar en equipo. De vuelta a terreno seguro, aprendiste a **reemplazar recursos dañados y a importar** infraestructura preexistente, a empaquetar configuración en **módulos** reutilizables y a exprimir **funciones, expresiones condicionales y workspaces**.

### Tabla resumen del curso

| Módulo | Tema | Idea clave |
|---|---|---|
| 1 | Introducción a la IaC | La infraestructura se declara en código versionable |
| 2 | Primeros pasos | Ciclo `init → plan → apply → destroy` |
| 3 | Providers, variables y outputs | Los providers traducen HCL a llamadas de API |
| 4 | El estado de Terraform | `terraform.tfstate` es la memoria de Terraform |
| 5 | Trabajar con Terraform | Inmutabilidad, `lifecycle`, comandos de inspección |
| 6 | Data sources y meta-argumentos | Leer datos externos; `count`, `for_each`, `depends_on` |
| 7 | AWS I: IAM, S3, DynamoDB | Autenticación y primeros recursos reales |
| 8 | AWS II: EC2 y provisioners | Instancias, `user_data`, provisioners como último recurso |
| 9 | Estado remoto | Backend S3 con bloqueo: colaboración segura |
| 10 | Reemplazo, import y depuración | `apply -replace`, `import`, `TF_LOG` |
| 11 | Módulos | Empaquetar y reutilizar configuración |
| 12 | Funciones, condicionales y workspaces | Lógica dentro de HCL sin dejar de ser declarativo |
| 13 | Conclusión y kit de recursos | Consolidar y seguir aprendiendo |

Este mini-proyecto "cápsula" condensa media docena de conceptos del curso en veinte líneas, todo en local:

```hcl
# main.tf — proyecto resumen: variables, random, for_each y outputs
terraform {
  required_version = ">= 1.0"          # restricción de versión (módulo 6)
  required_providers {
    local = {
      source  = "hashicorp/local"      # provider oficial del Registry (módulo 3)
      version = "~> 2.4"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}

variable "entornos" {
  type        = set(string)            # tipo de variable (módulo 3)
  default     = ["dev", "prod"]
  description = "Entornos a generar"
}

resource "random_pet" "nombre" {
  for_each = var.entornos              # meta-argumento (módulo 6)
  length   = 2
}

resource "local_file" "config" {
  for_each = var.entornos
  filename = "${path.module}/${each.key}.txt"
  # Dependencia implícita: usar el atributo crea el orden correcto (módulo 3)
  content  = "Entorno ${each.key} -> servidor ${random_pet.nombre[each.key].id}\n"
}

output "servidores" {
  value = { for e in var.entornos : e => random_pet.nombre[e].id }
}
```

```text
$ terraform apply -auto-approve
...
Apply complete! Resources: 4 added, 0 changed, 0 destroyed.

Outputs:

servidores = {
  "dev"  = "vast-mole"
  "prod" = "still-koala"
}
```

> ⚠️ **Errores comunes:**
> - Memorizar comandos sin entender el estado: la mitad de los problemas reales de Terraform (drift, recursos "huérfanos", conflictos en equipo) son problemas de estado, no de sintaxis.
> - Saltarse los módulos "aburridos" (variables, tipos, estado) para llegar rápido a la nube: sin esa base, AWS solo multiplica los errores… y la factura.
> - Creer que `plan` es opcional. Es tu red de seguridad: léelo siempre entero antes de aplicar.

> 💡 **Buenas prácticas:**
> - Reconstruye este mapa de memoria en una hoja en blanco: si puedes explicar cada módulo en una frase, lo tienes interiorizado.
> - Vuelve a los labs de los módulos 4 y 9 (estado local y remoto) pasados unos días: son los que más se olvidan y los que más importan en el trabajo real.
> - Guarda tus prácticas en un repositorio Git propio: te servirá de chuleta personal y de portfolio.

### 🧪 Laboratorio

**Enunciado:** sin mirar tus apuntes, crea desde cero un proyecto que: (1) fije versión de Terraform y de los providers `local` y `random`; (2) genere una contraseña aleatoria de 16 caracteres; (3) la escriba en un fichero `secreto.txt`; (4) exponga la longitud (no el valor) como output.

**Solución:**

1. Crea un directorio vacío y dentro un `main.tf` con el bloque `terraform` igual que el del ejemplo anterior.
2. Añade el recurso y el output:

```hcl
resource "random_password" "clave" {
  length  = 16
  special = true                       # incluye símbolos
}

resource "local_sensitive_file" "secreto" {
  filename = "${path.module}/secreto.txt"
  content  = random_password.clave.result   # atributo sensible
}

output "longitud" {
  # length() hereda la marca "sensible" de result; sin nonsensitive(),
  # Terraform exigiría declarar el output con sensitive = true (módulo 12)
  value = nonsensitive(length(random_password.clave.result))
}
```

3. Ejecuta `terraform init`, revisa `terraform plan` (fíjate en que el contenido aparece como `(sensitive value)`) y aplica con `terraform apply`. El output debe mostrar `longitud = 16`.
4. Limpia con `terraform destroy`.

> ❓ **Preguntas de repaso:**
> - **¿Cuál es el ciclo básico de trabajo de Terraform?** `terraform init` (descargar providers e inicializar), `terraform plan` (previsualizar cambios), `terraform apply` (ejecutarlos) y, si procede, `terraform destroy` (eliminarlos).
> - **¿Por qué el estado es "la pieza que lo une todo"?** Porque asocia tu configuración con los objetos reales: gracias a él Terraform sabe qué crear, qué cambiar y qué destruir, y consigue ser idempotente.
> - **¿Qué ventaja tuvo practicar con `local` y `random` antes de AWS?** Aprendiste toda la mecánica (HCL, estado, ciclo de vida, meta-argumentos) sin coste, sin credenciales y sin riesgo, dejando solo lo específico de la nube para después.

## 13.2 Chuleta de comandos de Terraform

**¿Qué vas a aprender?** Aquí tienes la referencia rápida de todos los comandos que has usado en el manual, verificados contra la documentación oficial de la CLI. Es la página que querrás imprimir y pegar junto al monitor.

Una chuleta de comandos es como el cajón de cubiertos de tu cocina: cuando empiezas, abres el cajón y dudas; cuando llevas meses cocinando, tu mano va sola al utensilio correcto. Esta tabla existe para acelerar esa memoria muscular. Casi todos los ejemplos funcionan sobre un proyecto local como el del laboratorio anterior (los de `import` y AWS son solo ilustrativos).

### Tabla de comandos

| Comando | Qué hace | Ejemplo |
|---|---|---|
| `terraform init` | Inicializa el directorio: descarga providers y configura el backend | `terraform init` |
| `terraform validate` | Comprueba que la configuración es sintácticamente válida y coherente | `terraform validate` |
| `terraform fmt` | Formatea los ficheros `.tf` al estilo canónico | `terraform fmt -recursive` |
| `terraform plan` | Calcula y muestra los cambios necesarios sin aplicarlos | `terraform plan -out=tfplan` |
| `terraform apply` | Crea o actualiza la infraestructura | `terraform apply tfplan` |
| `terraform apply -replace` | Fuerza el reemplazo de un recurso concreto (sustituye a `taint`) | `terraform apply -replace="local_file.pet"` |
| `terraform apply -refresh-only` | Sincroniza el estado con la realidad sin cambiar infraestructura | `terraform apply -refresh-only` |
| `terraform destroy` | Elimina toda la infraestructura gestionada | `terraform destroy` |
| `terraform show` | Muestra el estado actual o un plan guardado en formato legible | `terraform show tfplan` |
| `terraform providers` | Lista los providers que requiere la configuración | `terraform providers` |
| `terraform output` | Muestra los valores de output del módulo raíz | `terraform output servidores` |
| `terraform state list` | Lista los recursos registrados en el estado | `terraform state list` |
| `terraform state show` | Muestra los atributos de un recurso del estado | `terraform state show random_pet.nombre` |
| `terraform state mv` | Mueve o renombra un recurso dentro del estado | `terraform state mv local_file.a local_file.b` |
| `terraform state rm` | Saca un recurso del estado (sin destruirlo) | `terraform state rm local_file.viejo` |
| `terraform state pull` | Descarga y muestra el estado actual (útil con backends remotos) | `terraform state pull` |
| `terraform workspace` | Gestiona workspaces: `list`, `select`, `new`, `delete`, `show` | `terraform workspace new dev` |
| `terraform console` | Consola interactiva para evaluar expresiones contra el estado | `terraform console` |
| `terraform import` | Incorpora al estado un recurso creado fuera de Terraform | `terraform import aws_s3_bucket.web mi-bucket` |
| `terraform graph` | Genera el grafo de dependencias en formato DOT | `terraform graph \| dot -Tsvg > graph.svg` |
| `terraform version` | Muestra la versión de Terraform y de los providers instalados | `terraform version` |

```hcl
# chuleta.tf — configuración mínima para practicar la tabla entera en local
terraform {
  required_providers {
    local = { source = "hashicorp/local", version = "~> 2.4" }
  }
}

resource "local_file" "nota" {
  filename = "${path.module}/nota.txt"
  content  = "Practicando la chuleta de comandos\n"
}
```

```text
$ terraform state list
local_file.nota

$ terraform output
╷
│ Warning: No outputs found
╵
```

> 🔄 **Actualización:** el curso original usaba `terraform taint` para forzar la recreación de un recurso. Desde Terraform v0.15.2 ese comando está **obsoleto**: la documentación oficial recomienda `terraform apply -replace="direccion.recurso"`, que además te enseña el plan antes de tocar nada. Lo mismo ocurre con `terraform refresh`, hoy sustituido por `terraform apply -refresh-only`, que pide confirmación antes de reescribir el estado.

> ⚠️ **Errores comunes:**
> - Ejecutar `terraform state rm` pensando que destruye el recurso: solo lo "olvida" del estado; el objeto real sigue existiendo (y quizá facturando).
> - Usar `-out=tfplan` y subir ese fichero a Git: el plan guarda valores sensibles **en claro**, según advierte la propia documentación.
> - Editar `terraform.tfstate` a mano en lugar de usar `state mv`/`state rm`: un JSON corrupto puede dejarte sin memoria de toda tu infraestructura.
> - Confundir `validate` (¿es válido el código?) con `plan` (¿qué va a cambiar?): pasar `validate` no garantiza que el `apply` vaya a funcionar.

> 💡 **Buenas prácticas:**
> - Encadena siempre `fmt → validate → plan` antes de cualquier `apply`; en CI/CD, automatízalo.
> - Usa `terraform console` para probar funciones y expresiones antes de meterlas en el código: es tu laboratorio de HCL.
> - Reserva los comandos `state` para cirugía puntual y haz copia del estado (`terraform state pull > backup.json`) antes de operar.

### 🧪 Laboratorio

**Enunciado:** con el fichero `chuleta.tf` de arriba, ejecuta un "circuito" de 8 comandos: inicializa, formatea, valida, planifica con salida a fichero, aplica ese plan, lista el estado, fuerza el reemplazo del fichero y destruye.

**Solución:** `terraform init` → `terraform fmt` → `terraform validate` (debe decir `Success! The configuration is valid.`) → `terraform plan -out=tfplan` → `terraform apply tfplan` (no pide confirmación: el plan ya estaba aprobado) → `terraform state list` (muestra `local_file.nota`) → `terraform apply -replace="local_file.nota"` (el plan marca `# local_file.nota will be replaced, as requested`) → `terraform destroy`.

> ❓ **Preguntas de repaso:**
> - **¿Qué diferencia hay entre `terraform show` y `terraform state show`?** `show` presenta el estado completo o un plan guardado; `state show` muestra los atributos de **un** recurso concreto del estado.
> - **¿Cómo renombras un recurso en el código sin destruirlo y recrearlo?** Cambias el nombre en el `.tf` y ejecutas `terraform state mv direccion.antigua direccion.nueva` para que el estado siga apuntando al mismo objeto.
> - **¿Cuándo usarías `apply -refresh-only`?** Cuando alguien ha modificado la infraestructura fuera de Terraform y quieres que el estado refleje la realidad sin aplicar ningún cambio a los recursos.

## 13.3 Glosario español–inglés

**¿Qué vas a aprender?** Vas a fijar el vocabulario esencial de Terraform en ambos idiomas. La documentación oficial, los foros y las ofertas de empleo hablan en inglés; este glosario es tu puente para leer cualquier fuente sin fricción.

Aprender Terraform sin dominar su vocabulario es como mudarte a otro país sabiendo gramática pero sin léxico: entiendes la estructura de las frases, pero te pierdes en cada conversación. Cada término de esta tabla lo has visto en acción en algún módulo; aquí lo destilamos en una definición de bolsillo.

### Glosario

| Español | Inglés | Definición breve |
|---|---|---|
| Infraestructura como código | Infrastructure as Code (IaC) | Definir infraestructura en ficheros de texto versionables |
| Proveedor | Provider | Plugin que traduce HCL a llamadas de API (aws, local, random…) |
| Recurso | Resource | Objeto de infraestructura que Terraform crea y gestiona |
| Fuente de datos | Data source | Bloque de solo lectura para consultar datos existentes |
| Estado | State | Fichero (`terraform.tfstate`) que mapea configuración y realidad |
| Backend | Backend | Dónde y cómo se almacena el estado (local, S3…) |
| Estado remoto | Remote state | Estado compartido en un backend accesible por el equipo |
| Bloqueo de estado | State locking | Impedir dos operaciones simultáneas sobre el mismo estado |
| Deriva | Drift | Divergencia entre el estado y la infraestructura real |
| Módulo | Module | Conjunto reutilizable de ficheros `.tf`; el directorio raíz es el *root module* |
| Espacio de trabajo | Workspace | Instancia de estado independiente para una misma configuración |
| Meta-argumento | Meta-argument | Argumento válido en cualquier recurso: `count`, `for_each`, `depends_on`, `provider`, `lifecycle` |
| Aprovisionador | Provisioner | Ejecuta scripts al crear/destruir un recurso; último recurso |
| Marcar para reemplazo | Taint / replace | Forzar la recreación de un recurso (`apply -replace`) |
| Lenguaje de configuración | HCL | HashiCorp Configuration Language, el idioma de los `.tf` |
| Plan de ejecución | Plan | Previsualización de acciones: crear, cambiar, destruir |
| Aplicar | Apply | Ejecutar las acciones del plan contra la infraestructura |
| Idempotencia | Idempotency | Aplicar lo mismo dos veces no produce cambios adicionales |
| Variable de entrada | Input variable | Parámetro de la configuración (`variable {}`) |
| Valor de salida | Output value | Dato que la configuración expone (`output {}`) |
| Valor local | Local value | Expresión con nombre interno (`locals {}`) |
| Argumento | Argument | Lo que **tú** escribes en un bloque (`filename = ...`) |
| Atributo | Attribute | Lo que el recurso **devuelve** (`random_pet.n.id`) |
| Dependencia implícita | Implicit dependency | Orden deducido al referenciar atributos de otro recurso |
| Dependencia explícita | Explicit dependency | Orden forzado con `depends_on` |
| Interpolación | Interpolation | Insertar expresiones en cadenas: `"${var.x}"` |
| Expresión condicional | Conditional expression | `condicion ? valor_a : valor_b` |
| Función integrada | Built-in function | Funciones como `length`, `lookup`, `file` (no hay funciones de usuario) |
| Restricción de versión | Version constraint | Regla como `~> 3.6` para fijar versiones |
| Registro | Registry | Catálogo público de providers y módulos (registry.terraform.io) |
| Fichero de bloqueo | Dependency lock file | `.terraform.lock.hcl`: fija las versiones exactas de providers |
| Grafo de dependencias | Dependency graph | Estructura interna con la que Terraform ordena operaciones |

Así se ven muchos de estos términos juntos en diez líneas:

```hcl
# glosario.tf — cada comentario nombra el término que ilustra
variable "prefijo" {                     # input variable
  type    = string
  default = "app"
}

locals {                                 # local value
  nombre = "${var.prefijo}-demo"         # interpolación
}

resource "random_pet" "servidor" {}      # resource (del provider random)

resource "local_file" "etiqueta" {
  filename = "${path.module}/${local.nombre}.txt"
  content  = random_pet.servidor.id      # atributo → dependencia implícita
}

output "ruta" {                          # output value
  value = local_file.etiqueta.filename
}
```

> ⚠️ **Errores comunes:**
> - Confundir **argumento** (lo que escribes) con **atributo** (lo que Terraform te devuelve tras crear el recurso): es la duda número uno al leer documentación de providers.
> - Traducir *state* como "estatus" o hablar de "el tfstate" como si fuera opcional: es EL concepto central, no un fichero auxiliar.
> - Decir "Terraform hace deploy": Terraform **aprovisiona** infraestructura; el despliegue de aplicaciones es otra fase (y a menudo otra herramienta).

> 💡 **Buenas prácticas:**
> - Al leer docs en inglés, verbaliza mentalmente el término en español (y viceversa): fija el doble vínculo.
> - En equipos hispanohablantes, pacta el vocabulario del proyecto (¿"workspace" o "espacio de trabajo"?) y sé consistente en la documentación interna.
> - Cuando un término te baile, búscalo en el propio manual: cada uno tiene su módulo con ejemplos ejecutables.

### 🧪 Laboratorio

**Enunciado (mini-ejercicio):** copia `glosario.tf` en un directorio nuevo y, sin ejecutarlo aún, escribe en un papel qué recursos creará, en qué orden y por qué. Después compruébalo.

**Solución:** el orden es `random_pet.servidor` → `local_file.etiqueta`, porque `content` referencia el atributo `id` del primero (dependencia implícita). Verifícalo con `terraform init && terraform apply` y observa el orden de creación en la salida; después ejecuta `terraform graph` y localiza la arista entre ambos nodos.

> ❓ **Preguntas de repaso:**
> - **¿Qué diferencia a un data source de un resource?** El data source solo **lee** información existente; el resource **crea y gestiona** un objeto.
> - **¿Qué es el drift y qué comando te ayuda a reconciliarlo?** Es la divergencia entre estado y realidad; `terraform apply -refresh-only` actualiza el estado, y un `plan` posterior te muestra cómo volver a la configuración deseada.
> - **¿Para qué sirve `.terraform.lock.hcl`?** Fija las versiones exactas de los providers seleccionadas en `init`, garantizando instalaciones reproducibles; debe versionarse en Git.

## 13.4 Recursos oficiales y siguientes pasos

**¿Qué vas a aprender?** Vas a montar tu "kit de supervivencia" post-curso: las fuentes oficiales donde resolver cualquier duda, qué te aporta la certificación Terraform Associate y un itinerario concreto para seguir creciendo.

Terminar un curso es como terminar la autoescuela: tienes el título, pero conducir de verdad se aprende en la carretera. La diferencia entre quien se estanca y quien progresa está en dos hábitos: consultar siempre fuentes oficiales (no posts aleatorios desactualizados) y practicar con proyectos propios cada vez menos triviales.

### Fuentes oficiales imprescindibles

- **Documentación de Terraform** — `developer.hashicorp.com/terraform`: referencia del lenguaje HCL, de la CLI y tutoriales guiados. Tu primera parada, siempre.
- **Terraform Registry** — `registry.terraform.io`: catálogo de providers y módulos con la documentación de cada recurso, argumento y atributo. Aquí viven las docs de `hashicorp/local`, `hashicorp/random` y `hashicorp/aws`.
- **Guía de estilo oficial** — `developer.hashicorp.com/terraform/language/style`: nombres descriptivos con guiones bajos, indentación de dos espacios, ficheros separados (`main.tf`, `variables.tf`, `outputs.tf`), versiones fijadas y `terraform fmt` antes de cada commit.
- **Tutoriales oficiales** — `developer.hashicorp.com/terraform/tutorials`: itinerarios prácticos por temática (AWS, módulos, estado, certificación).

### La certificación HashiCorp Certified: Terraform Associate

Es el examen oficial de nivel asociado y la validación natural de este curso.

> 🔄 **Actualización:** cuando se grabó el curso, el examen vigente era una versión anterior (002/003). La versión actual es **Terraform Associate 004**, cuyos objetivos oficiales se agrupan en ocho dominios: (1) IaC con Terraform, (2) fundamentos de Terraform, (3) flujo de trabajo básico, (4) configuración, (5) módulos, (6) gestión del estado, (7) mantenimiento de infraestructura y (8) **HCP Terraform**. Consulta el temario vigente en la web oficial antes de reservar plaza.

**Qué cubre este curso:** los dominios 1 a 7 casi al completo — IaC, ciclo `init/plan/apply/destroy`, providers, variables, outputs, estado local y remoto, módulos, funciones, meta-argumentos, `import` y depuración.

**Qué te faltaría:** el dominio 8, **HCP Terraform** (la plataforma gestionada de HashiCorp: ejecuciones remotas, gestión de variables en la nube, Sentinel/políticas). Existe un plan gratuito con el que puedes cubrir ese hueco en una o dos tardes siguiendo los tutoriales oficiales de certificación.

### Tu itinerario recomendado

1. **Semana 1-2:** repite los labs de este manual sin mirar las soluciones y monta un proyecto personal (por ejemplo, una web estática en S3 gestionada 100 % con Terraform).
2. **Semana 3-4:** estudia HCP Terraform con los tutoriales oficiales y haz los exámenes de prueba del itinerario de certificación.
3. **Después:** aprende a probar tus módulos con `terraform test` (ficheros `.tftest.hcl`), integra Terraform en un pipeline de CI/CD y explora herramientas del ecosistema como TFLint.

Deja tus proyectos siempre con esta base, alineada con la guía de estilo:

```hcl
# terraform.tf — plantilla de arranque para todos tus proyectos futuros
terraform {
  required_version = ">= 1.5"    # exige un Terraform moderno
  required_providers {
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"         # acepta 3.6.x y 3.7+, nunca 4.x
    }
  }
}
```

```text
$ terraform init
Initializing provider plugins...
- Finding hashicorp/random versions matching "~> 3.6"...
- Installing hashicorp/random v3.7.2...

Terraform has been successfully initialized!
```

> ⚠️ **Errores comunes:**
> - Estudiar la certificación solo con *dumps* (bancos de preguntas filtradas, a menudo desactualizados): el examen actual incluye escenarios prácticos; sin horas de terminal, se nota.
> - Fiarte de tutoriales de blog de 2020: entre Terraform 0.13 y las versiones 1.x actuales han cambiado comandos (`taint`, `refresh`), el fichero de bloqueo y HCP Terraform. Contrasta siempre con la documentación oficial.
> - Dejar de practicar tras el curso: Terraform se oxida rápido; media hora semanal con un proyecto propio vale más que releer apuntes.

> 💡 **Buenas prácticas:**
> - Marca en favoritos la referencia de la CLI y la del lenguaje; acostúmbrate a resolver dudas ahí antes que en foros.
> - Versiona todos tus experimentos en Git con un `.gitignore` que excluya `.terraform/` y `*.tfstate*`.
> - Suscríbete al changelog de Terraform en GitHub para enterarte de novedades y deprecaciones.

### 🧪 Laboratorio

**Enunciado:** ve a `registry.terraform.io`, busca el provider `hashicorp/random` y localiza la documentación del recurso `random_pet`. Identifica un argumento que no hayamos usado en el curso, aplícalo en un proyecto local y verifica su efecto.

**Solución:** en la página del provider, pestaña *Documentation*, entra en `random_pet`. El argumento `separator` define el carácter que une las palabras (por defecto `-`). Crea un `main.tf` con la plantilla `terraform.tf` de arriba más:

```hcl
resource "random_pet" "mascota" {
  length    = 3
  separator = "_"   # une las palabras con guion bajo
}

output "nombre" {
  value = random_pet.mascota.id
}
```

Ejecuta `terraform init && terraform apply -auto-approve`: el output será algo como `nombre = "socially_engaged_stingray"`. Acabas de hacer lo que harás cientos de veces como profesional: leer la doc del Registry y aplicarla. Destruye al terminar.

> ❓ **Preguntas de repaso:**
> - **¿Dónde consultas los argumentos válidos de un recurso concreto?** En el Terraform Registry (`registry.terraform.io`), dentro de la documentación del provider correspondiente.
> - **¿Qué dominio del examen Terraform Associate 004 no cubre este curso y cómo lo completarías?** HCP Terraform; se completa con los tutoriales oficiales del itinerario de certificación en developer.hashicorp.com.
> - **¿Cuál debería ser tu siguiente proyecto tras este curso?** Uno propio y pequeño pero real (p. ej. una web estática en S3 con Terraform), versionado en Git y siguiendo la guía de estilo oficial: consolida todo lo aprendido y arranca tu portfolio.

---

Enhorabuena, Pablo: has pasado de no saber qué era un provider a leer planes con ojo crítico, operar el estado con bisturí y publicar módulos reutilizables. Ahora, a la carretera.
