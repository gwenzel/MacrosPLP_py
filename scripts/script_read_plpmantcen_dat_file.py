import pandas as pd

filename = r"C:\Users\BH5873\OneDrive - ENGIE\Bureau\plpmance_ini.dat"

list_of_cen = []
dict_cen_values = {}
list_of_dfs = []

with open(filename) as f:
    cen = f.readlines()
    for idx, line in enumerate(cen):
        if '# Nombre de la central\n' in line:
            current_cen = cen[idx + 1].strip().replace("'", "")
            print(current_cen)
            list_of_cen.append(current_cen)
        if '#   Mes    Bloque  NIntPot   PotMin   PotMax\n' in line:
            cen_with_values = int(cen[idx-1].split()[0])
            text_cen = cen[idx + 1:idx + 1 + cen_with_values]
            value_cen = [list(line.split()) for line in text_cen]
            dict_cen_values[current_cen] = value_cen
            df = pd.DataFrame(
                dict_cen_values[current_cen],
                columns=['Mes', 'Bloque', 'NIntPot', 'PotMin', 'PotMax'])
            df['Cen'] = current_cen
            list_of_dfs.append(df)
df_all = pd.concat(list_of_dfs)
df_all['Mes'] = df_all['Mes'].astype(int)
df_all['Bloque'] = df_all['Bloque'].astype(int)
df_all['NIntPot'] = df_all['NIntPot'].astype(int)
df_all['PotMin'] = df_all['PotMin'].astype(float)
df_all['PotMax'] = df_all['PotMax'].astype(float)

# df_all.to_csv('df_all.csv')

#df_all_pivot_pmin = df_all.pivot_table(
#    index='Bloque', columns='Cen', values=['PotMin'])
df_all_pivot_pmax = df_all.pivot_table(
    index='Bloque', columns='Cen', values=['PotMax'])

#df_all_pivot_pmin.to_csv(r"C:\Users\BH5873\OneDrive - ENGIE\Bureau\pmin_v11.csv")
df_all_pivot_pmax.to_csv(
    r"C:\Users\BH5873\OneDrive - ENGIE\Bureau\df_pmax_plpmance_ini.csv")
