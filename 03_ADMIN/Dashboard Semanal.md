---
tipo: dashboard
periodo: semanal
semana: "2026-W15"
fecha_creacion: 2026-04-06
fecha_inicio: 2026-04-06
fecha_fin: 2026-04-12
---

# 📅 Dashboard Semanal — Semana del 6 al 12 de Abril

## 🎯 Resumen de la Semana

```dataviewjs
const ahora = new Date();
const hoy = ahora.toISOString().split('T')[0];
const inicioSemana = new Date(ahora);
inicioSemana.setDate(ahora.getDate() - ahora.getDay() + 1);
const finSemana = new Date(inicioSemana);
finSemana.setDate(inicioSemana.getDate() + 6);

const inicioStr = inicioSemana.toISOString().split('T')[0];
const finStr = finSemana.toISOString().split('T')[0];

const todos = dv.pages('"01_TRABAJOS"');

// Trabajos de esta semana (por fecha o fecha_cierre)
const estaSemana = todos.filter(p => {
    if (!p.fecha && !p.fecha_cierre) return false;
    const f = p.fecha ? String(p.fecha).substring(0, 10) : '';
    const fc = p.fecha_cierre ? String(p.fecha_cierre).substring(0, 10) : '';
    return (f >= inicioStr && f <= finStr) || (fc >= inicioStr && fc <= finStr);
});

// Cobros de esta semana
const cobradosEstaSemana = estaSemana.filter(p => 
    p.pagado === true || p.pagado === "true"
);

const sumaCobradaSe = cobradosEstaSemana.length > 0 
    ? cobradosEstaSemana.mano_de_obra.array().reduce((a, b) => a + b, 0) 
    : 0;

const pendientesSemana = estaSemana.filter(p => 
    p.pagado === false || p.pagado === "false" || !p.pagado
);

const sumaPendienteSe = pendientesSemana.length > 0 
    ? pendientesSemana.mano_de_obra.array().reduce((a, b) => a + b, 0) 
    : 0;

// Totales globales
const todosPagados = todos.filter(p => p.pagado === true || p.pagado === "true");
const totalCobrado = todosPagados.length > 0 
    ? todosPagados.mano_de_obra.array().reduce((a, b) => a + b, 0) 
    : 0;

const todosDeudas = todos.filter(p => 
    p.estado && p.estado.includes('Terminado') && 
    (p.pagado === false || p.pagado === "false")
);
const totalDeuda = todosDeudas.length > 0 
    ? todosDeudas.mano_de_obra.array().reduce((a, b) => a + b, 0) 
    : 0;

dv.header(2, "📆 Rango");
dv.paragraph(`**${inicioStr}** → **${finStr}**`);
dv.paragraph("---");

dv.header(3, "💵 Cobrado esta semana");
dv.header(1, `$${sumaCobradaSe.toLocaleString()}`);
dv.paragraph(`${cobradosEstaSemana.length} trabajo(s) cobrado(s)`);

dv.paragraph("---");

dv.header(3, "⏳ Pendiente esta semana");
dv.header(2, `$${sumaPendienteSe.toLocaleString()}`);
dv.paragraph(`${pendientesSemana.length} pendiente(s)`);

dv.paragraph("===\n");

dv.header(3, "📈 Acumulado histórico cobrado");
dv.header(1, `$${totalCobrado.toLocaleString()}`);

dv.header(3, "🚨 Deuda total acumulada");
dv.header(2, `$${totalDeuda.toLocaleString()}`);
dv.paragraph(`${todosDeudas.length} cliente(s) con deuda`);
```

---

## 🔥 Trabajos en Curso

```dataview
TABLE cliente AS "Cliente", dirección AS "Dirección", prioridad AS "Prioridad", mano_de_obra AS "Presupuesto"
FROM "01_TRABAJOS"
WHERE estado = "🛠️ En curso"
SORT prioridad ASC
```

---

## 📝 Presupuestos Pendientes de Cerrar

```dataview
TABLE cliente AS "Cliente", dirección AS "Dirección", fecha AS "Fecha", mano_de_obra AS "Monto"
FROM "01_TRABAJOS"
WHERE estado = "🛠️ Presupuesto"
SORT fecha DESC
```

---

## 🚨 Cobranzas Urgentes

```dataview
TABLE cliente AS "Cliente", mano_de_obra AS "Monto", fecha AS "Fecha Trabajo", dirección AS "Dirección"
FROM "01_TRABAJOS"
WHERE estado = "🛠️ Terminado" AND (pagado = false OR pagado = "false")
SORT mano_de_obra DESC
```

