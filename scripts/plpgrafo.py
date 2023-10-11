__author__ = 'MPro'

import pygraphviz as pgv
import sys
#import networkx as nx
#import matplotlib.pyplot as plt



#OBTENER BARRAS
#/Users/MPro/Dropbox/AMEBA/diagram
#ruta="/Users/MPro/Downloads/"
ruta="./"
file = open(ruta +"plpbar_full.dat", "r")

lineas = file.readlines();

busbar_index=[];
busbar_name=[];
busbar_vol=[];
busbar_load=[];
busbar_iny=[];

nro_lines =len(lineas)


for line in range(4,nro_lines,1):
    words = lineas[line].split()
    busbar_index.append(int(words[0]))
    busbar_name.append(str(words[1]).replace("'",""))
    busbar_vol.append(int(words[2]))
    busbar_load.append(int(words[3]))
    busbar_iny.append(int(words[4]))
	
# Close opend file
file.close()

#OBTENER ARGS

filename=sys.argv[1]
itension=sys.argv[2]
tension=itension+".0"

ext="png"

#OBTENER LINEAS

file = open(ruta+filename+".dat", "r")

lineas = file.readlines();

lineas_name=[];
lineas_flujo=[];
lineas_busbarA=[];
lineas_busbarB=[];
lineas_tension=[];
lineas_estado=[];
#lineas_area=[];

nro_lines =len(lineas)


for line in range(5,nro_lines,1):

    words = lineas[line].split()
    lineas_name.append(words[0])
    lineas_flujo.append(words[1])

    lineas_busbarA.append(words[3])
    lineas_busbarB.append(words[4])
    lineas_tension.append(words[5])
    lineas_estado.append(words[10])
#    lineas_area.append(words[11])

# Close opend file
file.close()


# GRAFICO
Gpgv=pgv.AGraph(strict=False,directed=False,splines='ortho',ranksep='1.5',maxiter=300,rankdir='TB',overlap='false',overlap_shrink='false')
Gpgv.node_attr['shape']='rect'
Gpgv.node_attr['style']='filled'
Gpgv.node_attr['color']='grey96'
Gpgv.node_attr['fillcolor']='grey96'
Gpgv.node_attr['fontsize']=9
Gpgv.node_attr['fontname']="Helvetica"

for lin in range(0,len(lineas_name)):
    pw = 1
    estilo = 'solid, bold'

    if lineas_tension[lin] == '500.0':
        col = 'blue'
        pw = 2
    elif lineas_tension[lin] == '230.0':
        col = 'green'
    elif lineas_tension[lin] == '220.0':
        col = 'green'
    elif lineas_tension[lin] == '154.0':
        col = 'magenta'
    elif lineas_tension[lin] == '115.0':
        col = 'orange'
    elif lineas_tension[lin] == '110.0':
        col = 'orange'
    elif lineas_tension[lin] == '600.0':
        col = 'red'
        pw = 2
    else:
        col = 'black'

    if (lineas_flujo[lin] == '0.0') or (lineas_estado[lin] == 'F'):
        estilo = 'dashed'
        pw = 0.5
            
    if (tension == '0.0') or (lineas_tension[lin] == tension):
        bus_indexA = int(lineas_busbarA[lin])-1
        bus_indexB = int(lineas_busbarB[lin])-1

        flujo = str(lineas_flujo[lin]).split(".")

        Gpgv.add_edge( busbar_name[bus_indexA],
                       busbar_name[bus_indexB],
                       headlabel=flujo[0],
                       forcelabels="true",
                       labelfontsize=9,
                       labelfontname="Helvetica",
                       color = col, style = estilo, penwidth=pw)

        n=Gpgv.get_node(busbar_name[bus_indexA])
        n.attr['color']=col

        n=Gpgv.get_node(busbar_name[bus_indexB])
        n.attr['color']=col
            
        if busbar_load[bus_indexA] == 1:
            n=Gpgv.get_node(busbar_name[bus_indexA])
            n.attr['fillcolor']='pink'

        if busbar_load[bus_indexB] == 1:
            n=Gpgv.get_node(busbar_name[bus_indexB])
            n.attr['fillcolor']='pink'

        if busbar_iny[bus_indexA] == 1:
            n=Gpgv.get_node(busbar_name[bus_indexA])
            n.attr['shape']='octagon'

        if busbar_iny[bus_indexB] == 1:
            n=Gpgv.get_node(busbar_name[bus_indexB])
            n.attr['shape']='octagon'

        
#Gpgv.layout() # default to neato
Gpgv.layout(prog='dot') # use dot
Gpgv.draw(filename+'_'+itension+'_diagram.'+ext)

