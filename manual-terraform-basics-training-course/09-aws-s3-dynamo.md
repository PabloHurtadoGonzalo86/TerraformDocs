## 7.8 Introducción a Amazon S3

**¿Qué vas a aprender?** En esta lección conocerás Amazon S3 (Simple Storage Service), el servicio de almacenamiento de objetos de AWS: qué son los buckets y los objetos, por qué los nombres de bucket son únicos a nivel global, cómo se construye la URL de un objeto y cómo se controla quién puede acceder a qué (bucket policies, ACL y Block Public Access). Es la base imprescindible antes de crear buckets con Terraform en la siguiente lección.

### Buckets y objetos: un trastero con etiquetas

S3 es un servicio de **almacenamiento de objetos**: guarda ficheros (imágenes, backups, logs, vídeos, HTML...) junto con sus metadatos, de forma duradera y accesible por HTTP. No es un disco duro ni un sistema de ficheros: no montas S3 en tu máquina, sino que subes y descargas objetos mediante una API.

Piensa en S3 como una empresa de trasteros gigante. Tú alquilas un **bucket** (tu trastero) y dentro guardas **objetos** (cajas). Cada caja lleva una etiqueta única dentro de tu trastero: la **key** del objeto. Una key puede ser `foto.jpg` o `proyectos/2026/informe.pdf`. Ojo al detalle: en S3 **no existen carpetas reales**; cuando la key contiene barras, la consola de AWS te las pinta como carpetas por comodidad, pero internamente solo hay un espacio plano de keys. Es como escribir "estantería 3 / balda 2 / caja azul" en la etiqueta: la caja sigue siendo una sola caja.

Cada objeto puede pesar hasta 50 TB (límite ampliado por AWS en diciembre de 2025; antes era 5 TB), y un bucket puede contener un número ilimitado de objetos.

### Nombres únicos a nivel global

El nombre de un bucket vive en un **espacio de nombres global compartido**: debe ser único entre *todas* las cuentas de AWS de la partición estándar, no solo en la tuya. Si alguien en Australia ya creó un bucket llamado `mis-fotos`, tú no puedes. Las reglas principales (verifícalas si dudas, están en la documentación de AWS):

- Entre **3 y 63 caracteres**.
- Solo **minúsculas, números, puntos y guiones**; debe empezar y terminar por letra o número.
- Sin guiones bajos, sin mayúsculas, sin puntos consecutivos y sin formato de dirección IP (`192.168.5.4` no vale).

Por eso verás la costumbre de añadir sufijos aleatorios o el ID de cuenta al nombre: `informes-pablo-2026-x7k2`.

### La URL de un objeto

Aunque el espacio de nombres es global, cada bucket se crea en **una región concreta**. La URL de un objeto en estilo *virtual-hosted* (el recomendado) es:

```text
https://<nombre-bucket>.s3.<región>.amazonaws.com/<key>
```

Por ejemplo, el objeto `docs/bienvenida.txt` del bucket `informes-pablo-2026-x7k2` en Irlanda:

```text
https://informes-pablo-2026-x7k2.s3.eu-west-1.amazonaws.com/docs/bienvenida.txt
```

Existe también el estilo *path-style* (`https://s3.<región>.amazonaws.com/<bucket>/<key>`), que AWS mantiene por compatibilidad pero desaconseja para nuevos desarrollos.

### Permisos: policies, ACL y Block Public Access

Por defecto, **todo en S3 es privado**: solo el propietario del bucket accede a él. Para abrir la puerta a otros hay tres mecanismos:

1. **Bucket policies**: documentos JSON de IAM adjuntos al bucket que definen quién (`Principal`) puede hacer qué (`Action`, como `s3:GetObject`) sobre qué (`Resource`). Es el mecanismo recomendado hoy.
2. **ACL (Access Control Lists)**: el mecanismo histórico, anterior a IAM, que asignaba permisos por objeto o por bucket a "grantees". Hoy AWS recomienda **mantenerlas deshabilitadas** y usar policies.
3. **Block Public Access**: un "cortafuegos" de cuatro interruptores a nivel de bucket (o de cuenta) que bloquea cualquier intento de hacer público el contenido mediante ACL o policies, aunque alguien lo configure por error.

