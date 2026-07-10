---
title: "Módulo 3 · Primeros pasos con Terraform"
description: "Instalación de Terraform, fundamentos de HCL y tu primer flujo init/plan/apply/destroy."
---

## 3.1 Instalación de Terraform

**¿Qué vas a aprender?** En esta lección instalarás Terraform en tu máquina, sea cual sea tu sistema operativo, y comprobarás que funciona. Verás las dos vías principales (binario descargado a mano y gestores de paquetes) y entenderás por qué la instalación de Terraform es tan sencilla comparada con la de otras herramientas.

### Un único binario, cero dependencias

Terraform se distribuye como **un solo fichero ejecutable** escrito en Go. No necesita runtime, ni base de datos, ni servicio en segundo plano: lo descargas, lo colocas en una carpeta que esté en tu `PATH` y listo. Piensa en él como en una calculadora de bolsillo: no hay que "instalarla", basta con sacarla del cajón y que esté a mano cuando la necesites. Esa carpeta del `PATH` es precisamente eso, el cajón donde tu terminal busca las herramientas cuando tecleas un comando.

Esto tiene una consecuencia práctica estupenda: instalar, actualizar o tener varias versiones conviviendo es trivial, porque todo se reduce a gestionar un fichero llamado `terraform` (o `terraform.exe` en Windows).

### Instalación en Linux

En distribuciones basadas en Debian/Ubuntu, lo recomendable es usar el repositorio APT oficial de HashiCorp, que te garantiza binarios firmados y actualizaciones con `apt upgrade`:

```text
# 1. Añadir la clave GPG de HashiCorp
wget -O - https://apt.releases.hashicorp.com/gpg | \
  sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg

# 2. Añadir el repositorio oficial
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] \
  https://apt.releases.hashicorp.com $(lsb_release -cs) main" | \
  sudo tee /etc/apt/sources.list.d/hashicorp.list

# 3. Instalar
sudo apt update && sudo apt install terraform
```

En RHEL/CentOS/Fedora el equivalente usa el repositorio YUM/DNF oficial (`sudo yum-config-manager --add-repo https://rpm.releases.hashicorp.com/RHEL/hashicorp.repo` y después `sudo yum -y install terraform`).

La alternativa universal es el **binario manual**: descargas el `.zip` de tu arquitectura desde la página oficial de descargas (developer.hashicorp.com/terraform/install), lo descomprimes y mueves el ejecutable a `/usr/local/bin`:

```text
unzip terraform_1.15.7_linux_amd64.zip
sudo mv terraform /usr/local/bin/
```

### Instalación en macOS

Con Homebrew, usando el *tap* oficial de HashiCorp:

```text
brew tap hashicorp/tap
brew install hashicorp/tap/terraform
```

También puedes usar el binario manual (hay builds para Intel y Apple Silicon).

### Instalación en Windows

La vía oficial es descargar el `.zip` del binario, descomprimirlo en una carpeta (por ejemplo `C:\terraform`) y **añadir esa carpeta a la variable de entorno `PATH`** desde Configuración → Sistema → Variables de entorno. Si usas el gestor de paquetes Chocolatey (que es el que muestra el propio tutorial de HashiCorp), es una línea:

```text
choco install terraform
```

### Verificación

Abre una terminal **nueva** (para que cargue el `PATH` actualizado) y ejecuta:

```text
$ terraform version
Terraform v1.15.7
on linux_amd64
```

Si además `terraform -help` te muestra la lista de subcomandos (`init`, `plan`, `apply`...), la instalación está completa.

> 🔄 **Actualización:** el curso original se grabó con Terraform 0.13. Desde la versión 1.0 (junio de 2021), HashiCorp mantiene garantías de compatibilidad dentro de la serie 1.x, así que todo lo que aprendas aquí con un Terraform 1.x moderno (1.15 en el momento de escribir esto) te valdrá sin sobresaltos. Los comandos básicos no han cambiado; sí verás pequeñas diferencias en las salidas por pantalla respecto a los vídeos.

