---
title: "Módulo 9 · Terraform, EC2 y provisioners"
description: "EC2 con Terraform, provisioners remote-exec/local-exec y sus alternativas recomendadas."
---

## 9.1 Introducción a Amazon EC2

**¿Qué vas a aprender?** En esta lección vas a entender qué es Amazon EC2, el servicio de máquinas virtuales de AWS, y los cinco conceptos que necesitas dominar antes de tocar Terraform: AMIs, tipos de instancia, key pairs, security groups y user data. Con estas piezas claras, el código HCL de las siguientes lecciones te resultará casi obvio.

### Qué es EC2

**Amazon EC2** (Elastic Compute Cloud) es el servicio con el que alquilas servidores virtuales —llamados **instancias**— en la nube de AWS. Pagas por el tiempo que la instancia está encendida, puedes crearlas y destruirlas en minutos, y eliges exactamente cuánta CPU, memoria y red necesitas.

La analogía que mejor funciona es la de **alquilar un piso amueblado**: la AMI es el "estado en que te entregan el piso" (vacío, amueblado, con cocina montada...), el tipo de instancia es el tamaño del piso (estudio, dos habitaciones, ático), el key pair es la llave de la puerta, el security group es el portero que decide quién puede llamar al timbre, y el user data es la lista de tareas que le dejas al personal para que la ejecute nada más entregarte las llaves.

### Las cinco piezas

- **AMI (Amazon Machine Image)**: la plantilla desde la que arranca la instancia. Incluye el sistema operativo y, opcionalmente, software preinstalado. Cada AMI tiene un ID (por ejemplo `ami-0abcd1234...`) que **cambia según la región**: la AMI de Ubuntu 22.04 en `eu-west-1` tiene un ID distinto que en `us-east-1`.
- **Tipo de instancia**: define el hardware. El nombre sigue la convención `familia+generación.tamaño`. En `t3.micro`: `t` es la familia (propósito general con rendimiento *burstable*, es decir, acumula créditos de CPU y los gasta en picos), `3` es la generación y `micro` el tamaño. Otras familias habituales: `m` (propósito general equilibrado), `c` (optimizada para cómputo), `r` (optimizada para memoria). A más generación, mejor relación precio/rendimiento: `t3` corre sobre el hipervisor Nitro, más moderno que el Xen de `t2`.
- **Key pair**: un par de claves SSH. AWS guarda la **pública** y tú conservas la **privada** para conectarte. AWS nunca almacena tu clave privada.
- **Security group**: un cortafuegos virtual a nivel de instancia. Define reglas de entrada (*ingress*) y salida (*egress*) por protocolo, puerto y rango de IPs (CIDR). Es **con estado**: si permites la entrada por el puerto 22, la respuesta sale automáticamente.
- **User data**: un script (normalmente Bash o directivas cloud-init) que la instancia ejecuta **una sola vez en el primer arranque**. Perfecto para instalar y arrancar software automáticamente.

> ⚠️ **Errores comunes:**
> - Copiar un ID de AMI de un tutorial y usarlo en otra región: obtendrás un error `InvalidAMIID.NotFound`. Las AMIs son regionales.
> - Confundir `t2.micro` con "gratis siempre": la capa gratuita de AWS tiene límites y caduca (horas mensuales durante 12 meses en cuentas antiguas; un plan basado en créditos para cuentas creadas desde julio de 2025); revisa las condiciones vigentes de tu cuenta.
> - Pensar que el user data se ejecuta en cada reinicio: por defecto solo corre en el primer arranque de la instancia.

> 💡 **Buenas prácticas:**
> - Para aprender, usa los tamaños más pequeños (`t3.micro` o `t2.micro`) y **destruye lo que no uses**: en la nube, olvidar es pagar.
> - Anota siempre la región en la que trabajas y sé consistente; muchos "no encuentro mi instancia" son solo estar mirando otra región en la consola.

### 🧪 Laboratorio

