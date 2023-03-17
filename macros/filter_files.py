'''
Sub Filter_Files()
    Application.DisplayAlerts = False
    'Application.ScreenUpdating = False
    On Error GoTo NoFolder:
    
    Dim d_folder As String, d_folder_Plexos As String, d_file As String, a As String
    Dim i As Integer, j As Integer, n As Integer, m As Integer, count As Integer
    
    d_folder = Hoja01.Range("C1").value & "\Sal"
    If Dir(d_folder, vbDirectory) = "" Then: MkDir d_folder
    d_folder_Plexos = Hoja01.Range("C1").value & "\Dat Plexos"
    If Dir(d_folder_Plexos, vbDirectory) = "" Then: MkDir d_folder_Plexos
    d_folder = Hoja01.Range("C1").value & "\Dat"
    If Dir(d_folder, vbDirectory) = "" Then: MkDir d_folder
    
    On Error GoTo NoFile:
    
    n = Sheet24.Cells(Rows.count, 1).End(xlUp).Row
    m = Sheet24.Cells(1, Columns.count).End(xlToLeft).Column
    d_file = d_folder & "\block2day.csv"
    Open d_file For Output As #1
    d_file = d_folder_Plexos & "\block2day.csv"
    Open d_file For Output As #2
        For i = 1 To n
            For j = 1 To m
                Write #1, Sheet24.Cells(i, j).value,
                Write #2, Sheet24.Cells(i, j).value,
            Next j
            Write #1,
            Write #2,
        Next i
    Close #1
    Close #2
    
    d_file = d_folder & "\plpparam.csv"
    n = Hoja07.Cells(Rows.count, 1).End(xlUp).Row
    Open d_file For Output As #1
        Write #1, "Nº Hidr:", Hoja20.Range("D4").value
        Write #1, "Nº Sim:", Hoja20.Range("D2").value
        Write #1, "Nº Bloq:", Hoja07.Range("G5").value
        Write #1,
        Write #1, "", "Mes", "Año"
        Write #1, "Inicio:", Month(Hoja07.Range("B5").value), Year(Hoja07.Range("B5").value)
        Write #1, "Fin:", Month(Hoja07.Cells(n, 4).value), Year(Hoja07.Cells(n, 4).value)
    Close #1
    
    d_file = d_folder & "\plpetapas.csv"
    n = Hoja07.Cells(Rows.count, 1).End(xlUp).Row
    n_blo = Hoja01.Range("D5")
    count = 1
    Open d_file For Output As #1
        Write #1, "Etapa", "Year", "Month", "Block"
        For i = 5 To n
            For j = 1 To n_blo
                Write #1, count, Year(Hoja07.Cells(i, 2).value), Month(Hoja07.Cells(i, 2).value), j
                count = count + 1
            Next j
        Next i
    Close #1
    
    Call IdEtapa_Hidro
    
    Application.DisplayAlerts = True
    'Application.ScreenUpdating = True
    Exit Sub
    
NoFolder:
    a = MsgBox("No se crearon las carpetas. Revise directorio de archivos", vbCritical, "Error al crear carpetas")
    Application.DisplayAlerts = True
    'Application.ScreenUpdating = True
    Exit Sub
NoFile:
    a = MsgBox("No se crearon los archivos. Revise que no estén en uso", vbCritical, "Error al crear archivos")
    Application.DisplayAlerts = True
    'Application.ScreenUpdating = True
    Exit Sub
End Sub




'''