> 🔄 **Actualización:** cuando se grabó el curso, las ACL estaban habilitadas por defecto. Desde abril de 2023, todos los buckets nuevos se crean con **Object Ownership = "Bucket owner enforced"** (ACL deshabilitadas: las peticiones para modificarlas fallan) y con **Block Public Access activado**. El control de acceso moderno se hace con bucket policies y políticas IAM; las ACL solo se reactivan en casos muy concretos.

> ⚠️ **Errores comunes:**
> - Pensar que las "carpetas" de la consola son directorios reales: solo son prefijos de la key. Si borras todos los objetos con un prefijo, la "carpeta" desaparece.
> - Elegir un nombre de bucket genérico (`test`, `backup`) y frustrarte porque "ya existe": está ocupado por otra cuenta del mundo. Añade siempre un sufijo propio.
> - Confundir "global" con "sin región": el *nombre* es global, pero los *datos* residen en la región que elijas, lo que afecta a latencia, coste y normativa.
> - Intentar hacer público un objeto poniéndole una ACL `public-read` en un bucket moderno: fallará porque las ACL están deshabilitadas y Block Public Access lo impide.

> 💡 **Buenas prácticas:**
> - Incluye en el nombre del bucket un identificador tuyo y algo aleatorio para evitar colisiones y nombres predecibles.
> - Gestiona el acceso con bucket policies e IAM; deja las ACL deshabilitadas salvo necesidad justificada.
> - Mantén Block Public Access activado salvo que el bucket sirva contenido público a propósito (por ejemplo, una web estática).

### 🧪 Laboratorio

**Ejercicio (sin Terraform todavía):** entra en la consola de AWS y crea a mano un bucket llamado `s3-intro-<tu-nombre>-<4 dígitos aleatorios>` en `eu-west-1`. Sube un fichero `hola.txt`, localiza su URL de objeto e intenta abrirla en el navegador.

**Solución:** al crear el bucket verás que "Bloquear todo el acceso público" viene marcado y que Object Ownership es "ACL deshabilitadas": déjalo así. Tras subir `hola.txt`, en la pestaña de propiedades del objeto verás la URL `https://s3-intro-<tu-nombre>-<4-dígitos>.s3.eu-west-1.amazonaws.com/hola.txt`. Al abrirla en el navegador recibirás un XML con `AccessDenied`: es lo esperado, porque el objeto es privado y tu navegador es un usuario anónimo. Esa denegación es la demostración práctica de "todo privado por defecto". Borra el objeto y el bucket al terminar.

> ❓ **Preguntas de repaso:**
> 1. *¿Puede existir tu bucket `facturas` si otra cuenta de AWS ya lo creó en otra región?* No. El espacio de nombres es global dentro de la partición: si el nombre está cogido en cualquier cuenta y región, no puedes usarlo.
> 2. *¿Qué mecanismo usarías hoy para dar acceso de lectura a otra cuenta: ACL o bucket policy?* Bucket policy. Las ACL son el mecanismo histórico y están deshabilitadas por defecto en buckets nuevos.
> 3. *¿Qué hace Block Public Access?* Actúa como salvaguarda: bloquea que ACL o policies concedan acceso público, incluso si alguien las configura por error.

## 7.9 S3 con Terraform

**¿Qué vas a aprender?** Aquí pasamos de la teoría a la práctica: crearás buckets con `aws_s3_bucket`, subirás objetos con `aws_s3_object` y adjuntarás una bucket policy con `aws_s3_bucket_policy`. También verás el cambio más importante del provider AWS desde que se grabó el curso: la división del recurso de bucket en recursos independientes.

### El recurso aws_s3_bucket

Crear un bucket es sorprendentemente simple. El argumento `bucket` es opcional: si lo omites, Terraform genera un nombre único por ti (útil para evitar colisiones).

