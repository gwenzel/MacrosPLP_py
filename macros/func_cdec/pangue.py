from math import log


def Vol_PANGUE(Cota):
    a0, a1, a2 = 7091.6, -32.43, 0.0366
    if Cota < 493:
        return 0
    else:
        result = a0 + a1 * Cota + a2 * Cota ** 2
        return max(result, 0)


def Cot_PANGUE(Volumen):
    a0, a1, a2, a3 = 493, 0.293889548, -0.001273403, 0.00000656608
    return a0 + a1 * Volumen + a2 * Volumen ** 2 + a3 * Volumen ** 3


def Rend_PANGUE(Cotaa):
    cons1, cons2, cons3 = -3.6981, 0.0094, -0.0000008
    return cons1 + cons2 * Cotaa + cons3 * Cotaa ** 2


def Rend_PANGUE2(Cotaa2, PotPang):
    cona, conb, conc, cond, cone, conf, cong, conh, coni, conj = -2874.621,
    6.89711, 692.303, 0.0001319, 0, -2.23021, 0.00000001355, -5.946492,
    0.1803698, -0.000023142
    return cona + conb * PotPang + conc * log(Cotaa2) + cond * PotPang ** 2 +\
        cone * log(Cotaa2) ** 2 + conf * PotPang * log(Cotaa2) +\
        cong * PotPang ** 3 + conh * log(Cotaa2) ** 3 +\
        coni * PotPang * log(Cotaa2) ** 2 + conj * PotPang ** 2 * log(Cotaa2)
