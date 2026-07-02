# Módulo 1 · Introducción al curso

## 1.1 Bienvenida y mapa del curso

**¿Qué vas a aprender?** En esta primera lección te presento el manual, te explico cómo está organizado y te doy el mapa completo de los 13 módulos que vas a recorrer. Al terminarla sabrás qué te espera, en qué orden y con qué nivel de profundidad, para que estudies con intención y no a ciegas.

Bienvenido, Pablo. Este manual está pensado para alguien como tú: desarrollador que sabe programar pero nunca ha "tocado hierro". La buena noticia es que Terraform convierte la infraestructura en algo que ya dominas: **ficheros de texto versionables**. Piensa en el curso como aprender a conducir: primero entiendes por qué existe el coche (Módulos 1-2), luego arrancas en un parking vacío (3-6), después sales a carretera real con AWS (7-9) y por último aprendes maniobras avanzadas (10-13).

### El temario completo

| Nº | Módulo | Qué cubre |
|----|--------|-----------|
| 1 | Introducción | Presentación y recursos |
| 2 | Introducción a IaC | Problemas tradicionales, familias de herramientas, por qué Terraform |
| 3 | Primeros pasos con Terraform | Instalación, HCL básico, primer `apply` |
| 4 | Fundamentos de Terraform | Providers, variables, atributos, dependencias |
| 5 | Estado | Qué es el *state*, para qué sirve y sus riesgos |
| 6 | Trabajando con Terraform | Comandos, ciclo de vida, *datasources* (fuentes de datos) |
| 7 | Terraform con AWS | IAM, S3, DynamoDB, EC2 |
| 8 | Estado remoto | Backends remotos y bloqueo de estado |
| 9 | Provisioners | Ejecutar scripts al crear recursos |
| 10 | Import, Taint y Debugging | Adoptar recursos existentes, forzar recreación, logs |
| 11 | Módulos | Reutilizar y organizar código |
| 12 | Funciones y condicionales | Expresiones, bucles y lógica |
| 13 | Conclusión | Cierre y siguientes pasos |

Los módulos 1-6 y 10-13 se practican **en local**, sin gastar un céntimo, usando los *providers* (los plugins que conectan Terraform con cada plataforma; los estudiarás a fondo en el módulo 4) `local` y `random`. Solo los módulos 7-9 requieren una cuenta de AWS.

> 🔄 **Actualización:** el curso original en el que se basa este manual se grabó con una versión de Terraform anterior a la actual. Este manual está escrito y verificado para el **Terraform 1.x actual**. Cuando algo haya cambiado (por ejemplo, `terraform refresh` o `terraform taint` están obsoletos), lo señalaré con una caja como esta en la lección correspondiente.

Para abrir boca, así es el código que escribirás en pocos días:

```hcl
# Genera un nombre aleatorio tipo "adjetivo-animal" (provider random)
resource "random_pet" "mi_servidor" {
  length = 2 # número de palabras del nombre (2 es el valor por defecto)
}

# Crea un fichero local con ese nombre dentro (provider local)
resource "local_file" "saludo" {
  filename = "${path.module}/saludo.txt"
  content  = "Hola, soy ${random_pet.mi_servidor.id}"
}
```

> ⚠️ **Errores comunes:**
> - **Leer sin teclear.** Terraform se aprende ejecutando `plan` y `apply`, no memorizando. Haz todos los laboratorios.
> - **Saltarte los módulos conceptuales** (este y el 2). Sin ellos, los comandos parecen magia y la magia se olvida.
> - **Copiar código de blogs antiguos** con sintaxis de Terraform 0.11 (sin comillas en tipos, `"${var.x}"` en todas partes). Contrasta siempre con la documentación oficial.

> 💡 **Buenas prácticas:**
> - Crea una carpeta por lección (`m03-l01`, `m03-l02`...) y guárdala en Git desde el día uno: la infraestructura como código merece control de versiones como cualquier código.
> - Después de cada laboratorio, destruye lo creado con `terraform destroy` para empezar limpio.
> - Anota tus propias dudas al margen; las resolverás casi todas antes del módulo 6.

