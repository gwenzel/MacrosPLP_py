library(data.table) #fread
library(dplyr) #join, combine, filter, %>%
library(tidyr) #transponer

# Limpiar variables
rm(list=ls(all=TRUE))
closeAllConnections()

# Tiempo inicial
t_ini <- Sys.time()
message(t_ini)

# Hidrologías en Hyd med
n_hyd = 20
n_blo = 12
case_id = 1

# Directorios y carpetas
location <- getwd()
Path_Dat <- file.path(location, "Dat")
Path_Sal <- file.path(location, "Sal")
Sal_Folders <- list.files(path = Path_Sal)

g <- gregexpr(.Platform$file.sep,location)
Research_Name <- substr(location, g[[1]][length(g[[1]])]+1, nchar(location))

Path_Out <- file.path(location, Research_Name)
dir.create(file.path(Path_Out), showWarnings = FALSE)

# Archivo de etapas y block2day
plpeta_name <- "plpetapas.csv"
plpb2d_name <- "block2day.csv"

plpetapas <- fread(input = file.path(Path_Dat,plpeta_name), skip = 0L) %>% mutate(Tasa = 1.1^((ceiling(Etapa/12)-1)/12))

block2day <- fread(input = file.path(Path_Dat,plpb2d_name), skip = 0L) %>%
            rename("1"=jan,"2"=feb,"3"=mar,"4"=apr,"5"=may,"6"=jun,"7"=jul,"8"=aug,"9"=sep,"10"=oct,"11"=nov,"12"=dec,Hour=Hour2Blo) %>%
            select(1:13) %>% gather(Month,Block,-(Hour)) %>% mutate(Month=as.numeric(Month), Hour=as.numeric(Hour))

block_len <- block2day %>% group_by(Month,Block) %>% summarise(Block_Len=n())

blo_eta <- left_join(plpetapas,block_len, by = c("Month", "Block"))

rm("plpeta_name","plpb2d_name","plpetapas","block2day","block_len")


# Procesar por caso
Case_Name <- Sal_Folders[case_id]
Path_Case <- file.path(Path_Sal, Case_Name)
Path_Out <- file.path(location, Research_Name, Case_Name)
dir.create(file.path(Path_Out), showWarnings = FALSE)


# Marginales
Bar_Data <- fread(input = file.path(Path_Case,"plpbar.csv"), skip = 0L) %>% filter(Hidro!="MEDIA") %>%
  rename(Hyd=Hidro) %>% mutate(Hyd=as.numeric(Hyd)) %>% arrange(Hyd,Etapa,BarNom)

Bar_Param <- Bar_Data %>% select(BarNom) %>% distinct(BarNom, .keep_all = TRUE)

Bar_Data <- left_join(Bar_Data, blo_eta, by = "Etapa") %>% select(Hyd,Year,Month,Block,Block_Len,BarNom,CMgBar,DemBarE) %>%
  mutate(CMgBar = round(CMgBar,3), DemBarE = round(DemBarE,3))

# Data mensual
Bar_Data_m <- Bar_Data %>% mutate(CMgBar=Block_Len*CMgBar) %>% group_by(Hyd,Year,Month,BarNom) %>% summarise(CMgBar=sum(CMgBar)/24,DemBarE=sum(DemBarE)) %>%
  mutate(CMgBar = round(CMgBar,3), DemBarE = round(DemBarE,3))

# # Data Hyd med
# h_end <- max(Bar_Data$Hyd)
# h_ini <- h_end-n_hyd+1
# 
# Bar_Data_Hmed <- Bar_Data %>% filter(Hyd>=h_ini & Hyd<=h_end) %>%
#                 group_by(Year,Month,Block,BarNom) %>% summarise(CMgBar=mean(CMgBar),DemBarE=mean(DemBarE)) %>%
#                 mutate(Hyd=0,CMgBar = round(CMgBar,3),DemBarE = round(DemBarE,3)) %>% select(Hyd,Year,Month,Block,BarNom,CMgBar,DemBarE)
# 
# Bar_Data_m_Hmed <- Bar_Data_m %>% filter(Hyd>=h_ini & Hyd<=h_end) %>%
#                   group_by(Year,Month,BarNom) %>% summarise(CMgBar=mean(CMgBar),DemBarE=mean(DemBarE)) %>%
#                   mutate(Hyd=0,CMgBar = round(CMgBar,3),DemBarE = round(DemBarE,3)) %>% select(Hyd,Year,Month,BarNom,CMgBar,DemBarE)
# 
# Bar_Data <- bind_rows(Bar_Data_Hmed,Bar_Data)
# Bar_Data_m <- bind_rows(Bar_Data_m_Hmed,Bar_Data_m)
# rm("Bar_Data_Hmed", "Bar_Data_m_Hmed")


