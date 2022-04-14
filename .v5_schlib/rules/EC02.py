from rules.rule import KLCRule, positionFormater


class Rule(KLCRule):
    """
    Create the methods check and fix to use with the kicad lib files.
    """

    def __init__(self, component):
        super(Rule, self).__init__(
            component, "Check part reference, name and footprint position and alignment"
        )

    def check(self):
        """
        Proceeds the checking of the rule.
        The following variables will be accessible after checking:
            * recommended_ref_pos
            * recommended_ref_alignment
            * recommended_name_pos
            * recommended_name_alignment
            * recommended_fp_pos
            * recommended_fp_alignment
            * fp_is_missing
        """

        # check if component has just one rectangle, if not, skip checking
        if len(self.component.draw["rectangles"]) != 1:
            return False

        top = max(
            int(self.component.draw["rectangles"][0]["starty"]),
            int(self.component.draw["rectangles"][0]["endy"]),
        )
        bottom = min(
            int(self.component.draw["rectangles"][0]["starty"]),
            int(self.component.draw["rectangles"][0]["endy"]),
        )

        # reference checking

        # If there is no pin in the top, the recommended position to ref is at top-center,
        # horizontally centered.
        if not self.component.filterPins(direction="D"):
            self.recommended_ref_pos = {"posx": 0, "posy": (top + 125)}
            self.recommended_ref_alignment = "C"

        # otherwise, the recommended is put it before the first pin x position, right-aligned
        else:
            x = (
                min([int(i["posx"]) for i in self.component.filterPins(direction="D")])
                - 100
            )
            self.recommended_ref_pos = {"posx": x, "posy": (top + 125)}
            self.recommended_ref_alignment = "R"

        # get the current reference infos and compare them to recommended ones
        pos = {
            "posx": int(self.component.fields[0]["posx"]),
            "posy": int(self.component.fields[0]["posy"]),
        }
        if pos != self.recommended_ref_pos:
            self.warning(
                "field: reference, {0}, recommended {1}".format(
                    positionFormater(pos), positionFormater(self.recommended_ref_pos)
                )
            )
        if self.component.fields[0]["htext_justify"] != self.recommended_ref_alignment:
            self.warning(
                "field: reference, justification {0}, recommended {1}".format(
                    self.component.fields[0]["htext_justify"],
                    self.recommended_ref_alignment,
                )
            )
        # Does vertical alignment matter too?
        # What about orientation checking?

        # name checking

        # If there is no pin in the top, the recommended position to name is at top-center,
        # horizontally centered.
        if not self.component.filterPins(direction="D"):
            self.recommended_name_pos = {"posx": 0, "posy": (top + 50)}
            self.recommended_name_alignment = "C"

        # otherwise, the recommended is put it before the first pin x position, right-aligned
        else:
            x = (
                min([int(i["posx"]) for i in self.component.filterPins(direction="D")])
                - 100
            )
            self.recommended_name_pos = {"posx": x, "posy": (top + 50)}
            self.recommended_name_alignment = "R"

        # get the current name infos and compare them to recommended ones
        pos = {
            "posx": int(self.component.fields[1]["posx"]),
            "posy": int(self.component.fields[1]["posy"]),
        }
        if pos != self.recommended_name_pos:
            self.warning(
                "field: name, {0}, recommended {1}".format(
                    positionFormater(pos), positionFormater(self.recommended_name_pos)
                )
            )
        if self.component.fields[1]["htext_justify"] != self.recommended_name_alignment:
            self.warning(
                "field: name, justification {0}, recommended {1}".format(
                    self.component.fields[1]["htext_justify"],
                    self.recommended_name_alignment,
                )
            )
        # footprint checking

        # If there is no pins in the bottom, the recommended position to footprint is at
        # bottom-center, horizontally centered.
        if not self.component.filterPins(direction="U"):
            self.recommended_fp_pos = {"posx": 0, "posy": (bottom - 50)}
            self.recommended_fp_alignment = "C"

        # otherwise, the recommended is put it after the last pin x position, left-aligned
        else:
            x = (
                max([int(i["posx"]) for i in self.component.filterPins(direction="U")])
                + 50
            )
            self.recommended_fp_pos = {"posx": x, "posy": (bottom - 50)}
            self.recommended_fp_alignment = "L"

        # get the current footprint infos and compare them to recommended ones
        self.fp_is_missing = False
        if len(self.component.fields) >= 3:
            pos = {
                "posx": int(self.component.fields[2]["posx"]),
                "posy": int(self.component.fields[2]["posy"]),
            }
            if pos != self.recommended_fp_pos:
                self.warning(
                    "field: footprint, {0}, recommended {1}".format(
                        positionFormater(pos), positionFormater(self.recommended_fp_pos)
                    )
                )
            if (
                self.component.fields[2]["htext_justify"]
                != self.recommended_fp_alignment
            ):
                self.warning(
                    "field: footprint, justification {0}, recommended {1}".format(
                        self.component.fields[2]["htext_justify"],
                        self.recommended_fp_alignment,
                    )
                )
        else:
            self.warning(
                "field: footprint is missing, please re-save symbol using KiCad"
            )
            self.fp_is_missing = True

        # This entire rule only generates a WARNING (won't fail a component, only display a
        # message).
        return False

    def fix(self):
        """
        Proceeds the fixing of the rule, if possible.
        """
        self.info("Fixing...")
        self.component.fields[0]["posx"] = str(self.recommended_ref_pos["posx"])
        self.component.fields[0]["posy"] = str(self.recommended_ref_pos["posy"])
        self.component.fields[0]["htext_justify"] = self.recommended_ref_alignment

        self.component.fields[1]["posx"] = str(self.recommended_name_pos["posx"])
        self.component.fields[1]["posy"] = str(self.recommended_name_pos["posy"])
        self.component.fields[1]["htext_justify"] = self.recommended_name_alignment

        if not self.fp_is_missing:
            self.component.fields[2]["posx"] = str(self.recommended_fp_pos["posx"])
            self.component.fields[2]["posy"] = str(self.recommended_fp_pos["posy"])
            self.component.fields[2]["htext_justify"] = self.recommended_fp_alignment

        self.recheck()
