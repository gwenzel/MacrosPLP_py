# MACHICURA

def CotEST_MACHICURA(Volumen):
    a0 = 253.9619
    a1 = 0.243919
    a2 = -0.006546
    a3 = 0.000503
    a4 = -0.000022
    a5 = 0.000000382368

    CotEST_MACHICURA = a0 + (a1 * Volumen) + (a2 * Volumen ** 2) +\
        (a3 * Volumen ** 3) + (a4 * Volumen ** 4) + (a5 * Volumen ** 5)
    return CotEST_MACHICURA


def dVol_MACHICURA(Cota):
    a1 = 3.869693
    a2 = 0.854351
    a3 = -0.346473
    a4 = 0.080443
    a5 = -0.007131
    DCota = Cota - 254#

    return a1 + 2 * (a2 * DCota) + 3 * (a3 * DCota ** 2) +\
        4 * (a4 * DCota ** 3) + 5 * (a5 * DCota ** 4)


def Vol_MACHICURA(Cota):
    a0 = 0.220082
    a1 = 3.869693
    a2 = 0.854351
    a3 = -0.346473
    a4 = 0.080443
    a5 = -0.007131

    if Cota < 254.5:
        return 0
    else:
        DCota = Cota - 254#
        return a0 + (a1 * DCota) + (a2 * DCota ** 2) +\
            (a3 * DCota ** 3) + (a4 * DCota ** 4) + (a5 * DCota ** 5)


def Cot_MACHICURA(Volumen):
    Error_Cota = 0.005
    Num_de_Iter = 10
    Iter = 0
    CotIni = CotEST_MACHICURA(Volumen)

    while True:
        Iter += 1
        CotFin = CotIni - (Vol_MACHICURA(CotIni) - Volumen) /\
            dVol_MACHICURA(CotIni)
        CondERR = abs(CotFin - CotIni) < Error_Cota
        CondITE = Iter > Num_de_Iter
        CotIni = CotFin

        if CondERR or CondITE:
            break

    return CotFin


def Pot_MACHICURA(Caudal):
    Potmax = 95
    Pot_MACHICURA = Caudal * (0.358787 - 0.0002346443 * Caudal +
                              0.0000003703 * Caudal ** 2)

    if Pot_MACHICURA > Potmax:
        return Potmax
    else:
        return Pot_MACHICURA