### 🧪 Laboratorio

**Enunciado:** prepara tu espacio de trabajo: crea la carpeta raíz del curso con una subcarpeta por módulo y un `README.md` con el temario.

**Solución:**
1. Crea la carpeta raíz: `mkdir terraform-curso` y entra en ella.
2. Crea las subcarpetas `modulo-01` … `modulo-13` (en PowerShell: `1..13 | ForEach-Object { mkdir ("modulo-{0:d2}" -f $_) }`).
3. Crea `README.md` y pega la tabla del temario de arriba.
4. Inicializa Git: `git init` y haz tu primer commit. Ya tienes el esqueleto del curso versionado.

> ❓ **Preguntas de repaso:**
> 1. **¿Qué módulos necesitan cuenta de AWS?** Solo el 7, el 8 y el 9; el resto se practica en local con los providers `local` y `random`.
> 2. **¿Por qué conviene versionar las prácticas en Git?** Porque la IaC (*Infrastructure as Code*, infraestructura como código) trata la infraestructura como código: versionarla te da historial, reversibilidad y revisión, exactamente los beneficios que buscamos.

## 1.2 Recursos para seguir el curso

**¿Qué vas a aprender?** Aquí montamos tu "mochila" de estudio: qué software instalar, qué documentación oficial usar como referencia y cómo verificar que todo funciona antes del Módulo 3. Es una lección corta, pero evita el 90 % de los tropiezos iniciales.

Igual que no sales de ruta sin botas y cantimplora, no empieces con Terraform sin estas cuatro cosas:

1. **Terraform CLI**: descárgalo de `developer.hashicorp.com/terraform/install`. Es un único binario; en Windows también puedes usar `winget install Hashicorp.Terraform`.
2. **Un editor**: VS Code con la extensión oficial **HashiCorp Terraform** (autocompletado, validación y formateo de HCL).
3. **La documentación oficial**: `developer.hashicorp.com/terraform` (lenguaje y CLI) y `registry.terraform.io` (documentación de cada provider). Serán tus dos pestañas fijas.
4. **Una terminal y Git**: cualquier shell vale; Terraform es idéntico en Windows, macOS y Linux.

Comprueba la instalación:

```text
$ terraform version
Terraform v1.15.7
on windows_amd64
```

(La versión exacta variará; cualquier 1.x reciente sirve para este manual.)

Desde el primer día te acostumbrarás a fijar versiones en un fichero `versions.tf`. Así tu código declara qué necesita para funcionar, igual que un `package.json`:

```hcl
terraform {
  # Exigimos Terraform 1.5 o superior (usaremos bloques "import" más adelante)
  required_version = ">= 1.5.0"

  required_providers {
    # Provider "local": crea y lee ficheros en tu máquina
    local = {
      source  = "hashicorp/local"
      version = "~> 2.0" # cualquier 2.x
    }
    # Provider "random": genera valores aleatorios reproducibles
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }
}
```

> ⚠️ **Errores comunes:**
> - **No añadir el binario al PATH** en Windows: `terraform` "no se reconoce como comando". Con `winget` o un gestor de paquetes te lo ahorras.
> - **Instalar la extensión equivocada** de VS Code: la oficial es la de HashiCorp, no clones con nombres parecidos.
> - **Estudiar con documentación de terceros desactualizada**: la sintaxis cambió mucho entre 0.11 y 1.x. Ante la duda, manda la documentación oficial.

> 💡 **Buenas prácticas:**
> - Fija `required_version` y versiones de providers en todos tus proyectos: te protege de sorpresas cuando salga una versión nueva.
> - Ejecuta `terraform fmt` antes de cada commit para mantener formato canónico.
> - Guarda en marcadores la página del provider que uses: cada argumento que escribas debería estar verificado ahí.