> ⚠️ **Errores comunes:**
> - **"terraform: command not found"** justo después de instalar: casi siempre es que el binario no está en el `PATH` o que no has abierto una terminal nueva tras modificarlo.
> - **Instalar desde el repositorio de tu distribución** en lugar del de HashiCorp: algunas distros empaquetan versiones muy antiguas. Usa siempre el repositorio oficial o el binario de la web.
> - **Descargar la arquitectura equivocada** (amd64 vs arm64). En un Mac con Apple Silicon o una Raspberry Pi, verifica la arquitectura antes de descargar.
> - En Windows, **descomprimir el zip y ejecutarlo con doble clic**: Terraform es una herramienta de línea de comandos; se usa desde PowerShell o CMD, no tiene interfaz gráfica.

> 💡 **Buenas prácticas:**
> - Instala mediante gestor de paquetes cuando puedas: las actualizaciones de seguridad llegan solas.
> - Anota la versión que usas en cada proyecto (más adelante verás cómo fijarla en el código con `required_version`), para que todo el equipo trabaje con la misma.
> - Ejecuta `terraform version` periódicamente: si hay una versión más reciente disponible, el propio comando te lo avisa.

### 🧪 Laboratorio

**Enunciado:** instala Terraform en tu máquina y verifica que puedes ejecutarlo desde cualquier directorio.

**Solución paso a paso:**

1. Instala con el método de tu sistema (APT/Homebrew/Chocolatey o binario manual, como se ha visto arriba).
2. Abre una terminal nueva y sitúate en tu directorio personal (`cd ~` o `cd $HOME`).
3. Ejecuta `terraform version` y confirma que ves una versión 1.x.
4. Ejecuta `terraform -help` y localiza en la salida los tres comandos que usaremos en la siguiente lección: `init`, `plan` y `apply`.
5. (Extra) Ejecuta `terraform plan -help` para ver la ayuda específica de un subcomando. Acostúmbrate a este patrón: la ayuda integrada es tu primera fuente de consulta.

> ❓ **Preguntas de repaso:**
> 1. **¿Por qué la instalación de Terraform consiste básicamente en copiar un fichero?** Porque Terraform se distribuye como un único binario autocontenido escrito en Go, sin dependencias externas ni servicios asociados.
> 2. **¿Qué comando usas para comprobar la versión instalada?** `terraform version`.
> 3. **Tras instalar en Windows, tecleas `terraform` y no se encuentra el comando. ¿Cuál es la causa más probable?** La carpeta donde está `terraform.exe` no se ha añadido al `PATH`, o no has abierto una terminal nueva después de añadirla.

## 3.2 Fundamentos de HCL: tu primer recurso

**¿Qué vas a aprender?** Aquí está el corazón del módulo: la sintaxis de HCL (HashiCorp Configuration Language), la anatomía de un bloque `resource` y el ciclo completo `init → plan → apply` con el que crearás tu primera infraestructura real... que será un humilde fichero en tu disco. Sin cuenta cloud, sin coste, con todo el aprendizaje.

### La anatomía de un bloque HCL

Todo fichero Terraform (extensión `.tf`) se compone de **bloques** y **argumentos**. Un bloque es un contenedor con esta forma:

```hcl
# TIPO      ETIQUETA 1    ETIQUETA 2
resource "local_file" "mascota" {
  # argumento = valor
  filename = "/root/mascotas.txt"
  content  = "Me encantan los gatos"
}
```

Desmontémoslo pieza a pieza:

- **Tipo de bloque** (`resource`): la palabra clave que dice qué clase de contenido viene. Otros tipos que verás pronto: `provider`, `variable`, `output`, `terraform`.
- **Etiquetas** (*labels*): en un `resource` hay dos. La primera (`"local_file"`) es el **tipo de recurso**; fíjate en que sigue el patrón `proveedor_recurso`: el prefijo `local` identifica al provider y `file` a la clase de objeto que gestiona. La segunda (`"mascota"`) es el **nombre lógico** que tú eliges para referirte a este recurso dentro del código.
- **Cuerpo**: todo lo que va entre llaves `{ }`.
- **Argumentos**: pares `nombre = expresión`. Aquí `filename` (obligatorio: la ruta del fichero a crear; si faltan directorios intermedios, el provider los crea) y `content` (el texto que contendrá).

