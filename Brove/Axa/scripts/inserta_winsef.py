 # -*- coding: utf-8 -*-
import numpy as np
import ast
import pandas as pd
import pymysql.cursors
import json
import math
from datetime import datetime

# Connect to the database
connection = pymysql.connect(host='DESKTOP-3BT9MJ6',
                             user='admin',
                             password='Adminin01',
                             db='brove',
                             charset='utf8mb4',
                             cursorclass=pymysql.cursors.DictCursor,
                             client_flag = pymysql.constants.CLIENT.MULTI_STATEMENTS)



def getEndosoChubb(poliza_ws):
    endoso_chubb = "0"
    rows=""
    try:
        with connection.cursor() as cursor:
              sql = "SELECT endoso FROM chubb where poliza = '" + poliza_ws + "'"
              
              cursor.execute(sql)
              rows = cursor.fetchall()

            
    
    finally:        
        sql=""
        #connection.close()

    for row in rows:
        lista = pd.DataFrame.from_dict(row, orient = 'index')    
        endoso_chubb = lista[0]['endoso']
 
    return endoso_chubb

 
pathWnsef     = r"C:\\Brove\\Axa"
                 
fileNameWinSef = "winsef.csv"

#dsConcentrado = ast.literal_eval(dsConcentrado)

arrConci = []

count = 1

listado = []

dfWinSef = pd.read_csv(pathWnsef + '\\' + fileNameWinSef, escapechar='\\')  

maxLen = len(dfWinSef)
print("max : " + str(maxLen))

periodo  = ''
contador = 0

for i, j in dfWinSef.iterrows():    
   
    prima_moneda_origen    = 0
    comision_moneda_origen = 0
    
    poliza_ws   = str(j[92]).replace(' ','').strip()   
    #poliza_ws     = str(poliza_data[1]).strip()   
    
    reciboWS      = str(j[104]).split('/')
    no_recibos    = str(reciboWS[0]).replace('.','')
    total_recibos = reciboWS[1] 
    primaWS       = float(j[95])
    tipo_cambio   = float(j[111])          
    fecha_cobro   = str(j[56])
    forma_pago    = str(j[73])    
    
    comision_abonada   = str(j[28])
    comision_gastos    = str(j[29])
    comision_neta      = str(j[32])
    comision_recargo   = str(j[34])
    endoso_raw         = str(j[49])#.split('-')
    moneda_descripcion = str(j[83])
    endoso_ws           = endoso_raw#str(j[89]).strip()
    fecha_inicio_vigencia = str(j[65])
    #if(len(endoso_raw) > 1):
    #    endoso_ws  = endoso_raw[0]
    #else:
    #   endoso_raw = str(j[49]).split(' ')    
    #if(endoso_chubb == 'nan' or endoso_chubb == ""):
    #    endoso_chubb = getEndosoChubb(poliza_ws)
    #else:
    #    endoso_chubb = math.trunc(float(endoso_chubb))
   
    #print("póliza: '"+ poliza_ws +"', endoso_chubb: " + str(endoso_chubb))
    #endoso_ws  =  endoso_chubb#endoso_raw
    #print(fecha_inicio_vigencia)
    date_dt2 = datetime.strptime(fecha_inicio_vigencia[0:8], '%d/%m/%y')
   
    comision = float(comision_neta)  + \
               float(comision_abonada) + \
               float(comision_gastos) + \
               float(comision_recargo)
    
    recargos = float(j[98])

    if (tipo_cambio != 1):
        prima_moneda_origen = (float(primaWS) + float(recargos)) 
        comision_moneda_origen = comision
       
    comision_final = comision * tipo_cambio 
    prima_neta     = (float(primaWS) + float(recargos)) * tipo_cambio
    
    if(endoso_ws == "nan"):
        endoso_ws = "0"       
    if (forma_pago == "MENSUAL"):
        id_forma_pago = 1
    if (forma_pago == "BIMESTRAL"):
        id_forma_pago = 2
    if (forma_pago == "TRIMESTRAL"):
        id_forma_pago = 3
    if (forma_pago == "SEMESTRAL"):
        id_forma_pago = 5
    if (forma_pago == "CONTADO"):
        id_forma_pago = 6
    if (forma_pago == "ANUAL"):
        id_forma_pago = 7
    if (forma_pago == "MULT ANUAL"):
        id_forma_pago = 8
    if (forma_pago == "MULT CONT"):                       
        id_forma_pago = 9 
     
    try:
        with connection.cursor() as cursor:
            #Insertamos tabla winsef
            sql = " INSERT INTO winsef (poliza, endoso, no_recibos, total_recibos, " \
                  " prima, prima_neta, recargos, comision, fecha_cobro, tipo_cambio, " \
                  " id_forma_pago, endoso_rh, prima_moneda_origen, comision_moneda_origen, " \
                  " moneda_descripcion, fecha_inicio_vigencia) VALUES ('"+ poliza_ws + "', '" + str(endoso_ws) + "', '" + no_recibos + \
                  "', '" + total_recibos + "', '"+ str(primaWS) +"', '"+ str(prima_neta) +"', '"+ \
                   str(recargos) +"', '"+ str(comision_final) +"', '"+ fecha_cobro + \
                   "', '"+ str(tipo_cambio) +"', '" + str(id_forma_pago) + "', 0, '"+ \
                   str(prima_moneda_origen) + "', '"+ str(comision_moneda_origen) +"', '"+ moneda_descripcion +"', '"+ str(date_dt2) +"'); "
            #print(sql)
            #print("fecha_inicio_vigencia " + fecha_inicio_vigencia )
            cursor.execute(sql)
            connection.commit()                                                   
    finally:
        print(" *** Insercion en WinSef *** " + str(count))
        count = count + 1
  
connection.close()
print(" *** done *** ")