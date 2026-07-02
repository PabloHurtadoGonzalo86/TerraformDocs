# Módulo 7 · Terraform con AWS

Hasta ahora has practicado con los providers `local` y `random`, sin necesidad de cuenta cloud. En este módulo damos el salto a la nube de verdad: crearás una cuenta de AWS, entenderás su sistema de identidades (IAM) y gestionarás usuarios y políticas **con Terraform**. Es la base de todo lo que harás en AWS: si las credenciales y los permisos no están bien montados, nada de lo demás funcionará.

## 7.1 Primeros pasos con AWS

**¿Qué vas a aprender?** En esta lección vas a entender qué es AWS, cómo se organiza geográficamente en regiones y zonas de disponibilidad, y por qué es el proveedor que usaremos en los módulos 7 a 9. También verás qué papel juega Terraform en todo esto y cómo se declara el provider de AWS.

### Qué es AWS y por qué nos importa

Amazon Web Services (AWS) es el mayor proveedor de infraestructura en la nube del mundo. Ofrece cientos de servicios: máquinas virtuales (EC2), almacenamiento de objetos (S3), bases de datos gestionadas (RDS, DynamoDB), funciones sin servidor (Lambda)... y todos se pueden crear y destruir mediante una API. Eso último es la clave para nosotros: **si hay API, hay provider de Terraform**.

La mejor analogía es la de la compañía eléctrica. Antes de la red eléctrica, cada fábrica tenía su propio generador: caro, difícil de mantener y desaprovechado la mayor parte del tiempo. Con la red, enchufas, consumes y pagas solo por lo que usas. AWS hace lo mismo con los servidores: en vez de comprar hardware, alquilas capacidad de cómputo por horas (o segundos) y la devuelves cuando terminas. Terraform es, siguiendo la analogía, el cuadro eléctrico documentado de tu casa: un plano declarativo de qué está enchufado, dónde y por qué.

### Regiones y zonas de disponibilidad

AWS despliega su infraestructura en **regiones**: agrupaciones de centros de datos en una zona geográfica (por ejemplo, `eu-west-1` en Irlanda o `eu-south-2` en España). Cada región contiene varias **zonas de disponibilidad** (AZ): centros de datos aislados entre sí pero conectados con redes de baja latencia, para que un incendio o un corte eléctrico en uno no tumbe tu aplicación.

Cuando trabajes con Terraform siempre le dirás al provider **en qué región** operar. Elegir región importa por tres motivos: latencia (cuanto más cerca de tus usuarios, mejor), precio (no todas las regiones cuestan lo mismo) y requisitos legales (hay datos que deben quedarse en la UE).

Así se declara el provider que usaremos durante todo el módulo:

```hcl
# versions.tf — fija el provider de AWS para todo el proyecto
terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws" # provider oficial de HashiCorp/AWS
      version = "~> 6.0"        # serie 6.x, la actual
    }
  }
}

# main.tf — configuración del provider
provider "aws" {
  region = "eu-west-1" # Irlanda; todas las llamadas a la API irán a esta región
}
```

Fíjate en que **no** hemos escrito credenciales en el bloque `provider`. Es deliberado: las veremos en 7.5, y nunca deben ir en el código.

> ⚠️ **Errores comunes:**
> - Pensar que AWS es «un sitio»: cada región es casi un mundo aparte. Si creas un recurso en `eu-west-1` y luego lo buscas en la consola con `us-east-1` seleccionada, no lo verás y creerás que ha desaparecido.
> - No fijar la versión del provider con `required_providers`: una actualización mayor (de 5.x a 6.x, por ejemplo) puede cambiar comportamientos y romper tu configuración.
> - Confundir región con zona de disponibilidad: la región es el conjunto (`eu-west-1`); la AZ es cada centro de datos (`eu-west-1a`).

> 💡 **Buenas prácticas:**
> - Elige una región y sé consistente durante el curso; mezclar regiones sin querer es fuente clásica de confusión.
> - Declara siempre `required_providers` con una restricción `~>` para controlar las actualizaciones.
> - Antes de usar un servicio, comprueba en la documentación de AWS que está disponible en tu región: no todos los servicios existen en todas.

### 🧪 Laboratorio

**Ejercicio:** todavía sin cuenta de AWS, prepara el esqueleto del proyecto. Crea un directorio `aws-basics` con `versions.tf` y `main.tf` como los de arriba, ejecuta `terraform init` y verifica que descarga el provider `hashicorp/aws`.

**Solución:** crea los dos ficheros con el contenido mostrado y ejecuta:

```text
$ terraform init

Initializing provider plugins...
- Finding hashicorp/aws versions matching "~> 6.0"...
- Installing hashicorp/aws v6.53.0...
- Installed hashicorp/aws v6.53.0 (signed by HashiCorp)

Terraform has been successfully initialized!
```

`init` funciona sin credenciales porque solo descarga el plugin; para `plan` y `apply` ya necesitarás una cuenta (siguiente lección).

> ❓ **Preguntas de repaso:**
> 1. **¿Qué diferencia hay entre una región y una zona de disponibilidad?** Una región es una zona geográfica con varios centros de datos; cada zona de disponibilidad es uno de esos centros de datos aislados dentro de la región.
> 2. **¿Por qué Terraform puede gestionar AWS?** Porque AWS expone toda su funcionalidad mediante APIs, y el provider `hashicorp/aws` traduce tus bloques HCL en llamadas a esas APIs.
> 3. **¿Dónde se indica la región con la que trabajará el provider?** En el argumento `region` del bloque `provider "aws"` (o mediante variables de entorno como `AWS_REGION`, como verás en 7.5).

