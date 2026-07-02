# Módulo 11 · Módulos de Terraform

Hasta ahora has escrito toda tu configuración en un único directorio de trabajo. Funciona, pero no escala: en cuanto un proyecto crece, ese enfoque se convierte en un problema. En este módulo aprenderás la herramienta que Terraform ofrece para organizar y reutilizar código: los **módulos**. Verás qué son, cómo crear los tuyos y cómo aprovechar los que la comunidad publica en el Terraform Registry.

## 11.1 ¿Qué son los módulos?

**¿Qué vas a aprender?** En esta lección entenderás por qué una configuración monolítica acaba siendo inmanejable, descubrirás que un módulo no es más que un directorio con ficheros `.tf`, y aprenderás la diferencia entre el *root module* (módulo raíz) y los *child modules* (módulos hijos). Con esto tendrás el modelo mental necesario para las dos lecciones siguientes.

### El problema: la configuración monolítica

Imagina que tu empresa despliega una aplicación de nóminas con servidores, bases de datos y almacenamiento, y que lo hace en tres entornos: desarrollo, staging y producción. Si lo escribes todo en un único `main.tf`, te encuentras con tres problemas clásicos:

1. **Complejidad**: un fichero con cientos de bloques `resource` es difícil de leer, navegar y mantener. Encontrar el recurso que quieres tocar se convierte en una búsqueda arqueológica.
2. **Duplicación**: los tres entornos son casi idénticos, así que acabas copiando y pegando bloques enteros cambiando cuatro valores. Cada mejora hay que aplicarla tres veces, y tarde o temprano los entornos divergen sin que nadie sepa por qué.
3. **Riesgo**: todo vive en el mismo estado y en la misma configuración. Un despiste editando el recurso de desarrollo puede provocar que un `terraform apply` toque también producción. Cuanto mayor es el radio de acción de cada cambio, mayor es la probabilidad de accidente.

La analogía que a mí me lo dejó claro es la de una **urbanización de chalets**: si el arquitecto dibujara desde cero el plano completo de cada una de las 40 casas, tardaría meses y cometería errores distintos en cada plano. Lo que hace en realidad es diseñar **un plano maestro parametrizable** (color de fachada, número de habitaciones, orientación) y lo instancia 40 veces. El plano maestro es el módulo; cada casa, una llamada al módulo con sus parámetros.

### Qué es exactamente un módulo

La definición oficial es sorprendentemente simple: un módulo es una **colección de recursos que Terraform gestiona juntos**; en la práctica, **cualquier directorio que contenga ficheros `.tf`** es un módulo. No hay que declarar nada especial ni activar ninguna opción.

Esto tiene una consecuencia importante: **ya llevas todo el curso escribiendo módulos sin saberlo**. El directorio de trabajo donde ejecutas `terraform init`, `plan` y `apply` es lo que Terraform llama el **root module** (módulo raíz). Cuando desde ese módulo raíz invocas otro directorio con un bloque `module`, ese otro directorio pasa a ser un **child module** (módulo hijo). Los módulos hijos pueden, a su vez, llamar a otros módulos, y puedes invocar el mismo módulo varias veces con parámetros distintos.

| Concepto | Qué es |
|---|---|
| Root module | El directorio donde ejecutas los comandos de Terraform. Siempre existe. |
| Child module | Un directorio con `.tf` invocado desde otro módulo mediante un bloque `module`. |
| Módulo publicado | Un módulo distribuido en un registry (público o privado) para que otros lo consuman. |

La invocación tiene esta pinta (la veremos en detalle en 11.2):

```hcl
# main.tf del módulo raíz
# El bloque "module" invoca un módulo hijo. La etiqueta ("nominas_des")
# es el nombre local de ESTA llamada, no el nombre del módulo en disco.
module "nominas_des" {
  # source indica dónde vive el código del módulo; debe ser una cadena
  # literal (no admite expresiones ni variables normales).
  source = "./modules/servidor-aplicacion"

  # Estos argumentos son las variables de entrada del módulo hijo.
  nombre_app = "nominas"
  entorno    = "desarrollo"
}
```

