plp_commands = [
   {'description': 'Dat Files + Etapa2Dates',
    'command': 'python -c "from macros.filter_files import main; main()"',
    'parallel': False},
   {'description': 'Demand',
    'command': 'python -c "from macros.dem import main; main()"',
    'parallel': True},
   {'description': 'Inflow',
    'command': 'python -c "from macros.inflows import main; main(plp_enable=True, plx_enable=False)"',
    'parallel': True},
   {'description': 'Variable Cost',
    'command': 'python -c "from macros.cvar import main; main()"',
    'parallel': True},
   {'description': 'Buses',
    'command': 'python -c "from macros.bar import main; main()"',
    'parallel': False},
   {'description': 'Blocks',
    'command': 'python -c "from macros.blo import main; main()"',
    'parallel': False},
   {'description': 'Lines',
    'command': 'python -c "from macros.lin import main; main()"',
    'parallel': False},
   {'description': 'Lines Maintenance (In/Out)',
    'command': 'python -c "from macros.manli import main; main()"',
    'parallel': False},
   {'description': 'Lines Maintenance (Exp)',
    'command': 'python -c "from macros.manlix import main; main()"',
    'parallel': False},
   {'description': 'Generators',
    'command': 'python -c "from macros.cen import main; main()"',
    'parallel': False},
   {'description': 'Generators Maintenance (Exp)',
    'command': 'python -c "from macros.mantcen import main; main()"',
    'parallel': False},
   {'description': 'Generators ERNC',
    'command': 'python -c "from macros.ernc import main; main()"',
    'parallel': False},
   {'description': 'GNL',
    'command': 'python -c "from macros.PLPGNL import main; main()"',
    'parallel': False},
   {'description': 'Other Commands',
    'command': 'python -c "from macros.mat import main; main();'
                          'from macros.PLPCENPMAX import main; main();'
                          'from macros.PLPCENRE import main; main(); '
                          'from macros.PLPDEB import main; main(); '
                          'from macros.PLPEXTRAC import main; main(); '
                          'from macros.PLPFILTEMB import main; main(); '
                          'from macros.PLPIDSIMAPE_MANUAL import main; main();'
                          'from macros.PLPLAJA_M import main; main(); '
                          'from macros.PLPMANEM_ETA import main; main(); '
                          'from macros.PLPMAULE_N import main; main(); '
                          'from macros.PLPMINEMBH import main; main(); '
                          'from macros.PLPPLEM1 import main; main(); '
                          'from macros.PLPPLEM2 import main; main(); '
                          'from macros.PLPRALCO import main; main(); '
                          'from macros.PLPVREBEMB import main; main()"',
    'parallel': False},
]

plexos_commands = [
    {'description': 'Command 1',
     'command': 'echo Command 1 executed',
     'parallel': True},
    {'description': 'Command 2',
     'command': 'echo Command 2 executed',
     'parallel': False},
    {'description': 'Command 3',
     'command': 'echo Command 3 executed',
     'parallel': False,
     }
]
