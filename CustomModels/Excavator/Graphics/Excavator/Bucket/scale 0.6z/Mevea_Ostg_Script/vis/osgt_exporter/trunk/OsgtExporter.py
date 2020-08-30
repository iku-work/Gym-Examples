import os
import imp
import bpy
from itertools import chain, groupby
from collections import OrderedDict, Counter
from numpy import *
from collections import namedtuple

PLAIN = False

import MeshDataProcessor
imp.reload( MeshDataProcessor )
from MeshDataProcessor import MeshDataProcessor, printArray

import osgt_template_functions
from osgt_template_functions import write_root_stateset, write_material_stateset, write_mesh_texture_stateset, write_geometry
from osgt_template_functions import Traverser, write_primitive_set_list, write_color_data, write_texcoord_data
import imp
imp.reload( osgt_template_functions )



#cNOC     = "\033[0m\033[39m\033[49m"
#cGREY    = "\033[90m"
#cRED     = "\033[91m"
#cGREEN   = "\033[92m"
#cYELLOW  = "\033[93m"
#cBLUE    = "\033[94m"
#cPURPLE  = "\033[95m"
#cCYAN    = "\033[96m"
#cWHITE   = "\033[97m"

cNOC     = ''
cGREY    = ''
cRED     = ''
cGREEN   = ''
cYELLOW  = ''
cBLUE    = ''
cPURPLE  = ''
cCYAN    = ''
cWHITE   = ''




DrawableData = namedtuple( 'DrawableData',      ['attr_array', 'elem_array'] )

ExportImage = namedtuple( 'ExportImage',      ['image', 'export_name', 'unique_id'] )

class ImageExportManager( OrderedDict ):
    
    def __init__( self ):
        osgt_template_functions.getUniqueId.reset() # XXX: should be elsewhere
        super().__init__()
        self.default_textures = {}
        
        if 'default_normal' not in bpy.data.images:
            image = bpy.data.images.new( name='default_normal', width=1, height=1 )
            image.pixels[:] = ( 0.5, 0.5, 1.0, 1.0 )
        else:
            image = bpy.data.images['default_normal']
            image.pixels[:] = ( 0.5, 0.5, 1.0, 1.0 )
        
        if 'default' not in bpy.data.images:
            image = bpy.data.images.new( name='default', width=1, height=1 )
            image.pixels[:] = ( 1.0, 1.0, 1.0, 0.0 )
        else:
            image = bpy.data.images['default']
            image.pixels[:] = ( 1.0, 1.0, 1.0, 0.0 )
    
    def add_default_image( self, texture_target_str ):
        if 'normal' in texture_target_str:
            self.default_textures[ texture_target_str ] = ExportImage( bpy.data.images['default_normal'], 'default_normal.png', osgt_template_functions.getUniqueId() )
        else:
            self.default_textures[ texture_target_str ] = ExportImage( bpy.data.images['default'], 'default.png', osgt_template_functions.getUniqueId() )
    
    def getExportName( self, image ):
        return self[ image ].export_name
    
    def get_default_image( self, texture_target_str ):
        return self.default_textures[texture_target_str]
    
    def add_image( self, image ):
        if image != None and image not in self:
            i = len( self )
            self[ image ] = ExportImage( image, 'something_%04i.png' % i, osgt_template_functions.getUniqueId() )
            print(' +++: adding image: %30s --> %s' % ( image.name, self[image].export_name ) )
        

imageExportManager = ImageExportManager()




class UniformTreeElement:
    def __init__( self, type, key, primary_sort_priority, secondary_sort_priority, repr, value ):
        self.type                       = type
        self.key                        = key
        self.primary_sort_priority      = primary_sort_priority
        self.secondary_sort_priority    = secondary_sort_priority
        self.repr                       = repr
        self.value                      = value
    
    def __repr__( self ):
        #return '%s( val: %s  key: %i   repr: %s )' % ( self.type, self.value, self.key, self.repr )
        #return '%s( %i : %s )' % ( self.type, self.key, self.repr )
        #return '%s(%s : %s)' % ( self.type, self.key, self.repr )
        return '(%s)' % ( self.repr )
    
    def __eq__( self, other ):   # for Counter
        return (self.type, self.key) == (other.type, other.key)
        
    def __hash__( self ):   # for Counter
        return hash( ( self.type, self.key ) )




