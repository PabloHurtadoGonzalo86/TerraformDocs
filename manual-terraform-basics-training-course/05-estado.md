# Módulo 5 · El estado de Terraform

Hasta ahora has escrito configuraciones, has ejecutado `terraform apply` y has visto aparecer recursos como por arte de magia. En este módulo desmontamos el truco: toda esa magia depende de un fichero llamado `terraform.tfstate`. Entender qué es, para qué sirve y cómo tratarlo con respeto es lo que separa a quien "usa" Terraform de quien lo domina.

## 5.1 Introducción al estado de Terraform

**¿Qué vas a aprender?** En esta lección descubrirás qué es el fichero de estado de Terraform, cuándo se crea y qué contiene exactamente. Verás que es un documento JSON que actúa como el vínculo entre tu configuración y los objetos reales que existen en el mundo, y comprobarás con un ejemplo local cómo cambia el comportamiento de `plan` y `apply` según exista o no ese fichero.

### Qué es terraform.tfstate y cuándo aparece

Cuando ejecutas `terraform apply` por primera vez en un proyecto, Terraform crea los recursos y, justo después, escribe un fichero llamado **`terraform.tfstate`** en el directorio de trabajo (con el *backend* local —el mecanismo que decide dónde se guarda el estado—, que es el que usamos de momento). Ese fichero **no existe hasta el primer `apply`**: ni `init` ni `plan` lo crean.

Piensa en un guardamuebles. Tu configuración (`.tf`) es la lista de lo que quieres almacenar: "dos cajas de libros y una bicicleta". El almacén es el mundo real. Y el estado es **el cuaderno del encargado**: apunta que la caja 1 está en el trastero B-12 y la bici en el pasillo 3. Sin ese cuaderno, la lista y el almacén no se pueden relacionar: el encargado no sabría si tus cajas ya están dentro ni dónde. Terraform funciona igual: el estado guarda la correspondencia entre cada bloque `resource` y el objeto real que le corresponde.

Técnicamente, `terraform.tfstate` es un documento **JSON** que contiene, entre otras cosas:

| Campo | Qué guarda |
|---|---|
| `version` | Versión del formato interno del estado (actualmente 4) |
| `terraform_version` | Versión de Terraform que escribió el fichero |
| `serial` | Contador que se incrementa con cada cambio del estado |
| `lineage` | Identificador único que se asigna al crear el estado |
| `outputs` | Los valores de salida del módulo raíz |
| `resources` | La lista de recursos gestionados, con **todos sus atributos** |

### Verlo en acción con providers locales

Crea un directorio nuevo con este `main.tf` (solo necesitas los providers `local` y `random`, sin cuenta en ningún proveedor de nube):

```hcl
# main.tf — nuestro primer vistazo al estado

terraform {
  required_providers {
    local = {
      source  = "hashicorp/local"
      version = "~> 2.5"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}

# Genera un nombre aleatorio de dos palabras (p. ej. "casual-mongoose")
resource "random_pet" "mascota" {
  length = 2
}

# Crea un fichero local cuyo contenido usa el nombre generado
resource "local_file" "saludo" {
  filename = "${path.module}/saludo.txt"
  content  = "Mi mascota se llama ${random_pet.mascota.id}\n"
}
```

Ejecuta `terraform init` y luego `terraform plan`. Como **no hay estado**, Terraform asume que nada existe y propone crearlo todo:

```text
Terraform will perform the following actions:

  # local_file.saludo will be created
  ...
  # random_pet.mascota will be created
  ...

Plan: 2 to add, 0 to change, 0 to destroy.
```

Tras `terraform apply -auto-approve`, aparece `terraform.tfstate`. Si lo abres (¡solo para mirar!), verás algo así:

```json
{
  "version": 4,
  "terraform_version": "1.12.2",
  "serial": 1,
  "lineage": "9c1f2a77-....",
  "outputs": {},
  "resources": [
    {
      "mode": "managed",
      "type": "random_pet",
      "name": "mascota",
      "provider": "provider[\"registry.terraform.io/hashicorp/random\"]",
      "instances": [
        {
          "attributes": {
            "id": "casual-mongoose",
            "length": 2,
            "separator": "-"
          }
        }
      ]
    }
  ]
}
```

