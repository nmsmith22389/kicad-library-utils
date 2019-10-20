#!/usr/bin/env python3

import math
import os
import sys

sys.path.append(os.path.join(sys.path[0], '..'))

from KiCadSymbolGenerator import *

def roundToGrid(x, g):
    if x > 0:
        return math.ceil(x / g) * g
    else:
        return math.floor(x / g) * g

generator = SymbolGenerator('C_Network')

def generateCapacitorNetwork(count):
    name = 'C_Network{:02d}'.format(count)
    refdes = 'RN'
    footprint = ''
    footprint_filter = 'C?Array?SMD*'
    description = '{0} capacitor network, star topology, bussed capacitor, small symbol'.format(count)
    keywords = 'C network star-topology'
    datasheet = ''

    grid_size = 100
    junction_diameter = 20
    pin_length = 100
    capacitor_length = 20
    capacitor_width = 60
    capacitor_top_lead_length = 30
    body_left_offset = 50
    left = -math.floor(count / 2) * grid_size
    body_x = left - body_left_offset
    body_y = -125
    body_height = 250
    body_width = (count - 1) * grid_size + 2 * body_left_offset
    top = -200
    bottom = 200

    symbol = generator.addSymbol(name,
        dcm_options = {
            'datasheet': datasheet,
            'description': description,
            'keywords': keywords
        },
        footprint_filter = footprint_filter,
        offset = 0,
        pin_name_visibility = Symbol.PinMarkerVisibility.INVISIBLE
    )
    symbol.setReference(refdes,
        at = Point(body_x - 50, 0),
        orientation = SymbolField.FieldOrientation.VERTICAL
    )
    symbol.setValue(
        at = Point(body_x + body_width + 50, 0),
        orientation = SymbolField.FieldOrientation.VERTICAL
    )
    symbol.setDefaultFootprint(
        at = Point(body_x + body_width + 50 + 75, 0),
        orientation = SymbolField.FieldOrientation.VERTICAL,
        value = footprint
    )

    # Symbol body
    symbol.drawing.append(DrawingRectangle(
        end = Point(body_x + body_width, body_y + body_height),
        fill = ElementFill.FILL_BACKGROUND,
        start = Point(body_x, body_y),
        unit_idx = 0
    ))

    pin_left = left

    # Common pin
    symbol.drawing.append(DrawingPin(
        at = Point(pin_left, -top),
        name = 'common',
        number = 1,
        orientation = DrawingPin.PinOrientation.DOWN,
        pin_length = pin_length
    ))

    # First top capacitor lead
    symbol.drawing.append(DrawingPolyline(
        line_width = 0,
        points = [
            Point(pin_left, -(top + pin_length)),
            Point(pin_left, capacitor_length / 2)
        ],
        unit_idx = 0
    ))

    for s in range(1, count + 1):
        # Capacitor pins
        symbol.drawing.append(DrawingPin(
            at = Point(pin_left, -bottom),
            name = 'C{0}'.format(s),
            number = s + 1,
            orientation = DrawingPin.PinOrientation.UP,
            pin_length = pin_length
        ))
        # Capacitor bodies
        symbol.drawing.append(DrawingPolyline(
            line_width = 0,
            points = [
                Point(pin_left + capacitor_width / 2, -capacitor_length / 2),
                Point(pin_left - capacitor_width / 2, -capacitor_length / 2),
            ],
            unit_idx = 0
        ))
        symbol.drawing.append(DrawingPolyline(
            line_width = 0,
            points = [
                Point(pin_left + capacitor_width / 2, capacitor_length / 2),
                Point(pin_left - capacitor_width / 2, capacitor_length / 2),
            ],
            unit_idx = 0
        ))

        if s < count:
            # Top capacitor leads
            symbol.drawing.append(DrawingPolyline(
                line_width = 0,
                points = [
                    Point(pin_left, capacitor_length / 2),
                    Point(pin_left, capacitor_length / 2 + capacitor_top_lead_length),
                    Point(pin_left + grid_size, capacitor_length / 2 + capacitor_top_lead_length),
                    Point(pin_left + grid_size, capacitor_length / 2)
                ],
                unit_idx = 0
            ))
            # Junctions
            symbol.drawing.append(DrawingCircle(
                at = Point(pin_left, capacitor_length / 2 + capacitor_top_lead_length),
                fill = ElementFill.FILL_FOREGROUND,
                line_width = 0,
                radius = junction_diameter / 2,
                unit_idx = 0
            ))
        # Bottom Capacitor leads
        symbol.drawing.append(DrawingPolyline(
            line_width = 0,
            points = [
                Point(pin_left, -capacitor_length / 2),
                Point(pin_left, top + pin_length),
            ],
            unit_idx = 0
        ))
        pin_left = pin_left + grid_size