CMg_B <- Bar_Data %>% select(Hyd,Year,Month,Block,BarNom,CMgBar) %>% spread(BarNom,CMgBar)
Dem_B <- Bar_Data %>% select(Hyd,Year,Month,Block,BarNom,DemBarE) %>% spread(BarNom,DemBarE)
CMg_M <- Bar_Data_m %>% select(Hyd,Year,Month,BarNom,CMgBar) %>% spread(BarNom,CMgBar)
Dem_M <- Bar_Data_m %>% select(Hyd,Year,Month,BarNom,DemBarE) %>% spread(BarNom,DemBarE)

# CMg_B$Hyd[CMg_B$Hyd==0] <- "med"
# Dem_B$Hyd[Dem_B$Hyd==0] <- "med"
# CMg_M$Hyd[CMg_M$Hyd==0] <- "med"
# Dem_M$Hyd[Dem_M$Hyd==0] <- "med"

# Headers
Header_Data <- Bar_Param

Head_B <- data.table(BarNom=c("","","","Ubic:"))
Head_M <- data.table(BarNom=c("","","Ubic:"))

Header_B <- t(bind_rows(Head_B,Header_Data))
Header_M <- t(bind_rows(Head_M,Header_Data))

# Escribir archivos

Header_B[1,1] = "[USD/MWh]"
fwrite(Header_B, file = file.path(Path_Out, "outBarCMg_B.csv"), na = 0, col.names = FALSE, row.names = FALSE, buffMB = 128, nThread = getDTthreads()-1)
fwrite(CMg_B, file = file.path(Path_Out, "outBarCMg_B.csv"), na = 0, col.names = TRUE, row.names = FALSE, buffMB = 128, nThread = getDTthreads()-1, append = TRUE)

Header_B[1,1] = "[USD/MWh]"
fwrite(Header_M, file = file.path(Path_Out, "outBarCMg.csv"), na = 0, col.names = FALSE, row.names = FALSE, buffMB = 128, nThread = getDTthreads()-1)
fwrite(CMg_M, file = file.path(Path_Out, "outBarCMg.csv"), na = 0, col.names = TRUE, row.names = FALSE, buffMB = 128, nThread = getDTthreads()-1, append = TRUE)

Header_B[1,1] = "[GWh]"
fwrite(Header_B, file = file.path(Path_Out, "outDemEne_B.csv"), na = 0, col.names = FALSE, row.names = FALSE, buffMB = 128, nThread = getDTthreads()-1)
fwrite(Dem_B, file = file.path(Path_Out, "outDemEne_B.csv"), na = 0, col.names = TRUE, row.names = FALSE, buffMB = 128, nThread = getDTthreads()-1, append = TRUE)

Header_B[1,1] = "[GWh]"
fwrite(Header_M, file = file.path(Path_Out, "outDemEne.csv"), na = 0, col.names = FALSE, row.names = FALSE, buffMB = 128, nThread = getDTthreads()-1)
fwrite(Dem_M, file = file.path(Path_Out, "outDemEne.csv"), na = 0, col.names = TRUE, row.names = FALSE, buffMB = 128, nThread = getDTthreads()-1, append = TRUE)


# Generación
Gen_Data <- fread(input = file.path(Path_Case,"plpcen.csv"), skip = 0L) %>% filter(Hidro!="MEDIA") %>%
  rename(Hyd=Hidro) %>% mutate(Hyd=as.numeric(Hyd), CenInyE=CenInyE/1000) %>% arrange(Hyd,Etapa,CenNom)

Gen_Param <- Gen_Data %>% select(CenNom,BarNom,CenTip) %>% distinct(CenNom, .keep_all = TRUE)

Gen_Data <- left_join(Gen_Data, blo_eta, by = "Etapa") %>%
  mutate(CenEgen = round(CenEgen,3), CenCMg = round(1000*CenInyE*Tasa/CenEgen,3), CenInyE = round(CenInyE*Tasa,3), CurE = round(CurE,3)) %>%
  select(Hyd,Year,Month,Block,CenNom,CenEgen,CenInyE,CenCMg,CurE)

