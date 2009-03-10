#!/usr/bin/env python

## 
 # -*-Pyth-*-
 # ###################################################################
 #  FiPy - Python-based finite volume PDE solver
 # 
 #  FILE: "mesh.py"
 #
 #  Author: Jonathan Guyer <guyer@nist.gov>
 #  Author: Daniel Wheeler <daniel.wheeler@nist.gov>
 #  Author: James Warren   <jwarren@nist.gov>
 #    mail: NIST
 #     www: http://www.ctcms.nist.gov/fipy/
 #  
 # ========================================================================
 # This software was developed at the National Institute of Standards
 # and Technology by employees of the Federal Government in the course
 # of their official duties.  Pursuant to title 17 Section 105 of the
 # United States Code this software is not subject to copyright
 # protection and is in the public domain.  FiPy is an experimental
 # system.  NIST assumes no responsibility whatsoever for its use by
 # other parties, and makes no guarantees, expressed or implied, about
 # its quality, reliability, or any other characteristic.  We would
 # appreciate acknowledgement if the software is used.
 # 
 # This software can be redistributed and/or modified freely
 # provided that any derivative works bear some notice that they are
 # derived from it, and any modified versions bear some notice that
 # they have been modified.
 # ========================================================================
 #  See the file "license.terms" for information on usage and  redistribution
 #  of this file, and for a DISCLAIMER OF ALL WARRANTIES.
 #  
 # ###################################################################
 ##

__docformat__ = 'restructuredtext'

from fipy.tools import numerix
from fipy.tools.numerix import MA

from fipy.tools.dimensions.physicalField import PhysicalField

