package app.controlgastos

import android.app.NotificationChannel
import android.app.NotificationManager
import android.os.Build
import android.os.Bundle
import io.flutter.embedding.android.FlutterActivity

class MainActivity : FlutterActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        createRecurringRemindersChannel()
    }

    // FCM usa este canal por defecto (ver AndroidManifest). Crearlo es idempotente:
    // si ya existe, Android conserva lo que el usuario haya configurado.
    private fun createRecurringRemindersChannel() {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.O) return
        val channel = NotificationChannel(
            getString(R.string.recurring_reminders_channel_id),
            getString(R.string.recurring_reminders_channel_name),
            NotificationManager.IMPORTANCE_DEFAULT,
        ).apply {
            description = getString(R.string.recurring_reminders_channel_description)
        }
        getSystemService(NotificationManager::class.java).createNotificationChannel(channel)
    }
}