## 7.2 Crear y preparar una cuenta de AWS

**¿Qué vas a aprender?** Aquí vas a crear tu cuenta de AWS paso a paso, entenderás qué es el usuario root y por qué debes guardarlo bajo llave, y conocerás la capa gratuita actual para practicar sin sustos en la factura.

### Crear la cuenta

Crear una cuenta en [aws.amazon.com](https://aws.amazon.com) es como abrir una cuenta bancaria online: necesitas un correo electrónico (que será el identificador del **usuario root**), una contraseña, datos de contacto, una tarjeta de crédito/débito para verificación y un teléfono para el código de confirmación. El proceso resumido:

1. Entra en la página de registro de AWS y elige un correo y un nombre de cuenta.
2. Verifica el correo con el código que te envían y crea la contraseña del root.
3. Introduce datos de contacto y de facturación (la tarjeta puede recibir un cargo temporal de verificación).
4. Verifica tu identidad por SMS o llamada.
5. Elige el plan de soporte gratuito (Basic).

> 🔄 **Actualización:** cuando se grabó el curso, la capa gratuita era la «clásica»: 12 meses de ciertos servicios (750 h/mes de EC2 `t2.micro`, etc.) más servicios «siempre gratis». Desde el **15 de julio de 2025** AWS cambió el modelo para cuentas nuevas: al registrarte eliges entre **plan gratuito** o plan de pago. El plan gratuito te da **100 $ en créditos** al crear la cuenta (ampliables hasta 200 $ completando actividades guiadas) y garantiza que no se te cobrará nada; caduca a los **6 meses** o al agotar los créditos, lo que ocurra antes. Las cuentas anteriores a esa fecha siguen en el programa antiguo. Verifícalo en la documentación de facturación de AWS, porque las condiciones pueden evolucionar.

### El usuario root: el dueño del edificio

Al crear la cuenta naces con una única identidad: el **usuario root**, que tiene acceso total y sin restricciones a todo. Piensa en él como la escritura de propiedad de un edificio: te acredita como dueño y te permite hasta demolerlo, pero no vas a ir a trabajar cada día con la escritura en el bolsillo. Para el día a día usarás identidades con permisos limitados (lección 7.3). AWS recomienda explícitamente **no usar el root para tareas cotidianas**: resérvalo para lo que solo él puede hacer (cambiar el plan de soporte, cerrar la cuenta, ciertas operaciones de facturación).

Nada más crear la cuenta, haz dos cosas con el root: **activa MFA** (autenticación multifactor, con una app de códigos temporales de un solo uso —TOTP— o una llave física) y **no generes claves de acceso programático para él**.

### Verificar la cuenta desde Terraform

Un primer contacto útil (cuando tengas credenciales configuradas, lección 7.5) es preguntarle a AWS «¿quién soy?» con un *data source*:

```hcl
# whoami.tf — data source de solo lectura: no crea nada
data "aws_caller_identity" "actual" {}

output "id_de_cuenta" {
  value = data.aws_caller_identity.actual.account_id # nº de cuenta de 12 dígitos
}

output "identidad" {
  value = data.aws_caller_identity.actual.arn # ARN de la identidad que llama
}
```

```text
$ terraform apply -auto-approve

Outputs:

id_de_cuenta = "123456789012"
identidad    = "arn:aws:iam::123456789012:user/pablo"
```

> ⚠️ **Errores comunes:**
> - Usar el root a diario «porque total, es mi cuenta»: si esas credenciales se filtran, el atacante lo controla absolutamente todo, incluida la facturación.
> - No activar MFA en el root: es la cerradura principal de tu cuenta; sin MFA, tu seguridad depende de una sola contraseña.
> - Olvidarte de la cuenta con recursos corriendo: una instancia olvidada fuera de la capa gratuita genera factura cada hora. Configura alertas de presupuesto en AWS Budgets desde el primer día.

> 💡 **Buenas prácticas:**
> - Activa MFA en el root inmediatamente y guarda la contraseña en un gestor de contraseñas.
> - Crea una alerta de presupuesto (por ejemplo, 5 €) para enterarte de cualquier gasto inesperado.
> - Al terminar cada sesión de práctica, ejecuta `terraform destroy` y revisa la consola para confirmar que no queda nada vivo.

### 🧪 Laboratorio

**Ejercicio:** crea tu cuenta de AWS, protege el root con MFA y localiza tu ID de cuenta.

**Solución paso a paso:** 1) Completa el registro descrito arriba eligiendo el plan gratuito. 2) Inicia sesión como root, ve a **Credenciales de seguridad** (menú de tu nombre, arriba a la derecha) y en **Multi-factor authentication (MFA)** registra tu app de autenticación escaneando el QR e introduciendo dos códigos consecutivos. 3) En ese mismo menú verás el **ID de cuenta** de 12 dígitos: apúntalo, lo usarás en los ARN de todo el módulo. 4) Extra: entra en **AWS Budgets** y crea un presupuesto de coste cero para recibir avisos por correo.

> ❓ **Preguntas de repaso:**
> 1. **¿Qué es el usuario root y para qué debe usarse?** Es la identidad creada con la cuenta, con acceso total; debe usarse solo para tareas que lo requieran expresamente, nunca para el trabajo diario.
> 2. **¿Qué ofrece el plan gratuito actual para cuentas nuevas?** 100 $ de créditos al registrarte (hasta 200 $ con actividades), sin cargos, durante un máximo de 6 meses o hasta agotar los créditos.
> 3. **¿Cuál es la primera medida de seguridad tras crear la cuenta?** Activar MFA en el usuario root y no crear claves de acceso para él.

