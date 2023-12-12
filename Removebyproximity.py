from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsProcessingException,
                       QgsProcessingOutputNumber,
                       QgsProcessingParameterDistance,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterVectorDestination,
                       QgsProcessingParameterRasterDestination,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterVectorLayer,
                       QgsProcessingMultiStepFeedback,
                       QgsProcessingParameterField,
                       QgsVectorLayer,
                       QgsRectangle,
                       QgsCoordinateReferenceSystem
                       )
                       
from qgis import processing
from qgis.utils import iface


class ExampleProcessingAlgorithm(QgsProcessingAlgorithm):
    """
    This is an example algorithm that takes a vector layer,
    creates some new layers and returns some results.
    """

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        # Must return a new copy of your algorithm.
        return ExampleProcessingAlgorithm()

    def name(self):
        """
        Returns the unique algorithm name.
        """
        return 'bufferrasterextend'

    def displayName(self):
        """
        Returns the translated algorithm name.
        """
        return self.tr('Filter by distance')

    def group(self):
        """
        Returns the name of the group this algorithm belongs to.
        """
        return self.tr('Example scripts')

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs
        to.
        """
        return 'examplescripts'

    def shortHelpString(self):
        """
        Returns a localised short help string for the algorithm.
        """
        return self.tr('Este algoritmo filtra puntos en una calle segun una determinada distancia')

    def initAlgorithm(self, config=None):
        """
        Here we define the inputs and outputs of the algorithm.
        """
        # 'INPUT' is the recommended name for the main input
        # parameter.
        
        
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                'INPUT',
                self.tr('Calle'),
                types=[QgsProcessing.TypeVectorPoint]
            )
        )
        
        
        self.addParameter(
            QgsProcessingParameterVectorDestination(
                'OUTPUT',
                self.tr('Puntos filtrados'),
            )
        )
        
        
        self.addParameter(
            QgsProcessingParameterDistance(
                'DISTANCE',
                self.tr('Proximidad'),
                defaultValue = 50.0,
                # Make distance units match the INPUT layer units:
                parentParameterName='INPUT'
            )
        )

        self.addParameter(
            QgsProcessingParameterField(
                'filter', 
                'Campo a filtrar', 
                type=QgsProcessingParameterField.Any, 
                parentLayerParameterName='INPUT', 
                allowMultiple=True, 
                defaultValue=None
            )
        )        
        
        
        

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """
        # First, we get the count of features from the INPUT layer.
        # This layer is defined as a QgsProcessingParameterFeatureSource
        # parameter, so it is retrieved by calling
        # self.parameterAsSource.
        
        layer_base = self.parameterAsVectorLayer(parameters, 'INPUT', context)
        
        input_featuresource = self.parameterAsSource(parameters,
                                                     'INPUT',
                                                     context)
                                                     

        # Retrieve the buffer distance and raster cell size numeric
        # values. Since these are numeric values, they are retrieved
        # using self.parameterAsDouble.
        distance = self.parameterAsDouble(parameters, 'DISTANCE',
                                            context)
                                            
       
       
        layer = layer_base
        layer_extent = layer.extent()
        crs = layer.crs()
        
        
        regular = processing.run("qgis:regularpoints", {
                            'EXTENT':layer_extent,
                            'SPACING':distance,
                            'INSET':0,
                            'RANDOMIZE':False,
                            'IS_SPACING':True,
                            'CRS':QgsCoordinateReferenceSystem(crs.authid()),
                            'OUTPUT':QgsProcessing.TEMPORARY_OUTPUT
                            },
            is_child_algorithm=True,
            context=context,
            feedback=feedback)
       
        if feedback.isCanceled():
            return {}
            
            
        field = processing.run("native:addautoincrementalfield", {
                        'INPUT':regular['OUTPUT'],
                        'FIELD_NAME':'AUTO_COM',
                        'START':0,
                        'MODULUS':0,
                        'GROUP_FIELDS':[],
                        'SORT_EXPRESSION':'',
                        'SORT_ASCENDING':True,
                        'SORT_NULLS_FIRST':False,
                        'OUTPUT':'TEMPORARY_OUTPUT'
                            },
            is_child_algorithm=True,
            context=context,
            feedback=feedback)
       
        if feedback.isCanceled():
            return {}
            
        puntos = processing.run("native:joinbynearest", {
                        'INPUT':parameters['INPUT'],
                        'INPUT_2':field['OUTPUT'],
                        'FIELDS_TO_COPY':['AUTO_COM'],
                        'DISCARD_NONMATCHING':True,
                        'PREFIX':'',
                        'NEIGHBORS':1,
                        'MAX_DISTANCE':distance,
                        'OUTPUT':QgsProcessing.TEMPORARY_OUTPUT},
            is_child_algorithm=True,
            context=context,
            feedback=feedback)
            
        if feedback.isCanceled():
            return {}
            
        borrados = processing.run("native:removeduplicatesbyattribute", {
                        'INPUT':puntos['OUTPUT'],
                        'FIELDS':['AUTO_COM'],
                        'OUTPUT':QgsProcessing.TEMPORARY_OUTPUT},
            is_child_algorithm=True,
            context=context,
            feedback=feedback)
            
        if feedback.isCanceled():
            return {}
            
        limpio = processing.run("native:retainfields", {
                        'INPUT':borrados['OUTPUT'],
                        'FIELDS':parameters['filter'],
                        'OUTPUT':parameters['OUTPUT']},
            is_child_algorithm=True,
            context=context,
            feedback=feedback)

        if feedback.isCanceled():
            return {}
            
                # Return the results
        context.layerToLoadOnCompletionDetails(limpio['OUTPUT']).name = f'Puntos filtrados'
        return limpio
        
        
        

        
        
