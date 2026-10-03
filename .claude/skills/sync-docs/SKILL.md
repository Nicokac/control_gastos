---
name: sync-docs
description: Sincroniza la documentación interna de Control de Gastos (docs/DECISIONS.md con entradas DT-XXX, CHANGELOG.md, docs/FLUTTER_ROADMAP.md, y el versionado desacoplado web/mobile) después de completar una tarea de desarrollo. Úsala cuando el usuario pida "sincronizar documentación", "actualizar docs", "documentar esto", "qué falta documentar", "cerrar la tarea", "preparar el commit de docs", o en general al terminar un fix/feature y antes de hacer commit — incluso si el usuario solo dice "listo, ¿qué sigue?" después de confirmar que el código funciona. También aplica cuando se detecta que algún documento quedó desactualizado respecto al código (por ejemplo, un bump de versión sin su changelog correspondiente).
---

# Sincronizar documentación — Control de Gastos

Este proyecto (Django web + Flutter mobile) mantiene 4 documentos vivos que deben
actualizarse juntos cada vez que se completa una tarea de desarrollo. Ningún
mecanismo externo los mantiene sincronizados — es un paso manual que se olvida
fácil (ya pasó: `docs/FLUTTER_ROADMAP.md` quedó 3 meses desactualizado sin que
nadie lo notara). Esta skill estructura ese paso para que no se salte.

No se dispara sola. Se usa cuando el usuario la pide explícitamente, al cerrar
una tarea, justo antes del commit.

## Los 4 documentos y cuándo tocar cada uno

| Documento | Se toca cuando... |
|---|---|
| `docs/DECISIONS.md` | Se resolvió, descartó o dejó pendiente un ítem de deuda técnica, o se tomó una decisión de diseño no obvia que valga la pena justificar para el futuro |
| `CHANGELOG.md` | Hay un cambio con impacto real (feature nueva, fix de bug, no refactors internos sin efecto visible) |
| `APP_VERSION` (`apps/core/views.py`) + `WHATS_NEW` (mismo archivo) | El cambio toca la web y amerita bump según el criterio de versionado |
| `mobile/pubspec.yaml` (`version: X.Y.Z+N`) | El cambio toca la app Flutter y amerita bump (build number) |
| `docs/FLUTTER_ROADMAP.md` | El cambio toca mobile — tiene su propia tabla de "Registro de progreso" que se queda atrás si no se actualiza en el momento |

No todos los cambios tocan los 5. Un fix de backend puro sin UI nueva puede no
necesitar `WHATS_NEW` (eso es para funcionalidad *visible*). Un cambio solo-web
nunca toca `pubspec.yaml` ni `FLUTTER_ROADMAP.md`. Usar criterio, no aplicar
los 5 por inercia.

## Paso 1 — Entender qué se hizo

Antes de tocar nada, reconstruí qué cambió en esta sesión/tarea:
- Si hay un resumen de la conversación o una lista de archivos modificados, usala
- Si no, corré `git diff` / `git status` para ver el estado real
- Identificá: ¿es web, mobile, o ambos? ¿es un fix, una feature nueva, o deuda
  técnica resuelta/descartada? ¿cambió algo visible para el usuario final, o es
  interno (refactor, test, config)?

Esta clasificación determina qué documentos tocar en los pasos siguientes.

## Paso 2 — `docs/DECISIONS.md` (si corresponde)

Este documento tiene dos formatos conviviendo: entradas viejas `## D-XXX` (más
narrativas: Contexto/Decisión/Justificación/Riesgo aceptado) y entradas
recientes `### DT-XXX` (más compactas: Estado/Why/Resolución). **Para entradas
nuevas, usar siempre el formato `DT-XXX`** — es el que se usa desde mediados de
2026 y el que mejor se presta a numeración incremental.

**Numerar automáticamente:** buscar el último `DT-XXX` en el archivo
(`grep -n "### DT-"` o similar) y usar el número siguiente. No preguntarle al
usuario el número — si hay ambigüedad por algún gap, usar el mayor + 1.

**Plantilla de una entrada nueva:**

