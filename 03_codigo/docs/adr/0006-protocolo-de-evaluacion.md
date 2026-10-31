# ADR 0006 — Protocolo de evaluación y selección del modelo

- **Estado:** aceptada (2026-10-31)
- **Contexto:** hay 10, 4 y 4 días en train, valid y test, y un desbalance de unas 7,7:1 entre Bajo y Alto. Test solo puede influir en el informe, nunca en una decisión.
- **Decisión:**
  1. Cada modelo se ajusta **solo con train**. Las grillas pequeñas de `config.yaml` (LR: C ∈ {0,01; 0,1; 1; 10}; RF: 12 combinaciones; GB: 8 combinaciones) se puntúan con Macro F1 en **valid** (`reportes/busqueda_hiperparametros.json`).
  2. Desbalance: `class_weight="balanced"` en la regresión logística y el Random Forest. `GradientBoostingClassifier` no admite `class_weight`, así que recibe `sample_weight` balanceado al ajustar.
  3. La regresión logística usa *one-hot* de `turno`, `dia_semana` y `nivel_lag1_turno`, y escalado estándar del resto, con el preprocesamiento ajustado dentro del `Pipeline` solo con train.
  4. El **modelo vigente** es el de mayor Macro F1 en valid entre los modelos de ML (desde v1.1.0, tras la calibración del ADR 0007 y con validación dejando un día fuera). La persistencia es la referencia y no se elige, porque la priorización necesita probabilidades.
  5. Después de cerrar la selección, los cuatro modelos se evalúan **una vez** en test para la tabla de H1. El código calcula las métricas de test después de fijar `seleccionado`, y ninguna decisión las lee.
  6. No se reentrena con train+valid antes de la evaluación en test, para que la cifra de prueba corresponda exactamente al artefacto publicado y usado en la app.
  7. Por la alta varianza también se informan el Macro F1 por día y por turno, un IC 95 % bootstrap del Macro F1 global (remuestreo de días completos, 2 000 réplicas) y un IC por día (remuestreo de filas dentro del día).
  8. HE1 se evalúa con la importancia por permutación sobre valid, permutando cada **grupo** completo (historial, espacial, calendario, contexto; 20 repeticiones) y también cada variable.
  9. Semillas fijas (42) y Random Forest con `n_jobs=1`, para que las probabilidades sean idénticas bit a bit entre corridas (test de reproducibilidad).
- **Consecuencias:** test se toca una sola vez por configuración. Repetir `todo` con el mismo dato y la misma config recalcula exactamente las mismas cifras sin cambiar ninguna decisión.
