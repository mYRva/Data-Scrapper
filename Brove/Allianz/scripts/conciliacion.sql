select
	ws.poliza as poliza_winsef,
	allz.poliza as poliza_allianz,
	concat(".",ws.no_recibos, "/", ws.total_recibos) as recibos_winsef,		
	concat(".",allz.serie_no, "/", allz.serie_total) as recibos_allianz,
 	allz.recibo as recibo_allianz,
    round(ws.prima_neta,2) as prima_winsef,
	round(ws.recargos,2) as recargos_winsef,
	round(allz.prima,2) as prima_allianz,		        
	round(ws.comision,2) as comision_wisef,
	round(allz.comision_importe,2) as comision_allianz,		
	round(allz.prima - ws.prima_neta,2)  as diferencia_primas,
	round(allz.comision_importe - ws.comision,2) as diferencia_comisiones,
	allz.cve_Agente as agente,
	allz.fecha_aplicacion as fecha_aplicacion_allianz,
    ws.fecha_cobro as fecha_cobro_winsef,
	ws.tipo_cambio as tipo_cambio,
	'' as forma_pago_desc#fp.forma_pago_desc
from brove.winsef ws
right join brove.allianz allz on TRIM(LEADING '0' FROM ws.poliza) = TRIM(LEADING '0' FROM allz.poliza)
							  and TRIM(LEADING '0' FROM ws.no_recibos)    = TRIM(LEADING '0' FROM allz.serie_no) 
							  and TRIM(LEADING '0' FROM ws.total_recibos) = TRIM(LEADING '0' FROM allz.serie_total)
                              #and ws.endoso = allz.recibo
#nner join forma_pago fp on ws.id_forma_pago = fp.idforma_pago
where allz.poliza not in (select poliza from allianz where ramo in (189,191,192,194,196,197)
and serie_no = 0 and serie_total = 0 and allz.prima = 0)
and ws.poliza is null

 union all

select 
	'' as poliza_winsef,
	'PLUS GENERICA A PARTIR 20' as poliza_allianz,
	'' as recibos_winsef,		
	'' as recibos_allianz,
 	'' as recibo,
    '' as prima_winsef,
	'' as recargos_winsef,
	'' as prima_allianz,		        
	'' as comision_winsef,
	round(sum(importe_neto),2) as comision_allianz,		
	''  as diferencia_prima,
	'' as diferencia_comision,
 	'' as agente,
    '' as fecha_aplicacion_allianz,
    '' as fecha_cobro_winsef,
	'' as tipo_cambio,
	'' as forma_pago_desc
from brove.winsef ws
	right join brove.Allianz allz on TRIM(LEADING '0' FROM ws.poliza) = TRIM(LEADING '0' FROM allz.poliza)  
where ramo in (189,191,192,194,196,197)
and serie_no = 0 and serie_total = 0 and allz.prima = 0
group by ws.endoso;
 
 
 