La pareja *tipo de recurso + nombre lógico* (`local_file.mascota`) forma la **dirección** del recurso y debe ser única en tu configuración. Los comentarios se escriben con `#` (el estilo idiomático), aunque también se admiten `//` y `/* ... */`.

Una analogía: un bloque `resource` es como un **pedido a un restaurante de comida a domicilio**. El tipo de recurso es el plato del menú (existe un catálogo cerrado, definido por el provider: no puedes inventarte platos), el nombre lógico es el nombre que pones en el pedido para distinguirlo de otros, y los argumentos son las instrucciones de preparación ("sin cebolla, ración grande"). Tú describes el pedido; la cocina (el provider) sabe cómo prepararlo.

### Segundo ejemplo: un recurso sin ficheros de por medio

El provider `random` genera valores aleatorios gestionados como recursos. Su recurso `random_pet` produce nombres de mascota (sí, en serio: es la forma estándar de generar identificadores únicos legibles):

```hcl
resource "random_pet" "mi_mascota" {
  prefix    = "sr"  # texto que se antepone al nombre
  separator = "."   # separador entre palabras (por defecto "-")
  length    = 1     # número de palabras (por defecto 2)
}
```

Al aplicarlo obtendrás algo como `sr.perezoso`. Este recurso es "lógico": no crea nada en disco ni en ningún cloud, solo guarda un valor en el estado de Terraform. Es perfecto para practicar.

### El flujo de trabajo: init → plan → apply

Crea un directorio vacío, guarda dentro el primer ejemplo en un fichero `main.tf` (el nombre es convención, no obligación: Terraform lee **todos** los `.tf` del directorio) y ejecuta los tres comandos en orden.

**Paso 1 — `terraform init`:** inicializa el directorio de trabajo. Terraform lee tu configuración, detecta que usas el tipo de recurso `local_file`, deduce que necesita el provider `hashicorp/local` y lo descarga del Terraform Registry.

```text
$ terraform init

Initializing the backend...
Initializing provider plugins...
- Finding latest version of hashicorp/local...
- Installing hashicorp/local v2.5.2...
- Installed hashicorp/local v2.5.2 (signed by HashiCorp)

Terraform has created a lock file .terraform.lock.hcl to record the provider
selections it made above.

Terraform has been successfully initialized!
```

Línea a línea: *Initializing the backend* prepara dónde se guardará el estado (de momento, en local); *Installing hashicorp/local* descarga el plugin al subdirectorio oculto `.terraform/`; y el *lock file* `.terraform.lock.hcl` deja constancia de la versión exacta elegida. `init` es **idempotente**: puedes ejecutarlo cuantas veces quieras sin peligro; nunca borra tu configuración ni tu estado.

**Paso 2 — `terraform plan`:** el "ensayo general". Compara lo que describes en el código con lo que existe en la realidad y te enseña qué haría, sin tocar nada:

```text
$ terraform plan

Terraform used the selected providers to generate the following execution
plan. Resource actions are indicated with the following symbols:
  + create

Terraform will perform the following actions:

  # local_file.mascota will be created
  + resource "local_file" "mascota" {
      + content              = "Me encantan los gatos"
      + content_base64sha256 = (known after apply)
      + directory_permission = "0777"
      + file_permission      = "0777"
      + filename             = "/root/mascotas.txt"
      + id                   = (known after apply)
    }

Plan: 1 to add, 0 to change, 0 to destroy.
```

Observa tres cosas. Primera: el símbolo `+` marca todo lo que se va a **crear**. Segunda: aparecen argumentos que tú no escribiste, como `file_permission = "0777"`; son valores por defecto que el provider rellena (0777 son los permisos del fichero en notación octal). Tercera: `(known after apply)` señala atributos cuyo valor no se puede saber hasta crear el recurso de verdad, como el `id`. La última línea resume el plan: 1 recurso a añadir, 0 a cambiar, 0 a destruir.

