import pymysql.cursors

from tabula import read_pdf
import PyPDF2
import json
import os
import pandas as pd    
import csv

connection = pymysql.connect(host='DESKTOP-3BT9MJ6',
                             user='admin',
                             password='Adminin01',
                             db='brove',
                             charset='utf8mb4',
                             cursorclass=pymysql.cursors.DictCursor,
                             client_flag = pymysql.constants.CLIENT.MULTI_STATEMENTS)

path = 'C:\Brove\Chubb\PDFs'
files = []

for r,d,f in os.walk(path):
    for file in f:
        files.append(os.path.join(r, file))

for f in files:
    no_pages = PyPDF2.PdfFileReader(open(f, 'rb')).getNumPages()
    #print(f)
    count = 2
    while(count <= no_pages):
        df = read_pdf(f, output_format="json", pages=count)
        #Insertamos en tabla de Chubb
        data = str(df).replace('\'','"')

        _data = json.loads(data)
        
        datos = json.loads(str(_data[0]).replace('\'','"'))
        
        datos_detalle = datos['data']
        datos_detalle_encabezado = datos_detalle[0]        

        #recorremos el listado
        no_detalle = 0
        for elem in datos_detalle:
            #print("ELEMENTO:")
            #print(elem)

            if (no_detalle >= 2 and str(elem[0]['text']) != ''):
                fecha_pago   = str(elem[0]['text'])
                poliza       = str(elem[1]['text'])
                endoso       = str(elem[2]['text'])
                inciso       = str(elem[3]['text'])
                recibo       = str(elem[4]['text'])
                cons_recibo  = str(elem[5]['text'])
                ramo         = str(elem[6]['text'])
                ini_vigencia = str(elem[7]['text'])
                fin_vigencia = str(elem[8]['text'])
                asegurado    = str(elem[9]['text'])
                conducto     = str(elem[10]['text'])
                prima_neta   = str(elem[11]['text']).replace(",","").replace("$","")
                comision     = str(elem[12]['text']).replace(",","").replace("$","")
                csr          = str(elem[13]['text']).replace(",","").replace("$","")
                tipo_cambio  = str(elem[14]['text']).replace(",","").replace("$","")
                total_mxn    = str(elem[15]['text']).replace(",","").replace("$","")           
                
                #Insertamos en tabla Chubb
                #print("fecha_pago: " + fecha_pago, "poliza: "+ poliza,  "endoso: "+ endoso , "inciso: "+ inciso, "recibo: " + recibo, "cons_recibo: "+ cons_recibo, "ramo: " +  ramo, "ini_vigencia: " + ini_vigencia,  "fin_vigencia: " + fin_vigencia, "asegurado: " +  asegurado, "conducto: " + conducto, "prima_neta: "+ prima_neta, "comision: " + comision , "csr: "+ csr,  " tipo_cambio: "+ tipo_cambio,  "total_mxn: "+ total_mxn)


                try:
                    with connection.cursor() as cursor:
                        #Insertamos tabla allianz

                        sql = " insert into chubb (fecha_pago, poliza, endoso, inciso, " \
                            " recibo, cons_recibo, ramo, ini_vigencia, fin_vigencia, asegurado, " \
                            " conducto, prima_neta, comision, csr, tipo_cambio, total_mxn) " \
                            " values ('"+ fecha_pago + "', '" + poliza + "', '" + endoso + \
                            "', '" + inciso + "', '"+ recibo +"', '"+ cons_recibo +"', '"+ \
                            ramo +"', '" + ini_vigencia +"', '"+ fin_vigencia + \
                            "', '"+ asegurado +"', '" + conducto + "', '"+ prima_neta +"', '"+ \
                            comision + "', '"+ csr +"', '"+ tipo_cambio +"', '" + total_mxn + "'); "

                        print(sql)
                        cursor.execute(sql)
                        connection.commit()                                                   

                finally:
                    print('Insercion de Chub: '+ str(no_detalle))
                    
            
            no_detalle = no_detalle + 1

        count = count + 1 