import os
import imp
import bpy
from itertools import chain, groupby
from collections import OrderedDict, Counter
from numpy import *
from collections import namedtuple


import MeshDataProcessor
imp.reload( MeshDataProcessor )
from MeshDataProcessor import MeshDataProcessor, printArray

PLAIN = 1



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

#TODO: MAKE CLASS
def get_next_texture_cascade_level( cascade ):
    for k, v in locally_defined_textures.items():   # replace stack states with local states
                assert( k in self.defined_textures[-1].keys() )
                if v != None:
                    self.defined_textures[-1][k] = v
                

class ID_COUNTER:
    def __init__(self):
        self.id = 0

    def __call__(self):
        self.id += 1
        return self.id

    def reset(self):
        self.id = 0



class Traverser:
    def __init__(self, out):
        self.indent     = 0
        self.out        = out
        self.first_item = True

    def _ascend(self):
        self.indent += 1

    def _descend(self):
        self.indent -= 1

    def write( self, line ):
        if line == '}':
            self._descend()

        if line != '':
            self.out.write('    ' * self.indent)
        self.out.write( line )
        self.out.write( '\n' )
        self.first_item = True
        if line == '{':
            self._ascend()
        pass

    def write_item( self, line ):
        if self.first_item:
            self.out.write('    ' * self.indent)
        self.first_item = False
        self.out.write( line )
        pass


class UniformProperty:

    arraytype_table = {    'i4':     'IntArray',
                            'f4':    'FloatArray',
                            #'vec3f': 'FloatArray',
                            }
    datatype_table  = {    'i4':     'INT',
                            'f4':    'FLOAT',
                            #'vec3f': 'FLOAT',
                            }
    
    def __init__( self, _name, _type, _value ):
        self.name   = _name
        self.type   = _type
        #self.value  = _value
        
        #print( '_value:', _value )
        v = _value
        try:
            v = tuple( i for i in _value )
            #print( 'try: v:', _value )
        except:
            pass
        
        self.value  = v
        if type( v ) != tuple:
            self.value = ( v, )
        
        
        #print( 'UniformProperty.name:',  self.name  )
        #print( 'UniformProperty.type:',  self.type  )
        #print( 'UniformProperty.value:', self.value )
        
        
        #if type( self.value ) == int:       self.value = [ float(self.value) ]
        #if type( self.value ) == float:     self.value = [ float(self.value) ]
        #if type(_value) == ndarray:
        #    self.value = tuple( float(i) for i in _value )
        #else:
        #    self.value = [ float( _value ) ]
        #print('sodfksfn: ', type( self.value ) )
        #if type( self.value ) == tuple:
        #    for i in self.value:
        #        print('    ksfn: ', type( i ) )
        
        #print( self.value )
        #assert( type( self.value ) == list )
        
        self.arraytype     = self.arraytype_table[ self.type ]
        self.datatype      = self.datatype_table[ self.type ]
        
        if len( self.value ) > 1:
            self.datatype = '%s_VEC%i' % ( self.datatype, len( self.value ) )
        
        
        
    
    def get_arraytype( self ):
        return self.arraytype
        
    def get_datatype( self ):
        return self.datatype
    
    def get_num_elements( self ):
        return len( self.value )
    
    def get_elements( self ):
        #print( self.value )
        return self.value
        
    def get_name( self ):
        return self.name


getUniqueId  = None

DrawableData = namedtuple( 'DrawableData',     ['attr_array', 'elem_array']          )
ExportImage  = namedtuple( 'ExportImage',      ['image', 'export_name', 'unique_id'] )

ExportImageFormatExtensions = { 'JPEG':'.jpg',
                                'PNG':'.png',
                                }

class ImageExportManager( OrderedDict ):
    
    def __init__( self, old_export_format, export_format ):
        self.old_export_format = old_export_format
        self.export_format     = export_format
        #self.image_ext         = '.' + self.export_format.lower()
        self.export_names_dict = {}
        
        bpy.context.scene.render.image_settings.file_format = self.export_format
        
        getUniqueId.reset() # XXX: should be elsewhere
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
    
    def __del__(self):
        bpy.context.scene.render.image_settings.file_format = self.old_export_format
    
    def add_default_image( self, texture_target_str ):
        EXT = ExportImageFormatExtensions[ self.export_format ]
        print('###########################: add_default_image: ', texture_target_str )
        if 'normal' in texture_target_str:
            self.default_textures[ texture_target_str ] = ExportImage( bpy.data.images['default_normal'], 'default_normal'+EXT, getUniqueId() )
        else:
            self.default_textures[ texture_target_str ] = ExportImage( bpy.data.images['default'], 'default'+EXT, getUniqueId() )
    
    def getExportName( self, image ):
        return self[ image ].export_name
    
    def get_default_image( self, texture_target_str ):
        return self.default_textures[texture_target_str]
    
    def add_image( self, image ):
        EXT = ExportImageFormatExtensions[ self.export_format ]
        if image != None and image not in self:
            export_name = image.name
            if '.' in image.name and image.name[-4] == '.' and '.' not in image.name[-3:]:
                export_name = image.name[:-4]
                
            added_image_export_name = ('%s'+EXT) % (export_name)
            if added_image_export_name in self.export_names_dict:
                conflicting_image_a = self.export_names_dict[added_image_export_name]
                conflicting_image_b = image
                raise RuntimeError('ERROR: image "%s" will be exported with the same name as image "%s"' % (conflicting_image_a,conflicting_image_b))
            self.export_names_dict[ added_image_export_name ] = image
            self[ image ] = ExportImage( image, added_image_export_name, getUniqueId() )
            print(' +++: adding image: %30s --> %s' % ( image.name, self[image].export_name ) )
        


imageExportManager = None



