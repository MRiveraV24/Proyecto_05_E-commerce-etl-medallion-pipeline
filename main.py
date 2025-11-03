"""
Pipeline ETL con Arquitectura Medallion para E-commerce Dataset
Autor: Marcelo Rivera Vega Data Engineering
Fecha: 2025-10-28
Descripción: Pipeline completo para procesar datos de ventas online con capas Bronze, Silver y Gold
"""

import pandas as pd
import numpy as np
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Tuple, Optional
import warnings

warnings.filterwarnings('ignore')

# ==================== CONFIGURACIÓN ====================

class Config:
    """Configuración centralizada del pipeline"""
    
    # Rutas de datos
    BASE_PATH = Path('/content')
    BRONZE_PATH = BASE_PATH / 'data' / 'bronze'
    SILVER_PATH = BASE_PATH / 'data' / 'silver'
    GOLD_PATH = BASE_PATH / 'data' / 'gold'
    LOGS_PATH = BASE_PATH / 'logs'
    
    # URL del dataset
    DATASET_URL = 'https://archive.ics.uci.edu/ml/machine-learning-databases/00352/Online%20Retail.xlsx'
    
    # Parámetros de calidad
    MIN_QUANTITY = 0
    MIN_UNIT_PRICE = 0.01
    MAX_UNIT_PRICE = 10000
    
    @classmethod
    def create_directories(cls) -> None:
        """Crear estructura de directorios"""
        for path in [cls.BRONZE_PATH, cls.SILVER_PATH, cls.GOLD_PATH, cls.LOGS_PATH]:
            path.mkdir(parents=True, exist_ok=True)


# ==================== CONFIGURACIÓN DE LOGGING ====================

def setup_logging() -> logging.Logger:
    """
    Configura el sistema de logging del pipeline
    
    Returns:
        Logger configurado
    """
    Config.create_directories()
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = Config.LOGS_PATH / f'etl_pipeline_{timestamp}.log'
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger('ETL_Pipeline')
    logger.info("="*60)
    logger.info("Pipeline ETL Iniciado")
    logger.info(f"Timestamp: {timestamp}")
    logger.info("="*60)
    
    return logger


# ==================== CAPA BRONZE: EXTRACCIÓN ====================

def extract_data(logger: logging.Logger) -> Optional[pd.DataFrame]:
    """
    Extrae datos crudos desde la fuente original
    
    Args:
        logger: Logger para registro de eventos
        
    Returns:
        DataFrame con datos crudos o None si falla
    """
    logger.info("ETAPA 1: EXTRACCIÓN DE DATOS (BRONZE LAYER)")
    logger.info("-" * 60)
    
    try:
        logger.info(f"Descargando datos desde: {Config.DATASET_URL}")
        
        # Descargar datos
        df_raw = pd.read_excel(Config.DATASET_URL, engine='openpyxl')
        
        # Métricas de extracción
        logger.info(f"✓ Datos extraídos exitosamente")
        logger.info(f"  - Registros: {len(df_raw):,}")
        logger.info(f"  - Columnas: {len(df_raw.columns)}")
        logger.info(f"  - Tamaño en memoria: {df_raw.memory_usage(deep=True).sum() / 1024**2:.2f} MB")
        
        return df_raw
        
    except Exception as e:
        logger.error(f"✗ Error en extracción: {str(e)}")
        return None


def load_bronze(df: pd.DataFrame, logger: logging.Logger) -> bool:
    """
    Guarda datos crudos en la capa Bronze sin modificaciones
    
    Args:
        df: DataFrame con datos crudos
        logger: Logger para registro
        
    Returns:
        True si se guardó exitosamente, False en caso contrario
    """
    logger.info("Guardando datos en capa BRONZE...")
    
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filepath = Config.BRONZE_PATH / f'raw_data_{timestamp}.parquet'
        
        # Crear copia para no modificar el original
        df_to_save = df.copy()
        
        # Convertir tipos problemáticos para Parquet
        # InvoiceNo puede contener 'C' para cancelaciones, mantener como string
        if 'InvoiceNo' in df_to_save.columns:
            df_to_save['InvoiceNo'] = df_to_save['InvoiceNo'].astype(str)
        
        # StockCode también puede tener caracteres especiales
        if 'StockCode' in df_to_save.columns:
            df_to_save['StockCode'] = df_to_save['StockCode'].astype(str)
        
        # Description puede tener valores nulos
        if 'Description' in df_to_save.columns:
            df_to_save['Description'] = df_to_save['Description'].fillna('').astype(str)
        
        # CustomerID como float (tiene nulos)
        if 'CustomerID' in df_to_save.columns:
            df_to_save['CustomerID'] = df_to_save['CustomerID'].astype('float64')
        
        # Guardar en formato Parquet con compresión
        df_to_save.to_parquet(filepath, index=False, compression='snappy', engine='pyarrow')
        
        logger.info(f"✓ Datos guardados en: {filepath}")
        logger.info(f"  - Formato: Parquet (compresión Snappy)")
        logger.info(f"  - Tamaño archivo: {filepath.stat().st_size / 1024**2:.2f} MB")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Error guardando Bronze: {str(e)}")
        logger.exception("Stack trace completo:")
        return False