```hcl
resource "aws_s3_bucket" "finanzas" {
  # Nombre global único: sufijo propio para evitar colisiones
  bucket = "finanzas-pablo-2026-x7k2"

  # Permite destruir el bucket aunque contenga objetos (¡cuidado en producción!)
  force_destroy = true

  tags = {
    Descripcion = "Documentos del departamento de finanzas"
    Entorno     = "aprendizaje"
  }
}
```

Tras `terraform apply`:

```text
aws_s3_bucket.finanzas: Creating...
aws_s3_bucket.finanzas: Creation complete after 2s [id=finanzas-pablo-2026-x7k2]

Apply complete! Resources: 1 added, 0 changed, 0 destroyed.
```

El recurso exporta atributos útiles: `id` (el nombre), `arn` (con formato `arn:aws:s3:::finanzas-pablo-2026-x7k2`), `bucket_domain_name` y `bucket_regional_domain_name`.

> 🔄 **Actualización:** el curso se grabó con el provider AWS v3, donde `acl`, `versioning`, `policy`, etc. eran argumentos del propio `aws_s3_bucket`. Desde la **v4 del provider** (2022) esas configuraciones se extrajeron a **recursos independientes**: `aws_s3_bucket_acl`, `aws_s3_bucket_versioning`, `aws_s3_bucket_policy`, `aws_s3_bucket_server_side_encryption_configuration`, `aws_s3_bucket_cors_configuration`, `aws_s3_bucket_lifecycle_configuration`... El argumento `acl` dentro de `aws_s3_bucket` sigue apareciendo en la doc pero **está deprecado**. Además, `aws_s3_bucket_object` pasó a llamarse `aws_s3_object`. Si ves código antiguo con todo dentro del bloque del bucket, ya sabes por qué no compila igual hoy.

La lógica del cambio es la de los muebles modulares: antes el bucket era un armario monolítico con todos los cajones soldados; ahora cada cajón (versionado, cifrado, policy...) es una pieza que encajas aparte. Así cada configuración tiene su propio ciclo de vida y su propio plan.

### Subir objetos: aws_s3_object

Solo `bucket` y `key` son obligatorios. El contenido puede venir de un fichero local (`source`), de una cadena en línea (`content`) o de datos en base64 (`content_base64`); los tres son **mutuamente excluyentes**.

```hcl
# Opción A: subir un fichero local
resource "aws_s3_object" "politica_gastos" {
  bucket = aws_s3_bucket.finanzas.id
  key    = "docs/politica-gastos.pdf"   # la "ruta" dentro del bucket
  source = "${path.module}/ficheros/politica-gastos.pdf"

  # filemd5() cambia si cambia el fichero => Terraform re-sube el objeto
  etag = filemd5("${path.module}/ficheros/politica-gastos.pdf")
}

# Opción B: contenido generado en línea, sin fichero
resource "aws_s3_object" "leeme" {
  bucket       = aws_s3_bucket.finanzas.id
  key          = "docs/LEEME.txt"
  content      = "Bucket gestionado por Terraform. No subir ficheros a mano."
  content_type = "text/plain"
}
```

El detalle del `etag` es importante: sin él, si editas el PDF local, Terraform no detecta el cambio (el argumento `source` —la ruta— no ha cambiado). Con `etag = filemd5(...)`, cualquier modificación del fichero altera el hash y fuerza la re-subida.

### Bucket policy con jsonencode

Para dar acceso a otro principal (una usuaria IAM, otra cuenta...), adjuntamos una policy. La forma más directa es `jsonencode()`, que convierte un objeto HCL en JSON válido y te ahorra pelearte con comillas escapadas:

```hcl
resource "aws_s3_bucket_policy" "lectura_finanzas" {
  bucket = aws_s3_bucket.finanzas.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid       = "PermitirLecturaLucia"
      Effect    = "Allow"
      Principal = { AWS = "arn:aws:iam::123456789012:user/lucia" }
      Action    = "s3:GetObject"
      Resource  = "${aws_s3_bucket.finanzas.arn}/*"   # todos los objetos
    }]
  })
}
```

