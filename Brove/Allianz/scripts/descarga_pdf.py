import urllib.request

print('Beginning file download with urllib2...')

url = 'https://www5.abaseguros.com/Agentes/Comisiones/EstadoCuenta/VistaPreviaEstadoCuenta.asp?RutaPDF=/pdfs/EstadoDeCuenta_31069_93679_202008_02_20200825_222253.pdf'
urllib.request.urlretrieve(url, 'C:/Brove/Chubb/PDFs/EstadoDeCuenta_31069_93679_202007_02_20200825_193335.pdf')