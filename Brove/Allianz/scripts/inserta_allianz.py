import pymysql.cursors
import json
import os
import pandas as pd

# Connect to the database
connection = pymysql.connect(host='DESKTOP-3BT9MJ6',
                             user='admin',
                             password='Adminin01',
                             db='brove',
                             charset='utf8mb4',
                             cursorclass=pymysql.cursors.DictCursor,
                             client_flag = pymysql.constants.CLIENT.MULTI_STATEMENTS)
 
path = 'C:\Brove\Allianz\docs'

files = []

for r,d,f in os.walk(path):
    for file in f:
        files.append(os.path.join(r, file))

for f in files: 
      
    df = pd.read_csv(f)
    count = 1
    for i, j in df.iterrows():
        
        cve_agente          = str(j[0]).replace('\'','')
        ramo                = str(j[1])
        recibo              = str(j[2]).replace('\'','').strip()
        poliza              = str(j[3]).replace('\'','').strip()
        serie               = str(j[4])
        prima               = str(j[5])
        comision_porcentaje = str(j[6]).strip()
        comision_importe    = str(j[7])
        iva                 = str(j[8])
        isr                 = str(j[9])
        impuesto_cedular    = str(j[10])
        retencion           = str(j[11])
        importe_neto        = str(j[12])
        fecha_aplicacion    = str(j[13])

        #formateamos serie con leading zeros en caso de 3 digitos
        serie_no = '0'
        serie_total = '0'

        fecha_aplicacion = fecha_aplicacion[6:8] + "/" + fecha_aplicacion[4:6] + "/" + fecha_aplicacion[0:4]

        if(len(serie) == 4):
            serie_no    = serie[0:2]
            serie_total = serie[2:4]

        if(len(serie) == 3):
            serie_no    = serie[0:1].zfill(2) 
            serie_total = serie[1:3]        

        try:
            with connection.cursor() as cursor:
                #Insertamos tabla allianz

                sql = " INSERT INTO allianz (cve_agente, ramo, recibo, poliza, " \
                    " serie_no, serie_total, prima, comision_porcentaje, comision_importe, iva, isr, " \
                    " impuesto_cedular, retencion, importe_neto, fecha_aplicacion) " \
                    " VALUES ('"+ cve_agente + "', '" + ramo + "', '" + recibo + \
                    "', '" + poliza + "', '" + serie_no + "', '" + serie_total + "', '"+ str(prima) +"', '"+ \
                    str(comision_porcentaje) +"', '"+ str(comision_importe) +"', '"+ iva + \
                    "', '"+ str(isr) +"', '" + str(impuesto_cedular) + "', '"+ retencion +"', '"+ \
                    str(importe_neto) + "', '"+ str(fecha_aplicacion) +"'); "
                
                #print(sql)

                cursor.execute(sql)
                connection.commit()                                                   

        finally:
            print('Insercion de Allianz archivo: '+ str(f) + '/ No: ' + str(count))
            count = count + 1