### 🧪 Laboratorio

**Enunciado:** instala Terraform, verifica la versión y crea tu primer proyecto inicializado (sin recursos todavía).

**Solución:**
1. Instala Terraform y ejecuta `terraform version`; confirma que ves `v1.x`.
2. En `modulo-01/`, crea el fichero `versions.tf` con el contenido del ejemplo anterior.
3. Ejecuta `terraform init`. Verás algo así:

```text
Initializing provider plugins...
- Installing hashicorp/local v2.9.0...
- Installing hashicorp/random v3.9.0...

Terraform has been successfully initialized!
```

4. Observa que ha aparecido una carpeta `.terraform/` (los providers descargados) y un fichero `.terraform.lock.hcl` (versiones exactas bloqueadas). Este `init` lo repetirás en cada proyecto nuevo.

> ❓ **Preguntas de repaso:**
> 1. **¿De dónde descarga `terraform init` los providers?** Del Terraform Registry (`registry.terraform.io`), según lo declarado en `required_providers`.
> 2. **¿Para qué sirve `required_version`?** Para impedir que el proyecto se ejecute con una versión de Terraform incompatible con la sintaxis que usas.
> 3. **¿Qué dos webs oficiales serán tu referencia constante?** `developer.hashicorp.com/terraform` para lenguaje/CLI y `registry.terraform.io` para providers.

# Módulo 2 · Introducción a Infrastructure as Code

## 2.1 Desafíos de la infraestructura TI tradicional

**¿Qué vas a aprender?** Antes de amar la solución hay que sufrir el problema. En esta lección verás cómo se aprovisionaba (y en muchas empresas aún se aprovisiona) la infraestructura: tickets, esperas de semanas, configuración manual y entornos que nunca coinciden. Así entenderás qué dolor viene a curar la IaC.

Imagina pedir una pizza **por carta postal**: escribes el pedido, alguien lo lee días después, lo transcribe a mano, se equivoca con los ingredientes y tres semanas más tarde llega una pizza parecida-pero-no-igual. Absurdo, ¿verdad? Pues así funcionaba (y funciona) el flujo tradicional:

1. **El negocio pide una aplicación nueva** y el equipo estima qué máquinas necesita.
2. **Se abre un ticket** a infraestructura, que lanza una orden de compra de hardware.
3. **Semanas o meses de espera**: entrega, montaje en rack, cableado, sistema operativo.
4. **Configuración manual**: un técnico sigue (con suerte) un documento de pasos; cada campo tecleado a mano es una oportunidad de error.
5. **Repetir para cada entorno**: desarrollo, preproducción y producción los montan personas distintas en momentos distintos… y quedan sutilmente diferentes. Nace el clásico *"en mi máquina funciona"*.

Los problemas de fondo: **lentitud** (semanas para lo que hoy tarda minutos), **coste** (hardware sobredimensionado "por si acaso"), **error humano** (procesos no reproducibles), **inconsistencia entre entornos** (servidores "copo de nieve", únicos e irrepetibles) y **falta de trazabilidad** (¿quién cambió qué y cuándo? Nadie lo sabe).

La nube resolvió la parte física —una API crea una máquina virtual en minutos—, pero **clicar en una consola web sigue siendo un proceso manual**: no queda registro, no es repetible y no escala. La respuesta es describir la infraestructura en ficheros de código:

```hcl
# En lugar de un ticket que dice "necesito un fichero de inventario
# con la lista de servidores", lo DECLARO como código ejecutable:
resource "local_file" "inventario" {
  filename = "${path.module}/inventario.txt"
  content  = <<-EOT
    servidor-web-01
    servidor-web-02
    servidor-bd-01
  EOT
}
```

Ese puñado de líneas es a la vez **la petición, la documentación y la ejecución**. Se revisa en un *pull request* (la solicitud de revisión de cambios que tu equipo aprueba antes de fusionar), se versiona en Git y se aplica igual en los tres entornos.

