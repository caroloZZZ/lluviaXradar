import matplotlib
matplotlib.use('Agg')  # Backend no interactivo
import matplotlib.pyplot as plt
import xarray as xr
import numpy as np
import cartopy.crs as ccrs
import geopandas as gpd

def cargar_datos_radar(ruta_archivo, centro_lon=-77.849, centro_lat=21.4227, resolucion_km=1.0):
    """Carga y procesa los datos de radar desde un archivo NetCDF"""
    try:
        print("\nCargando radar...")
        ds = xr.open_dataset(ruta_archivo)
        
        # Detectar variable de precipitación (ajustado para tu archivo)
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
        
        print("\nCoordenadas generadas:")
        print(f"Longitud: {lon.min():.4f} a {lon.max():.4f}")
        print(f"Latitud: {lat.min():.4f} a {lat.max():.4f}")
        
        return da
            
    except Exception as e:
        print(f"Error cargando radar: {str(e)}")
        return None

def plotear_radar_camaguey(da_radar, output_file='precipitacion_camaguey.png'):
    """Guarda el mapa de radar en un archivo"""
    try:
        fig = plt.figure(figsize=(12, 10))
        ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())
        
        # Configuración del mapa para Camagüey
        ax.set_extent([-78.8, -76.8, 20.5, 22.0])  # Ajustado para Camagüey

        # -- Opción 1: Usar el shapefile de Cuba para el contorno --
        try:
            cuba = gpd.read_file('cu_shp/cuba.shp')
            cuba.boundary.plot(ax=ax, linewidth=1, edgecolor='gray')
            
            # Resaltar Camagüey (ajusta 'NAME_1' según tu shapefile)
            camaguey = cuba[cuba['NAME_1'] == 'Camagüey']
            camaguey.plot(ax=ax, color='none', edgecolor='red', linewidth=2)
        except Exception as e:
            print(f"Error con shapefile: {e}")
            # -- Opción 2: Dibujar la costa manualmente (si no tienes shapefile) --
            ax.coastlines(resolution='10m', linewidth=0.5)  # Usa una resolución baja

        # Plotear datos de radar
        mesh = ax.pcolormesh(
            da_radar.lon,
            da_radar.lat,
            da_radar.values,
            cmap='YlGnBu',
            transform=ccrs.PlateCarree(),
            shading='auto'
        )
        
        # Añadir barra de color y título
        cbar = plt.colorbar(mesh, label='Precipitación (mm)', extend='max')
        ax.set_title("Precipitación Radar - Camagüey")
        
        # Añadir gridlines
        gl = ax.gridlines(draw_labels=True, linestyle='--', alpha=0.5)
        gl.top_labels = False
        gl.right_labels = False
        
        # Guardar en archivo
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"\nMapa guardado exitosamente como: {output_file}")
        
    except Exception as e:
        print(f"Error generando mapa: {str(e)}")

# Ejecución principal
if __name__ == "__main__":
    ruta_radar = "lluvia8junio.nc"
    da_radar = cargar_datos_radar(ruta_radar)
    
    if da_radar is not None:
        plotear_radar_camaguey(da_radar)