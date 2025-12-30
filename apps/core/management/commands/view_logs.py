"""
Comando para ver logs de la aplicación.
Uso: python manage.py view_logs [--type TYPE] [--lines N] [--follow]
"""

import time

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Ver logs de la aplicación"

    def add_arguments(self, parser):
        parser.add_argument(
            "--type",
            type=str,
            default="all",
            choices=["all", "app", "error", "security"],
            help="Tipo de log a mostrar (default: all)",
        )
        parser.add_argument(
            "--lines",
            type=int,
            default=50,
            help="Número de líneas a mostrar (default: 50)",
        )
        parser.add_argument(
            "--follow",
            "-f",
            action="store_true",
            help="Seguir el log en tiempo real (como tail -f)",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Limpiar los archivos de log",
        )

    def handle(self, *args, **options):
        logs_dir = settings.BASE_DIR / "logs"

        log_files = {
            "app": logs_dir / "app.log",
            "error": logs_dir / "error.log",
            "security": logs_dir / "security.log",
        }

        # Limpiar logs
        if options["clear"]:
            self._clear_logs(log_files)
            return

        # Seleccionar archivos a mostrar
        if options["type"] == "all":
            files_to_show = log_files
        else:
            files_to_show = {options["type"]: log_files[options["type"]]}

        # Seguir logs en tiempo real
        if options["follow"]:
            self._follow_logs(files_to_show)
        else:
            self._show_logs(files_to_show, options["lines"])

    def _show_logs(self, log_files: dict, num_lines: int):
        """Muestra las últimas N líneas de los logs."""
        for log_type, log_path in log_files.items():
            self.stdout.write("")
            self.stdout.write("=" * 60)
            self.stdout.write(self.style.SUCCESS(f"📄 {log_type.upper()} LOG: {log_path}"))
            self.stdout.write("=" * 60)

            if not log_path.exists():
                self.stdout.write(self.style.WARNING("   (archivo no existe)"))
                continue

            try:
                with open(log_path, encoding="utf-8") as f:
                    lines = f.readlines()
                    last_lines = lines[-num_lines:] if len(lines) > num_lines else lines

                    if not last_lines:
                        self.stdout.write(self.style.WARNING("   (archivo vacío)"))
                    else:
                        for line in last_lines:
                            self._format_line(line.strip())
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"   Error leyendo archivo: {e}"))

    def _follow_logs(self, log_files: dict):
        """Sigue los logs en tiempo real."""
        self.stdout.write(self.style.SUCCESS("Siguiendo logs... (Ctrl+C para salir)"))
        self.stdout.write("")

        # Abrir todos los archivos y posicionarse al final
        file_handles = {}
        for log_type, log_path in log_files.items():
            if log_path.exists():
                f = open(log_path, encoding="utf-8")
                f.seek(0, 2)  # Ir al final
                file_handles[log_type] = f

        try:
            while True:
                for log_type, f in file_handles.items():
                    line = f.readline()
                    if line:
                        prefix = self.style.HTTP_INFO(f"[{log_type.upper()}]")
                        self._format_line(line.strip(), prefix)
                time.sleep(0.1)
        except KeyboardInterrupt:
            self.stdout.write("")
            self.stdout.write(self.style.SUCCESS("Detenido."))
        finally:
            for f in file_handles.values():
                f.close()

    def _format_line(self, line: str, prefix: str = ""):
        """Formatea una línea de log con colores."""
        if not line:
            return

        # Colorear según nivel
        if "ERROR" in line or "CRITICAL" in line:
            style = self.style.ERROR
        elif "WARNING" in line or "LOCKOUT" in line:
            style = self.style.WARNING
        elif "SUCCESS" in line or "LOGIN SUCCESS" in line:
            style = self.style.SUCCESS
        else:
            style = lambda x: x

        if prefix:
            self.stdout.write(f"{prefix} {style(line)}")
        else:
            self.stdout.write(f"   {style(line)}")

    def _clear_logs(self, log_files: dict):
        """Limpia todos los archivos de log."""
        self.stdout.write("Limpiando logs...")

        for log_type, log_path in log_files.items():
            if log_path.exists():
                try:
                    open(log_path, "w").close()
                    self.stdout.write(self.style.SUCCESS(f"   ✅ {log_type}.log limpiado"))
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"   ❌ Error limpiando {log_type}.log: {e}")
                    )
            else:
                self.stdout.write(self.style.WARNING(f"   ⚠️  {log_type}.log no existe"))