class Node:
    def __init__( self, common_factor ):
        self.children       = []
        self.common_factor  = common_factor
        self.dot            = 'o'
        
        self.defined_textures = None    # texture list
        
        if type( self.common_factor ) == str:
            self.dot == self.common_factor
        elif type( self.common_factor ) == UniformTreeElement:
            if self.common_factor.type == '_obj_index':
                self.dot = '_'
            elif self.common_factor.type == '_mat_index':
                self.dot = 'M'
            elif self.common_factor.type.startswith('tex'):
                self.dot = 'm'
            
            
    def add( self, node ):                  
        self.children.append( node )
        
    def _write_node( self, out ):
        #out.write('osg::Group #%s' % self.common_factor.type )
        #out.write('{')
        out.write('#%s' % self.common_factor.type )
        out.write( str( self.common_factor.value ) )
        #out.write('}')
        
    
    
    def _write_mesh_texture( self, out ):
        if PLAIN:
            return
        
        locally_defined_textures = self.common_factor.value # magic: self.common_factor.value is material
        
        for k, v in locally_defined_textures.items():   # replace stack values with local values
            assert( k in self.defined_textures[-1].keys() )
            if v != None:
                self.defined_textures[-1][k] = v
            
        export_texture = self.defined_textures[-1]
        
        
        out.write('StateSet TRUE')
        out.write('{')
        out.write('osg::StateSet')
        out.write('{')
        out.write('UniqueID %i' % osgt_template_functions.getUniqueId())
        out.write('Name "mesh_texture"' )
        out.write('DataVariance STATIC')

        if 1:
            #print('mesh texture stateset: ',  self.defined_textures[-1])
            
            L = sum([ 1 if image != None else 0 for image, _ in export_texture.items() ])
            L = 0
            for target_name, image in export_texture.items():
                if image:
                    L += 1
            out.write('TextureAttributeList %i' % ( len( export_texture.keys() ) ) )
            out.write('{')
            
            for target_name, image in export_texture.items():
                out.write('Data 1')
                out.write('{')
                out.write('osg::Texture2D')
                out.write('{')
                
                if image:
                    out.write('UniqueID %i' % imageExportManager[image].unique_id )
                else:
                    out.write('UniqueID %i' % imageExportManager.get_default_image( target_name ).unique_id )
                out.write('}')
                out.write('Value OFF')
                out.write('}')
                    
            out.write('}') # TextureAttributeList ends

        out.write('}') # osg::StateSet
        out.write('}') # StateSet TRUE
        return
        
    
    def _write_material_stateset( self, out ):
        if PLAIN:
            return
        m = self.common_factor.value[0] # magic: index 0 is material
        
        
        locally_defined_textures = self.common_factor.value[1] # magic: index 1 is export texture
        
        for k, v in locally_defined_textures.items():   # replace stack values with local values
            assert( k in self.defined_textures[-1].keys() )
            if v != None:
                self.defined_textures[-1][k] = v
        
        
        
        if m == None:
            assert(0)
            return
        else:
            alpha          = m.alpha
            alpha_blend    = m.game_settings.alpha_blend
            diffuse_color  = tuple([ m.diffuse_intensity  * component for component in m.diffuse_color[:]  ] )
            specular_color = tuple([ m.specular_intensity * component for component in m.specular_color[:] ] )
            shininess      = m.specular_hardness / 512.0
            emit           = tuple( m.emit * d for d in diffuse_color )

        render_bin_number = -1
        if m != None:
            render_bin_number = -1 if m.pass_index == 0 else m.pass_index


        out.write('StateSet TRUE')
        out.write('{')
        out.write('osg::StateSet')
        out.write('{')
        out.write('UniqueID %i' % osgt_template_functions.getUniqueId())
        out.write('Name "%s.material_state"' % 'hmm' )
        out.write('DataVariance STATIC')

        if 1:
            out.write('AttributeList 1')
            out.write('{')

            out.write('osg::Material')
            out.write('{')
            out.write('UniqueID %i' % osgt_template_functions.getUniqueId())
            out.write('Ambient   TRUE Front % 5.3f % 5.3f % 5.3f 1      Back % 5.3f % 5.3f % 5.3f 1'      % (0,0,0,0,0,0)    )
            out.write('Diffuse   TRUE Front % 5.3f % 5.3f % 5.3f % 5.3f Back % 5.3f % 5.3f % 5.3f % 5.3f' % ((diffuse_color+(alpha,))*2)  )
            out.write('Specular  TRUE Front % 5.3f % 5.3f % 5.3f 1      Back % 5.3f % 5.3f % 5.3f 1'      % (specular_color*2) )
            out.write('Emission  TRUE Front % 5.3f % 5.3f % 5.3f 1      Back % 5.3f % 5.3f % 5.3f 1'      % (emit*2)           )
            out.write('Shininess TRUE Front % 5.3f Back % 5.3f' % (shininess, shininess) )
            out.write('}')
            out.write('Value OFF')

            out.write('}') # AttributeList 1


        # write mateiral textures

        if 1:
            out.write('TextureModeList 1')
            out.write('{')
            out.write('Data 1')
            out.write('{')
            out.write('GL_TEXTURE_2D ON')
            out.write('}') # Data 1
            out.write('}') # TextureModeList

        
        if 1:
            #print('material_stateset: ',  self.defined_textures[-1])
            export_texture = self.defined_textures[-1]
            #material_textures = [ (target, etex) for target, etex in material_textures.items() if etex is not None ]
            L = sum([ 1 if image != None else 0 for image, _ in export_texture.items() ])
            L = 0
            for target_name, image in export_texture.items():
                if image:
                    L += 1
            out.write('TextureAttributeList %i' % ( len( export_texture.keys() ) ) )
            #out.write('TextureAttributeList %i' % (L) )
            out.write('{')
            
            # print( '+++' )
            # print( export_texture )
            # print( '+++' )
            
            for target_name, image in export_texture.items():
                #print('TARGET: ', target_name )
                out.write('Data 1')
                out.write('{')
                out.write('osg::Texture2D')
                out.write('{')
                #out.write('UniqueID %i' % osgt_template_functions.getUniqueId())
                
                if image:
                    out.write('UniqueID %i' % imageExportManager[image].unique_id )
                else:
                    out.write('UniqueID %i' % imageExportManager.get_default_image( target_name ).unique_id )
                #out.write('Name "s_%s"' % target_name )
                #out.write('WRAP_S REPEAT')
                #out.write('WRAP_T REPEAT')
                #out.write('WRAP_R CLAMP_TO_EDGE')
                #out.write('MIN_FILTER LINEAR_MIPMAP_LINEAR')
                #out.write('MAG_FILTER LINEAR')
                #out.write('UnRefImageDataAfterApply TRUE')
                #out.write('ResizeNonPowerOfTwoHint TRUE')
                #out.write('Image TRUE')
                #out.write('{')
                #out.write('UniqueID %i' % osgt_template_functions.getUniqueId())
                #out.write('FileName "%s"' % getExportName( image ) )
                #out.write('WriteHint 0 2')
                #out.write('DataVariance STATIC')
                #out.write('}')
                out.write('}')
                out.write('Value OFF')
                out.write('}')
                    
            out.write('}') # TextureAttributeList ends



        out.write('}') # osg::StateSet
        out.write('}') # StateSet TRUE
        return

    def _write_axis_stateset( self, out ):
        
        if PLAIN:
            return
            
        properties = self.common_factor
        
        out.write('StateSet TRUE')
        out.write('{')
        out.write('osg::StateSet')
        out.write('{')
        out.write('UniqueID %i' % osgt_template_functions.getUniqueId())
        out.write('Name "%s.material_state"' % 'hmm' )
        out.write('DataVariance STATIC')

        
        out.write('UniformList %i' % (8 + n_custom_properties) )
        out.write('{')
        
        for prop in properties:
            num_prop_elements = 1
            try:
                num_prop_elements = len( prop.value )
            except:
                pass
            out.write('osg::Uniform')
            out.write('{')
            out.write('UniqueID %i' % getUniqueId())
            out.write('Name "%s"' % prop.name     )
            out.write('Type %s'   % prop.datatype )
            out.write('NumElements 1')
            
            if prop.datatype == 'INT':
                array_type = 'Int'
            elif prop.datatype == 'FLOAT':
                array_type = 'Float'
            elif prop.datatype == 'FLOAT_VEC3':
                array_type = 'Float'
            else:
                raise RuntimeError('Custom property datatype is invalid!')    
            
            out.write('Elements TRUE ArrayID %i %sArray %i' % ( getUniqueId(), array_type, num_prop_elements ) )
            out.write('{')
            
            #out.write( '%5.7f' % ( material_scale ) )
            if prop.datatype == 'FLOAT_VEC3':
                out.write( ( '%5.7f ' * num_prop_elements ) % ( prop.value[:] ) )
            elif prop.datatype == 'INT':
                out.write( ( '%i ' * num_prop_elements ) % ( prop.value ) )
            else:
                raise RuntimeError('Custom property datatype is invalid!')
                
            out.write('}')
            out.write('}')
            out.write('Value OFF')
        
        out.write('}') # osg::StateSet
        out.write('}') # StateSet TRUE
    
    def write( self, out ):
        
        out.write('osg::Group')
        out.write('{')
        out.write('UniqueID %i' % osgt_template_functions.getUniqueId())
        
        #if   self.common_factor.type         == 'root':         self._write_node( out )
        #elif self.common_factor.type         == '_mat_index':   self._write_node( out )
        #elif self.common_factor.type         == '_obj_index':   self._write_node( out )
        #elif self.common_factor.type.startswith('tex'):         self._write_node( out )
        #elif self.common_factor.type         == 'prim':         self._write_geometry( out )
        #else: raise RuntimeError('Node: cannot write node into osgt file. (unsupported type received("%s"))' % (self.common_factor.type) )
        #else: pass
        
        if self.common_factor.type == '_mat_index':
            self._write_material_stateset( out )
            
        elif self.common_factor.type.startswith('tex'):
            self._write_mesh_texture( out )
            
        #elif self.common_factor.type == 'major_axis':
        #    self._write_axis_stateset( out )
        
        # write children
        out.write('Children %i' % len( self.children ) )
        out.write('{')
        for c in self.children:
            #c.write( out )
            self.defined_textures.append( self.defined_textures[-1].copy() )
            c.defined_textures = self.defined_textures # pass list reference
            c.write( out )
            self.defined_textures.pop()
        out.write('}')  # children
        out.write('}')  # this group
        pass