La alternativa más idiomática en proyectos grandes es el data source `aws_iam_policy_document`, que valida la estructura y permite componer statements:

```hcl
data "aws_iam_policy_document" "lectura" {
  statement {
    sid     = "PermitirLecturaLucia"
    effect  = "Allow"
    actions = ["s3:GetObject"]

    principals {
      type        = "AWS"
      identifiers = ["arn:aws:iam::123456789012:user/lucia"]
    }

    resources = ["${aws_s3_bucket.finanzas.arn}/*"]
  }
}

resource "aws_s3_bucket_policy" "lectura_finanzas" {
  bucket = aws_s3_bucket.finanzas.id
  policy = data.aws_iam_policy_document.lectura.json
}
```

### ¿Y las ACL y Block Public Access en Terraform?

Si algún día necesitas ACL (caso raro hoy), recuerda que primero debes habilitarlas cambiando el Object Ownership, y encadenarlo con `depends_on`:

```hcl
resource "aws_s3_bucket_ownership_controls" "finanzas" {
  bucket = aws_s3_bucket.finanzas.id
  rule {
    object_ownership = "BucketOwnerPreferred"   # reactiva las ACL
  }
}

resource "aws_s3_bucket_acl" "finanzas" {
  depends_on = [aws_s3_bucket_ownership_controls.finanzas]
  bucket     = aws_s3_bucket.finanzas.id
  acl        = "private"
}
```

Y Block Public Access se gestiona con su propio recurso. Atención: en el recurso de Terraform los cuatro argumentos tienen **valor por defecto `false`**, así que decláralos explícitamente:

```hcl
resource "aws_s3_bucket_public_access_block" "finanzas" {
  bucket = aws_s3_bucket.finanzas.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
```

> ⚠️ **Errores comunes:**
> - Usar `acl = "private"` dentro de `aws_s3_bucket` siguiendo tutoriales antiguos: está deprecado; usa `aws_s3_bucket_acl` (y solo si de verdad necesitas ACL).
> - `Error: BucketAlreadyExists` en el apply: el nombre está cogido por otra cuenta. No es un bug de Terraform; cambia el nombre.
> - Intentar `terraform destroy` sobre un bucket con objetos: falla con `BucketNotEmpty` salvo que hayas puesto `force_destroy = true`.
> - Olvidar el `etag`/`source_hash` en `aws_s3_object` y extrañarte de que el objeto en S3 no se actualice al cambiar el fichero local.

> 💡 **Buenas prácticas:**
> - Referencia siempre el bucket con `aws_s3_bucket.X.id` y su ARN con `aws_s3_bucket.X.arn` en lugar de repetir el nombre a mano: creas dependencias implícitas y evitas erratas.
> - Prefiere `jsonencode()` o `aws_iam_policy_document` antes que pegar JSON crudo entre comillas: obtienes validación de sintaxis en el plan.
> - Declara explícitamente `aws_s3_bucket_public_access_block` con todo a `true` en buckets privados: documenta la intención y protege buckets antiguos.

### 🧪 Laboratorio

**Enunciado:** crea con Terraform un bucket llamado `pelis-<sufijo aleatorio>` usando el provider `random` para el sufijo, sube un objeto `catalogo/estrenos-2026.txt` con el contenido `"Dune 3, Toy Story 5"` y expón como output la URL virtual-hosted del objeto. Después destruye todo.

**Solución paso a paso:**

```hcl
terraform {
  required_providers {
    aws    = { source = "hashicorp/aws" }
    random = { source = "hashicorp/random" }
  }
}

provider "aws" {
  region = "eu-west-1"
}

resource "random_id" "sufijo" {
  byte_length = 4   # 8 caracteres hexadecimales
}

resource "aws_s3_bucket" "pelis" {
  bucket        = "pelis-${random_id.sufijo.hex}"
  force_destroy = true
}

resource "aws_s3_object" "estrenos" {
  bucket       = aws_s3_bucket.pelis.id
  key          = "catalogo/estrenos-2026.txt"
  content      = "Dune 3, Toy Story 5"
  content_type = "text/plain"
}

output "url_objeto" {
  value = "https://${aws_s3_bucket.pelis.bucket_regional_domain_name}/${aws_s3_object.estrenos.key}"
}
```

