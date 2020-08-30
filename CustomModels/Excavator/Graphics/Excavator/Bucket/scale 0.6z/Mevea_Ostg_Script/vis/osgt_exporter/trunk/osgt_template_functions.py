import os
import imp
import bpy
from itertools import chain, groupby
from collections import OrderedDict, Counter
from numpy import *
from random import randint

import MeshDataProcessor
imp.reload( MeshDataProcessor )
from MeshDataProcessor import MeshDataProcessor, printArray


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



class ID_COUNTER:
    def __init__(self):
        #print('init ID_COUNTER')
        self.id = 0

    def __call__(self):
        self.id += 1
        #print('yielding ID: %3i' % self.id)
        return self.id

    def reset(self):
        #print('reseting ID_COUNTER')
        self.id = 0

getUniqueId             = ID_COUNTER()


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



def write_drawable( record_data, out ):

    record_data = list( record_data )
    sort_by_data = lambda r: (r.co, r.normal, r.uv, r.color )


    index_rewrite = [ [i,i] for i in range( len(record_data) ) ]
    counter = 0

    record_data.sort(  key=sort_by_data  )

    for k,g in groupby( record_data, key=sort_by_data ):
        for record in g:
            index_rewrite[ record[0] ][0] = record[0]     # set original index
            index_rewrite[ record[0] ][1] = counter       # set new index
        counter += 1


    counter = 0
    optimized_dataset = []
    for k,g in groupby( record_data, key=sort_by_data ):
        for record in g:
            new_record = VertexRecord(  loop_index   = counter,
                                        vertex_index = record.vertex_index,
                                        co           = record.co,
                                        normal       = record.normal,
                                        uv           = record.uv,
                                        color        = record.color,
                                        material     = record.material
                                        )
            optimized_dataset.append( new_record )
            break
        counter += 1

    write_mesh_data( optimized_dataset, index_rewrite, out )


def write_primitive_set_list( out, drawable ):
    #================
    # Write Indices
    #================

    out.write('PrimitiveSetList 1')
    out.write('{')
    out.write('DrawElementsUInt GL_TRIANGLES %i' % len(drawable.index_array) )
    out.write('{')

    for triplet in zip(  *[iter( drawable.index_array )]*3 ):
        out.write_item( '% 4i % 4i % 4i' % triplet )
        out.write('')

    out.write('}')
    out.write('}')

def write_vertex_data( out, drawable ):
    #================
    # Write vertices
    #================
    coordinates = drawable.attr_array['co']

    out.write('VertexData')
    out.write('{')
    out.write('Array TRUE ArrayID %i Vec3fArray %i' % ( getUniqueId(), len( drawable.attr_array ) ) )
    out.write('{')
    for co in coordinates:
        out.write_item( '% 12.8f % 12.8f % 12.8f ' % tuple(co) )
        out.write('')
    out.write('}')

    out.write('Indices FALSE')
    out.write('Binding BIND_PER_VERTEX')
    out.write('Normalize 0')

    out.write('}')

def write_normal_data( out, drawable ):
    #================
    # Write Normals
    #================

    normals = drawable.attr_array['no']

    out.write('NormalData')
    out.write('{')
    out.write('Array TRUE ArrayID %i Vec3fArray %i' % ( getUniqueId(), len( drawable.attr_array ) ) )
    out.write('{')
    for no in normals:
        out.write_item( '% 12.8f % 12.8f % 12.8f ' % tuple(no) )
        out.write('')
    out.write('}')

    out.write('Indices FALSE')
    out.write('Binding BIND_PER_VERTEX')
    out.write('Normalize 0')

    out.write('}')

def write_color_data( out, color_array ):
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


def write_texcoord_data( out, uv_array ):
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


def write_userdata( out, ctx ):
    out.write('UserDataContainer TRUE')
    out.write('{')
    out.write('osg::DefaultUserDataContainer')
    out.write('{')
    out.write('UniqueID %i' % getUniqueId())

    out.write('UDC_Descriptions 4')
    out.write('{')
    #out.write('"USE_SHADER %s/%s"' % ( ctx['output_directory'], ctx['shader_name']) )
    out.write('"USE_SHADER %s"' % ctx['shader_name'] ) # SHADER PATH IS SET HERE
    out.write('"USE_BUMP_MAP s_mat_diffuse"')
    out.write('"USE_BUMP_SCALE 10.0"')
    out.write('"USE_BUMP_UV_INDEX 0"')
    out.write('}')

    out.write('}')
    out.write('}')