## 7.3 Introducción a IAM

**¿Qué vas a aprender?** IAM (Identity and Access Management) es el servicio de AWS que decide **quién** puede hacer **qué** sobre **qué recursos**. Vas a conocer sus cuatro piezas —usuarios, grupos, roles y políticas—, la anatomía de una política JSON y el principio de mínimo privilegio.

### El edificio de oficinas

Imagina tu cuenta de AWS como un edificio de oficinas. El **usuario root** es el dueño con la llave maestra. Los **usuarios IAM** son los empleados, cada uno con su tarjeta identificativa (nombre + credenciales). Los **grupos** son los departamentos: en vez de dar permisos tarjeta a tarjeta, dices «todo el departamento de desarrollo puede entrar a la planta 3». Las **políticas** son las normas escritas que dicen qué puertas abre cada tarjeta. Y los **roles** son chalecos de visitante: no pertenecen a nadie, pero quien se lo pone (una persona, una aplicación o un servicio de AWS) adquiere temporalmente los permisos del chaleco.

IAM resuelve dos preguntas distintas: **autenticación** («¿eres quien dices ser?», mediante contraseña o claves) y **autorización** («¿tienes permiso para esto?», mediante políticas). Y una buena noticia: IAM es gratuito; solo pagas por los recursos que esas identidades consuman.

### Anatomía de una política

Una política IAM es un documento JSON con una estructura fija:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PermitirLecturaEC2",
      "Effect": "Allow",
      "Action": ["ec2:Describe*"],
      "Resource": "*"
    }
  ]
}
```

- **Version**: la versión del lenguaje de políticas. Usa siempre `"2012-10-17"`, la vigente (no es una fecha tuya, es la del lenguaje).
- **Statement**: lista de declaraciones; cada una es una regla.
- **Sid**: identificador opcional y descriptivo de la declaración.
- **Effect**: `Allow` o `Deny`. Por defecto todo está denegado (*deny* implícito), y un `Deny` explícito gana siempre a cualquier `Allow`.
- **Action**: qué operaciones de la API permite o deniega, con formato `servicio:Operación` y comodines (`ec2:Describe*`, `s3:*`).
- **Resource**: sobre qué recursos aplica, identificados por su **ARN** (Amazon Resource Name), como `arn:aws:iam::123456789012:user/pablo`. `"*"` significa «todos».

### Políticas gestionadas por AWS, gestionadas por el cliente e inline

Hay tres sabores de política:

| Tipo | Quién la mantiene | Ejemplo de uso |
|---|---|---|
| Gestionada por AWS | AWS (no editable) | `AdministratorAccess`, `ReadOnlyAccess`, `AmazonS3ReadOnlyAccess` |
| Gestionada por el cliente | Tú; reutilizable entre identidades | Tu política a medida para el equipo |
| Inline | Tú; incrustada en un único usuario/grupo/rol | Excepción muy específica de una identidad |

Las gestionadas por AWS tienen ARN bajo la cuenta especial `aws`, por ejemplo `arn:aws:iam::aws:policy/AdministratorAccess` (acceso total, la que se suele dar al administrador humano en cuentas de laboratorio). Como adelanto de 7.7, esta es la pinta que tiene una política en HCL:

```hcl
# Adelanto: la misma política JSON, generada desde HCL con jsonencode()
resource "aws_iam_policy" "lectura_ec2" {
  name = "lectura-ec2"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["ec2:Describe*"]
      Resource = "*"
    }]
  })
}
```

### Mínimo privilegio y MFA

El **principio de mínimo privilegio** manda: concede solo los permisos imprescindibles para la tarea, y amplíalos cuando haga falta, no «por si acaso». Empezar con `AdministratorAccess` para todo el mundo es cómodo y peligroso. Y para identidades humanas, añade **MFA**: aunque roben la contraseña, sin el segundo factor no entran.

> 🔄 **Actualización:** cuando se grabó el curso, crear usuarios IAM con contraseña para cada persona era lo habitual. Hoy AWS recomienda que las **personas** accedan mediante **IAM Identity Center** (federación con credenciales temporales) y reservar los usuarios IAM para casos concretos. En este curso seguiremos usando usuarios IAM porque es lo que Terraform gestiona con los recursos que estudiamos y es perfecto para aprender, pero conviene que sepas cuál es la recomendación actual.

> ⚠️ **Errores comunes:**
> - Confundir usuario y rol: el usuario tiene credenciales permanentes asociadas a una persona/aplicación; el rol se «asume» temporalmente y no tiene credenciales fijas.
> - Escribir `"Effect": "allow"` en minúscula: el JSON de IAM es sensible a mayúsculas; es `Allow`/`Deny`.
> - Abusar de políticas inline: no se reutilizan y son difíciles de auditar; casi siempre es mejor una política gestionada por el cliente.

> 💡 **Buenas prácticas:**
> - Asigna políticas a **grupos**, no a usuarios sueltos: cuando alguien cambie de equipo, bastará moverlo de grupo.
> - Aplica mínimo privilegio desde el principio; es más fácil ampliar que recortar.
> - Exige MFA a toda identidad humana, empezando por el root y tu usuario administrador.

### 🧪 Laboratorio

**Ejercicio (papel y boli):** escribe una política JSON que permita listar los buckets de S3 (`s3:ListAllMyBuckets`) y leer objetos (`s3:GetObject`) solo del bucket `informes-pablo`.

**Solución:**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ListarBuckets",
      "Effect": "Allow",
      "Action": "s3:ListAllMyBuckets",
      "Resource": "*"
    },
    {
      "Sid": "LeerInformes",
      "Effect": "Allow",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::informes-pablo/*"
    }
  ]
}
```