class UniformTreeElement(dict):
    def __init__( self, type, key, primary_sort_priority, secondary_sort_priority, repr ):
        super().__init__()
        self.type                       = type
        self.key                        = key
        self.primary_sort_priority      = primary_sort_priority
        self.secondary_sort_priority    = secondary_sort_priority
        self.repr                       = repr
        
        self['material']    = None
        self['textures']    = None
        self['properties']  = {}
    
    def set_property( self, name, state ):
        self['properties'][name] = state
    
    def __repr__( self ):
        return '(%s)' % ( self.repr )
    
    def __eq__( self, other ):   # for Counter
        return (self.type, self.key) == (other.type, other.key)
        
    def __hash__( self ):   # for Counter
        return hash( ( self.type, self.key ) )




class Node:
    def __init__( self, uniform_tree_element ):
        self.mergeable  = True
        self.children   = []
        self.state      = uniform_tree_element
        self.dot        = 'o'
        
        assert( type( uniform_tree_element ) == UniformTreeElement )
        
        if type( self.state ) == str:
            self.dot == self.state
        elif type( self.state ) == UniformTreeElement:
            if self.state.type == '_obj_index':
                self.dot = '_'
            elif self.state.type == 'material':
                self.dot = 'M'
            elif self.state.type.startswith('tex'):
                self.dot = 'm'
            
    def add( self, node ):                  
        self.children.append( node )
    
    def _merge( self, other ):
        # print( 'merging: %s %s' % ( self, other ) )
        self.dot        += other.dot
        self.state.repr += ' ' + other.state.repr
        
        assert( self.state['material'] == None or other.state['material'] == None )
        
        # merge material ( that is, make sure only other one or the other has material definition and use that )
        self.state['material'] = self.state['material'] or other.state['material']
        
        # merge textures
        if ( self.state['textures'] != None and other.state['textures'] != None ):
            print('self:',self.state['textures'])
            print('other:',other.state['textures'])
            self.state['textures'].merge( other.state['textures'] )
        elif ( self.state['textures'] == None and other.state['textures'] == None ):
            pass
        else:
            self.state['textures'] = self.state['textures'] or other.state['textures']
        
        # merge properties
        for k, v in other.state['properties'].items():
            assert( k not in self.state['properties'] )
            self.state['properties'][k] = v
            
        
    
    def collapse_singular_branches( self ):
        
        for c in self.children:
            c.collapse_singular_branches()
        
        for i, c in enumerate( self.children ):
            if len( c.children ) == 1:
                cc = c.children[0]
                if not ( cc.mergeable and c.mergeable ):
                    continue
                
                c.children = cc.children
                cc._merge( c )
                self.children[i] = cc
                
        #if len( self.children ) == 1:
        #    c = self.children[0]
        #    if self.mergeable and c.mergeable:
        #        self.children = c.children  # replace children
        #        self._merge( c )
    
    
    def _write_material_attributes( self, out ):
    
        m = self.state['material']
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
        
        
        #==========
        # ModeList
        #==========
        modelist = []
        
        if m.game_settings.use_backface_culling == True:
            modelist.append('GL_CULL_FACE ON')
        else:
            modelist.append('GL_CULL_FACE OFF')
        
        if m.invert_z:
            modelist.append('GL_DEPTH_TEST OFF')
        
        if m.offset_z != 0.0:
            modelist.append('GL_POLYGON_OFFSET_POINT ON|OVERRIDE')
            modelist.append('GL_POLYGON_OFFSET_LINE  ON|OVERRIDE')
            modelist.append('GL_POLYGON_OFFSET_FILL  ON|OVERRIDE')
        
        out.write('ModeList %i' % len(modelist) )
        out.write('{')
        for mode in modelist:
            for line in ( line.strip() for line in mode.splitlines() if len( line ) > 0 ):
                out.write( line )
        out.write('}')
        
        
        #===============
        # AttributeList
        #===============
        attribute_list = []
        
        if 'GL_WRITE_DEPTH' in m:
            if m['GL_WRITE_DEPTH'] == 0:
                attribute_list.append('''
                    osg::Depth
                    {
                    UniqueID %i
                    WriteMask FALSE
                    }
                    Value OFF''' % getUniqueId())
        
        if m.game_settings.alpha_blend == 'ADD':
            attribute_list.append('''
                osg::BlendFunc
                {
                UniqueID %i
                SourceRGB SRC_ALPHA
                SourceAlpha ONE
                DestinationRGB ONE
                DestinationAlpha ONE 
                }
                Value OFF''' % getUniqueId())
        elif m.game_settings.alpha_blend == 'ALPHA':  # interpret this as "multiply mode"
            #SourceRGB ONE
            #SourceAlpha ONE
            #DestinationRGB SRC_COLOR
            #DestinationAlpha ONE
            attribute_list.append('''
                osg::BlendFunc
                {
                UniqueID %i
                SourceRGB DST_COLOR
                SourceAlpha ONE
                DestinationRGB ZERO
                DestinationAlpha ONE_MINUS_SRC_ALPHA
                }
                Value OFF''' % getUniqueId())
        else:
            attribute_list.append('''
                osg::BlendFunc
                {
                UniqueID %i
                SourceRGB SRC_ALPHA
                SourceAlpha ONE
                DestinationRGB ONE_MINUS_SRC_ALPHA
                DestinationAlpha ONE
                }
                Value OFF''' % getUniqueId())
        
        if m.offset_z != 0.0:
            attribute_list.append('''
                osg::PolygonOffset 
                {
                    UniqueID %i
                    Factor 10.0 
                    Units %f
                }
                Value OFF|OVERRIDE''' % ( getUniqueId(), m.offset_z ) )
        if 1:
            a = []
            a.append('osg::Material')
            a.append('{')
            a.append('UniqueID %i' % getUniqueId())
            a.append('Ambient   TRUE Front % 5.3f % 5.3f % 5.3f 1      Back % 5.3f % 5.3f % 5.3f 1'      % (0,0,0,0,0,0))
            a.append('Diffuse   TRUE Front % 5.3f % 5.3f % 5.3f % 5.3f Back % 5.3f % 5.3f % 5.3f % 5.3f' % ((diffuse_color+(alpha,))*2))
            a.append('Specular  TRUE Front % 5.3f % 5.3f % 5.3f 1      Back % 5.3f % 5.3f % 5.3f 1'      % (specular_color*2))
            a.append('Emission  TRUE Front % 5.3f % 5.3f % 5.3f 1      Back % 5.3f % 5.3f % 5.3f 1'      % (emit*2))
            a.append('Shininess TRUE Front % 5.3f Back % 5.3f' % (shininess, shininess))
            a.append('}')
            a.append('Value OFF')
            attribute_list.append( '\n'.join(a) )
            del a
        
        out.write('AttributeList %i' % len( attribute_list ) )
        out.write('{')
        for attribute in attribute_list:
            for line in ( line.strip() for line in attribute.splitlines() if len( line ) > 0 ):
                out.write( line )
        out.write('}') # AttributeList
        
    def _write_texture_attribute_list( self, out, texture_cascade ):
        
        export_texture = texture_cascade.get_textures()
        
        L = sum([ 1 if image != None else 0 for image, _ in export_texture.items() ])
        L = 0
        for target_name, image in export_texture.items():
            if image:
                L += 1
        out.write('TextureAttributeList %i' % ( len( export_texture.keys() ) ) )
        out.write('{')
        
        #XXX: Root.write_texture_order_state needs equivalent sort as used in next line ( otherwise textures are out of sync with each other )
        for target_name, image in sorted( export_texture.items(), key=lambda target: ('normal' not in target[0], target[0]) ):
        #for target_name, image in export_texture.items():
            if image:   out.write('Data 1 { osg::Texture2D { UniqueID %i } Value OFF }' % imageExportManager[image].unique_id )
            else:       out.write('Data 1 { osg::Texture2D { UniqueID %i } Value OFF }' % imageExportManager.get_default_image( target_name ).unique_id )
                
        out.write('}') # TextureAttributeList ends
    
    
    def _write_uniformlist( self, out ):
        
        properties          = sorted( [ i for i in self.state['properties'].values() ], key=lambda prop: prop.name )
        n_custom_properties = len( properties )
        
        out.write('UniformList %i' % ( n_custom_properties ) )
        out.write('{')
        
        for prop in properties:
            out.write('osg::Uniform')
            out.write('{')
            out.write('UniqueID %i' % getUniqueId())
            out.write('Name "%s"' % prop.get_name() )
            out.write('Type %s' % prop.get_datatype() )
            out.write('NumElements 1')
            out.write('Elements TRUE ArrayID %i %s %i' % ( getUniqueId(), prop.get_arraytype(), prop.get_num_elements() ) )
            out.write('{')
            for e in prop.get_elements():
                out.write( '%5.3f' % e )
            out.write('}')
            out.write('}')
            out.write('Value OFF')
        
        out.write('}') # UniformList
    
    def _write_renderbin( self, out ):
        m = self.state['material']
        if m == None or m.pass_index == 0:
            return
        
        pass_index = m.pass_index
        if m.game_settings.alpha_blend != 'OPAQUE':
            pass_index = max( pass_index, 11000 )
        
        out.write('RenderBinMode USE_RENDERBIN_DETAILS')
        out.write('BinNumber %i' % pass_index )
        out.write('BinName "DepthSortedBin"')
        
        
    def _write_stateset( self, out, texture_cascade ):
        out.write('StateSet TRUE')
        out.write('{')
        out.write('osg::StateSet')
        out.write('{')
        out.write('UniqueID %i' % getUniqueId())
        out.write('Name "generic_stateset"')
        out.write('DataVariance STATIC')
        
        #==========
        # Material
        #==========
        if self.state['material'] != None:
            self._write_material_attributes( out )
            
        #==========
        # Textures
        #==========
        if self.state['textures'] != None:
            out.write('TextureModeList 1 { Data 1 { GL_TEXTURE_2D ON } }')
            self._write_texture_attribute_list( out, texture_cascade )
        
        #==========
        # Uniforms
        #==========
        if self.state['properties'] and len( self.state['properties'] ) > 0:
            self._write_uniformlist( out )
        
        #============
        # Render Bin
        #============
        self._write_renderbin( out )
        
        out.write('}') # osg::StateSet
        out.write('}') # StateSet TRUE

    def write( self, out, texture_cascade ):        
        if self.state['textures']:
            texture_cascade.push( self.state['textures'] )
        
        out.write('osg::Group')
        out.write('{')
        out.write('UniqueID %i' % getUniqueId())
        
        self._write_stateset( out, texture_cascade )
            
        # write children
        out.write('Children %i' % len( self.children ) )
        out.write('{')
        for c in self.children:
            c.write( out, texture_cascade )
            
        out.write('}')  # children
        out.write('}')  # this group
        
        if self.state['textures']:
            texture_cascade.pop()


        