def write_geode( out, ctx ):
    out.write('osg::Geode')
    out.write('{')
    out.write('UniqueID %i' % getUniqueId())
    out.write('Name "%s"' % ctx['name'] )

    write_userdata( out, ctx )
    out.write('Drawables %i' % len( ctx['drawables'] ))
    out.write('{')
    for d in ctx['drawables']:
        write_geometry( out, ctx, d )
    out.write('}')
    out.write('}')


def write_file_header( out ):
    out.write('#Ascii Scene')
    out.write('#Version 78')
    out.write('#Generator OpenSceneGraph 2.9.17')
    out.write('')


def write_stateset( out, ctx, uniform ):

    #out.write('############### write_stateset')
    #return

    out.write('StateSet TRUE')
    out.write('{')
    out.write('osg::StateSet')
    out.write('{')
    out.write('UniqueID %i' % getUniqueId())
    out.write('DataVariance STATIC')

    #out.write( '"' + uniform + '"' )
    out.write('ModeList 8')
    out.write('{')
    out.write('GL_CULL_FACE ON')
    out.write('GL_LIGHTING  ON')
    out.write('GL_NORMALIZE OFF|OVERRIDE')
    out.write('GL_BLEND ON')
    out.write('GL_POLYGON_OFFSET_POINT ON')
    out.write('GL_POLYGON_OFFSET_LINE ON')
    out.write('GL_POLYGON_OFFSET_FILL ON')
    out.write('GL_DEPTH_TEST ON')
    out.write('}')

    out.write('}')
    out.write('}')

def write_root_stateset( out, texture_export_list, name ):

    #out.write('############### write_root_stateset')
    #return

    alpha = 1.0
    alpha_blend    = 'OPAQUE'
    diffuse_color  = (1.0, 1.0, 1.0 )
    specular_color = (1.0, 1.0, 1.0 )
    shininess      = 32.0 / 512.0
    emit           = tuple( [0.2] ) * 6

    out.write('StateSet TRUE')
    out.write('{')
    out.write('osg::StateSet')
    out.write('{')
    out.write('UniqueID %i' % getUniqueId())
    out.write('Name "root_state"')
    out.write('DataVariance STATIC')

    out.write('ModeList 8')
    out.write('{')
    out.write('GL_CULL_FACE ON')
    out.write('GL_LIGHTING  ON')
    out.write('GL_NORMALIZE OFF|OVERRIDE')
    out.write('GL_BLEND ON')
    out.write('GL_POLYGON_OFFSET_POINT ON')
    out.write('GL_POLYGON_OFFSET_LINE ON')
    out.write('GL_POLYGON_OFFSET_FILL ON')
    out.write('GL_DEPTH_TEST ON')
    out.write('}') # ModeList 8

    out.write('AttributeList 1')
    out.write('{')

    out.write('osg::Material')
    out.write('{')
    out.write('UniqueID %i' % getUniqueId())
    out.write('Ambient   TRUE Front % 5.3f % 5.3f % 5.3f 1      Back % 5.3f % 5.3f % 5.3f 1'      % (0,0,0,0,0,0)    )
    out.write('Diffuse   TRUE Front % 5.3f % 5.3f % 5.3f % 5.3f Back % 5.3f % 5.3f % 5.3f % 5.3f' % ((diffuse_color+(alpha,))*2)  )
    out.write('Specular  TRUE Front % 5.3f % 5.3f % 5.3f 1      Back % 5.3f % 5.3f % 5.3f 1'      % (specular_color*2) )
    out.write('Emission  TRUE Front % 5.3f % 5.3f % 5.3f 1      Back % 5.3f % 5.3f % 5.3f 1'      % (emit)           )
    out.write('Shininess TRUE Front % 5.3f Back % 5.3f' % (shininess, shininess) )
    out.write('}') # osg::Material
    out.write('Value OFF')
    out.write('}') # AttributeList 1

    out.write('TextureModeList 1')
    out.write('{')
    out.write('Data 1')
    out.write('{')
    out.write('GL_TEXTURE_2D ON')
    out.write('}') # Data 1
    out.write('}') # TextureModeList



    texture_targets = texture_export_list.keys()

    out.write('TextureAttributeList %i' % ( len( texture_targets ) ) )
    out.write('{')
    for target in texture_targets:
        filename = name + '_default.png'
        if 'normal' in target:
            filename = name + '_default_normal.png'

        out.write('Data 1')
        out.write('{')
        out.write('osg::Texture2D')
        out.write('{')
        out.write('UniqueID %i' % getUniqueId())
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
        out.write('FileName "%s"' % filename )
        out.write('WriteHint 0 2')
        out.write('DataVariance STATIC')
        out.write('}')
        out.write('}')
        out.write('Value OFF')
        out.write('}')
    out.write('}') # TextureAttributeList ends

    out.write('}') # osg::StateSet
    out.write('}') # StateSet TRUE