Fíjate en el `/*` final: `GetObject` actúa sobre los **objetos** del bucket, no sobre el bucket en sí, así que el ARN debe cubrir su contenido.

> ❓ **Preguntas de repaso:**
> 1. **¿Qué diferencia autenticación de autorización en IAM?** Autenticación verifica la identidad (credenciales); autorización decide si esa identidad puede realizar la acción (políticas).
> 2. **Si una identidad tiene un `Allow` y un `Deny` sobre la misma acción, ¿qué ocurre?** Gana el `Deny` explícito; siempre prevalece sobre cualquier `Allow`.
> 3. **¿Qué tipo de política es `AdministratorAccess` y cuál es su ARN?** Es una política gestionada por AWS: `arn:aws:iam::aws:policy/AdministratorAccess`.

## 7.4 IAM en la práctica (usuarios, grupos, roles y políticas)

**¿Qué vas a aprender?** En esta lección pasarás de la teoría a la consola: crearás tu usuario administrador del día a día, un grupo con permisos, y entenderás cuándo un **rol** es la pieza correcta. Es la demo de IAM del curso, contada para que puedas reproducirla tú mismo.

### Crear tu administrador del día a día

Recuerda la analogía del edificio: ya tienes la escritura (root), ahora toca hacerte tu tarjeta de empleado. En la consola, entra como root una última vez y ve a **IAM**:

1. **Grupos** → crea el grupo `administradores` y adjúntale la política gestionada `AdministratorAccess`.
2. **Usuarios** → crea el usuario `pablo`, marca el acceso a la consola con contraseña y añádelo al grupo `administradores`.
3. Inicia sesión con ese usuario (la URL de acceso incluye tu ID de cuenta: `https://123456789012.signin.aws.amazon.com/console`), actívale MFA... y guarda el root en el cajón.

¿Ves el patrón? **Política → grupo → usuario**. El usuario no tiene permisos propios: los hereda del grupo. Mañana, cuando entre Lucía al equipo, solo tendrás que crear su usuario y meterla en el grupo.

### Roles: permisos sin credenciales

Los roles resuelven un problema distinto: ¿cómo le das permisos a **un servicio de AWS**? Una instancia EC2 que necesita leer de S3 no puede «iniciar sesión con contraseña». La solución incorrecta sería guardar unas claves de acceso dentro de la máquina (si alguien entra en la máquina, roba las claves). La correcta es crear un **rol** con la política de lectura de S3 y asociárselo a la instancia: AWS le inyecta credenciales **temporales y rotadas automáticamente**. El chaleco de visitante, exactamente. Los roles también sirven para dar acceso entre cuentas y para la federación de personas.

En Terraform, el trío de la consola se escribe así (los recursos de usuario y política se detallan en 7.6 y 7.7):

```hcl
# Grupo de administradores
resource "aws_iam_group" "administradores" {
  name = "administradores"
}

# Adjunta la política gestionada por AWS al grupo
resource "aws_iam_group_policy_attachment" "admin" {
  group      = aws_iam_group.administradores.name
  policy_arn = "arn:aws:iam::aws:policy/AdministratorAccess"
}

# Mete al usuario en el grupo (el usuario se define en 7.6)
resource "aws_iam_user_group_membership" "pablo_admin" {
  user   = aws_iam_user.pablo.name
  groups = [aws_iam_group.administradores.name]
}
```

> ⚠️ **Errores comunes:**
> - Adjuntar `AdministratorAccess` directamente a cada usuario: funciona, pero pierdes la gestión centralizada; hazlo siempre a través de grupos.
> - Guardar claves de acceso dentro de una instancia EC2 en lugar de usar un rol: es la vía clásica de filtración de credenciales.
> - Olvidar activar MFA en tu nuevo usuario administrador: tiene los mismos superpoderes que quieres proteger.

> 💡 **Buenas prácticas:**
> - Después de crear tu usuario administrador, deja de usar el root por completo.
> - Usa nombres descriptivos y consistentes (`administradores`, `desarrolladores`, `solo-lectura`): IAM se audita mejor cuando se lee bien.
> - Para servicios y aplicaciones, roles siempre; las claves de acceso permanentes son el último recurso.

### 🧪 Laboratorio

**Ejercicio:** en la consola, crea el grupo `solo-lectura` con la política gestionada `ReadOnlyAccess`, crea la usuaria `lucia` con acceso a la consola y métela en el grupo. Comprueba que Lucía puede **ver** recursos pero no crearlos.

**Solución:** 1) IAM → **User groups** → *Create group* → nombre `solo-lectura` → busca y marca `ReadOnlyAccess` → crear. 2) IAM → **Users** → *Create user* → nombre `lucia` → habilita acceso a la consola con contraseña autogenerada → en el paso de permisos, añádela al grupo `solo-lectura`. 3) Abre una ventana de incógnito, entra con la URL de tu cuenta y las credenciales de `lucia`, y prueba a crear cualquier recurso: recibirás un error de permisos (*not authorized to perform...*), mientras que listar y describir sí funciona. Ese error es IAM aplicando el *deny* implícito: no hay ningún `Allow` para acciones de escritura.

