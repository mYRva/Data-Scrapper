import os
import shutil

periodo  = "{periodo}"


pathSource = 'C:\\Brove\\Qualitas\\archivos\\descargas\\'
pathDest = 'C:\\Brove\\Qualitas\\archivos\\Portal\\'
for file in os.listdir(pathSource):
    if file.endswith(".xls"):      
        newfile = file.replace('.xls','') + "-" + periodo + ".xls"
        shutil.move(pathSource + file, pathDest + newfile)  
        print(newfile)

SetVar('archivo_periodo', newfile)