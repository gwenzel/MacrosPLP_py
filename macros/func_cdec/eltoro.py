# Declare global variables
Datos = [0, 48.28954, 97.47766, 147.26746, 197.35679, 248.04517, 299.43508,
         351.82341, 405.0131, 459.20122,
         514.48761, 570.97736, 628.56274, 687.35149, 747.53804, 808.92531,
         871.61054, 935.59635, 1000.88273,
         1067.4697, 1135.25477, 1204.23795, 1274.32464, 1345.60945, 1417.89268,
         1491.07712, 1565.25999, 1640.4439,
         1716.42655, 1793.41026, 1871.19533, 1949.97619, 2029.56105,
         2110.14171, 2191.52373, 2273.9068, 2357.18845,
         2441.47116, 2526.65244, 2612.83215, 2700.01554, 2788.19472,
         2877.37496, 2967.75593, 3059.03548, 3151.31608,
         3244.69758, 3339.17471, 3434.65552, 3531.13476, 3628.71226,
         3727.4905, 3827.36962, 3928.44686, 4030.62499,
         4133.90402, 4238.58084, 4344.35855, 4451.33437, 4559.61076,
         4668.98805, 4779.66329, 4891.53927, 5004.41367,
         5118.38896, 5233.46515, 5349.83928, 5467.31431, 5585.88761, 
         5705.66164, 5826.53656]

Cotas = [3.02, 4.04, 4.14, 4.31, 4.56, 4.86, 5.23, 5.66, 6.18, 6.76]
Caudal = [17, 20, 20, 30, 40, 50, 60, 70, 80, 90]


def Cot_ELTORO(Volumen):
    x = Volumen
    i, dc = punteroA(71, x, 0, 0)
    result = 1300 + i - 2 + dc

    if result < 1300:
        result = 1300
    elif result > 1370:
        result = 1370

    return result


def punteroA(m, x, i, dc):
    j = 1
    k = m
    while k - j > 1:
        i = round((k + j) / 2)
        if x <= Datos[i]:
            k = i
        else:
            j = i
    d1 = x - Datos[i - 1]
    d2 = Datos[i] - Datos[i - 1]
    dc = d1 / d2
    return i, dc


def Vol_ELTORO(Cota):
    if Cota >= 1370:
        return 5826.53656
    # else
    Cota = Cota - 1300
    i = min(round(Cota) + 1, 70)
    result = Datos[i - 1] + (Cota - round(Cota)) * (Datos[i] - Datos[i - 1])
    return max(result, 0)


def Filt_ELTORO(Cota):
    a0 = -133471.205667
    a1 = 251.668765787
    a2 = -0.112314280288
    a3 = -0.000031180464
    a4 = 0.000000022628942
    return a0 + (a1 * Cota) + (a2 * Cota ** 2) +\
        (a3 * Cota ** 3) + (a4 * Cota ** 4)


def Rend_ELTORO(Cota):
    cons1 = 0.008
    cons2 = 5.931
    return cons1 * Cota - cons2


def Qmax_ELTORO(Cota):
    Caudal = [17, 20, 20, 30, 40, 50, 60, 70, 80, 90]

    Cota -= 1300

    if Cota < 3.02:
        return 17
    elif Cota > 6.76:
        return 93.7
    else:
        i, dc = punteroB(10, Cota)
        return Caudal[i - 1] + dc * (Caudal[i] - Caudal[i - 1])


def punteroB(m, x, i, dc):
    j = 1
    k = m
    while k - j > 1:
        if k - j <= 1:
            i = k
        else:
            i = round((k + j) / 2)

            if x <= Cotas[i - 1]:
                k = i
            else:
                j = i
    d1 = x - Cotas[i - 1]
    d2 = Cotas[i] - Cotas[i - 1]
    dc = d1 / d2

    return i, dc