class Root( Node ):
    def __init__( self, uniform_tree_element ):
        super().__init__( uniform_tree_element )
        self.mergeable  = False # override
        self.dot = 'r'
    
    def write_texture_definitions( self, out ):

        out.write('osg::Group')
        out.write('{')
        out.write('UniqueID %i' % getUniqueId())
        
        out.write('StateSet TRUE')
        out.write('{')
        out.write('osg::StateSet')
        out.write('{')
        out.write('UniqueID %i' % getUniqueId())
        out.write('Name "texture_definitions"')
        out.write('DataVariance STATIC')
        
        if 1:
            out.write('TextureModeList 1 { Data 1 { GL_TEXTURE_2D ON } }')
        
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
            out.write('UniqueID %i' % getUniqueId())
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
    
    def write_texture_order_state( self, out, texture_cascade ):
        
        texture_list = texture_cascade.get_textures()
        
        out.write('StateSet TRUE')
        out.write('{')
        out.write('osg::StateSet')
        out.write('{')
        out.write('UniqueID %i' % getUniqueId())
        out.write('Name "texture_order_state"')
        out.write('DataVariance STATIC')
        
        out.write('ModeList 2')
        out.write('{')
        out.write('GL_CULL_FACE ON')
        #out.write('GL_LIGHTING  ON')
        #out.write('GL_NORMALIZE OFF|OVERRIDE')
        out.write('GL_BLEND ON')
        #out.write('GL_POLYGON_OFFSET_POINT ON')
        #out.write('GL_POLYGON_OFFSET_LINE ON')
        #out.write('GL_POLYGON_OFFSET_FILL ON')
        #out.write('GL_DEPTH_TEST OFF')
        out.write('}')
        
        out.write('TextureAttributeList %i' % len( texture_list ) )
        out.write('{')
        
        #XXX: Node._write_texture_attribute_list needs equivalent sort as used in next line ( otherwise textures are out of sync with each other )
        for target, image in sorted( texture_list.items(), key=lambda target: ('normal' not in target[0], target[0]) ):
        #for target, image in texture_list.items():
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
            out.write('UniqueID %i' % getUniqueId())
            out.write('FileName "%s"' % imageExportManager.get_default_image(target).export_name )
            out.write('WriteHint 0 2')
            out.write('DataVariance STATIC')
            out.write('}')
            out.write('}')
            out.write('Value OFF')
            out.write('}')
        out.write('}') # TextureAttributeList ends
        
        out.write('RenderBinMode USE_RENDERBIN_DETAILS')
        out.write('BinNumber %i' % 0 )
        out.write('BinName "DepthSortedBin"')
        
        out.write('}')  # StateSet TRUE
        out.write('}')  # osg::StateSet
        
    def write_userdata( self, out ):
    
        num_userdata = 3
        shader_name  = self.state.get('shader_name', None )
        if shader_name:
            num_userdata += 1
    
        out.write('UserDataContainer TRUE')
        out.write('{')
        out.write('osg::DefaultUserDataContainer')
        out.write('{')
        out.write('UniqueID %i' % getUniqueId())
        out.write('UDC_Descriptions %i' % num_userdata )
        out.write('{')
        if shader_name:
            out.write('"USE_SHADER %s"' % shader_name )
        #out.write('"ALTERNATIVE_SHADER_PATH %s"' % self.state['ALTERNATIVE_SHADER_PATH'] )
        out.write('"USE_BUMP_MAP s_mat_diffuse"')   # ei helvetti
        out.write('"USE_BUMP_SCALE 10.0"')
        out.write('"USE_BUMP_UV_INDEX 0"')
        #out.write('"BIND_VERTEX_ATTRIBUTE_NAME a_soft_light 10"')   #TODO: FIXME!
        out.write('}')
        out.write('}')
        out.write('}')
        
    def write( self, out, texture_cascade ):
        out.write('#Ascii Scene')
        out.write('#Version 78')
        out.write('#Generator OpenSceneGraph 2.9.17')

        out.write('osg::Group')
        out.write('{')
        out.write('UniqueID %i' % getUniqueId())
        
        self.write_userdata( out )
        self.write_texture_order_state( out, texture_cascade )
        
        
        out.write('Children %i' % ( len( self.children ) + 1 ) ) # +1 for texture order state
        out.write('{')
        
        self.write_texture_definitions( out )   # texture order state is a fake child
        
        for c in self.children:
            c.write( out, texture_cascade )
        
        out.write('}')  # children

        out.write('}')  # group



