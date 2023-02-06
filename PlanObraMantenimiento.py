from vb2py.vbfunctions import *
from vb2py.vbdebug import *



def PlanObra_Mantenimiento():
    TimeINI = Date()

    NMantencion = Variant()

    k = Integer()

    UltimoYear = Integer()

    Col = Variant()

    FilCicl = Integer()

    FilNoCicl = Integer()

    FilaBase = Integer()

    FilaMantCen = Variant()

    PES = Variant()

    ano_ini = Integer()

    mes_ini = Integer()

    dia_ini = Integer()

    ano_fin = Integer()

    mes_fin = Integer()

    dia_fin = Integer()

    fecha_ini_val = Date()

    fecha_fin_val = Date()

    MNCen = vbObjectInitialize(objtype=Variant)

    MFIni = vbObjectInitialize(objtype=Date)

    MFFin = vbObjectInitialize(objtype=Date)

    MPmin = vbObjectInitialize(objtype=Double)

    MPmax = vbObjectInitialize(objtype=Double)

    iw = Long()

    Hola = Variant()

    FilaGas = Integer()

    ColumnaGas = Integer()

    NCentral = Variant()

    ano = Variant()

    mes = Variant()

    Inicio = Variant()

    Final = Variant()

    aux = Variant()

    AnoFinal = Variant()

    AnoCiclAux = Variant()
    Application.ScreenUpdating = False
    Application.DisplayStatusBar = True
    Application.StatusBar = True
    TimeINI = Time
    #Dim Ano As Integer
    Col = 6
    #arreglos de resultados
    #UltimoYear = InputBox("¿Cuál será el ultimo año  de modelación?")
    #///////////Planillas//////////////////////////
    sheet_MantCenIM = ThisWorkbook.Worksheets('MantenimientosIM')
    sheet_MantCen = ThisWorkbook.Worksheets('MantCEN')
    sheet_PlanObras = ThisWorkbook.Worksheets('PlanObras')
    sheet_Etapas = ThisWorkbook.Worksheets('Etapas')
    UltimoYear = sheet_Etapas.Cells(sheet_Etapas.Range('E4').CurrentRegion.Rows.count + 3, 5)
    FilNoCicl = sheet_MantCenIM.Range('A1').CurrentRegion.Rows.count - 1
    FilCicl = sheet_MantCenIM.Range('H1').CurrentRegion.Rows.count - 1
    FilaMantCen = sheet_MantCen.Range('B5').CurrentRegion.Rows.count + 3
    FilaBase = WorksheetFunction.Match('Mantenimientos', sheet_MantCen.Range('A:A'), False)
    #//////////////Borrar mantenimientos anteriores////////////////////////
    sheet_MantCen.Activate()
    if FilaMantCen < FilaBase:
        sheet_MantCen.Range(Cells(FilaBase, 2), Cells(FilaBase, 6)).Clear()
    else:
        sheet_MantCen.Range(Cells(FilaBase, 2), Cells(FilaMantCen, 6)).Clear()
    sheet_MantCenIM.Activate()
    ref = sheet_MantCenIM.Range('A1')
    #//////////////Restricciones de Gas///////////////////
    FilaGas = sheet_MantCenIM.Range('P3').CurrentRegion.Rows.count - 2
    ColumnaGas = sheet_MantCenIM.Range('P3').CurrentRegion.Columns.count - 3
    aux = 0
    iw = 0
    for Fil in vbForRange(1, FilaGas):
        DoEvents()
        Application.StatusBar = 'Procesando restricciones de gas: ' + Format(Fil / FilaGas, '##0%...')
        ano = sheet_MantCenIM.Cells(Fil + 2, 16)
        AnoFinal = sheet_MantCenIM.Cells(Fil + 2, 17)
        if IsEmpty(sheet_MantCenIM.Cells(Fil + 2, 15)):
            #Nada
            pass
        else:
            NCentral = sheet_MantCenIM.Cells(Fil + 2, 15)
        if AnoFinal == '*':
            Diferencia = UltimoYear - ano
        else:
            Diferencia = AnoFinal - ano
        for years in vbForRange(1, Diferencia + 1):
            if UltimoYear >=  ( ano + years - 1 ) :
                for Col in vbForRange(1, ColumnaGas):
                    UltFilaActual = sheet_MantCen.Range('B5').CurrentRegion.Rows.count + 3
                    #Mes = "0" & Col
                    mes = Format(Col, '00')
                    if IsError(Application.VLookup(ref.Cells(NMant + 2, 9).Text, sheet_PlanObras.Range('A:B'), 2, False)) == True:
                        if aux == 0:
                            #Inicial = "01/" & Mes & "/" & Ano + years - 1
                            Inicial = DateSerial(ano + years - 1, CInt(mes), 1)
                            aux = 1
                        if sheet_MantCenIM.Cells(Fil + 2, 17 + Col).Text == sheet_MantCenIM.Cells(Fil + 2, 18 + Col).Text:
                            #Nada
                            pass
                        else:
                            #                        sheet_MantCen.Cells(UltFilaActual + 1, 2) = NCentral 'Central
                            #                        sheet_MantCen.Cells(UltFilaActual + 1, 3) = DateValue(Inicial) 'Fecha de Inicio
                            #                        sheet_MantCen.Cells(UltFilaActual + 1, 4) = DateAdd("m", 1, "01/" & Mes & "/" & Ano + years - 1) - 1 'Fecha Termino
                            #                        sheet_MantCen.Cells(UltFilaActual + 1, 5) = 0 'Pot Mínima
                            #                        sheet_MantCen.Cells(UltFilaActual + 1, 6) = sheet_MantCenIM.Cells(Fil + 2, 17 + Col) 'Pot Máxima
                            #                        sheet_MantCen.Cells(UltFilaActual + 1, 3).NumberFormat = "dd/mm/yyyy"
                            #                        sheet_MantCen.Cells(UltFilaActual + 1, 4).NumberFormat = "dd/mm/yyyy"
                            MNCen = vbObjectInitialize((iw,), Variant, MNCen)
                            MFIni = vbObjectInitialize((iw,), Variant, MFIni)
                            MFFin = vbObjectInitialize((iw,), Variant, MFFin)
                            MPmin = vbObjectInitialize((iw,), Variant, MPmin)
                            MPmax = vbObjectInitialize((iw,), Variant, MPmax)
                            MNCen[iw] = NCentral
                            MFIni[iw] = DateValue(Inicial)
                            #MFFin(iw) = CDate(DateAdd("m", 1, DateValue("01-" & Mes & "/" & Ano + years - 1)) - 1)
                            MFFin[iw] = CDate(DateAdd('m', 1, DateSerial(ano + years - 1, CInt(mes), 1)) - 1)
                            MPmin[iw] = 0
                            MPmax[iw] = sheet_MantCenIM.Cells(Fil + 2, 17 + Col)
                            iw = iw + 1
                            aux = 0
                    else:
                        PES = Application.VLookup(NCentral, sheet_PlanObras.Range('A:B'), 2, False)
                        if ( CDate(PES) > DateSerial(ano + years - 1, CInt(mes), 1) ) :
                            #Nada
                            Hola = NCentral
                        else:
                            if aux == 0:
                                #Inicial = "01/" & Mes & "/" & Ano + years - 1
                                Inicial = DateSerial(ano + years - 1, CInt(mes), 1)
                                aux = 1
                            if sheet_MantCenIM.Cells(Fil + 2, 17 + Col).Text == sheet_MantCenIM.Cells(Fil + 2, 18 + Col).Text:
                                #Nada
                                pass
                            else:
                                #                            sheet_MantCen.Cells(UltFilaActual + 1, 2) = NCentral 'Central
                                #                            sheet_MantCen.Cells(UltFilaActual + 1, 3) = DateValue(Inicial) 'Fecha de Inicio
                                #                            sheet_MantCen.Cells(UltFilaActual + 1, 4) = DateAdd("m", 1, "01/" & Mes & "/" & Ano + years - 1) - 1 'Fecha Termino
                                #                            sheet_MantCen.Cells(UltFilaActual + 1, 5) = 0 'Pot Mínima
                                #                            sheet_MantCen.Cells(UltFilaActual + 1, 6) = sheet_MantCenIM.Cells(Fil + 2, 17 + Col) 'Pot Máxima
                                #                            sheet_MantCen.Cells(UltFilaActual + 1, 3).NumberFormat = "dd/mm/yyyy"
                                #                            sheet_MantCen.Cells(UltFilaActual + 1, 4).NumberFormat = "dd/mm/yyyy"
                                MNCen = vbObjectInitialize((iw,), Variant, MNCen)
                                MFIni = vbObjectInitialize((iw,), Variant, MFIni)
                                MFFin = vbObjectInitialize((iw,), Variant, MFFin)
                                MPmin = vbObjectInitialize((iw,), Variant, MPmin)
                                MPmax = vbObjectInitialize((iw,), Variant, MPmax)
                                MNCen[iw] = NCentral
                                MFIni[iw] = DateValue(Inicial)
                                #MFFin(iw) = CDate(DateAdd("m", 1, DateValue("01/" & Mes & "/" & Ano + years - 1)) - 1)
                                MFFin[iw] = CDate(DateAdd('m', 1, DateSerial(ano + years - 1, CInt(mes), 1)) - 1)
                                MPmin[iw] = 0
                                MPmax[iw] = sheet_MantCenIM.Cells(Fil + 2, 17 + Col)
                                iw = iw + 1
                                aux = 0
    #//////////////////////No Ciclicas///////////////////////////
    sheet_MantCen.Activate()
    k = 0
    for NMant in vbForRange(1, FilNoCicl - 1):
        DoEvents()
        Application.StatusBar = 'Procesando mante no ciclicas: ' + Format(NMant / FilNoCicl, '##0%...')
        UltFilaActual = sheet_MantCen.Range('B5').CurrentRegion.Rows.count + 3
        ano = Year(CDate(ref.Cells(NMant + 2, 4)))
        if IsError(Application.VLookup(ref.Cells(NMant + 2, 2).Text, sheet_PlanObras.Range('A:B'), 2, False)) == True:
            if ano <= UltimoYear:
                #            sheet_MantCen.Cells(UltFilaActual + k, 2) = ref.Cells(NMant + 2, 2) 'Nombre de Central
                #            sheet_MantCen.Cells(UltFilaActual + k, 3) = ref.Cells(NMant + 2, 3)  'Fecha Inicio
                #            sheet_MantCen.Cells(UltFilaActual + k, 4) = ref.Cells(NMant + 2, 4)  'Fecha Termino
                #            sheet_MantCen.Cells(UltFilaActual + k, 5) = 0  'Potencia Mínima
                #            sheet_MantCen.Cells(UltFilaActual + k, 6) = ref.Cells(NMant + 2, 6)  'Potencia Máxima
                #            sheet_MantCen.Cells(UltFilaActual + k, 3).NumberFormat = "dd/mm/yyyy"
                #            sheet_MantCen.Cells(UltFilaActual + k, 4).NumberFormat = "dd/mm/yyyy"
                #            k = 1
                MNCen = vbObjectInitialize((iw,), Variant, MNCen)
                MFIni = vbObjectInitialize((iw,), Variant, MFIni)
                MFFin = vbObjectInitialize((iw,), Variant, MFFin)
                MPmin = vbObjectInitialize((iw,), Variant, MPmin)
                MPmax = vbObjectInitialize((iw,), Variant, MPmax)
                ano_ini = Year(ref.Cells(NMant + 2, 3))
                mes_ini = Month(ref.Cells(NMant + 2, 3))
                dia_ini = Day(ref.Cells(NMant + 2, 3))
                ano_fin = Year(ref.Cells(NMant + 2, 4))
                mes_fin = Month(ref.Cells(NMant + 2, 4))
                dia_fin = Day(ref.Cells(NMant + 2, 4))
                MNCen[iw] = ref.Cells(NMant + 2, 2)
                MFIni[iw] = DateSerial(ano_ini, mes_ini, dia_ini)
                MFFin[iw] = DateSerial(ano_fin, mes_fin, dia_fin)
                MPmin[iw] = 0
                MPmax[iw] = ref.Cells(NMant + 2, 6)
                iw = iw + 1
            else:
                # Exit For (nunca se usa)
                pass
        else:
            PES = Application.VLookup(ref.Cells(NMant + 2, 2).Text, sheet_PlanObras.Range('A:B'), 2, False)
            if CDate(PES) > CDate(ref.Cells(NMant + 2, 3)):
                #nada, ya que la central aún no entra en servicio
                #hola = ref.Cells(NMant + 2, 2)
                pass
            else:
                if ano <= UltimoYear:
                    #                    sheet_MantCen.Cells(UltFilaActual + k, 2) = ref.Cells(NMant + 2, 2)   'Nombre de Central
                    #                    sheet_MantCen.Cells(UltFilaActual + k, 3) = ref.Cells(NMant + 2, 3)  'Fecha Inicio
                    #                    sheet_MantCen.Cells(UltFilaActual + k, 4) = ref.Cells(NMant + 2, 4)  'Fecha Termino
                    #                    sheet_MantCen.Cells(UltFilaActual + k, 5) = 0  'Potencia Mínima
                    #                    sheet_MantCen.Cells(UltFilaActual + k, 6) = ref.Cells(NMant + 2, 6)  'Potencia Máxima
                    #                    sheet_MantCen.Cells(UltFilaActual + k, 3).NumberFormat = "dd/mm/yyyy"
                    #                    sheet_MantCen.Cells(UltFilaActual + k, 4).NumberFormat = "dd/mm/yyyy"
                    #                    k = 1
                    MNCen = vbObjectInitialize((iw,), Variant, MNCen)
                    MFIni = vbObjectInitialize((iw,), Variant, MFIni)
                    MFFin = vbObjectInitialize((iw,), Variant, MFFin)
                    MPmin = vbObjectInitialize((iw,), Variant, MPmin)
                    MPmax = vbObjectInitialize((iw,), Variant, MPmax)
                    ano_ini = Year(ref.Cells(NMant + 2, 3))
                    mes_ini = Month(ref.Cells(NMant + 2, 3))
                    dia_ini = Day(ref.Cells(NMant + 2, 3))
                    ano_fin = Year(ref.Cells(NMant + 2, 4))
                    mes_fin = Month(ref.Cells(NMant + 2, 4))
                    dia_fin = Day(ref.Cells(NMant + 2, 4))
                    MNCen[iw] = ref.Cells(NMant + 2, 2)
                    MFIni[iw] = DateSerial(ano_ini, mes_ini, dia_ini)
                    MFFin[iw] = DateSerial(ano_fin, mes_fin, dia_fin)
                    MPmin[iw] = 0
                    MPmax[iw] = ref.Cells(NMant + 2, 6)
                    iw = iw + 1
                else:
                    # Exit For (nunca se usa)
                    pass
    #//////////////////////Ciclicas///////////////////////////
    #Dim Ano As Integer
    for NMant in vbForRange(1, FilCicl - 1):
        DoEvents()
        Application.StatusBar = 'Procesando mante ciclicas: ' + Format(NMant / FilCicl, '##0%...')
        UltFilaActual = sheet_MantCen.Range('B5').CurrentRegion.Rows.count + 3
        ano = Year(DateValue(ref.Cells(NMant + 2, 10)))
        k = 0
        if IsError(Application.VLookup(ref.Cells(NMant + 2, 9).Text, sheet_PlanObras.Range('A:B'), 2, False)) == True:
            for Iyear in vbForRange(1, ( UltimoYear - ano + 1 ) ):
                #            sheet_MantCen.Cells(UltFilaActual + 1 + k, 2) = ref.Cells(NMant + 2, 9) 'Central
                #            sheet_MantCen.Cells(UltFilaActual + 1 + k, 3) = DateAdd("yyyy", k, ref.Cells(NMant + 2, 10)) 'Fecha de Inicio
                #            sheet_MantCen.Cells(UltFilaActual + 1 + k, 4) = DateAdd("yyyy", k, ref.Cells(NMant + 2, 11)) 'Fecha Termino
                #            sheet_MantCen.Cells(UltFilaActual + 1 + k, 5) = 0 'Pot Mínima
                #            sheet_MantCen.Cells(UltFilaActual + 1 + k, 6) = ref.Cells(NMant + 2, 13) 'Pot Máxima
                #            sheet_MantCen.Cells(UltFilaActual + 1 + k, 3).NumberFormat = "dd/mm/yyyy"
                #            sheet_MantCen.Cells(UltFilaActual + 1 + k, 4).NumberFormat = "dd/mm/yyyy"
                MNCen = vbObjectInitialize((iw,), Variant, MNCen)
                MFIni = vbObjectInitialize((iw,), Variant, MFIni)
                MFFin = vbObjectInitialize((iw,), Variant, MFFin)
                MPmin = vbObjectInitialize((iw,), Variant, MPmin)
                MPmax = vbObjectInitialize((iw,), Variant, MPmax)
                fecha_ini_val = DateValue(ref.Cells(NMant + 2, 10))
                ano_ini = Year(fecha_ini_val)
                mes_ini = Month(fecha_ini_val)
                dia_ini = Day(fecha_ini_val)
                fecha_fin_val = DateValue(ref.Cells(NMant + 2, 11))
                ano_fin = Year(fecha_fin_val)
                mes_fin = Month(fecha_fin_val)
                dia_fin = Day(fecha_fin_val)
                MNCen[iw] = ref.Cells(NMant + 2, 9)
                MFIni[iw] = DateAdd('yyyy', k, DateSerial(ano_ini, mes_ini, dia_ini))
                MFFin[iw] = DateAdd('yyyy', k, DateSerial(ano_fin, mes_fin, dia_fin))
                MPmin[iw] = 0
                MPmax[iw] = ref.Cells(NMant + 2, 13)
                iw = iw + 1
                k = k + 1
        else:
            PES = Application.VLookup(ref.Cells(NMant + 2, 9).Text, sheet_PlanObras.Range('A:B'), 2, False)
            for Iyear in vbForRange(1, ( UltimoYear - ano + 1 )):
                AnoCiclAux = DateAdd('yyyy', Iyear - 1, CDate(ref.Cells(NMant + 2, 10)))
                if PES > AnoCiclAux:
                    #nada, ya que la central aún no entra en servicio
                    Hola = ref.Cells(NMant + 2, 2)
                else:
                    # For Iyear = 1 To (UltimoYear - year + 1) 'Numero arbitrario que indica ultimo año del modelamiento
                    #                sheet_MantCen.Cells(UltFilaActual + 1 + k, 2) = ref.Cells(NMant + 2, 9) 'Central
                    #                sheet_MantCen.Cells(UltFilaActual + 1 + k, 3) = DateAdd("yyyy", Iyear - 1, ref.Cells(NMant + 2, 10)) 'Fecha de Inicio
                    #                sheet_MantCen.Cells(UltFilaActual + 1 + k, 4) = DateAdd("yyyy", Iyear - 1, ref.Cells(NMant + 2, 11)) 'Fecha Termino
                    #                sheet_MantCen.Cells(UltFilaActual + 1 + k, 5) = 0 'Pot Mínima
                    #                sheet_MantCen.Cells(UltFilaActual + 1 + k, 6) = ref.Cells(NMant + 2, 13) 'Pot Máxima
                    #                sheet_MantCen.Cells(UltFilaActual + 1 + k, 3).NumberFormat = "dd/mm/yyyy"
                    #                sheet_MantCen.Cells(UltFilaActual + 1 + k, 4).NumberFormat = "dd/mm/yyyy"
                    MNCen = vbObjectInitialize((iw,), Variant, MNCen)
                    MFIni = vbObjectInitialize((iw,), Variant, MFIni)
                    MFFin = vbObjectInitialize((iw,), Variant, MFFin)
                    MPmin = vbObjectInitialize((iw,), Variant, MPmin)
                    MPmax = vbObjectInitialize((iw,), Variant, MPmax)
                    fecha_ini_val = DateValue(ref.Cells(NMant + 2, 10))
                    ano_ini = Year(fecha_ini_val)
                    mes_ini = Month(fecha_ini_val)
                    dia_ini = Day(fecha_ini_val)
                    fecha_fin_val = DateValue(ref.Cells(NMant + 2, 11))
                    ano_fin = Year(fecha_fin_val)
                    mes_fin = Month(fecha_fin_val)
                    dia_fin = Day(fecha_fin_val)
                    MNCen[iw] = ref.Cells(NMant + 2, 9)
                    MFIni[iw] = DateAdd('yyyy', Iyear - 1, DateSerial(ano_ini, mes_ini, dia_ini))
                    MFFin[iw] = DateAdd('yyyy', Iyear - 1, DateSerial(ano_fin, mes_fin, dia_ifin))
                    MPmin[iw] = 0
                    MPmax[iw] = ref.Cells(NMant + 2, 13)
                    iw = iw + 1
                    k = k + 1
                    #Next Iyear
    #Application.ScreenUpdating = True
    #Application.DisplayStatusBar = True
    sheet_MantCen.Activate()
    # escribir resultados
    ActiveSheet.Range['B' + FilaBase + ':B' + FilaBase + UBound(MNCen)] = WorksheetFunction.Transpose(MNCen)
    ActiveSheet.Range['C' + FilaBase + ':C' + FilaBase + UBound(MFIni)] = WorksheetFunction.Transpose(MFIni)
    ActiveSheet.Range['D' + FilaBase + ':D' + FilaBase + UBound(MFFin)] = WorksheetFunction.Transpose(MFFin)
    ActiveSheet.Range['E' + FilaBase + ':E' + FilaBase + UBound(MPmin)] = WorksheetFunction.Transpose(MPmin)
    ActiveSheet.Range['F' + FilaBase + ':F' + FilaBase + UBound(MPmax)] = WorksheetFunction.Transpose(MPmax)
    #formato de tabla
    Range('C:C').Select()
    Range(Selection, Selection.End(xlDown)).Select()
    #Selection.NumberFormat = "dd/mm/yyyy"
    Range('D:D').Select()
    Range(Selection, Selection.End(xlDown)).Select()
    #Selection.NumberFormat = "dd/mm/yyyy"
    Range('E:F').Select()
    Range(Selection, Selection.End(xlDown)).Select()
    Selection.NumberFormat = '0.00'
    Range('B6').Select()
    Range(Selection, Selection.End(xlToRight)).Select()
    Range(Selection, Selection.End(xlDown)).Select()
    with_variable0 = Selection.Font
    with_variable0.name = 'Calibri'
    with_variable0.Size = 10
    with_variable0.Strikethrough = False
    with_variable0.Superscript = False
    with_variable0.Subscript = False
    with_variable0.OutlineFont = False
    with_variable0.Shadow = False
    with_variable0.Underline = xlUnderlineStyleNone
    with_variable0.TintAndShade = 0
    with_variable0.ThemeFont = xlThemeFontMinor
    Range('C6').Select()
    Range(Selection, Selection.End(xlToRight)).Select()
    Range(Selection, Selection.End(xlDown)).Select()
    with_variable1 = Selection
    with_variable1.HorizontalAlignment = xlCenter
    with_variable1.VerticalAlignment = xlBottom
    with_variable1.WrapText = False
    with_variable1.Orientation = 0
    with_variable1.AddIndent = False
    with_variable1.IndentLevel = 0
    with_variable1.ShrinkToFit = False
    with_variable1.ReadingOrder = xlContext
    with_variable1.MergeCells = False
    Range('B6').Select()
    Range(Selection, Selection.End(xlToRight)).Select()
    Range(Selection, Selection.End(xlDown)).Select()
    with_variable2 = Selection.Font
    with_variable2.ColorIndex = xlAutomatic
    with_variable2.TintAndShade = 0
    Application.ScreenUpdating = True
    Application.DisplayStatusBar = True
    Application.StatusBar = False