| Aspecto | Flujo tradicional | Infraestructura como código |
|---------|-------------------|------------------------------|
| Tiempo de entrega | Semanas/meses | Minutos |
| Reproducibilidad | Baja (pasos manuales) | Total (mismo código, mismo resultado) |
| Entornos | Divergen con el tiempo | Idénticos por construcción |
| Trazabilidad | Tickets dispersos | Historial de Git |
| Errores humanos | Frecuentes | Minimizados |

> ⚠️ **Errores comunes:**
> - Creer que **la nube por sí sola es IaC**: crear recursos a golpe de clic en la consola hereda casi todos los males del mundo tradicional.
> - Pensar que IaC es "scripts sueltos": un script de Bash que crea máquinas no sabe qué existe ya ni cómo actualizarlo; lo verás en 2.3.
> - **Documentar en wiki en vez de en código**: la wiki envejece; el código que se ejecuta, no.

> 💡 **Buenas prácticas:**
> - Toda modificación de infraestructura debería pasar por Git y revisión, igual que el código de aplicación.
> - Empieza describiendo en código lo pequeño (un fichero, un bucket) y crece desde ahí; no intentes migrar toda la empresa el primer día.
> - Trata la consola web como herramienta de *lectura*, no de escritura.

### 🧪 Laboratorio

**Enunciado:** simula la diferencia entre proceso manual y declarativo. Crea con Terraform el `inventario.txt` del ejemplo y demuestra que aplicar dos veces no duplica nada.

**Solución:**
1. En `modulo-02/lab1/`, crea `main.tf` con el bloque `terraform` de la lección 1.2 (solo el provider `local`) y el recurso `local_file.inventario` de arriba.
2. Ejecuta `terraform init` y luego `terraform apply` (confirma con `yes`):

```text
Plan: 1 to add, 0 to change, 0 to destroy.
...
Apply complete! Resources: 1 added, 0 changed, 0 destroyed.
```

3. Ejecuta `terraform apply` otra vez:

```text
No changes. Your infrastructure matches the configuration.
```

   Esto es **idempotencia**: el "ticket" se puede reejecutar mil veces sin efectos secundarios. Un procedimiento manual jamás te da esa garantía.
4. Limpia con `terraform destroy`.

> ❓ **Preguntas de repaso:**
> 1. **Cita tres problemas del aprovisionamiento tradicional.** Lentitud (semanas de espera), errores humanos por configuración manual e inconsistencia entre entornos (más coste y falta de trazabilidad).
> 2. **¿Migrar a la nube elimina la necesidad de IaC?** No: la nube acelera el aprovisionamiento, pero si se hace por consola sigue siendo manual, irrepetible y sin historial.

## 2.2 Tipos de herramientas IaC

**¿Qué vas a aprender?** No todas las herramientas de IaC hacen lo mismo. Aquí las clasificarás en tres familias —gestión de configuración, plantillas de servidor y aprovisionamiento— y sabrás cuándo encaja cada una, para colocar a Terraform en su casilla exacta.

Piensa en construir una casa: alguien **levanta la estructura** (cimientos, muros), alguien **amuebla** el interior, y existe la alternativa de comprarla **prefabricada**, ya montada de fábrica. Las herramientas IaC se reparten igual:

### Gestión de configuración — amueblar servidores existentes

**Ansible, Puppet y SaltStack** instalan y mantienen software *dentro* de máquinas que ya existen: paquetes, ficheros de configuración, servicios. Están pensadas para ejecutarse una y otra vez (son idempotentes) y para gestionar cientos de máquinas a la vez. Ansible funciona sin agente (por SSH); Puppet usa arquitectura con agente. No crean la máquina: la visten.

### Plantillas de servidor — la casa prefabricada

