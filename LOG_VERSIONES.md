# Log de versiones

Las versiones tienen 3 números para identificarlas: a.b.c

a. Versión principal. Se cambia cuando los cambios agregan funcionalidades nuevas o requieren cambios de forma en la planilla.
b. Versión secundaria. Se cambia cuando hay cambios que agregan funcionalidades nuevas que pueden convivir con la planilla tal como estaba.
c. Versión terciaria. Se cambia cuando se corrigen bugs sobre la versión actual.

Esta lógica es válida desde la versión 1.0.0.

## Versión 0

### Versión 0.0.1

- Versión inicial ERNC
  - Parte final plpmance.dat
- Versión inicial Demanda
  - plpdem.dat
  - uni_plpdem.dat
  - plpfal.prn

### Versión 0.0.2

- Versión inicial Costo Variable
  - plpcosce.dat
- Versión inicial Mantención de Centrales + integración ERNC
  - plpmance_ini.dat y plpmance.dat

### Versión 0.0.3

- Mejora Script de generación de perfiles ERNC - requiere los perfiles en la planilla IPLP (no en una carpeta centralizada)

### Versión 0.0.4

- Versión inicial Líneas y MantLin/x, incluyendo restricciones de transformadores
  - plpcnfli.dat
  - plpmanli.dat
  - plpmanlix.dat
- Versión inicial Afluentes
  - plpaflce.dat
  - Storage_NaturalInflow.csv

### Versión 0.0.5

- Versión inicial Script Plexos
  - Carpeta CSV + archivos varios
- Versión inicial Script Centrales + FuncCDEC
  - plpcnfce.dat
  - plptec.dat
- Versión inicial PLPBLO
  - PLPBLO.dat
  - PLPETA.dat 
  - Etapa2Dates.csv
- Versión inicial Bar
  - plpbar.dat
  - uni_plpbar.dat
  - plpbar_full.dat
- Versión inicial PLPMAT
  - plpmat.dat
- Mejoras Script Afluentes
- Mejoras Costo Variable
- Mejoras Script ERNC
- Mejora Script Demanda (nombre centrales de falla)

## Versión 1

### Versión 1.0.0

- Validación de Inputs
- Manejo de errores y mensajes 

### Versión 1.1.0

- Quitar restricciones de Transformadores

### Versión 1.2.0

- Quitar función de reducción de incertidumbre en Script Afluentes
- Arreglo de error en archivo de volumen de Gas Plexos, dejaba en 0 la el horizonte completo si había una celda vacía

### Versión 1.3.0

 - Demanda Plexos con resolución horaria

### Versión 1.3.1

- Arreglar bug en Demanda Plexos Horaria con el 29 de Febrero.

### Versión 1.4.0

- Cambios críticos para curtailment + actualización script
  - imprimir df_centrales
  - arreglar archivo df_ernc_rf_final
- Otros bugs
  - Espacio en mensaje de error costo de falla

### Versión 1.4.1

- Corrección de bug en script demanda - ahora no se cae con columnas nuevas

### Versión 1.4.2

- Quitar restricciones adicionales de gas en hoja mantcen

### Versión 1.5.0

- Agregar archivos CSV Plexos: BESS_Max_Capacity, BESS_Eff_Charge, BESS_Eff_Disharge, Generator_Heatrate_Fuel

### Versión 1.5.1

- Corrección de magnitudes y nombres de archivos en cambios 1.5.0

### Versión 1.5.2

- Corrección de bug en cen, si habían NaN en columna Check Perfil, valor FlagPerfil en plptec quedaba en 0.
- Este error causaba que los vertimientos se imprimieran todos en 0.

### Versión 2.0.0

- Adición de módulos faltantes relacionados a Embalses y GNL (PLPCENPMAX, PLPCENRE, etc)

### Versión 2.0.1

- Fix bug en plpminembh

### Versión 2.1.0

- Cambios en interfaz y adición de módulo "run_all"

### Versión 2.1.1

- Arreglo de bug que no reconocía perfiles con nombres que no empezaran con "fp_"
- Ajustes de espacios en módulos nuevos
- PLPGAS - ajuste de posición de columnas para los consumos (ahora a la izquierda) y los volúmenes (ahora a la derecha)

### Versión 2.1.2

- Adición de check_errors, que imprime una tabla resumen de los logs en la misma carpeta

### Versión 2.1.3

- En plexos, reemplazo de heat rate de consumo de gas en archivo HeatRateFuel, con valores en PLP_ships


### Versión 2.2.0

- Agregar interface al paquete distribuido, para habilitar comando run_all