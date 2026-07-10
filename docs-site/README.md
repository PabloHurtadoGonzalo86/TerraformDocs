# Terraform Basics Training Course · sitio de documentación

[![Built with Starlight](https://astro.badg.es/v2/built-with-starlight/tiny.svg)](https://starlight.astro.build)

Sitio de documentación construido con [Astro](https://astro.build) + [Starlight](https://starlight.astro.build) para el manual de estudio del curso [Terraform Basics Training Course](https://kodekloud.com/courses/terraform-for-beginners) de KodeKloud. El contenido fuente en Markdown "plano" vive en [`../manual-terraform-basics-training-course/`](../manual-terraform-basics-training-course/); este proyecto lo publica como un sitio navegable con búsqueda, en `src/content/docs/manual/`.

Se despliega automáticamente a GitHub Pages en cada push a `main` que toque `docs-site/` (ver [`.github/workflows/deploy-docs.yml`](../.github/workflows/deploy-docs.yml)).

## Estructura

```
.
├── public/
├── src/
│   ├── content/
│   │   └── docs/
│   │       ├── index.mdx          # Portada
│   │       └── manual/            # Las 13 páginas del manual, una por módulo del curso
│   └── content.config.ts
├── astro.config.mjs                # Título, sidebar y configuración de GitHub Pages (site/base)
└── package.json
```

## Comandos

Todos los comandos se ejecutan desde este directorio (`docs-site/`):

| Comando                   | Acción                                            |
| :------------------------ | :------------------------------------------------- |
| `npm install`              | Instala las dependencias                            |
| `npm run dev`               | Arranca el servidor de desarrollo en `localhost:4321` |
| `npm run build`             | Genera el sitio de producción en `./dist/`           |
| `npm run preview`           | Previsualiza el build en local antes de desplegar    |

## Más información

[Documentación de Starlight](https://starlight.astro.build/es/) · [Documentación de Astro](https://docs.astro.build)
