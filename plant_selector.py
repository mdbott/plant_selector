# -*- coding: utf-8 -*-
"""
/***************************************************************************
 PlantSelector
                                 A QGIS plugin
 The Plant Selector plugin queries the database to list plants matching the selected map location
                              -------------------
        begin                : 2016-01-12
        git sha              : $Format:%H$
        copyright            : (C) 2016 by Max Bott
        email                : max.d.bott@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, QObject, SIGNAL, QVariant
from PyQt4.QtGui import QAction, QIcon, QMessageBox, QTableWidget, QTableWidgetItem
from PyQt4.QtSql import QSqlDatabase, QSqlQuery
#from Qt import *
from qgis.core import QgsMapLayerRegistry, QgsGeometry, QgsFeatureRequest, QgsDataSourceURI
from qgis.gui import QgsMapToolEmitPoint
# Initialize Qt resources from file resources.py
import resources
# Import the code for the dialog
from plant_selector_dialog import PlantSelectorDialog
import os.path


class PlantSelector:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'PlantSelector_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Create the dialog (after translation) and keep reference
        self.dlg = PlantSelectorDialog()
        # reference to map canvas
        self.canvas = self.iface.mapCanvas()
        # reference to named layers
        # pHlayer = QgisMapLayerRegistry.instance().mapLayersByName('pH')

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Plant Selector')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'PlantSelector')
        self.toolbar.setObjectName(u'PlantSelector')
        # the identify tool will emit a QgsPoint on every click
        self.clickTool = QgsMapToolEmitPoint(self.canvas)
        # create a list to hold our selected feature ids
        self.phList = []
        self.MoistureList = []
        # Soil Property Layers
        self.pHLayer = None
        self.MoistureLayer = None
        self.NitrogenLayer = None
        # Above Ground Layers
        self.WindLayer = None
        self.LightLayer = None






    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('PlantSelector', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/PlantSelector/icon.png'
        self.action = self.add_action(
            icon_path,
            text=self.tr(u'Plant Selector'),
            callback=self.run,
            parent=self.iface.mainWindow())
        QObject.connect(self.action, SIGNAL("triggered()"), self.run)

        # connect to the currentLayerChanged signal of QgsInterface
        result = QObject.connect(self.iface, SIGNAL("currentLayerChanged(QgsMapLayer *)"), self.handleLayerChange)

        # connect to the selectFeature custom function to the map canvas click event
        QObject.connect(self.clickTool, SIGNAL("canvasClicked(const QgsPoint &, Qt::MouseButton)"), self.selectFeature)


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&Plant Selector'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar

    def handleMouseDown(self, point, button):
        self.dlg.clearTextBrowser()
        self.dlg.setTextBrowser(str(point.x()) + " , " + str(point.y()))
        # find out map coordinates from mouse click
        #mapPoint = self.toLayerCoordinates(layer, event.pos())
        #tolerance = self.plugin.getTolerance(layer)
        #area = QgsRectangle(mapPoint.x() - tolerance, mapPoint.y() - tolerance, mapPoint.x() + tolerance, mapPoint.y() + tolerance)

        #request = QgsFeatureRequest()
        #request.setFilterRect(area).setFlags(QgsFeatureRequest.ExactIntersect)
        #request.setSubsetOfAttributes([0])

    def handleLayerChange(self, layer):
        self.cLayer = self.canvas.currentLayer()
        if self.cLayer:
            self.provider = self.cLayer.dataProvider()


    def updateTextBrowser(self):
        # check to make sure we have a feature selected in our selectList -- note that there might be more than one feature
        phoutput = ""
        moistureoutput = ""
        if self.phList:

            # ############ EXAMPLE 1 EDITS GO HERE ####################
            ''' write code that will output ALL selected feature attributes for a single feature into the Text Browser'''
            ''' instead of using the dataProvider.select() function get the actual QgsFeature using dataProvider.featureAtId() '''
            # get the feature by passing in empty Feature
            request = QgsFeatureRequest(self.phList[0])
            for f in self.pHLayer.getFeatures(request):
                phoutput = "Soil pH Level: %s \n" % (f['pH'])

        if self.MoistureList:
            request = QgsFeatureRequest(self.MoistureList[0])
            for f in self.MoistureLayer.getFeatures(request):
                moistureoutput = "Soil Moisture Level: %s \n" % (f['moisture_level'])

        output = phoutput + moistureoutput
        self.dlg.setTextBrowser(output)

        provider = self.pHLayer.dataProvider()
        if provider.name() == 'postgres':
            # get the URI containing the connection parameters
            uri = QgsDataSourceURI(provider.dataSourceUri())
            print uri.uri()
            # create a PostgreSQL connection using QSqlDatabase
            db = QSqlDatabase.addDatabase('QPSQL')
            # check to see if it is valid
            if db.isValid():
                print "QPSQL db is valid"
                # set the parameters needed for the connection
                db.setHostName(uri.host())
                db.setDatabaseName(uri.database())
                db.setPort(int(uri.port()))
                db.setUserName(uri.username())
                db.setPassword(uri.password())
                # open (create) the connection
                if db.open():
                    print "Opened %s" % uri.uri()
                    # execute a simple query
                    #query = db.exec_("""select genus,species from botanical_name where genus = 'Prunus'""")
                    query = QSqlQuery ("""select genus,species from botanical_name where genus = 'Prunus'""")
                    self.dlg.tblPlants.clear()
                    self.dlg.tblPlants.setRowCount(query.size())
                    self.dlg.tblPlants.setColumnCount(query.record().count())
                    self.dlg.tblPlants.setHorizontalHeaderLabels(["Genus", "Species"])
                    self.dlg.tblPlants.setSelectionMode(QTableWidget.SingleSelection)
                    self.dlg.tblPlants.setSelectionBehavior(QTableWidget.SelectRows)
                    # loop through the result set and print the name
                    index=0
                    while query.next():
                        record = query.record()
                        self.dlg.tblPlants.setItem(index, 0, QTableWidgetItem(query.value(0)))
                        self.dlg.tblPlants.setItem(index, 1, QTableWidgetItem(query.value(1)))
                        index = index+1
                        # print record.field('name').value().toString()
                    self.dlg.tblPlants.resizeColumnsToContents()
                else:
                    err = db.lastError()
                    print err.driverText()
        # This piece of Python code is part of a plug-in that I wrote to QGis.
        # This code allows you to populate an object QTableWidget.
        # List contains a recordset query output with 2 fields
        # The first 6 lines of code are for:
        # - delete the contents of the object
        # - determine the number of rows
        # - set the number of columns
        # - insert the header object
        # - enable selection of the entire row
        # FOR the next served instead to populate the object with the contents of the recordset. Note that the object is populated cell by cell.
        # The last statement is used to resize the columns to content.


        # plantlist = [["Malus","Domestica"],["Prunus", "armeniaca"],["Prunus","Communis"]]
        # self.dlg.tblPlants.clear()
        # self.dlg.tblPlants.setRowCount(len(plantlist))
        # self.dlg.tblPlants.setColumnCount(2)
        # self.dlg.tblPlants.setHorizontalHeaderLabels(["Genus", "Species"])
        # self.dlg.tblPlants.setSelectionMode(QTableWidget.SingleSelection)
        # self.dlg.tblPlants.setSelectionBehavior(QTableWidget.SelectRows)
        #
        # for i, plant in enumerate(plantlist):
        #     genus = plant[0]
        #     item = QTableWidgetItem(genus)
        #     #selected = item
        #     #item.setData(Qt.UserRole, QVariant(long(id(plant))))
        #     self.dlg.tblPlants.setItem(i, 0, item)
        #
        #
        #     species = plant[1]
        #     item = QTableWidgetItem(species)
        #     self.dlg.tblPlants.setItem(i, 1, item)
        # pass
        #
        # self.dlg.tblPlants.resizeColumnsToContents()


    def selectFeature(self, point, button):
        # reset selection list on each new selection
        self.phList = []
        self.MoistureList = []
        pntGeom = QgsGeometry.fromPoint(point)
        pntBuff = pntGeom.buffer((self.canvas.mapUnitsPerPixel() * 2), 0)
        rect = pntBuff.boundingBox()
        #if self.pHLayer:
        rq = QgsFeatureRequest(rect)
        for feat in self.pHLayer.getFeatures(rq):
            if feat.geometry().intersects(pntBuff):
                self.phList.append(feat.id())
        for feat in self.MoistureLayer.getFeatures(rq):
            if feat.geometry().intersects(pntBuff):
                self.MoistureList.append(feat.id())
        if self.phList or self.MoistureList:
            self.updateTextBrowser()
        else:
                QMessageBox.information(self.iface.mainWindow(), "Info", "No pH layer currently selected in TOC")


    def run(self):
        """Run method that performs all the real work"""
        # set the current layer immediately if it exists, otherwise it will be set on user selection
        # self.cLayer = self.iface.mapCanvas().currentLayer()
        self.pHLayer = QgsMapLayerRegistry.instance().mapLayersByName('pH')[0]
        self.MoistureLayer = QgsMapLayerRegistry.instance().mapLayersByName('Moisture')[0]
        # make identify the tool we'll use 
        self.canvas.setMapTool(self.clickTool) 
        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            # Do something useful here - delete the line containing pass and
            # substitute with your code.
            pass