Ejecuta `terraform init`, `terraform plan` (verás `Plan: 3 to add`) y `terraform apply -auto-approve`:

```text
random_id.sufijo: Creating...
random_id.sufijo: Creation complete after 0s [id=sv-qxg]
aws_s3_bucket.pelis: Creating...
aws_s3_bucket.pelis: Creation complete after 2s [id=pelis-b2ffaac6]
aws_s3_object.estrenos: Creating...
aws_s3_object.estrenos: Creation complete after 1s [id=catalogo/estrenos-2026.txt]

Apply complete! Resources: 3 added, 0 changed, 0 destroyed.

Outputs:

url_objeto = "https://pelis-b2ffaac6.s3.eu-west-1.amazonaws.com/catalogo/estrenos-2026.txt"
```

Comprueba el objeto con `aws s3 ls s3://pelis-b2ffaac6/catalogo/` y termina con `terraform destroy -auto-approve` (gracias a `force_destroy`, borra bucket y contenido sin quejarse).

> ❓ **Preguntas de repaso:**
> 1. *¿Qué diferencia hay entre `source` y `content` en `aws_s3_object`?* `source` sube un fichero local indicando su ruta; `content` define el contenido como cadena directamente en el código. Son excluyentes entre sí (junto con `content_base64`).
> 2. *¿Por qué ya no se recomienda el argumento `acl` de `aws_s3_bucket`?* Desde la v4 del provider está deprecado: cada configuración del bucket vive en su propio recurso (`aws_s3_bucket_acl`, `aws_s3_bucket_policy`, etc.).
> 3. *¿Para qué sirve `${aws_s3_bucket.finanzas.arn}/*` en una policy?* El ARN del bucket identifica al bucket; añadir `/*` hace que la policy aplique a **todos los objetos** de su interior, que es lo que exige `s3:GetObject`.

## 7.10 Introducción a DynamoDB

**¿Qué vas a aprender?** En esta lección descubrirás DynamoDB, la base de datos NoSQL gestionada de AWS: su modelo de tablas, ítems y atributos, cómo funciona la clave primaria (partition key y sort key), de dónde sale su rendimiento y cómo se factura (aprovisionado frente a bajo demanda).

### Una base de datos NoSQL clave-valor

DynamoDB es una base de datos **NoSQL de tipo clave-valor y documental**, totalmente gestionada: no hay servidores que administrar, escala prácticamente sin límite y ofrece latencias de milisegundos de un solo dígito a cualquier escala, con replicación automática de los datos en varias zonas de disponibilidad.

Su estructura tiene tres niveles: una **tabla** contiene **ítems** (equivalentes a filas) y cada ítem es una colección de **atributos** (equivalentes a columnas). La gran diferencia con SQL: DynamoDB es **schemaless** salvo por la clave. Solo los atributos que forman la clave primaria deben declararse de antemano; el resto puede variar de un ítem a otro. Un coche puede tener `color` y otro no, sin migraciones ni `ALTER TABLE`.

### La clave primaria: partition key y sort key

Hay dos tipos de clave primaria:

| Tipo | Composición | Regla de unicidad |
|---|---|---|
| Simple | Solo **partition key** (hash key) | No puede haber dos ítems con la misma partition key |
| Compuesta | **Partition key + sort key** (range key) | Puede repetirse la partition key, pero la pareja debe ser única |

La partition key es como el recepcionista de un hotel enorme: aplica una **función hash** a su valor y el resultado decide en qué partición física se guarda el ítem. Por eso también se la llama *hash key*. La sort key (o *range key*) ordena físicamente los ítems que comparten partition key, lo que permite consultas del tipo "dame todas las canciones del artista X cuyo título empieza por H". Los atributos de clave solo pueden ser de tipo cadena, número o binario, y cada ítem puede ocupar como máximo **400 KB**.