**Paso 3 — `terraform apply`:** ejecuta el plan. Te lo vuelve a mostrar y pide confirmación explícita:

```text
$ terraform apply
...(mismo plan que antes)...

Do you want to perform these actions?
  Terraform will perform the actions described above.
  Only 'yes' will be accepted to approve.

  Enter a value: yes

local_file.mascota: Creating...
local_file.mascota: Creation complete after 0s [id=5f5fa6a48d...]

Apply complete! Resources: 1 added, 0 changed, 0 destroyed.
```

Solo la palabra exacta `yes` aprueba la operación. Tras el apply, comprueba el resultado con `cat /root/mascotas.txt`: ahí está tu fichero. Además, en el directorio ha aparecido `terraform.tfstate`, el fichero de estado donde Terraform apunta lo que ha creado (lo estudiaremos a fondo en su propio módulo).

> 🔄 **Actualización:** dos cambios desde la época del curso. El fichero de bloqueo `.terraform.lock.hcl` no existía en Terraform 0.13 (llegó en la 0.14) y hoy conviene versionarlo en Git junto al código. Y el argumento `sensitive_content` de `local_file`, que quizá veas en material antiguo, está obsoleto: para contenido sensible existe ahora el recurso dedicado `local_sensitive_file`.

> ⚠️ **Errores comunes:**
> - **Olvidar `terraform init`** y lanzarte al `plan`: obtendrás un error de que los providers no están instalados. `init` va siempre primero en cada directorio nuevo.
> - **Guardar el fichero sin la extensión `.tf`** (por ejemplo `main.tf.txt`): Terraform dirá que no encuentra configuración en el directorio.
> - **Confundir `filename` con el fichero de configuración**: `main.tf` es donde escribes el código; `filename` es la ruta del fichero que Terraform va a *crear*. Son cosas distintas.
> - **Duplicar la dirección de un recurso** (dos `resource "local_file" "mascota"`): error de validación inmediato. El nombre lógico debe ser único por tipo de recurso.

> 💡 **Buenas prácticas:**
> - Ejecuta `terraform fmt` para formatear el código (alineado, indentación) y `terraform validate` para detectar errores de sintaxis antes del plan.
> - Un directorio = una configuración. No mezcles proyectos distintos en la misma carpeta: Terraform fusiona todos los `.tf` que encuentre.
> - Elige nombres lógicos descriptivos (`config_app`, no `f1`): son la clave con la que referenciarás el recurso desde el resto del código.
> - Lee siempre el plan entero antes de aprobar, incluso en ejercicios de juguete. Es el hábito que te salvará en producción.

### 🧪 Laboratorio

**Enunciado:** en un directorio nuevo llamado `primer-recurso`, crea una configuración con dos recursos: un `local_file` llamado `manifiesto` que genere el fichero `manifiesto.txt` con el texto "La infraestructura también es código", y un `random_pet` llamado `alias` con prefijo `lab`, separador `_` y una sola palabra. Aplícala y verifica ambos resultados.

**Solución:**

1. Prepara el directorio y el fichero `main.tf`:

```hcl
resource "local_file" "manifiesto" {
  filename = "${path.module}/manifiesto.txt" # path.module = directorio actual
  content  = "La infraestructura también es código"
}

resource "random_pet" "alias" {
  prefix    = "lab"
  separator = "_"
  length    = 1
}
```

2. `terraform init` — verás que esta vez instala **dos** providers: `hashicorp/local` y `hashicorp/random`, porque tu código usa tipos de recurso de ambos.
3. `terraform plan` — comprueba que el resumen dice `Plan: 2 to add, 0 to change, 0 to destroy.`
4. `terraform apply` y confirma con `yes`.
5. Verifica: `cat manifiesto.txt` muestra el texto, y el nombre generado por `random_pet` aparece en la salida del apply (algo como `random_pet.alias: Creation complete after 0s [id=lab_koala]`).

