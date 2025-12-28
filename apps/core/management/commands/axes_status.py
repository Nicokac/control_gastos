"""
Comando para ver estado de bloqueos de django-axes.
Uso: python manage.py axes_status
"""

from django.core.management.base import BaseCommand
from axes.models import AccessAttempt, AccessLog, AccessFailureLog


class Command(BaseCommand):
    help = 'Muestra el estado actual de bloqueos de django-axes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--failures',
            action='store_true',
            help='Mostrar intentos fallidos recientes',
        )
        parser.add_argument(
            '--blocked',
            action='store_true',
            help='Mostrar solo IPs/usuarios bloqueados',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Limpiar todos los registros de axes',
        )
        parser.add_argument(
            '--unlock-ip',
            type=str,
            help='Desbloquear una IP específica',
        )
        parser.add_argument(
            '--unlock-user',
            type=str,
            help='Desbloquear un usuario específico',
        )

    def handle(self, *args, **options):
        self.stdout.write("=" * 60)
        self.stdout.write("🔒 Estado de Django-Axes - Rate Limiting")
        self.stdout.write("=" * 60)
        self.stdout.write("")
        
        # Limpiar registros
        if options['clear']:
            self._clear_all()
            return
        
        # Desbloquear IP
        if options['unlock_ip']:
            self._unlock_ip(options['unlock_ip'])
            return
        
        # Desbloquear usuario
        if options['unlock_user']:
            self._unlock_user(options['unlock_user'])
            return
        
        # Mostrar estadísticas
        self._show_stats()
        
        # Mostrar intentos fallidos
        if options['failures']:
            self._show_failures()
        
        # Mostrar bloqueados
        if options['blocked']:
            self._show_blocked()

    def _show_stats(self):
        """Muestra estadísticas generales."""
        from axes.helpers import get_lockout_parameters
        from django.conf import settings
        
        attempts_count = AccessAttempt.objects.count()
        
        self.stdout.write(f"📊 Configuración:")
        self.stdout.write(f"   • Intentos antes de bloqueo: {settings.AXES_FAILURE_LIMIT}")
        self.stdout.write(f"   • Tiempo de bloqueo: {settings.AXES_COOLOFF_TIME} hora(s)")
        self.stdout.write(f"   • Parámetros de bloqueo: {settings.AXES_LOCKOUT_PARAMETERS}")
        self.stdout.write("")
        self.stdout.write(f"📈 Estadísticas:")
        self.stdout.write(f"   • Total de intentos registrados: {attempts_count}")
        
        # Contar bloqueados actuales
        from axes.helpers import is_already_locked
        blocked_count = AccessAttempt.objects.filter(
            failures_since_start__gte=settings.AXES_FAILURE_LIMIT
        ).count()
        
        self.stdout.write(f"   • IPs/usuarios actualmente bloqueados: {blocked_count}")
        self.stdout.write("")

    def _show_failures(self):
        """Muestra intentos fallidos recientes."""
        self.stdout.write("❌ Intentos fallidos recientes:")
        
        attempts = AccessAttempt.objects.order_by('-attempt_time')[:10]
        
        if not attempts:
            self.stdout.write("   No hay intentos fallidos registrados")
            return
        
        for attempt in attempts:
            status = "🔴 BLOQUEADO" if attempt.failures_since_start >= 5 else "🟡"
            self.stdout.write(
                f"   {status} IP: {attempt.ip_address} | "
                f"Usuario: {attempt.username or 'N/A'} | "
                f"Intentos: {attempt.failures_since_start} | "
                f"Último: {attempt.attempt_time.strftime('%Y-%m-%d %H:%M')}"
            )
        self.stdout.write("")

    def _show_blocked(self):
        """Muestra IPs/usuarios bloqueados."""
        from django.conf import settings
        
        self.stdout.write("🚫 IPs/Usuarios bloqueados:")
        
        blocked = AccessAttempt.objects.filter(
            failures_since_start__gte=settings.AXES_FAILURE_LIMIT
        )
        
        if not blocked:
            self.stdout.write("   No hay bloqueos activos")
            return
        
        for attempt in blocked:
            self.stdout.write(
                f"   🔴 IP: {attempt.ip_address} | "
                f"Usuario: {attempt.username or 'N/A'} | "
                f"Intentos: {attempt.failures_since_start}"
            )
        self.stdout.write("")

    def _clear_all(self):
        """Limpia todos los registros."""
        from axes.utils import reset
        
        reset()
        self.stdout.write(
            self.style.SUCCESS("✅ Todos los registros de axes han sido eliminados")
        )

    def _unlock_ip(self, ip):
        """Desbloquea una IP específica."""
        from axes.utils import reset
        
        deleted = AccessAttempt.objects.filter(ip_address=ip).delete()
        
        if deleted[0] > 0:
            self.stdout.write(
                self.style.SUCCESS(f"✅ IP {ip} desbloqueada ({deleted[0]} registros eliminados)")
            )
        else:
            self.stdout.write(
                self.style.WARNING(f"⚠️  IP {ip} no tenía bloqueos registrados")
            )

    def _unlock_user(self, username):
        """Desbloquea un usuario específico."""
        deleted = AccessAttempt.objects.filter(username=username).delete()
        
        if deleted[0] > 0:
            self.stdout.write(
                self.style.SUCCESS(f"✅ Usuario {username} desbloqueado ({deleted[0]} registros eliminados)")
            )
        else:
            self.stdout.write(
                self.style.WARNING(f"⚠️  Usuario {username} no tenía bloqueos registrados")
            )