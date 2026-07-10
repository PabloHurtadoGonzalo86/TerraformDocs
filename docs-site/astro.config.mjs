// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';

// https://astro.build/config
export default defineConfig({
	site: 'https://pablohurtadogonzalo86.github.io',
	base: '/TerraformDocs',
	integrations: [
		starlight({
			title: 'Terraform Basics Training Course',
			description:
				'Manual completo en español del curso Terraform Basics Training Course (KodeKloud), verificado contra la documentación oficial de Terraform y AWS.',
			locales: {
				root: { label: 'Español', lang: 'es' },
			},
			social: [
				{
					icon: 'github',
					label: 'GitHub',
					href: 'https://github.com/PabloHurtadoGonzalo86/TerraformDocs',
				},
			],
			editLink: {
				baseUrl: 'https://github.com/PabloHurtadoGonzalo86/TerraformDocs/edit/main/docs-site/',
			},
			sidebar: [
				{
					label: 'Manual del curso',
					items: [
						{ label: '01 · Introducción al curso', slug: 'manual/01-introduccion' },
						{ label: '02 · Introducción a Infrastructure as Code', slug: 'manual/02-introduccion-iac' },
						{ label: '03 · Primeros pasos con Terraform', slug: 'manual/03-primeros-pasos' },
						{ label: '04 · Fundamentos de Terraform', slug: 'manual/04-fundamentos' },
						{ label: '05 · El estado de Terraform', slug: 'manual/05-estado' },
						{ label: '06 · Trabajando con Terraform', slug: 'manual/06-trabajando-con-terraform' },
						{ label: '07 · Terraform con AWS', slug: 'manual/07-terraform-con-aws' },
						{ label: '08 · Estado remoto', slug: 'manual/08-estado-remoto' },
						{ label: '09 · Provisioners y EC2', slug: 'manual/09-provisioners-ec2' },
						{ label: '10 · Taint, debugging e import', slug: 'manual/10-taint-debug-import' },
						{ label: '11 · Módulos de Terraform', slug: 'manual/11-modulos' },
						{ label: '12 · Funciones, condicionales y workspaces', slug: 'manual/12-funciones-workspaces' },
						{ label: '13 · Conclusión y kit de recursos', slug: 'manual/13-conclusion' },
					],
				},
			],
		}),
	],
});
