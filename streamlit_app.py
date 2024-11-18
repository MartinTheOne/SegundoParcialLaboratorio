import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.dates import YearLocator, DateFormatter


st.set_page_config(page_title="Segundo Parcial", layout="wide")

def mostrar_informacion_alumno():
    with st.container(border=True):
        st.markdown('**Legajo:** 58.720')
        st.markdown('**Nombre:** Gonzalez Martin Natanael')
        st.markdown('**Comisión:** C5')

mostrar_informacion_alumno()

with st.sidebar:
    st.header("Sube tu archivo CSV")
    archivo = st.file_uploader("Sube tu archivo CSV", type=['csv'], label_visibility="collapsed")
    
    if archivo is not None:
        file_size_kb = len(archivo.getvalue()) / 1024
        st.text(f"{archivo.name}\n{file_size_kb:.1f}KB")
    
    st.header("Seleccionar Sucursal")
    sucursales = ['Todas', 'Sucursal Norte', 'Sucursal Centro', 'Sucursal Sur']
    sucursal_seleccionada = st.selectbox('', sucursales, label_visibility="collapsed")




def calcular_variaciones(current_data, previous_data, threshold=1e-5):
    if abs(previous_data) < threshold:
        return 0  
    return ((current_data - previous_data) / previous_data) * 100

def calcular_datos(data_frame, sucursal='Todas'):
    if sucursal != 'Todas':
        data_frame = data_frame[data_frame['Sucursal'] == sucursal]
    
    productos = data_frame['Producto'].unique()
    productos_completos = {}
    
    for producto in productos:
      
        datos_producto = data_frame[data_frame['Producto'] == producto]
        
        datos_producto['Precio_promedio'] = datos_producto['Ingreso_total'] / datos_producto['Unidades_vendidas']
        precio_promedio = datos_producto['Precio_promedio'].mean()
        
        datos_producto['Margen'] = ((datos_producto['Ingreso_total'] - datos_producto['Costo_total']) / 
                                  datos_producto['Ingreso_total'] * 100)
        margen_promedio = datos_producto['Margen'].mean()
        
        unidades_vendidas = datos_producto['Unidades_vendidas'].sum()
        
        yearly_data = datos_producto.groupby('Año').agg({
            'Precio_promedio': 'mean',
            'Margen': 'mean',
            'Unidades_vendidas': 'sum'
        }).reset_index()
        
        variacion_precio = yearly_data['Precio_promedio'].pct_change().mean() * 100
        variacion_margen = yearly_data['Margen'].pct_change().mean() * 100
        variacion_unidades = yearly_data['Unidades_vendidas'].pct_change().mean() * 100
               
        datos_mensuales = datos_producto.groupby(['Año', 'Mes']).agg({
            'Precio_promedio': 'mean',
            'Margen': 'mean',
            'Unidades_vendidas': 'sum'
        }).reset_index()
        datos_mensuales['Fecha'] = pd.to_datetime(
            datos_mensuales.apply(lambda x: f"{int(x['Año'])}-{int(x['Mes'])}-01", axis=1)
        )
              
        x = np.arange(len(datos_mensuales))
        z = np.polyfit(x, datos_mensuales['Unidades_vendidas'], 1)
        p = np.poly1d(z)
        
        productos_completos[producto] = {
            'precio_promedio': precio_promedio,
            'variacion_precio': variacion_precio,
            'margen_promedio': margen_promedio,
            'variacion_margen': variacion_margen,
            'unidades_vendidas': unidades_vendidas,
            'variacion_unidades': variacion_unidades,
            'monthly_data': datos_mensuales,
            'trend': p(x)
        }
    
    return productos_completos

def hacer_grafico(data, producto):
    graf = plt.figure(figsize=(10, 5))
    ax = graf.add_axes([0.1, 0.15, 0.85, 0.65])
    ax.grid(True, linestyle='-', alpha=0.2, color='gray')
    
    monthly_data = data['monthly_data']
    ax.plot(monthly_data['Fecha'], monthly_data['Unidades_vendidas'], label=producto, color='#1f77b4')
    ax.plot(monthly_data['Fecha'], data['trend'], label='Tendencia', color='red', linestyle='--')
    
    ax.set_title('Evolución de Ventas Mensual', pad=20, y=1.2)
    ax.set_ylabel('Unidades vendidas', labelpad=10)
    ax.set_xlabel('Año-Mes', labelpad=10)
    ax.legend(title='Producto', bbox_to_anchor=(0, 1.02, 1, 0.2), loc='lower left', ncol=2, borderaxespad=0)
    ax.set_ylim(bottom=0)  
    ax.set_xlim(pd.Timestamp('2019-12-01'), pd.Timestamp('2024-12-31'))   
    ax.xaxis.set_major_locator(YearLocator(1))  
    ax.xaxis.set_major_formatter(DateFormatter('%Y')) 

    return graf

if archivo is not None:
    if sucursal_seleccionada == 'Todas':
      st.title("Datos de Todas las Sucursales")
    else:
      st.title(f"Datos de la {sucursal_seleccionada}")
     
    data_frame = pd.read_csv(archivo)
    results = calcular_datos(data_frame, sucursal_seleccionada)
    
    for producto, metrics in results.items():
      with st.container(border=True):
        col_datos, col_grafico = st.columns([1, 2])
        
        with col_datos:
            st.markdown(f"<h1 style='padding-bottom: 50px;'>{producto}</h1>", unsafe_allow_html=True)
            st.metric("Precio Promedío", f"${metrics['precio_promedio']:,.0f}", f"{metrics['variacion_precio']:.2f}%")
            st.metric("Margen Promedío", f"{metrics['margen_promedio']:,.0f}%", f"{metrics['variacion_margen']:.2f}%")
            st.metric("Unidades Vendídas", f"{metrics['unidades_vendidas']:,}", f"{metrics['variacion_unidades']:.2f}%")
        
        with col_grafico:
            graf = hacer_grafico(metrics, producto)
            st.pyplot(graf)
            plt.close(graf)

        