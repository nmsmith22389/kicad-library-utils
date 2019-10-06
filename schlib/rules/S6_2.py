# -*- coding: utf-8 -*-

from rules.rule import *


class Rule(KLCRule):
    """
    Create the methods check and fix to use with the kicad lib files.
    """
    def __init__(self, component):
        super(Rule, self).__init__(component, 'Symbols contain the correct metadata and field values')

    def checkVisibility(self, field):
        return field['visibility'] == 'V'

    # return True if a field is empty else false
    def checkEmpty(self, field):
        if 'name' in field.keys():
            name = field['name']
            if name and name not in ['""', "''"] and len(name) > 0:
                return False
        return True

    def checkReference(self):

        fail = False

        ref = self.component.fields[0]

        if (not self.component.isGraphicSymbol()) and (not self.component.isPowerSymbol()):
            if not self.checkVisibility(ref):
                self.error("Ref(erence) field must be VISIBLE")
                fail = True
        else:
            if self.checkVisibility(ref):
                self.error("Ref(erence) field must be INVISIBLE in graphic symbols or power-symbols")
                fail = True

        return fail

    def checkValue(self):
        fail = False

        value = self.component.fields[1]

        name = value['name']

        if name.startswith('"') and name.endswith('"'):
            name = name[1:-1]

        if (not self.component.isGraphicSymbol()) and (not self.component.isPowerSymbol()):
            if not name == self.component.name:
                self.error("Value {val} does not match component name.".format(val=name))
                fail = True
            # name field must be visible!
            if not self.checkVisibility(value):
                self.error("Value field must be VISIBLE")
                fail = True
        else:
            if (not ('~'+name) == self.component.name) and (not name == self.component.name):
                self.error("Value {val} does not match component name.".format(val=name))
                fail = True

        if not isValidName(self.component.name, self.component.isGraphicSymbol(), self.component.isPowerSymbol()):
            self.error("Symbol name '{val}' contains invalid characters as per KLC 1.7".format(
                val=self.component.name))
            fail = True

        return fail

    def checkFootprint(self):
        # Footprint field must be invisible
        fail = False

        fp = self.component.fields[2]

        if self.checkVisibility(fp):
            self.error("Footprint field must be INVISIBLE")
            fail = True

        return fail

    def checkDatasheet(self):

        # Datasheet field must be invisible
        fail = False

        ds = self.component.fields[3]

        if self.checkVisibility(ds):
            self.error("Datasheet field must be INVISIBLE")
            fail = True

        # Datasheet field must be empty
        if not self.checkEmpty(ds):
            self.error("Datasheet field (.lib file) must be EMPTY")
            fail = True

        return fail

    def checkDocumentation(self, name, documentation, alias=False, isGraphicOrPowerSymbol=False):

        errors = []
        warnings = []

        if not documentation:
            errors.append("Missing all metadata information in the .dcm file (datasheet, keyword and description)")
        elif (not documentation['description'] or
            not documentation['keywords'] or
            not documentation['datasheet']):

            if (not documentation['description']):
                errors.append("Missing DESCRIPTION entry (in dcm file)")
            if (not documentation['keywords']):
                errors.append("Missing KEYWORDS entry (in dcm file)")
            if (not isGraphicOrPowerSymbol) and (not documentation['datasheet']):
                errors.append("Missing DATASHEET entry (in dcm file)")

                if (documentation['description'] and
                    documentation['keywords']):
                    self.only_datasheet_missing = True

        # Symbol name should not appear in the description
        desc = documentation.get('description', '')
        if desc and name.lower() in desc.lower():
            warnings.append("Symbol name should not be included in description")

        # Datasheet field should look like a a datasheet
        ds = documentation.get('datasheet', '')

        if ds and len(ds) > 2:
            link = False
            links = ['http', 'www', 'ftp']
            if any([ds.startswith(i) for i in links]):
                link = True
            elif ds.endswith('.pdf') or '.htm' in ds:
                link = True

            if not link:
                warnings.append("Datasheet entry '{ds}' does not look like a URL".format(ds=ds))

        if len(errors) > 0 or len(warnings) > 0:
            msg = "{cmp} {name} has metadata errors:".format(
                cmp="ALIAS" if alias else "Component",
                name=name)
            if len(errors) == 0:
                self.warning(msg)
            else:
                self.error(msg)

            for err in errors:
                self.errorExtra(err)
            for warn in warnings:
                self.warningExtra(warn)

        return len(errors) > 0

    def check_lib_file(self):

        # Check for required fields
        n = len(self.component.fields)
        if n < 4:
            self.error("Component does not have minimum required fields!")

            if n < 1:
                self.errorExtra(" - Missing REFERENCE field")

            if n < 2:
                self.errorExtra(" - Missing VALUE field")

            if n < 3:
                self.errorExtra(" - Missing FOOTPRINT field")

            if n < 4:
                self.errorExtra(" - Missing DATASHEET field")

            return True

        # Check for extra fields!
        extraFields = False

        if n > 4:
            extraFields = True
            self.error("Component contains extra fields after DATASHEET field")

        return any([
            self.checkReference(),
            self.checkValue(),
            self.checkFootprint(),
            self.checkDatasheet(),
            extraFields
            ])

    def check_dcm_file(self):
        """
        Proceeds the checking of the rule.
        The following variables will be accessible after checking:
            * only_datasheet_missing
        """

        self.only_datasheet_missing = False
        invalid_documentation = 0

        # check part itself
        if self.checkDocumentation(self.component.name, self.component.documentation, False, self.component.isGraphicSymbol() or self.component.isPowerSymbol()):
            invalid_documentation += 1

        # check all its aliases too
        if self.component.aliases:
            invalid = []
            for alias in self.component.aliases.keys():
                if self.checkDocumentation(alias, self.component.aliases[alias], True, self.component.isGraphicSymbol() or self.component.isPowerSymbol()):
                    invalid_documentation += 1

        return invalid_documentation > 0

    def check(self):
        lib_result = self.check_lib_file()
        dcm_result = self.check_dcm_file()

        return lib_result or dcm_result

    def fix(self):
        """
        Proceeds the fixing of the rule, if possible.
        """
        self.info("Fixing VALUE-field...")
        self.component.fields[1]['name'] = self.component.name
        # store datasheet field contents for later reuse
        if ((not self.component.documentation['datasheet']) or len(self.component.documentation['datasheet']) == 0) and (len(self.component.fields[3]['name']) > 2):
            ds = self.component.fields[3]['name']
            if ds[0] == '"' and ds[len(ds)-1] == '"':
                ds = ds[1:(len(ds)-1)]
            self.component.documentation['datasheet'] = ds
            self.info("Copying DATASHEET '{ds}' to DCM-file ...".format(ds=ds))

        self.info("Emptying DATASHEET-field ...")
        self.component.fields[3]['name'] = ""

        self.info("Setting default field visibilities ...")
        self.component.fields[0]['visibility'] = "V"
        self.component.fields[1]['visibility'] = "V"
        self.component.fields[2]['visibility'] = "I"
        self.component.fields[3]['visibility'] = "I"
        self.recheck()
