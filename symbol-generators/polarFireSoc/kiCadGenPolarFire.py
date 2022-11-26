#!/usr/bin/env python3

# Usage:
# Step 1: Create a sheets folder that looks like this:
#  sheets/
#  ├── MPFS025T_MPFS025TS-FCSG325_Package_Pin_Assignment_Table_Public.xlsx
#  ├── MPFS025T_MPFS025TS-FCVG484_Package_Pin_Assignment_Table_Public.xlsx
#  ├── MPFS095T_MPFS095TS-FCSG536_Package_Pin_Assignment_Table_Public.xlsx
#  ├── MPFS095T_MPFS095TS-FCVG484_Package_Pin_Assignment_Table_Public.xlsx
#  ├── MPFS095T_MPFS095TS-FCVG784_Package_Pin_Assignment_Table_Public.xlsx
#  ├── MPFS160T_MPFS160TS-FCSG536_Package_Pin_Assignment_Table_Public.xlsx
#  ├── MPFS160T_MPFS160TS-FCVG484_Package_Pin_Assignment_Table_Public.xlsx
#  ├── MPFS160T_MPFS160TS-FCVG784_Package_Pin_Assignment_Table_Public.xlsx
#  ├── MPFS250T_MPFS250TS-FCG1152_Package_Pin_Assignment_Table_Public.xlsx
#  ├── MPFS250T_MPFS250TS-FCSG536_Package_Pin_Assignment_Table_Public.xlsx
#  ├── MPFS250T_MPFS250TS-FCVG484_Package_Pin_Assignment_Table_Public.xlsx
#  ├── MPFS250T_MPFS250TS-FCVG784_Package_Pin_Assignment_Table_Public.xlsx
#  └── MPFS460T_MPFS460TS-FCG1152_Package_Pin_Assignment_Table_Public.xlsx
# As of 11/24/22 the download format has a time/date code prefix and +'s
# Use this line to change to the format this script wants
# for f in *.xlsx; do NEW_NAME=$(echo $f | sed 's/.*++//g' | sed 's/+/_/g'); cp $f $NEW_NAME; done
#
# The general page is here:
# https://www.microchip.com/en-us/products/fpgas-and-plds/system-on-chip-fpgas/polarfire-soc-fpgas#Documentation
#
# Step 2: Run script
#  cd kicad-library-utils/symbol-generators/polarFireSoc
#  python3 kiCadGenPolarFire.py
#
# Step 3: Copy generated file to kicad-library dir
#  cp SoC_PolarFire.kicad_sym <KICAD6_SYMBOL_DIR>/kicad-symbols/
#
# Step 4: Edit sym-lib-table

# add directory (common) that contains the kicad_sym lib to the path
# you can also use a relative module path instead
import os
import sys

common = os.path.abspath(
    os.path.join(os.path.dirname(__file__), os.path.pardir, "..", "common")
)
print(common)
if common not in sys.path:
    sys.path.insert(0, common)

common_symgen = os.path.abspath(
    os.path.join(os.path.dirname(__file__), os.path.pardir, "common")
)
print(common_symgen)
if common_symgen not in sys.path:
    sys.path.insert(0, common_symgen)

from kicad_sym import Circle, KicadLibrary, KicadSymbol, Pin, Rectangle
from DrawingElements import Drawing, DrawingPin, DrawingRectangle, DrawingText, ElementFill
from Point import Point

# read in excel pin table
from openpyxl import load_workbook

