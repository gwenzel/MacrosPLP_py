import pandas as pd

filename = r"C:\Users\BH5873\OneDrive - ENGIE\Bureau\plpdem_119.dat"

list_of_items = []
dict_item2value = {}
list_of_dfs = []

with open(filename) as f:
    file_lines = f.readlines()
    for idx, line in enumerate(file_lines):
        if '# Nombre de la Barra\n' in line:
            current_item = file_lines[idx + 1].strip().replace("'", "")
            print(current_item)
            list_of_items.append(current_item)
        if '# Mes  Etapa   Demanda\n' in line:
            n_items = int(file_lines[idx-1].split()[0])
            text_item = file_lines[idx + 1:idx + 1 + n_items]
            value_item = [list(line.split()) for line in text_item]
            dict_item2value[current_item] = value_item
            df = pd.DataFrame(
                dict_item2value[current_item],
                columns=['Mes', 'Etapa', 'Demanda'])
            df['Dem'] = current_item
            list_of_dfs.append(df)
df_all = pd.concat(list_of_dfs)
df_all['Mes'] = df_all['Mes'].astype(int)
df_all['Etapa'] = df_all['Etapa'].astype(int)
df_all['Demanda'] = df_all['Demanda'].astype(float)


df_all_pivot_dem = df_all.pivot_table(
    index='Etapa', columns='Dem', values=['Demanda'])

df_all_pivot_dem.to_csv(r"C:\Users\BH5873\OneDrive - ENGIE\Bureau\plpdem_119.csv")