Esta lección no tiene lab en el curso, así que hacemos un mini-ejercicio de criterio. **Enunciado**: asigna la familia adecuada (`t`, `c`, `r`) a estos tres casos: (1) un blog personal con visitas esporádicas, (2) un servicio que codifica vídeo, (3) una base de datos en memoria tipo Redis.

**Solución**: (1) `t` — carga baja con picos ocasionales, ideal para burstable; (2) `c` — la codificación es intensiva en CPU; (3) `r` — Redis vive en RAM, prioriza memoria.

> ❓ **Preguntas de repaso:**
> - **¿Qué significa cada parte de `t3.micro`?** `t` = familia (propósito general burstable), `3` = generación, `micro` = tamaño.
> - **¿Quién guarda la clave privada de un key pair?** Tú. AWS solo almacena la pública.
> - **¿Un security group bloquea la respuesta a una conexión permitida?** No: es con estado, el tráfico de retorno se permite automáticamente.

## 9.2 Desplegar una instancia EC2 desde la consola

**¿Qué vas a aprender?** Antes de automatizar nada conviene hacerlo una vez a mano. Aquí recorremos conceptualmente el asistente "Launch an instance" de la consola de AWS para que, cuando escribas Terraform, sepas exactamente qué campo del asistente corresponde a cada argumento HCL.

### El recorrido por el asistente

Hacerlo desde la consola es como **pedir una pizza personalizada por teléfono**: te van preguntando masa, tamaño e ingredientes uno a uno. Funciona, pero si mañana quieres diez pizzas idénticas tendrás que repetir la llamada diez veces sin equivocarte. Terraform será la receta escrita; la consola, la llamada.

El asistente (EC2 → *Instances* → *Launch instances*) te pide, en orden:

1. **Name and tags**: un nombre, que en realidad es una etiqueta con clave `Name`. En Terraform será el mapa `tags`.
2. **Application and OS Images (AMI)**: eliges la imagen — Amazon Linux, Ubuntu, etc. Corresponde al argumento `ami`.
3. **Instance type**: por ejemplo `t3.micro`. Corresponde a `instance_type`.
4. **Key pair (login)**: seleccionas un key pair existente o creas uno nuevo (la consola te descarga el `.pem` **una única vez**; guárdalo bien). Corresponde a `key_name`.
5. **Network settings**: VPC, subred, IP pública y el security group, donde añades reglas como "SSH desde mi IP". Corresponde a `vpc_security_group_ids`.
6. **Configure storage**: el disco raíz (EBS), por ejemplo 8 GiB gp3.
7. **Advanced details**: al final encontrarás el campo **User data**, donde puedes pegar un script de arranque. Corresponde a `user_data`.

Pulsas **Launch instance**, esperas a que el estado pase a `Running` y las comprobaciones de estado a `2/2 checks passed`, copias la **IP pública** y te conectas:

```text
$ ssh -i ~/Descargas/mi-clave.pem ubuntu@54.170.12.34
Welcome to Ubuntu 22.04 LTS (GNU/Linux ...)
ubuntu@ip-172-31-5-201:~$
```

El usuario depende de la AMI: `ubuntu` en Ubuntu, `ec2-user` en Amazon Linux.

> 🔄 **Actualización:** cuando se grabó el curso, la consola usaba un asistente antiguo de 7 pasos secuenciales. Desde 2022 AWS lo sustituyó por el asistente de una sola página descrito arriba; los conceptos son idénticos, solo cambia la disposición.

> ⚠️ **Errores comunes:**
> - Perder el `.pem` descargado: AWS no te lo vuelve a dar; tendrías que crear otro key pair.
> - Conectar por SSH y recibir `Permission denied (publickey)`: suele ser usuario equivocado (`root` en vez de `ubuntu`) o permisos del fichero; ejecuta `chmod 400 mi-clave.pem` en Linux/macOS.
> - Abrir el puerto 22 a `0.0.0.0/0` "para probar": restringe a tu IP (`x.x.x.x/32`).

