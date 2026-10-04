const categoryColorNames = {
  '#dc3545': 'Rojo',
  '#fd7e14': 'Naranja',
  '#ffc107': 'Amarillo',
  '#28a745': 'Verde',
  '#20c997': 'Verde agua',
  '#0dcaf0': 'Celeste',
  '#0d6efd': 'Azul',
  '#6610f2': 'Violeta',
  '#d63384': 'Rosa',
  '#6c757d': 'Gris',
};

String categoryColorName(String hex) => categoryColorNames[hex] ?? hex;
