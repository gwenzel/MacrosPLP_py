

def CotEST_RAPEL(Volumen):
    a0, a1, a2, a3 = 89.57534303, 0.45374052, 0.02412212, -0.00068196
    return a0 + (a1 * Volumen ** 0.5) + (a2 * Volumen) + (a3 * Volumen ** 1.5)


def dVol_RAPEL(Cota):
    a1, a2, a3 = 1279.686867, -15.1802416, 0.060121028
    return a1 + 2 * (a2 * Cota) + 3 * (a3 * Cota ** 2)


def Vol_RAPEL(Cota):
    a0, a1, a2, a3 = -36039.35, 1279.686867, -15.1802416, 0.060121028
    result = a0 + (a1 * Cota) + (a2 * Cota ** 2) + (a3 * Cota ** 3)
    return max(result, 65.3)


def Cot_RAPEL(Volumen):
    Error_Cota, Num_de_Iter = 0.005, 10
    Iter, CotIni = 0, CotEST_RAPEL(Volumen)

    while Iter < Num_de_Iter:
        Iter += 1
        CotFin = CotIni - (Vol_RAPEL(CotIni) - Volumen) / dVol_RAPEL(CotIni)
        CondERR = abs(CotFin - CotIni) < Error_Cota
        CondITE = Iter > Num_de_Iter
        if CondERR or CondITE:
            break
        CotIni = CotFin

    return CotFin


def Rend_RAPEL(Cota):
    cons1, cons2, cons3 = -1.18346, 0.026904, -0.00009
    return cons1 + cons2 * Cota + cons3 * Cota ** 2


def Pot_RAPEL(Cota, Caudal):
    eta = 0.873
    return (Cota - 26.5 - 0.00571 * Caudal) * Caudal * eta * (1 / 102)