> 💡 **Buenas prácticas:**
> - Haz este proceso manual una vez y solo una: su valor es didáctico. Todo lo reproducible debe vivir en código.
> - Etiqueta todo (`Name`, `Project`, `Environment`); en una cuenta con decenas de recursos, las etiquetas son tu mapa.

### 🧪 Laboratorio

**Enunciado**: lanza desde la consola una instancia `t3.micro` con Ubuntu 22.04, un security group que permita SSH solo desde tu IP, conéctate y luego termínala.

**Solución**: (1) Sigue el asistente con AMI Ubuntu Server 22.04 y tipo `t3.micro`; (2) crea el key pair `lab-consola` y guarda el `.pem`; (3) en *Network settings*, regla SSH con origen *My IP*; (4) lanza, espera `Running`, copia la IP pública y conéctate con `ssh -i lab-consola.pem ubuntu@IP`; (5) dentro, ejecuta `uname -a` para verificar; (6) sal y en la consola: *Instance state* → *Terminate instance*. Comprueba que pasa a `Terminated`.

> ❓ **Preguntas de repaso:**
> - **¿En qué sección del asistente se pega el script de arranque?** En *Advanced details* → *User data*.
> - **¿Por qué la consola no escala como método de despliegue?** Porque es manual: no es repetible, ni versionable, ni auditable; cada despliegue depende de memoria humana.

## 9.3 EC2 con Terraform

**¿Qué vas a aprender?** Aquí traducimos el asistente de la consola a HCL: el recurso `aws_instance` con sus argumentos principales, `aws_key_pair` para la clave SSH, `aws_security_group` para el cortafuegos y un `output` con la IP pública para conectarte al terminar el `apply`.

### El proyecto completo

Si la consola era pedir la pizza por teléfono, esto es **dejar la receta escrita**: cualquiera (incluido tu yo del futuro) obtiene el mismo resultado ejecutando `terraform apply`. Crea un directorio con este `main.tf`:

```hcl
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

provider "aws" {
  region = "eu-west-1" # Irlanda; las credenciales, por variables de entorno
}

# Busca dinámicamente la AMI más reciente de Ubuntu 22.04
# (evita hardcodear un ID que caduca y cambia por región)
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }
}

# Sube TU clave pública a AWS; la privada no sale de tu máquina
resource "aws_key_pair" "web" {
  key_name   = "web-key"
  public_key = file("~/.ssh/id_rsa.pub")
}

# Cortafuegos: SSH y HTTP de entrada, todo permitido de salida
resource "aws_security_group" "web" {
  name        = "web-sg"
  description = "Permite SSH y HTTP"

  ingress {
    description = "SSH desde mi IP"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["203.0.113.10/32"] # cambia por tu IP pública
  }

  ingress {
    description = "HTTP desde cualquier sitio"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1" # -1 = todos los protocolos
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_instance" "web" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = "t3.micro"
  key_name               = aws_key_pair.web.key_name
  vpc_security_group_ids = [aws_security_group.web.id]

  # Script de primer arranque: instala nginx sin intervención manual
  user_data = <<-EOF
              #!/bin/bash
              apt-get update -y
              apt-get install -y nginx
              EOF

  tags = {
    Name = "webserver"
  }
}

output "ip_publica" {
  value       = aws_instance.web.public_ip
  description = "IP pública para SSH y HTTP"
}
```

Fíjate en las **referencias implícitas**: `aws_instance` usa `aws_key_pair.web.key_name` y `aws_security_group.web.id`, así que Terraform crea primero la clave y el security group, y después la instancia. Ejecuta:

```text
$ terraform apply
...
Plan: 3 to add, 0 to change, 0 to destroy.
...
aws_instance.web: Creation complete after 34s [id=i-0f3a9c1b2d4e5f678]

Apply complete! Resources: 3 added, 0 changed, 0 destroyed.

Outputs:

ip_publica = "54.170.12.34"
```

Y te conectas con `ssh -i ~/.ssh/id_rsa ubuntu@54.170.12.34`. Al abrir `http://54.170.12.34` en el navegador verás la página de bienvenida de nginx.

