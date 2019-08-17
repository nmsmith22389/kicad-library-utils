#!/usr/bin/env python3

import sys, os
sys.path.append(os.path.join(sys.path[0],'..'))
from KiCadSymbolGenerator import *

from functools import reduce
from pathlib import Path
import itertools
import json
import operator
import yaml


# sum must be dividable by 200 for even drawing
drawing_height = 400
drawing_sep = 200

pin_length=140
arc_offset=60
arc_size=50
arcs=6 # should be even for center taps
drawing_line_width = 0
dot_offset=20
dot_radius=5
core_width=20
core_line_width=10

reference_designator = "TR"


def generate_transformer(generator, config):
    symbol_name = config["name"].format(**config)

    footprint = config.get("footprint", "").format(**config)
    fp_filter = config.get("footprint_filter", "").format(**config)
    if not fp_filter:
        if not footprint:
            raise Exception("Missing footprint and footprint filter")
        fp_filter = footprint.replace("_", "*") + "*"


    symbol = generator.addSymbol(
        symbol_name,
        footprint_filter=fp_filter,
        pin_name_visibility=Symbol.PinMarkerVisibility.INVISIBLE,
        dcm_options = dict(
            description=config["description"].format(**config),
            keywords=config["keywords"].format(**config),
            datasheet=config.get("datasheet", "").format(**config),
            ),
        )

    drawing = symbol.drawing

    prims = config["primary"]
    secs = config["secondary"]
    for i, coil in enumerate(prims):
        drawing.append(draw_primary(coil["pins"], coil["dot"],
            pos=i-(len(prims)-1)/2))
    for i, coil in enumerate(secs):
        drawing.append(draw_secondary(coil["pins"], coil["dot"],
            pos=i-(len(secs)-1)/2))

    max_coils = max(len(prims), len(secs))
    height = max_coils * drawing_height + (max_coils - 1) * drawing_sep
    if config.get("core"):
        drawing.append(draw_core(height))

    translate = drawing_sep % 200 / 2
    drawing.translate(dict(
        x=0, y=translate))

    fontsize = 50
    symbol.setReference(at=Point(dict(x=0, y=height/2+50+translate)),
            fontsize=fontsize,
            ref_des=reference_designator,
            alignment_vertical=SymbolField.FieldAlignment.CENTER
            )
    symbol.setValue(at=Point(dict(x=0, y=-height/2-50+translate)),
            fontsize=fontsize,
            alignment_vertical=SymbolField.FieldAlignment.CENTER
            )
    symbol.setDefaultFootprint(value=config["footprint"].format(**config))

    for alias in config.get("aliases", []):
        name = alias["name"]
        del alias["name"]
        symbol.addAlias(alias_name=name, dcm_options=alias)

def draw_primary(pins, dot, pos):
    return draw_coil(pins, dot, pos).mirrorVertical()

def draw_secondary(pins, dot, pos):
    if dot == "top":
        dot = "bottom"
    elif dot == "bottom":
        dot = "top"
    return draw_coil(pins, dot, pos).mirrorHorizontal()

def draw_coil(pins, dot, pos):
    top_pin = Point(dict(
        x=-pin_length-arc_offset,
        y=-drawing_height/2,
        ))
    bottom_pin = top_pin.mirrorVertical(apply_on_copy=True)

    drawing = Drawing()

    drawing.append(DrawingPin(
        at=top_pin,
        number=pins[0],
        name="~",
        pin_length=pin_length,
        orientation=DrawingPin.PinOrientation.RIGHT
        ))
    drawing.append(DrawingPin(
        at=bottom_pin,
        number=pins[1],
        name="~",
        pin_length=pin_length,
        orientation=DrawingPin.PinOrientation.RIGHT
        ))

    arc_top = Point(dict(
        x=-arc_offset,
        y=-arcs/2*arc_size
        ))

    pin_connect = top_pin.translate(dict(
        x=pin_length, y=0), apply_on_copy=True)
    line = DrawingPolyline(
            points=(pin_connect, arc_top),
            line_width=drawing_line_width,
            )
    drawing.append(line)
    drawing.append(line.mirrorVertical(apply_on_copy=True))

    arc_center = arc_top.translate(dict(
        x=0, y=arc_size/2), apply_on_copy=True)
    drawing.append(DrawingArray(
        original=DrawingArc(
            at=arc_center,
            radius=arc_size/2,
            angle_start=899,
            angle_end=-899,
            line_width=drawing_line_width
            ),
        distance=dict(x=0, y=arc_size),
        number_of_instances=arcs
        ))

    dot_pos = arc_top.translate(dict(
        x=-dot_offset,
        y=0,
        ), apply_on_copy=True)
    if dot == "top":
        drawing.append(DrawingCircle(
            at=dot_pos,
            radius=dot_radius,
            line_width=drawing_line_width
            ))
    elif dot == "bottom":
        dot_pos.mirrorVertical()
        drawing.append(DrawingCircle(
            at=dot_pos,
            radius=dot_radius,
            line_width=drawing_line_width
            ))

    drawing.translate(dict(
        x=0,
        y=pos*(drawing_height+drawing_sep)
        ))

    return drawing

