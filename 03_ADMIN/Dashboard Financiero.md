---
tipo: dashboard
fecha_actualizacion: 2026-04-06
---

# 💰 Dashboard Financiero

## 📊 Resumen General

```dataviewjs
const trabajos = dv.pages('"01_TRABAJOS"').where(p => p.mano_de_obra);

// Total ganado
const totalCobrado = trabajos.where(p => p.pagado === true || p.pagado === "true");
const sumaCobrado = totalCobrado.length > 0 ? totalCobrado.mano_de_obra.array().reduce((a, b) => a + b, 0) : 0;

// Total pendiente
const totalPendiente = trabajos.where(p => p.pagado === false || p.pagado === "false");
const sumaPendiente = totalPendiente.length > 0 ? totalPendiente.mano_de_obra.array().reduce((a, b) => a + b, 0) : 0;

// En curso
const enCurso = dv.pages('"01_TRABAJOS"').where(p => p.estado && p.estado.includes("En curso"));
const sumaEnCurso = enCurso.filter(p => p.mano_de_obra).length > 0 ? enCurso.where(p => p.mano_de_obra).mano_de_obra.array().reduce((a, b) => a + b, 0) : 0;

dv.header(2, "💵 Total Cobrado: $" + sumaCobrado.toLocaleString());
dv.header(2, "⏳ Por Cobrar: $" + sumaPendiente.toLocaleString());
dv.header(2, "🛠️ En Curso (estimado): $" + sumaEnCurso.toLocaleString());
dv.paragraph("---");
dv.paragraph("**📈 Total Histórico:** $" + (sumaCobrado + sumaPendiente).toLocaleString());
```

---

## 🚨 Clientes con Deudas

```dataview
TABLE cliente AS "Cliente", mano_de_obra AS "Monto Adeudado", fecha AS "Fecha Trabajo", dirección AS "Dirección"
FROM "01_TRABAJOS"
WHERE estado = "🛠️ Terminado" AND (pagado = false OR pagado = "false")
SORT mano_de_obra DESC
```

### 📋 Resumen de Deudas

```dataviewjs
const deudas = dv.pages('"01_TRABAJOS"')
    .where(p => p.mano_de_obra && p.estado && p.estado.includes("Terminado") && (p.pagado === false || p.pagado === "false"));

const totalDeuda = deudas.length > 0 ? deudas.mano_de_obra.array().reduce((a, b) => a + b, 0) : 0;
const cantidadClientes = [...new Set(deudas.cliente.array())].length;

dv.header(3, "💸 Total a Cobrar: $" + totalDeuda.toLocaleString());
dv.paragraph("👥 Clientes con deuda: " + cantidadClientes);
```

---

## ✅ Trabajos Cobrados (Histórico)

```dataview
TABLE cliente AS "Cliente", mano_de_obra AS "Monto Cobrado", fecha AS "Fecha Cobro"
FROM "01_TRABAJOS"
WHERE estado = "🛠️ Terminado" AND (pagado = true OR pagado = "true")
SORT fecha DESC
```

---

## 🛠️ Trabajos en Curso

```dataview
TABLE cliente AS "Cliente", prioridad AS "Prioridad", fecha AS "Fecha Inicio", mano_de_obra AS "Presupuesto"
FROM "01_TRABAJOS"
WHERE estado = "🛠️ En curso"
SORT fecha ASC
```

---

## 📝 Presupuestos Pendientes

```dataview
TABLE cliente AS "Cliente", dirección AS "Dirección", fecha AS "Fecha Presupuesto", mano_de_obra AS "Presupuesto"
FROM "01_TRABAJOS"
WHERE estado = "🛠️ Presupuesto"
SORT fecha DESC
```

---

## 📅 Próximas Acciones

```dataview
TABLE estado AS "Estado", cliente AS "Cliente", dirección AS "Dirección"
FROM "01_TRABAJOS"
WHERE estado = "🛠️ Pendiente" OR estado = "🛠️ En curso"
SORT prioridad ASC
```