**Packer, Vagrant y Docker** trabajan con **imágenes inmutables**: horneas una imagen con todo el software ya dentro (una AMI con Packer, una imagen de contenedor con Docker, una caja de VM con Vagrant) y despliegas copias idénticas. Si hay que cambiar algo, no tocas el servidor: horneas una imagen nueva y reemplazas la antigua. Es el paradigma de **infraestructura inmutable**.

### Aprovisionamiento — levantar la estructura

**Terraform y AWS CloudFormation** crean la infraestructura en sí: redes, máquinas virtuales, bases de datos, balanceadores, DNS… CloudFormation solo funciona en AWS; Terraform habla con prácticamente cualquier plataforma. Aquí es donde vive este curso.

| Familia | Ejemplos | Actúa sobre | Pregunta que responde |
|---------|----------|-------------|------------------------|
| Gestión de configuración | Ansible, Puppet, SaltStack | El interior de servidores existentes | "¿Qué software lleva esta máquina?" |
| Plantillas de servidor | Packer, Vagrant, Docker | Imágenes inmutables | "¿Cómo horneo una copia idéntica?" |
| Aprovisionamiento | Terraform, CloudFormation | La infraestructura misma | "¿Qué recursos existen?" |

Las fronteras son porosas: Ansible puede crear máquinas y Terraform puede ejecutar scripts (módulo 9), pero cada herramienta brilla en su familia. En la práctica **se combinan**: Terraform crea la máquina y Ansible (o una imagen de Packer) la configura.

Así se ve el aprovisionamiento declarativo en miniatura, sin salir de tu portátil:

```hcl
# "Aprovisiono" dos elementos: un identificador único y un fichero que lo usa.
resource "random_pet" "entorno" {
  prefix = "dev" # el nombre resultante empezará por "dev"
  length = 2
}

resource "local_file" "config" {
  filename = "${path.module}/config.txt"
  # Referencio el atributo "id" del otro recurso: Terraform deduce el orden
  content  = "entorno: ${random_pet.entorno.id}"
}
```

> ⚠️ **Errores comunes:**
> - **Usar Terraform como si fuera Ansible**: gestionar el software interno de una máquina con provisioners de Terraform es frágil; cada herramienta a lo suyo.
> - **Memorizar la clasificación como dogma**: es un mapa orientativo, no una ley; muchas herramientas cruzan fronteras.
> - Confundir **Vagrant** (entornos de desarrollo locales) con **Packer** (imágenes para producción): ambos trabajan con imágenes, pero con fines distintos.

> 💡 **Buenas prácticas:**
> - Elige herramienta por familia de problema: crear infraestructura → aprovisionamiento; configurar el interior → gestión de configuración; empaquetar → plantillas.
> - Prefiere imágenes inmutables sobre servidores mutados a mano: menos deriva de configuración.
> - Cuando combines Terraform + Ansible, deja que Terraform sea la fuente de verdad de *qué existe*.

### 🧪 Laboratorio

**Enunciado:** clasifica estas herramientas en su familia: Puppet, Packer, CloudFormation, Docker, SaltStack, Terraform. Después, aplica el ejemplo `random_pet` + `local_file` y comprueba qué genera.

**Solución:**
1. Clasificación: gestión de configuración → Puppet, SaltStack; plantillas de servidor → Packer, Docker; aprovisionamiento → CloudFormation, Terraform.
2. En `modulo-02/lab2/`, crea `main.tf` con el bloque `terraform` (providers `local` y `random`) y los dos recursos del ejemplo.
3. `terraform init` y `terraform apply`. Salida esperada:

```text
Apply complete! Resources: 2 added, 0 changed, 0 destroyed.
```

4. Abre `config.txt`: verás algo como `entorno: dev-wiggly-yellowtail`. Terraform creó primero `random_pet` y después el fichero, porque detectó la dependencia automáticamente.
5. `terraform destroy` para limpiar.

