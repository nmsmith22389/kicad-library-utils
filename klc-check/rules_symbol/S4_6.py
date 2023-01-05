import itertools
import re
from copy import deepcopy
from typing import List

import boundingbox
from kicad_sym import KicadSymbol, Pin, Point, Polyline
from rules_symbol.rule import KLCRule, pinString


class Rule(KLCRule):
    """Hidden pins"""

    # No-connect pins should be "N"
    NC_PINS = ["^nc$", "^dnc$", r"^n\.c\.$"]

    def __init__(self, component: KicadSymbol):
        super().__init__(component)

        self.invisible_errors: List[Pin] = []
        self.power_invisible_errors: List[Pin] = []
        self.type_errors: List[Pin] = []
        self.nc_outside_outline_errors: List[Pin] = []

    # check if a pin name fits within a list of possible pins (using regex testing)
    def test(self, pinName: str, nameList: List[str]) -> bool:
        for name in nameList:
            if re.search(name, pinName, flags=re.IGNORECASE) is not None:
                return True

        return False

    @staticmethod
    def point_on_polyline(polyline: Polyline, point: Point):
        def is_on(a: Point, b: Point, c: Point):
            "Return true iff point c intersects the line segment from a to b."
            # (or the degenerate case that all 3 points are coincident)
            return (collinear(a, b, c)
                    and (within(a.x, c.x, b.x) if a.x != b.x else
                         within(a.y, c.y, b.y)))

        def collinear(a: Point, b: Point, c: Point):
            "Return true iff a, b, and c all lie on the same line."
            return (b.x - a.x) * (c.y - a.y) == (c.x - a.x) * (b.y - a.y)

        def within(p, q, r):
            "Return true iff q is between p and r (inclusive)."
            return p <= q <= r or r <= q <= p

        for p1, p2 in itertools.pairwise(polyline.points):
            if is_on(p1, p2, point):
                return True
        return False

    @staticmethod
    def isLineOrthogonal(line: Polyline) -> bool:
        if len(line.points) != 2:
            return False

        if line.points[0].x == line.points[1].x:
            return True

        if line.points[0].y == line.points[1].y:
            return True

        return False

    def checkPins(self, pins: List[Pin], is_power: bool) -> bool:
        self.invisible_errors = []
        self.power_invisible_errors = []
        self.type_errors = []

        for pin in pins:
            name = pin.name.lower()
            etype = pin.etype

            # Check NC pins
            if self.test(name, self.NC_PINS) or etype == "no_connect":
                # NC pins should be of type no_connect
                if not etype == "no_connect":  # Not set to NC
                    self.type_errors.append(pin)

                # NC pins should be invisible
                if not pin.is_hidden:
                    self.invisible_errors.append(pin)

            # For non-power-symbols: check if power-pins are invisible
            if not is_power and etype == "power_in" and pin.is_hidden:
                self.power_invisible_errors.append(pin)

        self.checkPinPositions()

        if self.type_errors:
            self.error("NC pins are not correct pin-type:")

            for pin in self.type_errors:
                self.errorExtra(
                    "{pin} should be of type NOT CONNECTED, but is of type {pintype}".format(
                        pin=pinString(pin), pintype=pin.etype
                    )
                )

        if self.invisible_errors:
            self.warning("NC pins are VISIBLE (should be INVISIBLE):")

            for pin in self.invisible_errors:
                self.warningExtra(
                    "{pin} should be INVISIBLE".format(pin=pinString(pin))
                )

        if self.power_invisible_errors:
            self.error(
                "Power input pins must not be invisible unless used in power symbols."
            )

            for pin in self.power_invisible_errors:
                self.errorExtra(
                    "{pin} is of type power_in and invisible".format(pin=pinString(pin))
                )

        if self.nc_outside_outline_errors:
            self.error(
                "Hidden NC pins should lie on or within the symbol's "
                "outline to prevent unwanted connections."
            )

            for pin in self.nc_outside_outline_errors:
                self.errorExtra(
                    "{pin} is outside of symbol outline".format(pin=pinString(pin))
                )

        return (
            self.invisible_errors
            or self.type_errors
            or self.power_invisible_errors
            or self.nc_outside_outline_errors
        )

    def checkPinPositions(self):
        """
        NC pins should lie within or on the symbol border,
        report the ones that lie outside and could be accidentally connected
        """
        self.nc_outside_outline_errors: List[Pin] = []

        outline_box: boundingbox.BoundingBox

        for unit in range(1, self.component.unit_count + 1):
            unit_pins = [pin for pin in self.component.pins if (pin.unit in [unit, 0])]

            # No pins? Ignore check.
            if not unit_pins:
                continue

            # rectangles are very fast to check position for, so we check them first.
            bounding_boxes_points = [i.as_polyline().get_boundingbox() for i in self.component.rectangles]
            bounding_boxes_points.extend(r.get_boundingbox() for r in self.component.polylines if r.is_rectangle())

            # if an NC pin is on an orthogonal line, assume that it's meant to be there, and it's ok.
            bounding_boxes_points.extend(line.get_boundingbox() for line in self.component.polylines
                                         if len(line.points) == 2 and self.isLineOrthogonal(line))

            bounding_boxes = [boundingbox.BoundingBox(b[2], b[3], b[0], b[1]) for b in bounding_boxes_points]

            # we can also check if a pin is inside a closed polygon
            closed_shapes = [pl for pl in self.component.polylines if pl.is_closed()]

            # include polylines that aren't closed but have background fill,
            # they should be treated as closed -- must connect last and first points
            # must deepcopy the object so that we don't modify the underlying object
            filled_polylines = [deepcopy(pl) for pl in self.component.polylines if
                                not pl.is_closed()
                                and pl.fill_type == 'background']

            for poly in filled_polylines:
                poly.points.append(poly.points[0])

            closed_shapes.extend(filled_polylines)

            # remove closed polylines inside bounding boxes
            # TODO check for polylines inside of other polylines
            filled_shapes = []
            for shape in closed_shapes:
                surrounded = False
                for box in bounding_boxes:
                    for point in shape.points:
                        if not box.containsPoint(point.x, point.y):
                            break
                    else:
                        surrounded = True

                if not surrounded:
                    filled_shapes.append(shape)

            # remove any unfilled polylines inside boundingboxes, since boundingboxes are faster to check
            polyline_edges = []
            for poly in [pl for pl in self.component.polylines if
                         not pl.is_closed()
                         and pl.fill_type == 'none'
                         and len(pl.points) > 2]:

                surrounded = False
                for box in bounding_boxes:
                    for point in poly.points:
                        if not box.containsPoint(point.x, point.y):
                            break
                    else:
                        surrounded = True

                if not surrounded:
                    polyline_edges.append(poly)

            if bounding_boxes or filled_shapes or polyline_edges:
                for pin in unit_pins:
                    if pin.etype == "no_connect" and pin.is_hidden:
                        ok = False
                        # check if pin in inside bounding box
                        for box in bounding_boxes:
                            if box.containsPoint(pin.posx, pin.posy):
                                ok = True
                                break

                        # check if pin is inside filled polyline
                        if not ok:
                            for shape in filled_shapes:
                                if shape.point_is_inside(Point(pin.posx, pin.posy)):
                                    ok = True
                                    break
                                else:
                                    # sometimes hidden pins are *almost* within a polyline, like
                                    # with op-amp shapes. Adding a little leniency here helps
                                    # eliminate false positives
                                    expanded_point = [
                                        Point(pin.posx + 0.01, pin.posy + 0.01),
                                        Point(pin.posx - 0.01, pin.posy + 0.01),
                                        Point(pin.posx + 0.01, pin.posy - 0.01),
                                        Point(pin.posx - 0.01, pin.posy - 0.01),
                                        Point(pin.posx + 0.01, pin.posy),
                                        Point(pin.posx - 0.01, pin.posy),
                                        Point(pin.posx, pin.posy + 0.01),
                                        Point(pin.posx, pin.posy - 0.01),
                                    ]

                                    if any(shape.point_is_inside(p) for p in expanded_point):
                                        ok = True
                                        break

                        # check if pin is on diagonal polyline segment
                        if not ok:
                            for poly in polyline_edges:
                                if self.point_on_polyline(poly, Point(pin.posx, pin.posy)):
                                    ok = True
                                    break

                        if not ok:
                            self.nc_outside_outline_errors.append(pin)

    def check(self) -> bool:
        """
        Proceeds the checking of the rule.
        The following variables will be accessible after checking:
            * invisible_errors
            * power_invisible_errors
            * type_errors
            * nc_outside_outline_errors
        """

        # no need to check this for a derived symbols
        if self.component.extends is not None:
            return False

        fail = False

        if self.checkPins(self.component.pins, self.component.is_power):
            fail = True

        return fail

    def fix(self) -> None:
        """
        Proceeds the fixing of the rule, if possible.
        """

        self.info("Fixing...")

        for pin in self.invisible_errors:
            if not pin.is_hidden:
                pin.is_hidden = True
                self.info("Setting pin {n} to INVISIBLE".format(n=pin.number))

        for pin in self.type_errors:
            if not pin.etype == "no_connect":
                pin.etype = "no_connect"
                self.info("Changing pin {n} type to NO_CONNECT".format(n=pin.number))

        self.recheck()