Ahí está la correspondencia (el *mapping*, como lo llama la documentación oficial): el bloque `random_pet.mascota` de tu código queda ligado al objeto real cuyo `id` es `casual-mongoose`. Si ahora repites `terraform plan`, Terraform consulta el estado, lo contrasta con la realidad y con tu configuración, y concluye:

```text
No changes. Your infrastructure matches the configuration.
```

Ese es el ciclo completo: **sin estado**, todo es "crear"; **con estado**, Terraform puede calcular diferencias (crear, cambiar, destruir o no tocar nada). Para inspeccionarlo sin abrir el JSON, usa `terraform show` (versión legible del estado) o `terraform state list` (lista de direcciones de recursos).

> ⚠️ **Errores comunes:**
> - Borrar `terraform.tfstate` "para empezar de cero". Terraform pierde el vínculo con los recursos ya creados y el siguiente `apply` los duplicará (o fallará por conflictos de nombres).
> - Confundir el estado con la configuración: los `.tf` describen lo que **quieres**; el `.tfstate` registra lo que Terraform **ya gestiona**.
> - Esperar que `terraform plan` cree el fichero de estado: no lo hace; solo `apply` (y los comandos que modifican estado) lo escriben.
> - Ignorar `terraform.tfstate.backup`: es la copia del estado anterior que Terraform guarda automáticamente; puede salvarte de un desastre.

> 💡 **Buenas prácticas:**
> - Trata el estado como una base de datos interna de Terraform: se consulta con comandos (`terraform show`, `terraform state list`), no editándolo.
> - Antes de experimentar, haz una copia de seguridad manual del `.tfstate` en proyectos de prueba: es la forma más barata de aprender sin sustos.
> - Acostúmbrate a leer el `Plan: X to add, Y to change, Z to destroy` y a preguntarte qué dice eso sobre lo que hay en el estado.

### 🧪 Laboratorio

**Enunciado:** parte del `main.tf` anterior. (1) Comprueba que antes del primer `apply` no existe estado. (2) Aplica y lista los recursos del estado. (3) Borra a mano el fichero `saludo.txt` y demuestra que Terraform detecta la desviación y propone recrearlo.

**Solución:**

```text
$ terraform init
$ ls terraform.tfstate        # error: el fichero aún no existe
$ terraform apply -auto-approve
Apply complete! Resources: 2 added, 0 changed, 0 destroyed.

$ terraform state list
local_file.saludo
random_pet.mascota

$ rm saludo.txt               # simulamos un cambio fuera de Terraform
$ terraform plan
  # local_file.saludo will be created
Plan: 1 to add, 0 to change, 0 to destroy.
```

Al refrescar, Terraform ve que el objeto registrado en el estado ya no existe en el mundo real y planifica recrearlo. Ejecuta `terraform apply` para dejarlo todo en orden.

> ❓ **Preguntas de repaso:**
> 1. **¿En qué formato se guarda el estado y cómo se llama el fichero por defecto?** En JSON, en `terraform.tfstate` (con el backend local, en el directorio de trabajo).
> 2. **¿Qué hace `terraform plan` si no existe fichero de estado?** Asume que ningún recurso existe todavía y propone crear todo lo declarado en la configuración.
> 3. **¿Qué campo del estado se incrementa con cada modificación?** El campo `serial`, que actúa como contador de versiones del estado.

## 5.2 El propósito del estado

**¿Qué vas a aprender?** Aquí responderás a la pregunta "¿de verdad hace falta el estado?". Verás las tres razones de fondo: guardar **metadatos** (como las dependencias entre recursos, imprescindibles para destruir en orden), mejorar el **rendimiento** actuando como caché de atributos, y hacer posible la **colaboración en equipo** compartiendo una única fuente de verdad.

### Metadatos: el orden importa

Terraform no solo apunta "qué existe", sino también **cómo se relacionan los recursos entre sí**. En nuestro ejemplo, `local_file.saludo` referencia a `random_pet.mascota`, así que Terraform sabe que debe crear primero la mascota y después el fichero. Recuerda dónde nace esa relación en el código:

```hcl
# La dependencia nace aquí: "saludo" referencia a "mascota"
resource "local_file" "saludo" {
  filename = "${path.module}/saludo.txt"
  content  = "Mi mascota se llama ${random_pet.mascota.id}\n" # <- dependencia implícita
}
```

