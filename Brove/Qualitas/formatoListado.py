import ast

ds = "{ds}" 
dsFinal = "{dsFinal}"
ds = ast.literal_eval(ds)
dsFinal = ast.literal_eval(dsFinal)

SetVar('dsFinal',  ds + dsFinal)   