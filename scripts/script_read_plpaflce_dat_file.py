import pandas as pd

filename = r"C:\Users\BH5873\ENGIE\Equipo Estudios - Biblioteca Equipo Estudios\08. Modelos\202311 - MejorasPLP\comparaciones BE Feb 24\afluentes\plpaflce_exp_afl_1.dat"

list_of_cen = []
dict_cen_values = {}
list_of_dfs = []

with open(filename) as f:
    lines = f.readlines()
    for idx, line in enumerate(lines):
        if "# Nombre de la central" in line:
            current_cen = lines[idx + 1].strip().replace("'", "")
            print(current_cen)
            list_of_cen.append(current_cen)
        if "# Mes   Bloque    Caudal" in line:
            lines_with_values = int(lines[idx-1].split()[0])
            text_cen = lines[idx + 1:idx + 1 + lines_with_values]
            value_cen = [list(line.split()) for line in text_cen]
            dict_cen_values[current_cen] = value_cen
            columns = ['Mes', 'Bloque']
            columns += ['H%s' % i for i in range(1, 21)]
            df = pd.DataFrame(
                dict_cen_values[current_cen],
                columns=columns)
            df['Cen'] = current_cen
            list_of_dfs.append(df)

df_all = pd.concat(list_of_dfs)
df_all['Mes'] = df_all['Mes'].astype(int)
df_all['Bloque'] = df_all['Bloque'].astype(int)


df_all.to_csv(r"C:\Users\BH5873\ENGIE\Equipo Estudios - Biblioteca Equipo Estudios\08. Modelos\202311 - MejorasPLP\comparaciones BE Feb 24\afluentes\df_plpaflce_exp_afl_1.csv")