class Geode( Node ):

    def __init__( self, state ):
        super().__init__( state )
        self.dot = 'g'
        self.drawables = []
    
    def add( self, _ ):
        raise RuntimeError('cannot add children to geode. add drawables instead')
    
    def add_drawable( self, drawable ):
        self.drawables.append( drawable )
    
    def write( self, out, texture_cascade ):
        if self.state['textures']:
            texture_cascade.push( self.state['textures'] )
        
        out.write('osg::Geode')
        out.write('{')
        out.write('UniqueID %i' % getUniqueId())
        out.write('Name "NAME_HERE"')
        
        self._write_stateset( out, texture_cascade )
        
        out.write('Drawables %i' % len(self.drawables) )
        out.write('{')
        
        for d in self.drawables:
            d.write( out )
        out.write('}')  # drawables
        
        out.write('}')
        
        if self.state['textures']:
            texture_cascade.pop()
    

        
class DrawableNode( Node ):
    
    def __init__( self, state ):
        super().__init__( state )
        self.mergeable  = False # override
    
    def write_elements( self, out ):
        #================
        # Write Indices
        #================
        elem_array = self.state['elem_array']
        attr_array = self.state['attr_array']
        
        out.write('PrimitiveSetList 1')
        out.write('{')
        out.write('DrawElementsUInt GL_TRIANGLES %i' % len( elem_array ) )
        out.write('{')
        
        for triplet in zip(  *[iter( elem_array )]*3 ):
            out.write_item( '% 4i % 4i % 4i' % triplet )
            out.write('')

        out.write('}')
        out.write('}')

    def write_vertex_data( self, out ):
        #================
        # Write vertices
        #================
        coordinates = self.state['attr_array']['co']

        out.write('VertexData')
        out.write('{')
        out.write('Array TRUE ArrayID %i Vec3fArray %i' % ( getUniqueId(), len( coordinates ) ) )
        out.write('{')
        for co in coordinates:
            out.write_item( '% 12.8f % 12.8f % 12.8f ' % tuple(co) )
            out.write('')
        out.write('}')

        out.write('Indices FALSE')
        out.write('Binding BIND_PER_VERTEX')
        out.write('Normalize 0')

        out.write('}')

    def write_normal_data( self, out ):
        #================
        # Write Normals
        #================
        normals = self.state['attr_array']['no']

        out.write('NormalData')
        out.write('{')
        out.write('Array TRUE ArrayID %i Vec3fArray %i' % ( getUniqueId(), len( normals ) ) )
        out.write('{')
        for no in normals:
            out.write_item( '% 12.8f % 12.8f % 12.8f ' % tuple(no) )
            out.write('')
        out.write('}')

        out.write('Indices FALSE')
        out.write('Binding BIND_PER_VERTEX')
        out.write('Normalize 0')

        out.write('}')

    def write_color_data( self, out, color_array ):
        #==============
        # Write Colors
        #==============

        out.write('ColorData')
        out.write('{')
        out.write('Array TRUE ArrayID %i Vec4fArray %i' % ( getUniqueId(),  len(color_array) ) )
        out.write('{')

        for color in color_array:
            out.write_item( '% 12.8f ' % color[0] )
            out.write_item( '% 12.8f ' % color[1] )
            out.write_item( '% 12.8f ' % color[2] )
            out.write_item( '% 12.8f ' % 1.0 )
            out.write('')
        out.write('}')

        out.write('Indices FALSE')
        out.write('Binding BIND_PER_VERTEX')
        out.write('Normalize 0')
        out.write('}')

    def write_texcoord_data( self, out, uv_array ):
        #================
        # Write UV
        #================

        out.write('Data')
        out.write('{')
        out.write('Array TRUE ArrayID %i Vec2fArray %i' % ( getUniqueId(), len(uv_array) ) )
        out.write('{')
        for uv in uv_array:
            out.write_item( '% 12.8f ' % uv[0] )
            out.write_item( '% 12.8f ' % uv[1] )
            out.write('')
        out.write('}')

        out.write('Indices FALSE')
        out.write('Binding BIND_PER_VERTEX')
        out.write('Normalize 0')

        out.write('}')


    def write( self, out ):
        #if PLAIN:
        #    return
        out.write('osg::Geometry')
        out.write('{')
        out.write('UniqueID %i' % getUniqueId())
        out.write('Name "%s"' % 'TODO: some name here' )
        out.write('DataVariance STATIC')
        
        #================
        # Write Indices
        #================
        self.write_elements( out )
        
        #================
        # Write vertices
        #================
        self.write_vertex_data( out )

        #================
        # Write Normals
        #================
        self.write_normal_data( out )
        
        #================
        # Write Colors
        #================
        attr_array = self.state['attr_array']
        
        for field_name in attr_array.dtype.names:
            if field_name.startswith('col'):
                self.write_color_data( out, attr_array[ field_name ] )
                break # write only one set for now

        uv_fields = [ field_name for field_name in attr_array.dtype.names if field_name.startswith('uv') ]
        
        #================
        # Write UVs
        #================
        if len( uv_fields ) > 0:
            out.write('TexCoordData %i' % len(uv_fields) )
            out.write('{')
            for field_name in uv_fields:
                if field_name.startswith('uv'):
                    self.write_texcoord_data( out, attr_array[ field_name ] )
            out.write('}')
            
        #=============
        # Custom Data
        #=============
        
        vertex_float_fields = [ attr_array[field_name] for field_name in attr_array.dtype.names if field_name.startswith('vertex_float') ]
        
        # out.write( 'VertexAttribData %i' % ( len( vertex_float_fields ) + 10 ) )
        # out.write( '{' )
        # for i in range( 10 ):
            # out.write('Data')
            # out.write('{')
            # out.write('Array FALSE')
            # out.write('Indices FALSE')
            # out.write('Binding BIND_OFF')
            # out.write('Normalize 0')
            # out.write('}')
        # for vertex_field in vertex_float_fields:
            # num_components = vertex_field.shape[1]
            # if num_components == 4:
                # out.write('Data')
                # out.write('{')
                # out.write('Array TRUE ArrayID %i Vec4fArray %i' % ( getUniqueId(), len( vertex_field ) ) )
                # out.write('{')
                # for val in vertex_field:
                    # out.write_item( '% 12.8f % 12.8f % 12.8f  % 12.8f ' % tuple(val) )
                    # out.write('')
                # out.write('}')

                # out.write('Indices FALSE')
                # out.write('Binding BIND_PER_VERTEX')
                # out.write('Normalize 0')
                # out.write('}')
            # else:
                # raise( RuntimeError('Unsupported vector dimensionality') )
            
        # out.write( '}' ) # VertexAttribData
        
        
        
        out.write('}')  # osg::Geometry