> ❓ **Preguntas de repaso:**
> 1. **¿Por qué asignar políticas a grupos y no a usuarios?** Porque centraliza la gestión: altas, bajas y cambios de equipo se resuelven moviendo usuarios entre grupos, sin tocar políticas.
> 2. **¿Cuándo usarías un rol en vez de un usuario?** Cuando quien necesita permisos es un servicio de AWS (EC2, Lambda...), otra cuenta o una identidad federada: el rol proporciona credenciales temporales sin contraseñas ni claves fijas.
> 3. **¿Qué significa el error «not authorized to perform» que ve Lucía?** Que ninguna política adjunta a su identidad contiene un `Allow` para esa acción; se aplica la denegación implícita.

## 7.5 Acceso programático: AWS CLI y credenciales

**¿Qué vas a aprender?** Terraform no usa tu contraseña de la consola: usa **claves de acceso**. Aquí aprenderás a crearlas, a configurarlas con `aws configure`, qué ficheros y variables de entorno entran en juego y, muy importante, en qué **orden** busca las credenciales el provider de AWS.

### Dos puertas de entrada

Tu usuario IAM puede tener dos tipos de credenciales, como quien tiene llave del portal y mando del garaje: la **contraseña** abre la consola web (para humanos) y las **claves de acceso** abren la API (para programas: AWS CLI, SDKs y Terraform). Una clave de acceso es una pareja de valores: el **Access Key ID** (empieza por `AKIA...`, actúa como identificador) y la **Secret Access Key** (el secreto propiamente dicho, que AWS solo te muestra **una vez**, al crearla).

Se crean en IAM → tu usuario → **Security credentials** → *Create access key*. La consola te pedirá el caso de uso y te sugerirá alternativas más seguras: para este curso, selecciona el caso de la CLI y confirma.

### `aws configure` y los ficheros de credenciales

Instala la AWS CLI v2 (desde la documentación oficial de AWS) y ejecuta:

```text
$ aws configure
AWS Access Key ID [None]: AKIAIOSFODNN7EXAMPLE
AWS Secret Access Key [None]: wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
Default region name [None]: eu-west-1
Default output format [None]: json
```

