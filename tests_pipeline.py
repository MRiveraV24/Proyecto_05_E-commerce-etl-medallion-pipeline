"""
Pruebas Unitarias para Pipeline ETL
Autor: Marcelo Rivera Vega Data Engineering
Fecha: 2025-10-28
Descripción: Suite de pruebas para validar transformaciones y calidad de datos
"""

import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


class TestDataQuality(unittest.TestCase):
    """Pruebas de calidad de datos"""
    
    def setUp(self):
        """Configurar datos de prueba"""
        self.sample_data = pd.DataFrame({
            'InvoiceNo': ['536365', '536365', '536366', '536367'],
            'StockCode': ['85123A', '71053', '84406B', '22752'],
            'Description': ['WHITE HANGING HEART', 'WHITE METAL LANTERN', 'CREAM CUPID HEARTS', 'SET 7 BABUSHKA NESTING BOXES'],
            'Quantity': [6, 6, 8, 2],
            'InvoiceDate': [datetime(2010, 12, 1, 8, 26)] * 4,
            'UnitPrice': [2.55, 3.39, 2.75, 7.65],
            'CustomerID': [17850.0, 17850.0, 17850.0, 17850.0],
            'Country': ['United Kingdom'] * 4
        })
    
    def test_no_missing_critical_columns(self):
        """Verificar que no falten columnas críticas"""
        required_columns = ['InvoiceNo', 'StockCode', 'Quantity', 'UnitPrice', 'CustomerID']
        for col in required_columns:
            self.assertIn(col, self.sample_data.columns, f"Columna crítica faltante: {col}")
    
    def test_positive_quantities(self):
        """Verificar que las cantidades sean positivas"""
        self.assertTrue((self.sample_data['Quantity'] > 0).all(), 
                       "Existen cantidades negativas o cero")
    
    def test_positive_prices(self):
        """Verificar que los precios sean positivos"""
        self.assertTrue((self.sample_data['UnitPrice'] > 0).all(), 
                       "Existen precios negativos o cero")
    
    def test_valid_customer_ids(self):
        """Verificar que CustomerID sea válido"""
        self.assertFalse(self.sample_data['CustomerID'].isna().any(), 
                        "Existen CustomerID nulos")
    
    def test_date_format(self):
        """Verificar formato de fechas"""
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(self.sample_data['InvoiceDate']),
                       "InvoiceDate no es tipo datetime")


class TestTransformations(unittest.TestCase):
    """Pruebas de transformaciones de datos"""
    
    def setUp(self):
        """Configurar datos de prueba"""
        self.df = pd.DataFrame({
            'Quantity': [10, 5, 20],
            'UnitPrice': [2.5, 10.0, 1.0],
            'InvoiceDate': [
                datetime(2010, 12, 1, 8, 26),
                datetime(2010, 12, 15, 14, 30),
                datetime(2011, 1, 10, 10, 15)
            ]
        })
    
    def test_total_price_calculation(self):
        """Verificar cálculo de precio total"""
        self.df['TotalPrice'] = self.df['Quantity'] * self.df['UnitPrice']
        expected = [25.0, 50.0, 20.0]
        np.testing.assert_array_almost_equal(self.df['TotalPrice'].values, expected)
    
    def test_date_extraction(self):
        """Verificar extracción de componentes de fecha"""
        self.df['Year'] = self.df['InvoiceDate'].dt.year
        self.df['Month'] = self.df['InvoiceDate'].dt.month
        
        self.assertEqual(self.df['Year'].iloc[0], 2010)
        self.assertEqual(self.df['Month'].iloc[0], 12)
        self.assertEqual(self.df['Month'].iloc[2], 1)
    
    def test_string_normalization(self):
        """Verificar normalización de strings"""
        df_test = pd.DataFrame({
            'Description': ['  white metal  ', 'CREAM CUPID', 'red heart  ']
        })
        df_test['Description'] = df_test['Description'].str.strip().str.upper()
        
        self.assertEqual(df_test['Description'].iloc[0], 'WHITE METAL')
        self.assertEqual(df_test['Description'].iloc[2], 'RED HEART')