> 🔄 **Actualización:** dos cambios relevantes desde que se grabó el curso. Primero, cambiar `user_data` en una instancia existente **ya no fuerza su recreación por defecto**: Terraform la para y la vuelve a arrancar (*stop/start*) para actualizar el atributo, y el script no se re-ejecuta (cloud-init solo lo corre en el primer arranque); si quieres que un cambio de user data recree la instancia, añade `user_data_replace_on_change = true`. Segundo, el proveedor AWS recomienda hoy definir las reglas con los recursos independientes `aws_vpc_security_group_ingress_rule` y `aws_vpc_security_group_egress_rule` en lugar de bloques `ingress`/`egress` inline, porque evitan conflictos entre configuraciones; los bloques inline siguen funcionando y son los que usa el curso.

> ⚠️ **Errores comunes:**
> - Pasarle a `public_key` la ruta del fichero en vez de su contenido: necesitas `file("~/.ssh/id_rsa.pub")`, que lee el contenido.
> - Usar `security_groups` (nombres, para EC2-Classic/default VPC) en vez de `vpc_security_group_ids` (IDs): mezcla ambos y tendrás recreaciones inesperadas.
> - Olvidar la regla `egress`: a diferencia del security group por defecto de AWS, **Terraform elimina la salida permitida** si no la declaras, y tu `apt-get update` se quedará colgado.
> - Hardcodear la AMI: usa el data source `aws_ami` para no depender de IDs que Canonical retira con el tiempo.

> 💡 **Buenas prácticas:**
> - Credenciales fuera del código: usa `aws configure` o las variables de entorno `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY`.
> - Extrae región, tipo de instancia y CIDR de tu IP a variables con valores por defecto sensatos.
> - Añade `description` a cada regla del security group: te lo agradecerás en la consola.

### 🧪 Laboratorio

**Enunciado**: partiendo del código anterior, (1) parametriza el tipo de instancia con una variable `instance_type` (por defecto `t3.micro`), (2) añade un output `url` que devuelva `http://IP_PUBLICA`, y (3) verifica que nginx responde.

**Solución**: añade a un fichero `variables.tf`:

```hcl
variable "instance_type" {
  type        = string
  default     = "t3.micro"
  description = "Tipo de instancia EC2"
}
```

En el recurso, sustituye por `instance_type = var.instance_type`. Añade el output:

```hcl
output "url" {
  value = "http://${aws_instance.web.public_ip}"
}
```

Ejecuta `terraform apply`, espera un minuto a que el user data termine y comprueba con `curl $(terraform output -raw url)`: debe devolver el HTML de bienvenida de nginx. Termina con `terraform destroy`.

> ❓ **Preguntas de repaso:**
> - **¿Por qué Terraform crea el security group antes que la instancia sin ningún `depends_on`?** Porque la instancia referencia `aws_security_group.web.id`, y esa referencia crea una dependencia implícita.
> - **¿Qué atributo exportado usas para la IP pública?** `public_ip` del recurso `aws_instance`.
> - **¿Qué hace hoy Terraform si cambias `user_data`?** No recrea la instancia (salvo `user_data_replace_on_change = true`): la para y la arranca de nuevo para actualizar el atributo, y el script no se vuelve a ejecutar.

## 9.4 Provisioners de Terraform

**¿Qué vas a aprender?** Los provisioners permiten ejecutar comandos como parte del ciclo de vida de un recurso: `remote-exec` los ejecuta **dentro** de la máquina recién creada (vía SSH) y `local-exec` en **tu** máquina, donde corre Terraform. Verás su sintaxis, el bloque `connection` y el objeto `self`.

### remote-exec y local-exec

Piensa en una **empresa de mudanzas**: Terraform, de serie, te entrega los muebles en el portal (crea la infraestructura). Un provisioner es contratar además el servicio de "montaje": entran en casa y ensamblan los muebles (configuran el interior de la máquina). Es cómodo, pero ya no es solo una mudanza: necesitan tus llaves y pueden fallar por motivos ajenos al transporte. Esa tensión la exploraremos en 9.6.

