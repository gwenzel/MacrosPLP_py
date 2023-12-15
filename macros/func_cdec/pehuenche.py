def Vol_PEHUENCHE(Cota):
    a0, a1, a2 = 12532.0161, -42.383595, 0.0358801
    return a0 + a1 * Cota + a2 * Cota ** 2


def Cot_PEHUENCHE(Volumen):
    a0, a1, a2 = 12532.0161, -42.383595, 0.0358801
    DVol = (a1 ** 2 - 4 * a2 * (a0 - Volumen)) ** 0.5
    return (-a1 + DVol) / (2 * a2)


def Rend_PEHUENCHE(Cota):
    d0, d1, d2 = 17.2105, -0.0563686, 0.0000502872
    return d0 + d1 * Cota + d2 * Cota ** 2


def Pmax_PEHUENCHE(Cota):
    a1, a2, a3 = -591.332, -0.5003277, 0.0035378153
    return a1 + a2 * Cota + a3 * Cota ** 2