Este comando escribe en dos ficheros de tu directorio personal (`~/.aws/` en Linux/macOS, `%USERPROFILE%\.aws\` en Windows):

```text
# ~/.aws/credentials  → las claves
[default]
aws_access_key_id     = AKIAIOSFODNN7EXAMPLE
aws_secret_access_key = wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY

# ~/.aws/config  → región y formato de salida
[default]
region = eu-west-1
output = json
```

`[default]` es el **perfil** por defecto; puedes tener varios (`[trabajo]`, `[personal]`) y elegir con `aws --profile trabajo ...` o con el argumento `profile` del provider. Verifica que todo funciona con el comando «¿quién soy?»:

```text
$ aws sts get-caller-identity
{
    "UserId": "AIDAEXAMPLE123456789",
    "Account": "123456789012",
    "Arn": "arn:aws:iam::123456789012:user/pablo"
}
```

### Variables de entorno y orden de resolución del provider

La alternativa a los ficheros son las variables de entorno, útiles en CI/CD y sesiones puntuales:

```text
$ export AWS_ACCESS_KEY_ID="AKIAIOSFODNN7EXAMPLE"
$ export AWS_SECRET_ACCESS_KEY="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
$ export AWS_REGION="eu-west-1"
```

(En PowerShell: `$env:AWS_ACCESS_KEY_ID = "..."`.) Para la región valen `AWS_REGION` y también `AWS_DEFAULT_REGION` (si están ambas, gana `AWS_REGION`), y existe `AWS_SESSION_TOKEN` para credenciales temporales. Según la documentación del provider de AWS, cuando Terraform necesita credenciales las busca **en este orden** (muy similar al que siguen la CLI y los SDKs):

1. Credenciales estáticas: parámetros del bloque `provider` (desaconsejado para secretos) o variables de entorno (`AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY`).
2. Configuración compartida: los ficheros `~/.aws/credentials` y `~/.aws/config`, con el perfil que indiques (`AWS_PROFILE` o el argumento `profile` del provider).
3. Identidad web (por ejemplo IAM Roles for Service Accounts en EKS), vía `AWS_ROLE_ARN` y `AWS_WEB_IDENTITY_TOKEN_FILE`.
4. Credenciales de rol de tarea en ECS o CodeBuild.
5. Credenciales del perfil de instancia EC2 (IMDS).

Gana la primera fuente que aporte credenciales. Por eso, si tienes variables de entorno exportadas de otra sesión, «taparán» lo que haya en tus ficheros: recuérdalo cuando algo autentique «con el usuario equivocado». La documentación del provider desaconseja explícitamente escribir credenciales en el código, por el riesgo de acabar en un repositorio público.

> ⚠️ **Errores comunes:**
> - Escribir `access_key` y `secret_key` en el bloque `provider` y subirlo a Git: los bots escanean GitHub en minutos y una clave filtrada se convierte en minado de criptomonedas a tu costa.
> - Perder la Secret Access Key: no se puede recuperar; tendrás que desactivar esa clave y crear otra.
> - Tener variables de entorno antiguas exportadas que pisan al perfil de `~/.aws/credentials` y despliegan en la cuenta equivocada. `aws sts get-caller-identity` es tu herramienta de diagnóstico.

> 💡 **Buenas prácticas:**
> - Nunca pongas credenciales en ficheros `.tf`; usa `aws configure` o variables de entorno.
> - Rota tus claves periódicamente y desactiva las que no uses.
> - Usa perfiles con nombre si manejas varias cuentas, y comprueba con `get-caller-identity` antes de cada `apply`.

### 🧪 Laboratorio

**Ejercicio (equivalente al lab «AWS CLI and IAM»):** usando solo la AWS CLI, crea la usuaria `ana`, el grupo `lectores` con la política `ReadOnlyAccess`, mete a `ana` en el grupo y verifica el resultado.

**Solución paso a paso:**

```text
$ aws iam create-user --user-name ana
$ aws iam create-group --group-name lectores
$ aws iam attach-group-policy --group-name lectores \
    --policy-arn arn:aws:iam::aws:policy/ReadOnlyAccess
$ aws iam add-user-to-group --user-name ana --group-name lectores

$ aws iam list-users --query "Users[].UserName"
[
    "ana",
    "pablo"
]
$ aws iam list-attached-group-policies --group-name lectores \
    --query "AttachedPolicies[].PolicyName"
[
    "ReadOnlyAccess"
]
```

Limpieza (en orden inverso, IAM no borra usuarios «con cosas dentro»): `aws iam remove-user-from-group --user-name ana --group-name lectores`, `aws iam detach-group-policy --group-name lectores --policy-arn arn:aws:iam::aws:policy/ReadOnlyAccess`, `aws iam delete-group --group-name lectores` y `aws iam delete-user --user-name ana`.

> ❓ **Preguntas de repaso:**
> 1. **¿Qué dos ficheros escribe `aws configure` y qué guarda cada uno?** `~/.aws/credentials` (claves de acceso por perfil) y `~/.aws/config` (región y formato de salida).
> 2. **Si defines `AWS_ACCESS_KEY_ID` como variable de entorno y además tienes `~/.aws/credentials`, ¿cuál usa Terraform?** La variable de entorno: en el orden de resolución del provider, las variables van antes que los ficheros compartidos.
> 3. **¿Cómo compruebas con qué identidad estás autenticado?** Con `aws sts get-caller-identity`, que devuelve el ID de cuenta y el ARN de la identidad.

## 7.6 Usuarios IAM con Terraform

**¿Qué vas a aprender?** Por fin: tu primer recurso real en AWS gestionado con Terraform. Vas a crear un usuario IAM con el recurso `aws_iam_user`, entender sus argumentos y atributos, y ver el ciclo `plan` → `apply` contra una nube de verdad.

### De la consola al código

Todo lo que hiciste a golpe de clic en 7.4 se puede declarar. La ventaja es la de siempre: el código es reproducible, revisable y auditable. Crear usuarios en la consola es como apuntar la lista de la compra de memoria; con Terraform la lista está escrita, versionada, y cualquiera puede verificar qué se compró y cuándo.

El recurso es `aws_iam_user`. Su único argumento obligatorio es `name`; opcionalmente puedes indicar `path` (una «carpeta» organizativa dentro de IAM, por defecto `/`), `tags`, `permissions_boundary` y `force_destroy` (si es `true`, al destruir el usuario Terraform elimina también credenciales creadas fuera de Terraform que, de otro modo, bloquearían el borrado):

```hcl
# iam-user.tf
resource "aws_iam_user" "pablo" {
  name = "pablo-dev"    # obligatorio: alfanumérico, sin espacios
  path = "/equipo-dev/" # opcional: organización jerárquica (default "/")

  tags = {
    Departamento  = "desarrollo"
    GestionadoPor = "terraform"
  }
}

# El ARN lo exporta AWS al crear el usuario: es un atributo, no un argumento
output "arn_usuario" {
  value = aws_iam_user.pablo.arn
}
```

Ejecuta el flujo completo:

```text
$ terraform plan

Terraform will perform the following actions:

  # aws_iam_user.pablo will be created
  + resource "aws_iam_user" "pablo" {
      + arn           = (known after apply)
      + force_destroy = false
      + id            = (known after apply)
      + name          = "pablo-dev"
      + path          = "/equipo-dev/"
      + tags          = {
          + "Departamento"  = "desarrollo"
          + "GestionadoPor" = "terraform"
        }
      + tags_all      = {
          + "Departamento"  = "desarrollo"
          + "GestionadoPor" = "terraform"
        }
      + unique_id     = (known after apply)
    }

Plan: 1 to add, 0 to change, 0 to destroy.

$ terraform apply -auto-approve
aws_iam_user.pablo: Creating...
aws_iam_user.pablo: Creation complete after 1s [id=pablo-dev]

Outputs:

arn_usuario = "arn:aws:iam::123456789012:user/equipo-dev/pablo-dev"
```

Fíjate en `(known after apply)`: el `arn` y el `unique_id` los decide AWS, así que Terraform no los conoce hasta después de crear el recurso. Entre los **atributos exportados** tienes `arn`, `unique_id` y `tags_all` (las etiquetas del recurso más las heredadas del bloque `default_tags` del provider, si lo usas). El `id` del recurso es el propio nombre del usuario.

Una particularidad de IAM: es un servicio **global**. Aunque el provider apunte a `eu-west-1`, el usuario existe en toda la cuenta, no en una región concreta (por eso su ARN no lleva región: `arn:aws:iam::123456789012:user/...`, con ese hueco vacío entre `iam::` y el número de cuenta).

> ⚠️ **Errores comunes:**
> - Crear el usuario con Terraform y luego editarlo a mano en la consola: en el siguiente `plan` Terraform detectará la deriva e intentará revertir los cambios. Un recurso gestionado por Terraform se toca solo desde Terraform.
> - Usar nombres con espacios o caracteres no válidos: IAM exige nombres alfanuméricos (con algunos símbolos permitidos como `+=,.@_-`), sin espacios.
> - `terraform destroy` que falla con `DeleteConflict`: el usuario tiene claves de acceso o perfil de inicio de sesión creados fuera de Terraform. Solución: `force_destroy = true` o eliminar antes esas credenciales.

> 💡 **Buenas prácticas:**
> - Etiqueta todos los recursos (por ejemplo `GestionadoPor = "terraform"`): en la consola sabrás al instante qué está bajo control del código.
> - Usa `path` para organizar identidades por equipos o entornos en cuentas grandes.
> - Empieza los nombres de recurso Terraform por su función, no por el nombre de la persona, cuando definas plantillas reutilizables.

### 🧪 Laboratorio

**Ejercicio:** crea con Terraform tres usuarios para el equipo (`dev-ana`, `dev-luis`, `dev-marta`) sin repetir tres bloques `resource`, y saca por `output` sus ARN.

**Solución:** usa `for_each` sobre un conjunto de nombres, como aprendiste en el módulo de bucles:

```hcl
variable "desarrolladores" {
  type    = set(string)
  default = ["dev-ana", "dev-luis", "dev-marta"]
}

resource "aws_iam_user" "equipo" {
  for_each = var.desarrolladores # una instancia por nombre
  name     = each.value

  tags = { GestionadoPor = "terraform" }
}

output "arns_equipo" {
  value = { for k, u in aws_iam_user.equipo : k => u.arn }
}
```

```text
$ terraform apply -auto-approve
...
Plan: 3 to add, 0 to change, 0 to destroy.

Outputs:

arns_equipo = {
  "dev-ana"   = "arn:aws:iam::123456789012:user/dev-ana"
  "dev-luis"  = "arn:aws:iam::123456789012:user/dev-luis"
  "dev-marta" = "arn:aws:iam::123456789012:user/dev-marta"
}
```

Termina con `terraform destroy` para dejar la cuenta limpia.

> ❓ **Preguntas de repaso:**
> 1. **¿Cuál es el único argumento obligatorio de `aws_iam_user`?** `name`, el nombre del usuario.
> 2. **¿Por qué el `arn` aparece como `(known after apply)` en el plan?** Porque lo asigna AWS al crear el recurso; Terraform no puede conocerlo antes del `apply`.
> 3. **¿IAM es un servicio regional o global?** Global: las identidades existen para toda la cuenta, independientemente de la región configurada en el provider.

## 7.7 Políticas IAM con Terraform

**¿Qué vas a aprender?** Cerramos el círculo: vas a crear políticas IAM con `aws_iam_policy` escribiendo el JSON de dos formas (heredoc y `jsonencode()`), y a adjuntarlas a usuarios con `aws_iam_user_policy_attachment` referenciando el `arn`. Es el patrón que repetirás constantemente en AWS.

### El JSON dentro del HCL: heredoc

El recurso `aws_iam_policy` crea una política gestionada por el cliente. Su argumento clave es `policy`, que espera **una cadena con el documento JSON**. La forma clásica de incrustar texto multilínea en HCL es el *heredoc*:

```hcl
# policy-heredoc.tf — el JSON tal cual, entre marcadores EOF
resource "aws_iam_policy" "lectura_ec2" {
  name        = "lectura-ec2"
  description = "Permite describir recursos de EC2"

  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["ec2:Describe*"],
      "Resource": "*"
    }
  ]
}
EOF
}
```

Todo lo que hay entre `<<EOF` y la línea `EOF` es literal (el marcador puede ser cualquier palabra; `<<-EOF` permite indentar el cierre). Es exactamente el estilo que usaba el curso original y funciona perfectamente... pero tiene un talón de Aquiles: para Terraform ese JSON es **una cadena opaca**. Una coma de más no se detecta hasta que AWS rechaza la llamada en el `apply`.

### La forma recomendada: `jsonencode()`

La función `jsonencode()` convierte una expresión HCL en JSON válido. Ganas tres cosas: validación de sintaxis en el `plan`, resaltado del editor y, sobre todo, **interpolación natural** de otros recursos:

```hcl
# policy-jsonencode.tf — misma política, escrita como objeto HCL
resource "aws_iam_policy" "lectura_ec2" {
  name        = "lectura-ec2"
  description = "Permite describir recursos de EC2"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["ec2:Describe*"]
        Resource = "*" # aquí podrías interpolar: aws_s3_bucket.datos.arn
      }
    ]
  })
}
```

Es como pasar de escribir una carta a máquina (si te equivocas, lo descubres al enviarla) a escribirla en un procesador con corrector: los errores saltan mientras escribes. El propio ejemplo de la documentación del provider usa `jsonencode()`. Existe además una tercera vía, el data source `aws_iam_policy_document`, que genera el JSON desde bloques HCL puros y es muy popular en proyectos grandes; te la dejo apuntada para cuando termines el curso.

### Adjuntar la política al usuario

Una política suelta no hace nada: hay que **adjuntarla** a una identidad. Para usuarios, el recurso es `aws_iam_user_policy_attachment`, con dos argumentos: `user` (el nombre) y `policy_arn` (el ARN de la política). Aquí brilla el grafo de dependencias de Terraform:

```hcl
resource "aws_iam_user" "auditor" {
  name = "auditor"
}

