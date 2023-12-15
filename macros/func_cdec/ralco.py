import math

Cotas = [598, 600, 610, 620, 630, 635, 636, 637, 638]
Vol_Inf = [0, 0.02132, 0.43767, 4.90172, 15.43637, 22.730575, 24.318677,
           25.984148, 27.732006]


def punteroA(Arreglo, m, x):
    j, k = 1, m
    while (k - j) > 1:
        i = (k + j) // 2
        if x <= Arreglo[i]:
            k = i
        else:
            j = i
    return k


def Vol_RALCO(Cota):
    a0, a1, a2, a3 = -30351, 2789.6, -72.676, 0.9869
    if Cota <= Cotas[-1]:
        i = punteroA(Cotas, 9, Cota)
        return ((Vol_Inf[i] - Vol_Inf[i - 1]) /
                (Cotas[i] - Cotas[i - 1])) * (Cota - Cotas[i]) + Vol_Inf[i]
    else:
        Cota_R = Cota - Cotas[0]
        return (a0 + a1 * Cota_R + a2 * Cota_R**2 + a3 * Cota_R**3) / 1000


def dVol_dCot(Cota):
    a1, a2, a3 = 2789.6, -72.676, 0.9869
    Cota_R = Cota - 598
    return (a1 + 2 * a2 * Cota_R + 3 * a3 * Cota_R**2) / 1000


def Cot_RALCO(Volumen):
    if Volumen <= Vol_Inf[-1]:
        i = punteroA(Vol_Inf, 9, Volumen)
        return ((Cotas[i] - Cotas[i - 1]) / (Vol_Inf[i] - Vol_Inf[i - 1])) *\
            (Volumen - Vol_Inf[i]) + Cotas[i]
    else:
        Cota_R = 708
        Error = 0.0001
        LimIter = 100
        Iter = 0
        DCot = 9999
        while DCot > Error and Iter < LimIter:
            Iter += 1
            Vol_aux = Vol_RALCO(Cota_R)
            dVol_aux = dVol_dCot(Cota_R)
            Cota_A = Cota_R + (Volumen - Vol_aux) / dVol_aux
            DCot = abs(Cota_R - Cota_A)
            Cota_R = Cota_A
        return Cota_R


def Rend_RALCO(Cota):
    Pend, Cte0 = 0.0089, -4.721475
    return Pend * Cota + Cte0


def Pot_Max_Ralco(Cota):
    Pendln, Pendln2, Cte0 = 485900, -36736, -1605998
    return Pendln * math.log(Cota) + Pendln2 * (math.log(Cota))**2 + Cte0