# Data mensual
Gen_Data_m <- Gen_Data %>% group_by(Hyd,Year,Month,CenNom) %>% summarise(CenEgen=sum(CenEgen),CenInyE=sum(CenInyE),CurE=sum(CurE)) %>%
  mutate(CenEgen = round(CenEgen,3), CenCMg = round(1000*CenInyE/CenEgen,3), CenInyE = round(CenInyE,3), CurE = round(CurE,3))

# # Data Hyd med
# h_end <- max(Gen_Data$Hyd)
# h_ini <- h_end-n_hyd+1
# 
# Gen_Data_Hmed <- Gen_Data %>% filter(Hyd>=h_ini & Hyd<=h_end) %>%
#                 group_by(Year,Month,Block,CenNom) %>% summarise(CenEgen=mean(CenEgen),CenInyE=mean(CenInyE),CurE=mean(CurE)) %>%
#                 mutate(Hyd=0, CenCMg = round(1000*CenInyE/CenEgen,3)) %>% select(Hyd,Year,Month,Block,CenNom,CenEgen,CenInyE,CenCMg,CurE)
# 
# Gen_Data_m_Hmed <- Gen_Data_m %>% filter(Hyd>=h_ini & Hyd<=h_end) %>%
#                   group_by(Year,Month,CenNom) %>% summarise(CenEgen=mean(CenEgen),CenInyE=mean(CenInyE),CurE=mean(CurE)) %>%
#                   mutate(Hyd=0, CenCMg = round(1000*CenInyE/CenEgen,3)) %>% select(Hyd,Year,Month,CenNom,CenEgen,CenInyE,CenCMg,CurE)
# 
# Gen_Data <- bind_rows(Gen_Data_Hmed,Gen_Data)
# Gen_Data_m <- bind_rows(Gen_Data_m_Hmed,Gen_Data_m)
# rm("Gen_Data_Hmed", "Gen_Data_m_Hmed")


Energ_B <- Gen_Data %>% select(Hyd,Year,Month,Block,CenNom,CenEgen) %>% spread(CenNom,CenEgen)
Reven_B <- Gen_Data %>% select(Hyd,Year,Month,Block,CenNom,CenInyE) %>% spread(CenNom,CenInyE)
CapPrice_B <- Gen_Data %>% select(Hyd,Year,Month,Block,CenNom,CenCMg) %>% spread(CenNom,CenCMg)
Curtail_B <- Gen_Data %>% select(Hyd,Year,Month,Block,CenNom,CurE) %>% spread(CenNom,CurE)
Energ_M <- Gen_Data_m %>% select(Hyd,Year,Month,CenNom,CenEgen) %>% spread(CenNom,CenEgen)
Reven_M <- Gen_Data_m %>% select(Hyd,Year,Month,CenNom,CenInyE) %>% spread(CenNom,CenInyE)
CapPrice_M <- Gen_Data_m %>% select(Hyd,Year,Month,CenNom,CenCMg) %>% spread(CenNom,CenCMg)
Curtail_M <- Gen_Data_m %>% select(Hyd,Year,Month,CenNom,CurE) %>% spread(CenNom,CurE)
rm("Gen_Data","Gen_Data_m")

# Energ_B$Hyd[Energ_B$Hyd==0] <- "med"
# Reven_B$Hyd[Reven_B$Hyd==0] <- "med"
# CapPrice_B$Hyd[CapPrice_B$Hyd==0] <- "med"
# Curtail_B$Hyd[Curtail_B$Hyd==0] <- "med"
# Energ_M$Hyd[Energ_M$Hyd==0] <- "med"
# Reven_M$Hyd[Reven_M$Hyd==0] <- "med"
# CapPrice_M$Hyd[CapPrice_M$Hyd==0] <- "med"
# Curtail_M$Hyd[Curtail_M$Hyd==0] <- "med"

# Headers
Header_Data <- Gen_Param %>% select(BarNom,CenTip,CenNom)

Head_B <- data.table(BarNom=c("","","","Ubic:"), CenTip=c("","","","Comb:"), CenNom=c("","","","Firm:"))
Head_M <- data.table(BarNom=c("","","Ubic:"), CenTip=c("","","Comb:"), CenNom=c("","","Firm:"))

Header_B <- t(bind_rows(Head_B,Header_Data))
Header_M <- t(bind_rows(Head_M,Header_Data))

# Escribir archivos

