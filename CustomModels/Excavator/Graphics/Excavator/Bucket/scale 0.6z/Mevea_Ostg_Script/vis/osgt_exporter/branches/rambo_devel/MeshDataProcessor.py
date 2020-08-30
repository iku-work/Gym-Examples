#======================================================================================
# class MeshDataProcessor
#======================================================================================
from copy import deepcopy
import bpy
import bmesh
import sys
import imp
import os
from collections import namedtuple
from numpy import *
import formatter
from mathutils import Vector, Matrix
from itertools import chain, groupby
from bpy_extras.mesh_utils import ngon_tessellate
from time import sleep

PLAIN = False

set_printoptions() # reset numpy print formatting

if os.name == 'posix':
    cNOC        = "\033[0m\033[39m\033[49m"
    cGREY       = "\033[90m"
    cRED        = "\033[91m"
    cGREEN      = "\033[92m"
    cYELLOW     = "\033[93m"
    cBLUE       = "\033[94m"
    cPURPLE     = "\033[95m"
    cCYAN       = "\033[96m"
    cWHITE      = "\033[97m"
else:
    cNOC        = ""
    cGREY       = ""
    cRED        = ""
    cGREEN      = ""
    cYELLOW     = ""
    cBLUE       = ""
    cPURPLE     = ""
    cCYAN       = ""
    cWHITE      = ""


def printArray( caption, arr ):
    print('+++', caption, '+++')
    row_num = 0
    for row in arr:
        print('%4i: ' % row_num, end='' )
        row_num += 1
        print('[ ', end='' )
        for col in row:
            if type( col ) == ndarray:
                print('  ', end='' )
                for i in range( col.shape[0] ):
                    print( " % 6.2f" % ( col[i] ), end='' )
                print('  ', end='' )
            elif type( col ) == int32:
                print( '%2i ' % col, end='' )
            else:
                print( '||| ', end='' )
        print('] ', end='' )
        print()


UVTextureRequest = namedtuple( 'UVTextureRequest', ['source', 'role'] )
RoledImage       = namedtuple( 'RoledImage',       ['image',  'role'] )
#InputObject      = namedtuple( 'InputObject',      ['obj_index', 'object', 'properties'] )
InputObject      = namedtuple( 'InputObject',      ['obj_index', 'object' ] )


Attr_Element_Uniforms = namedtuple( 'Attr_Element_Uniforms', ['attr_array', 'element_array', 'uniform_set'] )


class UniformRequest:
    def __init__(self, type, source=None, target=None, role=None):
        self.type   = type
        self.target = None if target == '' else target
        self.source = None if source == '' else source
        self.role   = None if role   == '' else role
        self.ident  = ':'.join( i for i in [self.type, self.target] if i != None )
        #print( self.__str__() )

    def __str__(self):
        return cYELLOW + 'UniformRequest:   ident:%-10s, type:%s, target:%s, source:%s role:%s' % ( self.ident, self.type, self.target, self.source, self.role ) + cNOC

class AttributeRequest:
    def __init__(self, type=None, source=None, target=None, default=None):
        self.type           = type
        self.target         = None if target  == '' else target
        self.source         = None if source  == '' else source
        self.default        = None if default == '' else default
        self.ident          = ':'.join( i for i in [self.type, self.target] if i != None )
        self.num_components = -1

        if type == 'vertex_float':
            self.source = [ i.strip() for i in self.source.split() ]
            self.num_components = len( self.source )

        print( 'ident:', self.ident )
        #print( self.__str__() )

    def __str__(self):
        return cYELLOW + 'AttributeRequest: ident:%-10s, type:%s, target:%s, source:%s' % ( self.ident, self.type, self.target, self.source ) + cNOC


