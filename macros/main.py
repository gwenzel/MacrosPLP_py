import ernc
import mantcen
import demanda
import barras

from utils import timeit


@timeit
def main():
    barras.main()
    demanda.main()
    mantcen.main()
    ernc.main()


if __name__ == "__main__":
    main()
