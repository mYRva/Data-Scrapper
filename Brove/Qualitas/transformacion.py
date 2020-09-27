import numpy as np
import ast
 
import win32com.client as win32

archivo = "{archivoTrans}" 

fname = archivo
excel = win32.gencache.EnsureDispatch('Excel.Application')
wb = excel.Workbooks.Open(fname)

wb.SaveAs(fname+"x", FileFormat = 51)    #FileFormat = 51 is for .xlsx extension
wb.Close()                               #FileFormat = 56 is for .xls extension
excel.Application.Quit()

os.remove(archivo)