Los provisioners se declaran **dentro del bloque `resource`**. `remote-exec` exige un bloque `connection` para que Terraform sepa cómo entrar en la máquina, y dentro del provisioner se usa **`self`** para referirse al propio recurso (escribir `aws_instance.web.public_ip` ahí crearía una dependencia circular):

```hcl
resource "aws_instance" "web" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = "t3.micro"
  key_name               = aws_key_pair.web.key_name
  vpc_security_group_ids = [aws_security_group.web.id]

  # Cómo se conecta Terraform a la instancia recién creada
  connection {
    type        = "ssh"
    host        = self.public_ip            # "self" = este recurso
    user        = "ubuntu"                  # usuario de la AMI de Ubuntu
    private_key = file("~/.ssh/id_rsa")     # tu clave privada local
  }

  # Se ejecuta DENTRO de la instancia, tras crearla
  provisioner "remote-exec" {
    inline = [
      "sudo apt-get update -y",
      "sudo apt-get install -y nginx",
    ]
  }

  # Se ejecuta en TU máquina (donde corre terraform apply)
  provisioner "local-exec" {
    command = "echo Instancia creada con IP ${self.public_ip} >> despliegues.txt"
  }

  tags = { Name = "webserver" }
}
```

`remote-exec` acepta `inline` (lista de comandos), `script` o `scripts` (ficheros locales que sube y ejecuta). `local-exec` acepta `command` y opcionales como `interpreter`, `working_dir` y `environment`. Durante el `apply` verás algo así:

```text
aws_instance.web: Provisioning with 'remote-exec'...
aws_instance.web (remote-exec): Connecting to remote host via SSH...
aws_instance.web (remote-exec):   Host: 54.170.12.34
aws_instance.web (remote-exec):   User: ubuntu
aws_instance.web (remote-exec): Connected!
aws_instance.web (remote-exec): Setting up nginx (1.18.0) ...
aws_instance.web: Provisioning with 'local-exec'...
aws_instance.web: Creation complete after 1m12s [id=i-0f3a9c1b2d4e5f678]
```

Un detalle importante: para que `remote-exec` funcione, **Terraform necesita alcanzar la instancia por red**: IP pública y puerto 22 abierto a la IP desde la que ejecutas Terraform. Con `user_data` (lección 9.3) esto no hace falta, porque el script lo ejecuta la propia instancia.

> ⚠️ **Errores comunes:**
> - Usar `aws_instance.web.public_ip` dentro del propio recurso: ciclo de dependencias. Usa siempre `self`.
> - `timeout - last error: dial tcp ...:22`: el security group no permite SSH desde tu IP o la instancia no tiene IP pública.
> - Ejecutar comandos que piden confirmación interactiva: no hay terminal humano al otro lado; usa flags como `-y`.
> - Olvidar que los provisioners **no aparecen en el plan**: `terraform plan` no puede predecir qué harán ni detectar si su resultado cambió.

> 💡 **Buenas prácticas:**
> - Antes de escribir un `remote-exec`, pregúntate si un `user_data` haría lo mismo sin exigir conectividad SSH desde Terraform.
> - Reserva `local-exec` para integraciones puntuales (avisos, inventarios locales), no como pegamento estructural de tu infraestructura.
> - Haz los comandos **idempotentes**: si el provisioner se repite (al recrear el recurso), no debe romper nada.

### 🧪 Laboratorio

**Enunciado**: modifica la instancia de 9.3 para que (1) un `remote-exec` instale nginx y escriba `¡Hola desde Terraform!` en `/var/www/html/index.html`, y (2) un `local-exec` guarde la IP pública en `inventario.txt`.

**Solución**: usa el código de arriba cambiando el `inline` por:

```hcl
  provisioner "remote-exec" {
    inline = [
      "sudo apt-get update -y",
      "sudo apt-get install -y nginx",
      "echo '¡Hola desde Terraform!' | sudo tee /var/www/html/index.html",
    ]
  }

  provisioner "local-exec" {
    command = "echo ${self.public_ip} >> inventario.txt"
  }
```