Fíjate en el matiz: el módulo no se "instala" en tu configuración como una librería global; se **instancia**. Cada bloque `module` crea una copia independiente de los recursos que el módulo define, igual que cada chalet construido a partir del plano maestro es una casa distinta.

> ⚠️ **Errores comunes:**
> - **Creer que un módulo requiere una sintaxis o fichero especial.** No: un directorio con `.tf` ya es un módulo. Lo único nuevo es el bloque `module` para invocarlo.
> - **Confundir la etiqueta del bloque `module` con el nombre del directorio.** La etiqueta es un identificador local de tu configuración; puedes llamar `module "a"` y `module "b"` al mismo directorio.
> - **Trocear por trocear.** Dividir un monolito en veinte módulos de un solo recurso no reduce la complejidad, la reparte. Un módulo debe agrupar recursos que forman una unidad lógica (por ejemplo, "un servidor de aplicación completo").

> 💡 **Buenas prácticas:**
> - Empieza siempre con todo en el módulo raíz y **extrae módulos cuando detectes duplicación real**, no antes.
> - Diseña cada módulo alrededor de un propósito claro que puedas describir en una frase ("crea la configuración de un servicio con nombre único").
> - Piensa en los módulos como en funciones de programación: entradas (variables), lógica (recursos) y salidas (outputs). Si te cuesta nombrar el módulo, probablemente agrupa cosas que no van juntas.

### 🧪 Laboratorio

**Enunciado**: en un directorio nuevo, crea un `main.tf` con estos dos recursos casi idénticos y razona (por escrito, en un comentario) qué extraerías a un módulo y qué parámetros tendría.

```hcl
resource "local_file" "bienvenida_des" {
  filename = "${path.module}/des-bienvenida.txt"
  content  = "Bienvenido a nominas en el entorno desarrollo"
}

resource "local_file" "bienvenida_pro" {
  filename = "${path.module}/pro-bienvenida.txt"
  content  = "Bienvenido a nominas en el entorno produccion"
}
```

**Solución**: los dos bloques solo se diferencian en el entorno (`des`/`desarrollo` frente a `pro`/`produccion`). El candidato a módulo es "fichero de bienvenida de una aplicación", con dos variables de entrada: `nombre_app` (aquí constante, `nominas`, pero parametrizable) y `entorno`. El recurso quedaría escrito una sola vez dentro del módulo y lo invocarías dos veces. Además, este directorio donde acabas de trabajar **ya es un módulo**: el módulo raíz. En la siguiente lección haremos exactamente esta extracción, con un ejemplo más completo.

> ❓ **Preguntas de repaso:**
> 1. **¿Qué convierte a un directorio en un módulo de Terraform?** Simplemente contener ficheros `.tf`. No hace falta ninguna declaración adicional.
> 2. **¿Qué es el root module?** El directorio de trabajo desde el que ejecutas los comandos de Terraform. Toda configuración tiene uno, aunque no invoque ningún módulo hijo.
> 3. **¿Qué tres problemas de las configuraciones monolíticas resuelven los módulos?** La complejidad (código más pequeño y navegable), la duplicación (un plano maestro reutilizable en vez de copia-pega) y el riesgo (cambios con un radio de acción acotado).

## 11.2 Crear y usar tu propio módulo

**¿Qué vas a aprender?** Aquí pasamos a la práctica: crearás desde cero un módulo reutilizable llamado `servidor-aplicacion`, lo invocarás dos veces desde el módulo raíz con parámetros distintos, le pasarás variables, leerás sus outputs con `module.<nombre>.<output>` y entenderás qué hacen `terraform init` y `terraform get` con los módulos.

### Diseño del módulo

Vamos a construir un módulo que representa "un servidor de aplicación": genera un nombre único de servidor y escribe su fichero de configuración. Para que puedas practicarlo **sin cuenta en la nube** usaremos los providers `random` y `local`; el patrón es idéntico al que usarías con un `aws_instance` (te lo enseño al final de la lección).