class Root( Node ):

    def __init__( self, common_factor ):
        super().__init__( common_factor )
        self.dot = 'r'
    
    def write_texture_definitions( self, out ):
        #if PLAIN:
        #    return
        out.write('osg::Group')
        out.write('{')
        out.write('UniqueID %i' % osgt_template_functions.getUniqueId())
        
        out.write('StateSet TRUE')
        out.write('{')
        out.write('osg::StateSet')
        out.write('{')
        out.write('UniqueID %i' % osgt_template_functions.getUniqueId())
        out.write('Name "texture_definitions"')
        out.write('DataVariance STATIC')
        
        out.write('TextureAttributeList %i' % ( len( imageExportManager.keys() ) ) )
        out.write('{')
        
        for image, export_image in imageExportManager.items():
            out.write('Data 1')
            out.write('{')
            out.write('osg::Texture2D')
            out.write('{')
            out.write('UniqueID %i' % export_image.unique_id )
            #out.write('Name "s_%s"' % target_name )
            out.write('WRAP_S REPEAT')
            out.write('WRAP_T REPEAT')
            out.write('WRAP_R CLAMP_TO_EDGE')
            out.write('MIN_FILTER LINEAR_MIPMAP_LINEAR')
            out.write('MAG_FILTER LINEAR')
            out.write('UnRefImageDataAfterApply TRUE')
            out.write('ResizeNonPowerOfTwoHint TRUE')
            out.write('Image TRUE')
            out.write('{')
            out.write('UniqueID %i' % osgt_template_functions.getUniqueId())
            out.write('FileName "%s"' % export_image.export_name )
            out.write('WriteHint 0 2')
            out.write('DataVariance STATIC')
            out.write('}')
            out.write('}')
            out.write('Value OFF')
            out.write('}')
        out.write('}') # TextureAttributeList ends
        
        out.write('}')  # StateSet TRUE
        out.write('}')  # osg::StateSet
        out.write('}')  # osg::Group
    
    def write_texture_order_state( self, out ):
        if PLAIN:
            return
        texture_list = self.value[0]
        
        out.write('StateSet TRUE')
        out.write('{')
        out.write('osg::StateSet')
        out.write('{')
        out.write('UniqueID %i' % osgt_template_functions.getUniqueId())
        out.write('Name "texture_definitions"')
        out.write('DataVariance STATIC')
        
        out.write('TextureAttributeList %i' % len( texture_list ) )
        out.write('{')
        
        for target, image in texture_list.items():
            out.write('Data 1')
            out.write('{')
            out.write('osg::Texture2D')
            out.write('{')
            out.write('UniqueID %i' % imageExportManager.get_default_image(target).unique_id )
            out.write('Name "s_%s"' % target )
            out.write('WRAP_S REPEAT')
            out.write('WRAP_T REPEAT')
            out.write('WRAP_R CLAMP_TO_EDGE')
            out.write('MIN_FILTER LINEAR_MIPMAP_LINEAR')
            out.write('MAG_FILTER LINEAR')
            out.write('UnRefImageDataAfterApply TRUE')
            out.write('ResizeNonPowerOfTwoHint TRUE')
            out.write('Image TRUE')
            out.write('{')
            out.write('UniqueID %i' % osgt_template_functions.getUniqueId())
            out.write('FileName "%s"' % imageExportManager.get_default_image(target).export_name )
            out.write('WriteHint 0 2')
            out.write('DataVariance STATIC')
            out.write('}')
            out.write('}')
            out.write('Value OFF')
            out.write('}')
        out.write('}') # TextureAttributeList ends
        
        out.write('}')  # StateSet TRUE
        out.write('}')  # osg::StateSet
        
    def write( self, out ):
        out.write('#Ascii Scene')
        out.write('#Version 78')
        out.write('#Generator OpenSceneGraph 2.9.17')

        out.write('osg::Group')
        out.write('{')
        out.write('UniqueID %i' % osgt_template_functions.getUniqueId())
        
        out.write('UserDataContainer TRUE')
        out.write('{')
        out.write('osg::DefaultUserDataContainer')
        out.write('{')
        out.write('UniqueID %i' % osgt_template_functions.getUniqueId())
        out.write('UDC_Descriptions 5')
        out.write('{')
        out.write('"USE_SHADER %s"' % self.value[1] ) # magic: shader name at index 1
        out.write('"USE_BUMP_MAP s_mat_diffuse"')   # ei helvetti
        out.write('"USE_BUMP_SCALE 10.0"')
        out.write('"USE_BUMP_UV_INDEX 0"')
        out.write('"BIND_VERTEX_ATTRIBUTE_NAME a_soft_light 10"')   #TODO: FIXME!
        out.write('}')
        out.write('}')
        out.write('}')
        
        # default texture order
        
        self.write_texture_order_state( out )
        
        num_children = len( self.children )
        if PLAIN == False:
            num_children += 1
        
        out.write('Children %i' % num_children )
        out.write('{')
        
        if PLAIN == False:
            self.write_texture_definitions( out )
        
        for c in self.children:
            self.defined_textures.append( self.defined_textures[-1].copy() )
            c.defined_textures = self.defined_textures # pass list reference
            c.write( out )
            self.defined_textures.pop()
        
        out.write('}')  # children
        out.write('}')




