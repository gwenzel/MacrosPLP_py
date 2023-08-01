import macros.ernc
import macros.mantcen
import macros.demanda
import macros.barras
import macros.filter_files

from utils.utils import timeit


@timeit
def main():
    
    macros.filter_files.main()
    macros.barras.main()
    macros.demanda.main()
    macros.mantcen.main()
    macros.ernc.main()


if __name__ == "__main__":
    main()
