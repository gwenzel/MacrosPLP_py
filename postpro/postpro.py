import os
import pandas as pd
import numpy as np

# Get working directory and create required folders
location = os.getcwd()
path_dat = os.path.join(location, "Dat")
path_sal = os.path.join(location, "Sal")
sal_folders = os.listdir(path_sal)

research_name = os.path.basename(location)
path_out = os.path.join(location, research_name)
if not os.path.exists(path_out):
    os.mkdir(path_out)

# Load plpetapas and block2day data
plpeta_name = "plpetapas.csv"
plpb2d_name = "block2day.csv"

plpetapas = pd.read_csv(os.path.join(path_dat, plpeta_name))
plpetapas['Tasa'] = np.power(1.1, np.ceil(plpetapas['Etapa'] / 12 - 1) / 12)

block2day = pd.read_csv(os.path.join(path_dat, plpb2d_name))
block2day = block2day.rename(columns={
    'jan': '1', 'feb': '2', 'mar': '3', 'apr': '4',
    'may': '5', 'jun': '6', 'jul': '7', 'aug': '8',
    'sep': '9', 'oct': '10', 'nov': '11', 'dec': '12'
})
block2day = block2day[['Hour2Blo'] + [f'{i}' for i in range(1, 13)]]
block2day = block2day.melt(id_vars='Hour2Blo', var_name='Month', value_name='Block')
block2day['Month'] = block2day['Month'].astype(int)
block2day['Hour'] = block2day['Hour2Blo'].astype(int)
block2day = block2day.drop(columns='Hour2Blo')

block_len = block2day.groupby(['Month', 'Block']).size().reset_index()
block_len.rename(columns={0: 'Block_Len'}, inplace=True)

blo_eta = pd.merge(plpetapas, block_len, on=['Month', 'Block'], how='left')

# Get the case data
case_id = 1
case_name = sal_folders[case_id]
path_case = os.path.join(path_sal, case_name)
path_out = os.path.join(location, research_name, case_name)
if not os.path.exists(path_out):
    os.mkdir(path_out)

# Load bar data
bar_data = pd.read_csv(os.path.join(path_case, "plpbar.csv"))
bar_data = bar_data[bar_data['Hidro'] != 'MEDIA']
bar_data = bar_data.rename(columns={'Hidro':
