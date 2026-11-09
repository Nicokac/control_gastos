package app.controlgastos

import android.app.NotificationChannel
import android.app.NotificationManager
import android.os.Build
import android.os.Bundle
import io.flutter.embedding.android.FlutterActivity

class MainActivity : FlutterActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        createChannel(
            R.string.recurring_reminders_channel_id,
            R.string.recurring_reminders_channel_name,
            R.string.recurring_reminders_channel_description,
        )
        createChannel(
            R.string.spending_alerts_channel_id,
            R.string.spending_alerts_channel_name,
            R.string.spending_alerts_channel_description,
        )
    }

    // Recordatorios es el canal por defecto de FCM (ver AndroidManifest); las alertas de
    // gastos llegan con su canal desde el backend. Crearlos es idempotente: si ya existen,
    // Android conserva lo que el usuario haya configurado y solo actualiza nombre y descripción.
    private fun createChannel(idRes: Int, nameRes: Int, descriptionRes: Int) {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.O) return
        val channel = NotificationChannel(
            getString(idRes),
            getString(nameRes),
            NotificationManager.IMPORTANCE_DEFAULT,
        ).apply {
            description = getString(descriptionRes)
        }
        getSystemService(NotificationManager::class.java).createNotificationChannel(channel)
    }
}
