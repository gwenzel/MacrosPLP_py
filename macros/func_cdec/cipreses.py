from math import log, exp


# CIPRESES
def Vol_CIPRESES(Cota):
    if Cota <= 1280:
        return 0
    else:
        a0 = 134744.88984
        a1 = -211.91025423
        a2 = 0.0833132678
        return a0 + (a1 * Cota) + (a2 * Cota**2)


def Cot_CIPRESES(Volumen):
    if Volumen <= 0:
        return 1280
    else:
        a0 = 134744.88984
        a1 = -211.91025423
        a2 = 0.0833132678
        DVol = (a1**2 - 4 * a2 * (a0 - Volumen))**0.5
        return (-a1 + DVol) / (2 * a2)


def Filt_CIPRESES(Cota):
    return 0.158 * Cota - 192.212 if Cota <= 1307 else 0.531 * Cota - 679.985


def Pot_CIPRESES(Cota, Caudal):
    a0, a1, a2, b0, b1, b2 = 0.875515, 0.0680838, 0.981487, 1.45996,
    0.101821, 0.76374
    if Caudal == 0:
        return 0
    cd = Cota - 1270
    if Caudal <= 24:
        return exp(a0 + a1 * log(cd) + a2 * log(Caudal))
    else:
        return exp(b0 + b1 * log(cd) + b2 * log(Caudal))


def Qmax_CIPRESES(Cota):
    a0, a1, b0, b1, b2, c0, c1, d0, d1, d2 = -45.044, 5.611, -22.3957, 6.5325,
    -0.176786, 36.9516, 0.055031, -11.6179, 2.33827, -0.0268453
    cd = Cota - 1270
    if Cota <= 1278:
        return 0
    elif Cota <= 1284:
        return a0 + a1 * cd
    elif Cota <= 1289:
        return b0 + cd * (b1 + b2 * cd)
    elif Cota <= 1312:
        return c0 + c1 * cd
    else:
        return d0 + cd * (d1 + d2 * cd)


def Rend_CIPRESES(Cota):
    cons1, cons2, cons3 = -354.62162659, 0.5410166883, -0.0002046658
    return cons1 + cons2 * Cota + cons3 * Cota**2


# ISLA
def Pot_ISLA(Caudal):
    a0, a1, a2, b0, b1, b2 = -7.259098, 1.432045, -0.01009883, -15.89178,
    1.495289, -0.00587928
    if Caudal == 0:
        return 0
    elif Caudal < 38.1:
        return a0 + Caudal * (a1 + a2 * Caudal)
    else:
        return b0 + Caudal * (b1 + b2 * Caudal)


# CURILLINQUE
def Pot_CURILLINQUE(Caudal):
    a0, a1, a2, a3 = 0.833023336663625, 0.000714859179181, 0.000095086701232,
    -0.000000891350262
    return (a0 + Caudal * (a1 + Caudal * (a2 + a3 * Caudal))) * Caudal


# LOMAALTA
def Pot_LOMAALTA(Caudal):
    a0, a1, a2, a3 = -0.107450536691195, 2.01309198488362E-02,
    -2.41044904140635E-04, 9.91511950595777E-07
    return (a0 + Caudal * (a1 + Caudal * (a2 + a3 * Caudal))) * Caudal
