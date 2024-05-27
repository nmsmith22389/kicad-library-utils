import logging
import glob
import sys, os, csv, re, urllib.request
sys.path.append(os.path.join(sys.path[0],'..'))
from KiCadSymbolGenerator import *
from xilinx import xilinx_generator

FOOTPRINT_PATH = "/usr/share/kicad/modules"

PAD_KEY = 'PAD'
NAME_KEY = 'Pin/Ball Function'
BANK_KEY = 'Bank'
HS_KEY = 'High Speed'
DQS_KEY = 'DQS'
DF_KEY = 'Dual Function'

NONE_STR = '-'
SUPPLY_PIN_RE = ['VSS*', 'VCC*']
GND_PIN_RE = ['GND']

class ecp_device(xilinx_generator.Device):
    _FAMILY_PART_REGEXPS = {
        "ECP5": re.compile("ECP5(U|UM|-5G)-(\d+)")
    }
    _FAMILY_NAMES = {
        "ECP5": "ECP5"
    }
    _FAMILY_DATASHEETS = {
        "ECP5": "http://www.latticesemi.com/view_document?document_id=50461"
    }
    _PACKAGE_REGEXP = re.compile("([a-zA-Z]+)(\d+)")

    class Pin(xilinx_generator.Device.Pin):        
        _TYPE_REGEXPS = {
            re.compile("^GND")                    : xilinx_generator.Device.Pin.PinType.GND,
            re.compile("^VCC")                    : xilinx_generator.Device.Pin.PinType.CORE_POWER,
            re.compile("^VCCAUX")                 : xilinx_generator.Device.Pin.PinType.AUX_POWER,
            re.compile("^VCCAUXA\d")              : xilinx_generator.Device.Pin.PinType.MGT_AUX_POWER,
            re.compile("^(RESERVED|NC)")               : xilinx_generator.Device.Pin.PinType.NC,
            re.compile("^P[BLRT]()?(\d+)[ABCD]")  : xilinx_generator.Device.Pin.PinType.GENERAL,
            re.compile("^VCCIO(\d)")              : xilinx_generator.Device.Pin.PinType.BANK_POWER,
            re.compile("^T((DI)|(DO)|(MS)|(CK))") : xilinx_generator.Device.Pin.PinType.JTAG,
            re.compile("^HDRX([NP])\d_D(\d)CH\d") : xilinx_generator.Device.Pin.PinType.MGT_RX,
            re.compile("^HDTX([NP])\d_D(\d)CH\d") : xilinx_generator.Device.Pin.PinType.MGT_TX,
            re.compile("^REFCLK(?=[NP]_D(\d))([NP])_D\d")     : xilinx_generator.Device.Pin.PinType.MGT_REFCLK,
            re.compile("((^VCCA\d)|(^VCCH[RT]X\d_D\dCH\d))") : xilinx_generator.Device.Pin.PinType.MGT_POWER,
            re.compile("^((CCLK)|(CFG_\d)|(DONE))|(INITN)|(PROGRAMN)") : xilinx_generator.Device.Pin.PinType.CONFIG
        }
        _TYPE_DEFAULT_ELTYPE = {
            xilinx_generator.Device.Pin.PinType.GENERAL       : DrawingPin.PinElectricalType.EL_TYPE_BIDIR,
            xilinx_generator.Device.Pin.PinType.CONFIG        : DrawingPin.PinElectricalType.EL_TYPE_INPUT,
            xilinx_generator.Device.Pin.PinType.JTAG          : DrawingPin.PinElectricalType.EL_TYPE_INPUT,
            xilinx_generator.Device.Pin.PinType.CORE_POWER    : DrawingPin.PinElectricalType.EL_TYPE_POWER_INPUT,
            xilinx_generator.Device.Pin.PinType.AUX_POWER     : DrawingPin.PinElectricalType.EL_TYPE_POWER_INPUT,
            xilinx_generator.Device.Pin.PinType.BANK_POWER    : DrawingPin.PinElectricalType.EL_TYPE_POWER_INPUT,
            xilinx_generator.Device.Pin.PinType.GND           : DrawingPin.PinElectricalType.EL_TYPE_POWER_INPUT,
            xilinx_generator.Device.Pin.PinType.NC            : DrawingPin.PinElectricalType.EL_TYPE_NC,
            xilinx_generator.Device.Pin.PinType.MGT_REFCLK    : DrawingPin.PinElectricalType.EL_TYPE_INPUT,
            xilinx_generator.Device.Pin.PinType.MGT_RX        : DrawingPin.PinElectricalType.EL_TYPE_INPUT,
            xilinx_generator.Device.Pin.PinType.MGT_TX        : DrawingPin.PinElectricalType.EL_TYPE_OUTPUT,
            xilinx_generator.Device.Pin.PinType.MGT_POWER     : DrawingPin.PinElectricalType.EL_TYPE_POWER_INPUT,
            xilinx_generator.Device.Pin.PinType.MGT_AUX_POWER : DrawingPin.PinElectricalType.EL_TYPE_POWER_INPUT
        }
        _SPECIAL_ELTYPE = {
            re.compile("^CCLK")                 : DrawingPin.PinElectricalType.EL_TYPE_BIDIR,
            re.compile("^DONE")                 : DrawingPin.PinElectricalType.EL_TYPE_BIDIR,
            re.compile("^((INITN)|(PROGRAMN))") : DrawingPin.PinElectricalType.EL_TYPE_OPEN_COLECTOR,
            re.compile("^TDO")                  : DrawingPin.PinElectricalType.EL_TYPE_OUTPUT,
        }
        
        _BANK_REGEXP = re.compile("(?!)")
        
        _PIN_NAME_REMAP = {}

    def __init__(self, file, pkgindex):
        self.csvFile = file;
        self.banks = {}
        self.pinCount = 0
        self.footprint = ""
        self.valid = False
        self.parseFile(pkgindex)

    def readPins(self):
        f = open(self.csvFile, "r")

        # Default column mapping for 7 series
        paramMapping = {"pin": 7, "name": 1, "bank": 2}
        extraMapping = {"df": 3, "hs": 5, "dqs": 6}

        for line in f:
            params = line.strip().split(",")

            if params[0] == PAD_KEY:
                # Found line describing columns, update column mapping
                for i in range (0, len(params)):
                    if params[i] == self.packageName:
                        paramMapping["pin"] = i
                    elif params[i] == NAME_KEY:
                        paramMapping["name"] = i
                    elif params[i] == BANK_KEY:
                        paramMapping["bank"] = i
                    elif params[i] == DF_KEY:
                        extraMapping["df"] = i
                    elif params[i] == HS_KEY:
                        extraMapping["hs"] = i
                    elif params[i] == DQS_KEY:
                        extraMapping["dqs"] = i
                continue

            # Extract info from row
            dic = {"type":""}
            fail = False
            if params[paramMapping["pin"]] == NONE_STR:
                fail = True
            else:
                for k,v in paramMapping.items():
                    dic[k] = params[v].strip()
                    if dic[k] == "":
                        fail = True
                if params[extraMapping["hs"]] != NONE_STR:
                    dic["name"] += "_HS"
                if params[extraMapping["df"]] != NONE_STR:
                    dic["name"] += "/" + params[extraMapping["df"]]
                if params[extraMapping["dqs"]] != NONE_STR:
                    dic["name"] += "/" + params[extraMapping["dqs"]]

            if fail:
                # That was not pin line
                continue

            # Create pin
            pin = ecp_device.Pin(dic)

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


    def parseFile(self, pkgindex):
        logging.info(f"File {self.csvFile}:")

        # Extract FPGA family/name/package from file name
        values = []
        self.family = ""
        with open(self.csvFile, "r") as csvf:
            header = next(csvf, None)
            for i in range(3):
                next(csvf, None)
            pkgs = [x.strip() for x in next(csvf, None).split(",") if "BGA" in x]
            for f, r in self._FAMILY_PART_REGEXPS.items():
                m = r.search(header)
                if m is not None:
                    self.family = f
                    break;

        if self.family == "":
            return
        if (pkgindex + 1) > len(pkgs):
            self.valid = False
            return

        self.name = m.group(0)
        self.packageName = pkgs[pkgindex]

        if self.family in self._FAMILY_NAMES:
            self.familyName = self._FAMILY_NAMES[self.family]
        else:
            self.familyName = self.family
        self.libraryName = f"{self.name.upper()}_{self.packageName.upper()}"

        pm = self._PACKAGE_REGEXP.match(self.packageName)
        if pm is None:
            self.packagePins = 0
        else:
            self.packagePins = int(pm.group(2))

        # Try to find footprint
        self.footprint = None
        self.footprintFilter = f"Lattice*{self.packageName.upper()}*"

        # A bit ugly here - find footprint in Package_BGA.pretty only
        fpFile = glob.glob(os.path.join(FOOTPRINT_PATH, "Package_BGA.pretty/", self.footprintFilter))
        if len(fpFile) > 0:
            self.footprint = f"Package_BGA:{os.path.splitext(os.path.basename(fpFile[0]))[0]}"

        if not self.footprint:
            self.footprint = f"Package_BGA:Lattice_{self.packageName.upper()}"
            logging.warning(f"{self.libraryName} - cannot find footprint file, suggested {self.footprint}")

        self.readPins()
        
        logging.info(f"  Name:\t\t{self.name}")
        logging.info(f"  Family:\t{self.familyName}")
        logging.info(f"  Package:\t{self.packageName}")
        logging.info(f"  Banks: {len(self.banks)}")
        logging.info(f"  Pins: {self.pinCount}")
        logging.info(f"  Footprint: {self.footprint}")
        logging.info(f"  Footprint filter: {self.footprintFilter}")
        logging.info(f"  Valid: {self.valid}")
        return True

    def createSymbol(self, gen):
        if not self.valid:
            return

        # Make strings for DCM entries
        desc = (f"Lattice {self.familyName} FPGA, {self.name.upper()}, {self.packageName.upper()}")
        keywords = f"Lattice FPGA {self.familyName}"
        datasheet = self._FAMILY_DATASHEETS[self.family]

        # Make the symbol
        self.symbol = gen.addSymbol(self.libraryName, dcm_options={
                'description': desc,
                'keywords': keywords,
                'datasheet': datasheet},
                offset=20)
        # Draw
        self.drawSymbol()
        return True

if __name__ == "__main__":
    s = SymbolGenerator('FPGA_Lattice_ECP')

    with open('link_ecp.csv') as link_file:
        links = [l.split(',')[0] for l in link_file.readlines()]

    for l in links:
        csvpath, info = urllib.request.urlretrieve(l)
        run = True
        pkgnum = 0
        while(run):
            d = ecp_device(csvpath, pkgnum)
            run = d.createSymbol(s)
            pkgnum += 1
    s.writeFiles()