def write_material_stateset( out, ctx, material ):

    #out.write('############### write_material_stateset')
    #return

    m = material

    if m == None:
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
    out.write('UniqueID %i' % getUniqueId())
    out.write('Name "%s.material_state"' % ctx['name'] )
    out.write('DataVariance STATIC')


    out.write('AttributeList 1')
    out.write('{')

    out.write('osg::Material')
    out.write('{')
    out.write('UniqueID %i' % getUniqueId())
    out.write('Ambient   TRUE Front % 5.3f % 5.3f % 5.3f 1      Back % 5.3f % 5.3f % 5.3f 1'      % (0,0,0,0,0,0)    )
    out.write('Diffuse   TRUE Front % 5.3f % 5.3f % 5.3f % 5.3f Back % 5.3f % 5.3f % 5.3f % 5.3f' % ((diffuse_color+(alpha,))*2)  )
    out.write('Specular  TRUE Front % 5.3f % 5.3f % 5.3f 1      Back % 5.3f % 5.3f % 5.3f 1'      % (specular_color*2) )
    out.write('Emission  TRUE Front % 5.3f % 5.3f % 5.3f 1      Back % 5.3f % 5.3f % 5.3f 1'      % (emit*2)           )
    out.write('Shininess TRUE Front % 5.3f Back % 5.3f' % (shininess, shininess) )
    out.write('}')
    out.write('Value OFF')

    out.write('}') # AttributeList 1


    # write mateiral textures

    out.write('TextureModeList 1')
    out.write('{')
    out.write('Data 1')
    out.write('{')
    out.write('GL_TEXTURE_2D ON')
    out.write('}') # Data 1
    out.write('}') # TextureModeList

    #print('material: %s' % m)
    #material_requests = ctx['mtex_requests']
    material_textures = []
    for mr in ctx['mtex_requests']:
        _, slot_number, target, _ = mr.split(':')
        slot_number = int( slot_number )
        if len( m.texture_slots ) < slot_number:
            continue
        if m.texture_slots[slot_number] == None:
            continue
        if m.texture_slots[slot_number].texture.image == None:
            continue

        image = m.texture_slots[slot_number].texture.image

        export_name = ctx['export_names'].get( image.name, None )
        if export_name == None:
            ctx['export_names'][image.name] = 'mtex_%04i.png' % ( len( ctx['export_names'] ) + 1 )
            export_name = ctx['export_names'][image.name]
            #print('len( ctx["export_names"]: ', len( ctx['export_names'] ) )

        material_textures.append( ( target, export_name )  )





    #material_textures = [ (target, etex) for target, etex in material_textures.items() if etex is not None ]

    out.write('TextureAttributeList %i' % ( len(material_textures) ) )
    out.write('{')
    for target, export_name in material_textures:
        out.write('Data 1')
        out.write('{')
        out.write('osg::Texture2D')
        out.write('{')
        out.write('UniqueID %i' % getUniqueId())
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
        out.write('FileName "%s"' % export_name )
        out.write('WriteHint 0 2')
        out.write('DataVariance STATIC')
        out.write('}')
        out.write('}')
        out.write('Value OFF')
        out.write('}')
    out.write('}') # TextureAttributeList ends



    out.write('}') # osg::StateSet
    out.write('}') # StateSet TRUE
    return


def write_geometry_stateset( out, ctx, drawable ):

    #out.write('############### write_geometry_stateset')
    #return

    out.write('StateSet TRUE')
    out.write('{')
    out.write('osg::StateSet')
    out.write('{')
    out.write('UniqueID %i' % getUniqueId())
    out.write('Name "%s.geometry_state"' % ctx['name'] )
    out.write('DataVariance STATIC')


    out.write('TextureModeList 1')
    out.write('{')
    out.write('Data 1')
    out.write('{')
    out.write('GL_TEXTURE_2D ON')
    out.write('}')
    out.write('}')