resource "aws_iam_user_policy_attachment" "auditor_lectura" {
  user       = aws_iam_user.auditor.name     # referencia → dependencia implícita
  policy_arn = aws_iam_policy.lectura_ec2.arn # el ARN exportado por la política
}
```

Al referenciar `.name` y `.arn`, Terraform sabe que debe crear primero el usuario y la política, y después el adjunto. También puedes adjuntar políticas gestionadas por AWS usando su ARN literal: `policy_arn = "arn:aws:iam::aws:policy/ReadOnlyAccess"`.

> 🔄 **Actualización:** quizá veas por ahí el recurso `aws_iam_policy_attachment` (sin `user_` en el nombre). Cuidado: ese recurso gestiona en **exclusiva** todas las asociaciones de una política y entra en conflicto con los recursos `*_policy_attachment` individuales: la documentación advierte de que definir ambos produce diferencias permanentes en el plan. Para adjuntar a usuarios, grupos o roles usa siempre `aws_iam_user_policy_attachment`, `aws_iam_group_policy_attachment` o `aws_iam_role_policy_attachment`.

> ⚠️ **Errores comunes:**
> - Pasar a `user` el ARN del usuario en vez del **nombre**: `user` espera `aws_iam_user.x.name`; el ARN va solo en `policy_arn`.
> - JSON inválido dentro del heredoc (comas finales, comillas sin cerrar): el `plan` no lo detecta y el `apply` falla con `MalformedPolicyDocument`. Con `jsonencode()` este problema desaparece.
> - Mezclar `aws_iam_policy_attachment` con `aws_iam_user_policy_attachment` para la misma política: provoca el conflicto descrito en la caja de actualización.

> 💡 **Buenas prácticas:**
> - Prefiere `jsonencode()` (o `aws_iam_policy_document`) sobre heredocs: validación temprana y referencias a otros recursos.
> - Referencia siempre atributos (`.arn`, `.name`) en lugar de copiar valores a mano: mantienes el grafo de dependencias y evitas errores de transcripción.
> - Añade `description` a tus políticas: tu yo del futuro agradecerá saber para qué era `lectura-ec2` sin leer el JSON.

### 🧪 Laboratorio

**Ejercicio (equivalente al lab «IAM with Terraform»):** crea un proyecto que declare: la usuaria `informes`, una política `solo-lectura-s3` que permita `s3:ListAllMyBuckets` y `s3:GetObject` sobre cualquier recurso, el adjunto entre ambas y un output con el ARN de la política. Aplica, verifica con la CLI y destruye.

**Solución completa:**

```hcl
# main.tf
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