Quita el `user_data` para no duplicar la instalación. Ejecuta `terraform apply`, comprueba con `curl http://$(terraform output -raw ip_publica)` que responde tu mensaje, y verifica que `inventario.txt` contiene la IP. Destruye al terminar.

> ❓ **Preguntas de repaso:**
> - **¿Dónde se ejecuta cada provisioner?** `remote-exec` dentro del recurso remoto (vía SSH/WinRM); `local-exec` en la máquina donde corre Terraform.
> - **¿Qué bloque es obligatorio para `remote-exec`?** Un bloque `connection` (aquí de tipo `ssh`).
> - **¿Por qué `self` y no el nombre del recurso?** Para evitar que el recurso se referencie a sí mismo y provoque un ciclo de dependencias.

## 9.5 Comportamiento de los provisioners

**¿Qué vas a aprender?** Los provisioners tienen dos "cuándos" y dos "qué pasa si fallo". Verás los provisioners de creación frente a los de destrucción (`when = destroy`), y cómo controlar el fallo con `on_failure = continue` o `fail`, incluido el efecto de marcar el recurso como *tainted*.

### Creación, destrucción y fallo

Un provisioner es como el **rito de entrada y salida de un piso de alquiler**: hay tareas al recibir las llaves (dar de alta la luz) y tareas al devolverlas (dar de baja los suministros). Por defecto un provisioner es **de creación**: se ejecuta justo después de crear el recurso, y nunca más (ni en updates ni en destroys). Con `when = destroy` lo conviertes en **de destrucción**: se ejecuta justo *antes* de destruir el recurso; si el provisioner falla, el destroy falla y el recurso no se destruye.

El segundo eje es `on_failure`. Su valor por defecto es `fail`: si el comando devuelve error, el `apply` se detiene. Y ojo al matiz clave: si falla un provisioner de creación, **el recurso ya se ha creado**, así que Terraform lo marca como **tainted** ("contaminado"): en el siguiente `apply` lo destruirá y recreará entero, porque no puede garantizar que quedara bien configurado. Con `on_failure = continue`, Terraform ignora el error y sigue como si nada.

```hcl
resource "aws_instance" "web" {
  ami           = data.aws_ami.ubuntu.id
  instance_type = "t3.micro"

  # Provisioner de CREACIÓN que no detiene el apply si falla
  provisioner "local-exec" {
    command    = "curl -fs http://${self.public_ip} > /dev/null"
    on_failure = continue # fail (defecto) | continue
  }

  # Provisioner de DESTRUCCIÓN: corre justo antes del destroy
  provisioner "local-exec" {
    when    = destroy
    command = "echo 'Se va a destruir la instancia ${self.id}' >> auditoria.txt"
  }
}
```

Así se ve un fallo con el comportamiento por defecto:

```text
aws_instance.web: Provisioning with 'remote-exec'...
╷
│ Error: remote-exec provisioner error
│   error executing "/tmp/terraform_1234.sh": Process exited with status 127
╵

$ terraform plan
aws_instance.web is tainted, so must be replaced
-/+ resource "aws_instance" "web" { ... }
Plan: 1 to add, 0 to change, 1 to destroy.
```

Dos limitaciones de los provisioners de destrucción que conviene grabarse: solo se ejecutan si **el bloque `resource` sigue existiendo en la configuración** en el momento del destroy (si borras el bloque entero, el provisioner desaparece con él), y **no se ejecutan sobre recursos tainted** al reemplazarlos. Además, dentro de un provisioner de destrucción solo puedes referenciar `self` (y `count.index` / `each.key`), no otros recursos.

