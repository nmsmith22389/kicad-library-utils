#!/usr/bin/env python3

import sys, os
import csv, json
import urllib.request, ssl

ssl._create_default_https_context = ssl._create_unverified_context

sys.path.append(os.path.join(sys.path[0], '..'))
from KiCadSymbolGenerator import *

generator = SymbolGenerator('Memory_Flash_NAND')

def getResponse(url):
    operUrl = urllib.request.urlopen(url)
    if(operUrl.getcode()==200):
        data = operUrl.read()
        jsonData = json.loads(data)
    else:
        print("Error receiving data", operUrl.getcode())
    return jsonData

def generateSymbol(flash):
    # get fallback values from FlashMaster https://github.com/iTXTech/FlashMaster
    json = getResponse('https://dev.peratx.net:444/fd/decode?lang=eng&pn='+flash['part'])
    ce = flash['ce'] if ('ce' in flash and flash['ce'] ) else json['data']['classification']['ce']
    density = flash['density'] if (flash['density']) else json['data']['density']
    voltage = flash['voltage'] if (flash['voltage']) else json['data']['voltage']
    page_size = flash['page_size'] if (flash['page_size']) else json['data']['extraInfo']['Page size'] if ("Page size" in json['data']['extraInfo']) else "Unknown"
    block_size = flash['block_size'] if (flash['block_size']) else json['data']['extraInfo']['Block size'] if ("Block size" in json['data']['extraInfo']) else "Unknown"
    vendor = flash['vendor'] if (flash['vendor']) else json['data']['vendor']
    width = flash['width'] if (flash['width']) else json['data']['deviceWidth']
    cells = flash['cells'] if (flash['cells']) else json['data']['cellLevel']

    if (ce == "Unknown" or ce == 0):
        print ("Unknown CE")
        return()

    description = vendor + ' ' + cells + ' NAND ' + density + width 
    keywords = page_size +' Page, ' if (page_size != 'Unknown') else ""
    keywords += block_size +' Block, ' if (block_size != 'Unknown') else ""
    keywords += voltage +', ' if (voltage != 'Unknown') else ""

    # resolve pin mapping and set unit count
    if ("BGA-63" in flash['footprint_default']):
        mapping = 'BGA-63'+'_'+str(ce)+'CE'
        units=json['data']['classification']['ch'] if ("ch" in json['data']['classification'] and json['data']['classification']['ch'] != "Unknown") else 1
    elif ("TSOP-I-48" in flash['footprint_default']):
        mapping = 'TSOP-48'+'_'+str(ce)+'CE'
        units=json['data']['classification']['ch'] if ("ch" in json['data']['classification'] and json['data']['classification']['ch'] != "Unknown") else 1
    elif ("BGA-100" in flash['footprint_default']):
        mapping = 'BGA-100'+'_'+str(ce)+'CE'
        units=json['data']['classification']['ch'] if ("ch" in json['data']['classification'] and json['data']['classification']['ch'] != "Unknown") else 2
    elif ("BGA-132" in flash['footprint_default']):
        mapping = 'BGA-132'+'_'+str(ce)+'CE'
        units=json['data']['classification']['ch'] if ("ch" in json['data']['classification'] and json['data']['classification']['ch'] != "Unknown") else 2
    elif ("BGA-152" in flash['footprint_default']):
        mapping = 'BGA-152'+'_'+str(ce)+'CE'
        units=json['data']['classification']['ch'] if ("ch" in json['data']['classification'] and json['data']['classification']['ch'] != "Unknown") else 2
    else:
        print ("no pin mapping found!")
        return()
    print ('pin mapping used: ' + mapping)

    # symbol properties
    current_symbol = generator.addSymbol(flash['part'],
        dcm_options = {
            'datasheet': flash['datasheet'],
            'description': description,
            'keywords': keywords + flash['temperature']
        },num_units=units)
    current_symbol.setReference('U', at={'x':0, 'y':0})
    current_symbol.setValue(at={'x':0, 'y':-100})
    current_symbol.setDefaultFootprint (value=flash['footprint_default'], alignment_vertical=SymbolField.FieldAlignment.CENTER, visibility=SymbolField.FieldVisibility.INVISIBLE)

    # draw body
    for u in range (0,units):
        rect = DrawingRectangle(start={'x':-700, 'y':1000}, end={'x':700, 'y':-1000}, fill=ElementFill.FILL_BACKGROUND,unit_idx=u)
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
                pin_length = p['length'], visibility=vis, el_type=DrawingPin.PinElectricalType(p['type']),unit_idx=p['unit']))

    # add alias
    if 'alias' in flash:
        for alias in flash['alias']:
            current_symbol.addAlias(alias['name'], dcm_options={
                'description': description,
                'keywords': keywords + alias['temperature'],
                'datasheet': alias['datasheet']}
            )

    # add footprint filters
#    print(flash['footprint_filters'])
#    for filter in flash['footprint_filters']:
#        current_symbol.addFootprintFilter(filter)

if __name__ == '__main__':
    with open(str(sys.argv[1]),'r') as flashes:
        fdb = json.loads(flashes.read())
        for i in fdb:
            print("Flash: "+i['part'])
            generateSymbol(i)

    generator.writeFiles()