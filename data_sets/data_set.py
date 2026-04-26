"""
Copyright (c) 2025 Ed Millard

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute copies of the Software, and
to permit persons to whom the Software is furnished to do so, subject to the
following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
from typing import Optional
from api.registry import Registry
from pathlib import Path
import pandas as pd

class DataSet:
    def __init__(self, name:str, month:int=10):
        self.name:str = name
        self.month:int = month
        self.df:Optional[pd.DataFrame]=None

    def load(self)->Optional[pd.DataFrame]:
        return None

    @staticmethod
    def to_csv(path:Path, df:pd.DataFrame):
        path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(
            path,
            index=False,            # Don't write the row index
            # float_format='%.6g',  # Clean floats (removes most trailing zeros)
            encoding='utf-8',
            na_rep='',              # Empty for NaN
            # date_format='%Y-%m-%d'  # if you have any date columns
        )

    def from_csv(self, filename:str)->pd.DataFrame:
        filename = Registry.make_nodule_name(filename)
        df:Optional[pd.DataFrame] = None
        base_path:Path = Path('data/riverwar')
        path = Path(base_path) / filename
        path = path.with_suffix('.csv')
        if path.exists():
            df = pd.read_csv(
                path,
                dtype={'Year': 'Int64'},  # Best for years
                float_precision='high'
            )
        else:
            df = self.load()
            DataSet.to_csv(path, df)
        return df

class DataSetRegistry(Registry):
    def __init__(self, name: str = "datasets"):
        super().__init__(name)

    def get(self, name) -> Optional[DataSet]:
        instance: Optional[DataSet] = None
        dataset_registry = self.registry[name]
        if dataset_registry is not None:
            instance = dataset_registry["instance"]
            if instance is None:
                constructor = dataset_registry["constructor"]
                if constructor is not None:
                    instance = constructor(name)
                    dataset_registry["instance"] = instance
        return instance