> ❓ **Preguntas de repaso:**
> 1. **En `resource "local_file" "mascota"`, ¿qué es cada una de las tres palabras?** `resource` es el tipo de bloque; `"local_file"` es el tipo de recurso (provider `local`, recurso `file`); `"mascota"` es el nombre lógico que tú eliges.
> 2. **¿Qué hace exactamente `terraform init` y cuántas veces puedes ejecutarlo?** Inicializa el directorio: configura el backend y descarga los providers (y módulos) que la configuración necesita. Es seguro ejecutarlo tantas veces como quieras.
> 3. **¿Qué significa `(known after apply)` en un plan?** Que ese atributo no puede calcularse hasta que el recurso se cree de verdad; Terraform lo conocerá después del apply.

## 3.3 Actualizar y destruir infraestructura

**¿Qué vas a aprender?** El ciclo de vida no acaba en la creación: en esta lección modificarás un recurso existente y aprenderás a leer los símbolos del plan (`+`, `-`, `~`, `-/+`) para saber si Terraform va a actualizar en el sitio o a destruir y recrear. Cerrarás el círculo con `terraform destroy`.

### Cambiar el código es cambiar la infraestructura

Recuerda el enfoque declarativo del módulo anterior: tú no das órdenes, describes el estado deseado. Así que para "actualizar infraestructura" no hay un comando especial: **editas el `.tf` y vuelves a ejecutar plan/apply**. Terraform calcula la diferencia entre lo que hay y lo que pides, y decide la operación mínima necesaria.

Esa operación puede ser de dos tipos, y la diferencia importa mucho:

- **Update in-place (`~`)**: el cambio se aplica sobre el recurso existente sin destruirlo. Ejemplo típico en cloud: cambiar las etiquetas de una máquina virtual.
- **Replacement (`-/+`)**: el argumento que has tocado no se puede modificar en caliente, así que Terraform **destruye el recurso y crea uno nuevo**. En el plan lo verás anotado como *forces replacement*.

¿Quién decide cuál toca? El **provider**, que conoce las reglas de cada tecnología. Es como las reformas de una casa: cambiar el color de las paredes es un *update in-place* (pintas encima); cambiar los cimientos obliga a demoler y reconstruir (*replacement*). Tú solo dices "quiero las paredes verdes" o "quiero otros cimientos"; el arquitecto sabe qué implica cada cosa.

### Viéndolo en acción con local_file

Partimos del recurso aplicado en la lección anterior y cambiamos el contenido:

```hcl
resource "local_file" "mascota" {
  filename = "/root/mascotas.txt"
  content  = "Ahora prefiero los perros" # ← cambiado
}
```

```text
$ terraform plan

Terraform used the selected providers to generate the following execution
plan. Resource actions are indicated with the following symbols:
-/+ destroy and then create replacement

Terraform will perform the following actions:

  # local_file.mascota must be replaced
-/+ resource "local_file" "mascota" {
      ~ content = "Me encantan los gatos" -> "Ahora prefiero los perros" # forces replacement
      ~ id      = "5f5fa6a48d..." -> (known after apply)
        # (argumentos sin cambios ocultos)
    }

Plan: 1 to add, 0 to change, 1 to destroy.
```

Lectura línea a línea: la cabecera anuncia el símbolo `-/+` (*destroy and then create replacement*); la línea `# local_file.mascota must be replaced` te dice qué recurso se recrea; dentro, la `~` marca cada atributo que cambia, y el comentario `# forces replacement` señala al culpable exacto de la recreación: `content`. El resumen final lo confirma: 1 a añadir y 1 a destruir (¡el mismo recurso, en dos actos!). Ocurre porque el provider `local` no sabe "editar" ficheros: ante cualquier cambio, borra el fichero y lo escribe de nuevo. En este caso da igual, pero imagina el mismo símbolo sobre una base de datos en producción: por eso hay que leer los planes.

La tabla completa de símbolos:

| Símbolo | Significado |
|---------|-------------|
| `+` | crear un recurso nuevo |
| `-` | destruir un recurso |
| `~` | actualizar en el sitio (in-place) |
| `-/+` | destruir y crear de nuevo (replacement) |

