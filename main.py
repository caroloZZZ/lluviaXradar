import customtkinter as ctk;
from tkinter import filedialog, messagebox;
import tkinter as tk;
import xarray as xr;
import pandas as pd;
import numpy as np;
import geopandas as gpd;
import matplotlib;
matplotlib.use('Agg')
import matplotlib.pyplot as plt;
import cartopy.crs as ccrs;
import cartopy.feature as cfeature;
from scipy.interpolate import RBFInterpolator;
from sklearn.metrics import mean_squared_error;
import os;

class FusionApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Configuración de la ventana principal
        self.title("Fusión Radar-Pluviómetros")
        self.geometry("900x700")
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")
        
        # Variables de configuración
        self.ruta_radar = tk.StringVar()
        self.ruta_pluviometros = tk.StringVar()
        self.ruta_salida = tk.StringVar(value=os.path.join(os.getcwd(), "precipitacion_corregida.png"));
        self.centro_lon = tk.DoubleVar(value=77.849)
        self.centro_lat = tk.DoubleVar(value=21.4227)
        self.resolucion_km = tk.DoubleVar(value=1.0)
        
        # Crear widgets
        self.crear_widgets()
    
    def crear_widgets(self):
        # Frame principal
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Título
        title_label = ctk.CTkLabel(main_frame, text="Fusión de Datos de Precipitación", 
                                  font=("Arial", 20, "bold"))
        title_label.pack(pady=(10, 20))
        
        # Frame de configuración
        config_frame = ctk.CTkFrame(main_frame)
        config_frame.pack(fill="x", padx=10, pady=5)
        
        # Sección de archivos
        file_frame = ctk.CTkFrame(config_frame)
        file_frame.pack(fill="x", padx=5, pady=5)
        
        # Radar
        ctk.CTkLabel(file_frame, text="Archivo Radar (NetCDF):").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        radar_entry = ctk.CTkEntry(file_frame, textvariable=self.ruta_radar, width=400)
        radar_entry.grid(row=0, column=1, padx=5, pady=2)
        ctk.CTkButton(file_frame, text="Examinar", command=lambda: self.seleccionar_archivo(self.ruta_radar, [("NetCDF files", "*.nc")])).grid(row=0, column=2, padx=5, pady=2)
        
        # Pluviómetros
        ctk.CTkLabel(file_frame, text="Archivo Pluviómetros (Excel):").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        pluv_entry = ctk.CTkEntry(file_frame, textvariable=self.ruta_pluviometros, width=400)
        pluv_entry.grid(row=1, column=1, padx=5, pady=2)
        ctk.CTkButton(file_frame, text="Examinar", command=lambda: self.seleccionar_archivo(self.ruta_pluviometros, [("Excel files", "*.xls *.xlsx")])).grid(row=1, column=2, padx=5, pady=2)
        
        # Salida
        ctk.CTkLabel(file_frame, text="Archivo Salida (PNG):").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        salida_entry = ctk.CTkEntry(file_frame, textvariable=self.ruta_salida, width=400)
        salida_entry.grid(row=2, column=1, padx=5, pady=2)
        ctk.CTkButton(file_frame, text="Examinar", command=lambda: self.seleccionar_archivo(self.ruta_salida, [("PNG files", "*.png")], save=True)).grid(row=2, column=2, padx=5, pady=2)
        
        # Sección de parámetros
        param_frame = ctk.CTkFrame(config_frame)
        param_frame.pack(fill="x", padx=5, pady=5)
        
        ctk.CTkLabel(param_frame, text="Parámetros del Radar:").grid(row=0, column=0, sticky="w", columnspan=2, pady=(0, 5))
        
        ctk.CTkLabel(param_frame, text="Longitud Centro:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        ctk.CTkEntry(param_frame, textvariable=self.centro_lon, width=100).grid(row=1, column=1, sticky="w", padx=5, pady=2)
        
        ctk.CTkLabel(param_frame, text="Latitud Centro:").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        ctk.CTkEntry(param_frame, textvariable=self.centro_lat, width=100).grid(row=2, column=1, sticky="w", padx=5, pady=2)
        
        ctk.CTkLabel(param_frame, text="Resolución (km):").grid(row=3, column=0, sticky="w", padx=5, pady=2)
        ctk.CTkEntry(param_frame, textvariable=self.resolucion_km, width=100).grid(row=3, column=1, sticky="w", padx=5, pady=2)
        
        # Frame de consola
        console_frame = ctk.CTkFrame(main_frame)
        console_frame.pack(fill="both", expand=True, padx=10, pady=(10, 5))
        
        ctk.CTkLabel(console_frame, text="Consola de Salida:", font=("Arial", 12, "bold")).pack(anchor="w", padx=5, pady=5)
        
        self.console = ctk.CTkTextbox(console_frame, wrap="word", height=200)
        self.console.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Frame de botones
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(fill="x", padx=10, pady=(5, 10))
        
        ctk.CTkButton(button_frame, text="Ejecutar Fusión", command=self.ejecutar_fusion, 
                      fg_color="green", hover_color="dark green").pack(side="left", padx=5, pady=5)
        ctk.CTkButton(button_frame, text="Limpiar Consola", command=self.limpiar_consola).pack(side="left", padx=5, pady=5)
        ctk.CTkButton(button_frame, text="Salir", command=self.destroy, 
                      fg_color="red", hover_color="dark red").pack(side="right", padx=5, pady=5)
    
    def seleccionar_archivo(self, variable, filetypes, save=False):
        if save:
            filepath = filedialog.asksaveasfilename(filetypes=filetypes, defaultextension=".png")
        else:
            filepath = filedialog.askopenfilename(filetypes=filetypes)
        
        if filepath:
            variable.set(filepath)
    
    def limpiar_consola(self):
        self.console.delete("1.0", "end")
    
    def log_consola(self, mensaje):
        self.console.insert("end", mensaje + "\n")
        self.console.see("end")
        self.update()
    
    def cargar_datos_radar(self):
        try:
            self.log_consola("\n[1/3] Cargando radar...")
            
            ds = xr.open_dataset(self.ruta_radar.get())
            self.log_consola("\nMetadatos del radar:")
            self.log_consola(f"Ubicación: {self.centro_lon.get()}°E, {self.centro_lat.get()}°N")
            self.log_consola(f"Dimensiones: {ds.dims}")
            
            # Detectar automáticamente la variable de precipitación
            var_precip = None
            for var in ds.data_vars:
                if len(ds[var].dims) == 2:  # Buscamos variables 2D (Y, X)
                    var_precip = var
                    break
            
            if var_precip is None:
                raise ValueError("No se encontró una variable 2D de precipitación en el archivo NetCDF")
                
            self.log_consola(f"Variable de precipitación detectada: {var_precip}")
            
            # Convertir resolución de km a grados (aproximación)
            resolucion_grados = self.resolucion_km.get() / 111.32;  # 1° ≈ 111.32 km
            
            # Calcular rangos considerando las dimensiones del archivo
            rango_lon = (ds.sizes['X'] * resolucion_grados) / 2
            rango_lat = (ds.sizes['Y'] * resolucion_grados) / 2
            
            # Generar coordenadas
            lon = np.linspace(self.centro_lon.get() - rango_lon, self.centro_lon.get() + rango_lon, ds.sizes['X'])
            lat = np.linspace(self.centro_lat.get() - rango_lat, self.centro_lat.get() + rango_lat, ds.sizes['Y'])
            
            # Crear DataArray con coordenadas
            da = xr.DataArray(
                data=ds[var_precip].values,
                dims=['Y', 'X'],
                coords={
                    'lat': (['Y'], lat),
                    'lon': (['X'], lon)
                },
                attrs={
                    'units': ds[var_precip].attrs.get('units', 'mm'),
                    'description': ds[var_precip].attrs.get('description', ''),
                    'centro': (self.centro_lon.get(), self.centro_lat.get()),
                    'resolucion_km': self.resolucion_km.get(),
                    'variable_original': var_precip
                }
            )
            
            self.log_consola("\nCoordenadas generadas:")
            self.log_consola(f"Longitud: {lon.min():.4f} a {lon.max():.4f}")
            self.log_consola(f"Latitud: {lat.min():.4f} a {lat.max():.4f}")
            
            return da
            
        except Exception as e:
            messagebox.showerror("Error", f"Error cargando radar: {str(e)}")
            return None
    
    def cargar_datos_pluviometros(self):
        try:
            self.log_consola("\n[2/3] Cargando pluviómetros...")
            
            # Primero leemos el archivo sin especificar columnas para ver su estructura
            df_temp = pd.read_excel(self.ruta_pluviometros.get(), sheet_name=None, nrows=1)
            
            # Obtenemos el nombre real de la primera hoja
            sheet_name = list(df_temp.keys())[0]
            self.log_consola(f"Leyendo hoja: {sheet_name}")
            
            # Leemos el archivo completo
            df = pd.read_excel(self.ruta_pluviometros.get(), sheet_name=sheet_name, header=None)
            
            # Verificamos cuántas columnas tiene el archivo
            num_cols = df.shape[1]
            self.log_consola(f"El archivo tiene {num_cols} columnas")
            
            # Asignamos nombres a las columnas según lo disponible
            if num_cols >= 4:
                df = df.iloc[1:, 0:4];  # Saltamos la primera fila (header) y tomamos 4 columnas
                df.columns = ['longitud', 'latitud', 'precipitacion', 'tipo']
            elif num_cols == 3:
                df = df.iloc[1:, 0:3];  # Saltamos la primera fila y tomamos 3 columnas
                df.columns = ['longitud', 'latitud', 'precipitacion']
            else:
                raise ValueError("El archivo debe tener al menos 3 columnas (longitud, latitud, precipitación)")
            
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
            
            self.log_consola(f"\nDatos pluviómetros cargados: {len(gdf)} estaciones")
            return gdf
            
        except Exception as e:
            messagebox.showerror("Error", f"Error cargando pluviómetros: {str(e)}\n\n"
                                      "Asegúrese que el archivo Excel tenga al menos 3 columnas con:\n"
                                      "1. Longitud\n2. Latitud\n3. Precipitación\n"
                                      "Y que no tenga filas vacías al inicio.")
            return None
    
    def fusionar_datos(self, radar_da, pluviometros_gdf):
        try:
            self.log_consola("\n[3/3] Fusionando datos...")
            
            # Preparar puntos para interpolación
            xx, yy = np.meshgrid(radar_da.lon, radar_da.lat)
            puntos_radar = np.column_stack([xx.ravel(), yy.ravel()])
            valores_radar = radar_da.values.ravel()
            
            puntos_pluv = np.column_stack([
                pluviometros_gdf.longitud,
                pluviometros_gdf.latitud
            ])
            valores_pluv = pluviometros_gdf.precipitacion.values
            
            # Interpolación
            interp = RBFInterpolator(puntos_radar, valores_radar, kernel='linear')
            radar_en_pluv = interp(puntos_pluv)
            
            # Filtrar valores válidos
            mask = (~np.isnan(radar_en_pluv)) & (~np.isnan(valores_pluv))
            valores_pluv = valores_pluv[mask]
            radar_en_pluv = radar_en_pluv[mask]
            
            if len(valores_pluv) == 0:
                self.log_consola("\nAdvertencia: No hay puntos válidos para comparación")
                return radar_da
            
            # Calcular factor de corrección
            ratio = np.median(valores_pluv / radar_en_pluv)
            self.log_consola(f"\nFactor de corrección: {ratio:.2f}")
            self.log_consola(f"RMSE antes: {np.sqrt(mean_squared_error(valores_pluv, radar_en_pluv)):.2f}")
            self.log_consola(f"RMSE después: {np.sqrt(mean_squared_error(valores_pluv, radar_en_pluv * ratio)):.2f}")
            
            return radar_da * ratio
            
        except Exception as e:
            messagebox.showerror("Error", f"Error en fusión: {str(e)}")
            return None
    
    def generar_mapa(self, radar_da, pluviometros_gdf):
        try:
            self.log_consola("\nGenerando mapa...")
            
            fig = plt.figure(figsize=(12, 10))
            ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())
            
            # Configurar mapa
            ax.add_feature(cfeature.COASTLINE)
            ax.add_feature(cfeature.BORDERS, linestyle=':')
            ax.set_extent([
                radar_da.lon.min() - 0.5,
                radar_da.lon.max() + 0.5,
                radar_da.lat.min() - 0.5,
                radar_da.lat.max() + 0.5
            ])
            
            # Plot precipitación
            mesh = ax.pcolormesh(
                radar_da.lon,
                radar_da.lat,
                radar_da.values,
                cmap='YlGnBu',
                transform=ccrs.PlateCarree()
            )
            
            # Plot pluviómetros
            pluviometros_gdf.plot(
                ax=ax,
                color='red',
                markersize=50,
                alpha=0.7,
                label='Pluviómetros',
                transform=ccrs.PlateCarree()
            )
            
            # Configuración final
            plt.colorbar(mesh, label='Precipitación (mm)')
            ax.set_title('Precipitación Radar Corregida')
            ax.legend()
            
            plt.savefig(self.ruta_salida.get(), dpi=300, bbox_inches='tight')
            plt.close()
            self.log_consola(f"\nMapa guardado en: {self.ruta_salida.get()}")
            
            # Mostrar mensaje de éxito
            messagebox.showinfo("Éxito", "Proceso completado exitosamente!\nEl mapa se ha generado correctamente.")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error generando mapa: {str(e)}")
    
    def ejecutar_fusion(self):
        try:
            self.log_consola("=== INICIANDO PROCESO DE FUSIÓN ===")
            
            # Validar entradas
            if not self.ruta_radar.get():
                messagebox.showwarning("Advertencia", "Debe seleccionar un archivo de radar")
                return
                
            if not self.ruta_pluviometros.get():
                messagebox.showwarning("Advertencia", "Debe seleccionar un archivo de pluviómetros")
                return
                
            if not self.ruta_salida.get():
                messagebox.showwarning("Advertencia", "Debe especificar una ruta de salida")
                return
            
            # 1. Cargar datos
            radar = self.cargar_datos_radar()
            
            if radar is None:
                return
                
            pluv = self.cargar_datos_pluviometros()
            if pluv is None:
                return
            
            # 2. Fusionar datos
            radar_corregido = self.fusionar_datos(radar, pluv)
            if radar_corregido is None:
                return
            
            # 3. Generar mapa
            self.generar_mapa(radar_corregido, pluv)
            
            self.log_consola("\nProceso completado exitosamente!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error inesperado: {str(e)}")
            self.log_consola(f"\nERROR: {str(e)}")

if __name__ == "__main__":
    app = FusionApp()
    app.mainloop()