def Vol_RUCATAYO(Cota):
    a0, a1 = 144, 148
    if Cota > a1:
        Cota = a1
    return ((Cota - a0) * 397552.5 + 4816560) / 1000000


def Cot_RUCATAYO(Volumen):
    a0, a1 = 144, 148
    Cot_RUCATAYO = (Volumen * 1000000 - 4816560) / 397552.5 + a0
    if Cot_RUCATAYO > a1:
        Cot_RUCATAYO = a1
    return Cot_RUCATAYO