Esa dependencia queda grabada en el estado, dentro de la instancia del recurso:

```json
"instances": [
  {
    "attributes": { "...": "..." },
    "dependencies": [
      "random_pet.mascota"
    ]
  }
]
```

¿Por qué guardarla, si ya está implícita en el código? Piensa en qué pasa cuando **eliminas ambos bloques** del `.tf`: la configuración ya no dice nada sobre ellos, pero Terraform aún tiene que destruirlos **en orden inverso** (primero el fichero, luego la mascota). Como la información ya no está en el código, la única fuente posible es la copia de dependencias que conserva el estado. Es como desmontar un mueble sin las instrucciones: si alguien apuntó en qué orden se montó, sabrás en qué orden desatornillar.

Puedes comprobarlo: comenta los dos recursos y ejecuta `terraform apply`:

```text
local_file.saludo: Destroying... [id=e5f1c...]
local_file.saludo: Destruction complete after 0s
random_pet.mascota: Destroying... [id=casual-mongoose]
random_pet.mascota: Destruction complete after 0s

Apply complete! Resources: 0 added, 0 changed, 2 destroyed.
```

Primero el dependiente, después la dependencia. Sin estado, ese orden sería imposible de calcular.

### Rendimiento: el estado como caché

Antes de cada `plan` o `apply`, Terraform hace un **refresh**: pregunta al provider por el estado real de cada recurso para detectar cambios hechos fuera de Terraform. Con dos recursos locales es instantáneo, pero imagina miles de recursos en la nube: cada consulta es una llamada a la API con su latencia y sus límites de peticiones. En infraestructuras grandes, ese refresco puede tardar muchos minutos.

Para esos casos, Terraform permite usar el estado como **caché de los valores de atributos** y saltarse la sincronización con la opción `-refresh=false`, disponible tanto en `plan` como en `apply`:

```text
$ terraform plan -refresh=false

No changes. Your infrastructure matches the configuration.
```

Terraform confía en lo que dice el estado sin verificarlo contra el mundo real. El plan sale mucho más rápido, a cambio de un riesgo: si alguien cambió algo por fuera, Terraform no lo verá y el plan puede ser **incompleto o incorrecto**. Los equipos con infraestructuras enormes combinan esta opción con `-target=DIRECCIÓN` (planificar solo recursos concretos) para trabajar de forma ágil, asumiendo ese compromiso conscientemente.

> 🔄 **Actualización:** en las versiones antiguas que usaba el curso existía el comando independiente `terraform refresh`. Hoy está **desaconsejado**: desde Terraform v0.15.4 la forma recomendada de sincronizar el estado con la realidad (sin tocar la infraestructura) es `terraform apply -refresh-only`, que además te muestra qué va a cambiar en el estado y te pide confirmación.

### Colaboración: una única fuente de verdad

El tercer propósito es el trabajo en equipo. Si tú tienes un `terraform.tfstate` en tu portátil y tu compañera tiene otro en el suyo, tenéis **dos versiones de la verdad**, y cada `apply` de uno invalida el mapa mental del otro: recursos duplicados, destrucciones accidentales, caos. El estado debe vivir en un **lugar compartido y único** —un *backend* remoto, como verás en el módulo de estado remoto— donde todo el mundo lea y escriba la misma copia. Los backends remotos añaden además **bloqueo (locking)**: mientras alguien ejecuta un `apply`, nadie más puede escribir el estado a la vez, evitando corrupciones.

> ⚠️ **Errores comunes:**
> - Abusar de `-refresh=false` "porque va más rápido" en proyectos pequeños: te acostumbras a planes que ignoran la realidad y acabas aplicando cambios sobre información obsoleta.
> - Creer que borrar un recurso del `.tf` lo "olvida": al contrario, Terraform lo **destruirá** en el siguiente `apply` porque sigue en el estado.
> - Compartir el estado por correo o copiándolo entre portátiles: sin bloqueo ni versión única, es cuestión de tiempo que dos `apply` simultáneos lo corrompan.

> 💡 **Buenas prácticas:**
> - Deja que el refresh ocurra por defecto; reserva `-refresh=false` para infraestructuras realmente grandes y úsalo sabiendo qué sacrificas.
> - Usa `terraform apply -refresh-only` periódicamente para detectar *drift* (cambios hechos fuera de Terraform) sin modificar nada.
> - En cuanto haya más de una persona en el proyecto, mueve el estado a un backend remoto con bloqueo.

