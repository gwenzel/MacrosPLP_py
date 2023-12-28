import pandas as pd

filename = r"C:\Users\BH5873\ENGIE\Equipo Estudios - Biblioteca Equipo Estudios\08. Modelos\202311 - MejorasPLP\comparaciones\costo_var\plpcosce_new.dat"

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
        if '# Mes   Etapa    CosVar\n' in line:
            cen_with_values = int(cen[idx-1].split()[0])
            text_cen = cen[idx + 1:idx + 1 + cen_with_values]
            value_cen = [list(line.split()) for line in text_cen]
            dict_cen_values[current_cen] = value_cen
            df = pd.DataFrame(
                dict_cen_values[current_cen],
                columns=['Mes', 'Etapa', 'CosVar'])
            df['Cen'] = current_cen
            list_of_dfs.append(df)
df_all = pd.concat(list_of_dfs)
df_all['Mes'] = df_all['Mes'].astype(int)
df_all['Etapa'] = df_all['Etapa'].astype(int)
df_all['CosVar'] = df_all['CosVar'].astype(float)


df_all_pivot_cvar = df_all.pivot(
    index='Etapa', columns='Cen', values=['CosVar'])

df_all_pivot_cvar.to_csv(r"C:\Users\BH5873\ENGIE\Equipo Estudios - Biblioteca Equipo Estudios\08. Modelos\202311 - MejorasPLP\comparaciones\costo_var\cvar_new.csv")