```markdown
### DT-NNN — Título corto y descriptivo

**Estado:** ⏳ Pendiente | 🟡 En progreso | ✅ Resuelto (vX.Y.Z web · Mobile A.B.C+D) | 🚫 Descartado

[Descripción del problema o situación en 1-3 líneas, en presente si sigue
pendiente o en pasado si ya se resolvió.]

**Why:** [la motivación — por qué importa, qué dolor concreto resuelve o qué
decisión de producto/arquitectura hay detrás. Si hay un incidente o reporte de
usuario que lo originó, nombrarlo.]

**Resolución** (o **Camino de resolución** si sigue pendiente): [qué se hizo
técnicamente — archivos tocados, decisiones de diseño tomadas, alternativas
descartadas y por qué.]

**Riesgo aceptado** (opcional, solo si aplica): [qué limitación queda
consciente y por qué se acepta.]

---
```

**Cuándo usar cada Estado:**
- `✅ Resuelto` — ya se implementó y verificó (tests pasando). Incluir versión(es) real(es), no un placeholder — si todavía no se bumpeó la versión, hacer el Paso 4 primero.
- `🟡 En progreso` — se avanzó pero queda trabajo (ej: instalación hecha, falta la fase 2).
- `🚫 Descartado` — se investigó algo (un reporte de bug, una pregunta de diseño) y se concluyó
  que no había nada que hacer: no era un bug real, o se decidió conscientemente no implementar
  algo. **Esto va en la sub-serie `DTD-XXX`, no en `DT-XXX`** — ver el apartado "Deudas técnicas
  descartadas" más abajo, es una distinción real del documento, no cosmética.
- `⏳ Pendiente` — documentado pero sin empezar. Útil para dejar registrada una idea o un reporte antes de decidir atacarlo.

**El filtro más importante de este paso — no crear un `DT-XXX` por cada fix.**
`DECISIONS.md` registra *decisiones*, no es un changelog técnico (eso ya lo cubre
`CHANGELOG.md` y el historial de git). La pregunta que separa un DT real de un fix
normal: **si alguien lee el código corregido dentro de 6 meses sin este contexto,
¿la solución le va a parecer obvia, o se va a preguntar "por qué se hizo así y no
de otra forma"?**

- "Deshabilité el botón mientras la request está en curso para evitar doble submit"
  → obvio al leer el código, no hace falta DT. Esto solo va en `CHANGELOG.md`.
- "Elegimos agrupar los impuestos en una sola fila en vez de mostrarlos todos
  (DT-055 Fase 1)" → no es obvio por qué se agruparon, hay una decisión de UX
  detrás que alguien podría querer revertir sin este contexto. Sí amerita DT.
- Un reporte de bug que resultó no ser un bug (típicamente por investigación,
  no por una línea de código) → siempre amerita una entrada (`DTD-XXX`, ver abajo),
  aunque no haya "decisión de diseño" — el valor es documentar que ya se investigó,
  para que nadie vuelva a perder tiempo con la misma pregunta.

Ante la duda entre crear un DT o no, el costo de omitirlo es bajo (el `CHANGELOG.md`
y el código ya quedan documentados); el costo de crear uno de más es ruido que
diluye los DT que sí importan. Ante la duda, no crear.

### Sub-serie `DTD-XXX` — deudas técnicas descartadas

Dentro de `docs/DECISIONS.md` hay una sección `## D-015 — Deudas técnicas
descartadas` con su propia numeración (`DTD-001`, `DTD-002`, ...), separada de
la numeración `DT-XXX`. Es el lugar correcto para cualquier entrada con Estado
`🚫 Descartado` — buscar el último `DTD-XXX` ahí (no el último `DT-XXX` del
resto del documento) y usar el siguiente número. El formato de la entrada es
más corto que el de un DT normal:

```markdown
### DTD-NNN — Título corto

**Estado:** 🚫 Descartado

**Motivo:** [qué se investigó, qué se encontró (o no se encontró), y por qué
se concluyó que no hacía falta ningún cambio.]

---
```

## Paso 3 — `CHANGELOG.md`