class PolarFireDrawing(Drawing):
    def __get_row(self, pin_name):
        for row in self.sh.rows:
            if row[self.idx_name].value == pin_name:
                return row
        # if there are no matches exit with failure
        print("No matching row for", pin_name, ", exiting...")
        exit(1)

    def __draw_pin(self, pin_name, x, y, pin_dir):
        row = self.__get_row(pin_name)
        if row[self.idx_used].value == "1":
            print("Already used", pin_name, ", exiting...")
            exit(1)
        row[self.idx_used].value = "1"
        #print(pin+" "+row[self.idx_name].value)
        self.append(DrawingPin(at=Point({'x':x, 'y':y}, grid=100),
                                                number=str(row[self.idx_pad].value), unit_idx=self.cur_unit,
                                                orientation = pin_dir,
                                                el_type = self.el_type[row[self.idx_dir].value],
                                                name = pin_name,
                                                pin_length = 200))

    # Use this function for Power Input pins where only the 1st is visible
    def __draw_group_by_name(self, grpName, x, y, pin_dir):
        ii = 0
        for row in self.sh.rows:
            # quick check of the pad name to see if it has a digit
            s = str(row[self.idx_pad].value)
            found_dig = False
            for i, c in enumerate(s):
                if c.isdigit():
                    found_dig = True
                    break
            if found_dig:
                if row[self.idx_name].value == grpName:
                    if ii == 0:
                        vis = DrawingPin.PinVisibility.VISIBLE
                        elType = DrawingPin.PinElectricalType.EL_TYPE_POWER_INPUT
                    else:
                        vis = DrawingPin.PinVisibility.INVISIBLE
                        elType = DrawingPin.PinElectricalType.EL_TYPE_PASSIVE


                    self.append(DrawingPin(at=Point({'x':x, 'y':y}, grid=100),
                                                    number=str(row[self.idx_pad].value), unit_idx=self.cur_unit,
                                                    orientation = pin_dir,
                                                    el_type = elType,
                                                    visibility = vis,
                                                    name = row[self.idx_name].value,
                                                    pin_length = 200))
                    if row[self.idx_used].value == "1":
                        print("Already used", pin_name, ", exiting...")
                        exit(1)
                    row[self.idx_used].value = "1"
                    #print(row[self.idx_name].value, row[self.idx_pad].value)
                    ii = ii+1

    def __init__(self, pn, pkg):

        Drawing.__init__(self)

        DBG_LVL = 0

        self.pn = pn
        self.pkg = pkg

        # MPFS250T_MPFS250TS_FCVG484_Package_Pin_Assignment_Table_Public.xlsx
        filename = self.pn+'_'+self.pn+'S-'+self.pkg+'_Package_Pin_Assignment_Table_Public.xlsx'
        wb = load_workbook("sheets/"+filename)
        self.sh = wb[self.pn+'-'+self.pkg]

        # define the column indexes of the spreadsheet
        self.idx_pad = 0
        self.idx_name = 1
        self.idx_bank = 3
        self.idx_dir = 4
        self.idx_type = 5
        # insert this column to keep track of if the row has been used
        self.idx_used = 6
        self.sh.insert_cols(self.idx_used)
        # mark all rows as not used
        maxBnk = 0;
        for row in self.sh.rows:
            # quick check of the pad name to see if it has a digit
            s = str(row[self.idx_pad].value)
            found_dig = False
            for i, c in enumerate(s):
                if c.isdigit():
                    found_dig = True
                    break
            if found_dig:
                row[self.idx_used].value = "0"
                if str(row[self.idx_bank].value).isnumeric():
                    if int(row[self.idx_bank].value) > maxBnk:
                        maxBnk = row[self.idx_bank].value
                #print("Bank No", row[self.idx_bank].value)
                #print("found digit at: "+str(i))

        self.el_type = {'I':   DrawingPin.PinElectricalType.EL_TYPE_INPUT,
                        'O':   DrawingPin.PinElectricalType.EL_TYPE_OUTPUT,
                        'I/O': DrawingPin.PinElectricalType.EL_TYPE_BIDIR,
                        'HSI': DrawingPin.PinElectricalType.EL_TYPE_INPUT,
                        'HSO': DrawingPin.PinElectricalType.EL_TYPE_OUTPUT,
                        'N/A': DrawingPin.PinElectricalType.EL_TYPE_POWER_INPUT}

        ###############################################################################
        ##                             NC PINs                                       ##
        ##          This little section needs to be done before we set num_units     ##
        ###############################################################################
        bank = maxBnk+3
        self.cur_unit = bank+1

        ioType = "NC"
        NC_count = 0
        for row in self.sh.rows:
            # quick check of the pad name to see if it has a digit
            s = str(row[self.idx_pad].value)
            found_dig = False
            for i, c in enumerate(s):
                if c.isdigit():
                    found_dig = True
                    break
            if found_dig:
                pin = str(row[self.idx_name].value)
                testStr = pin[0:len(ioType)]
                if testStr == ioType:
                    NC_count = NC_count + 1

        # There 2 or 3 extra non-Bank units: Power, XCVR and possibly NC
        if NC_count>0:
            numUnits = maxBnk+1+3
        else:
            numUnits = maxBnk+1+2

        print("#### Creating symbol",self.pn+'-'+self.pkg,"####");

        if DBG_LVL >= 1:
            print("The max Bank for this package is", maxBnk)


        ###############################################################################
        ##                             Bank 0                                        ##
        ###############################################################################
        bank = 0
        self.cur_unit = bank+1

        # first get a count of all Bank 0 HSIO
        ioType = "HSIO"
        count = 0
        for row in self.sh.rows:
            # quick check of the pad name to see if it has a digit
            pin = str(row[self.idx_name].value)
            testStr = pin[0:len(ioType)]
            if testStr == ioType and row[self.idx_bank].value == bank:
                count = count + 1
                #print(pin)

        if DBG_LVL >= 1:
            print("There are", count, "Bank", bank, ioType, "pins")

        # count x 1.5, because it's groups of 2 then a skip
        # first /2 for 2 sides second /2 for y0 being +/-
        y0 = round((count*1.5+4+6)/2/2)*100
        x0 = 1900

        if count%2 != 0:
            print(ioType, "count is not even, exiting")
            exit(1)

        if DBG_LVL >= 1:
            print("Bank", bank, " creation:")

        y = y0-400
        i = 0
        for row in self.sh.rows:
            # quick check of the pad name to see if it has a digit
            pin = str(row[self.idx_name].value)
            testStr = pin[0:len(ioType)]
            if testStr == ioType and row[self.idx_bank].value == bank:
                if i < count/2:
                    pin_dir = DrawingPin.PinOrientation.RIGHT
                    xLoc = -x0-210
                else:
                    pin_dir = DrawingPin.PinOrientation.LEFT
                    xLoc = x0+210
                row[self.idx_used].value = "1"
                #print(pin+" "+row[self.idx_name].value)
                self.append(DrawingPin(at=Point({'x':xLoc, 'y':y}, grid=100),
                                                            number=str(row[self.idx_pad].value), unit_idx=self.cur_unit,
                                                            orientation = pin_dir,
                                                            el_type = self.el_type[row[self.idx_dir].value],
                                                            name = pin,
                                                            pin_length = 200))
                # on the even numbers skip 2 on the odds just skip 1
                y = y-100-(i%2)*100
                # reset back to the top for the second side
                if i == count/2-1:
                    y = y0-400
                i = i+1

        # draw the outline
        rect = DrawingRectangle(start={'x':-x0, 'y':-y0}, end={'x':x0, 'y':y0}, unit_idx=self.cur_unit, fill=ElementFill.FILL_BACKGROUND)
        self.append(rect)
        # draw the bank text
        bnk_txt = DrawingText(at=Point({'x':0, 'y':y0-200}), text="BANK "+str(bank), size=100, unit_idx=self.cur_unit)
        self.append(bnk_txt)

        ###############################################################################
        ##                             Bank 1                                        ##
        ###############################################################################
        bank = 1
        self.cur_unit = bank+1

        # first get a count of all GPIO
        ioType = "GPIO"
        count = 0
        for row in self.sh.rows:
            # quick check of the pad name to see if it has a digit
            pin = str(row[self.idx_name].value)
            testStr = pin[0:len(ioType)]
            if testStr == ioType and row[self.idx_bank].value == bank:
                count = count + 1
                #print(pin)

        if DBG_LVL >= 1:
            print("There are", count, "Bank", bank, ioType, "pins")

        # count x 1.5, because it's groups of 2 then a skip
        # first /2 for 2 sides second /2 for y0 being +/-
        y0 = round((count*1.5+4+6)/2/2)*100
        x0 = 1900

        if count%2 != 0:
            print(ioType, "count is not even, exiting")
            exit(1)

        if DBG_LVL >= 1:
            print("Bank", bank, " creation:")

        y = y0-400
        i = 0
        for row in self.sh.rows:
            # quick check of the pad name to see if it has a digit
            pin = str(row[self.idx_name].value)
            testStr = pin[0:len(ioType)]
            if testStr == ioType and row[self.idx_bank].value == bank:
                if i < count/2:
                    pin_dir = DrawingPin.PinOrientation.RIGHT
                    xLoc = -x0-210
                else:
                    pin_dir = DrawingPin.PinOrientation.LEFT
                    xLoc = x0+210
                row[self.idx_used].value = "1"
                #print(pin+" "+row[self.idx_name].value)
                self.append(DrawingPin(at=Point({'x':xLoc, 'y':y}, grid=100),
                                                            number=str(row[self.idx_pad].value), unit_idx=self.cur_unit,
                                                            orientation = pin_dir,
                                                            el_type = self.el_type[row[self.idx_dir].value],
                                                            name = pin,
                                                            pin_length = 200))
                # on the even numbers skip 2 on the odds just skip 1
                y = y-100-(i%2)*100
                # reset back to the top for the second side
                if i == count/2-1:
                    y = y0-400
                i = i+1

        # draw the outline
        rect = DrawingRectangle(start={'x':-x0, 'y':-y0}, end={'x':x0, 'y':y0}, unit_idx=self.cur_unit, fill=ElementFill.FILL_BACKGROUND)
        self.append(rect)
        # draw the bank text
        bnk_txt = DrawingText(at=Point({'x':0, 'y':y0-200}), text="BANK "+str(bank), size=100, unit_idx=self.cur_unit)
        self.append(bnk_txt)

        ###############################################################################
        ##                             Bank 2                                        ##
        ###############################################################################
        bank = 2
        self.cur_unit = bank+1

        y0 = 900
        x0 = 700

        if DBG_LVL >= 1:
            print("Bank", bank, "left hand side creation:")

        y = y0-400
        for i in range(12):
            self.__draw_pin("MSSIO"+str(i+14)+"B2", -x0-210, y, DrawingPin.PinOrientation.RIGHT);
            y = y-100

        if DBG_LVL >= 1:
            print("Bank", bank, "right hand side creation:")

        y = y0-400
        for i in range(12):
            self.__draw_pin("MSSIO"+str(i+26)+"B2", x0+210, y, DrawingPin.PinOrientation.LEFT);
            y = y-100

        # draw the outline
        rect = DrawingRectangle(start={'x':-x0, 'y':-y0}, end={'x':x0, 'y':y0}, unit_idx=self.cur_unit, fill=ElementFill.FILL_BACKGROUND)
        self.append(rect)
        # draw the bank text
        bnk_txt = DrawingText(at=Point({'x':0, 'y':y0-200}), text="BANK "+str(bank), size=100, unit_idx=self.cur_unit)
        self.append(bnk_txt)

        ###############################################################################
        ##                             Bank 3                                        ##
        ###############################################################################
        bank = 3
        self.cur_unit = bank+1

        y0 = 600
        x0 = 700

        if DBG_LVL >= 1:
            print("Bank", bank,"left hand side creation:")

        self.__draw_pin("FF_EXIT_N", -x0-210, y0-400, DrawingPin.PinOrientation.RIGHT);
        self.__draw_pin("IO_CFG_INTF", -x0-210, y0-500, DrawingPin.PinOrientation.RIGHT);
        self.__draw_pin("SPI_EN", -x0-210, y0-600, DrawingPin.PinOrientation.RIGHT);
        self.__draw_pin("SCK", -x0-210, y0-700, DrawingPin.PinOrientation.RIGHT);
        self.__draw_pin("SDO", -x0-210, y0-800, DrawingPin.PinOrientation.RIGHT);
        self.__draw_pin("SDI", -x0-210, y0-900, DrawingPin.PinOrientation.RIGHT);
        self.__draw_pin("SS", -x0-210, y0-1000, DrawingPin.PinOrientation.RIGHT);

        if DBG_LVL >= 1:
            print("Bank", bank,"right hand side creation:")

        self.__draw_pin("DEVRST_N", x0+210, y0-400, DrawingPin.PinOrientation.LEFT);
        self.__draw_pin("TCK", x0+210, y0-500, DrawingPin.PinOrientation.LEFT);
        self.__draw_pin("TDI", x0+210, y0-600, DrawingPin.PinOrientation.LEFT);
        self.__draw_pin("TDO", x0+210, y0-700, DrawingPin.PinOrientation.LEFT);
        self.__draw_pin("TMS", x0+210, y0-800, DrawingPin.PinOrientation.LEFT);
        self.__draw_pin("TRSTB", x0+210, y0-900, DrawingPin.PinOrientation.LEFT);

        # draw the outline
        rect = DrawingRectangle(start={'x':-x0, 'y':-y0}, end={'x':x0, 'y':y0}, unit_idx=self.cur_unit, fill=ElementFill.FILL_BACKGROUND)
        self.append(rect)
        # draw the bank text
        bnk_txt = DrawingText(at=Point({'x':0, 'y':y0-200}), text="BANK "+str(bank), size=100, unit_idx=self.cur_unit)
        self.append(bnk_txt)

        ###############################################################################
        ##                             Bank 4                                        ##
        ###############################################################################
        bank = 4
        self.cur_unit = bank+1

        y0 = 600
        x0 = 700

        if DBG_LVL >= 1:
            print("Bank", bank, "left hand side creation:")

        y = y0-400
        for i in range(7):
            self.__draw_pin("MSSIO"+str(i)+"B4", -x0-210, y, DrawingPin.PinOrientation.RIGHT);
            y = y-100

        if DBG_LVL >= 1:
            print("Bank", bank, "right hand side creation:")

        y = y0-400
        for i in range(7):
            self.__draw_pin("MSSIO"+str(i+7)+"B4", x0+210, y, DrawingPin.PinOrientation.LEFT);
            y = y-100

        # draw the outline
        rect = DrawingRectangle(start={'x':-x0, 'y':-y0}, end={'x':x0, 'y':y0}, unit_idx=self.cur_unit, fill=ElementFill.FILL_BACKGROUND)
        self.append(rect)
        # draw the bank text
        bnk_txt = DrawingText(at=Point({'x':0, 'y':y0-200}), text="BANK "+str(bank), size=100, unit_idx=self.cur_unit)
        self.append(bnk_txt)

        ###############################################################################
        ##                             Bank 5 SGMII                                  ##
        ###############################################################################
        bank = 5
        self.cur_unit = bank+1

        y0 = 700
        x0 = 700

        if DBG_LVL >= 1:
            print("Bank", bank,"left hand side creation:")

        self.__draw_pin("MSS_SGMII_TXN1", -x0-210, y0-400, DrawingPin.PinOrientation.RIGHT);
        self.__draw_pin("MSS_SGMII_TXP1", -x0-210, y0-500, DrawingPin.PinOrientation.RIGHT);
        self.__draw_pin("MSS_SGMII_RXN1", -x0-210, y0-700, DrawingPin.PinOrientation.RIGHT);
        self.__draw_pin("MSS_SGMII_RXP1", -x0-210, y0-800, DrawingPin.PinOrientation.RIGHT);

        if DBG_LVL >= 1:
            print("Bank", bank,"right hand side creation:")

        self.__draw_pin("MSS_SGMII_TXN0", x0+210, y0-400, DrawingPin.PinOrientation.LEFT);
        self.__draw_pin("MSS_SGMII_TXP0", x0+210, y0-500, DrawingPin.PinOrientation.LEFT);
        self.__draw_pin("MSS_SGMII_RXN0", x0+210, y0-700, DrawingPin.PinOrientation.LEFT);
        self.__draw_pin("MSS_SGMII_RXP0", x0+210, y0-800, DrawingPin.PinOrientation.LEFT);
        self.__draw_pin("MSS_REFCLK_IN_N", x0+210, y0-1000, DrawingPin.PinOrientation.LEFT);
        self.__draw_pin("MSS_REFCLK_IN_P", x0+210, y0-1100, DrawingPin.PinOrientation.LEFT);

        # draw the outline
        rect = DrawingRectangle(start={'x':-x0, 'y':-y0}, end={'x':x0, 'y':y0}, unit_idx=self.cur_unit, fill=ElementFill.FILL_BACKGROUND)
        self.append(rect)
        # draw the bank text
        bnk_txt = DrawingText(at=Point({'x':0, 'y':y0-200}), text="BANK "+str(bank), size=100, unit_idx=self.cur_unit)
        self.append(bnk_txt)


        ###############################################################################
        ##                             Bank 6 DDR4                                   ##
        ###############################################################################
        bank = 6
        self.cur_unit = bank+1
        y0 = round(((8+7)*5-4)/2+2)*100
        y = y0-400
        x0 = 1200

        dq = 0

        if(self.pkg == 'FCSG325'):
            number_8_pin_dq_groups = 2
        else:
            number_8_pin_dq_groups = 5

        if DBG_LVL >= 1:
            print("Bank", bank,"left hand side creation:")

        for i in range(number_8_pin_dq_groups):
            for j in range(8):
                self.__draw_pin("MSS_DDR_DQ"+str(dq), -x0-210, y, DrawingPin.PinOrientation.RIGHT);
                y = y-100

                if(dq >= 35):
                    break
                dq = dq+1

            y = y-100
            self.__draw_pin("MSS_DDR_DQS_N"+str(i), -x0-210, y, DrawingPin.PinOrientation.RIGHT);
            y = y-100
            self.__draw_pin("MSS_DDR_DQS_P"+str(i), -x0-210, y, DrawingPin.PinOrientation.RIGHT);
            y = y-200
            self.__draw_pin("MSS_DDR_DM"+str(i), -x0-210, y, DrawingPin.PinOrientation.RIGHT);
            y = y-300 # skip two before next group

        if DBG_LVL >= 1:
            print("Bank 6, right hand side creation:")

        y = y0-400
        for i in range(17):
            self.__draw_pin("MSS_DDR_A"+str(i), x0+210, y, DrawingPin.PinOrientation.LEFT);
            y = y-100

        # Misc DDR pins
        y = y-200
        self.__draw_pin("MSS_DDR_RAM_RST_N/DDR_PLL0_OUT1", x0+210, y, DrawingPin.PinOrientation.LEFT);
        y = y-200

        self.__draw_pin("MSS_DDR_CS0", x0+210, y, DrawingPin.PinOrientation.LEFT);
        y = y-100

        if(self.pkg != 'FCSG325'):
            self.__draw_pin("MSS_DDR_CS1", x0+210, y, DrawingPin.PinOrientation.LEFT);
            y = y-200

        self.__draw_pin("MSS_DDR_CKE0", x0+210, y, DrawingPin.PinOrientation.LEFT);
        y = y-100

        if(self.pkg != 'FCSG325'):
            self.__draw_pin("MSS_DDR_CKE1", x0+210, y, DrawingPin.PinOrientation.LEFT);
            y = y-200

        self.__draw_pin("MSS_DDR_ACT_N", x0+210, y, DrawingPin.PinOrientation.LEFT);
        y = y-200

        self.__draw_pin("MSS_DDR_BG0", x0+210, y, DrawingPin.PinOrientation.LEFT);
        y = y-100
        self.__draw_pin("MSS_DDR_BG1", x0+210, y, DrawingPin.PinOrientation.LEFT);
        y = y-200

        self.__draw_pin("MSS_DDR_BA0", x0+210, y, DrawingPin.PinOrientation.LEFT);
        y = y-100
        self.__draw_pin("MSS_DDR_BA1", x0+210, y, DrawingPin.PinOrientation.LEFT);
        y = y-200

        self.__draw_pin("MSS_DDR3_WE_N", x0+210, y, DrawingPin.PinOrientation.LEFT);
        y = y-200

        self.__draw_pin("MSS_DDR_CK0/DDR_PLL0_OUT0", x0+210, y, DrawingPin.PinOrientation.LEFT);
        y = y-100
        self.__draw_pin("MSS_DDR_CK_N0", x0+210, y, DrawingPin.PinOrientation.LEFT);
        y = y-200

        if(self.pkg != 'FCSG325'):
            self.__draw_pin("MSS_DDR_CK1/DDR_PLL0_OUT0", x0+210, y, DrawingPin.PinOrientation.LEFT);
            y = y-100
            self.__draw_pin("MSS_DDR_CK_N1", x0+210, y, DrawingPin.PinOrientation.LEFT);
            y = y-200

        self.__draw_pin("MSS_DDR_PARITY", x0+210, y, DrawingPin.PinOrientation.LEFT);
        y = y-200

        self.__draw_pin("MSS_DDR_ODT0", x0+210, y, DrawingPin.PinOrientation.LEFT);
        y = y-100

        if(self.pkg != 'FCSG325'):
            self.__draw_pin("MSS_DDR_ODT1", x0+210, y, DrawingPin.PinOrientation.LEFT);
            y = y-200

        self.__draw_pin("MSS_DDR_ALERT_N", x0+210, y, DrawingPin.PinOrientation.LEFT);
        y = y-200

        self.__draw_pin("MSS_DDR_VREF_IN", x0+210, y, DrawingPin.PinOrientation.LEFT);
        y = y-200

        # draw the outline
        rect = DrawingRectangle(start={'x':-x0, 'y':-y0}, end={'x':x0, 'y':y0}, unit_idx=self.cur_unit, fill=ElementFill.FILL_BACKGROUND)
        self.append(rect)
        # draw the bank text
        bnk_txt = DrawingText(at=Point({'x':0, 'y':y0-200}), text="BANK "+str(bank), size=100, unit_idx=self.cur_unit)
        self.append(bnk_txt)

        ###############################################################################
        ##                             Bank 7-9                                      ##
        ##               These may be ther in the larger packages                    ##
        ###############################################################################
        for bank in range(7,maxBnk+1):

            if DBG_LVL >= 1:
                print("going through extra Bank", bank)

            self.cur_unit = bank+1
            # first get a count of all Bank 0 HSIO
            count = 0
            for row in self.sh.rows:
                # quick check of the pad name to see if it has a digit
                pin = str(row[self.idx_name].value)
                testStr = pin[0:len(ioType)]
                if row[self.idx_bank].value == bank and \
                (testStr == "GPIO" or
                    testStr == "HSIO"):

                    count = count + 1

            self.cur_unit = bank+1

            if DBG_LVL >= 1:
                print("There are", count, "Bank", bank, "pins")


            # count x 1.5, because it's groups of 2 then a skip
            # first /2 for 2 sides second /2 for y0 being +/-
            y0 = round((count*1.5+4+6)/2/2)*100
            x0 = 1900

            if count%2 != 0:
                print(ioType, "count is not even, exiting")
                exit(1)

            if DBG_LVL >= 1:
                print("Bank", bank, " creation:")

            y = y0-400
            i = 0
            for row in self.sh.rows:
                # quick check of the pad name to see if it has a digit
                pin = str(row[self.idx_name].value)
                testStr = pin[0:len(ioType)]
                if row[self.idx_bank].value == bank and \
                (testStr == "GPIO" or
                    testStr == "HSIO"):
                    if i < count/2:
                        pin_dir = DrawingPin.PinOrientation.RIGHT
                        xLoc = -x0-210
                    else:
                        pin_dir = DrawingPin.PinOrientation.LEFT
                        xLoc = x0+210
                    row[self.idx_used].value = "1"
                    #print(pin+" "+row[self.idx_name].value)
                    self.append(DrawingPin(at=Point({'x':xLoc, 'y':y}, grid=100),
                                                                number=str(row[self.idx_pad].value), unit_idx=self.cur_unit,
                                                                orientation = pin_dir,
                                                                el_type = self.el_type[row[self.idx_dir].value],
                                                                name = pin,
                                                                pin_length = 200))
                    # on the even numbers skip 2 on the odds just skip 1
                    y = y-100-(i%2)*100
                    # reset back to the top for the second side
                    if i == count/2-1:
                        y = y0-400
                    i = i+1

            # draw the outline
            rect = DrawingRectangle(start={'x':-x0, 'y':-y0}, end={'x':x0, 'y':y0}, unit_idx=self.cur_unit, fill=ElementFill.FILL_BACKGROUND)
            self.append(rect)
            # draw the bank text
            bnk_txt = DrawingText(at=Point({'x':0, 'y':y0-200}), text="BANK "+str(bank), size=100, unit_idx=self.cur_unit)
            self.append(bnk_txt)

        ###############################################################################
        ##                               XCVR                                        ##
        ###############################################################################
        bank = maxBnk+1
        self.cur_unit = bank+1

        # not the prettiest way to count xcvr groups, but it works
        ioType = "XCVR"
        count = 0
        for row in self.sh.rows:
            # quick check of the pad name to see if it has a digit
            pin = str(row[self.idx_name].value)
            testStr = pin[0:len(ioType)]
            if testStr == ioType:
                count = count + 1
                #print(pin)

        # not perfect for the 1152 package because it's missing a refclk
        # but the round catches it
        xcvrGrps = round((count-2)/22)
        #print("count", count)

        if DBG_LVL >= 1:
            print("There are", xcvrGrps, "XCVR groups")

        y0 = round((xcvrGrps*20+4)/2)*100
        x0 = 900

        if DBG_LVL >= 1:
            print("XCVR left hand side creation:")

        y = y0-400
        for i in range(xcvrGrps):
            for j in range(4):
                if(not (self.pkg == 'FCSG325' and (j==1 or j==3))):
                    self.__draw_pin("XCVR_"+str(i)+"_TX"+str(j)+"_N", -x0-210, y, DrawingPin.PinOrientation.RIGHT);
                    y = y-100
                    self.__draw_pin("XCVR_"+str(i)+"_TX"+str(j)+"_P", -x0-210, y, DrawingPin.PinOrientation.RIGHT);
                    y = y-200
            y = y-100
            self.__draw_pin("XCVR_"+str(i)+"A_REFCLK_P", -x0-210, y, DrawingPin.PinOrientation.RIGHT);
            y = y-100
            self.__draw_pin("XCVR_"+str(i)+"A_REFCLK_N", -x0-210, y, DrawingPin.PinOrientation.RIGHT);
            y = y-200
            # Special case 1152 package does not have C refclk group for xcvr 4
            if (i != 4 and self.pkg != 'FCSG325'):
                self.__draw_pin("XCVR_"+str(i)+"C_REFCLK_P", -x0-210, y, DrawingPin.PinOrientation.RIGHT);
                y = y-100
                self.__draw_pin("XCVR_"+str(i)+"C_REFCLK_N", -x0-210, y, DrawingPin.PinOrientation.RIGHT);
            else:
                y = y-100
            y = y-300

        if DBG_LVL >= 1:
            print("XCVR right hand side creation:")

        y = y0-400
        for i in range(xcvrGrps):
            for j in range(4):
                if(not (self.pkg == 'FCSG325' and (j==1 or j==3))):
                    self.__draw_pin("XCVR_"+str(i)+"_RX"+str(j)+"_N", x0+210, y, DrawingPin.PinOrientation.LEFT);
                    y = y-100
                    self.__draw_pin("XCVR_"+str(i)+"_RX"+str(j)+"_P", x0+210, y, DrawingPin.PinOrientation.LEFT);
                    y = y-200
            y = y-100
            # Special case 1152 package does not have B refclk group for xcvr 3
            if i != 3:
                self.__draw_pin("XCVR_"+str(i)+"B_REFCLK_P", x0+210, y, DrawingPin.PinOrientation.LEFT);
                y = y-100
                self.__draw_pin("XCVR_"+str(i)+"B_REFCLK_N", x0+210, y, DrawingPin.PinOrientation.LEFT);
            else:
                y = y-100
            y = y-600

        # draw the outline
        rect = DrawingRectangle(start={'x':-x0, 'y':-y0}, end={'x':x0, 'y':y0}, unit_idx=self.cur_unit, fill=ElementFill.FILL_BACKGROUND)
        self.append(rect)
        # draw the bank text
        bnk_txt = DrawingText(at=Point({'x':0, 'y':y0-200}), text="XCVR", size=100, unit_idx=self.cur_unit)
        self.append(bnk_txt)

        ###############################################################################
        ##                               VSS                                         ##
        ###############################################################################
        bank = maxBnk+2
        self.cur_unit = bank+1

        y0 = 1000
        x0 = 700

        if DBG_LVL >= 1:
            print("Power left hand side creation:")

        self.__draw_group_by_name("VDD", -x0-210, y0-400, DrawingPin.PinOrientation.RIGHT)
        self.__draw_group_by_name("VDD18", -x0-210, y0-500, DrawingPin.PinOrientation.RIGHT)
        self.__draw_group_by_name("VDD25", -x0-210, y0-600, DrawingPin.PinOrientation.RIGHT)
        self.__draw_group_by_name("VDDA", -x0-210, y0-700, DrawingPin.PinOrientation.RIGHT)
        self.__draw_group_by_name("VDDA25", -x0-210, y0-800, DrawingPin.PinOrientation.RIGHT)
        self.__draw_group_by_name("VDDAUX1", -x0-210, y0-900, DrawingPin.PinOrientation.RIGHT)
        self.__draw_group_by_name("VDDAUX2", -x0-210, y0-1000, DrawingPin.PinOrientation.RIGHT)
        self.__draw_group_by_name("VDDAUX4", -x0-210, y0-1100, DrawingPin.PinOrientation.RIGHT)
        y = y0-1200
        if maxBnk>6:
            self.__draw_group_by_name("VDDAUX7", -x0-210, y, DrawingPin.PinOrientation.RIGHT)
            y = y-100
        if maxBnk>8:
            self.__draw_group_by_name("VDDAUX9", -x0-210, y, DrawingPin.PinOrientation.RIGHT)
            y = y-100
        self.__draw_group_by_name("VSS", -x0-210, y, DrawingPin.PinOrientation.RIGHT)

        if DBG_LVL >= 1:
            print("Power right hand side creation:")

        # The spreadsheet is mis-named with VDDI0 instead of VDDIO0, so match that here
        self.__draw_group_by_name("VDDI0", x0+210, y0-400, DrawingPin.PinOrientation.LEFT)
        self.__draw_group_by_name("VDDI1", x0+210, y0-500, DrawingPin.PinOrientation.LEFT)
        self.__draw_group_by_name("VDDI2", x0+210, y0-600, DrawingPin.PinOrientation.LEFT)
        self.__draw_group_by_name("VDDI3", x0+210, y0-700, DrawingPin.PinOrientation.LEFT)
        self.__draw_group_by_name("VDDI4", x0+210, y0-800, DrawingPin.PinOrientation.LEFT)
        self.__draw_group_by_name("VDDI5", x0+210, y0-900, DrawingPin.PinOrientation.LEFT)
        self.__draw_group_by_name("VDDI6", x0+210, y0-1000, DrawingPin.PinOrientation.LEFT)
        y = y0-1100
        for i in range(7,maxBnk+1):
            self.__draw_group_by_name("VDDI"+str(i), x0+210, y, DrawingPin.PinOrientation.LEFT)
            y = y-100

        y = y-100
        self.__draw_group_by_name("VDD_XCVR_CLK", x0+210, y, DrawingPin.PinOrientation.LEFT)
        y = y-100
        self.__draw_group_by_name("XCVR_VREF", x0+210, y, DrawingPin.PinOrientation.LEFT)

        # draw the outline
        rect = DrawingRectangle(start={'x':-x0, 'y':-y0}, end={'x':x0, 'y':y0}, unit_idx=self.cur_unit, fill=ElementFill.FILL_BACKGROUND)
        self.append(rect)
        # draw the bank text
        bnk_txt = DrawingText(at=Point({'x':0, 'y':y0-200}), text="POWER", size=100, unit_idx=self.cur_unit)
        self.append(bnk_txt)

        ###############################################################################
        ##                             NC PINs                                       ##
        ## The spreadsheets says:                                                    ##
        ##   No Connection - No connection to die. These pins can be used for board  ##
        ##   level signal routing by the designer if needed when migrating designs   ##
        ##   to larger devices in the same package.                                  ##
        ###############################################################################
        if NC_count>0:
            bank = maxBnk+3
            self.cur_unit = bank+1

            ioType = "NC"
            NC_count = 0
            for row in self.sh.rows:
                # quick check of the pad name to see if it has a digit
                s = str(row[self.idx_pad].value)
                found_dig = False
                for i, c in enumerate(s):
                    if c.isdigit():
                        found_dig = True
                        break
                if found_dig:
                    pin = str(row[self.idx_name].value)
                    testStr = pin[0:len(ioType)]
                    if testStr == ioType:
                        NC_count = NC_count + 1

            print("There are", NC_count, ioType, "pins")

            # first /2 for 2 sides second /2 for y0 being +/-
            y0 = round((NC_count+4+6)/2/2)*100
            x0 = 300

            y = y0-400
            ii = 0

            for row in self.sh.rows:
                # quick check of the pad name to see if it has a digit
                s = str(row[self.idx_pad].value)
                found_dig = False
                for i, c in enumerate(s):
                    if c.isdigit():
                        found_dig = True
                        break
                if found_dig:
                    pin = str(row[self.idx_name].value)
                    testStr = pin[0:len(ioType)]
                    if testStr == ioType:
                        if row[self.idx_used].value == "1":
                            print("Already used", pin_name, ", exiting...")
                            exit(1)
                        row[self.idx_used].value = "1"
                        if ii < NC_count/2:
                            pin_dir = DrawingPin.PinOrientation.RIGHT
                            xLoc = -x0-210
                        else:
                            pin_dir = DrawingPin.PinOrientation.LEFT
                            xLoc = x0+210
                        self.append(DrawingPin(at=Point({'x':xLoc, 'y':y}, grid=100),
                                                                    number=str(row[self.idx_pad].value), unit_idx=self.cur_unit,
                                                                    orientation = pin_dir,
                                                                    el_type = DrawingPin.PinElectricalType.EL_TYPE_NC,
                                                                    visibility = DrawingPin.PinVisibility.INVISIBLE,
                                                                    name = pin,
                                                                    pin_length = 200))
                        # on the even numbers skip 2 on the odds just skip 1
                        y = y-100

                        # reset back to the top for the second side
                        if ii == NC_count/2-1:
                            y = y0-400
                        ii = ii+1

            # draw the outline
            rect = DrawingRectangle(start={'x':-x0, 'y':-y0}, end={'x':x0, 'y':y0}, unit_idx=self.cur_unit, fill=ElementFill.FILL_BACKGROUND)
            self.append(rect)
            # draw the bank text
            bnk_txt = DrawingText(at=Point({'x':0, 'y':y0-200}), text="NC Pins", size=100, unit_idx=self.cur_unit)
            self.append(bnk_txt)

        ###############################################################################
        ##                             Final check                                   ##
        ###############################################################################
        for row in self.sh.rows:
            # quick check of the pad name to see if it has a digit
            s = str(row[self.idx_pad].value)
            found_dig = False
            for i, c in enumerate(s):
                if c.isdigit():
                    found_dig = True
                    break
            if found_dig:
                if row[self.idx_used].value == "0":
                    print(row[self.idx_name].value, row[self.idx_pad].value)
                    print("Error, Row not matched! exiting...")
                    exit(1)

        print("")

    def get_KicadSymbol(self):
        name = self.pn+'-'+self.pkg
        libname = "SoC_PolarFire"
        description = "RISC-V System On Chip (SOC) IC PolarFire FPGA"
        datasheet = "https://ww1.microchip.com/downloads/aemDocuments/documents/FPGA/ProductDocuments/DataSheets/PolarFire+SoC+Datasheet.pdf"
        keywords = "SoC RISC-V RISCV RV64GC FPGA"

        packageDictionary = {
            "FCSG325": "Package_BGA:FCSG325_11x11mm_Layout21x21_P0.5mm",
            "FCVG484": "Package_BGA:FCVG484_19x19mm_Layout22x22_P0.8mm",
            "FCSG536": "Package_BGA:FCSG536_16x16mm_Layout30x30_P0.5mm",
            "FCVG784": "Package_BGA:FCVG784_23x23mm_Layout28x28_P0.8mm",
            "FCG1152": "Package_BGA:FCG1152_35x35mm_Layout34x34_P1.0mm"
        }
        packageFilterDictionary = {
            "FCSG325": "Package?BGA:FCSG325?11x11mm?Layout21x21?P0.5mm*",
            "FCVG484": "Package?BGA:FCVG484?19x19mm?Layout22x22?P0.8mm*",
            "FCSG536": "Package?BGA:FCSG536?16x16mm?Layout30x30?P0.5mm*",
            "FCVG784": "Package?BGA:FCVG784?23x23mm?Layout28x28?P0.8mm*",
            "FCG1152": "Package?BGA:FCG1152?35x35mm?Layout34x34?P1.0mm*"
        }

        kicad_symbol = KicadSymbol.new(name=name,
                                       libname=libname,
                                       description=description,
                                       keywords=keywords,
                                       datasheet=datasheet,
                                       reference = "U",
                                       footprint = packageDictionary[self.pkg],
                                       fp_filters = packageFilterDictionary[self.pkg])
        self.appendToSymbol(kicad_symbol)
        return(kicad_symbol)


if __name__ == '__main__':
    # These should be lists to match the Excel sheets available in the directory
    # Each row represents one Excel file
    pns_pkgs =  [['MPFS025T', 'FCSG325'],
                 ['MPFS025T', 'FCVG484'],
                 ['MPFS095T', 'FCVG484'],
                 ['MPFS095T', 'FCSG536'],
                 ['MPFS095T', 'FCVG784'],
                 ['MPFS160T', 'FCVG484'],
                 ['MPFS160T', 'FCSG536'],
                 ['MPFS160T', 'FCVG784'],
                 ['MPFS250T', 'FCVG484'],
                 ['MPFS250T', 'FCSG536'],
                 ['MPFS250T', 'FCVG784'],
                 ['MPFS250T', 'FCG1152'],
                 ['MPFS460T', 'FCG1152']]

    lib = KicadLibrary("SoC_PolarFire" + ".kicad_sym")

    for pn_pkg in pns_pkgs:
        drawing_symbol = PolarFireDrawing(pn_pkg[0], pn_pkg[1])
        lib.symbols.append(drawing_symbol.get_KicadSymbol())

    lib.write()
