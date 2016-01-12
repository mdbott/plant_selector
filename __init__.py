# -*- coding: utf-8 -*-
"""
/***************************************************************************
 PlantSelector
                                 A QGIS plugin
 The Plant Selector plugin queries the database to list plants matching the selected map location
                             -------------------
        begin                : 2016-01-12
        copyright            : (C) 2016 by Max Bott
        email                : max.d.bott@gmail.com
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load PlantSelector class from file PlantSelector.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .plant_selector import PlantSelector
    return PlantSelector(iface)