> ❓ **Preguntas de repaso:**
> 1. **¿En qué familia está Terraform y qué hace esa familia?** Aprovisionamiento: crea (y destruye) los recursos de infraestructura en sí, no su contenido.
> 2. **¿Qué es infraestructura inmutable?** La que no se modifica en caliente: para cambiar algo se hornea una imagen nueva (Packer/Docker) y se reemplaza la antigua.
> 3. **¿Ansible y Terraform compiten?** Más bien se complementan: Terraform crea las máquinas; Ansible configura su interior.

## 2.3 ¿Por qué Terraform?

**¿Qué vas a aprender?** Dentro de la familia de aprovisionamiento, ¿por qué Terraform y no otra? Verás sus cinco cartas ganadoras: enfoque declarativo, soporte multiproveedor, gestión de estado con idempotencia, un lenguaje legible (HCL) y la capacidad de adoptar recursos ya existentes.

**1. Es declarativo.** Con Terraform no escribes *instrucciones*, sino *el estado deseado*. Es la diferencia entre dictarle a un taxista cada giro (imperativo) y darle la dirección de destino (declarativo): tú dices *dónde* quieres estar y Terraform calcula *cómo* llegar desde donde estés. Si ya estás en el destino, no hace nada.

**2. Es multiproveedor.** Terraform trabaja mediante **providers**: plugins que traducen tus bloques HCL a llamadas de API. En `registry.terraform.io` hay **miles de providers** públicos —AWS, Azure, Google Cloud, Kubernetes, GitHub, Cloudflare y también los humildes `local` y `random` que usamos aquí—. Aprendes una sintaxis y una herramienta, y gestionas cualquier plataforma. CloudFormation, en cambio, solo sabe hablar con AWS.

**3. Gestiona el estado.** Terraform guarda en un fichero de estado (*state*) una foto de lo que ha creado: su **fuente de verdad**. Gracias a él, el flujo de trabajo tiene tres fases:

- **Refresh**: consulta el mundo real y actualiza la foto (hoy ocurre automáticamente dentro de `plan` y `apply`).
- **Plan**: compara estado deseado (tu código) con estado real y calcula la diferencia exacta.
- **Apply**: ejecuta solo esa diferencia, en el orden correcto de dependencias.

De ahí nace la **idempotencia**: aplicar el mismo código dos veces produce cero cambios la segunda vez.

> 🔄 **Actualización:** en el curso original se enseñaba el comando `terraform refresh` como paso independiente. Está **obsoleto** desde Terraform 0.15.4: hoy el refresco es automático y, si quieres solo refrescar, se usa `terraform plan -refresh-only` o `terraform apply -refresh-only`.

**4. HCL es legible.** El HashiCorp Configuration Language se lee casi como prosa; compáralo con las plantillas JSON/YAML de CloudFormation. Míralo entero:

```hcl
terraform {
  required_version = ">= 1.5.0"
  required_providers {
    local  = { source = "hashicorp/local", version = "~> 2.0" }
    random = { source = "hashicorp/random", version = "~> 3.0" }
  }
}

resource "random_pet" "servidor" {
  length    = 3   # tres palabras...
  separator = "_" # ...separadas por guion bajo
}

resource "local_file" "ficha" {
  filename = "${path.module}/ficha.txt"
  content  = "Servidor asignado: ${random_pet.servidor.id}\n"
}

# Un output muestra valores útiles al terminar el apply
output "nombre_servidor" {
  value = random_pet.servidor.id
}
```

Y así razona `terraform plan` antes de tocar nada:

```text
Terraform will perform the following actions:

  # local_file.ficha will be created
  + resource "local_file" "ficha" {
      + content  = (known after apply)
      + filename = "./ficha.txt"
      ...
    }

  # random_pet.servidor will be created
  + resource "random_pet" "servidor" {
      + id        = (known after apply)
      + length    = 3
      + separator = "_"
    }

Plan: 2 to add, 0 to change, 0 to destroy.
```

**5. Puede adoptar lo que ya existe.** Con `terraform import` (y, desde Terraform 1.5, con bloques `import` declarativos que incluso **generan el código** con `terraform plan -generate-config-out`), puedes traer bajo control recursos creados a mano. No necesitas empezar de cero para adoptar IaC.

