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
from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, QObject, SIGNAL
from PyQt4.QtGui import QAction, QIcon
from qgis.core import *
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

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Plant Selector')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'PlantSelector')
        self.toolbar.setObjectName(u'PlantSelector')
        # the identify tool will emit a QgsPoint on every click
        self.clickTool = QgsMapToolEmitPoint(self.canvas)
        # create a list to hold our selected feature ids
        self.selectList = []
        # current layer ref (set in handleLayerChange)
        self.cLayer = None
        # current layer dataProvider ref (set in handleLayerChange)
        self.provider = None





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
        self.dlg.setTextBrowser( str(point.x()) + " , " +str(point.y()) )

    def handleLayerChange(self, layer):
        self.cLayer = self.canvas.currentLayer()
        if self.cLayer:
            self.provider = self.cLayer.dataProvider()


    def updateTextBrowser(self):
        # check to make sure we have a feature selected in our selectList -- note that there might be more than one feature
        if self.selectList:

            # ############ EXAMPLE 1 EDITS GO HERE ####################
            ''' write code that will output ALL selected feature attributes for a single feature into the Text Browser'''
            ''' instead of using the dataProvider.select() function get the actual QgsFeature using dataProvider.featureAtId() '''
            # get the feature by passing in empty Feature
            request = QgsFeatureRequest(self.selectList[0])
            for f in self.cLayer.getFeatures(request):
                output = "FEATURE ID: %i\n\t %s " % (f['id'],f['pH'])

                self.dlg.setTextBrowser(output)


    def selectFeature(self, point, button):
        # reset selection list on each new selection
        self.selectList = []
        pntGeom = QgsGeometry.fromPoint(point)
        pntBuff = pntGeom.buffer((self.canvas.mapUnitsPerPixel() * 2), 0)
        rect = pntBuff.boundingBox()
        if self.cLayer:
            rq = QgsFeatureRequest(rect)
            for feat in self.cLayer.getFeatures(rq):
                if feat.geometry().intersects(pntBuff):
                    self.selectList.append(feat.id())
            self.cLayer.setSelectedFeatures(self.selectList)
            if self.selectList:
                # make the actual selection
                self.cLayer.setSelectedFeatures([self.selectList[0]])
                # update the TextBrowser
                self.updateTextBrowser()
        else:
                QMessageBox.information( self.iface.mainWindow(),"Info", "No layer currently selected in TOC" )


    def run(self):
        """Run method that performs all the real work"""
        # set the current layer immediately if it exists, otherwise it will be set on user selection
        self.cLayer = self.iface.mapCanvas().currentLayer()
        #self.cLayer = QgsMapLayerRegistry.instance().mapLayer('pH')
        if self.cLayer: self.provider = self.cLayer.dataProvider()

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