> ⚠️ **Errores comunes:**
> - Esperar que un provisioner de creación se re-ejecute al cambiar su `command`: no lo hará; solo corre al crear el recurso. Tendrías que recrearlo (`terraform apply -replace=...`).
> - Confiar en un provisioner de destrucción para limpiezas críticas: si el recurso está tainted o el bloque ya no está en el código, no se ejecutará.
> - Abusar de `on_failure = continue`: silencia errores y puedes acabar con máquinas a medio configurar sin enterarte.

> 💡 **Buenas prácticas:**
> - Deja `on_failure` en su valor por defecto salvo para tareas realmente opcionales (notificaciones, métricas).
> - Si un recurso queda tainted y sabes que en realidad está sano, puedes quitarle la marca con `terraform untaint DIRECCION`, pero investiga antes por qué falló.
> - Trata los provisioners de destrucción como "mejor esfuerzo", nunca como garantía.

### 🧪 Laboratorio

**Enunciado**: provoca un fallo controlado. (1) Añade a tu instancia un `remote-exec` con el comando inexistente `comando-que-no-existe`; (2) aplica y observa el error y el estado tainted; (3) corrige con `on_failure = continue` y verifica que el `apply` termina bien.

**Solución**: añade el provisioner con `inline = ["comando-que-no-existe"]` y aplica: verás el error `Process exited with status 127` y, en `terraform plan`, el mensaje `aws_instance.web is tainted, so must be replaced`. Añade `on_failure = continue` dentro del provisioner y ejecuta `terraform apply`: Terraform reemplaza la instancia, el provisioner vuelve a fallar, pero esta vez lo ignora y el apply acaba en `Apply complete`. Destruye al terminar.

> ❓ **Preguntas de repaso:**
> - **¿Qué le pasa a un recurso cuya provisión de creación falla (con `on_failure = fail`)?** Queda marcado como tainted y se destruirá y recreará en el siguiente apply.
> - **¿Cuándo se ejecuta un provisioner con `when = destroy`?** Justo antes de destruir el recurso; si falla, el destroy se aborta.
> - **¿Los provisioners de destrucción se ejecutan siempre?** No: no corren sobre recursos tainted ni si el bloque resource ya no está en la configuración.

## 9.6 Consideraciones y alternativas a los provisioners

**¿Qué vas a aprender?** Cerramos el módulo con la parte más importante: por qué la propia HashiCorp recomienda usar provisioners **solo como último recurso**, y qué alternativas usar en su lugar: `user_data`/cloud-init, AMIs preconfiguradas con Packer y herramientas de gestión de configuración.

### Por qué "último recurso"

La documentación oficial de Terraform es explícita: los provisioners deben ser una **última opción** ("last resort") porque Terraform está diseñado para infraestructura inmutable y **no puede modelar lo que ocurre dentro de un provisioner**. Volviendo a la mudanza: la empresa de transporte es excelente moviendo cajas (recursos), pero cuando le pides que además monte los muebles (configure el software), sales de su especialidad y aparecen los problemas:

- **Invisibles para el plan**: `terraform plan` no muestra qué harán los provisioners ni detecta desviaciones; lo que hacen no queda registrado en el estado.
- **Más superficie de fallo y de ataque**: `remote-exec` exige conectividad directa y credenciales (SSH) desde donde corre Terraform, algo especialmente incómodo en pipelines de CI.
- **Acoplamiento frágil**: un cambio en el script no dispara ningún update; el recurso "parece" al día aunque su interior haya divergido.

### Las alternativas, de más simple a más potente

| Alternativa | Qué es | Cuándo usarla |
|---|---|---|
| `user_data` / cloud-init | Script o directivas que ejecuta la propia instancia al arrancar | Bootstrap sencillo: instalar paquetes, escribir configuración inicial |
| AMI preconfigurada (Packer) | Horneas una imagen con todo el software ya instalado | Arranques rápidos, flotas homogéneas, infraestructura inmutable |
| Gestión de configuración (Ansible, Chef, Puppet) | Herramienta específica que mantiene la configuración a lo largo del tiempo | Configuración compleja o que evoluciona tras el despliegue |