# ==================== CAPA SILVER: TRANSFORMACIÓN ====================

def validate_data_quality(df: pd.DataFrame, logger: logging.Logger) -> Dict[str, int]:
    """
    Valida calidad de datos y reporta problemas
    
    Args:
        df: DataFrame a validar
        logger: Logger para registro
        
    Returns:
        Diccionario con métricas de calidad
    """
    logger.info("Validando calidad de datos...")
    
    metrics = {
        'total_rows': len(df),
        'duplicates': df.duplicated().sum(),
        'missing_invoice': df['InvoiceNo'].isna().sum(),
        'missing_customer': df['CustomerID'].isna().sum(),
        'negative_quantity': (df['Quantity'] < 0).sum(),
        'zero_price': (df['UnitPrice'] == 0).sum(),
        'invalid_dates': pd.isna(df['InvoiceDate']).sum()
    }
    
    logger.info("Métricas de calidad:")
    for key, value in metrics.items():
        if value > 0:
            logger.warning(f"  - {key}: {value:,} ({value/metrics['total_rows']*100:.2f}%)")
    
    return metrics


def transform_silver(df: pd.DataFrame, logger: logging.Logger) -> Optional[pd.DataFrame]:
    """
    Limpia y transforma datos para capa Silver
    
    Args:
        df: DataFrame de capa Bronze
        logger: Logger para registro
        
    Returns:
        DataFrame limpio o None si falla
    """
    logger.info("\nETAPA 2: TRANSFORMACIÓN Y LIMPIEZA (SILVER LAYER)")
    logger.info("-" * 60)
    
    try:
        df_clean = df.copy()
        initial_rows = len(df_clean)
        
        # 1. Validar calidad inicial
        validate_data_quality(df_clean, logger)
        
        # 2. Eliminar duplicados
        df_clean = df_clean.drop_duplicates()
        logger.info(f"Duplicados eliminados: {initial_rows - len(df_clean):,}")
        
        # 3. Filtrar registros con CustomerID válido
        df_clean = df_clean[df_clean['CustomerID'].notna()]
        logger.info(f"Registros sin CustomerID eliminados: {initial_rows - len(df_clean):,}")
        
        # 4. Filtrar cantidades y precios válidos
        df_clean = df_clean[
            (df_clean['Quantity'] > Config.MIN_QUANTITY) &
            (df_clean['UnitPrice'] >= Config.MIN_UNIT_PRICE) &
            (df_clean['UnitPrice'] <= Config.MAX_UNIT_PRICE)
        ]
        logger.info(f"Registros con valores inválidos eliminados")
        
        # 5. Crear columnas derivadas
        df_clean['TotalPrice'] = df_clean['Quantity'] * df_clean['UnitPrice']
        df_clean['InvoiceDate'] = pd.to_datetime(df_clean['InvoiceDate'])
        df_clean['Year'] = df_clean['InvoiceDate'].dt.year
        df_clean['Month'] = df_clean['InvoiceDate'].dt.month
        df_clean['DayOfWeek'] = df_clean['InvoiceDate'].dt.dayofweek
        df_clean['Hour'] = df_clean['InvoiceDate'].dt.hour
        
        # 6. Normalizar datos
        df_clean['Description'] = df_clean['Description'].str.strip().str.upper()
        df_clean['Country'] = df_clean['Country'].str.strip()
        df_clean['InvoiceNo'] = df_clean['InvoiceNo'].astype(str).str.strip()
        df_clean['StockCode'] = df_clean['StockCode'].astype(str).str.strip()
        df_clean['CustomerID'] = df_clean['CustomerID'].astype(int)
        
        # 7. Resumen de transformación
        final_rows = len(df_clean)
        logger.info(f"\n✓ Transformación completada:")
        logger.info(f"  - Registros iniciales: {initial_rows:,}")
        logger.info(f"  - Registros finales: {final_rows:,}")
        logger.info(f"  - Registros eliminados: {initial_rows - final_rows:,} ({(initial_rows-final_rows)/initial_rows*100:.2f}%)")
        logger.info(f"  - Columnas nuevas: Year, Month, DayOfWeek, Hour, TotalPrice")
        
        return df_clean
        
    except Exception as e:
        logger.error(f"✗ Error en transformación Silver: {str(e)}")
        return None


