#!/usr/bin/env python
from dataclasses import dataclass

@dataclass
class MaterialCost:
    name:str
    cost:float
    margin_percentage:float
    margins: tuple

    def update(self, cost=None, margin_percentage=None, margins=None):
        """
        Update the cost of the material

        """
        return None