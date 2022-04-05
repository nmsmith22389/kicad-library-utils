# -*- coding: utf-8 -*-

import os
import sys

common = os.path.abspath(os.path.join(sys.path[0], '..', 'common'))

if common not in sys.path:
    sys.path.append(common)

from kicad_sym import KicadSymbol, Pin, mil_to_mm, mm_to_mil
from rulebase import KLCRuleBase, Verbosity


def pinString(pin: Pin, loc: bool = True, unit = None, convert = None) -> str:
    return "Pin {name} ({num}){loc}{unit}".format(
        name=pin.name,
        num=pin.number,
        loc=' @ ({x},{y})'.format(x=mm_to_mil(pin.posx), y=mm_to_mil(pin.posy)) if loc else '',
        unit=' in unit {n}'.format(n=pin.unit) if unit else '')


def positionFormater(element) -> str:
    if type(element) == type({}):
        if(not {"posx", "posy"}.issubset(element.keys())):
            raise Exception("missing keys 'posx' and 'posy' in"+str(element))
        return "@ ({0}, {1})".format(mm_to_mil(element['posx']), mm_to_mil(element['posy']))
    if 'posx' in element.__dict__ and 'posy' in element.__dict__:
        return "@ ({0}, {1})".format(mm_to_mil(element.posx), mm_to_mil(element.posy))
    raise Exception("input type: ", type(element), "not supported, ", element)


class KLCRule(KLCRuleBase):
    """A base class to represent a KLC rule

    Create the methods check and fix to use with the kicad lib files.
    """
    verbosity: Verbosity = Verbosity.NONE

    def __init__(self, component: KicadSymbol):
        super().__init__()
        self.component: KicadSymbol = component
