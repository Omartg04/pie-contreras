import pandas as pd
import unicodedata

def quitar_acentos(texto):
    '''Elimina los acentos y convierte el texto a mayúsculas.'''
    if pd.isna(texto):
        return texto
    texto = str(texto)
    texto = unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('utf-8')
    return texto.strip().upper()

def cargar_csv_robusto(archivo_path):
    '''Prueba automáticamente diferentes codificaciones y separadores.'''
    encodings = ['utf-8', 'latin1', 'cp1252', 'iso-8859-1']
    separadores = [',', ';', '\t', '|']
    
    for encoding in encodings:
        for sep in separadores:
            try:
                # Probar lectura con las primeras filas
                df_test = pd.read_csv(archivo_path, encoding=encoding, sep=sep, nrows=5)
                if len(df_test.columns) > 1:
                    print(f"-> Archivo detectado con éxito (Encoding: {encoding} | Separador: '{sep}')")
                    return pd.read_csv(archivo_path, encoding=encoding, sep=sep, low_memory=False)
            except Exception:
                continue
                
    return pd.read_csv(archivo_path, low_memory=False)

def filtrar_ageb(archivo_entrada, archivo_salida, entidad, municipio):
    print(f"Leyendo el archivo: {archivo_entrada} ...")
    try:
        df = cargar_csv_robusto(archivo_entrada)
        
        # Normalizar los nombres de las columnas (quitar espacios invisibles y saltos de línea)
        df.columns = df.columns.astype(str).str.replace('\n', '_').str.replace(' ', '_').str.strip()
        
        # Columnas requeridas
        columnas_requeridas = [
            'ENTIDAD', 'NOM_ENT', 'MUN', 'NOM_MUN', 'LOC', 
            'NOM_LOC', 'AGEB', 'MZA', 'P_18YMAS', 'P_18YMAS_M', 'P_18YMAS_F'
        ]
        
        # Verificar que las columnas existan
        columnas_faltantes = [col for col in columnas_requeridas if col not in df.columns]
        if columnas_faltantes:
            print(f"\nError: Faltan las siguientes columnas en el archivo original: {columnas_faltantes}")
            print("Las columnas detectadas en tu archivo son:")
            print(list(df.columns))
            return
            
        # Filtrar solo las columnas deseadas
        df = df[columnas_requeridas]

        # Normalizar la información (quitar acentos, convertir a mayúsculas, quitar espacios)
        # Esto soluciona problemas como 'Tehuacán' vs 'TEHUACAN' vs 'Tehuacan '
        df['NOM_ENT_NORM'] = df['NOM_ENT'].apply(quitar_acentos)
        df['NOM_MUN_NORM'] = df['NOM_MUN'].apply(quitar_acentos)

        # Normalizar los parámetros de búsqueda
        entidad_str = quitar_acentos(entidad)
        municipio_str = quitar_acentos(municipio)
        
        print(f"Aplicando filtro -> Entidad: '{entidad_str}' | Municipio: '{municipio_str}'")
        df_filtrado = df[(df['NOM_ENT_NORM'] == entidad_str) & (df['NOM_MUN_NORM'] == municipio_str)].copy()

        if df_filtrado.empty:
            print("\nAdvertencia: No se encontraron registros con esos criterios.")
            print(f"Muestra de Entidades disponibles: {df['NOM_ENT'].dropna().unique()[:5]}")
            print(f"Muestra de Municipios disponibles: {df['NOM_MUN'].dropna().unique()[:5]}")
        else:
            # Eliminar las columnas auxiliares de normalización antes de guardar
            df_final = df_filtrado.drop(columns=['NOM_ENT_NORM', 'NOM_MUN_NORM'])

            # Guardar el archivo filtrado
            df_final.to_csv(archivo_salida, index=False, encoding='utf-8-sig')
            
            print(f"\n¡Éxito! Archivo guardado como: '{archivo_salida}'")
            print(f"Total de registros filtrados: {len(df_final)}")

    except FileNotFoundError:
        print(f"Error: No se encontró el archivo '{archivo_entrada}'. Verifica que esté en la misma carpeta.")
    except Exception as e:
        print(f"Ha ocurrido un error inesperado: {e}")

if __name__ == "__main__":
    ARCHIVO_ENTRADA = "conjunto_de_datos_ageb_urbana_09_cpv2020.csv"
    ARCHIVO_SALIDA = "AGEB_Filtrado_CDMX_MContreras.csv"
    
    ENTIDAD_A_FILTRAR = "Ciudad de Mexico"
    MUNICIPIO_A_FILTRAR = "La Magdalena Contreras"

    filtrar_ageb(ARCHIVO_ENTRADA, ARCHIVO_SALIDA, ENTIDAD_A_FILTRAR, MUNICIPIO_A_FILTRAR)