def generateCapacitorPack(count):
    name = 'C_Pack{:02d}'.format(count)
    refdes = 'CN'
    footprint = ''
    footprint_filter = ['DIP*', 'SOIC*']
    description = '{0} capacitor network, parallel topology, SMD package'.format(count)
    keywords = 'C network parallel topology isolated'
    datasheet = '~'

    grid_size = 100
    pin_length = 100
    capacitor_length = 20
    capacitor_width = 50
    body_left_offset = 50
    body_top_offset = 20
    left = -roundToGrid(((count - 1) * grid_size) / 2, 100)
    top = -200
    bottom = 200
    body_x = left - body_left_offset
    body_height = bottom - top - 2 * pin_length + 2 * body_top_offset
    body_y = -body_height / 2
    body_width = ((count - 1) * grid_size) + 2 * body_left_offset

    symbol = generator.addSymbol(name,
        dcm_options = {
            'datasheet': datasheet,
            'description': description,
            'keywords': keywords
        },
        footprint_filter = footprint_filter,
        offset = 0,
        pin_name_visibility = Symbol.PinMarkerVisibility.INVISIBLE
    )
    symbol.setReference(refdes,
        at = Point(body_x - 50, 0),
        orientation = SymbolField.FieldOrientation.VERTICAL
    )
    symbol.setValue(
        at = Point(body_x + body_width + 50, 0),
        orientation = SymbolField.FieldOrientation.VERTICAL
    )
    symbol.setDefaultFootprint(
        at = Point(body_x + body_width + 50 + 75, 0),
        orientation = SymbolField.FieldOrientation.VERTICAL,
        value = footprint
    )

    # Symbol body
    symbol.drawing.append(DrawingRectangle(
        end = Point(body_x + body_width, body_y + body_height),
        fill = ElementFill.FILL_BACKGROUND,
        start = Point(body_x, body_y),
        unit_idx = 0
    ))

    pin_left = left

    for s in range(1, count + 1):
        # Capacitor bottom pins
        symbol.drawing.append(DrawingPin(
            at = Point(pin_left, -bottom),
            name = 'R{0}.1'.format(s),
            number = s,
            orientation = DrawingPin.PinOrientation.UP,
            pin_length = pin_length
        ))
        # Capacitor top pins
        symbol.drawing.append(DrawingPin(
            at = Point(pin_left, -top),
            name = 'R{0}.2'.format(s),
            number = 2 * count - s + 1,
            orientation = DrawingPin.PinOrientation.DOWN,
            pin_length = pin_length
        ))
        # Capacitor bodies
        symbol.drawing.append(DrawingPolyline(
	    line_width = 0,
	    points = [
                Point(pin_left - capacitor_width / 2, -(-capacitor_length / 2)),
		Point(pin_left + capacitor_width / 2, -(-capacitor_length / 2)),
	    ],
            unit_idx = 0
        ))
        symbol.drawing.append(DrawingPolyline(
	    line_width = 0,
	    points = [
                Point(pin_left - capacitor_width / 2, (-capacitor_length / 2)),
		Point(pin_left + capacitor_width / 2, (-capacitor_length / 2)),
	    ],
            unit_idx = 0
        ))
        # Capacitor bottom leads
        symbol.drawing.append(DrawingPolyline(
            line_width = 0,
            points = [
                Point(pin_left, -(bottom - pin_length)),
                Point(pin_left, -(capacitor_length / 2))
            ],
            unit_idx = 0
        ))
        # Capacitor top leads
        symbol.drawing.append(DrawingPolyline(
            line_width = 0,
            points = [
                Point(pin_left, -(-capacitor_length / 2)),
                Point(pin_left, -(top + pin_length))
            ],
            unit_idx = 0
        ))

        pin_left = pin_left + grid_size


if __name__ == '__main__':
    for i in range(3, 14):
        generateCapacitorNetwork(i)

    for i in range(2, 8):
        generateCapacitorPack(i)

    generator.writeFiles()
