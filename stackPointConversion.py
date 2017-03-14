import os
import sys
import json
import urllib
import matplotlib.pyplot as plt
import matplotlib.path as mplpath
import numpy as np
import cv2
import PIL
from imageCanvas import *


class stackPointConversion():
    def getSectionBounds(self, stack, z):
        urlChar = (stack["baseUrl"] + '/owner/' + stack["owner"] +
                   '/project/' + stack["project"] + '/stack/' +
                   stack["stackname"] + '/z/' + str(z) + '/bounds')
        f = urllib.urlopen(urlChar)
        data = json.loads(f.read())
        return data

    def getTileBounds(self, stack, z):
        urlChar = (stack["baseUrl"] + '/owner/' + stack["owner"] +
                   '/project/' + stack["project"] + '/stack/' +
                   stack["stackname"] + '/z/' + str(z) + '.0' + '/tileBounds')
        f = urllib.urlopen(urlChar)
        tileBounds = json.loads(f.read())
        # compute the centerX and centerY and add it to the tileBounds
        for tile in tileBounds:
            cx = (tile["maxX"]-tile["minX"])/2 + tile["minX"]
            cy = (tile["maxY"]-tile["minY"])/2 + tile["minY"]
            tile.update({"centerX": cx})
            tile.update({"centerY": cy})
        return tileBounds

    def getTileSpecs(self, stack, z):
        '''
        stack - a structure that contains the baseUrl, owner, project,
            stackname, etc.
        z - z-value of the section
        '''
        # get a list of all tiles
        urlChar = (stack["baseUrl"] + '/owner/' + stack["owner"] +
                   '/project/' + stack["project"] + '/stack/' +
                   stack["stackname"] + '/z/' + str(z) + '.0' + '/tile-specs')
        f = urllib.urlopen(urlChar)
        tileSpecs = json.loads(f.read())

        return tileSpecs

    def getTileSpecsFromTileID(self, stack, tileIDs):
        # get the list of tilespecs corresponding to tileIDs from "stack"
        print tileIDs
        tileSpecs = []
        for tileID in tileIDs:
            urlChar = (stack["baseUrl"] + '/owner/' + stack["owner"] +
                       '/project/' + stack["project"] + '/stack/' +
                       stack["stackname"] + '/tile/' + tileID)
            f = urllib.urlopen(urlChar)
            tileSpec = json.loads(f.read())
            tileSpecs.append(tileSpec)
        return tileSpecs

    def loadTileData(self, stackJsonData, stack):
        tileData = {}
        for i, jt in enumerate(stackJsonData):
            td = {}
            td["z"] = jt["z"]
            td["id"] = i
            td["tileId"] = jt["tileId"]
            td["height"] = jt["height"]
            td["width"] = jt["width"]
            td["minX"] = jt["minX"]
            td["minY"] = jt["minY"]
            td["maxX"] = jt["maxX"]
            td["maxY"] = jt["maxY"]
            sectionId = jt["layout"]["sectionId"]

            # compute tile centers in world coordinates
            td["centerX"] = (td["maxX"]-td["minX"])/2
            td["centerY"] = (td["maxY"]-td["minY"])/2

            #  Not used at the moment
            # td["camera"] = jt["layout"]["camera"]
            # td["stageX"] = jt["layout"]["stageX"]
            # td["stageY"] = jt["layout"]["stageY"]
            # td["imageRow"] = jt["layout"]["imageRow"]
            # td["imageCol"] = jt["layout"]["imageCol"]
            # td["owner"] = stack["owner"]
            # td["project"] = stack["project"]
            # td["stackname"] = stack["stackname"]
            tileData[sectionId] = td
        return tileData

    def selectTilesInsidePolygon(self, polygonPoints, tileData):
        '''
        polygonPoints is a set of coordinates that define the polygon
            boundary in world coordinates
        note that the first and last coordinates are
            not the same in polygonPoints
        returns a set of tile indices referencing tileData indices for
            those tiles whose centers are within the polygon
        '''

        # extract the tile center from tileData
        tileCenters = []
        tileIds = []
        for td in tileData:
            tileCenters.append([td["centerX"], td["centerY"]])
            tileIds.append(td["tileId"])

        # create a bounding box path for the polygon
        pPoints = np.array(polygonPoints)

        # create a bounding box path for the polygon
        bbpath = mplpath.Path(pPoints)

        # check if the tile centers are within the polygon
        contains = bbpath.contains_points(tileCenters)

        # extract the indices of those tiles whose centers are within the polygon
        indices = np.nonzero(contains==True)[0]

        # extract the tile IDs from the indices
        tileId = [x for i, x in enumerate(tileIds) if i in indices]
        return tileId


def select_tilespecs_inside_polygon(polygonPoints, tilespecs):
    def tilecenter(tilespec):
        return np.array([(tilespec.maxX - tilespec.minX)/2 + tilespec.minX,
                         (tilespec.maxY - tilespec.minY)/2 + tilespec.minY])
    bbpath = mplpath.Path(np.array(polygonPoints))
    ts_inside = [ts for ts in tilespecs if
                 bbpath.contains_point(tilecenter(ts))]
    return ts_inside