def printTree( node, trunk, stem ):
    
    print(''.join( trunk[1:] + [stem]), end='')
    print( node.dot, node.state )
    
    
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
        states = []
        for row in rows:
            for i in range( level, len( row ) ):
                states.append( row[i] )
        
        states = [ i for i in  Counter( states ).most_common() ]
        
        #print(' states:')
        #for cf in states:
        #    print('   ', cf)
        
        # sort by primary priority, count, then by secondary priority
        states.sort( key=lambda x: ( x[0].primary_sort_priority, x[1], x[0].secondary_sort_priority ), reverse=True )
        
        #print(' sorted states:')
        #for cf in states:
        #    print('   ', cf)
        
        state      = states[0][0]
        state_type = state.type
        
        #print( 'using common factor:', state )
        #print( 'common factor type:',  state_type )
        
        # 2. place it first on every row
        for row in rows:
            for i in range( level, len( row ) ):
                if row[i].type == state_type:
                    row[i], row[level] = row[level], row[i]
                    break # assume there's only one state of each type
        
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
            # pack all leaf nodes into geode node ( LEAVES MUST BE DRAWABLES )
            geode = Geode( UniformTreeElement( type='Geode', key=None, primary_sort_priority=None, secondary_sort_priority=None, repr='Geode' ) )
            for row in rows:
                child = DrawableNode( row[ level ] )
                #geode.add( child )
                geode.add_drawable( child )
            return_nodes.append( geode )
        
        #super_node.add( node )
        #return node
        return return_nodes
    
    def simplify( self ):
        ute = ute = UniformTreeElement(     type                    = 'root',
                                            key                     = None,
                                            primary_sort_priority   = None,
                                            secondary_sort_priority = None,
                                            repr                    = 'root',
                                            )
        root = Root( ute )    # put dummy element as root
        
        for child in self._group_sub_tree( self.table, 0 ):
            root.add( child )
        return root
    




