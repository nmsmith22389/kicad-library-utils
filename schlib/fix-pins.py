#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
from schlib import *
import argparse

# cases covered by this script:
#  (1) resize pins with posx wrong if component has pins with L direction but not R direction
#  (2) resize pins with posx wrong if component has pins with R direction but not L direction
#  (3) resize pins with posy wrong if component has pins with U direction but not D direction
#  (4) resize pins with posy wrong if component has pins with D direction but not U direction
#  (5) resize pins with posx wrong if component has at least one pin wrong in each of the following direction: L, R
#  (6) resize pins with posy wrong if component has at least one pin wrong in each of the following direction: U, D
#  (7) shifts pins with posx to 100mil grid if pin is in U or D direction
#  (8) shifts pins with posy to 100mil grid if pin is in L or R direction

class CheckComponent(object):
    def __init__(self, component):
        self.component = component
        self.prerequisites_ok = False
        self.header_printed = False

        self.pinsL = component.filterPins(direction='L')
        self.pinsL_count = len(self.pinsL)
        self.pinsR = component.filterPins(direction='R')
        self.pinsR_count = len(self.pinsR)
        self.pinsU = component.filterPins(direction='U')
        self.pinsU_count = len(self.pinsU)
        self.pinsD = component.filterPins(direction='D')
        self.pinsD_count = len(self.pinsD)

        self.need_fix_L = False
        self.need_fix_R = False
        self.need_fix_U = False
        self.need_fix_D = False

        if args.verbose:
            print('\tConsidering component: %s' % component.name)

        ## check the prerequisites

        # component has only one rectangle
        # assuming it as the body of the component
        if len(component.draw['rectangles']) != 1:
            if args.verbose:
                print('\t\tNumber of rectangles != 1')
            return

        # all pins L and R have the same size
        lengths = []
        if self.pinsL_count > 0:
            lengths += [pin['length'] for pin in self.pinsL]
        if self.pinsR_count > 0:
            lengths += [pin['length'] for pin in self.pinsR]
        if lengths and lengths.count(lengths[0]) != len(lengths):
            if args.verbose:
                print('\t\tMore than one pin length encountered on left or right side')
            return

        # all pins U and D have the same size
        lengths = []
        if self.pinsU_count > 0:
            lengths += [pin['length'] for pin in self.pinsU]
        if self.pinsD_count > 0:
            lengths += [pin['length'] for pin in self.pinsD]
        if lengths and lengths.count(lengths[0]) != len(lengths):
            if args.verbose:
                print('\t\tMore than one pin length encountered on top or bottom')
            return

        # pins length have to be multiple of 50mil
        for pin in component.pins:
            if (int(pin['length']) % 50) != 0:
                if args.verbose:
                  print('\t\tPin lengths are not all multiples of 50mil')
                return

        # pins posx and posy have to be multiple of 50mil
        for pin in component.pins:
            if (int(pin['posx']) % 50) != 0 or (int(pin['posy']) % 50) != 0:
                if args.verbose:
                  print('\t\tPin positions are not all multiples of 50mil')
                return

        # check if at least one pin is wrong in each direction
        if self.pinsL_count > 0 and self.pinsR_count > 0:
            for pin in self.pinsL:
                posx = int(pin['posx'])
                if (posx % 100) != 0:
                    self.need_fix_L = True
                    break

            for pin in self.pinsR:
                posx = int(pin['posx'])
                if (posx % 100) != 0:
                    self.need_fix_R = True
                    break

        if self.pinsU_count > 0 and self.pinsD_count > 0:
            for pin in self.pinsU:
                posy = int(pin['posy'])
                if (posy % 100) != 0:
                    self.need_fix_U = True
                    break

            for pin in self.pinsD:
                posy = int(pin['posy'])
                if (posy % 100) != 0:
                    self.need_fix_D = True
                    break
        if args.verbose:
            print('\t\tWill fix component')
        self.prerequisites_ok = True

    def print_header(self):
        if not self.header_printed:
            print('\tComponent: %s' % component.name)
            self.header_printed = True

    def resize_pin(self, pin, new_len, pos, new_pos):
        self.print_header()
        print('\t\t[resize] pin: %s (%s), length: %s -> %i, %s: %s -> %i' %
            (pin['name'], pin['num'], pin['length'], new_len, pos, pin[pos], new_pos))

        pin['length'] = str(new_len)
        pin[pos] = str(new_pos)

    def resize_all_pins(self):

        # case (1)
        if self.pinsL_count > 0 and self.pinsR_count == 0:
            for pin in self.pinsL:
                posx = int(pin['posx'])
                length = int(pin['length'])

                if (posx % 100) != 0:
                    if length <= 100:
                        length += 50
                        posx += 50
                    elif length >= 150:
                        length -= 50
                        posx -= 50

                    self.resize_pin(pin, length, 'posx', posx)

        # case (2)
        if self.pinsR_count > 0 and self.pinsL_count == 0:
            for pin in self.pinsR:
                posx = int(pin['posx'])
                length = int(pin['length'])

                if (posx % 100) != 0:
                    if length <= 100:
                        length += 50
                        posx -= 50
                    elif length >= 150:
                        length -= 50
                        posx += 50

                    self.resize_pin(pin, length, 'posx', posx)

        # case (3)
        if self.pinsU_count > 0 and self.pinsD_count == 0:
            for pin in self.pinsU:
                posy = int(pin['posy'])
                length = int(pin['length'])

                if (posy % 100) != 0:
                    if length <= 100:
                        length += 50
                        posy -= 50
                    elif length >= 150:
                        length -= 50
                        posy += 50

                    self.resize_pin(pin, length, 'posy', posy)

        # case (4)
        if self.pinsD_count > 0 and self.pinsU_count == 0:
            for pin in self.pinsD:
                posy = int(pin['posy'])
                length = int(pin['length'])

                if (posy % 100) != 0:
                    if length <= 100:
                        length += 50
                        posy += 50
                    elif length >= 150:
                        length -= 50
                        posy -= 50

                    self.resize_pin(pin, length, 'posy', posy)

        # case (5)
        if self.need_fix_L and self.need_fix_R:
            for pin in (self.pinsL + self.pinsR):
                posx = int(pin['posx'])
                length = int(pin['length'])

                if length <= 100:
                    length += 50
                    posx += 50 if posx > 0 else -50
                elif length >= 150:
                    length -= 50
                    posx += -50 if posx > 0 else 50

                self.resize_pin(pin, length, 'posx', posx)

        # case (6)
        if self.need_fix_U and self.need_fix_D:
            for pin in (self.pinsU + self.pinsD):
                posy = int(pin['posy'])
                length = int(pin['length'])

                if length <= 100:
                    length += 50
                    posy += 50 if posy > 0 else -50
                elif length >= 150:
                    length -= 50
                    posy += -50 if posy > 0 else 50

                self.resize_pin(pin, length, 'posy', posy)

        return self.header_printed
  
    #shifts a pin after ensuring that doing so doesn't cause an overlap
    def shift_pin(self,pin, oldx, oldy, newx, newy):
      self.print_header()
      if((newx, newy) in self.pin_positions):
        if args.verbose:
          print("\t\tshifting pin causes overlap: %s (%s) from %i,%i  to %i,%i'" % (pin['name'], pin['num'], oldx, oldy, newx, newy))
        return False
      if args.verbose:
        print('\t\t[movex] pin from %i,%i to %i,%i: %s (%s)' %
          (oldx, oldy, newx, newy, pin['name'], pin['num']))
      pin['posx'] = str(newx)
      pin['posy'] = str(newy)
      self.pin_positions.append((int(pin['posx']), int(pin['posy'])))


    def shift_all_pins(self):

      self.pin_positions = []
      
      #initialize list of pin positions with current list
      #this is later used to prevent pin overlaps as a result of shifts
      for pin in (self.pinsU + self.pinsD + self.pinsL + self.pinsR):
        self.pin_positions.append((int(pin['posx']), int(pin['posy'])))

      # case (7)
      for pin in (self.pinsU + self.pinsD):
        posx = int(pin['posx'])
        posy = int(pin['posy'])
        newposx = posx - (posx%100) 
        if (newposx != posx):
          self.shift_pin(pin, posx, posy, newposx, posy)
          
      #case (8)
      for pin in (self.pinsL + self.pinsR):
        posx = int(pin['posx'])
        posy = int(pin['posy'])
        newposy = posy - (posy%100) 
        if (newposy != posy):
          self.shift_pin(pin, posx, posy, posx, newposy)
      return self.header_printed



parser = argparse.ArgumentParser()
parser.add_argument('libfiles', nargs='+')
parser.add_argument('-y', '--apply', help='Apply the suggested modifications in the report', action='store_true')
parser.add_argument('-v', '--verbose', help='Print output for all pins - violating or not', action='store_true')
args = parser.parse_args()

for libfile in args.libfiles:
    lib = SchLib(libfile)
    print('library: %s' % libfile)
    for component in lib.components:
        componentCheck = CheckComponent(component)

        component_printed = componentCheck.resize_all_pins()
        component_printed = componentCheck.shift_all_pins() or component_printed
        
        if not component_printed:
            if args.verbose:
                print('\tcomponent: %s......OK' % component.name)

    if args.apply:
        lib.save()