La primera ya la conoces de 9.3: `user_data` no necesita SSH ni credenciales, la nube lo entrega y cloud-init lo ejecuta dentro de la máquina. La segunda invierte el orden: en lugar de "crear máquina y luego instalarle nginx", con **Packer** (otra herramienta de HashiCorp) construyes una AMI que **ya lleva nginx**, y Terraform solo la referencia en `ami`; es el enfoque de **infraestructura inmutable**: si hay que cambiar algo, horneas una imagen nueva y reemplazas instancias, en vez de parchearlas en caliente. La tercera delega en herramientas cuyo trabajo es precisamente mantener configuración: descripciones idempotentes, informes de desviación, ejecución continua.

```hcl
# Enfoque inmutable: la AMI horneada con Packer ya contiene la aplicación
data "aws_ami" "app" {
  most_recent = true
  owners      = ["self"] # tus propias AMIs

  filter {
    name   = "name"
    values = ["mi-app-nginx-*"] # nombre que le diste en Packer
  }
}

resource "aws_instance" "app" {
  ami           = data.aws_ami.app.id
  instance_type = "t3.micro"
  # Sin provisioners y sin user_data: no hay nada que instalar
  tags = { Name = "app-inmutable" }
}
```

¿Cuándo sí usar un provisioner? Cuando ninguna alternativa llega: un sistema legado sin API que exige un comando puntual, o una acción que debe ocurrir exactamente en el momento de crear/destruir el recurso y que ningún argumento del provider cubre.

> ⚠️ **Errores comunes:**
> - Convertir los provisioners en tu herramienta de configuración por defecto "porque ya conozco la sintaxis": acabarás con despliegues frágiles imposibles de razonar desde el plan.
> - Meter lógica pesada en `user_data`: alarga el arranque y complica el diagnóstico; si el script crece, hornea una AMI.
> - Olvidar que lo que hace un provisioner no está en el estado: si el script cambia, Terraform no se entera ni corrige nada.

> 💡 **Buenas prácticas:**
> - Orden de preferencia: argumento nativo del provider → `user_data`/cloud-init → imagen horneada con Packer → gestión de configuración → y, solo si nada de eso sirve, provisioner.
> - Si usas Packer, versiona los nombres de tus AMIs (`mi-app-nginx-1.4.2-...`) y selecciónalas con `data "aws_ami"`.
> - Documenta en un comentario *por qué* cada provisioner que dejes en el código es imprescindible: es una señal para revisores y para tu futuro yo.

### 🧪 Laboratorio

**Enunciado**: refactoriza el laboratorio de 9.4 eliminando los provisioners: consigue el mismo servidor web (nginx sirviendo "¡Hola desde Terraform!") solo con `user_data`, y explica qué has ganado.

**Solución**: elimina los bloques `provisioner` y `connection` y añade a la instancia:

```hcl
  user_data = <<-EOF
              #!/bin/bash
              apt-get update -y
              apt-get install -y nginx
              echo '¡Hola desde Terraform!' > /var/www/html/index.html
              EOF
```

Aplica y comprueba con `curl http://$(terraform output -raw ip_publica)` (dale un minuto al primer arranque). Ganancias: ya no necesitas abrir el puerto 22 a la máquina que ejecuta Terraform, ni distribuir la clave privada, ni depender de que SSH esté disponible durante el apply; incluso podrías cerrar el puerto 22 por completo. Destruye al terminar.

> ❓ **Preguntas de repaso:**
> - **¿Por qué recomienda HashiCorp evitar los provisioners?** Porque Terraform no puede modelar ni planificar lo que hacen: quedan fuera del plan y del estado, añaden requisitos de red/credenciales y hacen el despliegue más frágil.
> - **¿Qué ventaja clave tiene `user_data` sobre `remote-exec`?** Lo ejecuta la propia instancia al arrancar: no requiere conectividad SSH ni credenciales desde donde corre Terraform.
> - **¿Qué papel juega Packer en este ecosistema?** Hornear AMIs con el software ya instalado, habilitando infraestructura inmutable en la que Terraform solo referencia la imagen.
