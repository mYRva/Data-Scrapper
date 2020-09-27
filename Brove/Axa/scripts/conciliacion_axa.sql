select 	
    axa.tipo_usuario,
    ws.poliza as poliza_winsef,
	axa.poliza as poliza_axa,
    ws.endoso as endoso_winsef,
    axa.endoso as endoso_axa,
	ws.fecha_inicio_vigencia as fecha_inicio_vigencia_winsef,		
	axa.anio_vigor as 'Año Vigor',
	ws.prima_neta as prima_winsef,
	round(sum(ws.recargos),2) as recargos_winsef,
	round(sum(axa.prima_neta),2) as prima_axa,
	round(sum(ws.comision),2) as comision_wisef,
	round(sum(axa.comision_s_prima),2) as comision_axa,	
	round(sum(axa.prima_neta) - ws.prima_neta, 2)  as diferencia_primas,
	round(sum(axa.comision_s_prima) - ws.comision, 2) as diferencia_comisiones,
    ws.fecha_cobro as fecha_cobro_winsef,
    #chb.fecha_pago as fecha_pago_chubb,
	ws.tipo_cambio as tipo_cambio
	#'' as forma_pago_desc
from brove.winsef ws
inner join  brove.axa axa on ws.poliza = axa.poliza
							and ws.fecha_inicio_vigencia = axa.anio_vigor
#where ws.poliza is null
#where ws.poliza = 'FW52376E'
group by axa.poliza, axa.anio_vigor							

#select * from winsef where poliza = 'FW52376E'
#select * from axa where poliza = 'FW52376E'
                             



                             