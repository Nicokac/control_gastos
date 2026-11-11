# Control de Gastos — App mobile

App Android en Flutter, cliente de la API REST del backend Django (`/api/v1/`). Publicada en Google Play como `app.controlgastos`.

- Arquitectura general y flujos (login, push): [`docs/ARQUITECTURA.md`](../docs/ARQUITECTURA.md)
- Roadmap y estado de publicación: [`docs/FLUTTER_ROADMAP.md`](../docs/FLUTTER_ROADMAP.md)
- Historial de versiones: [`CHANGELOG.md`](../CHANGELOG.md) (entradas `Mobile X.Y.Z+N`)

---

## Stack

| | |
|---|---|
| Flutter / Dart | 3.44 / 3.12 |
| Estado | Riverpod |
| HTTP | Dio, con renovación automática del JWT ante un 401 |
| Rutas | GoRouter |
| Almacenamiento | `flutter_secure_storage` (tokens), `shared_preferences` (caché y preferencias) |
| Push | `firebase_core` + `firebase_messaging` |
| Tests | `flutter_test` + `mockito` |

## Estructura

```text
lib/
├── main.dart, app.dart     # Arranque, Firebase, tema y router
├── core/                   # Constantes (api_constants.dart), tema, formatters, widgets comunes
├── data/
│   ├── repositories/       # Un repositorio por recurso de la API
│   └── services/           # ApiService, StorageService, CacheService, PushNotificationService
├── features/               # Una carpeta por sección: screens, providers y widgets
└── routing/                # Rutas (GoRouter)
test/
├── unit/                   # Providers y servicios (con mocks de mockito)
└── widget/                 # Pantallas y widgets
```

---

## Requisitos

- Flutter SDK 3.44 (`flutter doctor` sin errores en la parte de Android).
- Android Studio con un emulador (API 30 o superior) o un celular con depuración USB.
- Dos archivos que **no están en el repo** y hay que pedir o generar:

| Archivo | Para qué | Cómo se obtiene |
|---|---|---|
| `android/app/google-services.json` | Firebase (push). Sin él no compila | Consola de Firebase → proyecto → app Android `app.controlgastos` → descargar |
| `android/key.properties` | Firma del build de release, pero hoy lo exige **cualquier** build | Quien publica tiene el real (ver [Release](#release)); para desarrollo, uno propio con un keystore de prueba |

> **Sin `key.properties` no compila ni el build de debug.** `android/app/build.gradle.kts` arma la firma de release (`signingConfigs.create("release")`) al configurar el proyecto, sin importar qué build se pida, y convierte los valores del archivo con `as String`. Si el archivo no existe, esos valores son `null` y Gradle corta con `null cannot be cast to non-null type kotlin.String`.
>
> Para desarrollar sin la clave real, generar un keystore de prueba y apuntar a él:
>
> ```bash
> keytool -genkey -v -keystore ~/debug-upload.jks -alias debug -keyalg RSA -keysize 2048 -validity 10000
> ```
>
> y crear `android/key.properties` con el formato de la sección [Release](#release). Ese build no sirve para subir a Play Console, que exige la clave de subida real.

---

## Correr la app

```bash
cd mobile
flutter pub get
flutter run
```

Sin parámetros, la app habla con **producción**. Para usar el backend local, pasar la URL:

```bash
# Backend: desde la raíz del repo, escuchando en todas las interfaces
python manage.py runserver 0.0.0.0:8001

# App en el emulador (10.0.2.2 es la PC vista desde el emulador)
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8001/api/v1
```

- Con un celular físico, usar la IP de la PC en la red local en lugar de `10.0.2.2` y habilitar el puerto en el firewall de Windows.
- En Android Studio: *Run → Edit Configurations → Additional run args* → `--dart-define=API_BASE_URL=...`.
- Los usuarios del backend local viven en `db.sqlite3`; no son los de producción.
- Si se alterna entre local y producción, los tokens guardados no sirven para el otro entorno: cerrar sesión o reinstalar la app.

Hot reload: `r` en la terminal. Restart completo: `R` (necesario tras cambiar `AndroidManifest.xml`).

---

## Tests y análisis

```bash
flutter test                                   # todos
flutter test test/widget/login_screen_test.dart  # uno
flutter analyze
```

Los mocks (`*.mocks.dart`) se generan con mockito. Después de cambiar una clase mockeada (`@GenerateMocks`):

```bash
dart run build_runner build --delete-conflicting-outputs
```

Patrones usados en los tests de widgets:

- Montos ocultos: override de `amountsHiddenProvider` con una subclase de `AmountsVisibilityNotifier`.
- Tema: `ThemeData(extensions: const [AppSemanticColors.light])`, porque los widgets leen los colores semánticos del tema.
- Pantallas angostas y fuente grande: fijar `tester.view.physicalSize` y `MediaQueryData(textScaler: ...)` (ver `projection_banner_test.dart`).

---

## Release

1. **Versión** en `pubspec.yaml`: `version: X.Y.Z+N`. El número de build (`+N`) sube en cada subida a Play Console; uno ya subido no se puede reutilizar.
2. **Texto de novedades** dentro de la app: `latestReleaseSummary` en `lib/core/constants/api_constants.dart`.
3. **Documentación:** entrada `[Mobile X.Y.Z+N]` en `CHANGELOG.md` y fila en el registro de progreso de `docs/FLUTTER_ROADMAP.md`.
4. **Build** (apunta a producción por defecto; requiere `key.properties` y el keystore):

   ```bash
   flutter build appbundle --release
   ```

   Resultado: `build/app/outputs/bundle/release/app-release.aab`.
5. **Play Console:** subir a prueba interna, probar en un celular, promover a prueba cerrada y luego a producción.

`android/key.properties` (fuera del repo) tiene este formato:

```properties
storeFile=<ruta al keystore .jks>
storePassword=<...>
keyAlias=<...>
keyPassword=<...>
```

**El keystore y sus contraseñas no se pueden recuperar si se pierden:** Google Play exige firmar cada actualización con la misma clave de subida. Guardar una copia fuera de la PC.

---

## Problemas comunes

| Síntoma | Causa probable |
|---|---|
| La app no conecta al backend local | Django escuchando en `127.0.0.1` en vez de `0.0.0.0`, o URL sin `--dart-define` |
| El primer pedido tarda mucho contra producción | Render Free despierta el servicio (DT-106) |
| No llegan push en el emulador | El emulador necesita imagen con Google Play Services y permiso de notificaciones concedido |
| Cambios en el manifest no se aplican | Hace falta restart completo o reinstalar, no hot reload |
