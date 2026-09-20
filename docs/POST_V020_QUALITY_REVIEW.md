# Backlog post-v0.2.0 — Calidad, revisión humana y observabilidad

Este documento conserva hallazgos y decisiones provisionales obtenidos durante
pruebas reales posteriores a la implementación de v0.2.0. No forman parte del
alcance de la release v0.2.0 mientras su validación esté en curso.

Deben revisarse formalmente antes de abrir la siguiente versión.

## 1. Observabilidad y progreso

### Hallazgo

Durante una transcripción real, la CLI puede permanecer varios minutos sin
indicar claramente si está descargando el modelo, cargándolo o transcribiendo.

### Dirección acordada

La próxima versión debe mostrar estados explícitos en CLI y GUI:

- descargando modelo;
- cargando modelo;
- preparando/abriendo audio;
- transcribiendo;
- generando TXT/JSON/SRT/VTT;
- completado;
- tiempo transcurrido;
- en modo carpeta, archivo N/total.

Nunca se mostrará un porcentaje inventado. Si una etapa no expone progreso real,
se usará un estado indeterminado/spinner más tiempo transcurrido.

## 2. Caché de Hugging Face en Windows y clasificación de errores

### Hallazgo real

Una ejecución `device=auto` cayó a CPU con un mensaje que indicaba que CUDA no
había podido inicializarse. El detalle real era `WinError 1314` al intentar
crear un symlink dentro del caché de Hugging Face.

Una ejecución posterior con `HF_HUB_DISABLE_SYMLINKS=1`,
`device=cuda` y `compute_type=float16` completó correctamente sobre GPU y
generó TXT/JSON/SRT/VTT.

### Conclusiones

- CUDA/float16 funciona en el equipo objetivo con un MP4 real.
- El error de symlink/caché no debe clasificarse automáticamente como fallo CUDA.
- El manejo de excepciones actual alrededor de la creación del modelo es demasiado
  amplio para producir diagnósticos precisos.

### Dirección acordada

Separar diagnóstico por origen:

- descarga/caché del modelo;
- permisos/symlinks del caché;
- carga del modelo;
- runtime CUDA/cuDNN/cuBLAS;
- inferencia/transcripción;
- escritura de outputs.

Evaluar una política explícita de caché sin symlinks en Windows cuando sea
necesario, sin requerir privilegios de administrador.

## 3. Calidad: Turbo frente a large-v3

### Prueba real

Se compararon tres configuraciones sobre la misma llamada:

1. `large-v3-turbo + VAD`;
2. `large-v3 + VAD`;
3. `large-v3 + --no-vad`.

### Resultado observado

- `large-v3-turbo + VAD` produjo una transcripción global casi perfecta, pero
  falló en un fragmento de habla baja/enredada.
- `large-v3 + VAD` corrigió ese fragmento difícil, pero introdujo errores en
  otras partes que Turbo había transcrito correctamente.
- `large-v3 + --no-vad` empeoró el resultado general en esta llamada.

### Conclusiones provisionales

- No sustituir globalmente `large-v3-turbo` por `large-v3`.
- Mantener VAD activado como comportamiento predeterminado.
- No tratar `--no-vad` como mejora general de calidad.
- Usar `large-v3` como segunda opinión para segmentos dudosos, no necesariamente
  como transcriptor principal.

Estas conclusiones provienen de una prueba real concreta y deben validarse sobre
más llamadas antes de convertirse en reglas universales.

## 4. Estrategia híbrida de transcripción

### Dirección propuesta

Usar `large-v3-turbo + VAD` como primera pasada y detectar segmentos con
evidencia de baja confianza o discrepancia.

Sólo esos segmentos se volverían a procesar con `large-v3 + VAD`.

Flujo previsto:

```text
MP4
 |
 v
large-v3-turbo + VAD
 |
 +-- segmento normal -----------------> conservar
 |
 +-- segmento sospechoso
        |
        v
    large-v3 + VAD
        |
        v
 comparar resultados
        |
        +-- concordancia suficiente ---> conservar
        |
        +-- discrepancia relevante ----> marcar REVISAR
```

La segunda pasada debe ser selectiva cuando sea técnicamente viable para evitar
reprocesar la llamada completa y reducir tiempo de GPU.

## 5. Señales de confianza

Investigar y conservar métricas disponibles en faster-whisper/Whisper que puedan
ayudar a identificar segmentos dudosos, por ejemplo:

- `avg_logprob`;
- `no_speech_prob`;
- `compression_ratio`;
- probabilidad por palabra cuando esté disponible;
- discrepancia textual entre Turbo y large-v3.

Estas señales no deben presentarse como una probabilidad calibrada de que el
texto sea correcto. Se usarán para priorizar revisión humana.

También debe evaluarse `condition_on_previous_text=False` en casos de
repetición/hallucination loops, sin convertirlo en default sin benchmark.

## 6. Reproductor y revisión humana

### Objetivo

Permitir que un revisor compruebe visual y auditivamente que la transcripción
coincide con la llamada original.

### Requisitos previstos

- reproductor del audio/video original dentro de la GUI;
- play/pause;
- seek/timeline;
- salto directo al timestamp del segmento seleccionado;
- visualización de texto por segmento;
- resaltado del segmento actualmente reproducido;
- marcas `REVISAR` para segmentos dudosos;
- mostrar, cuando exista, alternativa Turbo frente a large-v3;
- edición manual del texto revisado;
- conservar trazabilidad entre texto automático y corrección humana.

No se extraerá ni duplicará audio persistentemente si Qt puede reproducir
directamente el MP4 original de forma fiable.

## 7. Hotwords y contexto

Evaluar soporte opcional de `hotwords` o `initial_prompt` para nombres propios,
empresas y terminología de dominio.

Debe ser opcional y explícito: el contexto puede mejorar nombres conocidos pero
también sesgar la transcripción.

## 8. Prioridad propuesta para la siguiente versión

Orden sugerido para revisión:

1. progreso/observabilidad;
2. clasificación correcta de errores y caché Windows;
3. reproductor sincronizado + revisión humana;
4. persistencia de señales de confianza;
5. detección automática de segmentos dudosos;
6. segunda pasada selectiva con large-v3;
7. hotwords/contexto;
8. evaluación de `condition_on_previous_text`.

La arquitectura y criterios definitivos deben aprobarse al abrir formalmente la
siguiente versión. Este documento no modifica por sí solo los defaults ni el
contrato de v0.2.0.
