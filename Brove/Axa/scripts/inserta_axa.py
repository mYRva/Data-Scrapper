import pandas as pd
import ast
import pymysql.cursors
from datetime import datetime

connection = pymysql.connect(host='DESKTOP-3BT9MJ6',
                             user='admin',
                             password='Adminin01',
                             db='brove',
                             charset='utf8mb4',
                             cursorclass=pymysql.cursors.DictCursor,
                             client_flag = pymysql.constants.CLIENT.MULTI_STATEMENTS)

ds_axa = "{tabla}"
str_tipo_usuario = "{tipo_usuario}"
#print(ds_axa)
ds_axa_lit = ast.literal_eval(ds_axa)  

#print(ds_axa_lit)
no_detalle = 1
for item in ds_axa_lit:
    if (item[0] == "MN"):
        #leemos el registro        
        moneda           = item[0]
        ramo             = item[1]
        asegurado        = item[2]
        poliza           = item[3]
        endoso           = item[4]
        vigor            = item[5]# + "20"
        dia              = item[6]
        contable         = item[7]
        caja             = item[8]
        prima_neta       = str(item[9]).replace('.','').replace(',','.')
        prima_total      = str(item[10]).replace('.','').replace(',','.')
        comision_s_prima = str(item[11]).replace('.','').replace(',','.')
        derechos         = str(item[12]).replace('.','').replace(',','.')
        recargos         = str(item[13]).replace('.','').replace(',','.')
        total            = str(item[14]).replace('.','').replace(',','.')
        tipo_usuario     = str_tipo_usuario

 
        date_dt2 = datetime.strptime(vigor, '%d/%m/%y')

        try:
            with connection.cursor() as cursor:
                #Insertamos tabla allianz

                sql = " insert into axa (moneda, ramo, asegurado, poliza, " \
                    " endoso, anio_vigor, dia, comprobante_contable, comprobante_caja, prima_neta, " \
                    " prima_total, comision_s_prima, derechos, recargos, total, tipo_usuario) " \
                    " values ('"+ moneda + "', '" + ramo + "', '" + asegurado + \
                    "', '" + poliza + "', '"+ endoso +"', '"+ str(date_dt2) +"', '"+ \
                    dia +"', '" + contable +"', '"+ caja + \
                    "', '"+ prima_neta +"', '" + prima_total + "', '"+ comision_s_prima +"', '"+ \
                    derechos + "', '"+ recargos +"', '"+ total +"', '" + tipo_usuario + "'); "

                #print(sql)
                cursor.execute(sql)
                connection.commit()                                                   

        finally:
            print('Insercion de Axa: '+ str(no_detalle))
        
        no_detalle = no_detalle + 1