class Geode( Node ):

    def __init__( self, common_factor ):
        super().__init__( common_factor )
        self.dot = 'g'

    def write( self, out ):
        out.write('osg::Geode')
        out.write('{')
        out.write('UniqueID %i' % osgt_template_functions.getUniqueId())
        out.write('Name "NAME_HERE"')
        
        out.write('Drawables %i' % len(self.children) )
        out.write('{')
        for c in self.children:
            c.write( out )
        out.write('}')  # drawables
        
        #out.write('Drawables 0')
        #out.write('{')
        #out.write('}')
        
        out.write('}')

        
class DrawableNode( Node ):
    def write( self, out ):
        out.write('osg::Geometry')
        out.write('{')
        out.write('UniqueID %i' % osgt_template_functions.getUniqueId())
        out.write('Name "%s"' % 'TODO: some name here' )
        out.write('DataVariance STATIC')
        
        
        
        
        
        
        #write_geometry_stateset ( out, ctx, drawable )
        
        #write_primitive_set_list( out, drawable )
        #================
        # Write Indices
        #================
        
        elem_array = self.common_factor.value.elem_array
        attr_array = self.common_factor.value.attr_array
        
        out.write('PrimitiveSetList 1')
        out.write('{')
        out.write('DrawElementsUInt GL_TRIANGLES %i' % len( elem_array ) )
        out.write('{')
        
        for triplet in zip(  *[iter( elem_array )]*3 ):
            out.write_item( '% 4i % 4i % 4i' % triplet )
            out.write('')

        out.write('}')
        out.write('}')
        
        #def write_vertex_data( out, drawable ):
        #================
        # Write vertices
        #================
        coordinates = attr_array['co']

        out.write('VertexData')
        out.write('{')
        out.write('Array TRUE ArrayID %i Vec3fArray %i' % ( osgt_template_functions.getUniqueId(), len( attr_array ) ) )
        out.write('{')
        for co in coordinates:
            out.write_item( '% 12.8f % 12.8f % 12.8f ' % tuple(co) )
            out.write('')
        out.write('}')

        out.write('Indices FALSE')
        out.write('Binding BIND_PER_VERTEX')
        out.write('Normalize 0')

        out.write('}')

        #def write_normal_data( out, drawable ):
        #================
        # Write Normals
        #================

        normals = attr_array['no']

        out.write('NormalData')
        out.write('{')
        out.write('Array TRUE ArrayID %i Vec3fArray %i' % ( osgt_template_functions.getUniqueId(), len( attr_array ) ) )
        out.write('{')
        for no in normals:
            out.write_item( '% 12.8f % 12.8f % 12.8f ' % tuple(no) )
            out.write('')
        out.write('}')

        out.write('Indices FALSE')
        out.write('Binding BIND_PER_VERTEX')
        out.write('Normalize 0')

        out.write('}')
        # normals
        
        
        for field_name in attr_array.dtype.names:
            if field_name.startswith('col'):
                write_color_data( out, attr_array[ field_name ] )
                break # write only one set for now

        uv_fields = [ field_name for field_name in attr_array.dtype.names if field_name.startswith('uv') ]
        
        if len( uv_fields ) > 0:
            out.write('TexCoordData %i' % len(uv_fields) )
            out.write('{')
            for field_name in uv_fields:
                if field_name.startswith('uv'):
                    write_texcoord_data( out, attr_array[ field_name ] )
                    #break # write only one set for now
            out.write('}')
            
        
        #=============
        # Custom Data
        #=============
        
        vertex_float_fields = [ attr_array[field_name] for field_name in attr_array.dtype.names if field_name.startswith('vertex_float') ]
        
        
        out.write( 'VertexAttribData %i' % ( len( vertex_float_fields ) + 10 ) )
        out.write( '{' )
        for i in range( 10 ):
            out.write('Data')
            out.write('{')
            out.write('Array FALSE')
            out.write('Indices FALSE')
            out.write('Binding BIND_OFF')
            out.write('Normalize 0')
            out.write('}')
        for vertex_field in vertex_float_fields:
            num_components = vertex_field.shape[1]
            if num_components == 4:
                out.write('Data')
                out.write('{')
                out.write('Array TRUE ArrayID %i Vec4fArray %i' % ( osgt_template_functions.getUniqueId(), len( vertex_field ) ) )
                out.write('{')
                for val in vertex_field:
                    out.write_item( '% 12.8f % 12.8f % 12.8f  % 12.8f ' % tuple(val) )
                    out.write('')
                out.write('}')

                out.write('Indices FALSE')
                out.write('Binding BIND_PER_VERTEX')
                out.write('Normalize 0')
                out.write('}')
            else:
                raise( RuntimeError('Unsupported vector dimensionality') )
            
        out.write( '}' ) # VertexAttribData
        
        
        
        out.write('}')  # osg::Geometry