Piensa en el módulo como en un **electrodoméstico con enchufes**: las variables son las clavijas de entrada (tú decides qué corriente le das), los recursos son la maquinaria interna (no la tocas), y los outputs son las salidas que el fabricante decidió exponer. Nada más entra ni sale: eso se llama encapsulación, y es lo que hace que un módulo sea seguro de reutilizar.

La estructura de directorios recomendada por HashiCorp coloca los módulos hijos bajo `modules/`, y cada módulo con tres ficheros mínimos (más un `README.md` si lo vas a compartir):

```text
proyecto/
├── main.tf                        <- módulo raíz: invoca al módulo hijo
├── outputs.tf                     <- outputs del módulo raíz
└── modules/
    └── servidor-aplicacion/
        ├── main.tf                <- recursos del módulo
        ├── variables.tf           <- entradas del módulo
        └── outputs.tf             <- salidas del módulo
```

### El código del módulo hijo

`modules/servidor-aplicacion/variables.tf`:

```hcl
# Las variables de un módulo son su "interfaz de entrada".
# Una variable SIN default se convierte en argumento obligatorio
# para quien invoque el módulo.
variable "nombre_app" {
  description = "Nombre de la aplicación que ejecuta este servidor"
  type        = string
}

variable "entorno" {
  description = "Entorno de despliegue: desarrollo, staging o produccion"
  type        = string
  default     = "desarrollo" # con default, el argumento es opcional
}

variable "puerto" {
  description = "Puerto TCP en el que escucha la aplicación"
  type        = number
  default     = 8080
}
```

`modules/servidor-aplicacion/main.tf`:

```hcl
# Un módulo reutilizable debe DECLARAR qué providers necesita,
# pero no configurarlos: la configuración vive en el módulo raíz.
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

# Nombre único de servidor, p. ej. "nominas-relaxed-panda".
resource "random_pet" "servidor" {
  prefix = var.nombre_app
  length = 2
}

# Fichero de configuración del servidor.
# OJO: path.module apunta al directorio DEL MÓDULO; path.root, al
# directorio del módulo raíz. Aquí queremos los ficheros generados
# junto a la configuración raíz, no dentro de modules/.
resource "local_file" "configuracion" {
  filename = "${path.root}/generado/${var.entorno}-${var.nombre_app}.cfg"
  content  = <<-EOT
    # Generado por Terraform: no editar a mano
    servidor   = ${random_pet.servidor.id}
    aplicacion = ${var.nombre_app}
    entorno    = ${var.entorno}
    puerto     = ${var.puerto}
  EOT
}
```

`modules/servidor-aplicacion/outputs.tf`:

```hcl
# Los outputs son la ÚNICA vía por la que el exterior puede leer
# valores de este módulo. Lo que no se exporta aquí, no existe fuera.
output "nombre_servidor" {
  description = "Identificador único generado para el servidor"
  value       = random_pet.servidor.id
}

output "ruta_configuracion" {
  description = "Ruta del fichero de configuración generado"
  value       = local_file.configuracion.filename
}
```

### Invocar el módulo desde el módulo raíz

`main.tf` (raíz):

```hcl
# Dos instancias del MISMO módulo con parámetros distintos:
# esta es la reutilización que perseguíamos.
module "nominas_des" {
  # Ruta local: debe empezar por ./ o ../ para que Terraform
  # la reconozca como directorio local y no como módulo de registry.
  source = "./modules/servidor-aplicacion"

  nombre_app = "nominas"
  # entorno y puerto usan sus defaults: desarrollo y 8080
}

module "nominas_pro" {
  source = "./modules/servidor-aplicacion"

  nombre_app = "nominas"
  entorno    = "produccion"
  puerto     = 443
}
```

`outputs.tf` (raíz):

```hcl
# Sintaxis para leer un output de un módulo hijo:
# module.<etiqueta>.<nombre_del_output>
output "servidor_desarrollo" {
  value = module.nominas_des.nombre_servidor
}

output "config_produccion" {
  value = module.nominas_pro.ruta_configuracion
}
```