def load_silver(df: pd.DataFrame, logger: logging.Logger) -> bool:
    """
    Guarda datos limpios en capa Silver
    
    Args:
        df: DataFrame limpio
        logger: Logger para registro
        
    Returns:
        True si se guardó exitosamente
    """
    try:
        logger.info("\nGuardando datos en capa SILVER...")
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filepath = Config.SILVER_PATH / f'clean_data_{timestamp}.parquet'
        
        df.to_parquet(filepath, index=False, compression='snappy')
        
        logger.info(f"✓ Datos guardados en: {filepath}")
        logger.info(f"  - Tamaño archivo: {filepath.stat().st_size / 1024**2:.2f} MB")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Error guardando Silver: {str(e)}")
        return False


# ==================== CAPA GOLD: AGREGACIÓN ====================

def aggregate_sales_by_country(df: pd.DataFrame, logger: logging.Logger) -> Optional[pd.DataFrame]:
    """
    Agrega ventas por país
    
    Args:
        df: DataFrame de capa Silver
        logger: Logger para registro
        
    Returns:
        DataFrame agregado
    """
    try:
        logger.info("Creando agregación: Ventas por País")
        
        df_country = df.groupby('Country').agg({
            'InvoiceNo': 'nunique',
            'CustomerID': 'nunique',
            'Quantity': 'sum',
            'TotalPrice': 'sum'
        }).reset_index()
        
        df_country.columns = ['Country', 'TotalOrders', 'UniqueCustomers', 
                              'TotalQuantity', 'TotalRevenue']
        
        df_country['AvgOrderValue'] = df_country['TotalRevenue'] / df_country['TotalOrders']
        df_country = df_country.sort_values('TotalRevenue', ascending=False)
        
        logger.info(f"  ✓ Agregación completada: {len(df_country)} países")
        
        return df_country
        
    except Exception as e:
        logger.error(f"  ✗ Error en agregación por país: {str(e)}")
        return None


def aggregate_sales_by_time(df: pd.DataFrame, logger: logging.Logger) -> Optional[pd.DataFrame]:
    """
    Agrega ventas por período temporal
    
    Args:
        df: DataFrame de capa Silver
        logger: Logger para registro
        
    Returns:
        DataFrame agregado
    """
    try:
        logger.info("Creando agregación: Ventas por Período")
        
        df['YearMonth'] = df['InvoiceDate'].dt.to_period('M').astype(str)
        
        df_time = df.groupby('YearMonth').agg({
            'InvoiceNo': 'nunique',
            'CustomerID': 'nunique',
            'TotalPrice': ['sum', 'mean'],
            'Quantity': 'sum'
        }).reset_index()
        
        df_time.columns = ['YearMonth', 'TotalOrders', 'UniqueCustomers', 
                          'TotalRevenue', 'AvgOrderValue', 'TotalQuantity']
        
        logger.info(f"  ✓ Agregación completada: {len(df_time)} períodos")
        
        return df_time
        
    except Exception as e:
        logger.error(f"  ✗ Error en agregación temporal: {str(e)}")
        return None


def aggregate_top_products(df: pd.DataFrame, logger: logging.Logger, top_n: int = 50) -> Optional[pd.DataFrame]:
    """
    Identifica productos más vendidos
    
    Args:
        df: DataFrame de capa Silver
        logger: Logger para registro
        top_n: Número de productos top
        
    Returns:
        DataFrame con top productos
    """
    try:
        logger.info(f"Creando agregación: Top {top_n} Productos")
        
        df_products = df.groupby(['StockCode', 'Description']).agg({
            'Quantity': 'sum',
            'TotalPrice': 'sum',
            'InvoiceNo': 'nunique',
            'CustomerID': 'nunique'
        }).reset_index()
        
        df_products.columns = ['StockCode', 'Description', 'TotalQuantitySold', 
                               'TotalRevenue', 'TotalOrders', 'UniqueCustomers']
        
        df_products['AvgPricePerUnit'] = df_products['TotalRevenue'] / df_products['TotalQuantitySold']
        df_products['AvgQuantityPerOrder'] = df_products['TotalQuantitySold'] / df_products['TotalOrders']
        df_products = df_products.sort_values('TotalRevenue', ascending=False).head(top_n)
        
        logger.info(f"  ✓ Top productos identificados")
        
        return df_products
        
    except Exception as e:
        logger.error(f"  ✗ Error en agregación de productos: {str(e)}")
        return None


