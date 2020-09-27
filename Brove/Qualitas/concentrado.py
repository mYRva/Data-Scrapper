 # -*- coding: utf-8 -*-
import numpy as np
import ast
import pandas as pd
import pymysql.cursors
import json

# Connect to the database
connection = pymysql.connect(host='DESKTOP-3BT9MJ6',
                             user='admin',
                             password='Admin01',
                             db='brove',
                             charset='utf8mb4',
                             cursorclass=pymysql.cursors.DictCursor,
                             client_flag = pymysql.constants.CLIENT.MULTI_STATEMENTS)


dsConcentrado = "{dsConcentrado}"

dsConcentrado = ast.literal_eval(dsConcentrado)

arrConci = []

count = 1
#countTest = 0

listado = []
dfWinSef = pd.read_csv('C:\\Brove\\Qualitas\\archivos\\WinSef\\RadGridExport.csv')  

maxLen = len(dfWinSef)
print(maxLen)

for i, j in dfWinSef.iterrows():    
    #if (i < 100):
    polizaWS   = str(j[91])     
    reciboWS   = str(j[103])    
    primaWS    = str(j[94])          
    comisionWS = str(j[32])
 
    try:
        with connection.cursor() as cursor:
            #Insertamos tabla winsef
            sql = " INSERT INTO winsef (poliza, recibo, prima, comision) VALUES ('"+ polizaWS +"', '"+ reciboWS +"', '"+ primaWS +"', '"+ comisionWS +"'); "        
            cursor.execute(sql)
            connection.commit()                        
            #print(sql)                
    finally:
        print(" *** Insercion en WinSef *** " + str(count))
        count = count + 1
        #connection.close()


periodo = ''
for itemQua in dsConcentrado:                
    dia = str(itemQua[0])
    if("DIA" in dia):
        conceptoArr = str(itemQua[0]).split('|')
        if(len(conceptoArr) > 1):            
            periodo = conceptoArr[1]

    if(itemQua[1] != " " and itemQua[1] != "0" and itemQua[1] != "POLIZA" and  "PAGO" not in itemQua[7] and "GTOS" not in itemQua[7]  and itemQua[1] !=""):                       
        
        polizaQ    = str(itemQua[1])             
        arrNo      = itemQua[4].split('-')
        no         = arrNo[1]
        total      = arrNo[0]
        reciboQ    = str(no + "/" + total)    
        primaQ     = str(itemQua[8])    
        comisionQ  = str(itemQua[9])            

        try:
            with connection.cursor() as cursor:
                sql = "INSERT INTO qualitas (poliza, recibo, prima, comision, periodo) VALUES ('"+ polizaQ +"', '"+ reciboQ +"', '"+ primaQ +"', '"+ comisionQ +"', '"+ periodo +"');"
                #Insertamos control de recibos
                cursor.execute(sql)
                connection.commit()                        
            
        finally:
            print(" *** Insercion Qualitas *** ")                       

     
connection.close()
print(" *** ya acabe *** ")
#SetVar('layout',  arrConci)    