Header_B[1,1] = "[GWh]"
fwrite(Header_B, file = file.path(Path_Out, "outEnerg_B.csv"), na = 0, col.names = FALSE, row.names = FALSE, buffMB = 128, nThread = getDTthreads()-1)
fwrite(Energ_B, file = file.path(Path_Out, "outEnerg_B.csv"), na = 0, col.names = TRUE, row.names = FALSE, buffMB = 128, nThread = getDTthreads()-1, append = TRUE)

Header_M[1,1] = "[GWh]"
fwrite(Header_M, file = file.path(Path_Out, "outEnerg.csv"), na = 0, col.names = FALSE, row.names = FALSE, buffMB = 128, nThread = getDTthreads()-1)
fwrite(Energ_M, file = file.path(Path_Out, "outEnerg.csv"), na = 0, col.names = TRUE, row.names = FALSE, buffMB = 128, nThread = getDTthreads()-1, append = TRUE)

Header_B[1,1] = "[MUSD]"
fwrite(Header_B, file = file.path(Path_Out, "outReven_B.csv"), na = 0, col.names = FALSE, row.names = FALSE, buffMB = 128, nThread = getDTthreads()-1)
fwrite(Reven_B, file = file.path(Path_Out, "outReven_B.csv"), na = 0, col.names = TRUE, row.names = FALSE, buffMB = 128, nThread = getDTthreads()-1, append = TRUE)

Header_M[1,1] = "[MUSD]"
fwrite(Header_M, file = file.path(Path_Out, "outReven.csv"), na = 0, col.names = FALSE, row.names = FALSE, buffMB = 128, nThread = getDTthreads()-1)
fwrite(Reven_M, file = file.path(Path_Out, "outReven.csv"), na = 0, col.names = TRUE, row.names = FALSE, buffMB = 128, nThread = getDTthreads()-1, append = TRUE)

Header_B[1,1] = "[USD/MWh]"
fwrite(Header_B, file = file.path(Path_Out, "outCapPrice_B.csv"), na = 0, col.names = FALSE, row.names = FALSE, buffMB = 128, nThread = getDTthreads()-1)
fwrite(CapPrice_B, file = file.path(Path_Out, "outCapPrice_B.csv"), na = 0, col.names = TRUE, row.names = FALSE, buffMB = 128, nThread = getDTthreads()-1, append = TRUE)

Header_M[1,1] = "[USD/MWh]"
fwrite(Header_M, file = file.path(Path_Out, "outCapPrice.csv"), na = 0, col.names = FALSE, row.names = FALSE, buffMB = 128, nThread = getDTthreads()-1)
fwrite(CapPrice_M, file = file.path(Path_Out, "outCapPrice.csv"), na = 0, col.names = TRUE, row.names = FALSE, buffMB = 128, nThread = getDTthreads()-1, append = TRUE)

Header_B[1,1] = "[GWh]"
fwrite(Header_B, file = file.path(Path_Out, "outCurtail_B.csv"), na = 0, col.names = FALSE, row.names = FALSE, buffMB = 128, nThread = getDTthreads()-1)
fwrite(Curtail_B, file = file.path(Path_Out, "outCurtail_B.csv"), na = 0, col.names = TRUE, row.names = FALSE, buffMB = 128, nThread = getDTthreads()-1, append = TRUE)

Header_M[1,1] = "[GWh]"
fwrite(Header_M, file = file.path(Path_Out, "outCurtail.csv"), na = 0, col.names = FALSE, row.names = FALSE, buffMB = 128, nThread = getDTthreads()-1)
fwrite(Curtail_M, file = file.path(Path_Out, "outCurtail.csv"), na = 0, col.names = TRUE, row.names = FALSE, buffMB = 128, nThread = getDTthreads()-1, append = TRUE)


# Líneas Transmisión
Lin_Data <- fread(input = file.path(Path_Case,"plplin.csv"), skip = 0L) %>% filter(Hidro!="MEDIA") %>%
  rename(Hyd=Hidro) %>% mutate(Hyd=as.numeric(Hyd)) %>% arrange(Hyd,Etapa,LinNom)

Lin_Param <- Lin_Data %>% select(LinNom) %>% distinct(LinNom, .keep_all = TRUE)

Lin_Data <- left_join(Lin_Data, blo_eta, by = "Etapa") %>% select(Hyd,Year,Month,Block,Block_Len,LinNom,LinFluP,LinUso) %>%
  mutate(LinFluP = round(LinFluP,3), LinUso = round(LinUso,3))

