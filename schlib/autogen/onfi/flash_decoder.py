#!/usr/bin/env python3

import sys, os, re, json

micron = r'(^MT)(29)([E,F])(.{,3}[G,T])([0,1][1,8,6])([A,C,E]|.)([A,B,D,E,F,G,J,K,L,M,Q,R,T,U,V,]|.)([A,B,C,E,F,G,H,J,K,L]|.)([A,B,C,D,E]|.)([A,B,C,D]|.)([W,H,J][P,C,1-9]|..)'
kioxia = r'(^T[H,C]58)([N,D,T]|.)([V,Y,A,B,D]|.)([M,G,T][0-9])([S,D,T]|.)([0-9])([A-H])'
#samsung
#winbond
#macronix

regex = [micron, kioxia]

def decode(var):
    for r in regex:
        matches = re.findall(r, var)
        for flash in matches:
            if flash[0] == 'MT':
                return micron(flash)
            if flash[0] in ['TH58', 'TC58']:
                return kioxia(flash)
    #        if flash[0] in ['K']:
    #            return samsung(flash)
            else:
                print ("unknown flash")
                exit()

def kioxia(id):
    # CELLS
    if id[4] == 'S':
        cells = 'SLC'
    elif id[4] == 'D':
        cells = 'MLC'
    elif id[4] == 'T':
        cells = 'TLC'
    else:
        cells = None

    # VOLTAGE
    if id[2] == 'V':
        vcc='3.3V';vccq=None
    elif id[2] == 'Y':
        vcc='1.8V';vccq=None
    elif id[2] == 'A':
        vcc='3.3V';vccq='1.8V'
    elif id[2] == 'B':
        vcc='3.3V';vccq='1.65-3.6V'
    elif id[2] == 'D':
        vcc='1.8V or 3.3V';vccq='1.8V or 3.3V'
    else:
        vcc=None;vccq=None

    return {
        'vendor':'Kioxia',
        'density':str(2**int(id[3][1]))+id[3][0],
        'width':None,
        'cells':cells,
        'classification':None,
        'voltage':{'Vcc':vcc,'Vccq':vccq},
        'interface':None,
        'footprint':None,
        'speed':None,
        'temperature':str(None),
        'page_size':None,
        'block_size':None,
        'alias':None
    }

def micron(id):
    # CELLS
    if id[5] == 'A':
        cells = 'SLC'
    elif id[5] == 'C':
        cells = 'MLC'
    elif id[5] == 'E':
        cells = 'TLC'
    else:
        cells = None
    
    # CLASSIFICATION
    if id[6] == 'A':
        die=1;ce=0;rb=0;ch=1
    elif id[6] == 'B':
        die=1;ce=1;rb=1;ch=1
    elif id[6] == 'D':
        die=2;ce=1;rb=1;ch=1
    elif id[6] == 'E':
        die=2;ce=2;rb=2;ch=2
    elif id[6] == 'F':
        die=2;ce=2;rb=2;ch=1
    elif id[6] == 'G':
        die=3;ce=3;rb=3;ch=3
    elif id[6] == 'J':
        die=4;ce=2;rb=2;ch=1
    elif id[6] == 'K':
        die=4;ce=2;rb=2;ch=2
    elif id[6] == 'L':
        die=4;ce=4;rb=4;ch=4
    elif id[6] == 'M':
        die=4;ce=4;rb=4;ch=2
    elif id[6] == 'Q':
        die=8;ce=4;rb=4;ch=4
    elif id[6] == 'R':
        die=8;ce=2;rb=2;ch=2
    elif id[6] == 'T':
        die=16;ce=8;rb=4;ch=2
    elif id[6] == 'U':
        die=8;ce=4;rb=4;ch=2
    elif id[6] == 'V':
        die=16;ce=8;rb=4;ch=4
    else:
        die=None;ce=None;rb=None;ch=None

    # VOLTAGE
    if id[7] == 'A':
        vcc='3.3V (2.7-3.6V)';vccq='3.3V (2.7-3.6V)'
    elif id[7] == 'B':
        vcc='1.8V (1.7-1.95V)';vccq=None
    elif id[7] == 'C':
        vcc='3.3V (2.7-3.6V)';vccq='1.8V (1.7-1.95V)'
    elif id[7] == 'E':
        vcc='3.3V (2.7-3.6V)';vccq='3.3V (2.7-3.6V) or 1.8V (1.7-1.95V)'
    elif id[7] == 'F':
        vcc=' (2.5-3.6V)';vccq='1.2V (1.14-1.26V)'
    elif id[7] == 'G':
        vcc='3.3V (2.6-3.6V)';vccq='1.8V (1.7-1.95V)'
    elif id[7] == 'H':
        vcc='3.3V (2.5-3.6V)';vccq='1.2V (1.14-1.26V) or 1.8V (1.7-1.95V)'
    elif id[7] == 'J':
        vcc='3.3V (2.5-3.6V)';vccq='1.8V (1.7-1.95V)'
    elif id[7] == 'K':
        vcc='3.3V (2.6-3.6V)';vccq='3.3V (2.6-3.6V)'
    elif id[7] == 'L':
        vcc='3.3V (2.6-3.6V)';vccq='3.3V (2.6-3.6V) or 1.8 (1.7-1.95V)'
    else:
        vcc=None;vccq=None

    # INTERFACE
    if id[9] == 'A':
        sync=False;synca=True
    elif id[9] == 'B':
        sync=True;synca=True
    elif id[9] == 'C':
        sync=True;synca=False
    else:
        sync=None;synca=None

    # FOOTPRINT
    if id[10] in ['WP', 'WC']:
        footprint="Package_SO:TSOP-I-48_18.4x12mm_P0.5mm"
    elif id[10] in ['H1', 'H2', 'H3']:
        footprint="Package_BGA.pretty:BGA-100_10x17_Layout12x18mm_P1.0mm"
    elif id[10] in ['H4', 'HC']:
        footprint="Package_BGA:BGA-63_9x11mm_Layout10x12_P0.8mm"
    elif id[10] in ['H6', 'H7', 'H8', 'J7']:
        footprint="Package_BGA:BGA-152_14x18mm_Layout13x17_P1.0mm"
    elif id[10] in ['J1', 'J2', 'J3', 'J4', 'J5', 'J6', 'J9']:
        footprint="Package_BGA:BGA-132_12x18mm_Layout11x17_P1.0mm"
    else:
        footprint=None

    return {
        'vendor':'Micron',
        'density':id[3],
        'width':'x'+id[4].strip('0'),
        'cells':cells,
        'classification':{'die':die,'ce':ce,'rb':rb,'ch':ch},
        'voltage':{'Vcc':vcc,'Vccq':vccq},
        'interface':{'sync':sync,'async':synca},
        'footprint':footprint,
        'speed':None,
        'temperature':str(None),
        'page_size':None,
        'block_size':None,
        'alias':None
    }


if __name__ == "__main__":
    var = sys.argv[1]
    print (decode(var))