### init, get, plan y apply

Cada vez que añades un bloque `module` o cambias su `source`, tienes que ejecutar `terraform init` para que Terraform instale el módulo (y los providers que este requiera):

```text
$ terraform init

Initializing the backend...
Initializing modules...
- nominas_des in modules/servidor-aplicacion
- nominas_pro in modules/servidor-aplicacion

Initializing provider plugins...
- Finding hashicorp/random versions matching "~> 3.6"...
- Finding hashicorp/local versions matching "~> 2.5"...
...
Terraform has been successfully initialized!
```

Existe también `terraform get`, que descarga y actualiza **solo** los módulos (los deja bajo el directorio `.terraform`, que no debes subir al control de versiones), sin tocar providers ni backend. Acepta el flag `-update` para refrescar módulos ya descargados. En el día a día casi siempre usarás `init`, que lo hace todo; `get` es útil cuando solo has cambiado módulos y quieres una operación más rápida.

Con `terraform plan` verás que las direcciones de los recursos ahora incluyen el prefijo del módulo:

```text
$ terraform plan
...
  # module.nominas_des.local_file.configuracion will be created
  # module.nominas_des.random_pet.servidor will be created
  # module.nominas_pro.local_file.configuracion will be created
  # module.nominas_pro.random_pet.servidor will be created

Plan: 4 to add, 0 to change, 0 to destroy.
```

Y tras `terraform apply -auto-approve`:

```text
Apply complete! Resources: 4 added, 0 changed, 0 destroyed.

Outputs:

config_produccion = "./generado/produccion-nominas.cfg"
servidor_desarrollo = "nominas-relaxed-panda"
```

El mismo patrón, con AWS, sería un módulo cuyo `main.tf` contiene un `aws_instance` parametrizado (`ami`, `instance_type`, etc. como variables) y cuyo output expone, por ejemplo, la IP privada. Solo cambia la maquinaria interna; los enchufes funcionan igual:

```hcl
# Fragmento ilustrativo (requeriría cuenta AWS): mismo patrón de módulo
resource "aws_instance" "app" {
  ami           = var.ami
  instance_type = var.tipo_instancia
  tags          = { Name = "${var.nombre_app}-${var.entorno}" }
}
```

> ⚠️ **Errores comunes:**
> - **Intentar leer recursos internos del módulo desde la raíz** (`module.nominas_des.random_pet.servidor` no es una referencia válida en tus expresiones). Solo puedes consumir lo que el módulo exporta como `output`.
> - **Olvidar `terraform init` tras añadir un módulo o cambiar `source`**: obtendrás un error del tipo `Module not installed`. Ejecuta `init` y listo.
> - **Usar `version` en un módulo local**: el argumento `version` solo es válido para módulos de registry. Para módulos locales, la "versión" es la del propio repositorio Git.
> - **Rutas relativas dentro del módulo sin `path.module`/`path.root`**: una ruta "a pelo" se resuelve de forma frágil. Sé explícito: `path.module` para ficheros del módulo, `path.root` para el directorio raíz.

> 💡 **Buenas prácticas:**
> - Sigue la estructura estándar (`main.tf`, `variables.tf`, `outputs.tf`, `README.md`) y pon una `description` de una o dos frases a **todas** las variables y outputs: es la documentación de tu interfaz.
> - No configures providers dentro de módulos reutilizables (nada de bloques `provider` con credenciales o región); decláralos en `required_providers` y deja la configuración al módulo raíz.
> - Da `default` solo a las variables con un valor razonable universal; lo que deba decidirse conscientemente (como `entorno`) mejor obligatorio.
> - Exporta como outputs todo lo que un consumidor pueda necesitar encadenar (IDs, rutas, nombres), aunque hoy no lo uses.

### 🧪 Laboratorio

