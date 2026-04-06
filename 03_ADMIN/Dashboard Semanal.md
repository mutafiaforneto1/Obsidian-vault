---
tipo: dashboard
tema: semanal
fecha_creación: 2026-04-06
---

# 📅 Dashboard Semanal

> **Semana del:** `= this.semanaInicio`  
> **Generado automáticamente** — no hace falta editar fechas

```dataviewjs
// --- CÁLCULO DE SEMANA AUTOMÁTICO ---
// Semana actual basada en el lunes
const hoy = new Date();
const diaSemana = hoy.getDay(); // 0=dom, 1=lun, ...
const diff = hoy.getDate() - diaSemana + (diaSemana === 0 ? -6 : 1); // ajustar al lunes
const lunesInicio = new Date(hoy.setDate(diff));
const viernesFin = new Date(hoy);
viernesFin.setDate(lunesInicio.getDate() + 4);

const fechaStart = lunesInicio.toISOString().split('T')[0]; // "2026-04-06"
const fechaEnd = viernesFin.toISOString().split('T')[0]; // "2026-04-10"

// Mostrar semana
dv.header(2, `📅 Semana: ${formatDateEs(fechaStart)} — ${formatDateEs(fechaEnd)}`);

function formatDateEs(fechaStr) {
    const f = new Date(fechaStr + 'T12:00:00');
    const dias = ['Dom','Lun','Mar','Mié','Jue','Vie','Sáb'];
    const meses = ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic'];
    return `${dias[f.getDay()]} ${f.getDate()} ${meses[f.getMonth()]}`;
}

// --- TRABAJOS DE ESTA SEMANA ---
const todosTrabajos = dv.pages('"01_TRABAJOS"');

// Filtramos por fecha dentro de esta semana
function estaEnSemana(fecha) {
    if (!fecha) return false;
    const f = String(fecha);
    // Soporta formatos: "2026-04-06", "2026-04-06 10:00", etc
    const fechaDate = new Date(f + 'T12:00:00');
    return fechaDate >= lunesInicio && fechaDate <= viernesFin;
}

const trabajosSemana = todosTrabajos.filter(p => estaEnSemana(p.fecha));

dv.header(3, `🔨 Trabajos de esta semana: ${trabajosSemana.length}`);

if (trabajosSemana.length > 0) {
    dv.table(
        ["📋 Trabajo", "Cliente", "Estado", "💰 M.O."],
        trabajosSemana
            .sort((a, b) => a.prioridad - (b.prioridad || 99))
            .map(p => [
                p.file.link,
                p.cliente || "—",
                p.estado || "Sin estado",
                p.mano_de_obra ? `$${Number(p.mano_de_obra).toLocaleString()}` : "—"
            ])
    );
} else {
    dv.paragraph("_No hay trabajos registrados para esta semana._");
}

// --- RESUMEN FINANCIERO SEMANAL ---
dv.header(3, "💰 Resumen semanal");

const cobradosSemana = trabajosSemana.filter(p => p.pagado === true || p.pagado === "true");
const sumaCobrado = cobradosSemana.length > 0 ? cobradosSemana.mano_de_obra.array().reduce((a, b) => a + Number(b), 0) : 0;

const pendientesSemana = trabajosSemana.filter(p => p.pagado === false || p.pagado === "false" || !p.pagado);
const sumaPendiente = pendientesSemana.length > 0 ? pendientesSemana.mano_de_obra.array().reduce((a, b) => a + Number(b), 0) : 0;

const enCursoSemana = trabajosSemana.filter(p => p.estado && p.estado.includes("En curso"));

dv.paragraph(`**✅ Cobrado esta semana:** $${sumaCobrado.toLocaleString()}`);
dv.paragraph(`**⏳ Por cobrar:** $${sumaPendiente.toLocaleString()}`);
dv.paragraph(`**🛠️ En curso:** ${enCursoSemana.length} trabajo(s)`);
dv.paragraph(`**📈 Total facturado:** $${(sumaCobrado + sumaPendiente).toLocaleString()}`);

// --- PRESUPUESTOS PENDIENTES DE RESPUESTA ---
dv.header(3, "📝 Presupuestos esperando respuesta");

const presupuestos = todosTrabajos
    .filter(p => p.estado && p.estado.includes("Presupuesto"))
    .filter(p => {
        if (!p.fecha) return false;
        const diasDesdePresup = Math.floor((hoy - new Date(String(p.fecha) + 'T12:00:00')) / (1000 * 60 * 60 * 24));
        return diasDesdePresup <= 30; // últimos 30 días
    });

if (presupuestos.length > 0) {
    dv.table(
        ["📋 Presupuesto", "Cliente", "📅 Fecha", "💰 Monto"],
        presupuestos
            .sort((a, b) => String(b.fecha).localeCompare(String(a.fecha)))
            .map(p => [
                p.file.link,
                p.cliente || "—",
                String(p.fecha || "Sin fecha"),
                p.mano_de_obra ? `$${Number(p.mano_de_obra).toLocaleString()}` : "—"
            ])
    );
} else {
    dv.paragraph("_No hay presupuestos pendientes._");
}

// --- DIARIO DE LA SEMANA ---
dv.header(3, "📓 Notas del diario de esta semana");

const notasDiario = dv.pages('"05_DIARIO"')
    .filter(n => {
        const nombre = n.file.name;
        return nombre.includes(fechaStart) || (n.fecha && estaEnSemana(n.fecha));
    });

// Buscar notas que coincidan con los días de la semana
const diasSemana = [];
for (let d = lunesInicio; d <= viernesFin; d.setDate(d.getDate() + 1)) {
    diasSemana.push(d.toISOString().split('T')[0]);
}

const notasEncontradas = dv.pages('"05_DIARIO"')
    .filter(n => diasSemana.some(dia => n.file.name.includes(dia)));

if (notasEncontradas.length > 0) {
    dv.list(notasEncontradas.map(n => n.file.link));
    // Agregar enlaces para crear las notas que faltan
    const nombresEncontrados = notasEncontradas.map(n => n.file.name);
    const faltantes = diasSemana.filter(dia => !nombresEncontrados.some(n => n.includes(dia)));
    if (faltantes.length > 0) {
        dv.paragraph("_Notas sin crear:_ " + faltantes.map(f => `[[05_DIARIO/${f}]]`).join(", "));
    }
} else {
    dv.paragraph("_No hay notas de diario esta semana._");
    dv.paragraph("Días disponibles: " + diasSemana.map(d => `[[05_DIARIO/${d}]]`).join(", "));
}
```

---

## 🚨 Deudas Activas (Recordatorio)

```dataview
TABLE cliente AS "Cliente", mano_de_obra AS "Monto", fecha AS "Fecha Trabajo"
FROM "01_TRABAJOS"
WHERE estado = "🛠️ Terminado" AND (pagado = false OR pagado = "false")
SORT mano_de_obra DESC
```

---

## 📅 Próximos Compromisos

```dataview
TABLE cliente AS "Cliente", dirección AS "Dirección", fecha AS "Fecha", prioridad AS "Prioridad"
FROM "01_TRABAJOS"
WHERE estado = "🛠️ En curso" OR estado = "🛠️ Pendiente" OR estado = "🛠️ pendiente"
SORT fecha ASC
```
