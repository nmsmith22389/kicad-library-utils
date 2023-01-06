"""
Library for dealing with bounding boxes (2D areas defined by four points).
"""

from typing import Dict, Optional
from math import pi, sqrt, atan2


class BoundingBox:
    def __init__(
        self,
        xmin: Optional[float] = None,
        ymin: Optional[float] = None,
        xmax: Optional[float] = None,
        ymax: Optional[float] = None,
    ):
        self.xmin: Optional[float] = None
        self.ymin: Optional[float] = None
        self.xmax: Optional[float] = None
        self.ymax: Optional[float] = None

        self.addPoint(xmin, ymin)
        self.addPoint(xmax, ymax)

    def checkMin(
        self, current: Optional[float], compare: Optional[float]
    ) -> Optional[float]:
        if current is None:
            return compare

        if compare is None:
            return current

        if compare < current:
            return compare

        return current

    def checkMax(
        self, current: Optional[float], compare: Optional[float]
    ) -> Optional[float]:
        if current is None:
            return compare

        if compare is None:
            return current

        if compare > current:
            return compare

        return current

    def addPoint(
        self, x: Optional[float], y: Optional[float], radius: float = 0.0
    ) -> None:
        # x might be 'None' so prevent subtraction
        self.xmin = self.checkMin(self.xmin, x - radius if x else x)
        self.xmax = self.checkMax(self.xmax, x + radius if x else x)

        # y might be 'None' so prevent subtraction
        self.ymin = self.checkMin(self.ymin, y - radius if y else y)
        self.ymax = self.checkMax(self.ymax, y + radius if y else y)

    def addArc(
        self, startx: float, starty: float, endx: float, endy: float, midx: float, midy: float
    ) -> None:
        # Start/end points of the arc are always in the bounding box
        self.addPoint(startx, starty)
        self.addPoint(endx, endy)

        # Convert to radius and angles, making sure that angles are positive
        radius = sqrt((startx-midx)**2 + (starty-midy)**2)
        startphi = atan2(starty-midy, startx-midx)
        if startphi < 0:
            startphi += 2*pi
        endphi = atan2(endy-midy, endx-midx)
        while endphi < startphi:
            endphi += 2*pi

        # Quadrants of the arc
        startquad = int(startphi // (pi/2))
        endquad = int(endphi // (pi/2))

        # For each quadrant change, add the point touching the next quadrant (clockwise)
        for q in [q % 4 for q in range(startquad, endquad)]:
            if q == 0:
                self.addPoint(midx, midy + radius)
            elif q == 1:
                self.addPoint(midx - radius, midy)
            elif q == 2:
                self.addPoint(midx, midy - radius)
            elif q == 3:
                self.addPoint(midx + radius, midy)

    def addBoundingBox(self, other: "BoundingBox") -> None:
        self.addPoint(other.xmin, other.ymin)
        self.addPoint(other.xmax, other.ymax)

    @property
    def valid(self) -> bool:
        return (
            self.xmin is not None
            and self.ymin is not None
            and self.xmax is not None
            and self.ymax is not None
        )

    def containsPoint(self, x: Optional[float], y: Optional[float]) -> bool:
        if not self.valid:
            return False

        if x < self.xmin or self.xmax < x:
            return False

        if y < self.ymin or self.ymax < y:
            return False

        return True

    def expand(self, distance: float) -> None:
        if not self.valid:
            return

        self.xmin -= distance
        self.ymin -= distance

        self.xmax += distance
        self.ymax += distance

    def overlaps(self, other: "BoundingBox") -> bool:
        return any(
            [
                self.containsPoint(other.xmin, other.ymin),
                self.containsPoint(other.xmin, other.ymax),
                self.containsPoint(other.xmax, other.ymax),
                self.containsPoint(other.xmax, other.ymin),
            ]
        )

    @property
    def x(self) -> Optional[float]:
        return self.xmin

    @property
    def y(self) -> Optional[float]:
        return self.ymin

    @property
    def width(self) -> float:
        if self.xmin is None or self.xmax is None:
            return 0.0

        return self.xmax - self.xmin

    @property
    def height(self) -> float:
        if self.ymin is None or self.ymax is None:
            return 0.0

        return self.ymax - self.ymin

    @property
    def size(self):
        return {"x": self.width, "y": self.height}

    @property
    def center(self) -> Dict[str, float]:
        if self.valid:
            return {"x": self.xmin + self.width / 2, "y": self.ymin + self.height / 2}
        else:
            return {"x": 0.0, "y": 0.0}


if __name__ == "__main__":
    bb1 = BoundingBox(-20, 50, 10, -20)
    bb2 = BoundingBox(-5, -5, 7, 21)

    bb3 = BoundingBox(2, 200)
    bb3.addPoint(3, 5)

    bb3.addBoundingBox(bb1)

    print(bb1.size)
    print(bb2.size)
    print(bb3.size)
