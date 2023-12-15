def Vol_PILMAIQUEN(Cota):
    a0, a1 = 102, 103.7
    if Cota <= a1:
        return (Cota - a0) * 117 * 100 * 14148 / 1000000
    else:
        return (a1 - a0) * 117 * 100 * 14148 / 1000000


def Cot_PILMAIQUEN(Volumen):
    a0, a1 = 102, 103.7
    result = Volumen / (11700 * 14148) * 1000000 + a0
    return min(max(result, a0), a1)