**Enunciado**: crea un módulo `ficha-entorno` que genere un fichero JSON descriptivo de un entorno. Debe aceptar `nombre_entorno` (obligatorio) y `puerto_base` (opcional, default `3000`), elegir un puerto aleatorio entre `puerto_base` y `puerto_base + 999`, y escribir `<nombre_entorno>.json` con el nombre y el puerto. Exporta el puerto como output. Invócalo para `desarrollo` y `produccion` (este último con `puerto_base = 8000`) y muestra ambos puertos como outputs de la raíz.

**Solución paso a paso**:

1. Crea la estructura: `proyecto-lab/modules/ficha-entorno/` con sus tres ficheros, y `main.tf` en la raíz.

2. `modules/ficha-entorno/variables.tf`:

```hcl
variable "nombre_entorno" {
  description = "Nombre del entorno a describir"
  type        = string
}

variable "puerto_base" {
  description = "Inicio del rango de puertos del entorno"
  type        = number
  default     = 3000
}
```

3. `modules/ficha-entorno/main.tf`:

```hcl
resource "random_integer" "puerto" {
  min = var.puerto_base
  max = var.puerto_base + 999
}

resource "local_file" "ficha" {
  filename = "${path.root}/${var.nombre_entorno}.json"
  content = jsonencode({
    entorno = var.nombre_entorno
    puerto  = random_integer.puerto.result
  })
}
```

4. `modules/ficha-entorno/outputs.tf`:

```hcl
output "puerto" {
  description = "Puerto asignado al entorno"
  value       = random_integer.puerto.result
}
```

5. `main.tf` de la raíz:

```hcl
module "des" {
  source         = "./modules/ficha-entorno"
  nombre_entorno = "desarrollo"
}

module "pro" {
  source         = "./modules/ficha-entorno"
  nombre_entorno = "produccion"
  puerto_base    = 8000
}

output "puerto_des" { value = module.des.puerto }
output "puerto_pro" { value = module.pro.puerto }
```

6. Ejecuta `terraform init` (verás `- des in modules/ficha-entorno` y `- pro in ...`), después `terraform apply -auto-approve`:

```text
Apply complete! Resources: 4 added, 0 changed, 0 destroyed.

Outputs:

puerto_des = 3417
puerto_pro = 8852
```

7. Comprueba que existen `desarrollo.json` y `produccion.json` y termina con `terraform destroy -auto-approve`.

> ❓ **Preguntas de repaso:**
> 1. **¿Cómo accedes desde el módulo raíz al output `puerto` de la llamada `module "des"`?** Con `module.des.puerto`.
> 2. **¿Qué diferencia hay entre `terraform init` y `terraform get` respecto a los módulos?** Ambos instalan/actualizan los módulos declarados, pero `init` además inicializa backend y providers; `get` se limita a los módulos (con `-update` refresca los ya descargados).
> 3. **¿Qué requisito tiene el `source` de un módulo local?** Debe ser una cadena literal (sin expresiones) y empezar por `./` o `../`.

## 11.3 Usar módulos del Terraform Registry

