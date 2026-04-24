"""
Copyright (c) 2026 Ed Millard

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
from __future__ import annotations
import importlib
import importlib.util
import inspect
from pathlib import Path
from typing import Optional, Dict, Any, Type

class Registry:
    def __init__(self, name: str):
        self.name = Path(name)
        self.registry: Dict[str, Dict[str, Any]] = {}

        self._load_all()

    def _load_all(self):
        """Dynamically load all classes from the directory"""
        base_class_name = str(self.name)[:-1]
        base_class_name = base_class_name + '.py'
        if not self.name.exists():
            print(f"Warning: directory not found: {self.name}")
            return

        for file in sorted(self.name.glob("*.py")):
            if file.name == base_class_name:
                continue
            if file.name.startswith("__"):
                continue

            module_name = file.stem

            try:
                # === Proper way to import dynamically ===
                spec = importlib.util.spec_from_file_location(module_name, str(file))
                if spec is None or spec.loader is None:
                    continue

                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # Find the main class (most likely class whose name matches the file)
                for _, obj in inspect.getmembers(module, inspect.isclass):
                    if (obj.__module__ == module_name and
                            not obj.__name__.startswith('_')):  # Main public class

                        nice_name = Registry._make_nice_name(module_name)

                        self.registry[nice_name] = {
                            "constructor": obj,  # Class itself
                            "instance": None,  # Instantiated object
                            "module": module,
                            "filepath": str(file)
                        }
                        print(f"✓ Loaded: {nice_name}")
                        break
                else:
                    print(f"⚠ No suitable class found in {file.name}")

            except Exception as e:
                print(f"✗ Failed to load {file.name}: {e}")

    @staticmethod
    def _make_nice_name(filename: str) -> str:
        return filename.replace("_", " ").replace("-", " ").title()

    # ====================== Convenience Methods ======================

    def get_instance(self, name: str) -> Optional[Any]:
        entry = self.registry.get(name)
        return entry["instance"] if entry else None

    def get_constructor(self, name: str) -> Optional[Type]:
        entry = self.registry.get(name)
        return entry["constructor"] if entry else None

    def list_all(self) -> list[str]:
        return sorted(self.registry.keys())
