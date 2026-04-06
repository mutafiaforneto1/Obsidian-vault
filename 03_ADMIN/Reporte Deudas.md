---
tipo: reporte
categoria: cobranzas
fecha: 2026-04-06
---

# 🚨 Reporte de Clientes con Deudas

> Generado automáticamente el: `=this.fecha`

## 📊 Resumen

```dataviewjs
const deudas = dv.pages('"01_TRABAJOS"')
    .where(p => p.mano_de_obra && p.estado && p.estado.includes("Terminado") && (p.pagado === false || p.pagado === "false"));

const totalDeuda = deudas.length > 0 ? deudas.mano_de_obra.array().reduce((a, b) => a + b, 0) : 0;
const cantidadTrabajos = deudas.length;
const clientesUnicos = [...new Set(deudas.cliente.array())].filter(c => c);

dv.header(2, "💸 Total a Cobrar: $" + totalDeuda.toLocaleString());
dv.paragraph("📋 Trabajos pendientes de cobro: " + cantidadTrabajos);
dv.paragraph("👥 Clientes con deuda: " + clientesUnicos.length);
```

---

## 📋 Detalle por Cliente

```dataview
TABLE 
    dirección AS "Dirección del Trabajo",
    fecha AS "Fecha",
    mano_de_obra AS "Monto",
    tipo_trabajo AS "Tipo de Trabajo"
FROM "01_TRABAJOS"
WHERE estado = "🛠️ Terminado" AND (pagado = false OR pagado = "false")
SORT mano_de_obra DESC
```

---

## 📱 Contactos para Cobranza

```dataview
TABLE
    file.link AS "Cliente",
    dirección_fija AS "Dirección",
    teléfono AS "Teléfono",
    categoría AS "Categoría"
FROM "02_CLIENTES"
WHERE file.name IN listaClientes
```

---

## 💡 Acciones Recomendadas

1. **Prioridad Alta** (> $30,000): Contactar inmediatamente
2. **Prioridad Media** ($10,000 - $30,000): Contactar esta semana
3. **Prioridad Baja** (< $10,000): Contactar cuando sea posible

---

## 📝 Notas de Cobranza

> Usar [[Control de cobros]] para registrar los pagos recibidos.
