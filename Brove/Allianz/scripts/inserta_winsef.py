 # -*- coding: utf-8 -*-
import numpy as np
import ast
import pandas as pd
import pymysql.cursors
import json
import math
 

# Connect to the database
connection = pymysql.connect(host='DESKTOP-3BT9MJ6',
                             user='admin',
                             password='Adminin01',
                             db='brove',
                             charset='utf8mb4',
                             cursorclass=pymysql.cursors.DictCursor,
                             client_flag = pymysql.constants.CLIENT.MULTI_STATEMENTS)



def getReciboAllianz(poliza_ws):
    recibo_allianz = "0"
    rows=""
    try:
        with connection.cursor() as cursor:
              sql = "SELECT recibo FROM allianz where poliza = " + poliza_ws + ""
              
              cursor.execute(sql)
              rows = cursor.fetchall()

            
    
    finally:        
        sql=""
        #connection.close()

    for row in rows:
        lista = pd.DataFrame.from_dict(row, orient = 'index')    
        recibo_allianz = lista[0]['recibo']
 
    return recibo_allianz

 
pathWnsef     = r"C:\\Brove\\Allianz"
                 
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
    
    poliza_data   = str(j[92]).replace('/','-').split('-')   
    poliza_ws     = str(poliza_data[1]).strip()
    
    
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
    recibo_pago_allz   = str(j[89]).strip()
    
    #if(len(endoso_raw) > 1):
    #    endoso_ws  = endoso_raw[0]
    #else:
    #   endoso_raw = str(j[49]).split(' ')    
    if(recibo_pago_allz == 'nan' or recibo_pago_allz == ""):
        recibo_pago_allz = getReciboAllianz(poliza_ws)
   
    #print("póliza: '"+ poliza_ws +"', recibo_pago_allz: " + recibo_pago_allz) 
    endoso_ws  =  recibo_pago_allz#endoso_raw
    
    #if(endoso_ws == "nan"):
    #    endoso_ws = "0"
   
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
    
    #if(endoso_ws == "nan"):
    #    endoso_ws = "0"       
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
                  " moneda_descripcion) VALUES ('"+ poliza_ws + "', '" + endoso_ws + "', '" + no_recibos + \
                  "', '" + total_recibos + "', '"+ str(primaWS) +"', '"+ str(prima_neta) +"', '"+ \
                   str(recargos) +"', '"+ str(comision_final) +"', '"+ fecha_cobro + \
                   "', '"+ str(tipo_cambio) +"', '" + str(id_forma_pago) + "', 0, '"+ \
                   str(prima_moneda_origen) + "', '"+ str(comision_moneda_origen) +"', '"+ moneda_descripcion +"'); "
            
            cursor.execute(sql)
            connection.commit()                                                   
    finally:
        print(" *** Insercion en WinSef *** " + str(count))
        count = count + 1
  
connection.close()
print(" *** ya acabe *** ")