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
import pandas as pd

class DataSet:
    def __init__(self, name:str, month:int=10):
        self.name:str = name
        self.month:int = month
        self.df:Optional[pd.DataFrame]=None

class DataSetRegistry(Registry):
    def __init__(self, name: str = "datasets"):
        super().__init__(name)

    def get(self, name) -> Optional[DataSet]:
        instance: Optional[DataSet] = None
        reservoir_registry = self.registry[name]
        if reservoir_registry is not None:
            instance = reservoir_registry["instance"]
            if instance is None:
                constructor = reservoir_registry["constructor"]
                if constructor is not None:
                    instance = constructor(name)
                    reservoir_registry["instance"] = instance
        return instance