Este diseño explica el rendimiento: como toda búsqueda parte de la clave, DynamoDB salta directamente a la partición correcta sin recorrer la tabla. La contrapartida es que consultar por atributos que no son clave exige un *scan* completo (lento y caro) o índices secundarios.

### Facturación: PROVISIONED frente a PAY_PER_REQUEST

DynamoDB ofrece dos modos de capacidad:

- **PROVISIONED**: reservas capacidad de lectura y escritura (RCU/WCU) por adelantado. Pagas por lo reservado, lo uses o no. Ideal para cargas predecibles; si te pasas del límite, las peticiones se estrangulan (*throttling*).
- **PAY_PER_REQUEST** (bajo demanda): pagas por cada lectura/escritura realizada, sin planificar nada. Ideal para cargas irregulares o desconocidas, y para aprender sin sustos.

### Un vistazo rápido con la CLI

Antes de pasar a Terraform, conviene ver la materia prima. Con la AWS CLI puedes crear y consultar una tabla en un minuto:

```text
$ aws dynamodb scan --table-name flota
{
    "Items": [
        {
            "vin": { "S": "VF1RFB00558123456" },
            "fabricante": { "S": "Renault" }
        }
    ],
    "Count": 1,
    "ScannedCount": 1
}
```

Fíjate en el formato de los atributos: cada valor va envuelto en un descriptor de tipo (`"S"` para cadena, `"N"` para número, `"B"` para binario...). Ese mismo formato lo reutilizarás en Terraform en la próxima lección.

> ⚠️ **Errores comunes:**
> - Diseñar la tabla "como en SQL" y luego consultar por atributos que no son clave: acabarás haciendo *scans* carísimos. En DynamoDB primero se piensan las consultas y después la clave.
> - Elegir una partition key con pocos valores distintos (por ejemplo, `pais`): concentra el tráfico en pocas particiones ("hot partitions") y degrada el rendimiento.
> - Confundir la unicidad: en una tabla con clave compuesta, la partition key **sí** puede repetirse; lo único que debe ser único es el par partition+sort.

> 💡 **Buenas prácticas:**
> - Para aprender y para cargas impredecibles, usa `PAY_PER_REQUEST`: sin capacidad que calcular y sin throttling por infraprovisionar.
> - Elige partition keys de alta cardinalidad (IDs, matrículas, UUIDs) para repartir bien los datos.
> - Guarda en DynamoDB ítems pequeños y frecuentes; los ficheros grandes van a S3 y en la tabla solo guardas su key.

### 🧪 Laboratorio

**Mini-ejercicio:** sin escribir Terraform, diseña sobre papel la tabla para una app de podcasts donde la consulta principal es "dame todos los episodios de un programa ordenados por fecha". ¿Qué clave primaria eliges y por qué?

**Solución:** clave compuesta con `programa_id` como partition key (alta cardinalidad, agrupa los episodios de cada programa en la misma partición) y `fecha_publicacion` como sort key (los episodios quedan almacenados ordenados por fecha, así que la consulta "episodios del programa X entre enero y marzo" es una query directa, sin scan). Una clave simple con `episodio_id` sería única, pero obligaría a escanear toda la tabla para listar los episodios de un programa.

> ❓ **Preguntas de repaso:**
> 1. *¿Qué papel juega la función hash en DynamoDB?* Transforma el valor de la partition key en la partición física donde se almacena el ítem, lo que permite localizarlo directamente sin recorrer la tabla.
> 2. *¿Cuándo elegirías PROVISIONED en vez de PAY_PER_REQUEST?* Con tráfico estable y predecible, donde reservar RCU/WCU sale más barato que pagar por petición.
> 3. *¿Qué atributos hay que definir de antemano al crear una tabla?* Solo los de la clave primaria (y los de claves de índices, si los hay); el resto de atributos es libre en cada ítem.

## 7.11 DynamoDB con Terraform