### 🧪 Laboratorio

**Enunciado:** con el proyecto de 5.1 aplicado, (1) localiza la lista `dependencies` en el estado, (2) modifica `saludo.txt` a mano y compara `terraform plan` con `terraform plan -refresh=false`, y (3) explica la diferencia.

**Solución:**

```text
# 1. Vuelca el estado y busca las dependencias
$ terraform state pull | findstr /C:"dependencies"   # en Linux/macOS: | grep -A2 dependencies
        "dependencies": [

# 2. Cambia el fichero por fuera de Terraform
$ echo contenido manipulado > saludo.txt

$ terraform plan
Note: Objects have changed outside of Terraform
  # local_file.saludo has been deleted
  ...
  # local_file.saludo will be created
Plan: 1 to add, 0 to change, 0 to destroy.

$ terraform plan -refresh=false
No changes. Your infrastructure matches the configuration.
```

Con el *refresh* activado, Terraform detecta que el contenido real ya no coincide con lo registrado (el provider `local` comprueba el contenido del fichero y, al no encontrar coincidencia, informa a Terraform de que el objeto ya no existe tal como estaba definido) y propone recrearlo. Con `-refresh=false` se fía de la caché del estado y no ve nada raro: exactamente el riesgo (y la ganancia de velocidad) del que hemos hablado. Termina con `terraform apply` para reparar el fichero.

> ❓ **Preguntas de repaso:**
> 1. **¿Por qué Terraform guarda las dependencias en el estado si ya están en el código?** Porque cuando eliminas recursos de la configuración, el código ya no contiene esa información y Terraform la necesita para destruirlos en el orden inverso correcto.
> 2. **¿Qué gana y qué arriesga `terraform plan -refresh=false`?** Gana velocidad al evitar llamadas a la API del provider; arriesga planificar sobre datos obsoletos e ignorar cambios hechos fuera de Terraform.
> 3. **¿Por qué el estado debe ser compartido en un equipo?** Para que todos trabajen sobre una única fuente de verdad y, con un backend remoto con bloqueo, evitar ejecuciones simultáneas que corrompan el estado.

## 5.3 Consideraciones al trabajar con el estado

**¿Qué vas a aprender?** Cerramos el módulo con las reglas de seguridad e higiene del estado: por qué contiene secretos en texto plano, por qué jamás debe subirse a Git ni editarse a mano, y dónde debería vivir en un proyecto serio.

### El estado guarda secretos en texto plano

El estado almacena **todos los atributos** de tus recursos, y eso incluye datos sensibles: contraseñas iniciales de bases de datos, tokens, claves... en **texto plano**, sin cifrar. Compruébalo tú mismo:

```hcl
# secreto.tf — demuestra que el estado guarda secretos legibles

resource "random_password" "db" {
  length  = 16   # longitud de la contraseña generada
  special = true # incluye caracteres especiales
}
```

Al aplicar, Terraform trata el resultado como sensible **en pantalla**: el plan y `terraform state show random_password.db` lo enmascaran como `(sensitive value)`. Pero el fichero crudo no perdona:

```text
$ terraform state pull | findstr result     # grep result en Linux/macOS
        "result": "k8!vQ2#mZp9$wX4c",
```

Ahí está la contraseña, legible para cualquiera que pueda abrir el fichero. El estado es como el **libro de contabilidad de una empresa**: apunta todo con pelos y señales, y precisamente por eso no se deja encima de la mesa de recepción; se guarda bajo llave y solo lo consulta quien debe.

De esta realidad se derivan tres reglas:

1. **Nunca subas el estado a Git.** Un repositorio (aunque sea privado) multiplica las copias del secreto, lo expone en el historial para siempre y carece de bloqueo. Añade esto a tu `.gitignore` desde el primer día:

```text
# .gitignore — nunca versionar el estado ni el directorio de trabajo
*.tfstate
*.tfstate.*
.terraform/
crash.log
```

