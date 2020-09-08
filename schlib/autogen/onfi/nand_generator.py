#!/usr/bin/env python3

import sys, os
import csv, json

sys.path.append(os.path.join(sys.path[0], '..'))
from KiCadSymbolGenerator import *

generator = SymbolGenerator('Memory_Flash_NAND')

def generateSymbol(name,flash):
    # resolve pin mapping
    if ("BGA-63" in flash['footprint_default']):
        mapping = 'BGA-63'+'_'+flash['ce']+'CE'
    elif ("TSOP-48" in flash['footprint_default']):
        mapping = 'TSOP-48'+'_'+flash['ce']+'CE'
    elif ("BGA-132" in flash['footprint_default']):
        mapping = 'BGA-132'+'_'+flash['ce']+'CE'
    elif ("BGA-152" in flash['footprint_default']):
        mapping = 'BGA-152'+'_'+flash['ce']+'CE'
    else:
        print ("no pin mapping found!")
        return()
    print ('pin mapping used: ' + mapping)

    # symbol properties
    current_symbol = generator.addSymbol(name,
        dcm_options = {
            'datasheet': flash['datasheet'],
            'description': flash['density']+'x8 '+flash['cells']+' NAND '+flash['voltage'],
            'keywords': flash['page_size']+' Page, '+flash['block_size']+' Block'
        })
    current_symbol.setReference('U', at={'x':0, 'y':100})
    current_symbol.setValue(at={'x':0, 'y':0})
    current_symbol.setDefaultFootprint (value=flash['footprint_default'], alignment_vertical=SymbolField.FieldAlignment.CENTER, visibility=SymbolField.FieldVisibility.INVISIBLE)

    # draw body
    rect = DrawingRectangle(start={'x':-700, 'y':1000}, end={'x':700, 'y':-1000}, fill=ElementFill.FILL_BACKGROUND)
    current_symbol.drawing.append(rect)

    # add pins
    with open(mapping + '.part','r') as pinmapping:
        pins = csv.DictReader(pinmapping, delimiter=' ')
        for p in pins:
            if p['visibility'] is None:
                vis=DrawingPin.PinVisibility('')
            else:
                vis=DrawingPin.PinVisibility('N')

            current_symbol.drawing.append(DrawingPin(at=Point({'x':p['x'], 'y':p['y']},
                grid=50), number=p['number'], name = p['name'], orientation = DrawingPin.PinOrientation(p['orientation']),
                pin_length = p['length'], visibility=vis, el_type=DrawingPin.PinElectricalType(p['type'])))

    # add alias
    for alias in flash['alias']:
        current_symbol.addAlias(alias['name'], dcm_options={
            'description': flash['density']+'x8 '+flash['cells']+' NAND '+flash['voltage'],
            'keywords': alias['keywords'],
            'datasheet': flash['datasheet']}
        )

    # add footprint filters
    for filter in flash['footprint_filters']:
        current_symbol.addFootprintFilter(filter)

if __name__ == '__main__':
    with open('flashes.json','r') as flashes:
        fdb = json.loads(flashes.read())
        for k, v in fdb.items():
            print("Flash: "+k)
            generateSymbol(k,v)

    generator.writeFiles()