from math import log, exp
# CANUTILLAR


def Vol_CANUTILLAR(Cota):
    if Cota < 230:
        return 44.9739 * Cota - 9894.258
    elif 230 <= Cota <= 240:
        return 46.3472 * Cota - 10210.117
    else:
        return 50.7225 * Cota - 11260.189


def Cot_CANUTILLAR(Volumen):
    if Volumen < 449.739:
        return 0.022235119 * Volumen + 220
    elif 449.739 <= Volumen <= 913.211:
        return 0.021576276 * Volumen + 220.29631
    else:
        return 0.019715117 * Volumen + 221.99594


def Rend_CANUTILLAR(Cota):
    Rend0 = 2.082606
    cons1 = -0.018920591
    cons2 = 0.000120086
    cons3 = -0.0000001742
    return Rend0 + Cota * cons1 + Cota**2 * cons2 + Cota**3 * cons3


def Pot_CANUTILLAR(Cota, Caudal):
    Potmax = 172
    if Caudal >= 1:
        pot = exp(-4.755425 + 1.015902 * log(Cota) + 0.9758028 * log(Caudal))
    else:
        pot = 0

    return min(pot, Potmax)


def Qmax_CANUTILLAR(Cota):
    Potmax = 172
    return min(19.0967 + 0.2625014 * Cota,
               exp((log(Potmax) + 4.755425 - 1.015902 * log(Cota)) *
                   (1 / 0.9758028)))
