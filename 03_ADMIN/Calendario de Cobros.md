---
tipo: calendario
tags:
  - dashboard
  - calendario
  - cobranzas
---

# 📅 Calendario de Cobros y Seguimiento

> Este calendario muestra automáticamente:
> 🚨 **Cobros pendientes** — trabajos terminados sin cobrar
> ⏳ **Seguimiento de presupuestos** — para hacer follow-up
> 🔥 **Trabajos en curso** — con fechas de avance
> ✅ **Cobros realizados** — histórico

---

## 🚨 Cobros Vencidos (urgentes)

```dataview
TABLE cliente AS "Cliente", mano_de_obra AS "Monto", fecha AS "Fecha Trabajo", dirección AS "Dirección", round(date(today) - date(fecha)) AS "Días"
FROM "01_TRABAJOS"
WHERE estado = "🛠️ Terminado" AND (pagado = false OR pagado = "false")
SORT date(fecha) ASC
```

---

## ⏳ Presupuestos para hacer Seguimiento

```dataview
TABLE cliente AS "Cliente", fecha AS "Fecha Presupuesto", dirección AS "Dirección", mano_de_obra AS "Presupuesto", round(date(today) - date(fecha)) AS "Días sin respuesta"
FROM "01_TRABAJOS"
WHERE estado = "🛠️ Presupuesto" OR state = "🛠️ Presupuesto"
SORT date(fecha) DESC
```

---

## 🔥 Trabajos en Curso

```dataview
TABLE cliente AS "Cliente", prioridad AS "Prioridad", fecha AS "Inicio", dirección AS "Dirección", mano_de_obra AS "Presupuesto"
FROM "01_TRABAJOS"
WHERE estado = "🛠️ En curso"
SORT date(fecha) ASC
```

---

## 💰 Resumen Financiero Rápido

```dataviewjs
const todos = dv.pages('"01_TRABAJOS"');

// Deudas
const deudas = todos.filter(p => 
    p.estado && p.estado.includes('Terminado') && 
    (p.pagado === false || p.pagado === "false")
);
const totalDeuda = deudas.length > 0 ? deudas.mano_de_obra.array().reduce((a, b) => a + b, 0) : 0;

// Este mes
const mesActual = new Date().toISOString().substring(0, 7);
const cobrosMes = todos.filter(p => 
    (p.pagado === true || p.pagado === "true") && 
    p.fecha && String(p.fecha).includes(mesActual)
);
const totalMes = cobrosMes.length > 0 ? cobrosMes.mano_de_obra.array().reduce((a, b) => a + b, 0) : 0;

// Mes anterior
const mesAnt = new Date();
mesAnt.setMonth(mesAnt.getMonth() - 1);
const mesAntStr = mesAnt.toISOString().substring(0, 7);
const cobrosMesAnt = todos.filter(p => 
    (p.pagado === true || p.pagado === "true") && 
    p.fecha && String(p.fecha).includes(mesAntStr)
);
const totalMesAnt = cobrosMesAnt.length > 0 ? cobrosMesAnt.mano_de_obra.array().reduce((a, b) => a + b, 0) : 0;

dv.table(
    ["Concepto", "Monto"],
    [
        ["🚨 Total en la calle", `$${totalDeuda.toLocaleString()}`],
        ["✅ Cobrado este mes", `$${totalMes.toLocaleString()}`],
        ["✅ Cobrado mes anterior", `$${totalMesAnt.toLocaleString()}`],
    ]
);
```

---

## 📋 Mensajes de Seguimiento (copiar/pegar para WhatsApp)

### Para deudas

```dataview
LIST "Hola " + cliente + ", te escribo por el trabajo del " + fecha + " (" + link(file.link) + ") — Monto: $" + mano_de_obra
FROM "01_TRABAJOS"
WHERE estado = "🛠️ Terminado" AND (pagado = false OR pagado = "false")
```

### Para presupuestos pendientes

```dataview
LIST "Hola " + cliente + ", ¿pudiste revisar el presupuesto? (" + link(file.link) + ")"
FROM "01_TRABAJOS"
WHERE estado = "🛠️ Presupuesto"
```

---

## 📅 Para Full Calendar Plugin

> **Cómo usar:**
> 1. Instalá el plugin **Full Calendar** si no lo tenés
> 2. Creás un calendario nuevo
> 3. Configurás que use Dataview queries o tareas con fechas
> 4. Podés arrastrar eventos en el calendario y se actualizan solos

### Eventos para agregar manualmente:
- Cuando un trabajo se **termina y no pagaron**, agregás un evento en 7 días: "Seguir cobro a [cliente]"
- Cuando mandás un **presupuesto**, agregás un evento en 3 días: "Follow-up presupuesto [cliente]"
- Cada **trabajo en curso**, evento con fecha de próximo avance

### Script automático de sincronización

Para que los cobros pendientes se creen automáticamente como eventos en Full Calendar, podés usar este script en tu rutina:

~~~dataviewjs
// Este dataview genera una lista de tareas con fechas para Full Calendar
// Las tareas con fecha se muestran automáticamente en el calendario

const deudas = dv.pages('"01_TRABAJOS"').filter(p => 
    p.estado && p.estado.includes('Terminado') && 
    (p.pagado === false || p.pagado === "false")
);

if (deudas.length > 0) {
    dv.header(3, "📅 Tareas de Cobro (agregá estas a tu calendario)");
    for (let d of deudas) {
        const fechaCobro = d.fecha ? new Date(d.fecha) : new Date();
        fechaCobro.setDate(fechaCobro.getDate() + 7);
        const fechaStr = fechaCobro.toISOString().split('T')[0];
        dv.paragraph(`- [ ] 🔴 Cobrar a [[${d.cliente}]] — $${(d.mano_de_obra || 0).toLocaleString()} — 📅 ${fechaStr}`);
    }
}

const presupuestos = dv.pages('"01_TRABAJOS"').filter(p => 
    p.estado && (p.estado.includes('Presupuesto'))
);

if (presupuestos.length > 0) {
    dv.header(3, "📅 Tareas de Seguimiento de Presupuestos");
    for (let p of presupuestos) {
        const fechaSeg = p.fecha ? new Date(p.fecha) : new Date();
        fechaSeg.setDate(fechaSeg.getDate() + 3);
        const fechaStr = fechaSeg.toISOString().split('T')[0];
        dv.paragraph(`- [ ] ⏳ Follow-up presupuesto [[${p.cliente}]] — 📅 ${fechaStr}`);
    }
}
~~~

---

*Actualizado: <% tp.date.now("DD/MM/YYYY HH:mm") %>*