def printTree( node, trunk, stem ):
    
    print(''.join( trunk[1:] + [stem]), end='')
    print( node.dot, node.common_factor )
    
    
    if stem == '├──':
        trunk.append('│  ')
    else:
        trunk.append('   ')
    
    if len( node.children ) == 1:
        for child in node.children:
            printTree( child, trunk, '└──' )
        
    elif len( node.children ) > 1:
        for child in node.children[0:-1]:   # all but last element
            printTree( child, trunk, '├──' )
            
        for child in node.children[-1:]:    # last element
            printTree( child, trunk, '└──' )
    trunk.pop()



class TreeSimplifier:
    def __init__( self, source_table ):
        self.table    = source_table
        self.n_levels = len( self.table[0] )
    
    def _group_sub_tree( self, rows, level ):
        #--------------------------------
        # 1. find common factor
        # 2. place it first on every row
        # 3. group rows by this factor
        # 4. recurse every group
        #--------------------------------
        
        # 1. find common factor
        values = []
        for row in rows:
            for i in range( level, len( row ) ):
                values.append( row[i] )
        
        common_factors = [ i for i in  Counter( values ).most_common() ]
        
        #print(' common_factors:')
        #for cf in common_factors:
        #    print('   ', cf)
        
        # sort by primary priority, count, then by secondary priority
        common_factors.sort( key=lambda x: ( x[0].primary_sort_priority, x[1], x[0].secondary_sort_priority ), reverse=True )
        
        #print(' sorted common_factors:')
        #for cf in common_factors:
        #    print('   ', cf)
        
        common_factor      = common_factors[0][0]
        common_factor_type = common_factor.type
        
        #print( 'using common factor:', common_factor )
        #print( 'common factor type:',  common_factor_type )
        
        # 2. place it first on every row
        for row in rows:
            for i in range( level, len( row ) ):
                if row[i].type == common_factor_type:
                    row[i], row[level] = row[level], row[i]
                    break # assume there's only one value of each type
        
        # 3. group rows by this factor
        rows.sort( key=lambda r: (r[level].type, r[level].key) )
        
        #for row in rows:
        #    print( 'row:   ', row )
        
        return_nodes = []
        
        if level < self.n_levels - 1:
            #for key, g in groupby( rows, key=lambda r: (r[level].type, r[level].key) ): # group by common factor key
            for key, g in groupby( rows, key=lambda r: r[level] ):
                sub_rows = [ r for r in g ]
                
                #print('    ' * level + 'level %i subrows' % (level+1) )
                #for row in sub_rows:
                #    print('    ' + '    ' * level + str(row) )
                
                node = Node( key )
                for child in self._group_sub_tree( sub_rows, level + 1 ):
                    node.add( child )
                return_nodes.append( node )
        else:
            geode = Geode( 'Geode' ) # pack all leaf nodes into geode node ( LEAVES MUST BE DRAWABLES )
            for row in rows:
                child = DrawableNode( row[ level ] )
                geode.add( child )
            return_nodes.append( geode )
        
        #super_node.add( node )
        #return node
        return return_nodes
    
    def simplify(self):
        root = Root( None )    # put dummy element as root
        
        for child in self._group_sub_tree( self.table, 0 ):
            root.add( child )
        return root







