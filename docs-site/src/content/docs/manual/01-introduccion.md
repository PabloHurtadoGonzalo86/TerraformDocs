---
title: "Módulo 1 · Introducción al curso"
description: "Presentación del manual, mapa completo del curso y recursos para seguir el aprendizaje."
---

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
