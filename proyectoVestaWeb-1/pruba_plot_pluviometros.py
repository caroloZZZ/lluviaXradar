import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from matplotlib.patches import Rectangle

def cargar_datos_pluviometros(ruta_archivo):
    """Carga y procesa los datos de pluviómetros desde un archivo Excel"""
    try:
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
        
        print(f"\nDatos pluviómetros cargados: {len(gdf)} estaciones")
        return gdf
            
    except Exception as e:
        print(f"Error cargando pluviómetros: {str(e)}")
        return None

def plotear_mapa_camaguey(gdf, titulo="Precipitación en Pluviómetros"):
    try:
        fig = plt.figure(figsize=(12, 10))
        ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())
        
        # Define los límites del mapa manualmente
        ax.set_extent([-78.8, -76.8, 20.5, 22.0])  # Ajusta según Camagüey

        # -- Intento 1: Usar shapefiles locales --
        try:
            # Cargar shapefile de Cuba
            cuba = gpd.read_file('cu_shp/cuba.shp')
            cuba.boundary.plot(ax=ax, linewidth=1, edgecolor='gray')
            
            # Intentar resaltar Camagüey (prueba con diferentes nombres de campo)
            nombres_posibles = ['NAME_1', 'name_1', 'NAM', 'nombre', 'provincia']
            encontrado = False
            
            for nombre in nombres_posibles:
                if nombre in cuba.columns:
                    try:
                        camaguey = cuba[cuba[nombre].str.contains('Camagüey|Camaguey', case=False, regex=True)]
                        if not camaguey.empty:
                            camaguey.plot(ax=ax, color='none', edgecolor='red', linewidth=2)
                            encontrado = True
                            break
                    except:
                        continue
            
            if not encontrado:
                print("No se pudo identificar Camagüey en el shapefile")
                # Dibujar un rectángulo aproximado para Camagüey
                ax.add_patch(Rectangle((-78.5, 20.7), 1.7, 1.3, 
                                    fill=False, color='red', linewidth=2, 
                                    transform=ccrs.PlateCarree()))
                
        except Exception as e:
            print(f"Error con shapefile: {e}")
            # -- Opción 2: Dibujar características básicas --
            ax.add_feature(cfeature.COASTLINE, linewidth=0.5)
            ax.add_feature(cfeature.BORDERS, linestyle=':', linewidth=0.5)
            # Dibujar un rectángulo aproximado para Camagüey
            ax.add_patch(Rectangle((-78.5, 20.7), 1.7, 1.3, 
                                fill=False, color='red', linewidth=2, 
                                transform=ccrs.PlateCarree()))

        # Plotear pluviómetros
        scatter = ax.scatter(
            gdf['longitud'],
            gdf['latitud'],
            c=gdf['precipitacion'],
            cmap='YlGnBu',
            s=100,
            edgecolor='black',
            transform=ccrs.PlateCarree()
        )

        plt.colorbar(scatter, label='Precipitación (mm)')
        ax.set_title(titulo)
        ax.gridlines(draw_labels=True)
        plt.show()

    except Exception as e:
        print(f"Error generando mapa: {e}")

# Uso del código
ruta_pluviometros = "lluvia.xls"
gdf_pluv = cargar_datos_pluviometros(ruta_pluviometros)

if gdf_pluv is not None:
    plotear_mapa_camaguey(gdf_pluv)