class ObjectPropertyRequest:
    def __init__( self, name, datatype, num_elements, default_value ):
        self.name           = name
        self.datatype       = datatype
        self.num_elements   = num_elements
        self.default_value  = default_value
        

class ExportSourceSetup:
    def __init__( self, shader_name,
                        attributes,
                        groupby,
                        mesh_textures,
                        material_textures,
                        object_property_requests,
                        weld_tolerance
                        ):
        self.shader_name                = shader_name
        self.attributes                 = attributes
        self.groupby                    = groupby
        self.mesh_textures              = mesh_textures
        self.material_textures          = material_textures
        self.object_property_requests   = object_property_requests
        self.weld_tolerance             = weld_tolerance


        
class TextureExportList( OrderedDict ):
    
    def __repr__( self ):
        ret = 'TextureExportList:\n'
        #for name, values in self.items():
        #    ret += '    %30s: %s\n' % ( name, ' '.join([ i.name if i else '-' for i in values ]) )
        for name, image in self.items():
            ret += '    %30s: %s\n' % ( name, image.name if image else '-' )
        return ret
        
        
        
class OsgtExporter:

    def _construct_texture_list( self ):
        ret = []
        for field in self.pro.uni_fields:
            if field.startswith('tex'):
                ret.append( field )
        for mtex_request in self.export_source_setup.material_textures:
            ret.append( mtex_request )
        return ret
    
    

    def _write_osgt( self,  out, AEU ):
        print('\n--- writing osgt --------------------\n')

        attr_arrays  = [ i.attr_array    for i in AEU ]
        elem_arrays  = [ i.element_array for i in AEU ]
        uniform_sets = [ i.uniform_set   for i in AEU ]
        
        #==========================================================================
        ptr_to_image    = { i.as_pointer():i for i in bpy.data.images    }
        ptr_to_material = { m.as_pointer():m for m in bpy.data.materials }
        #--------------------------------------------------------------------------
        ptr_to_image[0]     = None
        ptr_to_material[0]  = None
        #==========================================================================
        
        texture_export_list = TextureExportList()
        
        #================================
        # Initialize texture export list
        #================================
        for name in self.export_source_setup.mesh_textures:
            print( 'tex:::', name )
            tex_target_name = name.split(':')[2]
            texture_export_list[ tex_target_name ] = None
        #================================
        for uni_name in self.export_source_setup.material_textures:
            print( 'uni_name:::', uni_name )
            tex_target_name = uni_name.split(':')[2]
            texture_export_list[ tex_target_name ] = None
        #================================
        
        #used_images = ptr_to_image()
        
        
        
        #print( imageExportManager )
        
        for texture_target in texture_export_list.keys():
            imageExportManager.add_default_image( texture_target )
        
        print('-------------------')
        print( texture_export_list )
        print('+++++++++++++++++++')
        
        print( uniform_sets[0].dtype )
        
        assert( len(attr_arrays) == len(elem_arrays) == len(uniform_sets) )
        L = len( attr_arrays )
        
        
        
        
        
        #==================
        # rewrite uniforms
        #==================
        uniform_tree_rows = []
        for i in range( L ):
            
            tree_row = []
            for u in range( len( uniform_sets[i] ) ):
                field_name    = uniform_sets[i].dtype.names[u]
                uniform_value = uniform_sets[i][u]
                
                if field_name.startswith('tex'):
                    image = ptr_to_image[ uniform_value ]
                    tex_target_name = field_name.split(':')[1]
                    export_image = texture_export_list.copy()
                    #print( 'sdklfjghlsdijgklsdfgbksdlgbklsdgn', 'field:', field_name, '   tex_target_name:', tex_target_name )
                    export_image[ tex_target_name ] = image
                    imageExportManager.add_image( image )
                    tree_row.append( UniformTreeElement( field_name, uniform_value, 0, 2, repr=image.name if image else 'N/A', value=export_image ) )
                    
                elif field_name == '_mat_index':
                    material = ptr_to_material[ uniform_value ]
                    # fill in export image table
                    export_image = texture_export_list.copy()
                    
                    if material is not None:
                        for uni_name in self.export_source_setup.material_textures:
                            tex_target_name = uni_name.split(':')[2]
                            slot_number     = int( uni_name.split(':')[1] )
                            if slot_number < len( material.texture_slots ) and material.texture_slots[ slot_number ] is not None:
                                image = material.texture_slots[ slot_number ].texture.image
                                export_image[ tex_target_name ] = image
                                imageExportManager.add_image( image )
                    
                    tree_row.append( UniformTreeElement( field_name, uniform_value, 0, 1, repr=material.name if material else 'N/A', value=(material, export_image) ) )
                
                elif field_name == 'major_axis':
                    tree_row.append( UniformTreeElement( field_name, uniform_value, -2, 0, repr='major_axis(%i)' % uniform_value, value=uniform_value ) )
                    
                elif field_name == '_obj_index':
                    #tree_row.append( UniformTreeElement( field_name, uniform_value, 0, 0, repr='obj_index(%i)' % uniform_value, value=uniform_value) )
                    tree_row.append( UniformTreeElement( field_name, 0, 2, 0, repr='obj_index(irrelevant)', value=None) )
                
                elif field_name == 'cubic_cell':
                    val = tuple( uniform_value[:] )
                    tree_row.append( UniformTreeElement( field_name, val, 0, 0, repr='cubic_cell:%s' % str(val), value=val ) )
                
                else:
                    raise RuntimeError('Unsupported uniform type')
            
            tree_row.append( UniformTreeElement( 'prim', i, -10, -10, repr='leaf', value=DrawableData( attr_arrays[i], elem_arrays[i] ) ) )
            
            uniform_tree_rows.append( tree_row )
        
        
        
        #=======================
        # simplify uniform tree
        #=======================
        
        
        simp = TreeSimplifier( uniform_tree_rows )
        root = simp.simplify()
        
        print('-----------------------------------------------')
        print()
        printTree( root, [' '], '   ' )
        print()
        print('-----------------------------------------------')
        
        
        print('Exported images =======================================')
        for image, export_image in imageExportManager.items():
            print( 'image: %30s -> %20s (id:%i)' % ( image.name, export_image.export_name, export_image.unique_id ) )
        print('=======================================================')
        
        root.value = ( texture_export_list, self.export_source_setup.shader_name )
        
        root.defined_textures = [ texture_export_list ]
        
        root.write( out )
        


    #==============================================================================
    def __init__( self, reference_matrix, export_group_name, export_source_setup ):
        self.reference_matrix       = reference_matrix
        self.export_group_name      = export_group_name
        self.export_source_setup    = export_source_setup

        self.objects               = []
        self.per_object_properties = []


    def feed_object( self, object, per_object_properties ):
        assert( type( per_object_properties) == list )

        self.objects.append(               object )
        self.per_object_properties.append( per_object_properties )

    def run( self ):
        for i in range( 6 ):
            print( ' ' * i + '\\' )
        msg = 'Exporting "%s"' % self.export_group_name
        print('-' * len(msg))
        print(msg)
        print('-' * len(msg))
        
        self.valid = False
        self.pro = MeshDataProcessor()
        self.export_source_setup = self.export_source_setup
        
        # Perform sanity check
        for o in self.objects:
            assert( o.type == 'MESH' )
        
        self.AEU = self.pro.run(    objects                 = self.objects,
                                    per_object_properties   = self.per_object_properties,
                                    export_source_setup     = self.export_source_setup,
                                    reference_matrix        = self.reference_matrix,
                                    use_shared_vertex_data  = False
                                    )
        self.valid = True


    
    def save( self, basename, output_directory ):
        t = Traverser( open( output_directory + '/' + basename + '.osgt', 'w') )
        
        try:
            self._write_osgt( t, self.AEU )
        except:
            t.out.close()
            raise

        t.out.close()
        
        
        #=======
        last_time_tuples = []
        try:
            txt = open( output_directory + '/used_textures.txt', 'r' )
            last_time_tuples = [ tuple( l.strip().split(':') ) for l in txt.readlines() ]
            txt.close()
            del txt
        except:
            pass
        last_time_hashes = { tex_name : tex_hash for tex_name, tex_hash in last_time_tuples }
        del last_time_tuples
        #=======
        
        
        
        txt = open( output_directory + '/used_textures.txt', 'w' )
        for image, export_image in imageExportManager.items():
            export_name = export_image.export_name
            image_install_path = output_directory + '/' + export_name
            new_hash = str( hash( image.pixels[:] ) )
            if last_time_hashes.get( export_name, None ) != new_hash:
                print( 'saving texture image: %s' % image_install_path )
                image.save_render( filepath=image_install_path )
            else:
                # print( 'SKIP: "%s"' % export_name )
                pass
            txt.write( export_name + ':' + new_hash + '\n' )
        # default textures
        for _, export_image in imageExportManager.default_textures.items():
            export_name = export_image.export_name
            image_install_path = output_directory + '/' + export_name
            new_hash = str( hash( export_image.image.pixels[:] ) )
            if last_time_hashes.get( export_name, None ) != new_hash:
                print( 'saving texture image: %s' % image_install_path )
                export_image.image.save_render( filepath=image_install_path )
            else:
                # print( 'SKIP: "%s"' % export_name )
                pass
            txt.write( export_name + ':' + new_hash + '\n' )
        txt.close()
        
        print()
        print()
        print('Closing output stream')

        
        
        
        