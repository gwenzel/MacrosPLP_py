import pandas as pd

filename = r"C:\Users\BH5873\OneDrive - ENGIE\Bureau\plpmanli_v9.dat"

list_of_lines = []
dict_lines_values = {}
list_of_dfs = []

with open(filename) as f:
    lines = f.readlines()
    for idx, line in enumerate(lines):
        if '# Nombre de la lineas\n' in line:
            current_line = lines[idx + 1].strip().replace("'", "")
            print(current_line)
            list_of_lines.append(current_line)
        if '# Bloque         PotMaxAB   PotMaxBA     Operativa\n' in line:
            lines_with_zero = int(lines[idx-1])
            text_lines = lines[idx+1:idx + 1 + lines_with_zero]
            value_lines = [list(line.split()) for line in text_lines]
            dict_lines_values[current_line] = value_lines
            df = pd.DataFrame(
                dict_lines_values[current_line],
                columns=['Etapa', 'AB', 'BA', 'Flag'])
            df['Line'] = current_line
            list_of_dfs.append(df)
    df_all = pd.concat(list_of_dfs)
    df_all['Etapa'] = df_all['Etapa'].astype(int)
    df_all['AB'] = df_all['AB'].astype(float)
    df_all['BA'] = df_all['BA'].astype(float)

    df_all.to_csv('v9_all.csv')

    df_all_pivot_ab = df_all.pivot(
        index='Etapa', columns='Line', values=['AB']).fillna(1)
    df_all_pivot_ba = df_all.pivot(
        index='Etapa', columns='Line', values=['BA']).fillna(1)
    df_all_pivot_flag = df_all.pivot(
        index='Etapa', columns='Line', values=['Flag']).fillna('T')
    df_all_pivot_ab.to_csv('v9_ab.csv')
    df_all_pivot_ba.to_csv('v9_ba.csv')
    df_all_pivot_flag.to_csv('v9_flag.csv')