**¿Qué vas a aprender?** No siempre hay que escribir los módulos: en [registry.terraform.io](https://registry.terraform.io) hay miles ya publicados. Aprenderás a identificarlos por su `source` de tres partes, a fijar su `version`, a usar sus submódulos con la sintaxis `//` y a distinguir los módulos con badge de partner de los módulos de la comunidad.

### El Registry: la tienda de módulos

Si en 11.2 hiciste de carpintero fabricando tu propio mueble, el Registry es **la tienda de muebles**: piezas ya diseñadas, documentadas y probadas por miles de usuarios, listas para montar con tus parámetros. El Terraform Registry público aloja tanto providers (que ya conoces) como módulos, con su documentación de inputs, outputs, dependencias y ejemplos.

Hay dos grandes categorías:

- **Módulos de partners** (con badge *Partner*): publicados y mantenidos por partners tecnológicos de HashiCorp, que los revisa para garantizar estabilidad y compatibilidad. Puedes filtrar por ellos en el buscador.
- **Módulos de la comunidad**: publicados por cualquiera. Aquí están algunos de los más usados del ecosistema, como los del *namespace* (el espacio de nombres que identifica a quien publica, similar a una cuenta u organización) `terraform-aws-modules` (su módulo de VPC supera los 195 millones de descargas).

> 🔄 **Actualización:** cuando se grabó el curso, el Registry marcaba estos módulos revisados como *verified modules*, con una marca azul. Hoy ese distintivo se llama **badge de Partner** (la API del Registry aún conserva el parámetro `verified` para filtrarlos). La idea es la misma: un sello de revisión y mantenimiento, no una garantía de que sea el mejor módulo para tu caso.

### Invocar un módulo del Registry

Para módulos del Registry público, el `source` tiene el formato de tres partes `<NAMESPACE>/<NAME>/<PROVIDER>` y, a diferencia de los módulos locales, admite (y pide a gritos) el argumento `version`. Ejemplo real con el módulo de VPC más popular (última versión 6.6.1 al escribir esto):

```hcl
# providers.tf — el módulo usa el provider aws, que configura la RAÍZ
provider "aws" {
  region = "eu-west-1"
}

# main.tf
module "red_principal" {
  # namespace / nombre / provider objetivo
  source = "terraform-aws-modules/vpc/aws"
  # Restricción de versión: "~> 6.6" acepta 6.6.x y 6.7.x,
  # pero nunca 7.0. Terraform usa la versión más reciente
  # que cumpla la restricción.
  version = "~> 6.6"

  # Inputs documentados en la pestaña "Inputs" del Registry
  name = "vpc-curso"
  cidr = "10.0.0.0/16"

  azs             = ["eu-west-1a", "eu-west-1b"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24"]

  enable_nat_gateway = false # los NAT Gateway cuestan dinero
}

# Los outputs del módulo se consumen igual que con tus módulos
output "vpc_id" {
  value = module.red_principal.vpc_id
}
```

Este bloque `module` de ~10 líneas sustituye a decenas de recursos (`aws_vpc`, `aws_subnet`, `aws_route_table`, `aws_internet_gateway`...) que el módulo crea y cablea por ti. Al ejecutar `terraform init`, Terraform lo descarga a `.terraform/modules/`:

```text
$ terraform init

Initializing the backend...
Initializing modules...
Downloading registry.terraform.io/terraform-aws-modules/vpc/aws 6.6.1 for red_principal...
- red_principal in .terraform/modules/red_principal

Initializing provider plugins...
- Finding hashicorp/aws versions matching ">= 6.28"...
...
Terraform has been successfully initialized!
```

Fíjate en que el propio módulo arrastra su requisito de provider (`aws >= 6.28` en este caso): el Registry lo documenta en la pestaña *Dependencies*.

### Submódulos

Muchos paquetes de módulos incluyen **submódulos** bajo su directorio `modules/`, variantes especializadas listadas en la pestaña *Submodules* del Registry. Para apuntar a un subdirectorio dentro del paquete se usa `//` en el `source`. Por ejemplo, el módulo `terraform-aws-modules/security-group/aws` (versión 6.0.0) trae submódulos preconfigurados para servicios concretos (`ssh`, `http-80`, `postgresql`...):

```hcl
module "sg_postgresql" {
  # Todo lo que sigue a "//" es un subdirectorio DENTRO del paquete
  source  = "terraform-aws-modules/security-group/aws//modules/postgresql"
  version = "~> 6.0"

  name        = "postgresql"
  description = "Acceso a PostgreSQL desde la VPC"
  vpc_id      = module.red_principal.vpc_id

  ingress_cidr_ipv4 = {
    vpc = "10.0.0.0/16"
  }
}
```

El submódulo ya trae las reglas de entrada típicas de PostgreSQL; tú solo aportas de dónde se permite el tráfico. Menos código, menos errores.

> ⚠️ **Errores comunes:**
> - **Omitir `version`**: sin restricción, cada `init` en una máquina nueva puede traer una versión distinta, incluida una major con cambios incompatibles. Fija siempre versión.
> - **Copiar el ejemplo del README de la rama principal con una versión antigua fijada**: los inputs cambian entre majors (por ejemplo, los submódulos de security-group renombraron argumentos en la v6). Consulta la documentación **de la versión que instalas**.
> - **Usar un módulo sin leer sus inputs y outputs**: asumir que "creará lo que necesito" acaba en sorpresas. Revisa qué es obligatorio, qué es opcional y qué expone.
> - **Intentar poner `version` a un módulo Git o local**: solo los módulos de registry lo soportan; en Git se fija con `?ref=` en la URL.

> 💡 **Buenas prácticas:**
> - Usa el operador pesimista `~>` para recibir parches y minors sin saltos de major inesperados.
> - Antes de adoptar un módulo, echa un vistazo a su repositorio (todos enlazan a su código fuente): actividad reciente, issues abiertas y número de descargas son buenos indicadores de salud.
> - Prefiere módulos con badge Partner o con adopción masiva y mantenimiento activo; para lógica muy específica de tu empresa, escribe el tuyo (ya sabes cómo).
> - Trata los módulos del Registry como dependencias de software: actualízalos de forma deliberada, leyendo el changelog, no "cuando toque".

### 🧪 Laboratorio

**Enunciado**: sin necesidad de cuenta AWS, prepara una configuración que use el módulo `terraform-aws-modules/vpc/aws` fijado a `~> 6.6`, descárgalo con `terraform init`, valida la sintaxis y explora dónde ha quedado instalado el código del módulo.

**Solución paso a paso**:

1. Entra en `registry.terraform.io`, busca `vpc`, abre el módulo del namespace `terraform-aws-modules` y revisa sus pestañas *Inputs*, *Outputs* y *Submodules*: así se estudia cualquier módulo antes de usarlo.
2. En un directorio nuevo, crea `main.tf` con el bloque `provider "aws"` y el bloque `module "red_principal"` del ejemplo de esta lección.
3. Ejecuta `terraform init`. No necesitas credenciales para este paso: descarga el módulo y el provider. Verás la línea `Downloading registry.terraform.io/terraform-aws-modules/vpc/aws 6.6.x for red_principal...`.
4. Ejecuta `terraform validate`; debe responder `Success! The configuration is valid.` (un `plan` o `apply` ya sí exigiría credenciales de AWS).
5. Explora `.terraform/modules/`: encontrarás el directorio `red_principal` con el código fuente completo del módulo y un fichero `modules.json` que actúa de manifiesto (qué módulos hay instalados, de dónde vienen y en qué versión). Abre el `main.tf` del módulo y cuenta cuántos recursos te has ahorrado escribir.
6. Limpieza: como no has aplicado nada, basta con borrar el directorio.

> ❓ **Preguntas de repaso:**
> 1. **¿Qué formato tiene el `source` de un módulo del Registry público?** Tres partes: `NAMESPACE/NAME/PROVIDER`, por ejemplo `terraform-aws-modules/vpc/aws`.
> 2. **¿Para qué sirve `//` en un `source`?** Indica que lo que sigue es un subdirectorio dentro del paquete del módulo; es la forma de invocar submódulos, como `...security-group/aws//modules/postgresql`.
> 3. **¿Qué significa hoy el badge de un módulo "verificado"?** Es el badge *Partner*: el módulo lo publica y mantiene un partner de HashiCorp y ha pasado su revisión de estabilidad y compatibilidad. Los módulos comunitarios sin badge pueden ser igualmente excelentes (mira descargas y mantenimiento).

---

📌 **Resumen del módulo**: un módulo es cualquier directorio con ficheros `.tf`; tu directorio de trabajo es el root module y los que invocas con bloques `module` son child modules. Un módulo bien diseñado es una función: variables de entrada, recursos dentro y outputs que consumes con `module.<nombre>.<output>`. Y antes de escribir uno, mira el Registry: probablemente alguien ya lo ha construido, versionado y probado por ti.