class ObjectPropertyRequest:
    def __init__( self, name, datatype, num_elements, default_value ):
        self.name           = name
        self.datatype       = datatype
        self.num_elements   = num_elements
        self.default_value  = default_value
    
    def __repr__( self ):
        return 'ObjectPropertyRequest( %-15s type:%s n:%i, def:%s )' % ( self.name, self.datatype, self.num_elements, self.default_value )

class ExportSourceSetup:
    def __init__( self, shader_name,
                        attributes,
                        groupby,
                        mesh_textures,
                        # node_textures,
                        material_textures,
                        object_property_requests,
                        weld_tolerance,
                        alternative_shader_path = '',
                        export_edges    = False,
                        export_vertices = False,
                        edge_material   = None,
                        vertex_material = None,
                        ):
        self.shader_name                = shader_name
        self.attributes                 = attributes
        self.groupby                    = groupby
        self.mesh_textures              = mesh_textures
        # self.node_textures              = node_textures
        self.material_textures          = material_textures
        self.object_property_requests   = object_property_requests
        self.weld_tolerance             = weld_tolerance
        self.alternative_shader_path    = alternative_shader_path

class TextureExportList( OrderedDict ):
    
    def merge( self, other ):
        #ret = self.copy()
        for k, v in other.items():
            print( 'TRACE:', self[k] )
            assert( k in self )
            assert( self[k] == None or other[k] == None )
            self[k] = self[k] or other[k]

    def __repr__( self ):
        ret = 'TextureExportList:\n'
        #for name, states in self.items():
        #    ret += '    %30s: %s\n' % ( name, ' '.join([ i.name if i else '-' for i in states ]) )
        for name, image in self.items():
            ret += '    %30s: %s\n' % ( name, image.name if image else '-' )
        return ret

class TextureCascade:
    def __init__( self, textures ):
        self.textures = [ textures ]
        assert( type( textures ) == TextureExportList )
    
    def merge( self, other ):
        for k, v in other.textures.items():
            assert( k in self.textures )
            assert( self.textures[k] == None )
            self.textures[k] = v
    
    def push( self, overriding_textures ):
        #print( overriding_textures )
        assert( type( overriding_textures ) == TextureExportList )
        
        self.textures.append( self.textures[-1].copy() )   # make a copy of stack top
        for k, v in overriding_textures.items():
            assert( k in self.textures[-1].keys() ) # override textures
            if v != None:
                self.textures[-1][k] = v
        
    def pop( self ):
        self.textures.pop()
        
    def get_textures( self ):
        return self.textures[-1]
        
        

        
        
        