Ejecuta `terraform apply`, aprueba con `yes`, y verás en la salida `Destroying...` seguido de `Creating...`.

### terraform destroy: el botón de demolición

Cuando ya no necesitas la infraestructura, `terraform destroy` elimina **todos** los recursos gestionados por la configuración del directorio actual. Muestra un plan en modo destrucción (todo con `-`) y exige confirmación:

```text
$ terraform destroy

  # local_file.mascota will be destroyed
  - resource "local_file" "mascota" {
      - content         = "Ahora prefiero los perros" -> null
      - file_permission = "0777" -> null
      - filename        = "/root/mascotas.txt" -> null
      - id              = "b0a2c9..." -> null
    }

Plan: 0 to add, 0 to change, 1 to destroy.

Do you really want to destroy all resources?
  ...
  Enter a value: yes

local_file.mascota: Destroying... [id=b0a2c9...]
local_file.mascota: Destruction complete after 0s

Destroy complete! Resources: 1 destroyed.
```

Si quieres previsualizar la destrucción sin ejecutarla, usa `terraform plan -destroy`. Y en automatizaciones existe `-auto-approve` para saltarse la confirmación, tanto en `apply` como en `destroy`; úsalo con muchísimo respeto.

> 🔄 **Actualización:** en las versiones modernas, `terraform destroy` es formalmente un alias de `terraform apply -destroy`: el mismo motor de planes funcionando en "modo destrucción". No cambia nada en tu día a día, pero explica por qué ambos comandos comparten casi todas sus opciones.

> ⚠️ **Errores comunes:**
> - **Aprobar un plan sin buscar los `-/+`**: una recreación implica que el recurso desaparece durante unos instantes (o que sus datos se pierden). Busca siempre la frase *forces replacement*.
> - **Editar a mano el fichero creado** (con un editor, fuera de Terraform) y esperar que Terraform lo "vea": ese desajuste se llama *drift* y Terraform lo detectará al refrescar en el siguiente plan, proponiéndote volver al estado declarado. La fuente de verdad es el código, no el objeto.
> - **Ejecutar `destroy` en el directorio equivocado**: destruye todo lo que gestiona *esa* configuración. Comprueba con `pwd` dónde estás antes de teclearlo.
> - **Usar `-auto-approve` por pereza** en tu máquina: te acostumbra a no leer planes. Resérvalo para pipelines donde el plan ya fue revisado.

> 💡 **Buenas prácticas:**
> - Ejecuta siempre `terraform plan` antes de `apply`, aunque `apply` ya muestre el plan: separar los pasos te obliga a leer.
> - En equipos y CI, guarda el plan con `terraform plan -out=fichero.tfplan` y aplica exactamente ese fichero con `terraform apply fichero.tfplan`: garantiza que se ejecuta lo que se revisó (y trátalo como sensible: contiene datos en claro).
> - Destruye los entornos de práctica al terminar. Con providers locales no cuesta dinero, pero el hábito es oro cuando pases a cloud.

### 🧪 Laboratorio

**Enunciado:** partiendo del proyecto `primer-recurso` de la lección anterior (con `local_file.manifiesto` y `random_pet.alias` aplicados), realiza tres operaciones: (a) cambia el `content` del fichero a "El código también es infraestructura" y observa qué tipo de cambio propone el plan; (b) cambia el `length` de `random_pet` a `2` y comprueba si también fuerza recreación; (c) destruye todo.

**Solución:**

1. Edita ambos argumentos en `main.tf` y ejecuta `terraform plan`. Verás **dos** recursos marcados con `-/+`: en `local_file` el culpable es `content` (*forces replacement*) y en `random_pet` es `length`, porque un nombre de 1 palabra no puede "convertirse" en uno de 2: hay que generar otro. Resumen esperado: `Plan: 2 to add, 0 to change, 2 to destroy.`
2. `terraform apply` → `yes`. Comprueba con `cat manifiesto.txt` que el contenido es el nuevo y observa que el id del `random_pet` ha cambiado (ahora tiene dos palabras, p. ej. `lab_koala_valiente`).
3. `terraform destroy` → revisa que el plan lista los 2 recursos con `-` → `yes`. Verifica que `manifiesto.txt` ya no existe (`ls`). El fichero `terraform.tfstate` sigue ahí, pero ahora registra cero recursos.

