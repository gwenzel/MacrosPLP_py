import pygraphviz as pgv
import sys


def read_busbar_data(ruta):
    file = open(ruta + "\\plpbar_full.dat", "r")
    lineas = file.readlines()

    busbar_data = {
        'busbar_index': [],
        'busbar_name': [],
        'busbar_vol': [],
        'busbar_load': [],
        'busbar_iny': [],
    }

    nro_lines = len(lineas)

    for line in range(4, nro_lines, 1):
        words = lineas[line].split()
        busbar_data['busbar_index'].append(int(words[0]))
        busbar_data['busbar_name'].append(str(words[1]).replace("'",""))
        busbar_data['busbar_vol'].append(int(words[2]))
        busbar_data['busbar_load'].append(int(words[3]))
        busbar_data['busbar_iny'].append(int(words[4]))

    # Close opened file
    file.close()
    return busbar_data


def read_line_data(ruta, year):
    file = open(ruta + "\\plpcnfli_" + year + ".dat", "r")
    lineas = file.readlines()
    lines_data = {
        'lineas_name': [],
        'lineas_flujo': [],
        'lineas_busbarA': [],
        'lineas_busbarB': [],
        'lineas_tension': [],
        'lineas_estado': []
    }

    nro_lines = len(lineas)
    for line in range(5, nro_lines, 1):
        words = lineas[line].split()
        lines_data['lineas_name'].append(words[0])
        lines_data['lineas_flujo'].append(words[1])
        lines_data['lineas_busbarA'].append(words[3])
        lines_data['lineas_busbarB'].append(words[4])
        lines_data['lineas_tension'].append(words[5])
        lines_data['lineas_estado'].append(words[10])
    #    lineas_area.append(words[11])
    # Close opend file
    file.close()

    return lines_data


def build_graph(busbar_data, lines_data, ruta, year, itension):
    tension = itension + ".0"
    # GRAFICO
    Gpgv=pgv.AGraph(strict=False,
                    directed=False,
                    splines='ortho',
                    ranksep='1.5',
                    maxiter=300,
                    rankdir='TB',
                    overlap='false',
                    overlap_shrink='false')
    Gpgv.node_attr['shape'] = 'rect'
    Gpgv.node_attr['style'] = 'filled'
    Gpgv.node_attr['color'] = 'grey96'
    Gpgv.node_attr['fillcolor'] = 'grey96'
    Gpgv.node_attr['fontsize'] = 9
    Gpgv.node_attr['fontname'] = "Helvetica"

    for lin in range(0, len(lines_data['lineas_name'])):
        pw = 1
        estilo = 'solid, bold'

        if lines_data['lineas_tension'][lin] == '500.0':
            col = 'blue'
            pw = 2
        elif lines_data['lineas_tension'][lin] == '230.0':
            col = 'green'
        elif lines_data['lineas_tension'][lin] == '220.0':
            col = 'green'
        elif lines_data['lineas_tension'][lin] == '154.0':
            col = 'magenta'
        elif lines_data['lineas_tension'][lin] == '115.0':
            col = 'orange'
        elif lines_data['lineas_tension'][lin] == '110.0':
            col = 'orange'
        elif lines_data['lineas_tension'][lin] == '600.0':
            col = 'red'
            pw = 2
        else:
            col = 'black'

        if (lines_data['lineas_flujo'][lin] == '0.0') or (lines_data[
                'lineas_estado'][lin] == 'F'):
            estilo = 'dashed'
            pw = 0.5

        if (tension == '0.0') or (lines_data['lineas_tension'][lin] == tension):
            bus_indexA = int(lines_data['lineas_busbarA'][lin])-1
            bus_indexB = int(lines_data['lineas_busbarB'][lin])-1

            flujo = str(lines_data['lineas_flujo'][lin]).split(".")

            Gpgv.add_edge(busbar_data['busbar_name'][bus_indexA],
                          busbar_data['busbar_name'][bus_indexB],
                          headlabel=flujo[0],
                          forcelabels="true",
                          labelfontsize=9,
                          labelfontname="Helvetica",
                          color=col,
                          style=estilo,
                          penwidth=pw)

            n = Gpgv.get_node(busbar_data['busbar_name'][bus_indexA])
            n.attr['color'] = col

            n = Gpgv.get_node(busbar_data['busbar_name'][bus_indexB])
            n.attr['color'] = col

            if busbar_data['busbar_load'][bus_indexA] == 1:
                n = Gpgv.get_node(busbar_data['busbar_name'][bus_indexA])
                n.attr['fillcolor'] = 'pink'

            if busbar_data['busbar_load'][bus_indexB] == 1:
                n = Gpgv.get_node(busbar_data['busbar_name'][bus_indexB])
                n.attr['fillcolor'] = 'pink'

            if busbar_data['busbar_iny'][bus_indexA] == 1:
                n = Gpgv.get_node(busbar_data['busbar_name'][bus_indexA])
                n.attr['shape'] = 'octagon'

            if busbar_data['busbar_iny'][bus_indexB] == 1:
                n = Gpgv.get_node(busbar_data['busbar_name'][bus_indexB])
                n.attr['shape'] = 'octagon'

    # Gpgv.layout() # default to neato
    Gpgv.layout(prog='dot') # use dot
    Gpgv.draw(ruta + '\\plpcnfli_' + year + '_' + itension + '_diagram.png')


def main():

    # OBTENER ARGS
    ruta = sys.argv[1]
    year = sys.argv[2]
    itension = sys.argv[3]

    # Leer barras
    busbar_data = read_busbar_data(ruta)
    lineas_data = read_line_data(ruta, year)

    build_graph(busbar_data, lineas_data, ruta, year, itension)


if __name__ == "__main__":
    main()
