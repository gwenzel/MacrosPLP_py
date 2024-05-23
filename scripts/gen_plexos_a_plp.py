# Ejemplo de pasar archivo de despacho plexos a plp

import pandas as pd
import math
import time
from pathlib import Path
from functools import wraps

# Definir directorio de entrada
input_path = Path(r"C:\Users\BH5873\OneDrive - ENGIE\Bureau")
# Definir archivo de entrada
input_csv_file = input_path / "ejemplo_despacho_plexos.csv"
# Definir archivo de salida
output_csv_file = input_path / "ejemplo_despacho_plp.csv"
# Mapeo de horas a bloques
hour_to_block_dict = {i: math.ceil(i/2) for i in range(1, 25)}


def timeit(func):
    '''
    Wrapper to measure time
    '''
    @wraps(func)
    def timeit_wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        total_time = end_time - start_time
        print(f'Function {func.__name__} Took {total_time:.4f} seconds')
        return result
    return timeit_wrapper


@timeit
def read_plexos_csv(input_csv_file):
    # Leer csv y retornar DataFrame
    df_input = pd.read_csv(input_csv_file)
    return df_input


@timeit
def process_df(df_input):
    df_processed = df_input.copy()
    # Agregar mapeo a bloques
    df_processed['Block'] = df_processed['Hour'].map(hour_to_block_dict)
    # Definir índices y botar DATETIME (dejar solo valores sin índice)
    new_index = ['Year', 'Month', 'Day', 'Hour', 'Block']
    df_processed = df_processed.set_index(new_index)
    df_processed = df_processed.drop(columns=['DATETIME'])
    # Usar melt para hacer unpivot, y renombrar columnas Gen y Value
    df_processed = pd.melt(df_processed.reset_index(),
                           id_vars=new_index,
                           value_vars=df_processed.columns,
                           var_name='Gen',
                           value_name='Value')
    return df_processed


@timeit
def group_df(df_processed):
    # Definir columnas a ser agregadas
    cols_to_group = ['Year', 'Month', 'Block', 'Gen']
    df_grouped = df_processed.copy()
    df_grouped = df_processed.groupby(cols_to_group).sum().reset_index()
    # Botar columnas sobrantes
    df_grouped = df_grouped.drop(columns=['Day', 'Hour'])
    return df_grouped


@timeit
def main():
    print('--Iniciando proceso de conversión de despacho Plexos a PLP')
    print('Archivo de entrada:', input_csv_file)
    print('Leyendo archivo de entrada')
    df_input = read_plexos_csv(input_csv_file)
    print('Procesando datos')
    df_processed = process_df(df_input)
    print('Agrupando datos')
    df_grouped = group_df(df_processed)
    print('Imprimiendo resultados')
    df_grouped.to_csv(output_csv_file, index=False)
    print('Archivo de salida:', output_csv_file)
    print('--Proceso terminado')


if __name__ == "__main__":
    main()
