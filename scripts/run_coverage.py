"""
Script para ejecutar tests con coverage y generar reportes.
Uso: python scripts/run_coverage.py [--html] [--xml] [--fail-under N]
"""

import argparse
import subprocess
import sys
import webbrowser
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description='Ejecutar tests con coverage')
    parser.add_argument(
        '--html',
        action='store_true',
        help='Generar reporte HTML y abrirlo en navegador'
    )
    parser.add_argument(
        '--xml',
        action='store_true',
        help='Generar reporte XML (para CI/CD)'
    )
    parser.add_argument(
        '--fail-under',
        type=int,
        default=80,
        help='Umbral mínimo de cobertura (default: 80)'
    )
    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Mostrar output detallado'
    )
    parser.add_argument(
        'pytest_args',
        nargs='*',
        help='Argumentos adicionales para pytest'
    )
    
    args = parser.parse_args()
    
    # Construir comando
    cmd = [
        'pytest',
        '--cov=apps',
        '--cov-report=term-missing',
        f'--cov-fail-under={args.fail_under}',
    ]
    
    if args.html:
        cmd.append('--cov-report=html')
    
    if args.xml:
        cmd.append('--cov-report=xml')
    
    if args.verbose:
        cmd.append('-v')
    
    # Agregar argumentos adicionales
    cmd.extend(args.pytest_args)
    
    print("=" * 60)
    print("🧪 Ejecutando tests con coverage")
    print("=" * 60)
    print(f"Comando: {' '.join(cmd)}")
    print()
    
    # Ejecutar
    result = subprocess.run(cmd)
    
    # Abrir reporte HTML si se generó
    if args.html and result.returncode == 0:
        htmlcov_path = Path('htmlcov/index.html')
        if htmlcov_path.exists():
            print()
            print("=" * 60)
            print("📊 Abriendo reporte HTML en navegador...")
            print("=" * 60)
            webbrowser.open(f'file://{htmlcov_path.absolute()}')
    
    # Resumen
    print()
    print("=" * 60)
    if result.returncode == 0:
        print("✅ Tests completados exitosamente")
        print(f"   Cobertura mínima requerida: {args.fail_under}%")
    else:
        print("❌ Tests fallaron o cobertura insuficiente")
        print(f"   Cobertura mínima requerida: {args.fail_under}%")
    print("=" * 60)
    
    sys.exit(result.returncode)


if __name__ == '__main__':
    main()