2. **Nunca edites el estado a mano.** Un JSON mal cerrado, un `serial` incoherente o un atributo cambiado sin criterio pueden dejar el proyecto inutilizable. Para manipularlo existen los subcomandos `terraform state`: `list` (listar recursos), `show` (ver uno), `mv` (renombrar/mover), `rm` (dejar de gestionar un recurso sin destruirlo) y `pull`/`push` (leer/escribir el estado completo). Además, **todo subcomando que modifica el estado escribe una copia de seguridad automáticamente y eso no se puede desactivar**: Terraform te protege incluso de ti mismo.

3. **Guárdalo en un backend remoto seguro.** En equipo, el estado debe vivir en un almacenamiento remoto con cifrado en reposo, TLS en tránsito, control de acceso y bloqueo: HCP Terraform, un bucket S3 con la opción `encrypt` activada, Azure Storage, Google Cloud Storage… Lo configurarás en detalle en el módulo de estado remoto.

> 🔄 **Actualización:** desde Terraform 1.10 existen los **recursos efímeros** (`ephemeral`), pensados justo para este problema: valores como contraseñas que se usan durante la ejecución pero **no se guardan ni en el plan ni en el estado**. El provider `random` ya ofrece una variante efímera de `random_password`. En el curso original esto no existía; tenlo en el radar para gestionar secretos en proyectos modernos.

> ⚠️ **Errores comunes:**
> - Hacer `git add .` sin `.gitignore` y publicar el `.tfstate` con secretos dentro. Si ocurre, no basta con borrarlo: hay que purgar el historial y **rotar los secretos expuestos**.
> - Editar el JSON a mano para "arreglar" un recurso: casi siempre acaba peor. Usa `terraform state mv/rm` o, para adoptar recursos existentes, `terraform import`.
> - Confundir `terraform state rm` con destruir: solo saca el recurso de la gestión de Terraform; el objeto real sigue existiendo.
> - Pensar que marcar un valor como `sensitive` lo cifra: solo lo oculta en la salida por pantalla, no en el fichero de estado.

> 💡 **Buenas prácticas:**
> - Crea el `.gitignore` de Terraform **antes** del primer commit del proyecto, no después.
> - Trata el acceso al estado como acceso a secretos: mínimo privilegio, cifrado en reposo y, si el backend lo permite, registros de auditoría.
> - Cuando necesites cirugía sobre el estado, trabaja siempre sobre una copia (`terraform state pull > respaldo.tfstate`) y usa los subcomandos oficiales.

### 🧪 Laboratorio

**Enunciado:** (1) añade `random_password.db` al proyecto y aplica; (2) demuestra que `terraform state show` enmascara el secreto pero el estado crudo no; (3) protege el proyecto con un `.gitignore`; (4) saca el recurso de la gestión de Terraform sin destruir nada.

**Solución:**

```text
$ terraform apply -auto-approve
random_password.db: Creation complete after 0s

$ terraform state show random_password.db
# random_password.db:
resource "random_password" "db" {
    length  = 16
    result  = (sensitive value)
    ...
}

$ terraform state pull | findstr result
        "result": "k8!vQ2#mZp9$wX4c",     # ¡texto plano!

$ echo *.tfstate >> .gitignore            # completa con el resto de líneas vistas arriba

$ terraform state rm random_password.db
Removed random_password.db
Successfully removed 1 resource instance(s).
```

Fíjate en que tras el `rm` aparece un fichero de respaldo del estado en el directorio: es la copia automática que Terraform escribe siempre que modificas el estado. Si ahora ejecutas `terraform plan`, propondrá crear una contraseña nueva, porque el recurso sigue en tu código pero ya no está en el estado (elimínalo del `.tf` para dejar el proyecto limpio).

> ❓ **Preguntas de repaso:**
> 1. **¿Los valores marcados como sensibles están cifrados dentro de `terraform.tfstate`?** No. Se ocultan en la salida por pantalla, pero en el fichero JSON figuran en texto plano; por eso el estado entero debe tratarse como información sensible.
> 2. **¿Cuál es la forma correcta de renombrar un recurso en el estado?** Con `terraform state mv ORIGEN DESTINO`, nunca editando el JSON a mano; además, el comando genera automáticamente una copia de seguridad imposible de desactivar.
> 3. **¿Dónde debería almacenarse el estado en un proyecto de equipo y por qué?** En un backend remoto seguro (HCP Terraform, S3 con cifrado, etc.): ofrece una única fuente de verdad, cifrado en reposo, control de acceso y bloqueo frente a ejecuciones simultáneas.
