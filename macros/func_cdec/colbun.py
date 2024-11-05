import datetime
import math

# Declare global variables
volumenes = [319.1, 333.76, 348.83, 364.32, 380.22]
Cotas = [393, 394, 395, 396, 397]


def CotEST_COLBUN(Volumen):
    a0 = 364.83334314
    a1 = 0.1113822656
    a2 = -0.00008523
    a3 = 0.000000044
    a4 = -1.3231988E-11
    a5 = 1.8734156E-15
    return (a0 + (a1 * Volumen) + (a2 * Volumen ** 2) + (a3 * Volumen ** 3) +
            (a4 * Volumen ** 4) + (a5 * Volumen ** 5))


def dVol_COLBUN(Cota):
    a3 = 215.679132
    a2 = -564.993651
    a1 = 496.907289
    CMÁX = 437
    VMÁX = 1550.63
    return (a1 / CMÁX + (2 * a2) * (Cota / CMÁX) +
            (3 * a3) * (Cota / CMÁX) ** 2) * VMÁX


def Vol_COLBUN(Cota):
    a3 = 215.679132
    a2 = -564.993651
    a1 = 496.907289
    a0 = -146.591083
    CMÁX = 437
    VMÁX = 1550.63
    if Cota < 393:
        return 319.1
    elif Cota < 397:
        i = math.floor(Cota - 392)
        m = volumenes[i] - volumenes[i - 1]
        b = volumenes[i - 1] - Cotas[i - 1] * m
        return m * Cota + b
    else:
        return (a1 * (Cota / CMÁX) + a2 * (Cota / CMÁX) ** 2 +
                a3 * (Cota / CMÁX) ** 3 + a0) * VMÁX


def Cot_COLBUN(Volumen):
    Error_Cota = 0.005
    if Volumen < 319.1:
        return 393
    elif Volumen < 380.22:
        i, dc = punteroC(5, Volumen, 0, 0)
        return Cotas[i - 1] + dc * (Cotas[i] - Cotas[i - 1])
    else:
        Num_de_Iter = 10
        Iter = 0
        CotIni = CotEST_COLBUN(Volumen)
        while True:
            Iter += 1
            CotFin = CotIni - (Vol_COLBUN(CotIni) - Volumen) /\
                dVol_COLBUN(CotIni)
            CondERR = abs(CotFin - CotIni) < Error_Cota
            CondITE = Iter > Num_de_Iter
            CotIni = CotFin
            if CondERR or CondITE:
                break
        return CotFin


def Filt_COLBUN(Cota):
    if Cota >= 423:
        return 0.487507978 * Cota - 202.489444
    elif 411.65 <= Cota <= 423:
        return 0.32644867 * Cota - 134.3795415
    else:
        return 0


def Rend_COLBUN(Cota):
    Rend0 = 1.55
    Cota0 = 430.55
    CotaD = 267.76
    return Rend0 * (Cota - CotaD) / (Cota0 - CotaD)


def Cotmax_COLBUN(fecha):
    if 4 <= datetime.datetime.strptime(fecha, '%Y-%m-%d').month <= 9:
        return 436
    else:
        return 437


def Cotmin_COLBUN(fecha):
    Habilita_Funcion = True
    if (5 <= datetime.datetime.strptime(fecha, '%Y-%m-%d').month <= 9 and
            Habilita_Funcion):
        return 397
    else:
        return 422.3


def Volmax_COLBUN(fecha):
    if 4 <= datetime.datetime.strptime(fecha, '%Y-%m-%d').month <= 9:
        return 1504
    else:
        return 1554


def Pot_COLBUN(Cota, Caudal):
    Potmax = 457
    result = Caudal * (-2.54358 + 0.00952104 * Cota -
                       0.0000003649 * Caudal ** 2)
    return min(result, Potmax)


def Qmax_COLBUN(Cota):
    if Cota <= 425:
        return 1.294 * Cota - 238.4
    else:
        return -1.957 * Cota + 1143


def Pot_SANIGNACIO(Caudal):
    Rensig = 0.19
    CauMax = 194

    if Caudal > CauMax:
        Caudal = CauMax

    return Caudal * Rensig


def punteroC(m, x, i, dc):
    j = 1
    k = m

    while k - j > 1:
        i = int((k + j) / 2)
        if x <= volumenes[i]:
            k = i
        else:
            j = i

    d1 = x - volumenes[i - 1]
    d2 = volumenes[i] - volumenes[i - 1]
    dc = d1 / d2
    return i, dc
