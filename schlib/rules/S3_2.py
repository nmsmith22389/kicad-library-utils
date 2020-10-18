# -*- coding: utf-8 -*-

from rules.rule import *


class Rule(KLCRule):
    """
    Create the methods check and fix to use with the kicad lib files.
    """
    v6 = True
    def __init__(self, component):
        super(Rule, self).__init__(component, 'Text properties should use common size of 50mils, but labels and numbers may use text size as low as 20mil if required')

    def check(self):
        """
        Proceeds the checking of the rule.
        The following variables will be accessible after checking:
            * violating_pins
            * violating_properties
        """
        self.violating_properties = []
        for prop in self.component.properties:
            text_size = self.mm_to_mil(prop.effects.sizex)
            if (text_size != 50):
                self.violating_properties.append(prop)
                message = ("{0} at posx {1} posy {2}".format(prop.name, self.mm_to_mil(prop.posx), self.mm_to_mil(prop.posy)))
                self.error(" - Field {0} size {1}".format(message, text_size))

        self.violating_pins = []

        """
        Pin number MUST be 50mils
        Pin name must be between 20mils and 50mils
        Pin name should be 50mils
        """

        for pin in self.component.pins:
            name_text_size = self.mm_to_mil(pin.name_effect.sizex)
            num_text_size = self.mm_to_mil(pin.number_effect.sizex)

            if (name_text_size < 20) or (name_text_size > 50) or (num_text_size < 20) or (num_text_size > 50):
                self.violating_pins.append(pin)
                self.error(' - Pin {0} ({1}), text size {2}, number size {3}'.format(pin.name, pin.number, name_text_size, num_text_size))
            else:
                if name_text_size != 50:
                    self.warning("Pin {0} ({1}) name text size should be 50mils (or 20...50mils if required by the symbol geometry)".format(pin.name, pin.number))
                if num_text_size != 50:
                    self.warning("Pin {0} ({1}) number text size should be 50mils (or 20...50mils if required by the symbol geometry)".format(pin.name, pin.number))

        if (len(self.violating_properties) > 0 or
            len(self.violating_pins) > 0):
            return True

        return False

    def fix(self):
        """
        Proceeds the fixing of the rule, if possible.
        """
        if len(self.violating_properties) > 0:
            self.info("Fixing field text size")
        for prop in self.violating_properties:
            prop.effects.sizex = self.mil_to_mm(50)
            prop.effects.sizey = self.mil_to_mm(50)

        if len(self.violating_pins) > 0:
            self.info("Fixing pin text size")
        for pin in self.violating_pins:
            pin.name_effect.sizex = self.mil_to_mm(50)
            pin.name_effect.sizey = self.mil_to_mm(50)
            pin.number_effect.sizex = self.mil_to_mm(50)
            pin.number_effect.sizey = self.mil_to_mm(50)
        self.recheck()