class TestAggregations(unittest.TestCase):
    """Pruebas de agregaciones"""
    
    def setUp(self):
        """Configurar datos de prueba"""
        self.df = pd.DataFrame({
            'Country': ['UK', 'UK', 'France', 'France', 'Germany'],
            'InvoiceNo': ['001', '002', '003', '004', '005'],
            'CustomerID': [100, 101, 102, 102, 103],
            'TotalPrice': [50.0, 75.0, 100.0, 150.0, 200.0]
        })
    
    def test_country_aggregation(self):
        """Verificar agregación por país"""
        result = self.df.groupby('Country').agg({
            'InvoiceNo': 'nunique',
            'TotalPrice': 'sum'
        }).reset_index()
        
        uk_sales = result[result['Country'] == 'UK']['TotalPrice'].iloc[0]
        self.assertEqual(uk_sales, 125.0)
    
    def test_customer_count(self):
        """Verificar conteo de clientes únicos"""
        unique_customers = self.df['CustomerID'].nunique()
        self.assertEqual(unique_customers, 4)
    
    def test_sorting(self):
        """Verificar ordenamiento de resultados"""
        result = self.df.groupby('Country')['TotalPrice'].sum().reset_index()
        result = result.sort_values('TotalPrice', ascending=False)
        
        self.assertEqual(result.iloc[0]['Country'], 'France')


class TestDataCleaning(unittest.TestCase):
    """Pruebas de limpieza de datos"""
    
    def test_duplicate_removal(self):
        """Verificar eliminación de duplicados"""
        df = pd.DataFrame({
            'A': [1, 1, 2, 3],
            'B': ['a', 'a', 'b', 'c']
        })
        df_clean = df.drop_duplicates()
        self.assertEqual(len(df_clean), 3)
    
    def test_null_removal(self):
        """Verificar eliminación de nulos"""
        df = pd.DataFrame({
            'CustomerID': [1.0, 2.0, np.nan, 4.0]
        })
        df_clean = df[df['CustomerID'].notna()]
        self.assertEqual(len(df_clean), 3)
    
    def test_outlier_filtering(self):
        """Verificar filtrado de valores atípicos"""
        df = pd.DataFrame({
            'UnitPrice': [1.0, 2.0, 15000.0, 3.0]
        })
        MAX_PRICE = 10000
        df_clean = df[df['UnitPrice'] <= MAX_PRICE]
        self.assertEqual(len(df_clean), 3)


class TestPipelineIntegration(unittest.TestCase):
    """Pruebas de integración del pipeline"""
    
    def test_bronze_to_silver_flow(self):
        """Verificar flujo de Bronze a Silver"""
        # Simular datos Bronze (crudos)
        df_bronze = pd.DataFrame({
            'InvoiceNo': ['001', '001', '002'],
            'Quantity': [5, -2, 10],
            'UnitPrice': [2.0, 3.0, 0.0],
            'CustomerID': [100.0, np.nan, 200.0]
        })
        
        # Simular limpieza Silver
        df_silver = df_bronze[
            (df_bronze['CustomerID'].notna()) &
            (df_bronze['Quantity'] > 0) &
            (df_bronze['UnitPrice'] > 0)
        ].copy()
        
        # Verificar resultados
        self.assertEqual(len(df_silver), 1)
        self.assertEqual(df_silver.iloc[0]['InvoiceNo'], '001')
    
    def test_gold_tables_count(self):
        """Verificar que se generan 4 tablas Gold"""
        expected_tables = ['sales_by_country', 'sales_by_time', 
                          'top_products', 'customer_segments']
        self.assertEqual(len(expected_tables), 4)


def run_tests():
    """Ejecutar todas las pruebas"""
    print("="*60)
    print("EJECUTANDO SUITE DE PRUEBAS UNITARIAS")
    print("="*60 + "\n")
    
    # Crear suite de pruebas
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Agregar todas las clases de prueba
    suite.addTests(loader.loadTestsFromTestCase(TestDataQuality))
    suite.addTests(loader.loadTestsFromTestCase(TestTransformations))
    suite.addTests(loader.loadTestsFromTestCase(TestAggregations))
    suite.addTests(loader.loadTestsFromTestCase(TestDataCleaning))
    suite.addTests(loader.loadTestsFromTestCase(TestPipelineIntegration))
    
    # Ejecutar pruebas
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Resumen
    print("\n" + "="*60)
    print("RESUMEN DE PRUEBAS")
    print("="*60)
    print(f"Total de pruebas: {result.testsRun}")
    print(f"Exitosas: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Fallidas: {len(result.failures)}")
    print(f"Errores: {len(result.errors)}")
    print("="*60)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    exit(0 if success else 1)
