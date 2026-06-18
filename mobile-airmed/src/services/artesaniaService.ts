import { Artesano, Producto } from '../types/index';

export const artesanos: Artesano[] = [
  {
    id: 1,
    nombre: 'María López',
    especialidad: 'Cerámica Talavera',
    imagen: 'https://picsum.photos/id/1011/200',
    ubicacion: 'Puebla, México',
  },
  {
    id: 2,
    nombre: 'Juan Méndez',
    especialidad: 'Textiles Otomí',
    imagen: 'https://picsum.photos/id/1012/200',
    ubicacion: 'Querétaro, México',
  },
  {
    id: 3,
    nombre: 'Rosa Hernández',
    especialidad: 'Alebrijes',
    imagen: 'https://picsum.photos/id/1013/200',
    ubicacion: 'Oaxaca, México',
  },
];

export const productos: Producto[] = [
  {
    id: 1,
    nombre: 'Jarrón Talavera Azul',
    descripcion: 'Jarrón hecho a mano con técnica tradicional de Talavera.',
    imagen: 'https://picsum.photos/id/200/300',
    precioInicial: 500,
    precioActual: 650,
    artesanoId: 1,
    fechaFin: '2026-07-01',
  },
  {
    id: 2,
    nombre: 'Mantel Bordado Otomí',
    descripcion: 'Mantel con bordado a mano con motivos de la cultura Otomí.',
    imagen: 'https://picsum.photos/id/201/300',
    precioInicial: 800,
    precioActual: 950,
    artesanoId: 2,
    fechaFin: '2026-07-05',
  },
  {
    id: 3,
    nombre: 'Alebrije Dragón',
    descripcion: 'Figura de madera pintada a mano representando un dragón.',
    imagen: 'https://picsum.photos/id/202/300',
    precioInicial: 1200,
    precioActual: 1200,
    artesanoId: 3,
    fechaFin: '2026-07-10',
  },
];