**¿Qué vas a aprender?** Cerrarás el módulo creando tablas DynamoDB con `aws_dynamodb_table` (con ambos modos de facturación) e insertando ítems con `aws_dynamodb_table_item`, incluido el peculiar formato JSON con descriptores de tipo. Al terminar sabrás modelar y poblar una tabla completa desde código.

### El recurso aws_dynamodb_table

Los argumentos esenciales son `name`, `hash_key` y, como mínimo, un bloque `attribute` que defina esa clave. Es como el impreso de alta de un club: solo te piden rellenar los campos que identifican al socio; el resto de la ficha se completa sobre la marcha.

```hcl
resource "aws_dynamodb_table" "flota" {
  name         = "flota"
  billing_mode = "PAY_PER_REQUEST"   # bajo demanda: sin capacidad que declarar
  hash_key     = "vin"               # partition key

  # Todo atributo usado como clave DEBE declararse en un bloque attribute
  attribute {
    name = "vin"
    type = "S"   # S = cadena, N = número, B = binario
  }
}
```

Dos reglas de oro verificadas en la documentación del provider:

1. La `hash_key` (y la `range_key`, si existe) **debe** estar definida también como bloque `attribute`.
2. **Solo** se declaran como `attribute` los atributos que son clave de la tabla o de algún índice (GSI/LSI). Si declaras atributos "normales" ahí, el plan fallará o entrarás en un bucle de cambios perpetuos. Los atributos no clave simplemente aparecen al insertar ítems: recuerda que la tabla es schemaless.

Con el modo `PROVISIONED` (que es el valor por defecto de `billing_mode`), los argumentos `read_capacity` y `write_capacity` pasan a ser obligatorios:

```hcl
resource "aws_dynamodb_table" "puntuaciones" {
  name           = "puntuaciones"
  billing_mode   = "PROVISIONED"
  read_capacity  = 5    # RCU reservadas
  write_capacity = 5    # WCU reservadas
  hash_key       = "jugador_id"
  range_key      = "partida"        # sort key => clave compuesta

  attribute {
    name = "jugador_id"
    type = "S"
  }

  attribute {
    name = "partida"
    type = "N"
  }
}
```

### Insertar ítems: aws_dynamodb_table_item

Para datos de configuración pequeños y estáticos, Terraform puede insertar ítems. El argumento `item` recibe JSON en el **formato atributo-tipo** de DynamoDB que viste en la CLI: cada valor envuelto en su descriptor (`{"S": ...}`, `{"N": ...}`). Los números también van entre comillas dentro del descriptor `N`.

```hcl
resource "aws_dynamodb_table_item" "coche_1" {
  table_name = aws_dynamodb_table.flota.name
  hash_key   = aws_dynamodb_table.flota.hash_key   # referencia, sin repetir "vin"

  item = <<ITEM
{
  "vin":        {"S": "VF1RFB00558123456"},
  "fabricante": {"S": "Renault"},
  "modelo":     {"S": "Clio"},
  "anio":       {"N": "2023"}
}
ITEM
}
```

Fíjate en el *heredoc* (`<<ITEM ... ITEM`): permite escribir JSON multilínea sin escapar comillas. Y observa que `fabricante`, `modelo` y `anio` no aparecen por ningún sitio en la definición de la tabla: schemaless en acción. La propia documentación advierte de que este recurso **no está pensado para gestionar grandes volúmenes de datos** —no escala—; para cargas reales usa tu aplicación o herramientas de importación.

El `apply` completo:

```text
aws_dynamodb_table.flota: Creating...
aws_dynamodb_table.flota: Creation complete after 11s [id=flota]
aws_dynamodb_table_item.coche_1: Creating...
aws_dynamodb_table_item.coche_1: Creation complete after 1s [id=flota,VF1RFB00558123456]

Apply complete! Resources: 2 added, 0 changed, 0 destroyed.
```

