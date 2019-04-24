#!/usr/bin/env python3

import argparse
import os
import sys
import logging
import re
import os.path
import fnmatch

sys.path.append(os.path.join(sys.path[0],'..'))
from KiCadSymbolGenerator import *

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

    class Pin:
        _IO_PIN_REGEXP = re.compile("IO_(L?)(\d+)([PN]?)")

        def __init__(self, dic):
            self.pin = dic["pin"]
            self.name = dic["name"]
            try:
                self.bank = int(dic["bank"])
            except:
                self.bank = -1

            self.type = dic["type"]

            self.number = -1
            self.pair = False
            self.pairNeg = False

            # Detect pin/pair name
            m = self._IO_PIN_REGEXP.match(self.name)
            if m:
                if m.group(1) == "L":
                    self.pair = True
                    self.pairNeg = m.group(3) == "N"
                self.number = int(m.group(2))

        # For sorting
        def __lt__(self, other):
            if self.bank < other.bank:
                return True
            elif self.bank == other.bank:
                if self.number < other.number:
                    return True
                elif self.number == other.number:
                    if self.pairNeg < other.pairNeg:
                        return True
                    elif self.pairNeg == other.pairNeg:
                        return self.name < other.name

        def __str__(self):
            return f"({self.name}, {self.pin}, {self.bank}, {self.type}, {self.number}, {self.pair}, {self.pairNeg})"

        def drawingPin(self, **kwargs):
            return DrawingPin(at=Point(0, 0), number=self.pin, name=self.name, **kwargs)

    def __init__(self, file):
        self.csvFile = file;
        self.parseFileName()
        self.readPins()

    def readPins(self):
        f = open(self.csvFile, "r")

        self.banks = {}

        # Default for 7 series
        paramMapping = {"pin": 0, "name": 1, "bank": 3, "type": 6}

        for line in f:
            params = line.strip().split(",")

            if "" in params:
                continue;
            elif params[0].lower() == "pin":
                # Parse line describing columns
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
            dic = {}
            for k,v in paramMapping.items():
                dic[k] = params[v].strip()

            pin = Device.Pin(dic)

            if pin.bank not in self.banks:
                self.banks[pin.bank] = []
            self.banks[pin.bank].append(pin)

        self.pinCount = 0
        # Sort pins inside banks
        for k,_ in self.banks.items():
            self.banks[k].sort()
            self.pinCount += len(self.banks[k])

        for k, v in self.banks.items():
            logging.info(f"Bank {k}")
            for pin in v:
                logging.debug(f"  {pin}")
        logging.info(f"Total pins: {self.pinCount }")

        if self.pinCount != self.packagePins:
            logging.warning(f"Package pin count mismatch: found {self.pinCount} pins, should be {self.packagePins}")



    def parseFileName(self):
        logging.info(f"File {self.csvFile}:")

        baseName = os.path.basename(self.csvFile)

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

        logging.info(f"  Name:\t\t{self.name}")
        logging.info(f"  Family:\t{self.familyName}")
        logging.info(f"  Package:\t{self.packageName}")
        logging.info(f"  Capacity:\t{self.capacity}")

    def drawSymbol(self):
        bank_list = list(self.banks.items())

        self.symbol.setReference('U')
        self.symbol.setValue(value=self.libraryName)
        self.symbol.num_units = len(bank_list)
        self.symbol.interchangable = Symbol.UnitsInterchangable.NOT_INTERCHANGEABLE

        for bank_idx in range(0, self.symbol.num_units):
            bank, pins = bank_list[bank_idx]
            y = 0
            for pin in pins:
                dp = pin.drawingPin()

                dp.translate(Point(0, y))
                dp.unit_idx = bank_idx + 1

                self.symbol.drawing.append(dp)
                y += 100

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
        self.drawSymbol()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
            description='Generator for Xilinx FPGAs symbols')
    parser.add_argument('dir',
            help='Directory containing ONLY valid Xilinx ASCII package files (CSV)')
    parser.add_argument('-v', '--verbose', action='count', default=0,
            help='Print more information')

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