#    texture_output_order = [ i for i in drawable.textures.items() if i[1] is not None ]
#    texture_output_order.sort( key=lambda x: x[0], reverse=True )
#    texture_output_order.sort( key=lambda x: 'mat_normal' == x[0], reverse=True )
#
#    out.write('TextureAttributeList %i' % ( len( texture_output_order ) ) )
#    out.write('{')
#    for target, etex in texture_output_order:
#        out.write('Data 1')
#        out.write('{')
#        out.write('osg::Texture2D')
#        out.write('{')
#        out.write('UniqueID %i' % getUniqueId())
#        out.write('Name "s_%s"' % target )
#        out.write('WRAP_S REPEAT')
#        out.write('WRAP_T REPEAT')
#        out.write('WRAP_R CLAMP_TO_EDGE')
#        out.write('MIN_FILTER LINEAR_MIPMAP_LINEAR')
#        out.write('MAG_FILTER LINEAR')
#        out.write('UnRefImageDataAfterApply TRUE')
#        out.write('ResizeNonPowerOfTwoHint TRUE')
#        out.write('Image TRUE')
#        out.write('{')
#        out.write('UniqueID %i' % getUniqueId())
#        out.write('FileName "%s"' % etex.export_name )
#        out.write('WriteHint 0 2')
#        out.write('DataVariance STATIC')
#        out.write('}')
#        out.write('}')
#        out.write('Value OFF')
#        out.write('}')
#    out.write('}')


    out.write('}') # osg::StateSet
    out.write('}') # StateSet TRUE
    return


def write_mesh_texture_stateset( out, ctx, image, texture_target ):

    #print( export_image )

    out.write('StateSet TRUE')
    out.write('{')
    out.write('osg::StateSet')
    out.write('{')
    out.write('UniqueID %i' % getUniqueId())
    out.write('Name "%s.mesh_texture"' % ctx['name'] )
    out.write('DataVariance STATIC')

    # write mateiral textures

    out.write('TextureModeList 1')
    out.write('{')
    out.write('Data 1')
    out.write('{')
    out.write('GL_TEXTURE_2D ON')
    out.write('}') # Data 1
    out.write('}') # TextureModeList

    export_name = ctx['export_names'].get( image.name, None )
    if export_name == None:
        ctx['export_names'][image.name] = 'tex_%04i.png' % ( len( ctx['export_names'] ) + 1 )
        export_name = ctx['export_names'][image.name]

    out.write('TextureAttributeList 1')
    out.write('{')
    out.write('Data 1')
    out.write('{')
    out.write('osg::Texture2D')
    out.write('{')
    out.write('UniqueID %i' % getUniqueId())
    out.write('Name "s_%s"' % texture_target )
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
    out.write('FileName "%s"' % export_name )
    out.write('WriteHint 0 2')
    out.write('DataVariance STATIC')
    out.write('}')
    out.write('}')
    out.write('Value OFF')
    out.write('}')
    out.write('}') # TextureAttributeList ends





    out.write('}') # osg::StateSet
    out.write('}') # StateSet TRUE
    return







def write_geometry( out, ctx, drawable ):
    out.write('osg::Geometry')
    out.write('{')
    out.write('UniqueID %i' % getUniqueId())
    out.write('Name "%s"' % drawable.name )
    out.write('DataVariance STATIC')
    #write_geometry_stateset ( out, ctx, drawable )
    write_primitive_set_list( out, drawable )
    write_vertex_data       ( out, drawable )
    write_normal_data       ( out, drawable )

    for field_name in drawable.attr_array.dtype.names:
        if field_name.startswith('col'):
            write_color_data( out, drawable.attr_array[ field_name ] )
            break # write only one set for now

    uv_fields = [ field_name for field_name in drawable.attr_array.dtype.names if field_name.startswith('uv') ]
    #print('attrs :', str(drawable.attr_array.dtype) )
    #for field_name in drawable.attr_array.dtype.names:
    if len( uv_fields ) > 0:
        out.write('TexCoordData %i' % len(uv_fields) )
        out.write('{')
        for field_name in uv_fields:
            if field_name.startswith('uv'):
                write_texcoord_data( out, drawable.attr_array[ field_name ] )
                #break # write only one set for now
        out.write('}')

    out.write('}')





