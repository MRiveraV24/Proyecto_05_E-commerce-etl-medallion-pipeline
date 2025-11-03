"""
Módulo de Visualizaciones para Pipeline ETL
Autor: Marcelo Rivera Vega Data Engineering
Fecha: 2025-10-28
Descripción: Generación de gráficos y reportes visuales desde capa Gold
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Optional
import logging

# Configuración de estilo
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 6)
plt.rcParams['font.size'] = 10


class VisualizationEngine:
    """Motor de generación de visualizaciones"""
    
    def __init__(self, gold_path: Path, output_path: Optional[Path] = None):
        """
        Inicializa el motor de visualizaciones
        
        Args:
            gold_path: Ruta a los datos Gold
            output_path: Ruta para guardar gráficos
        """
        self.gold_path = gold_path
        self.output_path = output_path or gold_path.parent / 'visualizations'
        self.output_path.mkdir(exist_ok=True)
        
        self.logger = logging.getLogger('Visualizations')
    
    def load_gold_table(self, table_name: str) -> Optional[pd.DataFrame]:
        """
        Carga tabla desde capa Gold
        
        Args:
            table_name: Nombre de la tabla
            
        Returns:
            DataFrame con datos
        """
        try:
            # Buscar archivo más reciente
            files = list(self.gold_path.glob(f'{table_name}_*.parquet'))
            if not files:
                self.logger.error(f"No se encontró tabla: {table_name}")
                return None
            
            latest_file = max(files, key=lambda p: p.stat().st_mtime)
            df = pd.read_parquet(latest_file)
            
            self.logger.info(f"Tabla cargada: {table_name} ({len(df)} registros)")
            return df
            
        except Exception as e:
            self.logger.error(f"Error cargando {table_name}: {str(e)}")
            return None
    
    def plot_top_countries(self, top_n: int = 10) -> None:
        """
        Gráfico de barras: Top países por ingresos
        
        Args:
            top_n: Número de países a mostrar
        """
        df = self.load_gold_table('sales_by_country')
        if df is None:
            return
        
        # Preparar datos
        df_top = df.nlargest(top_n, 'TotalRevenue')
        
        # Crear figura
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
        
        # Gráfico 1: Ingresos por país
        bars1 = ax1.barh(df_top['Country'], df_top['TotalRevenue'], color='steelblue')
        ax1.set_xlabel('Ingresos Totales (£)', fontsize=12, fontweight='bold')
        ax1.set_ylabel('País', fontsize=12, fontweight='bold')
        ax1.set_title(f'Top {top_n} Países por Ingresos', fontsize=14, fontweight='bold')
        ax1.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'£{x/1000:.0f}K'))
        
        # Agregar valores
        for bar in bars1:
            width = bar.get_width()
            ax1.text(width, bar.get_y() + bar.get_height()/2, 
                    f'£{width/1000:.1f}K',
                    ha='left', va='center', fontsize=9, fontweight='bold')
        
        # Gráfico 2: Clientes únicos por país
        bars2 = ax2.barh(df_top['Country'], df_top['UniqueCustomers'], color='coral')
        ax2.set_xlabel('Clientes Únicos', fontsize=12, fontweight='bold')
        ax2.set_ylabel('País', fontsize=12, fontweight='bold')
        ax2.set_title(f'Top {top_n} Países por Clientes', fontsize=14, fontweight='bold')
        
        # Agregar valores
        for bar in bars2:
            width = bar.get_width()
            ax2.text(width, bar.get_y() + bar.get_height()/2, 
                    f'{int(width):,}',
                    ha='left', va='center', fontsize=9, fontweight='bold')
        
        plt.tight_layout()
        
        # Guardar
        output_file = self.output_path / 'top_countries_analysis.png'
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        self.logger.info(f"✓ Gráfico guardado: {output_file}")
        plt.show()
    
    def plot_sales_trend(self) -> None:
        """Gráfico de líneas: Tendencia de ventas en el tiempo"""
        df = self.load_gold_table('sales_by_time')
        if df is None:
            return
        
        # Crear figura con subplots
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 10))
        
        # Gráfico 1: Ingresos totales por mes
        ax1.plot(df['YearMonth'], df['TotalRevenue'], 
                marker='o', linewidth=2, markersize=6, color='steelblue')
        ax1.fill_between(range(len(df)), df['TotalRevenue'], alpha=0.3, color='steelblue')
        ax1.set_xlabel('Período', fontsize=11, fontweight='bold')
        ax1.set_ylabel('Ingresos (£)', fontsize=11, fontweight='bold')
        ax1.set_title('Evolución de Ingresos Mensuales', fontsize=13, fontweight='bold')
        ax1.tick_params(axis='x', rotation=45)
        ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'£{x/1000:.0f}K'))
        ax1.grid(True, alpha=0.3)
        
        # Gráfico 2: Número de pedidos
        ax2.plot(df['YearMonth'], df['TotalOrders'], 
                marker='s', linewidth=2, markersize=6, color='coral')
        ax2.fill_between(range(len(df)), df['TotalOrders'], alpha=0.3, color='coral')
        ax2.set_xlabel('Período', fontsize=11, fontweight='bold')
        ax2.set_ylabel('Número de Pedidos', fontsize=11, fontweight='bold')
        ax2.set_title('Evolución de Pedidos Mensuales', fontsize=13, fontweight='bold')
        ax2.tick_params(axis='x', rotation=45)
        ax2.grid(True, alpha=0.3)
        
        # Gráfico 3: Clientes únicos
        ax3.plot(df['YearMonth'], df['UniqueCustomers'], 
                marker='^', linewidth=2, markersize=6, color='green')
        ax3.fill_between(range(len(df)), df['UniqueCustomers'], alpha=0.3, color='green')
        ax3.set_xlabel('Período', fontsize=11, fontweight='bold')
        ax3.set_ylabel('Clientes Únicos', fontsize=11, fontweight='bold')
        ax3.set_title('Evolución de Clientes Activos', fontsize=13, fontweight='bold')
        ax3.tick_params(axis='x', rotation=45)
        ax3.grid(True, alpha=0.3)
        
        # Gráfico 4: Valor promedio de pedido
        ax4.plot(df['YearMonth'], df['AvgOrderValue'], 
                marker='D', linewidth=2, markersize=6, color='purple')
        ax4.fill_between(range(len(df)), df['AvgOrderValue'], alpha=0.3, color='purple')
        ax4.set_xlabel('Período', fontsize=11, fontweight='bold')
        ax4.set_ylabel('Valor Promedio (£)', fontsize=11, fontweight='bold')
        ax4.set_title('Evolución del Valor Promedio de Pedido', fontsize=13, fontweight='bold')
        ax4.tick_params(axis='x', rotation=45)
        ax4.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'£{x:.0f}'))
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # Guardar
        output_file = self.output_path / 'sales_trends_analysis.png'
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        self.logger.info(f"✓ Gráfico guardado: {output_file}")
        plt.show()
    
    def plot_top_products(self, top_n: int = 15) -> None:
        """
        Gráfico: Top productos más vendidos
        
        Args:
            top_n: Número de productos a mostrar
        """
        df = self.load_gold_table('top_products')
        if df is None:
            return
        
        df_top = df.head(top_n)
        
        # Truncar descripciones largas
        df_top['Description'] = df_top['Description'].apply(
            lambda x: x[:40] + '...' if len(x) > 40 else x
        )
        
        # Crear figura
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
        
        # Gráfico 1: Top por ingresos
        bars1 = ax1.barh(df_top['Description'], df_top['TotalRevenue'], color='teal')
        ax1.set_xlabel('Ingresos Totales (£)', fontsize=12, fontweight='bold')
        ax1.set_ylabel('Producto', fontsize=12, fontweight='bold')
        ax1.set_title(f'Top {top_n} Productos por Ingresos', fontsize=14, fontweight='bold')
        ax1.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'£{x/1000:.0f}K'))
        
        for bar in bars1:
            width = bar.get_width()
            ax1.text(width, bar.get_y() + bar.get_height()/2, 
                    f'£{width/1000:.1f}K',
                    ha='left', va='center', fontsize=8)
        
        # Gráfico 2: Top por cantidad vendida
        bars2 = ax2.barh(df_top['Description'], df_top['TotalQuantitySold'], color='orange')
        ax2.set_xlabel('Unidades Vendidas', fontsize=12, fontweight='bold')
        ax2.set_ylabel('Producto', fontsize=12, fontweight='bold')
        ax2.set_title(f'Top {top_n} Productos por Unidades', fontsize=14, fontweight='bold')
        
        for bar in bars2:
            width = bar.get_width()
            ax2.text(width, bar.get_y() + bar.get_height()/2, 
                    f'{int(width):,}',
                    ha='left', va='center', fontsize=8)
        
        plt.tight_layout()
        
        # Guardar
        output_file = self.output_path / 'top_products_analysis.png'
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        self.logger.info(f"✓ Gráfico guardado: {output_file}")
        plt.show()
    
    def plot_customer_segments(self) -> None:
        """Gráfico de segmentación de clientes"""
        df = self.load_gold_table('customer_segments')
        if df is None:
            return
        
        print("\n📈 Visualización: Segmentación de Clientes")
        print("-" * 40)
        
        # Crear figura
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
        fig.suptitle('👥 Análisis de Segmentación de Clientes', 
                     fontsize=16, fontweight='bold', y=0.98)
        
        # Gráfico 1: Distribución de segmentos (pie chart)
        segment_counts = df['Segment'].value_counts()
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']
        explode = (0.05, 0.05, 0.1)
        
        wedges, texts, autotexts = ax1.pie(
            segment_counts.values, 
            labels=segment_counts.index,
            autopct='%1.1f%%',
            colors=colors,
            explode=explode,
            startangle=90,
            textprops={'fontsize': 11, 'fontweight': 'bold'}
        )
        
        ax1.set_title('📊 Distribución de Segmentos', fontsize=13, fontweight='bold', pad=15)
        
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontsize(12)
        
        # Gráfico 2: Valor promedio por segmento
        segment_stats = df.groupby('Segment').agg({
            'TotalSpent': 'mean',
            'TotalOrders': 'mean'
        }).reset_index()
        
        import numpy as np
        x_pos = np.arange(len(segment_stats))
        bars = ax2.bar(x_pos, segment_stats['TotalSpent'], color=colors, 
                      alpha=0.8, edgecolor='black', linewidth=1.5)
        
        ax2.set_xlabel('Segmento', fontsize=12, fontweight='bold')
        ax2.set_ylabel('Gasto Promedio (£)', fontsize=12, fontweight='bold')
        ax2.set_title('💰 Valor Promedio por Segmento', fontsize=13, fontweight='bold', pad=15)
        ax2.set_xticks(x_pos)
        ax2.set_xticklabels(segment_stats['Segment'], fontsize=11)
        ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'£{x:,.0f}'))
        ax2.grid(axis='y', alpha=0.3, linestyle='--')
        
        for i, bar in enumerate(bars):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2, height,
                    f'£{height:,.0f}',
                    ha='center', va='bottom', fontsize=10, fontweight='bold')
        
        plt.tight_layout()
        
        # Guardar
        output_file = self.output_path / 'customer_segments_analysis.png'
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        self.logger.info(f"✓ Gráfico guardado: {output_file}")
        plt.show()
    
    def generate_dashboard(self) -> None:
        """Genera dashboard completo con métricas clave"""
        print("\n" + "="*60)
        print("GENERANDO DASHBOARD DE VISUALIZACIONES")
        print("="*60 + "\n")
        
        try:
            self.plot_top_countries(top_n=10)
            self.plot_sales_trend()
            self.plot_top_products(top_n=15)
            self.plot_customer_segments()
            
            print("\n" + "="*60)
            print("✓ DASHBOARD GENERADO EXITOSAMENTE")
            print(f"Gráficos guardados en: {self.output_path}")
            print("="*60)
            
        except Exception as e:
            self.logger.error(f"Error generando dashboard: {str(e)}")


def main():
    """Función principal para ejecutar visualizaciones"""
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Rutas
    gold_path = Path('/content/data/gold')
    
    # Crear motor de visualizaciones
    viz_engine = VisualizationEngine(gold_path)
    
    # Generar dashboard
    viz_engine.generate_dashboard()


if __name__ == '__main__':
    main()
