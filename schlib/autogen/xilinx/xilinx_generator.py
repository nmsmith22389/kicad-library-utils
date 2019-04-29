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

def _roundUp(x, step=100):
    return math.ceil(x / step) * step

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
            PS_GENERAL = 2      # PS_MIO_* - General I/O pins for Zynq CPU (PS)
            CONFIG = 3          # INIT, PROGRAM, DONE - Configuration pins (reset, init, etc.)
            BOOT = 4            # M[2:0] - Boot type
            JTAG = 5            # JTAG
            ADC_REF = 6         # VREFP/VREFN - XADC reference
            ADC = 7             # V_N/V_P - ADC input
            ADC_DIODE = 8       # DXP/DXN - On-die thermal diode
            CORE_POWER = 9      # VCCINT - Core power
            BRAM_POWER = 10     # VCCBRAM - Internal RAM power
            AUX_POWER = 11      # VCCAUX - Aux power
            ADC_POWER = 12      # VCCADC - ADC power
            BATT_POWER = 13     # VCCBATT - Battery backup power
            BANK_POWER = 14     # VCCO_* - I/O power
            MGT_RREF = 15       # MGTRREF* - Termination resistor
            MGT_RCAL = 16       # MGT*RCAL - Calibration resistor
            MGT_REFCLK = 17     # MGTREFCLK* - Transceiver clock
            MGT_RX = 18         # MGT*RX* - Transceiver input
            MGT_TX = 19         # MGT*TX* - Transceiver output
            MGT_POWER = 20      # MGT*VCC* - Transceiver power
            MGT_AUX_POWER = 21  # MGT*VCCAUX* - Transceiver aux power
            MGT_VTT = 22        # MGT*VTT* - Transceiver termination power
            GND = 23            # GND
            ADC_GND = 24        # ADC GND
            NC = 25             # No connect
            PS_CTL = 26         # Control ports of Zynq CPU (PS)
            PS_DDR_DQ = 27      # PS_DDR_DQ* - RAM data for Zynq CPU (PS)
            PS_DDR_DQS = 28     # PS_DDR_DQ* - RAM data strobe for Zynq CPU (PS)
            PS_DDR_DM = 29      # PS_DDR_DM* - RAM data mask for Zynq CPU (PS)
            PS_DDR_A = 30       # PS_DDR_A* - RAM address for Zynq CPU (PS)
            PS_DDR_BA = 31      # PS_DDR_BA* - RAM bank address for Zynq CPU (PS)
            PS_DDR_CTL = 32     # PS_DDR_* - RAM control for Zynq CPU (PS)
            PS_DDR_CLK = 33     # PS_DDR_CK* - RAM clock for Zynq CPU (PS)
            PS_DDR_DCI_REF = 34 # PS_DDR_VR* - RAM DCI reference voltage for Zynq CPU (PS)
            PS_DDR_ODT = 35     # PS_DDR_ODT - RAM termination for Zynq CPU (PS)
            PS_DDR_VREF = 36    # PS_DDR_VREF* - RAM reference voltage for Zynq CPU (PS)
            PS_VCCPINT = 37     # VCCPINT* - Core power for Zynq CPU (PS)
            PS_VCCPAUX = 38     # VCCPAUX - Aux power for Zynq CPU (PS)
            PS_VCCPLL = 39      # VCCPLL - PLL power for Zynq CPU (PS)
            PS_MIO_VREF = 40    # PS_MIO_VREF - reference voltage for Zynq CPU (PS)
            AUX_IO_POWER = 41   # Aux IO Power

        # Pin type filters
        _TYPE_REGEXPS = {
            re.compile("^((PROGRAM)|(INIT)|(DONE))|(CFGBVS)|(CCLK)")
                                                    : PinType.CONFIG,
            re.compile("^M(\d+)")                   : PinType.BOOT,
            re.compile("^T((DI)|(DO)|(MS)|(CK))")   : PinType.JTAG,
            re.compile("^VREF([PN])")               : PinType.ADC_REF,
            re.compile("^V([PN])")                  : PinType.ADC,
            re.compile("^DX([PN])")                 : PinType.ADC_DIODE,
            re.compile("^VCCO_(?:DDR_)?(?:MIO\d*_)?(\d+)")
                                                    : PinType.BANK_POWER,
            re.compile("^VCCINT")                   : PinType.CORE_POWER,
            re.compile("^VCCBRAM")                  : PinType.BRAM_POWER,
            re.compile("^VCCAUX_IO")                : PinType.AUX_IO_POWER,
            re.compile("^VCCAUX")                   : PinType.AUX_POWER,
            re.compile("^VCCADC")                   : PinType.ADC_POWER,
            re.compile("^VCCBATT")                  : PinType.BATT_POWER,
            re.compile("^GNDADC")                   : PinType.ADC_GND,
            re.compile("^GND")                      : PinType.GND,
            re.compile("^PS_((CLK)|(POR_B)|(SRST_B))")
                                                    : PinType.PS_CTL,
            re.compile("^PS_DDR_DQ(\d+)")           : PinType.PS_DDR_DQ,
            re.compile("^PS_DDR_DQS_([PN])(\d+)")   : PinType.PS_DDR_DQS,
            re.compile("^PS_DDR_DM(\d+)")           : PinType.PS_DDR_DM,
            re.compile("^PS_DDR_A(\d+)")            : PinType.PS_DDR_A,
            re.compile("^PS_DDR_BA(\d+)")           : PinType.PS_DDR_BA,
            re.compile("^PS_DDR_((DRST)|(CS_B)|(CKE)|(WE_B)|(CAS_B)|(RAS_B))")
                                                    : PinType.PS_DDR_CTL,
            re.compile("^PS_DDR_CK([PN])")          : PinType.PS_DDR_CLK,
            re.compile("^PS_DDR_VR([PN])")          : PinType.PS_DDR_DCI_REF,
            re.compile("^PS_DDR_ODT")               : PinType.PS_DDR_ODT,
            re.compile("^PS_DDR_VREF(\d+)")         : PinType.PS_DDR_VREF,
            re.compile("^PS_MIO_VREF")              : PinType.PS_MIO_VREF,
            re.compile("^VCCPINT")                  : PinType.PS_VCCPINT,
            re.compile("^VCCPAUX")                  : PinType.PS_VCCPAUX,
            re.compile("^VCCPLL")                   : PinType.PS_VCCPLL,
            re.compile("^IO_(L?)(\d+)([PN]?)")      : PinType.GENERAL,
            re.compile("^PS_MIO(\d+)")              : PinType.PS_GENERAL,
            re.compile("^MGTRREF")                  : PinType.MGT_RREF,
            re.compile("^MGT\w+RCAL")               : PinType.MGT_RCAL,
            re.compile("^MGTREFCLK(\d+)([PN])")     : PinType.MGT_REFCLK,
            re.compile("^MGT[PXH]RX([PN])(\d+)")    : PinType.MGT_RX,
            re.compile("^MGT[PXH]TX([PN])(\d+)")    : PinType.MGT_TX,
            re.compile("^MGTAVCC")                  : PinType.MGT_POWER,
            re.compile("^MGTAVTT")                  : PinType.MGT_VTT,
            re.compile("^MGTVCCAUX")                : PinType.MGT_AUX_POWER,
            re.compile("^(NC)|(RSVDGND)")           : PinType.NC
        }

        # Default KiCAD electrical type for pin types
        _TYPE_DEFAULT_ELTYPE = {
            PinType.GENERAL:        DrawingPin.PinElectricalType.EL_TYPE_BIDIR,
            PinType.PS_GENERAL:     DrawingPin.PinElectricalType.EL_TYPE_BIDIR,
            PinType.CONFIG:         DrawingPin.PinElectricalType.EL_TYPE_INPUT,
            PinType.BOOT:           DrawingPin.PinElectricalType.EL_TYPE_INPUT,
            PinType.JTAG:           DrawingPin.PinElectricalType.EL_TYPE_INPUT,
            PinType.ADC_REF:        DrawingPin.PinElectricalType.EL_TYPE_PASSIVE,
            PinType.ADC:            DrawingPin.PinElectricalType.EL_TYPE_INPUT,
            PinType.ADC_DIODE:      DrawingPin.PinElectricalType.EL_TYPE_PASSIVE,
            PinType.CORE_POWER:     DrawingPin.PinElectricalType.EL_TYPE_POWER_INPUT,
            PinType.BRAM_POWER:     DrawingPin.PinElectricalType.EL_TYPE_POWER_INPUT,
            PinType.AUX_POWER:      DrawingPin.PinElectricalType.EL_TYPE_POWER_INPUT,
            PinType.ADC_POWER:      DrawingPin.PinElectricalType.EL_TYPE_POWER_INPUT,
            PinType.BATT_POWER:     DrawingPin.PinElectricalType.EL_TYPE_POWER_INPUT,
            PinType.BANK_POWER:     DrawingPin.PinElectricalType.EL_TYPE_POWER_INPUT,
            PinType.GND:            DrawingPin.PinElectricalType.EL_TYPE_POWER_INPUT,
            PinType.ADC_GND:        DrawingPin.PinElectricalType.EL_TYPE_POWER_INPUT,
            PinType.NC:             DrawingPin.PinElectricalType.EL_TYPE_NC,
            PinType.MGT_RREF:       DrawingPin.PinElectricalType.EL_TYPE_PASSIVE,
            PinType.MGT_RCAL:       DrawingPin.PinElectricalType.EL_TYPE_PASSIVE,
            PinType.MGT_REFCLK:     DrawingPin.PinElectricalType.EL_TYPE_INPUT,
            PinType.MGT_RX:         DrawingPin.PinElectricalType.EL_TYPE_INPUT,
            PinType.MGT_TX:         DrawingPin.PinElectricalType.EL_TYPE_OUTPUT,
            PinType.MGT_POWER:      DrawingPin.PinElectricalType.EL_TYPE_POWER_INPUT,
            PinType.MGT_VTT:        DrawingPin.PinElectricalType.EL_TYPE_POWER_INPUT,
            PinType.MGT_AUX_POWER:  DrawingPin.PinElectricalType.EL_TYPE_POWER_INPUT,
            PinType.PS_CTL:         DrawingPin.PinElectricalType.EL_TYPE_INPUT,
            PinType.PS_DDR_DQ:      DrawingPin.PinElectricalType.EL_TYPE_BIDIR,
            PinType.PS_DDR_DQS:     DrawingPin.PinElectricalType.EL_TYPE_BIDIR,
            PinType.PS_DDR_DM:      DrawingPin.PinElectricalType.EL_TYPE_OUTPUT,
            PinType.PS_DDR_A:       DrawingPin.PinElectricalType.EL_TYPE_OUTPUT,
            PinType.PS_DDR_BA:      DrawingPin.PinElectricalType.EL_TYPE_OUTPUT,
            PinType.PS_DDR_CTL:     DrawingPin.PinElectricalType.EL_TYPE_OUTPUT,
            PinType.PS_DDR_CLK:     DrawingPin.PinElectricalType.EL_TYPE_OUTPUT,
            PinType.PS_DDR_DCI_REF: DrawingPin.PinElectricalType.EL_TYPE_PASSIVE,
            PinType.PS_DDR_ODT:     DrawingPin.PinElectricalType.EL_TYPE_OUTPUT,
            PinType.PS_DDR_VREF:    DrawingPin.PinElectricalType.EL_TYPE_PASSIVE,
            PinType.PS_VCCPINT:     DrawingPin.PinElectricalType.EL_TYPE_POWER_INPUT,
            PinType.PS_VCCPAUX:     DrawingPin.PinElectricalType.EL_TYPE_POWER_INPUT,
            PinType.PS_VCCPLL:      DrawingPin.PinElectricalType.EL_TYPE_POWER_INPUT,
            PinType.PS_MIO_VREF:    DrawingPin.PinElectricalType.EL_TYPE_PASSIVE,
            PinType.AUX_IO_POWER:   DrawingPin.PinElectricalType.EL_TYPE_POWER_INPUT
        }

        # Some dedicated pins has different electrical type...
        _SPECIAL_ELTYPE = {
            re.compile("^CCLK"):    DrawingPin.PinElectricalType.EL_TYPE_BIDIR,
            re.compile("^DONE"):    DrawingPin.PinElectricalType.EL_TYPE_BIDIR,
            re.compile("^INIT"):    DrawingPin.PinElectricalType.EL_TYPE_OPEN_COLECTOR,
            re.compile("^TDO"):     DrawingPin.PinElectricalType.EL_TYPE_OUTPUT,
        }

        _BANK_REGEXP = re.compile(".+_(\d+)$")

        # Some pins should be tied either to GND or VCC, so just rename them
        _PIN_NAME_REMAP = {
            re.compile("^RSVDVCC\d*"):  "VCCO_0"
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

            # Rename, if needed
            for r, n in self._PIN_NAME_REMAP.items():
                m = r.match(self.name)
                if m:
                    logging.info(f"Renaming {self.name} -> {n}")
                    self.name = n

            # Check bank name
            m = self._BANK_REGEXP.match(self.name)
            if m:
                newBank = int(m.group(1));
                if self.bank != newBank:
                    logging.warning(f"Wrong bank for {self.name}, was {self.bank} should be {newBank}")
                    self.bank = newBank

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
            elif self.type == self.PinType.PS_GENERAL or self.type == self.PinType.PS_DDR_DQ or \
                    self.type == self.PinType.PS_DDR_DM or self.type == self.PinType.PS_DDR_A or \
                    self.type == self.PinType.PS_DDR_BA or self.type == self.PinType.PS_DDR_VREF:
                self.number = int(m.group(1))
            elif self.type == self.PinType.ADC or self.type == self.PinType.ADC_DIODE or \
                    self.type == self.PinType.ADC_REF or self.type == self.PinType.PS_DDR_CLK or \
                    self.type == self.PinType.PS_DDR_DCI_REF:
                self.pair = True
                self.pairNeg = m.group(1) == "N"
            elif self.type == self.PinType.MGT_REFCLK:
                self.number = int(m.group(1))
                self.pair = True
                self.pairNeg = m.group(2) == "N"
            elif self.type == self.PinType.MGT_RX or self.type == self.PinType.MGT_TX \
                    or self.type == self.PinType.PS_DDR_DQS:
                self.number = int(m.group(2))
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
        self.valid = False

        self.parseFile()

    def readPins(self):
        f = open(self.csvFile, "r")

        # Default column mapping for 7 series
        paramMapping = {"pin": 0, "name": 1, "bank": 3, "type": 6}

        for line in f:
            params = line.strip().split(",")

            if params[0].lower() == "pin":
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
            fail = False
            for k,v in paramMapping.items():
                dic[k] = params[v].strip()
                if dic[k] == "":
                    fail = True

            if fail:
                # That was not pin line
                continue

            # Create pin
            pin = Device.Pin(dic)

            # Place pin into bank (or create it)
            if pin.bank not in self.banks:
                self.banks[pin.bank] = []
            self.banks[pin.bank].append(pin)

        self.pinCount = 0
        self.valid = True

        # Sort pins inside banks
        for k,_ in self.banks.items():
            self.banks[k].sort()
            self.pinCount += len(self.banks[k])

        for k, v in self.banks.items():
            logging.debug(f"Bank {k}")
            for pin in v:
                logging.debug(f"  {pin}")

        # Primitive error checking
        for k, v in self.banks.items():
            for pin in v:
                if pin.type == self.Pin.PinType.UNKNOWN:
                    self.valid = False

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
        logging.info(f"  Valid: {self.valid}")

    def drawSymbol(self):
        bankList = list(self.banks.items())
        pinList = []

        for b, l in bankList:
            pinList.extend(l)

        # Basic info
        self.symbol.setReference('U')
        self.symbol.setValue(value=self.libraryName.upper())
        if self.footprint:
            self.symbol.setDefaultFootprint(value=self.footprint)
        if self.footprintFilter:
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
                      self.Pin.PinType.ADC, self.Pin.PinType.ADC_DIODE, self.Pin.PinType.MGT_RX,
                      self.Pin.PinType.MGT_REFCLK, self.Pin.PinType.MGT_RREF, self.Pin.PinType.MGT_RCAL,
                      self.Pin.PinType.PS_MIO_VREF, self.Pin.PinType.PS_CTL, self.Pin.PinType.PS_DDR_DQ,
                      self.Pin.PinType.PS_DDR_DQS, self.Pin.PinType.PS_DDR_DM],
                "r": [self.Pin.PinType.MGT_TX, self.Pin.PinType.PS_DDR_VREF, self.Pin.PinType.PS_DDR_CLK,
                      self.Pin.PinType.PS_DDR_CTL, self.Pin.PinType.PS_DDR_A, self.Pin.PinType.PS_DDR_BA,
                      self.Pin.PinType.PS_DDR_DCI_REF, self.Pin.PinType.PS_DDR_ODT],
                "t": [self.Pin.PinType.CORE_POWER, self.Pin.PinType.BRAM_POWER, self.Pin.PinType.AUX_POWER,
                      self.Pin.PinType.AUX_IO_POWER, self.Pin.PinType.BANK_POWER, self.Pin.PinType.ADC_POWER,
                      self.Pin.PinType.BATT_POWER, self.Pin.PinType.MGT_POWER, self.Pin.PinType.MGT_AUX_POWER,
                      self.Pin.PinType.MGT_VTT, self.Pin.PinType.PS_VCCPINT, self.Pin.PinType.PS_VCCPAUX,
                      self.Pin.PinType.PS_VCCPLL],
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
                        pinList.remove(p)
                    pinoffsets[s] = pinoffsets[s] + 1

            # Draw general IO, starting from left side
            genSide = "l"
            genPins = pinsGrouped[self.Pin.PinType.GENERAL] if self.Pin.PinType.GENERAL in pinsGrouped else []

            if self.Pin.PinType.PS_GENERAL in pinsGrouped:
                genPins.extend(pinsGrouped[self.Pin.PinType.PS_GENERAL])

            for idx in range(0, len(genPins)):
                # Draw pin horizontally
                pin = genPins[idx]
                dp = pin.drawingPin()
                dp.translate(Point(0, -pinoffsets[genSide] * 100))
                pinsides[genSide].append(dp)
                pinoffsets[genSide] = pinoffsets[genSide] + 1
                pinList.remove(pin)

                # Switch side to right when left side is filled
                if genSide == "l" and (pinoffsets["l"] >= (pinoffsets["r"] + (len(genPins) - idx - 1))) \
                        and (not pin.pair or pin.pairNeg):
                    genSide = "r"

            # Fix offsets
            if len(genPins) > 0:
                pinoffsets["l"] = pinoffsets["l"] + 1
                pinoffsets["r"] = pinoffsets["r"] + 1

            for k,v in pinoffsets.items():
                if pinoffsets[k] >= 2:
                    pinoffsets[k] = pinoffsets[k] - 2

            # Calc max pin names - for bounding calculation
            for s, l in pinsides.items():
                for p in l:
                    ceilName = len(p.name) * 48
                    maxNames[s] = ceilName if ceilName > maxNames[s] else maxNames[s]

            maxRowNames = maxNames["l"] if maxNames["l"] > maxNames["r"] else maxNames["r"]
            if pinoffsets["l"] > 0 and pinoffsets["r"] > 0:
                maxRowNames = maxRowNames * 2

            # Calc total vertical/horizontal pin count
            maxLRHeight = (pinoffsets["l"] if pinoffsets["l"] > pinoffsets["r"] else pinoffsets["r"]) * 100
            maxTBWidth = (pinoffsets["t"] if pinoffsets["t"] > pinoffsets["b"] else pinoffsets["b"]) * 100

            if maxRowNames > maxTBWidth:
                width = _roundUp(maxRowNames + maxTBWidth + 200, 200)
                height = _roundUp(maxLRHeight + 200, 200)
            else:
                width = _roundUp(maxTBWidth + 200, 200)
                height = _roundUp(maxLRHeight, 200) + _roundUp(_roundUp(maxNames["t"] + 70) + _roundUp(maxNames["b"] + 70), 200)

            left = - width / 2
            right = width / 2
            top = height / 2
            bottom = - height / 2

            # Pin draw starts
            if maxRowNames > maxTBWidth:
                hStartY =  height / 2 - _roundUp((height - maxLRHeight) / 2)
            else:
                hStartY = height / 2 - _roundUp(maxNames["t"] + 70)

            tStartX = _roundUp((width - pinoffsets["t"] * 100) / 2) - width / 2
            bStartX = _roundUp((width - pinoffsets["b"] * 100) / 2) - width / 2

            # Move/rotate pins
            for s, l in pinsides.items():
                for dp in l:
                    dp.unit_idx = bankIdx + 1
                    dp.pin_length = pinLength
                    if s == "l":
                        dp.orientation = DrawingPin.PinOrientation.RIGHT
                        dp.translate(Point(left - pinLength, hStartY))
                    elif s == "r":
                        dp.translate(Point(right + pinLength, hStartY))
                    elif s == "t":
                        dp.orientation = DrawingPin.PinOrientation.DOWN
                        dp.translate(Point(tStartX, top + pinLength))
                    elif s == "b":
                        dp.orientation = DrawingPin.PinOrientation.UP
                        dp.translate(Point(bStartX, bottom - pinLength))
                    self.symbol.drawing.append(dp)

            # Draw body
            self.symbol.drawing.append(DrawingRectangle(Point(left, bottom), Point(right, top),
                                                        unit_idx=bankIdx + 1,
                                                        fill=ElementFill.FILL_BACKGROUND))

        for pin in pinList:
            if pin.type != self.Pin.PinType.NC:
                logging.warning(f"Unplaced pin: {pin.name} ({pin.pin})")

    def createSymbol(self, gen):
        if not self.valid:
            return

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