> ❓ **Preguntas de repaso:**
> 1. **¿Qué diferencia hay entre `~` y `-/+` en un plan?** `~` es una actualización en el sitio (el recurso sobrevive); `-/+` es destruir y recrear, porque algún argumento no admite modificación en caliente.
> 2. **¿Cómo sabes qué argumento concreto ha provocado una recreación?** En el detalle del plan, ese argumento lleva el comentario `# forces replacement`.
> 3. **¿Qué comando te enseña qué se destruiría sin destruir nada?** `terraform plan -destroy`.

## 3.4 Laboratorio guiado: HCL básico

**¿Qué vas a aprender?** Esta lección es el equivalente al laboratorio de HCL del curso: un ejercicio integrador, 100 % local y sin cuenta cloud, donde repasarás la anatomía de HCL, el ciclo init/plan/apply, la lectura de planes y la depuración de errores de sintaxis. Trabaja sin mirar las soluciones hasta haberlo intentado: el objetivo es que los errores te los dé Terraform, no que los evites leyendo.

### Cómo abordar un laboratorio

Un laboratorio de Terraform es como una **receta de cocina que cocinas de verdad**: leerla no te enseña casi nada; mancharte, sí. La dinámica siempre es la misma: escribir configuración, ejecutar, leer con calma lo que Terraform responde (los mensajes de error de HCL son de los mejores del sector: indican fichero, línea y causa) y corregir. Crea un directorio limpio para este lab, por ejemplo `lab-hcl`.

### Ejercicio 1 — Disecciona un bloque

Sin ejecutar nada, responde sobre este código:

```hcl
resource "local_file" "juegos" {
  filename = "/root/favoritos/juegos.txt"
  content  = "FIFA 21"
}
```

¿Cuál es el tipo de bloque? ¿El tipo de recurso? ¿El provider implicado? ¿El nombre lógico? ¿Cuántos argumentos hay?

**Solución:** tipo de bloque `resource`; tipo de recurso `local_file`; provider `local` (el prefijo del tipo de recurso); nombre lógico `juegos`; dos argumentos (`filename` y `content`). Detalle extra: el directorio `/root/favoritos` no existe todavía, pero no fallará: el provider crea los directorios intermedios que falten.

### Ejercicio 2 — Arregla la configuración rota

Guarda este fichero como `main.tf` en `lab-hcl` e intenta aplicarlo. Contiene **tres errores**. Encuéntralos con ayuda de los mensajes de Terraform:

```hcl
resource "local_file" {
  filename = "./secreto.txt"
  contents = "clave: patata123"
}

resource "random_pet" "servidor" {
  prefix = "web"
  prefix = "app"
}
```

**Solución paso a paso:**

1. `terraform init` ya protesta: el primer bloque `resource` solo tiene una etiqueta. Un `resource` necesita exactamente dos: tipo y nombre lógico. Corrección: `resource "local_file" "secreto" {`.
2. Reejecuta. `terraform validate` (o el propio plan) señala el siguiente: el argumento `contents` no existe en `local_file`; se llama `content`. Los argumentos válidos de cada recurso están en su documentación del Registry; invéntate uno y Terraform lo rechazará con *"An argument named X is not expected here"*.
3. El tercero: `prefix` aparece dos veces en `random_pet`. Un argumento solo puede asignarse una vez por bloque. Deja solo `prefix = "web"`.

El fichero corregido:

```hcl
resource "local_file" "secreto" {
  filename = "./secreto.txt"
  content  = "clave: patata123"
}

resource "random_pet" "servidor" {
  prefix = "web"
}
```

4. Ahora sí: `terraform init`, `terraform plan` (comprueba: `Plan: 2 to add, 0 to change, 0 to destroy.`) y `terraform apply` con `yes`.

