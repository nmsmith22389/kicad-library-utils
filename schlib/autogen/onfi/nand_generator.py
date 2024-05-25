#!/usr/bin/env python3

import sys, os
import json, pyexcel
import flash_decoder as fd
from csv import DictReader

sys.path.append(os.path.join(sys.path[0], '..'))
from KiCadSymbolGenerator import *

generator = SymbolGenerator('Memory_Flash_NAND')


def generateSymbol(flashCSV):
    # resolve flash properties
    flashDECOD = fd.decode(flashCSV['name'])
    if flashDECOD is None:
        return()
#    print(flashDECOD)
    vendor = flashDECOD['vendor']
    ce = int(flashDECOD['classification']['ce'])
    density = flashDECOD['density']
    voltage = json.dumps(flashDECOD['voltage'])
    page_size = flashDECOD['page_size'] if flashDECOD['page_size'] else flashCSV['page_size']
    block_size = flashDECOD['block_size'] if flashDECOD['block_size'] else flashCSV['block_size']
    width = flashDECOD['width']
    cells = flashDECOD['cells']
    interface = flashDECOD['interface']
    channels = flashDECOD['classification']['ch']
    footprint = flashDECOD['footprint'] if flashDECOD['footprint'] else flashCSV['footprint']

    # translate interface
    mode =""
    if 'toggle' in interface:
        if interface['toggle'] is True:
            mode='DDR'
        elif interface['toggle'] is False:
            mode='SDR'
        else:
            print ("not supported interface: " + json.dumps(interface))
            return()
    elif 'sync' in interface:
        if interface['sync'] is True:
            mode='DDR'
        elif interface['async'] is True:
            mode='SDR'
        else:
            print ("not supported interface: " + json.dumps(interface))
            return()

    # abort with invalid data
    if (ce is None):
        print ("flash not properly detected")
        print ("CE:" + ce)
        return()

    # combine strings
    description = vendor + ' ' + cells + ' NAND ' + density + width + ', ' + mode
    keywords = page_size +' Page, ' if page_size  else ""
    keywords += block_size +' Block, ' if block_size else ""
    keywords += voltage if (voltage is not None) else ""

    # symbol properties
    current_symbol = generator.addSymbol(flashCSV['name'],
        dcm_options = {
            'datasheet': flashCSV['datasheet'],
            'description': description,
            'keywords': keywords + ', ' + flashDECOD['temperature']
        },num_units=channels)
    current_symbol.setReference('U', at={'x':0, 'y':100})
    current_symbol.setValue(at={'x':0, 'y':0})
    current_symbol.setDefaultFootprint (value=footprint, alignment_vertical=SymbolField.FieldAlignment.CENTER, visibility=SymbolField.FieldVisibility.INVISIBLE)

    # draw body
    for u in range (0,channels):
        rect = DrawingRectangle(start={'x':-700, 'y':1000}, end={'x':700, 'y':-1000}, fill=ElementFill.FILL_BACKGROUND,unit_idx=u)
        current_symbol.drawing.append(rect)

    # add pins
    current_symbol.pin_name_offset = 20
    package = pyexcel.get_sheet(file_name="pinmap.ods", name_columns_by_row=0, sheet_name=footprint.split(':')[1])
    for pin in package.to_records():
        if ((pin['interface'] == "") or (mode in pin['interface'].split(","))) and (pin['name']):
            if (int(pin['ce']) <= ce) and (pin['width']==width or not pin['width']):
                if pin['visibility'] == 'N':
                    vis=DrawingPin.PinVisibility('N')
                else:
                    vis=DrawingPin.PinVisibility('')

                current_symbol.drawing.append(DrawingPin(at=Point({'x':pin['x'], 'y':pin['y']},
                    grid=50), number=pin['pin'], name = pin['name'], orientation = DrawingPin.PinOrientation(pin['orientation']),
                    pin_length = 200, visibility=vis, el_type=DrawingPin.PinElectricalType(pin['type']),unit_idx=pin['channel']))

    # add alias
#    if 'alias' in flash:
#        for alias in flashCSV['alias']:
#            current_symbol.addAlias(alias['name'], dcm_options={
#                'description': description,
#                'keywords': keywords + ', ' + alias['temperature'],
#                'datasheet': alias['datasheet']}
#            )

    # add footprint filters
    for filter in flashCSV['footprint_filters']:
        current_symbol.addFootprintFilter(filter)


if __name__ == '__main__':
    with open('flashes.csv', 'r') as read_obj:
        csv_dict_reader = DictReader(read_obj, delimiter=";")
        for row in csv_dict_reader:
           generateSymbol(row)

    generator.writeFiles()