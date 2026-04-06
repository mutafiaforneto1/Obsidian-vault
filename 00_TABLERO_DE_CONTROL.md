---
tipo: tablero
---

# 📊 Tablero de Control

## 🚨 Trabajos Pendientes y en Curso

```dataview
TABLE cliente AS "Cliente", dirección AS "Dirección", prioridad AS "Prioridad", estado AS "Estado"
FROM "01_TRABAJOS"
WHERE estado != "🛠️ Terminado"
SORT estado ASC, prioridad ASC
```

---

## 📈 Estadísticas Rápidas

| Métrica | Valor |
|---------|-------|
| Total Trabajos | `=length(list_from("01_TRABAJOS"))` |
| Clientes | `=length(list_from("02_CLIENTES"))` |

---

## 🔗 Accesos Rápidos

- [[Dashboard Financiero]] - Resumen de ingresos y deudas
- [[Reporte Deudas]] - Clientes con saldos pendientes
- [[Historial de Trabajos]] - Registro completo de trabajos
- [[Control de cobros]] - Seguimiento de cobranzas