### Ejercicio 3 — Conecta los dos recursos (adelanto)

Como aperitivo de lo que estudiarás en el módulo siguiente: haz que el contenido del fichero incluya el nombre generado por `random_pet`. Modifica el `local_file`:

```hcl
resource "local_file" "secreto" {
  filename = "./secreto.txt"
  # Referencia al atributo exportado "id" del otro recurso:
  content  = "Servidor asignado: ${random_pet.servidor.id}"
}
```

**Solución:** al ejecutar `terraform plan` verás un `-/+` sobre el fichero (cambiar `content` fuerza recreación, como ya sabes). Tras el apply, `cat secreto.txt` mostrará algo como `Servidor asignado: web-alce`. La expresión `random_pet.servidor.id` es una **referencia**: la dirección del recurso más el atributo exportado `id`. Terraform deduce de ella que el fichero depende del nombre aleatorio y ordena las operaciones él solo, sin que tengas que indicárselo.

### Ejercicio 4 — Limpieza

Ejecuta `terraform plan -destroy` para previsualizar, y después `terraform destroy` con `yes`. Comprueba que `secreto.txt` ha desaparecido.

> ⚠️ **Errores comunes:**
> - **Corregir un error y no reejecutar `validate`/`plan`**: Terraform informa de los errores por tandas; arregla, reejecuta y repite hasta que la salida quede limpia.
> - **Copiar código con comillas tipográficas** (“ ”) desde documentos de texto: HCL exige comillas rectas (`"`). Usa siempre un editor de código.
> - **Escribir los argumentos de memoria**: ante la duda, consulta la página del recurso en registry.terraform.io; ahí está la lista exacta de argumentos requeridos y opcionales con sus valores por defecto.

> 💡 **Buenas prácticas:**
> - Adopta el ciclo corto `fmt → validate → plan` después de cada cambio; detecta el 90 % de los problemas antes de tocar nada real.
> - Mantén cada laboratorio en su propio directorio con su propio estado: te evita interferencias entre ejercicios.
> - Cuando un error no te cuadre, lee el mensaje **entero**: HCL te da fichero, número de línea y hasta un fragmento del código señalado.

### 🧪 Laboratorio

**Enunciado (reto final, sin guía):** crea desde cero un proyecto `inventario` que genere un fichero `inventario.txt` cuyo contenido sea `Entorno: ` seguido del id de un `random_pet` con prefijo `dev` y separador `-`. Requisitos: el plan inicial debe mostrar exactamente 2 recursos a crear, debes provocar después una recreación cambiando el prefijo a `pro`, y terminar con `terraform destroy`.

**Solución resumida:**

```hcl
resource "random_pet" "entorno" {
  prefix    = "dev"
  separator = "-"
}

resource "local_file" "inventario" {
  filename = "./inventario.txt"
  content  = "Entorno: ${random_pet.entorno.id}"
}
```

Secuencia: `init` → `plan` (verifica `2 to add`) → `apply` → editar `prefix = "pro"` → `plan` (verás `-/+` en **ambos** recursos: el pet se recrea por el prefijo y el fichero por su contenido, que depende de él) → `apply` → `destroy`. Si tu salida coincide, has completado el módulo: ya sabes escribir HCL, leer planes y gestionar el ciclo de vida completo de un recurso.

> ❓ **Preguntas de repaso:**
> 1. **¿Cuántas etiquetas lleva un bloque `resource` y qué representa cada una?** Dos: el tipo de recurso (que empieza por el nombre del provider) y el nombre lógico único que tú asignas.
> 2. **En el reto final, ¿por qué cambiar solo el `prefix` del `random_pet` recreó también el `local_file`?** Porque el contenido del fichero referencia `random_pet.entorno.id`; al recrearse el pet, su id cambia, el `content` del fichero cambia con él y ese argumento fuerza recreación.
> 3. **¿Dónde consultas la lista oficial de argumentos de un recurso como `local_file`?** En la documentación del provider dentro del Terraform Registry (registry.terraform.io), sección del recurso correspondiente.
