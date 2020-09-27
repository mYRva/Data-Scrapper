 # -*- coding: utf-8 -*-
 
import os
import numpy as np
from pathlib import Path

from pandas import DataFrame, read_csv
import pandas as pd 
 
path = u"C:\Users\Rubén Vazquez\Documents\BigBot\Brove\Qualitas\Portal"
         #C:\ Users\ Rubén Vazquez \Documents \BigBot \Brove \Qualitas\ Portal

 
entries = Path(path)
for entry in entries.iterdir():
    print(entry.name)
