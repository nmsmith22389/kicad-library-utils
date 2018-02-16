#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import sys, os

common = os.path.abspath(os.path.join(sys.path[0], '..','common'))

if not common in sys.path:
    sys.path.append(common)

from schlib import *

from print_color import *
import re
from rules import __all__ as all_rules
from rules import *
from rules.rule import KLCRule
from rulebase import logError

#enable windows wildcards
from glob import glob


def checklib(libfiles,
        component=None,
        pattern=None,
        rule=None,
        fix=False,
        color=True,
        verbose=0,
        silent=False,
        log=None,
        warnings=True,
        footprints=None):
    printer = PrintColor(use_color = color)

    # Set verbosity globally
    verbosity = 0
    if verbose:
        verbosity = verbose

    KLCRule.verbosity = verbosity

    if rule is not None:
        selected_rules = rule.split(',')
    else:
        #ALL rules are used
        selected_rules = None

    rules = []

    for r in all_rules:
        r_name = r.replace('_', '.')
        if selected_rules == None or r_name in selected_rules:
            rules.append(globals()[r].Rule)

    #grab list of libfiles (even on windows!)
    libfiles_globbed = []

    if len(all_rules)<=0:
        printer.red("No rules selected for check!")
        return 1
    else:
        if (verbosity>2):
            printer.regular("checking rules:")
            for r in all_rules:
                printer.regular("  - "+str(r))
            printer.regular("")

    for libfile in libfiles:
        libfiles_globbed += glob(libfile)

    if len(libfiles_globbed) == 0:
        printer.red("File argument invalid: {f}".format(f=libfiles))
        return 1

    exit_code = 0

    for libfile in libfiles_globbed:
        lib = SchLib(libfile)

        # Remove .lib from end of name
        lib_name = os.path.basename(libfile)[:-4]

        n_components = 0

        # Print library name
        if len(libfiles_globbed) > 1:
            printer.purple('Library: %s' % libfile)

        n_allviolations=0

        for c in lib.components:

            #simple match
            match = True
            if component is not None:
                match = match and component.lower() == c.name.lower()

            #regular expression match
            if pattern is not None:
                match = match and re.search(pattern, c.name, flags=re.IGNORECASE)

            if not match: continue

            n_components += 1

            # check the rules
            n_violations = 0

            first = True

            for r in rules:
                r = r(c)

                r.footprints_dir = footprints

                if verbosity > 2:
                    printer.white("checking rule" + r.name)

                r.check()

                if not warnings and not r.hasErrors():
                    continue

                if r.hasOutput():
                    if first:
                        printer.green("Checking symbol '{sym}':".format(sym=c.name))
                        first = False

                    printer.yellow("Violating " + r.name, indentation=2)
                    r.processOutput(printer, verbosity, silent)

                # Specifically check for errors
                if r.hasErrors():
                    n_violations += r.errorCount

                    if log is not None:
                        logError(log, r.name, lib_name, c.name)

                    if fix:
                        r.fix()
                        r.processOutput(printer, verbosity, silent)
                        r.recheck()

            # No messages?
            if first:
                if not silent:
                    printer.green("Checking symbol '{sym}' - No errors".format(sym=c.name))

            # check the number of violations
            if n_violations > 0:
                exit_code += 1
            n_allviolations=n_allviolations+n_violations

        if fix and n_allviolations > 0:
            lib.save()
            printer.green("saved '{file}' with fixes for {n_violations} violations.".format(file=libfile, n_violations=n_allviolations))

    return exit_code

def checklib_command(args=None):
    parser = argparse.ArgumentParser(description='Checks KiCad library files (.lib) against KiCad Library Convention (KLC) rules. You can find the KLC at http://kicad-pcb.org/libraries/klc/')
    parser.add_argument('libfiles', nargs='+')
    parser.add_argument('-c', '--component', help='check only a specific component (implicitly verbose)', action='store')
    parser.add_argument('-p', '--pattern', help='Check multiple components by matching a regular expression', action='store')
    parser.add_argument('-r','--rule',help='Select a particular rule (or rules) to check against (default = all rules). Use comma separated values to select multiple rules. e.g. "-r 3.1,EC02"')
    parser.add_argument('--fix', help='fix the violations if possible', action='store_true')
    parser.add_argument('--nocolor', help='does not use colors to show the output', action='store_true')
    parser.add_argument('-v', '--verbose', help='Enable verbose output. -v shows brief information, -vv shows complete information', action='count')
    parser.add_argument('-s', '--silent', help='skip output for symbols passing all checks', action='store_true')
    parser.add_argument('-l', '--log', help='Path to JSON file to log error information')
    parser.add_argument('-w', '--nowarnings', help='Hide warnings (only show errors)', action='store_true')
    parser.add_argument('--footprints', help='Path to footprint libraries (.pretty dirs). Specify with e.g. "~/kicad/footprints/"')

    parsed_args = parser.parse_args(args)

    return checklib(libfiles=parsed_args.libfiles,
        component=parsed_args.component,
        pattern=parsed_args.pattern,
        rule=parsed_args.rule,
        fix=parsed_args.fix,
        color=not parsed_args.nocolor,
        verbose=parsed_args.verbose,
        silent=parsed_args.silent,
        log=parsed_args.log,
        warnings=not parsed_args.nowarnings,
        footprints=parsed_args.footprints)

if __name__ == "__main__":
    sys.exit(checklib_command())
