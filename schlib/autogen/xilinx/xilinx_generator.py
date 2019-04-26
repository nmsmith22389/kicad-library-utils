#!/usr/bin/env python3

import argparse
import os
import sys
import logging
import re
import os.path
import fnmatch
import math
from enum import IntEnum
import glob

sys.path.append(os.path.join(sys.path[0],'..'))
from KiCadSymbolGenerator import *

FOOTPRINT_PATH = "/usr/share/kicad/modules"

class Device:
    _FAMILY_PART_REGEXPS = {
        "Spartan7":             re.compile("(x[cq]7s(\d+))([a-zA-Z]+\d+)pkg"),
        "Artix7":               re.compile("(x[cq]7a(\d+)t)([a-zA-Z]+\d+)pkg"),
        "Kintex7":              re.compile("(x[cq]7k(\d+)t)([a-zA-Z]+\d+)pkg"),
        "Virtex7":              re.compile("(x[cq]7v[a-zA-Z]*(\d+)t)([a-zA-Z]+\d+)pkg"),
        "Zynq7000":             re.compile("(x[cq]7z(\d+)s?)([a-zA-Z]+\d+)pkg"),
        "ZynqUltrascaleP":      re.compile("(x[cq]zu(\d+)[ce][gv])([a-zA-Z]+\d+)pkg"),
        "ZynqUltrascalePRFSoC": re.compile("(x[cq]zu(\d+)dr)([a-zA-Z]+\d+)pkg"),
        "KintexUltrascaleP":    re.compile("(x[cq]ku(\d+)p)([a-zA-Z]+\d+)pkg"),
        "VirtexUltrascaleP":    re.compile("(x[cq]vu(\d+)p)([a-zA-Z]+\d+)pkg"),
        "KintexUltrascale":     re.compile("(x[cq]ku(\d+))([a-zA-Z]+\d+)pkg"),
        "VirtexUltrascale":     re.compile("(x[cq]vu(\d+))([a-zA-Z]+\d+)pkg")
    }
    _FAMILY_NAMES = {
        "Spartan7":             "Spartan-7",
        "Artix7":               "Artix-7",
        "Kintex7":              "Kintex-7",
        "Virtex7":              "Virtex-7",
        "Zynq7000":             "Zynq-7000",
        "ZynqUltrascaleP":      "Zynq Ultrascale+",
        "ZynqUltrascalePRFSoC": "Zynq Ultrascale+ RFSoC",
        "KintexUltrascaleP":    "Kintex Ultrascale+",
        "VirtexUltrascaleP":    "Virtex Ultrascale+",
        "KintexUltrascale":     "Kintex Ultrascale",
        "VirtexUltrascale":     "Virtex Ultrascale"
    }
    _FAMILY_DATASHEETS = {
        "Spartan7": "https://www.xilinx.com/support/documentation/data_sheets/ds180_7Series_Overview.pdf",
        "Artix7": "https://www.xilinx.com/support/documentation/data_sheets/ds180_7Series_Overview.pdf",
        "Kintex7": "https://www.xilinx.com/support/documentation/data_sheets/ds180_7Series_Overview.pdf",
        "Virtex7": "https://www.xilinx.com/support/documentation/data_sheets/ds180_7Series_Overview.pdf",
        "Zynq7000": "https://www.xilinx.com/support/documentation/data_sheets/ds190-Zynq-7000-Overview.pdf",
        "ZynqUltrascaleP": "https://www.xilinx.com/support/documentation/data_sheets/ds890-ultrascale-overview.pdf",
        "ZynqUltrascalePRFSoC": "https://www.xilinx.com/support/documentation/data_sheets/ds890-ultrascale-overview.pdf",
        "KintexUltrascaleP": "https://www.xilinx.com/support/documentation/data_sheets/ds890-ultrascale-overview.pdf",
        "VirtexUltrascaleP": "https://www.xilinx.com/support/documentation/data_sheets/ds890-ultrascale-overview.pdf",
        "KintexUltrascale": "https://www.xilinx.com/support/documentation/data_sheets/ds890-ultrascale-overview.pdf",
        "VirtexUltrascale": "https://www.xilinx.com/support/documentation/data_sheets/ds890-ultrascale-overview.pdf"
    }
    _PACKAGE_REGEXP = re.compile("([a-zA-Z]+)(\d+)")

    _PACKAGE_FILTER_MAP = {
        re.compile("ftg?b?196"):    "BGA*196*15.0x15.0mm*Layout14x14*P1.0mm*",
        re.compile("fgg?a?484"):    "BGA*484*23.0x23.0mm*Layout22x22*P1.0mm*",
        re.compile("fgg?a?676"):    "BGA*676*27.0x27.0mm*Layout26x26*P1.0mm*",
        re.compile("cpg?a?196"):    "BGA*196*8.0x8.0mm*Layout14x14*P0.5mm*",
        re.compile("csg?a?225"):    "BGA*225*13.0x13.0mm*Layout15x15*P0.8mm*",
        re.compile("csg?a?32[45]"): "BGA*324*15.0x15.0mm*Layout18x18*P0.8mm*",
    }

    class Pin:
        # FPGA pin types. Pin with same pin type grouped together.
        class PinType(IntEnum):
            UNKNOWN = 0
            GENERAL = 1         # IO_* - General I/O pins
            CONFIG = 2          # INIT, PROGRAM, DONE - Configuration pins (reset, init, etc.)
            BOOT = 3            # M[2:0] - Boot type
            JTAG = 4            # JTAG
            ADC_REF = 5         # VREFP/VREFN - XADC reference
            ADC = 6             # V_N/V_P - ADC input
            ADC_DIODE = 7       # DXP/DXN - On-die thermal diode
            CORE_POWER = 8      # VCCINT - Core power
            BRAM_POWER = 9      # VCCBRAM - Internal RAM power
            AUX_POWER = 10      # VCCAUX - Aux power
            ADC_POWER = 11      # VCCADC - ADC power
            BATT_POWER = 12     # VCCBATT - Battery backup power
            BANK_POWER = 13     # VCCO_* - I/O power
            GND = 14            # GND
            ADC_GND = 15        # ADC GND
            NC = 16             # No connect

        # Pin type filters
        _TYPE_REGEXPS = {
            re.compile("^((PROGRAM)|(INIT)|(DONE))|(CFGBVS)|(CCLK)")
                                                    : PinType.CONFIG,
            re.compile("^M(\d+)")                   : PinType.BOOT,
            re.compile("^T((DI)|(DO)|(MS)|(CK))")   : PinType.JTAG,
            re.compile("^VREF([PN])")               : PinType.ADC_REF,
            re.compile("^V([PN])")                  : PinType.ADC,
            re.compile("^DX([PN])")                 : PinType.ADC_DIODE,
            re.compile("^VCCO_(\d+)")               : PinType.BANK_POWER,
            re.compile("^VCCINT")                   : PinType.CORE_POWER,
            re.compile("^VCCBRAM")                  : PinType.BRAM_POWER,
            re.compile("^VCCAUX")                   : PinType.AUX_POWER,
            re.compile("^VCCADC")                   : PinType.ADC_POWER,
            re.compile("^VCCBATT")                  : PinType.BATT_POWER,
            re.compile("^GNDADC")                   : PinType.ADC_GND,
            re.compile("^GND")                      : PinType.GND,
            re.compile("^IO_(L?)(\d+)([PN]?)")      : PinType.GENERAL,
            re.compile("^NC")                       : PinType.NC
        }

        # Default KiCAD electrical type for pin types
        _TYPE_DEFAULT_ELTYPE = {
            PinType.GENERAL:    DrawingPin.PinElectricalType.EL_TYPE_BIDIR,
            PinType.CONFIG:     DrawingPin.PinElectricalType.EL_TYPE_INPUT,
            PinType.BOOT:       DrawingPin.PinElectricalType.EL_TYPE_INPUT,
            PinType.JTAG:       DrawingPin.PinElectricalType.EL_TYPE_INPUT,
            PinType.ADC_REF:    DrawingPin.PinElectricalType.EL_TYPE_PASSIVE,
            PinType.ADC:        DrawingPin.PinElectricalType.EL_TYPE_INPUT,
            PinType.ADC_DIODE:  DrawingPin.PinElectricalType.EL_TYPE_PASSIVE,
            PinType.CORE_POWER: DrawingPin.PinElectricalType.EL_TYPE_POWER_INPUT,
            PinType.BRAM_POWER: DrawingPin.PinElectricalType.EL_TYPE_POWER_INPUT,
            PinType.AUX_POWER:  DrawingPin.PinElectricalType.EL_TYPE_POWER_INPUT,
            PinType.ADC_POWER:  DrawingPin.PinElectricalType.EL_TYPE_POWER_INPUT,
            PinType.BATT_POWER: DrawingPin.PinElectricalType.EL_TYPE_POWER_INPUT,
            PinType.BANK_POWER: DrawingPin.PinElectricalType.EL_TYPE_POWER_INPUT,
            PinType.GND:        DrawingPin.PinElectricalType.EL_TYPE_POWER_INPUT,
            PinType.ADC_GND:    DrawingPin.PinElectricalType.EL_TYPE_POWER_INPUT,
            PinType.NC:         DrawingPin.PinElectricalType.EL_TYPE_NC
        }

        # Some dedicated pins has different electrical type...
        _SPECIAL_ELTYPE = {
            re.compile("^CCLK"):    DrawingPin.PinElectricalType.EL_TYPE_BIDIR,
            re.compile("^DONE"):    DrawingPin.PinElectricalType.EL_TYPE_BIDIR,
            re.compile("^INIT"):    DrawingPin.PinElectricalType.EL_TYPE_OPEN_COLECTOR,
            re.compile("^TDO"):     DrawingPin.PinElectricalType.EL_TYPE_OUTPUT,
        }

        def __init__(self, dic):
            self.type = self.PinType.UNKNOWN
            self.pin = dic["pin"]
            self.name = dic["name"]
            try:
                self.bank = int(dic["bank"])
            except: # All pins without bank goes to bank 0
                self.bank = 0

            self.bankType = dic["type"]

            self.number = -1
            self.pair = False
            self.pairNeg = False

            # Detect pin type
            for r,t in self._TYPE_REGEXPS.items():
                m = r.match(self.name)
                if m is None:
                    continue

                self.type = t
                break

            if self.type == self.PinType.UNKNOWN:
                logging.warning(f"Unknown pin type for pin {self.name}")

            if self.type == self.PinType.GENERAL:
                # General I/O pins has number and can be in pair
                if m.group(1) == "L":
                    self.pair = True
                    self.pairNeg = m.group(3) == "N"
                self.number = int(m.group(2))
            elif self.type == self.PinType.ADC or self.type == self.PinType.ADC_DIODE:
                self.pair = True
                self.pairNeg = m.group(1) == "N"
            elif self.type == self.PinType.ADC_REF:
                self.pair = True
                self.pairNeg = m.group(1) == "N"


        # Sort pins by bank->type->number->P/N->name
        def __lt__(self, other):
            if self.bank < other.bank:
                return True
            elif self.bank == other.bank:
                if self.type < other.type:
                    return True
                elif self.type == other.type:
                    if (self.number != -1) and (other.number != -1) and self.number < other.number:
                        return True
                    elif (self.number == -1) or (other.number == -1) or (self.number == other.number):
                        if self.pair and other.pair and self.pairNeg < other.pairNeg:
                            return True
                        elif not self.pair or not other.pair or self.pairNeg == other.pairNeg:
                            return self.name < other.name

        def __str__(self):
            return f"({self.name}, {self.pin}, {self.bank}, {self.bankType}, {self.number}, {self.type}, {self.pair}, {self.pairNeg})"

        def drawingPin(self, **kwargs):
            # Try to find electrical type
            eltype = self._TYPE_DEFAULT_ELTYPE[self.type] if self.type in self._TYPE_DEFAULT_ELTYPE else \
                DrawingPin.PinElectricalType.EL_TYPE_PASSIVE

            for r,t in self._SPECIAL_ELTYPE.items():
                if r.match(self.name):
                    eltype = t
                    break

            return DrawingPin(at=Point(0, 0), number=self.pin, name=self.name, el_type=eltype, **kwargs)

    def __init__(self, file):
        self.csvFile = file;
        self.banks = {}
        self.pinCount = 0
        self.footprint = ""

        self.parseFile()

    def readPins(self):
        f = open(self.csvFile, "r")

        # Default column mapping for 7 series
        paramMapping = {"pin": 0, "name": 1, "bank": 3, "type": 6}

        for line in f:
            params = line.strip().split(",")

            if "" in params:
                continue;
            elif params[0].lower() == "pin":
                # Found line describing columns, update column mapping
                for i in range (0, len(params)):
                    paramName = params[i].strip().lower()
                    if paramName == "pin":
                        paramMapping["pin"] = i
                    elif paramName == "pin name":
                        paramMapping["name"] = i
                    elif paramName == "bank":
                        paramMapping["bank"] = i
                    elif paramName == "i/o type":
                        paramMapping["type"] = i
                continue

            # Extract info from row
            dic = {}
            for k,v in paramMapping.items():
                dic[k] = params[v].strip()

            # Create pin
            pin = Device.Pin(dic)

            # Place pin into bank (or create it)
            if pin.bank not in self.banks:
                self.banks[pin.bank] = []
            self.banks[pin.bank].append(pin)

        self.pinCount = 0
        # Sort pins inside banks
        for k,_ in self.banks.items():
            self.banks[k].sort()
            self.pinCount += len(self.banks[k])

        for k, v in self.banks.items():
            logging.debug(f"Bank {k}")
            for pin in v:
                logging.debug(f"  {pin}")

        # Primitive error checking
        if self.pinCount != self.packagePins:
            logging.warning(f"{self.libraryName} - package pin count mismatch: found {self.pinCount} pins, should be {self.packagePins}")


    def parseFile(self):
        logging.info(f"File {self.csvFile}:")

        baseName = os.path.basename(self.csvFile)

        # Extract FPGA family/name/package from file name
        values = []
        self.family = ""
        for f, r in self._FAMILY_PART_REGEXPS.items():
            m = r.match(baseName)
            if m is not None:
                self.family = f
                values = m.groups()
                break;

        if self.family == "" or len(values) == 0:
            return

        self.name = values[0]
        self.packageName = values[2]
        self.capacity = int(values[1])
        if self.family in self._FAMILY_NAMES:
            self.familyName = self._FAMILY_NAMES[self.family]
        else:
            self.familyName = self.family
        self.libraryName = f"{self.name.upper()}-{self.packageName.upper()}"

        pm = self._PACKAGE_REGEXP.match(self.packageName)
        if pm is None:
            self.packagePins = 0
        else:
            self.packagePins = int(pm.group(2))

        # Try to find footprint
        self.footprintFilter = None
        self.footprint = None
        for r, f in self._PACKAGE_FILTER_MAP.items():
            if r.match(self.packageName):
                self.footprintFilter = f

                # A bit ugly here - find footprint in Package_BGA.pretty only
                fpFile = glob.glob(os.path.join(FOOTPRINT_PATH, "Package_BGA.pretty/", f))
                if len(fpFile) > 0:
                    self.footprint  = f"Package_BGA:{os.path.basename(fpFile[0])}"
                break

        if not self.footprint:
            logging.warning(f"{self.libraryName} - cannot find footprint file")
        if not self.footprintFilter:
            logging.warning(f"{self.libraryName} - unknown footprint")

        self.readPins()

        logging.info(f"  Name:\t\t{self.name}")
        logging.info(f"  Family:\t{self.familyName}")
        logging.info(f"  Package:\t{self.packageName}")
        logging.info(f"  Capacity:\t{self.capacity}")
        logging.info(f"  Banks: {len(self.banks)}")
        logging.info(f"  Pins: {self.pinCount}")
        logging.info(f"  Footprint: {self.footprint}")
        logging.info(f"  Footprint filter: {self.footprintFilter}")

    def drawSymbol(self):
        bankList = list(self.banks.items())

        # Basic info
        self.symbol.setReference('U')
        self.symbol.setValue(value=self.libraryName.upper())
        self.symbol.setDefaultFootprint(value=self.footprint)
        self.symbol.addFootprintFilter(self.footprintFilter)

        # I/O Bank = KiCAD Unit
        self.symbol.num_units = len(bankList)
        self.symbol.interchangable = Symbol.UnitsInterchangable.NOT_INTERCHANGEABLE

        # Calc max package pin name
        maxPackagePin = 0
        for bank, pins in bankList:
            for pin in pins:
                maxPackagePin = len(pin.pin) if len(pin.pin) > maxPackagePin else maxPackagePin
        pinLength = 200 if maxPackagePin > 2 else 100

        # Generate units
        for bankIdx in range(0, self.symbol.num_units):
            bank, pins = bankList[bankIdx]

            # Different sides of symbol (left, right, top, bottom)
            pinsides = {"l": [], "r": [], "t": [], "b": []}
            pinoffsets = {"l": 0, "r": 0, "t": 0, "b": 0}
            maxNames = {"l": 0, "r": 0, "t": 0, "b": 0}
            pinsGrouped = {}

            # Extract pin groups
            for p in pins:
                if p.type not in pinsGrouped:
                    pinsGrouped[p.type] = []
                pinsGrouped[p.type].append(p)

            # Force some pin group to specific side and draw them
            forcedSides = {
                "l": [self.Pin.PinType.CONFIG, self.Pin.PinType.BOOT, self.Pin.PinType.JTAG, self.Pin.PinType.ADC_REF,
                      self.Pin.PinType.ADC, self.Pin.PinType.ADC_DIODE],
                "r": [],
                "t": [self.Pin.PinType.CORE_POWER, self.Pin.PinType.BRAM_POWER, self.Pin.PinType.AUX_POWER,
                      self.Pin.PinType.BANK_POWER, self.Pin.PinType.ADC_POWER, self.Pin.PinType.BATT_POWER],
                "b": [self.Pin.PinType.GND, self.Pin.PinType.ADC_GND]
            }

            # Draw all non-I/O pin groups
            for s, l in forcedSides.items():
                for g in l:
                    if g not in pinsGrouped:
                        continue

                    mergedPins = {}
                    for p in pinsGrouped[g]:
                        dp = p.drawingPin()
                        if p.name in mergedPins:
                            # Merging pins with same name within group
                            dp.translate(mergedPins[p.name].at)
                            dp.visibility = DrawingPin.PinVisibility.INVISIBLE
                            if (dp.el_type == DrawingPin.PinElectricalType.EL_TYPE_POWER_INPUT) or \
                                (dp.el_type == DrawingPin.PinElectricalType.EL_TYPE_POWER_OUTPUT):
                                dp.el_type = DrawingPin.PinElectricalType.EL_TYPE_PASSIVE
                        else:
                            # Draw pin vertically or horizontally
                            if s == "l" or s == "r":
                                dp.translate(Point(0, -pinoffsets[s] * 100))
                            else:
                                dp.translate(Point(pinoffsets[s] * 100, 0))
                            mergedPins[p.name] = dp
                            pinoffsets[s] = pinoffsets[s] + 1
                        pinsides[s].append(dp)
                    pinoffsets[s] = pinoffsets[s] + 1

            # Draw general IO, starting from left side
            genSide = "l"
            genPins = pinsGrouped[self.Pin.PinType.GENERAL] if self.Pin.PinType.GENERAL in pinsGrouped else []
            for idx in range(0, len(genPins)):
                # Draw pin horizontally
                pin = genPins[idx]
                dp = pin.drawingPin()
                dp.translate(Point(0, -pinoffsets[genSide] * 100))
                pinsides[genSide].append(dp)
                pinoffsets[genSide] = pinoffsets[genSide] + 1

                # Switch side to right when left side is filled
                if genSide == "l" and (pinoffsets["l"] >= (pinoffsets["r"] + (len(genPins) - idx - 1))) \
                        and (not pin.pair or pin.pairNeg):
                    genSide = "r"

            # Calc max pin names - for bounding calculation
            for s, l in pinsides.items():
                for p in l:
                    maxNames[s] = len(p.name) if len(p.name) > maxNames[s] else maxNames[s]

            maxRowNames = 0

            # Calc max names on same row
            for lp in pinsides["l"]:
                for rp in pinsides["r"]:
                    if lp.at.y != rp.at.y:
                        continue

                    l = len(lp.name) + len(rp.name)
                    if l > maxRowNames:
                        maxRowNames = l

            # Calc total vertical/horizontal pin count
            maxLROffset = pinoffsets["l"] if pinoffsets["l"] > pinoffsets["r"] else pinoffsets["r"]
            maxTBOffset = pinoffsets["t"] if pinoffsets["t"] > pinoffsets["b"] else pinoffsets["b"]

            # Pin offset from body - used for pin positioning
            lPinOffset = pinLength + 20 if len(pinsides["l"]) > 0 else 0
            rPinOffset = pinLength + 20 if len(pinsides["r"]) > 0 else 0
            tPinOffset = pinLength + 20 if len(pinsides["t"]) > 0 else 0
            bPinOffset = pinLength + 20 if len(pinsides["b"]) > 0 else 0

            # vStride - size from center to upper/lower corner
            vStride = math.ceil(((maxLROffset - 1) * 100 + (maxNames["t"] + maxNames["b"]) * 48) / 2 / 100) * 100
            top = math.ceil((vStride + tPinOffset) / 100) * 100
            bottom = -math.ceil((vStride + bPinOffset) / 100) * 100

            # hStride - size from center to left/right corner
            hStride = math.ceil(maxRowNames * 48 / 2 / 100) * 100
            hStrideV = math.ceil((maxTBOffset - 1) / 2) * 100
            if hStrideV > hStride:
                hStride = hStrideV
            left =  -math.ceil((hStride + lPinOffset) / 100) * 100
            right = math.ceil((hStride + rPinOffset) / 100) * 100

            # Pin draw starts
            hStartY = math.floor((vStride - maxNames["t"] * 48) / 100) * 100
            tStartX = -math.floor((pinoffsets["t"] - 1) / 2) * 100
            bStartX = -math.floor((pinoffsets["b"] - 1) / 2) * 100

            # Move/rotate pins
            for s, l in pinsides.items():
                for dp in l:
                    dp.unit_idx = bankIdx + 1
                    dp.pin_length = pinLength
                    if s == "l":
                        dp.orientation = DrawingPin.PinOrientation.RIGHT
                        dp.translate(Point(left, hStartY))
                    elif s == "r":
                        dp.translate(Point(right, hStartY))
                    elif s == "t":
                        dp.orientation = DrawingPin.PinOrientation.DOWN
                        dp.translate(Point(tStartX, top))
                    elif s == "b":
                        dp.orientation = DrawingPin.PinOrientation.UP
                        dp.translate(Point(bStartX, bottom))
                    self.symbol.drawing.append(dp)

            # Draw body
            rectX0 = left + pinLength if len(pinsides["l"]) > 0 else left - 100
            rectX1 = right - pinLength if len(pinsides["r"]) > 0 else right + 100
            rectY0 = bottom + pinLength if len(pinsides["b"]) > 0 else bottom - 100
            rectY1 = top - pinLength if len(pinsides["t"]) > 0 else top + 100

            self.symbol.drawing.append(DrawingRectangle(Point(rectX0, rectY0), Point(rectX1, rectY1),
                                                        unit_idx=bankIdx + 1,
                                                        fill=ElementFill.FILL_BACKGROUND))

    def createSymbol(self, gen):
        # Make strings for DCM entries
        desc = (f"Xilinx {self.familyName} FPGA, {self.name.upper()}, {self.packageName.upper()}")
        keywords = f"Xilinx FPGA {self.familyName}"
        datasheet = self._FAMILY_DATASHEETS[self.family]

        # Make the symbol
        self.symbol = gen.addSymbol(self.libraryName, dcm_options={
                'description': desc,
                'keywords': keywords,
                'datasheet': datasheet},
                offset=20)
        # Draw
        self.drawSymbol()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
            description='Generator for Xilinx FPGAs symbols')
    parser.add_argument('dir',
            help='Directory containing ONLY valid Xilinx ASCII package files (CSV)')
    parser.add_argument('-v', '--verbose', action='count', default=0,
            help='Print more information')
    parser.add_argument('--footprints',
                        help='Path to footprint libraries (.pretty dirs)',
                        default='/usr/share/kicad/modules')

    args = parser.parse_args()

    if not os.path.isdir(args.dir):
        parser.error("dir must be directory")

    if args.verbose == 0:
        loglevel = logging.WARNING
    elif args.verbose == 1:
        loglevel = logging.INFO
    elif args.verbose >= 2:
        loglevel = logging.DEBUG

    logging.basicConfig(format='%(levelname)s:\t%(message)s', level=loglevel)

    FOOTPRINT_PATH = args.footprints

    # Load devices from CSV, sorted by family
    libraries = {}
    for path, dirs, files in os.walk(args.dir):
        for file in files:
            fullpath = os.path.join(path, file)
            if fnmatch.fnmatch(fullpath.lower(), '*.csv'):
                fpga = Device(fullpath)
                # If there isn't a SymbolGenerator for this family yet, make one
                if fpga.family not in libraries:
                    libraries[fpga.family] = SymbolGenerator(
                        lib_name=f"FPGA_Xilinx_{fpga.family}")
                # Make a symbol for part
                fpga.createSymbol(libraries[fpga.family])

    # Write libraries
    for gen in libraries.values():
        gen.writeFiles()