class MeshDataProcessor():
    #===========
    # __init__
    #===========
    def __init__( self ):
        MissingData = namedtuple( 'MissingData', ['uv_layers', 'uv_textures', 'vertex_colors'] )
        self.missing_data = MissingData( [],[],[] )
        self.valid = True
        self.objects = []

    def _is_all_requested_data_present( self ):
        # every object must provide requested [ uv_layers, uv_textures, vertex_colors ]
        ok = True
        for o in self.input_objects:

            available_uv_layers     = set( [ l.name for l in o.data.uv_layers     ] )
            available_uv_textures   = set( [ l.name for l in o.data.uv_textures   ] )
            available_vertex_colors = set( [ l.name for l in o.data.vertex_colors ] )

            missing_uv_layers     =     self.requested_uv_layers           - available_uv_layers
            missing_uv_textures   = set(self.requested_uv_textures.keys()) - available_uv_textures
            missing_vertex_colors =     self.requested_vertex_colors       - available_vertex_colors

            self.missing_data.uv_layers.append(     missing_uv_layers )
            self.missing_data.uv_textures.append(   missing_uv_textures )
            self.missing_data.vertex_colors.append( missing_vertex_colors )

            # report missing layers
            if len( missing_uv_layers     ) > 0: ok = False; print('ERROR: missing missing uv_layers: %s: [ %s ]' % (o.name, ', '.join( missing_uv_layers     )) )
            if len( missing_uv_textures   ) > 0: ok = False; print('ERROR: missing uv_textures:       %s: [ %s ]' % (o.name, ', '.join( missing_uv_textures   )) )
            if len( missing_vertex_colors ) > 0: ok = False; print('ERROR: missing vertex colors:     %s: [ %s ]' % (o.name, ', '.join( missing_vertex_colors )) )

            o.select = 0
            if len( missing_uv_layers     ) > 0: o.select = 1
            if len( missing_uv_textures   ) > 0: o.select = 1
            if len( missing_vertex_colors ) > 0: o.select = 1
            #o.hide = 1
            #if len( missing_uv_layers     ) > 0: o.hide = 0
            #if len( missing_uv_textures   ) > 0: o.hide = 0
            #if len( missing_vertex_colors ) > 0: o.hide = 0
        return ok


    def _construct_indexing_data( self, mesh ):
        ''' _construct_indexing_data return two lists (v_indices, l_indices) that
        contain the triangle indices of the input mesh 'mesh'.
        These lists can be used to build output triangle data by referring to either
        vertex data (co, no, ...) or loop data (uv, col, ...)
        listed indices will be triads of consecutive tuples of form
        [  vertex_data_index_0,   vertex_data_index_1,   vertex_data_index_2,
          ...
          vertex_data_index_n+0, vertex_data_index_n+1, vertex_data_index_n+2 ]
        '''
        v_indices = []
        l_indices = []
        p_indices = []
        for polygon in mesh.polygons:
            triangle_loop_data = list( chain( *ngon_tessellate( mesh, polygon.vertices, True ) ) )
            for loop_index in ( polygon.loop_indices[i] for i in triangle_loop_data ):
                p_indices.append( polygon.index )
                v_indices.append( mesh.loops[ loop_index ].vertex_index )
                l_indices.append( loop_index )
        return p_indices, v_indices, l_indices


    def _construct_datagrid( self ): #FIXME: appropriate name

        class data_iterator:
            def __init__( self, data_layer, key, indices ):
                self.data_layer = data_layer
                self.key        = key
                self.indices    = indices
            def __iter__( self ):
                for i in self.indices: yield getattr( self.data_layer[i], self.key )[:]

        class true_normal_iterator:
            def __init__( self, data_layer, key, indices ):
                self.data_layer = data_layer
                self.key        = key
                self.indices    = indices
            def __iter__( self ):
                for i in self.indices:
                    true_normal = list( getattr( self.data_layer[i], self.key )[:] )
                    true_normal[0] = true_normal[0] - 0.5
                    true_normal[1] = true_normal[1] - 0.5
                    true_normal[2] = true_normal[2] - 0.5
                    true_normal[0] = true_normal[0] * 2.0
                    true_normal[1] = true_normal[1] * 2.0
                    true_normal[2] = true_normal[2] * 2.0
                    #print( true_normal )
                    yield tuple( true_normal )

        def get_major_axis( N ):
            return sorted( [ (index, c) for index, c in enumerate( N[:] ) ], key=lambda x: abs(x[1]), reverse=True )[0][0]

        def get_cubic_cell( center ):
            S = 50
            x  = floor( center[0] * ( 1.0 / S ) ) * S
            #y = floor( center[1] * ( 1.0 / S ) ) * S
            z  = floor( center[2] * ( 1.0 / S ) ) * S
            return ( x, 0, z )

        #def get_image_ptr( image_or_none ):
        #    if image_or_none:
        #        return image_or_none.as_pointer()
        #    return 0
        class image_iterator:
            def __init__( self, tex_layer, p_indices ):
                self.tex_layer = tex_layer
                self.p_indices = p_indices

            def __iter__( self ):
                for i in self.p_indices:
                    if self.tex_layer[ i ].image:
                        yield self.tex_layer[ i ].image.as_pointer()
                    else:
                        yield 0

        def get_material_ptr( object, polygon ):
            if len( object.material_slots ) <= polygon.material_index:
                return 0
            return object.material_slots[ polygon.material_index ].material.as_pointer()

        def custom_vertex_float_iterator( bm, req, v_indices ):
            components = req.source
            try:
                layers = [ bm.verts.layers.float[i] for i in components ]
            except:
                print("WARNING: missing data: '%s'" % components)
                for i in v_indices:
                    yield (1.0, 0.3, 0.0)
                return


            for i in v_indices:
                r = tuple( bm.verts[i][layer] for layer in layers )
                #print( r )
                yield r


        loop_arrays = [] # loop data arrays for each object


        for object_counter, o in enumerate( self.input_objects ):

            #sys.stdout.flush()
            mesh = o.to_mesh( scene=bpy.context.scene, apply_modifiers=True, settings='RENDER' )
            bm   = bmesh.new()
            bm.from_mesh( mesh )
            p_indices, v_indices, l_indices = self._construct_indexing_data( mesh )

            M = self.reference_matrix.inverted() * o.matrix_world.copy()  # matrix transform applied when vertex values are stored
            R = M.to_3x3()                                                # matrix rotation applied to normals
            R[0].normalize()    # axes must be normalized to prevent normal scaling
            R[1].normalize()
            R[2].normalize()

            columns = {}
            columns['loop_index'] = arange( len( l_indices ) )
            for req in self.attribute_requests:
                if req.type == 'co':  columns[ req.ident ] = data_iterator(                         mesh.vertices, 'co',     v_indices )
                if req.type == 'no':
                    #if 'true_normal.x' in o.loops.float and 'true_normal.y' in o.loops.float and 'true_normal.z' in o.loops.float
                    if 'true_normal' in bm.loops.layers.color:
                        columns[ req.ident ] = true_normal_iterator( mesh.vertex_colors[ 'true_normal' ].data, 'color',  l_indices )
                    else:
                        columns[ req.ident ] = data_iterator( mesh.vertices, 'normal', v_indices )

                if req.type == 'uv':  columns[ req.ident ] = data_iterator(     mesh.uv_layers[ req.source ].data, 'uv',     l_indices )
                if req.type == 'col': columns[ req.ident ] = data_iterator( mesh.vertex_colors[ req.source ].data, 'color',  l_indices )
                #if req.type == 'vertex_float':
                #    columns[ req.ident ] = custom_vertex_float_iterator( bm, req, v_indices )   #TODO: REMOVE vertex_float

            # define dummy data for dummy uniform type
            columns[ 'dummy' ] = ( 0 for p_index in p_indices )

            for req in self.uniform_requests:
                #assert( type( req ) == UniformRequest )
                #req = deepcopy( req )
                #assert( req.ident not in columns )
                src = req.source # have to make copy. generator object closures screw up local scoping...
                #if req.type == 'tex':          columns[ req.ident ]            = ( get_image_ptr(     mesh.uv_textures[ src ].data[ p_index ].image ) for p_index in p_indices )
                if req.type == 'tex':          columns[ req.ident ]            = image_iterator( mesh.uv_textures[ src ].data, p_indices )
                if req.type == 'major_axis':   columns[ 'prop:i4:major_axis' ] = ( get_major_axis(   R * mesh.polygons[ p_index ].normal )            for p_index in p_indices )
                if req.type == 'material':     columns[ 'material']            = ( get_material_ptr( o,  mesh.polygons[ p_index ] )                   for p_index in p_indices )
                if req.type == '_obj_index':   columns[ req.ident ]           = ( o.pass_index                                             for _       in p_indices )
                if req.type == '_obj_counter': columns[ req.ident ]           = ( object_counter                                           for _       in p_indices )
                if req.type == 'cubic_cell':   columns[ req.ident ]            = ( get_cubic_cell( mesh.polygons[ p_index ].center )                  for p_index in p_indices )

            for req in self.object_property_requests:
                #print( req )
                if req.name in o:
                    columns[ 'prop:%s:%s' % ( req.datatype, req.name ) ] = list( o[ req.name ] for _ in p_indices )
                else:
                    columns[ 'prop:%s:%s' % ( req.datatype, req.name ) ] = list( req.default_value for _ in p_indices )




            #=================================
            # Generate major axis information
            #=================================


            print( o.name.ljust(30), end=' ' )
            # Compose data matrix
            loop_array = zeros( len( l_indices ), dtype=self.loop_dtype + self.attr_dtype + self.uni_dtype )
            for field_name in loop_array.dtype.names:
                print( field_name, end=' ' )
                #print(  )
                sys.stdout.flush()
                l = list( columns[ field_name ] )
                #print( 'dtype:', loop_array[ field_name ].dtype )
                #print( 'array:', l )
                #print(  )

                loop_array[ field_name ] = l
            print()



            # Apply transformations
            #FIXME: python iteration may be slow
            print('Applying transformation...')
            if 'co' in self.attr_fields:
                for i, co in enumerate( loop_array['co'] ):
                    loop_array['co'][i] = ( M * Vector( co ).to_4d() )[:3]

            if 'no' in self.attr_fields:
                for i, no in enumerate( loop_array['no'] ):
                    loop_array['no'][i] = ( R * Vector( no ) )[:]

            #TODO: remove vertex_float
            if 'vertex_float:soft_light' in self.attr_fields:
                for i, no in enumerate( loop_array['vertex_float:soft_light'] ):
                    loop_array['vertex_float:soft_light'][i][0:3] = ( M * Vector( no ).to_4d() )[0:3]
                    #print( loop_array['vertex_float:soft_light'][i][0:3] )

            #if 'vertex_float:soft_light' in self.attr_fields:
            #    for i, no in enumerate( loop_array['vertex_float:soft_light'] ):
            #        loop_array['vertex_float:soft_light'][i][0:3] = ( R * Vector( no ).to_3d() )[0:3]


            #for i, no in enumerate( loop_array['no'] ):
            #    loop_array['no'][i] = ( R * Vector( no ) )[:]

            loop_arrays.append( loop_array )

            continue
        #
        #=================================== end for
        print('Merging object datagrids...')
        loop_array = concatenate( loop_arrays )
        loop_array['loop_index'] = arange( len( loop_array ) ) # reset loop_index field
        return loop_array



    def _weld( self, input_array ):
        # remove duplicates by given tolerance
        # and return ( reduced_input_array, indices_to_reconstruct_the_original_input_array )

        dup = input_array.copy()
        # first sort by uni fields so that returned array can be grouped by uniforms
        dup.sort( order=self.uni_fields + self.loop_field )

        for field_name in dup.dtype.names:
            if dup[ field_name ].dtype == float32:
               dup[ field_name ] = around( dup[ field_name ], self.weld_tolerance )
        reduced_attributes, take_index_attr, attr_element_indices = unique( dup[ self.attr_fields ], return_index=1, return_inverse=1 )
        reduced_uniforms,   take_index_uni                        = unique( dup[ self.uni_fields ], return_index=1, return_inverse=0 )

        #==============================
        # Create attr and index arrays
        #==============================

        L = len( take_index_uni )
        uni_spans = list( zip( take_index_uni[0:L-1], take_index_uni[1:L] ) )
        uni_spans.append( ( take_index_uni[L-1], len( attr_element_indices ) ) )
        return reduced_attributes, attr_element_indices, reduced_uniforms, uni_spans




    def _weld_one_attr_and_many_element_arrays( self, input_array ):

        dup = input_array.copy()
        # first sort by uni fields so that returned array can be grouped by uniforms
        dup.sort( order=self.uni_fields + self.loop_field )
        #printArray( 'dup', dup )

        for field_name in dup.dtype.names:
            if dup[ field_name ].dtype == float32:
               dup[ field_name ] = around( dup[ field_name ], self.weld_tolerance )
        #reduced_attributes, take_index_attr, attr_element_indices = unique( dup[ self.attr_fields ], return_index=1, return_inverse=1 )
        reduced_uniforms,  take_index_uni                        = unique( dup[ self.uni_fields  ], return_index=1, return_inverse=0 )


        L = len( take_index_uni )
        uni_spans = list( zip( take_index_uni[0:L-1], take_index_uni[1:L] ) )
        uni_spans.append( ( take_index_uni[L-1], len( dup ) ) )

        ret = []

        for span, take_uni in zip( uni_spans, take_index_uni ):
            attr_array = dup[ self.attr_fields ][span[0]:span[1]]
            reduced_attributes, take_index_attr, attr_element_indices = unique( attr_array, return_index=1, return_inverse=1 )

            ret.append(     Attr_Element_Uniforms( reduced_attributes,
                                                   attr_element_indices,
                                                   dup[self.uni_fields][ take_uni ] ))
           #
           #---

        return ret



    def run( self, objects, export_source_setup, reference_matrix, use_shared_vertex_data=False ):
        attributes             = export_source_setup.attributes
        grouping               = export_source_setup.groupby
        # Processor parameters =================
        self.object_property_requests   = export_source_setup.object_property_requests

        self.reference_matrix           = reference_matrix
        self.input_objects              = sorted( objects, key=lambda o: o.name )
        self.weld_tolerance             = export_source_setup.weld_tolerance

        self.attribute_requests        = [ AttributeRequest(   *a.split(':') ) for a in attributes                          ]
        self.uniform_requests          = [ UniformRequest(     *u.split(':') ) for u in grouping                            ]
        self.uniform_requests         += [ UniformRequest(     *(['tex',]  + u.split(':')) ) for u in export_source_setup.mesh_textures   ]

        self.valid_attributes   = 'co no uv col'.split()
        self.valid_uniforms     = 'material cubic_cell tex prop major_axis _obj_index _obj_counter'.split()

        for req in self.attribute_requests:
            if req.type not in self.valid_attributes:
                raise NameError( 'MeshDataProcessor cannot process attribute of type "%s"' % req.type )
        for req in self.uniform_requests:
            if req.type not in self.valid_uniforms:
                raise NameError( 'MeshDataProcessor cannot process uniform of type "%s"' % req.type )


        # Requested uniform options ============
        self.requested_uv_textures   = dict()    # require images reference to be present on these uv layers
        self.requested_uv_layers     = set()     # require these uv layers to be present
        self.requested_vertex_colors = set()
        # ======================================
        self.loop_dtype = [ ('loop_index', 'i4', 1) ]
        self.attr_dtype = []
        self.uni_dtype  = []   # used to refer to per object properties (ie. spot_binding)
        # ======================================
        for req in self.attribute_requests:
            if req.type == 'co':   self.attr_dtype.append( ( req.ident, 'f4', 3) )
            if req.type == 'no':   self.attr_dtype.append( ( req.ident, 'f4', 3) )
            if req.type == 'uv':   self.attr_dtype.append( ( req.ident, 'f4', 2) ); self.requested_uv_layers.add(     req.source )
            if req.type == 'col':  self.attr_dtype.append( ( req.ident, 'f4', 3) ); self.requested_vertex_colors.add( req.source )
            if req.type == 'vertex_float':
                self.attr_dtype.append( ( req.ident, 'f4', req.num_components) )

        # add dummy uniform request because one must always be present
        self.uni_dtype.append(  ('dummy', 'i4', 1 ) )

        for req in self.uniform_requests:
            #print( req )
            if req.type == 'material':      self.uni_dtype.append(  ('material',           'i8', 1) )
            if req.type == 'tex':           self.uni_dtype.append(  ( req.ident,           'i8', 1) ); self.requested_uv_textures[req.source] = UVTextureRequest( req.source, req.role )
            if req.type == 'major_axis':    self.uni_dtype.append(  ('prop:i4:major_axis', 'i8', 1) )
            if req.type == '_obj_index':    self.uni_dtype.append(  ( req.type,            'i8', 1) )
            if req.type == '_obj_counter':  self.uni_dtype.append(  ( req.type,            'i8', 1) )
            if req.type == 'cubic_cell':    self.uni_dtype.append(  ('cubic_cell',         'i8', 3) )

        for req in self.object_property_requests:
            self.uni_dtype.append(  ('prop:%s:%s' % ( req.datatype, req.name ), req.datatype, req.num_elements ) )
            print( self.uni_dtype )


        # Assert that all requested data is available ===========================
        if not self._is_all_requested_data_present():
            self.valid = False
            raise RuntimeError('Missing required data')
            return

        self.loop_field  = [ i[0] for i in self.loop_dtype ]
        self.attr_fields = [ i[0] for i in self.attr_dtype ]
        self.uni_fields  = [ i[0] for i in self.uni_dtype  ]

        #=============================================
        # Construct_datagrid
        #=============================================
        # loop | attr | attr | ... | uni | uni | uni |
        #------|------|------| ... |-----|-----|-----|
        #  0   |  ..  |  ..  |  .  |  .. |  .. | ..  |
        #  1   |  ..  |  ..  | ... |  .. |  .. | ..  |
        #  2   |  ..  |  ..  |  .  |  .. |  .. | ..  |
        # ...
        #
        print('constructing datagrid...')
        big_data = self._construct_datagrid()


        #===================
        # Compose Drawables
        #===================

        if use_shared_vertex_data:
            reduced_attributes, attr_element_indices, reduced_uniforms, uni_spans = self._weld( big_data )

            #self.reduced_attributes     = reduced_attributes
            #self.attr_element_indices   = attr_element_indices
            #self.reduced_uniforms       = reduced_uniforms
            #self.uni_spans              = uni_spans

            return reduced_attributes, attr_element_indices, reduced_uniforms, uni_spans
        else:
            # Many attr arrays and many index arrays
            splitted_arrays = self._weld_one_attr_and_many_element_arrays( big_data )

            return splitted_arrays





        print('Mesh data processor is now done')


    def print_missing_data( self ):
        if len( self.missing_data.uv_layers     ) > 0: print('ERROR: missing missing uv_layers: %s: [ %s ]' % (o.name, ', '.join( self.missing_data.uv_layers     )) )
        if len( self.missing_data.uv_textures   ) > 0: print('ERROR: missing uv_textures:       %s: [ %s ]' % (o.name, ', '.join( self.missing_data.uv_textures   )) )
        if len( self.missing_data.vertex_colors ) > 0: print('ERROR: missing vertex colors:     %s: [ %s ]' % (o.name, ', '.join( self.missing_data.vertex_colors )) )