Formato [Keep a Changelog](https://keepachangelog.com/es/1.0.0/) adaptado.
Mirar las últimas 2-3 entradas del archivo para calibrar tono y nivel de
detalle antes de escribir — varía si es una entrada solo-web, solo-mobile
(`## [Mobile X.Y.Z+N]`), o combinada (`## [X.Y.Z / Mobile A.B.C+D]`).

**Plantilla:**

```markdown
## [X.Y.Z / Mobile A.B.C+D] — YYYY-MM-DD

### Added

- **Título corto**: descripción de 1-3 líneas en lenguaje de changelog técnico
  (más detallado que WHATS_NEW, que es para el usuario final).

### Fixed

- **Título corto**: qué estaba roto, por qué, y qué se corrigió.

---
```

Usar `### Added` para funcionalidad nueva, `### Fixed` para bugs corregidos.
Si el cambio es solo mobile o solo web, el título de versión refleja eso
(`## [Mobile 1.16.0+10]` sin versión web si no hubo cambios ahí).

## Paso 4 — Bump de versión (requiere confirmación del usuario)

**Nunca aplicar un bump sin que el usuario lo confirme explícitamente.**
Proponer el número y esperar el OK antes de editar `APP_VERSION` o
`pubspec.yaml`.

**Criterio de versionado semántico (de CLAUDE.md del proyecto):**
- **PATCH** (x.x.+1): fix de bug, ajuste visual/UX menor, sin funcionalidad nueva.
- **MINOR** (x.+1.0): funcionalidad nueva visible (nueva sección, feature, flujo).
- **MAJOR** (+1.0.0): cambio de arquitectura o ruptura de compatibilidad. Raro.

**Web** (`apps/core/views.py`):
```python
APP_VERSION = "X.Y.Z"
```
Si el cambio es funcionalidad nueva visible, agregar también una entrada en
`WHATS_NEW` (mismo archivo, arriba de la lista) — lenguaje para el usuario
final, no técnico. Ejemplo real del estilo esperado:

```python
{
    "version": "1.22.0",
    "date": "Octubre 2026",
    "title": "Aviso de novedades al entrar",
    "items": [
        "Ahora te avisamos con un mensaje emergente cuando hay novedades nuevas",
        "Corregido: el color del botón de Cafecito en la app móvil no coincidía con el de la web",
    ],
},
```
**No** agregar entrada en `WHATS_NEW` si es solo un fix interno sin impacto
visible — mirar las últimas entradas reales del archivo para confirmar el
patrón (varios fixes de esta sesión no generaron entrada ahí a propósito).

**Mobile** (`mobile/pubspec.yaml`):
```yaml
version: X.Y.Z+N
```
El build number (`+N`) incrementa en cada build subido a Play Console, incluso
si `X.Y.Z` no cambia. **Importante:** si ya se compiló un AAB y se subió a Play
Console con un build number, ese número queda "usado" para siempre — Play
Console lo rechaza si se intenta resubir. Si el usuario va a compilar un AAB
nuevo después de este cambio, bumpear `+N` aunque `X.Y.Z` no cambie.

Si mobile también usa una constante de versión visible en la UI (ya pasó un
bug por esto — ver DT relacionado con "Acerca de" mostrando versión vieja),
verificar que no haya una constante hardcodeada desincronizada en
`mobile/lib/core/constants/api_constants.dart` (`appVersion`).

## Paso 5 — `docs/FLUTTER_ROADMAP.md` (solo si el cambio toca mobile)

Tiene una tabla "Registro de progreso" al final del archivo, formato:

```markdown
| YYYY-MM-DD | Fase | Descripción corta de qué se hizo |
```

Agregar una fila nueva al final de la tabla por cada cambio relevante de
mobile (bump de versión, feature nueva, fix). Usar la fase correspondiente del
roadmap si el cambio encaja en una (Fase 4 = Features, Fase 5 = Release, etc.)
o "Fix" si es una corrección puntual fuera del roadmap original.

También revisar la sección "Estado Actual" al principio del archivo — tiene
líneas tipo `✅ App Flutter publicada en Google Play Console (vX.Y.Z+N)` que
quedan obsoletas en cada bump y hay que actualizar a mano.

## Paso 6 — Resumen final

Antes de terminar, mostrar al usuario qué se tocó y qué se decidió dejar sin
tocar (y por qué) — igual que el resto de esta sesión, el usuario valora ver
el razonamiento, no solo el resultado. Si quedó algo pendiente de confirmación
(ej: el bump de versión), dejarlo explícito como próximo paso, no asumir que
ya se aplicó.

No correr `git commit` ni `git push` como parte de esta skill — eso lo pide el
usuario aparte, explícitamente, siguiendo las reglas de CLAUDE.md del proyecto.
