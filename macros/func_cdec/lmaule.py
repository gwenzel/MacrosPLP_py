# LAGUNA DEL MAULE

def CotEST_LMAULE(Volumen):
    a0 = 3.25854232403699E-03
    a1 = 0.025405983908303
    a2 = -1.35727677749965E-05
    a3 = 2.49264011608606E-08
    a4 = -3.23135007234829E-11
    a5 = 2.43385209187998E-14
    a6 = -9.6847814254483E-18
    a7 = 1.57390037611625E-21

    CotEST_LMAULE = a0 + (a1 * Volumen) + (a2 * Volumen ** 2) +\
        (a3 * Volumen ** 3) + (a4 * Volumen ** 4) + (a5 * Volumen ** 5)
    CotEST_LMAULE += a6 * Volumen ** 6 + a7 * Volumen ** 7
    CotEST_LMAULE += 2152.135
    CotEST_LMAULE = min(CotEST_LMAULE, 2180.3)
    return CotEST_LMAULE


def dVol_LMAULE(Cota):
    DCota = Cota - 2152.135
    # a0 = -0.426511610904754
    a1 = 39.85091749344
    a2 = 0.713891558517388
    a3 = -2.68621789452889E-02
    a4 = 7.69400535914122E-04
    a5 = -8.51368088853222E-06

    return a1 + 2 * (a2 * DCota) + 3 * (a3 * DCota ** 2) +\
        4 * (a4 * DCota ** 3) + 5 * (a5 * DCota ** 4)


def Vol_LMAULE(Cota):
    DCota = Cota - 2152.135
    a0 = -0.426511610904754
    a1 = 39.85091749344
    a2 = 0.713891558517388
    a3 = -2.68621789452889E-02
    a4 = 7.69400535914122E-04
    a5 = -8.51368088853222E-06

    Vol_LMAULE = a0 + (a1 * DCota) + (a2 * DCota ** 2) +\
        (a3 * DCota ** 3) + (a4 * DCota ** 4) + (a5 * DCota ** 5)
    return max(Vol_LMAULE, 0)


def Cot_LMAULE(Volumen):
    Error_Cota = 0.005
    Num_de_Iter = 10
    Iter = 0
    CotIni = CotEST_LMAULE(Volumen)

    while True:
        Iter += 1
        CotFin = CotIni - (Vol_LMAULE(CotIni) - Volumen) / dVol_LMAULE(CotIni)
        CondERR = abs(CotFin - CotIni) < Error_Cota
        CondITE = Iter > Num_de_Iter
        CotIni = CotFin

        if CondERR or CondITE:
            break

    return CotFin


def Rend_LMAULE(Cota):
    return 1.0