class Mesh:
    """
    Generic mesh class defining implementation-agnostic behavior.

    Make changes to mesh here first, then implement specific implementations in
    `pyMesh` and `numMesh`.

    Meshes contain cells, faces, and vertices.
    """

    def __init__(self):
        self.scale = {
            'length': 1.,
            'area': 1.,
            'volume': 1.
        }
        
        self._calcTopology()
        self._calcGeometry()
    
    def __add__(self, other):
        """
        Either translate a `Mesh` or concatenate two `Mesh` objects.
        
            >>> from fipy.meshes.grid2D import Grid2D
            >>> baseMesh = Grid2D(dx = 1.0, dy = 1.0, nx = 2, ny = 2)
            >>> print baseMesh.getCellCenters()
            [[ 0.5  1.5  0.5  1.5]
             [ 0.5  0.5  1.5  1.5]]
             
        If a vector is added to a `Mesh`, a translated `Mesh` is returned
        
            >>> translatedMesh = baseMesh + ((5,), (10,))
            >>> print translatedMesh.getCellCenters()
            [[  5.5   6.5   5.5   6.5]
             [ 10.5  10.5  11.5  11.5]]

             
        If a `Mesh` is added to a `Mesh`, a concatenation of the two 
        `Mesh` objects is returned
        
            >>> addedMesh = baseMesh + (baseMesh + ((2,), (0,)))
            >>> print addedMesh.getCellCenters()
            [[ 0.5  1.5  0.5  1.5  2.5  3.5  2.5  3.5]
             [ 0.5  0.5  1.5  1.5  0.5  0.5  1.5  1.5]]
        
        The two `Mesh` objects must be properly aligned in order to concatenate them
        
            >>> addedMesh = baseMesh + (baseMesh + ((3,), (0,)))
            Traceback (most recent call last):
            ...
            MeshAdditionError: Vertices are not aligned

            >>> addedMesh = baseMesh + (baseMesh + ((2,), (2,)))
            Traceback (most recent call last):
            ...
            MeshAdditionError: Faces are not aligned

        No provision is made to avoid or consolidate overlapping `Mesh` objects
        
            >>> addedMesh = baseMesh + (baseMesh + ((1,), (0,)))
            >>> print addedMesh.getCellCenters()
            [[ 0.5  1.5  0.5  1.5  1.5  2.5  1.5  2.5]
             [ 0.5  0.5  1.5  1.5  0.5  0.5  1.5  1.5]]
            
        Different `Mesh` classes can be concatenated
         
            >>> from fipy.meshes.tri2D import Tri2D
            >>> triMesh = Tri2D(dx = 1.0, dy = 1.0, nx = 2, ny = 1)
            >>> triMesh = triMesh + ((2,), (0,))
            >>> triAddedMesh = baseMesh + triMesh
            >>> print triAddedMesh.getCellCenters()
            [[ 0.5         1.5         0.5         1.5         2.83333333  3.83333333
               2.5         3.5         2.16666667  3.16666667  2.5         3.5       ]
             [ 0.5         0.5         1.5         1.5         0.5         0.5
               0.83333333  0.83333333  0.5         0.5         0.16666667  0.16666667]]

        but their faces must still align properly
        
            >>> triMesh = Tri2D(dx = 1.0, dy = 2.0, nx = 2, ny = 1)
            >>> triMesh = triMesh + ((2,), (0,))
            >>> triAddedMesh = baseMesh + triMesh
            Traceback (most recent call last):
            ...
            MeshAdditionError: Faces are not aligned

        `Mesh` concatenation is not limited to 2D meshes
        
            >>> from fipy.meshes.grid3D import Grid3D
            >>> threeDBaseMesh = Grid3D(dx = 1.0, dy = 1.0, dz = 1.0, 
            ...                         nx = 2, ny = 2, nz = 2)
            >>> threeDSecondMesh = Grid3D(dx = 1.0, dy = 1.0, dz = 1.0, 
            ...                           nx = 1, ny = 1, nz = 1)
            >>> threeDAddedMesh = threeDBaseMesh + (threeDSecondMesh + ((2,), (0,), (0,)))
            >>> print threeDAddedMesh.getCellCenters()
            [[ 0.5  1.5  0.5  1.5  0.5  1.5  0.5  1.5  2.5]
             [ 0.5  0.5  1.5  1.5  0.5  0.5  1.5  1.5  0.5]
             [ 0.5  0.5  0.5  0.5  1.5  1.5  1.5  1.5  0.5]]

        but the different `Mesh` objects must, of course, have the same 
        dimensionality.
        
            >>> InvalidMesh = threeDBaseMesh + baseMesh
            Traceback (most recent call last):
            ...
            MeshAdditionError: Dimensions do not match
        """
        pass
        
    def __mul__(self, factor):
        """
        Dilate a `Mesh` by `factor`.
        
            >>> from fipy.meshes.grid2D import Grid2D
            >>> baseMesh = Grid2D(dx = 1.0, dy = 1.0, nx = 2, ny = 2)
            >>> print baseMesh.getCellCenters()
            [[ 0.5  1.5  0.5  1.5]
             [ 0.5  0.5  1.5  1.5]]

        The `factor` can be a scalar
        
            >>> dilatedMesh = baseMesh * 3
            >>> print dilatedMesh.getCellCenters()
            [[ 1.5  4.5  1.5  4.5]
             [ 1.5  1.5  4.5  4.5]]

        or a vector
        
            >>> dilatedMesh = baseMesh * ((3,), (2,))
            >>> print dilatedMesh.getCellCenters()
            [[ 1.5  4.5  1.5  4.5]
             [ 1.   1.   3.   3. ]]

        
        but the vector must have the same dimensionality as the `Mesh`
        
            >>> dilatedMesh = baseMesh * ((3,), (2,), (1,))
            Traceback (most recent call last):
            ...
            ValueError: shape mismatch: objects cannot be broadcast to a single shape
            
        """
        pass
        
    def __repr__(self):
        return "%s()" % self.__class__.__name__
        
    """topology methods"""
    
    def _calcTopology(self):
        self._calcInteriorAndExteriorFaceIDs()
        self._calcInteriorAndExteriorCellIDs()
        self._calcCellToFaceOrientations()
        self._calcAdjacentCellIDs()
        self._calcCellToCellIDs()
        self._calcCellToCellIDsFilled()
       
    """calc topology methods"""
        
    def _calcInteriorAndExteriorFaceIDs(self):
        pass

    def _calcExteriorCellIDs(self):
        pass
        
    def _calcInteriorCellIDs(self):
        pass