def aggregate_customer_segments(df: pd.DataFrame, logger: logging.Logger) -> Optional[pd.DataFrame]:
    """
    Crea segmentación de clientes basada en comportamiento de compra
    
    Args:
        df: DataFrame de capa Silver
        logger: Logger para registro
        
    Returns:
        DataFrame con segmentos de clientes
    """
    try:
        logger.info("Creando agregación: Segmentación de Clientes")
        
        df_customers = df.groupby('CustomerID').agg({
            'InvoiceNo': 'nunique',
            'TotalPrice': 'sum',
            'Quantity': 'sum',
            'InvoiceDate': ['min', 'max']
        }).reset_index()
        
        df_customers.columns = ['CustomerID', 'TotalOrders', 'TotalSpent', 
                               'TotalItems', 'FirstPurchase', 'LastPurchase']
        
        # Calcular métricas derivadas
        df_customers['AvgOrderValue'] = df_customers['TotalSpent'] / df_customers['TotalOrders']
        df_customers['CustomerLifetime'] = (df_customers['LastPurchase'] - df_customers['FirstPurchase']).dt.days
        
        # Crear segmentos
        df_customers['Segment'] = pd.cut(
            df_customers['TotalSpent'],
            bins=[0, 1000, 5000, float('inf')],
            labels=['Low Value', 'Medium Value', 'High Value']
        )
        
        logger.info(f"  ✓ {len(df_customers)} clientes segmentados")
        
        return df_customers
        
    except Exception as e:
        logger.error(f"  ✗ Error en segmentación de clientes: {str(e)}")
        return None


def load_gold(dataframes: Dict[str, pd.DataFrame], logger: logging.Logger) -> bool:
    """
    Guarda tablas agregadas en capa Gold
    
    Args:
        dataframes: Diccionario con DataFrames agregados
        logger: Logger para registro
        
    Returns:
        True si se guardó exitosamente
    """
    logger.info("\nETAPA 3: AGREGACIÓN Y ALMACENAMIENTO (GOLD LAYER)")
    logger.info("-" * 60)
    
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        for name, df in dataframes.items():
            if df is not None:
                filepath = Config.GOLD_PATH / f'{name}_{timestamp}.parquet'
                df.to_parquet(filepath, index=False, compression='snappy')
                logger.info(f"✓ Guardado: {name} ({len(df)} registros)")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Error guardando Gold: {str(e)}")
        return False


# ==================== ORQUESTACIÓN PRINCIPAL ====================

def main() -> bool:
    """
    Función principal que orquesta el pipeline ETL completo
    
    Returns:
        True si el pipeline se ejecutó exitosamente
    """
    logger = setup_logging()
    
    try:
        # EXTRACCIÓN (Bronze)
        df_raw = extract_data(logger)
        if df_raw is None:
            logger.error("Pipeline abortado: Error en extracción")
            return False
        
        load_bronze(df_raw, logger)
        
        # TRANSFORMACIÓN (Silver)
        df_clean = transform_silver(df_raw, logger)
        if df_clean is None:
            logger.error("Pipeline abortado: Error en transformación")
            return False
        
        load_silver(df_clean, logger)
        
        # AGREGACIÓN (Gold)
        gold_tables = {
            'sales_by_country': aggregate_sales_by_country(df_clean, logger),
            'sales_by_time': aggregate_sales_by_time(df_clean, logger),
            'top_products': aggregate_top_products(df_clean, logger),
            'customer_segments': aggregate_customer_segments(df_clean, logger)
        }
        
        load_gold(gold_tables, logger)
        
        # RESUMEN FINAL
        logger.info("\n" + "="*60)
        logger.info("PIPELINE ETL COMPLETADO EXITOSAMENTE")
        logger.info("="*60)
        logger.info(f"Registros procesados: {len(df_clean):,}")
        logger.info(f"Tablas Gold generadas: {len([t for t in gold_tables.values() if t is not None])}")
        logger.info("="*60)
        
        return True
        
    except Exception as e:
        logger.critical(f"Error crítico en pipeline: {str(e)}")
        return False


# ==================== EJECUCIÓN ====================

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