> ⚠️ **Errores comunes:**
> - Declarar en `attribute` campos que no son clave (por ejemplo `modelo`): provoca errores o *diffs* infinitos en cada plan. Solo claves de tabla e índices.
> - Olvidar `read_capacity`/`write_capacity` con `billing_mode = "PROVISIONED"`: el plan falla porque son obligatorios en ese modo.
> - Escribir el ítem en JSON "normal" (`"anio": 2023`) en vez del formato atributo-tipo (`"anio": {"N": "2023"}`): DynamoDB rechaza la petición.
> - Cambiar la `hash_key` de una tabla existente pensando que se actualiza en caliente: fuerza la **recreación** de la tabla (y la pérdida de sus datos si no hay backup).

> 💡 **Buenas prácticas:**
> - Referencia `table_name` y `hash_key` desde el recurso de la tabla (`aws_dynamodb_table.flota.name`) para mantener una única fuente de verdad.
> - Reserva `aws_dynamodb_table_item` para datos de arranque pequeños (configuración, catálogos mínimos); nunca para datos de negocio vivos.
> - En tablas de producción, añade `deletion_protection_enabled = true` y valora `point_in_time_recovery` para poder restaurar ante errores.

### 🧪 Laboratorio

**Enunciado:** crea una tabla `inventario_juegos` en modo bajo demanda con clave compuesta (`plataforma` como partition key, `titulo` como sort key), inserta dos juegos de plataformas distintas con un atributo extra `precio`, y expón el ARN de la tabla como output. Verifica con la CLI y destruye.

**Solución paso a paso:**

```hcl
provider "aws" {
  region = "eu-west-1"
}

resource "aws_dynamodb_table" "inventario" {
  name         = "inventario_juegos"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "plataforma"
  range_key    = "titulo"

  attribute {
    name = "plataforma"
    type = "S"
  }

  attribute {
    name = "titulo"
    type = "S"
  }
}

resource "aws_dynamodb_table_item" "juego_switch" {
  table_name = aws_dynamodb_table.inventario.name
  hash_key   = aws_dynamodb_table.inventario.hash_key
  range_key  = aws_dynamodb_table.inventario.range_key

  item = <<ITEM
{
  "plataforma": {"S": "Switch"},
  "titulo":     {"S": "Zelda TOTK"},
  "precio":     {"N": "59.99"}
}
ITEM
}

resource "aws_dynamodb_table_item" "juego_ps5" {
  table_name = aws_dynamodb_table.inventario.name
  hash_key   = aws_dynamodb_table.inventario.hash_key
  range_key  = aws_dynamodb_table.inventario.range_key

  item = <<ITEM
{
  "plataforma": {"S": "PS5"},
  "titulo":     {"S": "Gran Turismo 7"},
  "precio":     {"N": "49.99"}
}
ITEM
}

output "arn_tabla" {
  value = aws_dynamodb_table.inventario.arn
}
```

Pasos: `terraform init` y `terraform apply -auto-approve` (verás `Plan: 3 to add`; como los dos ítems solo dependen de la tabla, se crean en paralelo). Verifica:

```text
$ aws dynamodb scan --table-name inventario_juegos --query "Count"
2
```

El output mostrará algo como `arn_tabla = "arn:aws:dynamodb:eu-west-1:123456789012:table/inventario_juegos"`. Cierra con `terraform destroy -auto-approve`: primero caen los ítems y después la tabla, respetando el grafo de dependencias.

> ❓ **Preguntas de repaso:**
> 1. *¿Por qué la tabla `flota` solo declara el atributo `vin` si sus ítems tienen cuatro campos?* Porque en el bloque `attribute` solo se declaran los atributos que forman claves; DynamoDB es schemaless para el resto, que aparecen al escribir cada ítem.
> 2. *¿Qué pareja de argumentos se vuelve obligatoria al usar `billing_mode = "PROVISIONED"`?* `read_capacity` y `write_capacity`, la capacidad reservada de lectura y escritura.
> 3. *¿Qué significa `{"N": "2023"}` en el argumento `item`?* Es el formato atributo-tipo de DynamoDB: el descriptor `N` indica que el valor es numérico; el número en sí siempre se escribe como cadena dentro del JSON.