class OsgtExporter:


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
        
        #print( ptr_to_image )
        
        texture_export_list = TextureExportList()
        
        #================================
        # Initialize texture export list
        #================================
        for name in self.export_source_setup.mesh_textures:
            print( 'tex:::', name )
            tex_target_name = name.split(':')[1]
            texture_export_list[ tex_target_name ] = None
        #================================
        for uni_name in self.export_source_setup.material_textures:
            print( 'uni_name:::', uni_name )
            tex_target_name = uni_name.split(':')[1]
            texture_export_list[ tex_target_name ] = None
        #================================
        #for uni_name in self.export_source_setup.node_textures:
        #    print( 'node_texture:::', uni_name )
        #    tex_target_name = uni_name.split(':')[1]
        #    texture_export_list[ tex_target_name ] = None
        #================================
        
        #used_images = ptr_to_image()
        
        
        #print( imageExportManager )
        
        #NOTE: If osgt graphic has 1x1 pixel transparent default texture, this texture must not
        #      be the first one declared in the texture_order_state.
        #      We have to sort this declaration list so that default normal is declared first.
        #      FIXME: this again does NOT work if model has no normal textures!!
        for texture_target in sorted( texture_export_list.keys(), key=lambda x: ('normal' not in x,x) ): 
            imageExportManager.add_default_image( texture_target )
        
        #print('-------------------')
        #print( texture_export_list )
        #print('+++++++++++++++++++')
        #print( uniform_sets[0].dtype )
        assert( len(attr_arrays) == len(elem_arrays) == len(uniform_sets) )
        L = len( attr_arrays )
        
        
        
        print('#=============================================================================#')
        print('data array dtype:')
        for i, (label, datatype) in enumerate( uniform_sets[0].dtype.fields.items() ):
            print( 'field: %2i' % i, label.ljust(20), datatype[0] )
        for u in uniform_sets:
            print( u )
        
        
        print('#=============================================================================#')
        
        
        #==================
        # rewrite uniforms
        #==================
        uniform_tree_rows = []
        for i in range( L ):
            
            tree_row = []
            for u in range( len( uniform_sets[i] ) ):
                field_name    = uniform_sets[i].dtype.names[u]
                uniform_value = uniform_sets[i][u]
                
                # translate numpy.ndarray into tuple if ndarray is received
                if type( uniform_value ) == ndarray:
                    #TODO: handle integers too
                    uniform_value = tuple( float(i) for i in uniform_value )
                
                
                #================================================================================================================
                # Texture UTE
                #================================================================================================================
                if field_name.startswith('tex'):
                    image = ptr_to_image[ uniform_value ]
                    #print('image = ptr_to_image[ uniform_value ]', image.name, uniform_value)
                    tex_target_name = field_name.split(':')[1]
                    export_image = texture_export_list.copy()
                    
                    export_image[ tex_target_name ] = image
                    imageExportManager.add_image( image )
                    
                    ute = UniformTreeElement(   type                    = field_name, 
                                                key                     = uniform_value, 
                                                primary_sort_priority   = 0, 
                                                secondary_sort_priority = 2, 
                                                repr                    = image.name if image else 'N/A'
                                                )
                    ute['textures'] = export_image 
                    assert( export_image != None )
                    tree_row.append( ute )
                    #print('####################', export_image )
                #================================================================================================================
                # Material UTE
                #================================================================================================================
                elif field_name == 'material':
                    extra_properties = []
                    
                    material = ptr_to_material[ uniform_value ]
                    # fill in export image table
                    export_image = texture_export_list.copy()
                    
                    if material is not None:
                        #for uni_name in self.export_source_setup.node_textures:
                        #    if material.node_tree == None:
                        #        raise RuntimeError('Material "%s" was supposed to export node_textures but has no node tree.' % material.name )
                        #    node_name, tex_target_name, tex_role = uni_name.split(':')[0:3]
                        #    if node_name not in material.node_tree.nodes:
                        #        raise RuntimeError('Material "%s" node_tree must have texture node named "%s".' % (material.name, node_name) )
                        #    node = material.node_tree.nodes[ node_name ]
                        #    assert( node.type == 'TEXTURE' )
                        #    image = node.texture.image
                        #    export_image[ tex_target_name ] = image
                        #    imageExportManager.add_image( image )
                        
                        for uni_name in self.export_source_setup.material_textures:
                            slot_number, tex_target_name, tex_role = uni_name.split(':')[0:3]
                            
                            slot_number = int( slot_number )
                            
                            if slot_number < len( material.texture_slots ) and material.texture_slots[ slot_number ] is not None:
                                if tex_role == 'normal':
                                    normal_factor = material.texture_slots[slot_number].normal_factor
                                    prop = UniformProperty( '%s_normal_factor' % ( tex_target_name ), 'f4', normal_factor )
                                    extra_properties.append( prop )
                                    
                                image = material.texture_slots[ slot_number ].texture.image
                                export_image[ tex_target_name ] = image
                                imageExportManager.add_image( image )
                    
                    ute = UniformTreeElement(   type                    = field_name,
                                                key                     = uniform_value, 
                                                primary_sort_priority   = 0,
                                                secondary_sort_priority = 1,
                                                repr                    = material.name if material else 'N/A',
                                                )
                    ute['material'] = material
                    ute['textures'] = export_image
                    
                    material_scale = 1.0
                    gloss_factor   = 0.0
                    reflect_factor = 0.0
                    fresnel_power  = 2.0
                    fresnel_factor = 1.25
                    transmit_color = ( 1.0, 1.0, 1.0 )
                    mirror_color   = ( 1.0, 1.0, 1.0 )
                    translucency   = 0.0
                    invert_z       = 0.0
                    
                    if material is not None:
                        gloss_factor    = material.raytrace_mirror.gloss_factor
                        #reflect_factor  = material.raytrace_mirror.reflect_factor * material.raytrace_mirror.use
                        reflect_factor  = material.raytrace_mirror.reflect_factor
                        fresnel_power   = material.raytrace_mirror.fresnel
                        fresnel_factor  = material.raytrace_mirror.fresnel_factor
                        #transmit_color = material.subsurface_scattering.color
                        transmit_color  = material.mirror_color
                        mirror_color    = material.mirror_color
                        translucency    = material.translucency
                        invert_z        = material.invert_z
                    try:
                        material_scale = material.texture_slots[0].scale.x
                        #gloss_factor     = material
                    except:
                        pass
                    
                    ute.set_property( 'material_scale', UniformProperty( 'material_scale', 'f4', material_scale     ) )
                    ute.set_property( 'gloss_factor',   UniformProperty( 'gloss_factor',   'f4', gloss_factor       ) )
                    ute.set_property( 'reflect_factor', UniformProperty( 'reflect_factor', 'f4', reflect_factor     ) )
                    ute.set_property( 'fresnel_power',  UniformProperty( 'fresnel_power',  'f4', fresnel_power      ) )
                    ute.set_property( 'fresnel_factor', UniformProperty( 'fresnel_factor', 'f4', fresnel_factor     ) )
                    ute.set_property( 'transmit_color', UniformProperty( 'transmit_color', 'f4', transmit_color     ) )
                    ute.set_property( 'mirror_color',   UniformProperty( 'mirror_color',   'f4', mirror_color       ) )
                    ute.set_property( 'translucency',   UniformProperty( 'translucency',   'f4', translucency       ) )
                    ute.set_property( 'invert_z',       UniformProperty( 'invert_z',       'i4', invert_z           ) )
                    for prop in extra_properties:
                        ute.set_property( prop.name, prop )
                    tree_row.append( ute )
                    
                #================================================================================================================
                # Property UTE
                #================================================================================================================
                elif field_name.startswith('prop'):
                    _, property_type, property_name = field_name.split(':')
                    
                    ute = UniformTreeElement(   type                    = field_name,
                                                key                     = uniform_value,
                                                primary_sort_priority   = -1,
                                                secondary_sort_priority = 0,
                                                repr                    = '%s:%s' % ( property_name, str(uniform_value) )
                                                )
                    prop = UniformProperty( property_name, property_type, uniform_value )
                    ute.set_property( property_name, prop )
                    tree_row.append( ute )
                
                #================================================================================================================
                # Object index UTE ( probably shouldn't be used at all )
                #================================================================================================================
                elif field_name == '_obj_index':
                    #assert(0) # obj_index should 
                    #tree_row.append( UniformTreeElement( field_name, uniform_value, 0, 0, repr='obj_index(%i)' % uniform_value, state=uniform_value) )
                    #tree_row.append( UniformTreeElement( field_name, 0, 2, 0, repr='obj_index(irrelevant)', state=None) )
                    ute = UniformTreeElement(   type                    = field_name,
                                                key                     = uniform_value,
                                                primary_sort_priority   = 2,
                                                secondary_sort_priority = 0,
                                                repr                    = '_obj_index:%s' % ( str(uniform_value) )
                                                )
                    prop = UniformProperty( '_obj_index', 'i4', uniform_value )
                    ute.set_property( '_obj_index', prop )
                    tree_row.append( ute )
                    
                    
                    
                
                #================================================================================================================
                # Cubic cell UTE ( used to split geometry into smaller pieces for culling )
                #================================================================================================================
                elif field_name == 'cubic_cell':
                    #val = tuple( uniform_value[:] )
                    #tree_row.append( UniformTreeElement( field_name, val, 0, 0, repr='cubic_cell:%s' % str(val), state=val ) )
                    ute = UniformTreeElement(   type                    = field_name,
                                                key                     = uniform_value,
                                                primary_sort_priority   = 0,
                                                secondary_sort_priority = 0,
                                                repr                    = 'cubic_cell:%s' % ( str(uniform_value) )
                                                )
                    tree_row.append( ute )
                    
                elif field_name == 'dummy':
                    pass # no utes are added for dummy type
                else:
                    raise RuntimeError( 'Unsupported uniform type "%s"' % field_name )
            
            ute = UniformTreeElement(   type                    = 'prim',
                                        key                     = i,
                                        primary_sort_priority   = -10,
                                        secondary_sort_priority = -10,
                                        repr                    = 'leaf',
                                        )
            ute['attr_array'] = attr_arrays[i]
            ute['elem_array'] = elem_arrays[i]
            tree_row.append( ute )
            
            uniform_tree_rows.append( tree_row )    # finalize row
        
        
        
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
        
        
        root.collapse_singular_branches()
        
        print('-----------------------------------------------')
        print()
        printTree( root, [' '], '   ' )
        print()
        print('-----------------------------------------------')
        
        
        print('Exported images =======================================')
        for image, export_image in imageExportManager.items():
            print( 'image: %30s -> %20s (id:%i)' % ( image.name, export_image.export_name, export_image.unique_id ) )
        print('=======================================================')
        
        root.state['shader_name']             = self.export_source_setup.shader_name
        root.state['ALTERNATIVE_SHADER_PATH'] = self.export_source_setup.alternative_shader_path
        
        
        
        texture_cascade = TextureCascade( texture_export_list )
        
        
        root.write( out, texture_cascade )
        


    #==============================================================================
    def __init__( self, reference_matrix, export_group_name, export_source_setup ):
        
        #============================================
        # initialize global objects
        #============================================
        # XXX: REMOVE ALL GLOBAL CLASSES !!!
        # XXX: THEIR STATE IS LEFT HANGING BETWEEN EXPORTS
        global getUniqueId
        global imageExportManager
        getUniqueId         = ID_COUNTER()
        
        #OLD_IMAGE_EXPORT_FORMAT = bpy.context.scene.render.image_settings.file_format
        imageExportManager  = ImageExportManager( bpy.context.scene.render.image_settings.file_format, 'PNG' )
        #bpy.context.scene.render.image_settings.file_format = imageExportManager.export_format
        #============================================
    
        self.reference_matrix       = reference_matrix
        self.export_group_name      = export_group_name
        self.export_source_setup    = export_source_setup

        self.objects                = []
        self.line_objects           = []
        #self.per_object_properties = []
    

    def feed_object( self, object ):
        self.objects.append( object )
        
    def feed_lines( self, object ):
        self.line_objects.append( object )

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
        self.objects = filter( lambda x: x.type=='MESH', self.objects )
        
        self.AEU = self.pro.run(    objects                 = self.objects,
                                    #line_objects            = self.line_objects,
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
        
        
        dependencies = set()
        for image, export_image in imageExportManager.items():
            export_name = export_image.export_name
            image_install_path = output_directory + '/' + export_name
            print( 'saving texture image: %s' % image_install_path )
            image.save_render( filepath=image_install_path )
            dependencies.add( export_name )
        # default textures
        for export_image in set( [i for i in imageExportManager.default_textures.values()] ):
            export_name = export_image.export_name
            image_install_path = output_directory + '/' + export_name
            print( 'saving default texture image: %s' % image_install_path )
            export_image.image.save_render( filepath=image_install_path )
            dependencies.add( export_name )
        
        with open( output_directory + '/%s.osgt.depends' % basename, 'w' ) as txt:
            for export_name in sorted( dependencies ):
                txt.write( export_name + '\n' )
        
        os.system('explorer "%s"' % (os.path.dirname(image_install_path)).replace('/', os.sep) )
        
        
        #=======
        #last_time_tuples = []
        #try:
        #    txt = open( output_directory + '/used_textures.txt', 'r' )
        #    last_time_tuples = [ tuple( l.strip().split(':') ) for l in txt.readlines() ]
        #    txt.close()
        #    del txt
        #except:
        #    pass
        #last_time_hashes = { tex_name : tex_hash for tex_name, tex_hash in last_time_tuples }
        #del last_time_tuples
        #=======
        
        
        
        #txt = open( output_directory + '/used_textures.txt', 'w' )
        #for image, export_image in imageExportManager.items():
        #    export_name = export_image.export_name
        #    image_install_path = output_directory + '/' + export_name
        #    new_hash = str( hash( image.pixels[:] ) )
        #    if last_time_hashes.get( export_name, None ) != new_hash:
        #        print( 'saving texture image: %s' % image_install_path )
        #        image.save_render( filepath=image_install_path )
        #    else:
        #        # print( 'SKIP: "%s"' % export_name )
        #        pass
        #    txt.write( export_name + ':' + new_hash + '\n' )
        ## default textures
        #for _, export_image in imageExportManager.default_textures.items():
        #    export_name = export_image.export_name
        #    image_install_path = output_directory + '/' + export_name
        #    new_hash = str( hash( export_image.image.pixels[:] ) )
        #    if last_time_hashes.get( export_name, None ) != new_hash:
        #        print( 'saving texture image: %s' % image_install_path )
        #        export_image.image.save_render( filepath=image_install_path )
        #    else:
        #        # print( 'SKIP: "%s"' % export_name )
        #        pass
        #    txt.write( export_name + ':' + new_hash + '\n' )
        #txt.close()
        
        #============================================
        # uninitialize global objects
        #============================================
        # XXX: AGAIN: REMOVE ALL GLOBAL CLASSES !!!
        # XXX: THEIR STATE IS LEFT HANGING BETWEEN EXPORTS
        global getUniqueId
        global imageExportManager
        getUniqueId         = None
        imageExportManager  = None
        #============================================
        
        print()
        print()
        print('Closing output stream')

