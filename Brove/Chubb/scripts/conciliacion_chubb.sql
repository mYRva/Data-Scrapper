select 	
    ws.poliza as poliza_winsef,
	chb.poliza as poliza_chubb,
    ws.endoso as endoso_winsef,
    chb.endoso as endoso_chubb,
	concat(".", ws.no_recibos, "/", ws.total_recibos) as recibos_winsef,		
	concat(".", chb.cons_recibo) as recibos_chubb,
	round(ws.prima_neta,2) as prima_winsef,
	round(ws.recargos,2) as recargos_winsef,
	round(sum(chb.prima_neta),2) as prima_chubb,		        
	round(ws.comision,2) as comision_wisef,
	round(sum(chb.total_mxn),2) as comision_chubb,		
	round(sum(chb.prima_neta) - ws.prima_neta, 2)  as diferencia_primas,
	round(sum(chb.total_mxn) - ws.comision, 2) as diferencia_comisiones,
    ws.fecha_cobro as fecha_cobro_winsef,
    chb.fecha_pago as fecha_pago_chubb,
	ws.tipo_cambio as tipo_cambio,
	'' as forma_pago_desc
from brove.winsef ws
right join  brove.chubb chb on ws.poliza = chb.poliza
							and concat(ws.no_recibos, "/", ws.total_recibos) =  chb.cons_recibo 
							and ws.endoso = chb.endoso
where ws.poliza is null
group by chb.poliza, chb.cons_recibo, chb.endoso; #right and inner
#group by ws.poliza, ws.no_recibos, ws.total_recibos, ws.endoso; #left

#select * from chubb
 
 
 
 