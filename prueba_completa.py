import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import matplotlib
matplotlib.use('TkAgg')  # Backend para Tkinter
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import pandas as pd
import geopandas as gpd
import xarray as xr
import numpy as np
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from matplotlib.patches import Rectangle
import os

class RadarLluviaApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Estimación de Lluvia por Radar - Camagüey")
        self.root.geometry("1200x800")
        
        # Variables para datos
        self.gdf_pluv = None
        self.da_radar = None
        self.comparison_data = None
        
        # Configurar estilo
        style = ttk.Style()
        style.configure('TFrame', background='#f0f0f0')
        style.configure('TButton', font=('Arial', 10), padding=5)
        style.configure('TLabel', background='#f0f0f0', font=('Arial', 10))
        
        # Crear widgets
        self.create_widgets()
        
    def create_widgets(self):
        # Frame principal
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Frame de controles
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(side=tk.TOP, fill=tk.X, pady=(0, 10))
        
        # Botones de carga
        ttk.Button(control_frame, text="Cargar Pluviómetros (Excel)", 
                  command=self.load_pluviometros).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Cargar Radar (NetCDF)", 
                  command=self.load_radar).pack(side=tk.LEFT, padx=5)
        
        # Botones de visualización
        ttk.Button(control_frame, text="Mostrar Pluviómetros", 
                  command=self.plot_pluviometros).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Mostrar Radar", 
                  command=self.plot_radar).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Comparar Ambos", 
                  command=self.plot_comparison).pack(side=tk.LEFT, padx=5)
        
        # Frame para el gráfico
        graph_frame = ttk.Frame(main_frame)
        graph_frame.pack(fill=tk.BOTH, expand=True)
        
        # Figura de matplotlib
        self.fig = Figure(figsize=(10, 8), dpi=100)
        self.ax = self.fig.add_subplot(111, projection=ccrs.PlateCarree())
        
        # Canvas para el gráfico
        self.canvas = FigureCanvasTkAgg(self.fig, master=graph_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Barra de herramientas
        self.toolbar = NavigationToolbar2Tk(self.canvas, graph_frame)
        self.toolbar.update()
        self.canvas._tkcanvas.pack(fill=tk.BOTH, expand=True)
        
        # Frame de estado
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.status_label = ttk.Label(status_frame, text="Listo")
        self.status_label.pack(side=tk.LEFT)
    
    def load_pluviometros(self):
        filepath = filedialog.askopenfilename(
            title="Seleccionar archivo de pluviómetros",
            filetypes=[("Excel files", "*.xls *.xlsx"), ("All files", "*.*")]
        )
        
        if filepath:
            try:
                self.gdf_pluv = self.cargar_datos_pluviometros(filepath)
                self.update_status(f"Pluviómetros cargados: {len(self.gdf_pluv)} estaciones")
                messagebox.showinfo("Éxito", "Datos de pluviómetros cargados correctamente")
            except Exception as e:
                messagebox.showerror("Error", f"Error al cargar pluviómetros: {str(e)}")
    
    def load_radar(self):
        filepath = filedialog.askopenfilename(
            title="Seleccionar archivo de radar",
            filetypes=[("NetCDF files", "*.nc"), ("All files", "*.*")]
        )
        
        if filepath:
            try:
                self.da_radar = self.cargar_datos_radar(filepath)
                self.update_status("Datos de radar cargados correctamente")
                messagebox.showinfo("Éxito", "Datos de radar cargados correctamente")
            except Exception as e:
                messagebox.showerror("Error", f"Error al cargar radar: {str(e)}")
    
    def plot_pluviometros(self):
        if self.gdf_pluv is None:
            messagebox.showwarning("Advertencia", "Primero cargue los datos de pluviómetros")
            return
            
        self.clear_plot()
        
        # Configurar el mapa
        self.setup_map()
        
        # Plotear pluviómetros
        scatter = self.ax.scatter(
            self.gdf_pluv['longitud'],
            self.gdf_pluv['latitud'],
            c=self.gdf_pluv['precipitacion'],
            cmap='YlGnBu',
            s=100,
            edgecolor='black',
            transform=ccrs.PlateCarree()
        )
        
        # Añadir barra de color y título
        self.fig.colorbar(scatter, ax=self.ax, label='Precipitación (mm)')
        self.ax.set_title("Precipitación en Pluviómetros - Camagüey")
        
        self.canvas.draw()
    
    def plot_radar(self):
        if self.da_radar is None:
            messagebox.showwarning("Advertencia", "Primero cargue los datos de radar")
            return
            
        self.clear_plot()
        
        # Configurar el mapa
        self.setup_map()
        
        # Plotear datos de radar
        mesh = self.ax.pcolormesh(
            self.da_radar.lon,
            self.da_radar.lat,
            self.da_radar.values,
            cmap='YlGnBu',
            transform=ccrs.PlateCarree(),
            shading='auto'
        )
        
        # Añadir barra de color y título
        self.fig.colorbar(mesh, ax=self.ax, label='Precipitación (mm)', extend='max')
        self.ax.set_title("Precipitación Radar - Camagüey")
        
        self.canvas.draw()
    
    def plot_comparison(self):
        if self.gdf_pluv is None or self.da_radar is None:
            messagebox.showwarning("Advertencia", "Necesita cargar ambos conjuntos de datos")
            return
            
        self.clear_plot()
        
        # Configurar el mapa
        self.setup_map()
        
        # Plotear radar primero (fondo)
        mesh = self.ax.pcolormesh(
            self.da_radar.lon,
            self.da_radar.lat,
            self.da_radar.values,
            cmap='YlGnBu',
            transform=ccrs.PlateCarree(),
            shading='auto',
            alpha=0.6
        )
        
        # Plotear pluviómetros encima
        scatter = self.ax.scatter(
            self.gdf_pluv['longitud'],
            self.gdf_pluv['latitud'],
            c=self.gdf_pluv['precipitacion'],
            cmap='YlGnBu',
            s=100,
            edgecolor='black',
            transform=ccrs.PlateCarree()
        )
        
        # Añadir barra de color y título
        self.fig.colorbar(scatter, ax=self.ax, label='Precipitación (mm)')
        self.ax.set_title("Comparación Radar y Pluviómetros - Camagüey")
        
        # Calcular y mostrar estadísticas de comparación
        self.calculate_comparison_stats()
        
        self.canvas.draw()
    
    def calculate_comparison_stats(self):
        # Interpolar datos de radar a ubicaciones de pluviómetros
        radar_values = []
        
        for idx, row in self.gdf_pluv.iterrows():
            # Encontrar el píxel más cercano en los datos del radar
            dist = (self.da_radar.lon - row['longitud'])**2 + (self.da_radar.lat - row['latitud'])**2
            y_idx, x_idx = np.unravel_index(dist.argmin(), dist.shape)
            radar_values.append(float(self.da_radar.values[y_idx, x_idx]))
        
        # Crear DataFrame de comparación
        self.comparison_data = pd.DataFrame({
            'Pluviometro': self.gdf_pluv['precipitacion'],
            'Radar': radar_values,
            'Diferencia': self.gdf_pluv['precipitacion'] - radar_values
        })
        
        # Mostrar estadísticas en una ventana nueva
        stats_window = tk.Toplevel(self.root)
        stats_window.title("Estadísticas de Comparación")
        
        # Calcular estadísticas
        bias = self.comparison_data['Diferencia'].mean()
        mae = self.comparison_data['Diferencia'].abs().mean()
        rmse = np.sqrt((self.comparison_data['Diferencia']**2).mean())
        correlation = self.comparison_data[['Pluviometro', 'Radar']].corr().iloc[0,1]
        
        # Crear widgets para mostrar estadísticas
        ttk.Label(stats_window, text=f"Sesgo (Bias): {bias:.2f} mm").pack(pady=5)
        ttk.Label(stats_window, text=f"Error Absoluto Medio (MAE): {mae:.2f} mm").pack(pady=5)
        ttk.Label(stats_window, text=f"Raíz del Error Cuadrático Medio (RMSE): {rmse:.2f} mm").pack(pady=5)
        ttk.Label(stats_window, text=f"Correlación: {correlation:.2f}").pack(pady=5)
        
        # Botón para guardar resultados
        ttk.Button(stats_window, text="Guardar Resultados", 
                  command=self.save_comparison_results).pack(pady=10)
    
    def save_comparison_results(self):
        if self.comparison_data is None:
            messagebox.showwarning("Advertencia", "No hay datos de comparación para guardar")
            return
            
        filepath = filedialog.asksaveasfilename(
            title="Guardar resultados de comparación",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if filepath:
            try:
                self.comparison_data.to_csv(filepath, index=False)
                messagebox.showinfo("Éxito", f"Resultados guardados en {filepath}")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo guardar: {str(e)}")
    
    def setup_map(self):
        # Limpiar ejes y configurar mapa base
        self.ax.clear()
        self.ax.set_extent([-78.8, -76.8, 20.5, 22.0])  # Ajustado para Camagüey
        
        # Intentar cargar shapefile de Cuba
        try:
            cuba = gpd.read_file('cu_shp/cg.shp')
            cuba.boundary.plot(ax=self.ax, linewidth=1, edgecolor='gray')
            
            # Resaltar Camagüey
            nombres_posibles = ['NAME_1', 'name_1', 'NAM', 'nombre', 'provincia']
            encontrado = False
            
            for nombre in nombres_posibles:
                if nombre in cuba.columns:
                    try:
                        camaguey = cuba[cuba[nombre].str.contains('Camagüey|Camaguey', case=False, regex=True)]
                        if not camaguey.empty:
                            camaguey.plot(ax=self.ax, color='none', edgecolor='red', linewidth=2)
                            encontrado = True
                            break
                    except:
                        continue
            
            if not encontrado:
                # Dibujar un rectángulo aproximado para Camagüey
                self.ax.add_patch(Rectangle((-78.5, 20.7), 1.7, 1.3, 
                                 fill=False, color='red', linewidth=2, 
                                 transform=ccrs.PlateCarree()))
                
        except Exception as e:
            print(f"Error con shapefile: {e}")
            # Dibujar características básicas
            self.ax.add_feature(cfeature.COASTLINE, linewidth=0.5)
            self.ax.add_feature(cfeature.BORDERS, linestyle=':', linewidth=0.5)
            # Dibujar un rectángulo aproximado para Camagüey
            self.ax.add_patch(Rectangle((-78.5, 20.7), 1.7, 1.3, 
                             fill=False, color='red', linewidth=2, 
                             transform=ccrs.PlateCarree()))
        
        # Añadir gridlines
        self.ax.gridlines(draw_labels=True)
    
    def clear_plot(self):
        self.ax.clear()
        self.canvas.draw()
    
    def update_status(self, message):
        self.status_label.config(text=message)
        self.root.update_idletasks()
    
    # Funciones de carga de datos (adaptadas de los scripts originales)
    def cargar_datos_pluviometros(self, ruta_archivo):
        """Carga y procesa los datos de pluviómetros desde un archivo Excel"""
        # Leer el archivo Excel (primera hoja)
        df = pd.read_excel(ruta_archivo, sheet_name=0, header=None)
        
        # Asignar nombres a las columnas
        df = df.iloc[1:, 0:3]  # Saltar la primera fila (header) y tomar 3 columnas
        df.columns = ['longitud', 'latitud', 'precipitacion']
        
        # Limpieza y conversión
        df = df.dropna(subset=['longitud', 'latitud', 'precipitacion'])
        df['precipitacion'] = pd.to_numeric(df['precipitacion'], errors='coerce')
        df = df[df['precipitacion'] >= 0]
        
        # Convertir a GeoDataFrame
        gdf = gpd.GeoDataFrame(
            df,
            geometry=gpd.points_from_xy(df.longitud, df.latitud),
            crs="EPSG:4326"
        )
        
        return gdf
    
    def cargar_datos_radar(self, ruta_archivo, centro_lon=-77.849, centro_lat=21.4227, resolucion_km=1.0):
        """Carga y procesa los datos de radar desde un archivo NetCDF"""
        ds = xr.open_dataset(ruta_archivo)
        
        # Detectar variable de precipitación
        var_precip = 'Ra'  # Según tu output, la variable es 'Ra'
        
        # Convertir resolución de km a grados (aproximadamente)
        resolucion_grados = resolucion_km / 111.32
        
        # Calcular rangos
        rango_lon = (ds.sizes['X'] * resolucion_grados) / 2
        rango_lat = (ds.sizes['Y'] * resolucion_grados) / 2
        
        # Generar coordenadas
        lon = np.linspace(centro_lon - rango_lon, centro_lon + rango_lon, ds.sizes['X'])
        lat = np.linspace(centro_lat - rango_lat, centro_lat + rango_lat, ds.sizes['Y'])
        
        # Crear DataArray
        da = xr.DataArray(
            data=ds[var_precip].values,
            dims=['Y', 'X'],
            coords={
                'lat': (['Y'], lat),
                'lon': (['X'], lon)
            }
        )
        
        return da

if __name__ == "__main__":
    root = tk.Tk()
    app = RadarLluviaApp(root)
    root.mainloop()