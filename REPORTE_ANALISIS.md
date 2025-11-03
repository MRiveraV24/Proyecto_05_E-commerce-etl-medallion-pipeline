# 📊 Reporte de Análisis ETL - E-commerce Dataset

## 📋 Resumen Ejecutivo

**Fecha de Ejecución:** 2025-11-01 15:49:58
**Estado:** SUCCESS

---

## 🥉 Capa Bronze - Datos Crudos

- **Registros Extraídos:** 541,909
- **Fuente:** UCI Machine Learning Repository
- **Formato:** Parquet (Snappy compression)

---

## 🥈 Capa Silver - Datos Limpios

### Transformaciones Aplicadas:

1. ✅ Eliminación de duplicados
2. ✅ Filtrado de CustomerID nulos
3. ✅ Validación de cantidades y precios
4. ✅ Creación de 8 columnas derivadas
5. ✅ Normalización de strings

### Métricas:

- **Registros Limpios:** 392,688
- **Registros Filtrados:** 149,221
- **Tasa de Retención:** 72.46%

---

## 🥇 Capa Gold - Datos Agregados

### Tablas Generadas:

1. **sales_by_country** - Ventas por país
2. **sales_by_time** - Tendencias temporales
3. **top_products** - Productos más vendidos
4. **customer_segments** - Segmentación de clientes

---

## 💼 Insights de Negocio

### Métricas Principales:

| Métrica | Valor |
|---------|-------|
| 💰 Ingresos Totales | £8,887,208.89 |
| 🛒 Ticket Promedio | £479.56 |
| 👥 Clientes Únicos | 4,338 |
| 📦 Productos Únicos | 3,664 |
| 📋 Total Pedidos | 18,532 |
| 🌍 Países Atendidos | 37 |

### Hallazgos Clave:


#### 🏆 País Principal: United Kingdom
- Ingresos: £7,285,024.64

#### 📅 Mejor Mes: 2011-11
- Ingresos: £1,156,205.61

#### 🥇 Producto Top: PAPER CRAFT , LITTLE BIRDIE
- Ingresos: £168,469.60


### 🌍 Top 5 Países por Ingresos:

| Ranking | País | Ingresos | Clientes | Pedidos |
|---------|------|----------|----------|---------|
| 36 | United Kingdom | £7,285,025 | 3,920 | 16,646 |
| 24 | Netherlands | £285,446 | 9 | 94 |
| 11 | EIRE | £265,262 | 3 | 260 |
| 15 | Germany | £228,678 | 94 | 457 |
| 14 | France | £208,934 | 87 | 389 |


### 📈 Análisis Temporal:

- **Períodos Analizados:** 13 meses
- **Crecimiento Promedio:** 3.62% mensual
- **Mejor Período:** 2011-11
- **Peor Período:** 2011-02


---

## 📊 Visualizaciones Generadas:

1. `top_countries_dashboard.png` - Análisis de países
2. `sales_trends_dashboard.png` - Tendencias temporales
3. `top_products_analysis.png` - Productos más vendidos
4. `customer_segments_analysis.png` - Segmentación de clientes

---

## 🏗️ Arquitectura del Pipeline

```
┌─────────────────┐
│   UCI Repository│
└────────┬────────┘
         ↓
    ┌────────┐
    │ BRONZE │ ← Datos crudos (Parquet)
    └────┬───┘
         ↓
    ┌────────┐
    │ SILVER │ ← Datos limpios + transformaciones
    └────┬───┘
         ↓
    ┌────────┐
    │  GOLD  │ ← Agregaciones analíticas
    └────────┘
```

---

## 📝 Notas Técnicas

- **Formato de Almacenamiento:** Parquet con compresión Snappy
- **Herramientas:** Python, Pandas, Matplotlib, Seaborn
- **Ambiente:** Google Colab
- **Calidad de Datos:** 8 pruebas unitarias ejecutadas exitosamente

---

**Generado automáticamente por Pipeline ETL**
*Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