##      self.interiorCellIDs = list(sets.Set(range(self.numberOfCells)) - sets.Set(self.exteriorCellIDs))
##        onesWhereInterior = numerix.zeros(self.numberOfCells)
##        numerix.put(onesWhereInterior, self.exteriorCells, numerix.zeros((len(self.exteriorCellIDs))))
##        self.interiorCellIDs = numerix.nonzero(onesWhereInterior)
##        self.interiorCellIDs = (0,0)
        
    def _calcInteriorAndExteriorCellIDs(self):
        self._calcExteriorCellIDs()
        self._calcInteriorCellIDs()

    def _calcCellToFaceOrientations(self):
        pass

    def _calcAdjacentCellIDs(self):
        pass

    def _calcCellToCellIDs(self):
        pass

    def _calcCellToCellIDsFilled(self):
        N = self.getNumberOfCells()
        M = self._getMaxFacesPerCell()
        cellIDs = numerix.repeat(numerix.arange(N)[numerix.newaxis, ...], M, axis=0)
        cellToCellIDs = self._getCellToCellIDs()
        self.cellToCellIDsFilled = MA.where(MA.getmaskarray(cellToCellIDs), cellIDs, cellToCellIDs)

    
    """get topology methods"""

    def _getFaceVertexIDs(self):
        return self.faceVertexIDs

    def _getCellFaceIDs(self):
        return self.cellFaceIDs

    def _getNumberOfFacesPerCell(self):
        cellFaceIDs = self._getCellFaceIDs()
        if type(cellFaceIDs) is type(MA.array(0)):
            ## bug in count returns float values when there is no mask
            return numerix.array(cellFaceIDs.count(axis=0), 'l')
        else:
            return self._getMaxFacesPerCell() * numerix.ones(cellFaceIDs.shape[-1], 'l')

    def getExteriorFaces(self):
        pass

    def getInteriorFaces(self):
        pass
        
    def _getExteriorCellIDs(self):
        """ Why do we have this?!? It's only used for testing against itself? """
        return self.exteriorCellIDs

    def _getInteriorCellIDs(self):
        """ Why do we have this?!? It's only used for testing against itself? """
        return self.interiorCellIDs

    def _getCellFaceOrientations(self):
        return self.cellToFaceOrientations

    def getNumberOfCells(self):
        return self.numberOfCells

    def _isOrthogonal(self):
        return False
    
    def _getNumberOfVertices(self):
        if hasattr(self, 'numberOfVertices'):
            return self.numberOfVertices
        else:
            return len(self.vertexCoords[:,0])
        
    def _getAdjacentCellIDs(self):
        return self.adjacentCellIDs

    def getDim(self):
        return self.dim

    def _getCellsByID(self, ids = None):
        pass
            
    def getCells(self, ids=None):
        """
        Return `Cell` objects of `Mesh`.

           >>> from fipy import Grid2D
           >>> m = Grid2D(nx=2, ny=2)
           >>> x, y = m.getCellCenters()
           >>> print m.getCells()[x < 1]
           [Cell(mesh=UniformGrid2D(dx=1.0, dy=1.0, nx=2, ny=2), id=0)
            Cell(mesh=UniformGrid2D(dx=1.0, dy=1.0, nx=2, ny=2), id=2)]
           >>> print m.getCells(ids=(0, 2))
           [Cell(mesh=UniformGrid2D(dx=1.0, dy=1.0, nx=2, ny=2), id=0)
            Cell(mesh=UniformGrid2D(dx=1.0, dy=1.0, nx=2, ny=2), id=2)]

        """
        return self._getCellsByID(ids)
        
    def _getFaces(self):
        pass
    
    def getFaces(self):
        """
        Return `Face` objects of `Mesh`.

           >>> from fipy import Grid2D
           >>> m = Grid2D(nx=2, ny=2)
           >>> x, y = m.getFaceCenters()
           >>> print m.getFaces()[x < 1]
           [0 2 4 6 9]

        """
        from fipy.variables.faceVariable import FaceVariable
        return FaceVariable(mesh=self, value=self._getFaces())

    def getFacesLeft(self):
        """
        Return face on left boundary of Grid1D as list with the
        x-axis running from left to right.

            >>> from fipy import Grid2D, Grid3D
            >>> mesh = Grid3D(nx = 3, ny = 2, nz = 1, dx = 0.5, dy = 2., dz = 4.)
            >>> numerix.allequal((21, 25), 
            ...                  numerix.nonzero(mesh.getFacesLeft())[0])
            1
            >>> mesh = Grid2D(nx = 3, ny = 2, dx = 0.5, dy = 2.)        
            >>> numerix.allequal((9, 13), 
            ...                  numerix.nonzero(mesh.getFacesLeft())[0])
            1

        """
        x = self.getFaceCenters()[0]
        from fipy.variables.faceVariable import FaceVariable
        return FaceVariable(mesh=self, value=x == min(x))

    def getFacesRight(self):
        """
        Return list of faces on right boundary of Grid3D with the
        x-axis running from left to right. 

            >>> from fipy import Grid2D, Grid3D, numerix
            >>> mesh = Grid3D(nx = 3, ny = 2, nz = 1, dx = 0.5, dy = 2., dz = 4.)
            >>> numerix.allequal((24, 28), 
            ...                  numerix.nonzero(mesh.getFacesRight())[0])
            1
            >>> mesh = Grid2D(nx = 3, ny = 2, dx = 0.5, dy = 2.)        
            >>> numerix.allequal((12, 16), 
            ...                  numerix.nonzero(mesh.getFacesRight())[0])
            1
            
        """
        x = self.getFaceCenters()[0]        
        from fipy.variables.faceVariable import FaceVariable
        return FaceVariable(mesh=self, value=x == max(x))

    def getFacesBottom(self):
        """
        Return list of faces on bottom boundary of Grid3D with the
        y-axis running from bottom to top.

            >>> from fipy import Grid2D, Grid3D, numerix
            >>> mesh = Grid3D(nx = 3, ny = 2, nz = 1, dx = 0.5, dy = 2., dz = 4.)
            >>> numerix.allequal((12, 13, 14), 
            ...                  numerix.nonzero(mesh.getFacesBottom())[0])
            1
            >>> x, y, z = mesh.getFaceCenters()
            >>> numerix.allequal((12, 13), 
            ...                  numerix.nonzero(mesh.getFacesBottom() & (x < 1))[0])
            1
            
        """
        y = self.getFaceCenters()[1]        
        from fipy.variables.faceVariable import FaceVariable
        return FaceVariable(mesh=self, value=y == min(y))

    getFacesDown = getFacesBottom

    def getFacesTop(self):
        """
        Return list of faces on top boundary of Grid3D with the
        y-axis running from bottom to top.

            >>> from fipy import Grid2D, Grid3D, numerix
            >>> mesh = Grid3D(nx = 3, ny = 2, nz = 1, dx = 0.5, dy = 2., dz = 4.)
            >>> numerix.allequal((18, 19, 20), 
            ...                  numerix.nonzero(mesh.getFacesTop())[0])
            1
            >>> mesh = Grid2D(nx = 3, ny = 2, dx = 0.5, dy = 2.)        
            >>> numerix.allequal((6, 7, 8), 
            ...                  numerix.nonzero(mesh.getFacesTop())[0])
            1
            
        """
        y = self.getFaceCenters()[1]        
        from fipy.variables.faceVariable import FaceVariable
        return FaceVariable(mesh=self, value=y == max(y))

    getFacesUp = getFacesTop

    def getFacesBack(self):
        """
        Return list of faces on back boundary of Grid3D with the
        z-axis running from front to back. 

            >>> from fipy import Grid3D, numerix
            >>> mesh = Grid3D(nx = 3, ny = 2, nz = 1, dx = 0.5, dy = 2., dz = 4.)
            >>> numerix.allequal((6, 7, 8, 9, 10, 11), 
            ...                  numerix.nonzero(mesh.getFacesBack())[0])
            1

        """
        z = self.getFaceCenters()[2]        
        from fipy.variables.faceVariable import FaceVariable
        return FaceVariable(mesh=self, value=z == max(z))

    def getFacesFront(self):
        """
        Return list of faces on front boundary of Grid3D with the
        z-axis running from front to back. 

            >>> from fipy import Grid3D, numerix
            >>> mesh = Grid3D(nx = 3, ny = 2, nz = 1, dx = 0.5, dy = 2., dz = 4.)
            >>> numerix.allequal((0, 1, 2, 3, 4, 5), 
            ...                  numerix.nonzero(mesh.getFacesFront())[0])
            1

        """
        z = self.getFaceCenters()[2]        
        from fipy.variables.faceVariable import FaceVariable
        return FaceVariable(mesh=self, value=z == min(z))
    
    def _getMaxFacesPerCell(self):
        pass

    def _getNumberOfFaces(self):
        return self.numberOfFaces

    def _getCellToCellIDs(self):
        return self.cellToCellIDs

    def _getCellToCellIDsFilled(self):
        return self.cellToCellIDsFilled
        
    """geometry methods"""
    
    def _calcGeometry(self):
        self._calcFaceAreas()
        self._calcCellCenters()
        self._calcFaceToCellDistances()
        self._calcCellDistances()        
        self._calcFaceNormals()
        self._calcOrientedFaceNormals()
        self._calcCellVolumes()
        self._calcCellCenters()
        self._calcFaceCellToCellNormals()
        self._calcFaceToCellDistances()
        self._calcCellDistances()        
        self._calcFaceTangents()
        self._calcCellToCellDistances()
        self._calcScaledGeometry()
        self._calcCellAreas()
       
    """calc geometry methods"""
    
    def _calcFaceAreas(self):
        pass
        
    def _calcFaceNormals(self):
        pass
        
    def _calcOrientedFaceNormals(self):
        pass
        
    def _calcCellVolumes(self):
        pass
        
    def _calcCellCenters(self):
        pass
        
    def _calcFaceToCellDistances(self):
        pass

    def _calcCellDistances(self):
        pass
        
    def _calcAreaProjections(self):
        pass

    def _calcOrientedAreaProjections(self):
        pass

    def _calcFaceTangents(self):
        pass

    def _calcFaceToCellDistanceRatio(self):
        pass

    def _calcFaceAspectRatios(self):
        self.faceAspectRatios = self._getFaceAreas() / self._getCellDistances()

    def _calcCellToCellDistances(self):
        pass

    def _calcCellAreas(self):
        from fipy.tools.numerix import take
        self.cellAreas =  take(self._getFaceAreas(), self.cellFaceIDs)
    
    """get geometry methods"""
        
    def _getFaceAreas(self):
        return self.scaledFaceAreas

    def _getFaceNormals(self):
        return self.faceNormals

    def _getFaceCellToCellNormals(self):
        return self.faceCellToCellNormals
        
    def getCellVolumes(self):
        return self.scaledCellVolumes

    def getCellCenters(self):
        return self.scaledCellCenters

    def _getFaceToCellDistances(self):
        return self.scaledFaceToCellDistances

    def _getCellDistances(self):
        return self.scaledCellDistances

    def _getFaceToCellDistanceRatio(self):
        return self.faceToCellDistanceRatio

    def _getOrientedAreaProjections(self):
        return self.orientedAreaProjections

    def _getAreaProjections(self):
        return self.areaProjections

    def _getOrientedFaceNormals(self):
        return self.orientedFaceNormals

    def _getFaceTangents1(self):
        return self.faceTangents1

    def _getFaceTangents2(self):
        return self.faceTangents2
        
    def _getFaceAspectRatios(self):
        return self.faceAspectRatios
    
    def _getCellToCellDistances(self):
        return self.scaledCellToCellDistances

    def _getCellNormals(self):
        return self.cellNormals

    def _getCellAreas(self):
        return self.cellAreas

    def _getCellAreaProjections(self):
        return self.cellNormals * self._getCellAreas()

    """scaling"""

    def setScale(self, value = 1.):
        self.scale['length'] = PhysicalField(value = value)
        if self.scale['length'].getUnit().isDimensionless():
            self.scale['length'] = 1
        self._calcHigherOrderScalings()
        self._calcScaledGeometry()

    def _calcHigherOrderScalings(self):
        self.scale['area'] = self.scale['length']**2
        self.scale['volume'] = self.scale['length']**3

    def _calcScaledGeometry(self):
        self.scaledFaceAreas = self.scale['area'] * self.faceAreas
        self.scaledCellVolumes = self.scale['volume'] * self.cellVolumes
        self.scaledCellCenters = self.scale['length'] * self.cellCenters
        
        self.scaledFaceToCellDistances = self.scale['length'] * self.faceToCellDistances
        self.scaledCellDistances = self.scale['length'] * self.cellDistances
        self.scaledCellToCellDistances = self.scale['length'] * self.cellToCellDistances
        
        self._calcAreaProjections()
        self._calcOrientedAreaProjections()
        self._calcFaceToCellDistanceRatio()
        self._calcFaceAspectRatios()
        
    """point to cell distances"""
    
    def _getPointToCellDistances(self, point):
        tmp = self.getCellCenters() - PhysicalField(point)
        from fipy.tools import numerix
        return numerix.sqrtDot(tmp, tmp)

    def getNearestCell(self, point):
        return self._getCellsByID([self._getNearestCellID(point)])[0]

    def _getNearestCellID(self, points):
        """
        Test cases

           >>> from fipy import *
           >>> m0 = Grid2D(dx=(.1, 1., 10.), dy=(.1, 1., 10.))
           >>> m1 = Grid2D(nx=2, ny=2, dx=5., dy=5.)
           >>> print m0._getNearestCellID(m1.getCellCenters())
           [4 5 7 8]
           
        """
        points = numerix.resize(points, (self.getNumberOfCells(), len(points), len(points[0]))).swapaxes(0,1)

        try:
            tmp = self.getCellCenters()[...,numerix.newaxis] - points
        except TypeError:
            tmp = self.getCellCenters()[...,numerix.newaxis] - PhysicalField(points)

        return numerix.argmin(numerix.dot(tmp, tmp, axis = 0), axis=0)

## pickling

##    self.__getinitargs__(self):
##        return (self.vertexCoords, self.faceVertexIDs, self.cellFaceIDs)
    

## ##     def __getstate__(self):
## ##         dict = {
## ##             'vertexCoords' : self.vertexCoords,            
## ##             'faceVertexIDs' : self.faceVertexIDs,
## ##             'cellFaceIDs' : self.cellFaceIDs }
## ##         return dict
## ## 
## ##     def __setstate__(self, dict):
## ##         self.__init__(dict['vertexCoords'], dict['faceVertexIDs'], dict['cellFaceIDs'])
        
                      
    
def _test():
    import doctest
    return doctest.testmod()

if __name__ == "__main__":
    _test()