# Data mensual
Lin_Data_m <- Lin_Data %>% mutate(LinFluP=Block_Len*LinFluP, LinUso=Block_Len*LinUso) %>% group_by(Hyd,Year,Month,LinNom) %>%
  summarise(LinFluP=sum(LinFluP)/24,LinUso=sum(LinUso)/24) %>% mutate(LinFluP = round(LinFluP,3), LinUso = round(LinUso,3))

LinFlu_B <- Lin_Data %>% select(Hyd,Year,Month,Block,LinNom,LinFluP) %>% spread(LinNom,LinFluP)
LinUse_B <- Lin_Data %>% select(Hyd,Year,Month,Block,LinNom,LinUso) %>% spread(LinNom,LinUso)
LinFlu_M <- Lin_Data_m %>% select(Hyd,Year,Month,LinNom,LinFluP) %>% spread(LinNom,LinFluP)
LinUse_M <- Lin_Data_m %>% select(Hyd,Year,Month,LinNom,LinUso) %>% spread(LinNom,LinUso)

# Headers
Header_Data <- Lin_Param

Head_B <- data.table(LinNom=c("","","","Ubic:"))
Head_M <- data.table(LinNom=c("","","Ubic:"))

Header_B <- t(bind_rows(Head_B,Header_Data))
Header_M <- t(bind_rows(Head_M,Header_Data))

# Escribir archivos

Header_B[1,1] = "[MW]"
fwrite(Header_B, file = file.path(Path_Out, "outLinFlu_B.csv"), na = 0, col.names = FALSE, row.names = FALSE, buffMB = 128, nThread = getDTthreads()-1)
fwrite(LinFlu_B, file = file.path(Path_Out, "outLinFlu_B.csv"), na = 0, col.names = TRUE, row.names = FALSE, buffMB = 128, nThread = getDTthreads()-1, append = TRUE)

Header_B[1,1] = "[MW]"
fwrite(Header_M, file = file.path(Path_Out, "outLinFlu.csv"), na = 0, col.names = FALSE, row.names = FALSE, buffMB = 128, nThread = getDTthreads()-1)
fwrite(LinFlu_M, file = file.path(Path_Out, "outLinFlu.csv"), na = 0, col.names = TRUE, row.names = FALSE, buffMB = 128, nThread = getDTthreads()-1, append = TRUE)

Header_B[1,1] = "[%]"
fwrite(Header_B, file = file.path(Path_Out, "outLinUse_B.csv"), na = 0, col.names = FALSE, row.names = FALSE, buffMB = 128, nThread = getDTthreads()-1)
fwrite(LinUse_B, file = file.path(Path_Out, "outLinUse_B.csv"), na = 0, col.names = TRUE, row.names = FALSE, buffMB = 128, nThread = getDTthreads()-1, append = TRUE)

Header_B[1,1] = "[%]"
fwrite(Header_M, file = file.path(Path_Out, "outLinUse.csv"), na = 0, col.names = FALSE, row.names = FALSE, buffMB = 128, nThread = getDTthreads()-1)
fwrite(LinUse_M, file = file.path(Path_Out, "outLinUse.csv"), na = 0, col.names = TRUE, row.names = FALSE, buffMB = 128, nThread = getDTthreads()-1, append = TRUE)

#Fallas
Fail_Data <- fread(input = file.path(Path_Case,"plpfal.csv"), skip = 0L) %>% filter(Hidro!="MEDIA") %>%
  rename(Hyd=Hidro) %>% mutate(Hyd=as.numeric(Hyd)) %>% arrange(Hyd,Etapa,BarNom)

Fail_Data <- left_join(Fail_Data, blo_eta, by = "Etapa") %>% select(Hyd,Year,Month,Block,BarNom,CenPgen,CenEgen) %>%
  mutate(CenPgen = round(CenPgen,3), CenEgen = round(CenEgen,3))

fwrite(Fail_Data, file = file.path(Path_Out, "outFailure_B.csv"), na = 0, col.names = TRUE, row.names = FALSE, buffMB = 128, nThread = getDTthreads()-1)

# Copiar salidas extras
file.copy("plpfal.csv", Path_Out)
file.copy("plpplanos.csv", Path_Out)


# Tiempo final
t_end <- Sys.time()
message(t_end)
t <- t_end-t_ini
message(paste("Process Time: ",floor(t),":",round(60*(t-floor(t)), digits = 0)), collapse = NULL)