provider "aws" {
  region = "eu-west-1"
}

resource "aws_iam_user" "informes" {
  name = "informes"
  tags = { GestionadoPor = "terraform" }
}

resource "aws_iam_policy" "solo_lectura_s3" {
  name        = "solo-lectura-s3"
  description = "Listar buckets y leer objetos de S3"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["s3:ListAllMyBuckets", "s3:GetObject"]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_user_policy_attachment" "informes_s3" {
  user       = aws_iam_user.informes.name
  policy_arn = aws_iam_policy.solo_lectura_s3.arn
}

output "arn_politica" {
  value = aws_iam_policy.solo_lectura_s3.arn
}
```

```text
$ terraform init && terraform apply -auto-approve
...
Plan: 3 to add, 0 to change, 0 to destroy.
aws_iam_user.informes: Creation complete after 1s [id=informes]
aws_iam_policy.solo_lectura_s3: Creation complete after 1s
aws_iam_user_policy_attachment.informes_s3: Creation complete after 0s

Outputs:

arn_politica = "arn:aws:iam::123456789012:policy/solo-lectura-s3"

$ aws iam list-attached-user-policies --user-name informes \
    --query "AttachedPolicies[].PolicyName"
[
    "solo-lectura-s3"
]

$ terraform destroy -auto-approve
...
Destroy complete! Resources: 3 destroyed.
```

Observa el orden del `destroy`: Terraform elimina primero el adjunto y después la política y el usuario, recorriendo el grafo de dependencias a la inversa.

> ❓ **Preguntas de repaso:**
> 1. **¿Qué ventajas tiene `jsonencode()` frente a un heredoc para el argumento `policy`?** Valida la sintaxis en el `plan`, permite interpolar atributos de otros recursos y evita errores de JSON manual que solo aparecerían en el `apply`.
> 2. **¿Qué argumentos requiere `aws_iam_user_policy_attachment`?** `user` (nombre del usuario IAM) y `policy_arn` (ARN de la política a adjuntar).
> 3. **¿Por qué conviene evitar `aws_iam_policy_attachment`?** Porque gestiona en exclusiva todas las asociaciones de la política y entra en conflicto con los adjuntos individuales de usuario, grupo o rol, generando diferencias permanentes en el plan.

---

📌 **Recapitulando el módulo (parte 1):** ya tienes cuenta de AWS protegida, entiendes IAM (identidades, políticas JSON, mínimo privilegio), sabes autenticar Terraform con claves de acceso y conoces el orden de resolución de credenciales, y has creado tus primeros recursos reales: usuarios y políticas IAM declarados en HCL. En la siguiente parte del módulo pasaremos a los servicios estrella: **EC2 y S3 con Terraform**.
