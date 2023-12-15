def CotEST_POLCURA(Volumen):
    a0 = 730.02173
    a1 = 8.94574
    a2 = -8.50159
    a3 = 13.99204
    a4 = -13.87739
    a5 = 5.10665
    DVol = Volumen
    return (a0 + (a1 * DVol) + (a2 * DVol ** 2) + (a3 * DVol ** 3) +
            (a4 * DVol ** 4) + (a5 * DVol ** 5))


def dVol_POLCURA(Cota):
    a1 = 90.859293303
    a2 = 40.08341237
    a3 = -13.9725593488
    a4 = 2.5864430194
    a5 = -0.159930272
    DCota = Cota - 730
    return ((a1) + 2 * (a2 * DCota) + 3 * (a3 * DCota ** 2) +
            4 * (a4 * DCota ** 3) + 5 * (a5 * DCota ** 4)) / 1000


def Vol_POLCURA(Cota):
    a0 = 0.6976365827
    a1 = 90.859293303
    a2 = 40.08341237
    a3 = -13.9725593488
    a4 = 2.5864430194
    a5 = -0.159930272
    DCota = Cota - 730
    return (a0 + (a1 * DCota) + (a2 * DCota ** 2) + (a3 * DCota ** 3) +
            (a4 * DCota ** 4) + (a5 * DCota ** 5)) / 1000


def Cot_POLCURA(Volumen):
    Error_Cota = 0.005
    Num_de_Iter = 10
    Iter = 0
    CotIni = CotEST_POLCURA(Volumen)
    while True:
        Iter += 1
        CotFin = CotIni - (Vol_POLCURA(CotIni) - Volumen) /\
            dVol_POLCURA(CotIni)
        CondERR = abs(CotFin - CotIni) < Error_Cota
        CondITE = Iter > Num_de_Iter
        CotIni = CotFin
        if CondERR or CondITE:
            break
    return CotFin