| Criterio | Terraform | CloudFormation | Ansible |
|----------|-----------|----------------|---------|
| Familia | Aprovisionamiento | Aprovisionamiento | Gestión de configuración |
| Plataformas | Miles de providers | Solo AWS | Multiplataforma |
| Lenguaje | HCL declarativo | JSON/YAML | YAML (playbooks, orientado a tareas) |
| Estado | Fichero de estado propio | Gestionado por AWS (stacks) | Sin estado central |
| Vista previa de cambios | `terraform plan` | Change sets | Modo `--check` (parcial) |

> ⚠️ **Errores comunes:**
> - **Editar recursos por consola** cuando ya los gestiona Terraform: creas *drift* (deriva) entre estado y realidad. Cambia siempre el código y aplica.
> - **Tratar el fichero de estado como algo desechable**: es la memoria de Terraform; sin él no sabe qué existe (lo estudiarás a fondo en el módulo 5).
> - **Ejecutar `apply` sin leer el `plan`**: el plan es tu red de seguridad; léelo siempre, sobre todo las líneas con `-` (destruir) y `-/+` (reemplazar).

> 💡 **Buenas prácticas:**
> - Haz de `plan` un hábito: en equipos reales el plan se revisa en el pull request antes de aplicar.
> - Verifica cada recurso y argumento en la documentación del provider en el Registry: es la referencia canónica.
> - Adopta la mentalidad multiproveedor desde el principio: lo que aprendas con `local_file` se aplica igual a un `aws_instance`.

### 🧪 Laboratorio

**Enunciado:** demuestra las tres fases y la idempotencia. Aplica la configuración del ejemplo, vuelve a aplicar sin cambios, y después cambia el estado deseado (`length = 2`) para observar cómo Terraform calcula un reemplazo.

**Solución:**
1. En `modulo-02/lab3/`, guarda el ejemplo completo en `main.tf`; ejecuta `terraform init` y `terraform apply`. Anota el output `nombre_servidor` (p. ej. `primly_lasting_toucan`: con `length = 3`, el nombre es adverbio + adjetivo + animal).
2. Ejecuta `terraform apply` de nuevo. Resultado: `No changes. Your infrastructure matches the configuration.` — idempotencia demostrada.
3. Edita `main.tf` y cambia `length = 3` por `length = 2`. Ejecuta `terraform plan`:

```text
  # random_pet.servidor must be replaced
-/+ resource "random_pet" "servidor" {
      ~ id     = "primly_lasting_toucan" -> (known after apply)
      ~ length = 3 -> 2 # forces replacement
    }

  # local_file.ficha must be replaced
-/+ resource "local_file" "ficha" {
      ~ content  = "Servidor asignado: primly_lasting_toucan\n" -> (known after apply) # forces replacement
      ...
    }

Plan: 2 to add, 0 to change, 2 to destroy.
```

   Fíjate: no le has dicho *qué hacer*; has cambiado el *destino* y Terraform ha deducido que debe reemplazar el nombre **y también** el fichero que dependía de él.
4. Aplica, verifica el nuevo contenido de `ficha.txt` y termina con `terraform destroy`.

> ❓ **Preguntas de repaso:**
> 1. **¿Qué significa que Terraform sea declarativo?** Que describes el estado final deseado y la herramienta calcula y ejecuta los pasos para alcanzarlo desde el estado actual.
> 2. **¿Para qué sirve el fichero de estado?** Es la fuente de verdad de lo que Terraform gestiona: permite comparar deseado vs. real en `plan` y aplicar solo la diferencia.
> 3. **¿Qué ventaja clave tiene Terraform frente a CloudFormation?** CloudFormation solo gestiona AWS; Terraform, mediante miles de providers del Registry, gestiona prácticamente cualquier plataforma con un único lenguaje y flujo de trabajo.