def draw_core(height):
    drawing = Drawing()
    line = DrawingPolyline(
        points=(
            Point(dict(x=core_width/2, y=-height/2)),
            Point(dict(x=core_width/2, y=height/2))
        ),
        line_width=core_line_width
        )
    drawing.append(line)
    drawing.append(line.mirrorHorizontal(apply_on_copy=True))
    return drawing

def load_definitions(file_path):
    with open(file_path, 'r') as f:
        conf = yaml.safe_load(f)

    configs = []
    for series_name, series_config in conf.items():
        configs += expand_definition(series_name, series_config)

    return configs

def coil_to_sorting_key(coil_config):
    return json.dumps(coil_config)

def sorting_key(config):
    return (coil_to_sorting_key(config["primary"]),
            coil_to_sorting_key(config["secondary"]),
            config["footprint"].format(**config))

def group_aliases(configs):
    grouped = []
    configs.sort(key=sorting_key)
    for _, group in itertools.groupby(configs, key=sorting_key):
        master = next(group)
        master["aliases"] = [dict(
            name=conf["name"].format(**conf),
            description=conf["description"].format(**conf),
            keywords=conf["keywords"].format(**conf),
            datasheet=conf.get("datasheet", "").format(**conf)
            ) for conf in group]
        grouped.append(master)
    return grouped

def handle_variant_shorthand(name, v):
    if isinstance(v, dict):
        return v
    else:
        return {name: v}

def expand_definition(name, config):
    variants = config.get("variants")
    if variants is None:
        return [config]

    try:
        vs = {}
        for name, values in variants.items():
            vs[name] = [handle_variant_shorthand(name, v) for v in values]
        all_variants = list(itertools.product(*vs.values()))
        expanded_variants = [{k: v for d in var for k, v in d.items()}
                             for var in all_variants]
    except AttributeError:
        # probaby a list, not a dict. Assume it to be a 1D iteration
        # in this case short hand notation is not possible
        expanded_variants = variants

    del config["variants"]

    # call recursively to allow for definition of variants inside other
    # variants
    expanded = reduce(operator.concat, [expand_definition(name,
        dict(config, **vs)) for vs in expanded_variants])

    for exp in expanded:
        exp["primary"] = expand_coil_definition(exp, exp["primary"],
                pin_start=1)
        last_used_pin = max(max(*prim["pins"]) for prim in exp["primary"])
        exp["secondary"] = expand_coil_definition(exp, exp["secondary"],
                pin_start=last_used_pin)

    return expanded

def expand_coil_definition(config, coil_config, pin_start=1):
    dot = config.get("dots", "none")

    if isinstance(coil_config, int):
        # just an amount of coils
        return [dict(pins=[pin_start+i, pin_start+i+1], dot=dot) for i in range(0, coil_config*2, 2)]
    if isinstance(coil_config[0], list):
        # list of pin tuples
        return [dict(pins=pins, dot=dot) for pins in coil_config]
    if isinstance(coil_config[0], int):
        # single pin tuple
        return [dict(pins=coil_config, dot=dot)]

    # must be a list of dicts
    out = []
    for i, coil_conf in enumerate(coil_config):
        coil_conf["dot"] = coil_conf.get("dot", dot)
        coil_conf["pins"] = coil_conf.get("pins", [pin_start+i*2, pin_start+i*2+1])
        out.append(coil_conf)
    return out

def build_symbols(file_path):
    defs = []
    for path in Path("definitions").glob("*.yaml"):
        defs += load_definitions(path)
    defs = group_aliases(defs)
    generator = SymbolGenerator("Transformer")
    for definition in defs:
        generate_transformer(generator, definition)
    generator.writeFiles()


if __name__ == "__main__":
    build_symbols("definitions/block.yaml")