### Deuda total

```dataviewjs
const todos = dv.pages('"01_TRABAJOS"');
const deudas = todos.filter(p => 
    p.estado && p.estado.includes('Terminado') && 
    (p.pagado === false || p.pagado === "false")
);
const total = deudas.length > 0 
    ? deudas.mano_de_obra.array().reduce((a, b) => a + b, 0) 
    : 0;
dv.header(2, `💸 $${total.toLocaleString()} en la calle`);
dv.paragraph(`${deudas.length} trabajo(s) sin cobrar`);
```

---

## 📋 Trabajos de la Semana

### Finalizados esta semana

```dataviewjs
const ahora = new Date();
const inicioSemana = new Date(ahora);
inicioSemana.setDate(ahora.getDate() - ahora.getDay() + 1);
const finSemana = new Date(inicioSemana);
finSemana.setDate(inicioSemana.getDate() + 6);
const inicioStr = inicioSemana.toISOString().split('T')[0];
const finStr = finSemana.toISOString().split('T')[0];

const terminados = dv.pages('"01_TRABAJOS"').filter(p => {
    if (!p.fecha_cierre && !p.fecha) return false;
    const f = p.fecha_cierre ? String(p.fecha_cierre).substring(0, 10) : String(p.fecha).substring(0, 10);
    const terminado = p.estado && p.estado.includes('Terminado');
    return f >= inicioStr && f <= finStr && terminado;
});

if (terminados.length > 0) {
    dv.table(["Cliente", "Dirección", "Monto", "Estado Pago"],
        terminados.map(p => [
            p.cliente || "Sin nombre",
            p.dirección || "N/A",
            `$${(p.mano_de_obra || 0).toLocaleString()}`,
            (p.pagado === true || p.pagado === "true") ? "✅ Cobrado" : "⏳ Pendiente"
        ])
    );
} else {
    dv.paragraph("_No hay trabajos finalizados registrados esta semana._");
}
```

---

## 💰 Comparativa Mensual

```dataviewjs
// Mes actual vs mes anterior
const ahora = new Date();
const mesActual = ahora.toISOString().substring(0, 7); // "2026-04"
const mesAnt = new Date(ahora.getFullYear(), ahora.getMonth() - 1, 1)
    .toISOString().substring(0, 7);

const todos = dv.pages('"01_TRABAJOS"');
const pagados = todos.filter(p => p.pagado === true || p.pagado === "true");

const mesAct = pagados.filter(p => {
    if (!p.fecha) return false;
    return String(p.fecha).includes(mesActual);
});

const mesAnt = pagados.filter(p => {
    if (!p.fecha) return false;
    return String(p.fecha).includes(mesAnt);
});

const totalMesAct = mesAct.length > 0 
    ? mesAct.mano_de_obra.array().reduce((a, b) => a + b, 0) 
    : 0;

const totalMesAnt = mesAnt.length > 0 
    ? mesAnt.mano_de_obra.array().reduce((a, b) => a + b, 0) 
    : 0;

// Mes con nombre en español
const nombresMes = {
    "01": "Enero", "02": "Febrero", "03": "Marzo", "04": "Abril",
    "05": "Mayo", "06": "Junio", "07": "Julio", "08": "Agosto",
    "09": "Septiembre", "10": "Octubre", "11": "Noviembre", "12": "Diciembre"
};

const mesActNom = nombresMes[mesActual.substring(5)] || mesActual.substring(5);
const mesAntNom = nombresMes[mesAnt.substring(5)] || mesAnt.substring(5);

dv.header(2, `📊 ${mesActNom} vs ${mesAntNom}`);
dv.paragraph(`**${mesActNom} (actual):** $${totalMesAct.toLocaleString()} (${mesAct.length} cobros)`);
dv.paragraph(`**${mesAntNom} (anterior):** $${totalMesAnt.toLocaleString()} (${mesAnt.length} cobros)`);

if (totalMesAnt > 0) {
    const diff = ((totalMesAct - totalMesAnt) / totalMesAnt * 100).toFixed(1);
    const emoji = diff >= 0 ? "📈" : "📉";
    dv.paragraph(`${emoji} **Diferencia:** ${diff}%`);
} else if (totalMesAct > 0) {
    dv.paragraph("🆕 Primer cobro registrado");
}
```

---

## 📌 Notas de la Semana

- _Agregar notas, recordatorios o pendientes aquí_

---

*Generado el 2026-04-06 — Se actualiza automáticamente con Dataview*
