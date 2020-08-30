import os
import re
import sys
sys.path.append('D:\\Python33\\Lib\\site-packages')
os.environ['PATH'] += ';C:\\Program Files (x86)\\WinMerge\\'

import bpy
import imp
from bpy import path
import xml.etree.ElementTree as ET

from mathutils import Vector

sys.path.append( bpy.path.abspath('//') )

import OsgtExporter
imp.reload( OsgtExporter )
from OsgtExporter import OsgtExporter, ExportSourceSetup, ObjectPropertyRequest




#=============================================================
# Legacy function for exporting collision graphic
#=============================================================

def export_collision_graphic( output_filepath, matrix, collision_group  ):
    
    view        = bpy.context.scene.active_layer
    scene       = bpy.context.scene
    export_path = output_filepath
    #----------------------------------------------------------------
    # ensure the group has a matrix object to define exported origin
    #----------------------------------------------------------------
    ROT = matrix.copy()
    
    # deselect everything
    for o in bpy.data.objects:
        o.select = False
    
    # make temporary objects for collision export
    temp_objects = []
    for i, o in enumerate( collision_group.objects ):
        d = o.to_mesh( scene=bpy.context.scene, apply_modifiers=True, settings='RENDER' )
        c = bpy.data.objects.new( name='temp_collision_for_export_%3i' % i, object_data=d )
        temp_objects.append( c )
        scene.objects.link(c)
        c.layers[view]   = True
        c.select         = True
        c.matrix_world   = o.matrix_world
        c.matrix_world   = ROT.inverted() * c.matrix_world
    print( 'Exporting collision graphics to "%s"' % export_path )
    if 1:
        bpy.ops.export_scene.autodesk_3ds(  filepath        = export_path,
                                            check_existing  = False,
                                            filter_glob     = '*.3ds',
                                            use_selection   = True,
                                            axis_forward    = 'Y',
                                            axis_up         = 'Z'
                                            )
    for o in temp_objects:
        scene.objects.unlink( o )

#=========================================


MISSING_MATERIAL = -1

os.system('cls')
os.system('cls')
#s.system('clear')
#os.system('clear')



def export_groups( groups, export_source_setup ):
    for group_name, objects, ref_matrix, ask_coll, install_basedir in [ (    group_name,
                                                                            bpy.data.groups[  group_name ].objects,
                                                                            bpy.data.objects[ group_name + '.matrix' ].matrix_world,
                                                                            ask_coll,
                                                                            install_basedir
                                                                        ) for group_name, ask_coll, install_basedir, _ in groups ]:
        
        ask_for_collision = ask_coll
        collision_group   = None
        
        if ask_for_collision:
            collision_group_name = group_name + '.COLL'
            if collision_group_name in bpy.data.groups:
                if len( bpy.data.groups[ collision_group_name ].objects ) == 0:
                    raise RuntimeError( 'Collision group "%s" found but contains no objects "%s"' % collision_group_name )
                collision_group   = bpy.data.groups[ collision_group_name ]
            else:
                raise RuntimeError( 'Collision group not found "%s"' % collision_group_name )
            #print( collision_object )
            
        collect_dir = install_basedir + '/'+ group_name
        try:
            os.mkdir( collect_dir )
        except:
            pass
        
        
        oe = OsgtExporter( ref_matrix, group_name, export_source_setup )
        for o in objects:
            oe.feed_object( o, [] )
        oe.run()
        oe.save( output_directory=collect_dir, basename=group_name )
        
        if ask_for_collision:
            export_collision_graphic(   output_filepath  = collect_dir + '/' + 'COLL_' + group_name + '.3ds',
                                        matrix           = ref_matrix,
                                        collision_group  = collision_group
                                        )
        


def update_xml( xml_filename, groups, graphics_install_path ):
    #======================================================================
    #============================ UPDATE XML ==============================
    #======================================================================
    input_file = open( xml_filename, 'r' )
    xml_content = input_file.read()
    input_file.close()
    
    assert( len( xml_content ) > 0 )
    
    name_map = { name : targets if targets is not None else ( name, ) for name, _, _, targets in groups }
    
    def update_attribute( xml_tag_str, name, value ):
        #print(xml_tag_str)
        #print('')
        subbed = re.sub( r'%s="([^"]*)"' % ( name ), '%s="%s"' % ( name, value ), xml_tag_str )
        #print( subbed )
        #print('')
        return subbed
    
    print('=' * ( 12 + len(xml_filename) ) )
    print('Rewriting "%s"' % xml_filename)
    print('=' * ( 12 + len(xml_filename) ) )
    
    for name, targets in name_map.items():
        for target in targets:
            
            tag_match_pattern = '<%s_Graphics\s+.*>' % (target)
            
            print( ('XML Rewrite "%s"    ' % target).ljust(30), end='' )
            
            matched_tags = re.findall( tag_match_pattern, xml_content )
            if len( matched_tags ) != 1:
                print('TAG NOT FOUND')
                continue
            
            new_tag = matched_tags[0]
            
            new_tag = update_attribute( new_tag, 'FileName', graphics_install_path + name + '/' + name + '.osgt')
            #new_tag = update_attribute( new_tag, 'BothSides'             ,"No")
            #new_tag = update_attribute( new_tag, 'CastShadows'           ,"Yes")
            #new_tag = update_attribute( new_tag, 'IsActive'              ,"Yes")
            #new_tag = update_attribute( new_tag, 'Material'              ,"None")
            #new_tag = update_attribute( new_tag, 'ReceiveShadows'        ,"Yes")
            #new_tag = update_attribute( new_tag, 'Scale'                 ,"1")
            #new_tag = update_attribute( new_tag, 'ShaderName'            ,"")
            #new_tag = update_attribute( new_tag, 'TextureName'           ,"")
            #new_tag = update_attribute( new_tag, 'Transparency'          ,"1")
            #new_tag = update_attribute( new_tag, 'TransparentBin'        ,"No")
            #new_tag = update_attribute( new_tag, 'bumpMapScale'          ,"10.0")
            #new_tag = update_attribute( new_tag, 'isTerrain'             ,"No")
            #new_tag = update_attribute( new_tag, 'linkDefaultShaders'    ,"No"
            #new_tag = update_attribute( new_tag, 'ocean_reflect'         ,"No")
            #new_tag = update_attribute( new_tag, 'ocean_refract'         ,"No")
            #new_tag = update_attribute( new_tag, 'useColor'              ,"No")
            #new_tag = update_attribute( new_tag, 'use_flexible_shader'   ,"No")
            #new_tag = update_attribute( new_tag, 'use_fragment_light'    ,"No")
            #new_tag = update_attribute( new_tag, 'use_normal_map'        ,"No")
            
            xml_content = re.sub( tag_match_pattern, new_tag, xml_content )
            print('OK')
            
    assert( os.path.exists( xml_filename ) )
    out_file = open( xml_filename, 'w')
    #out_file = open(r'D:\temp\temp.xml', 'w')
    out_file.write( xml_content )
    out_file.close()
    
    #os.system(r'WinMergeU.exe "%s" "%s"' % (xml_filename, 'D:\\temp\\temp.xml') )
    print("\n")
    
print('\n'*50)
    


#======================================================================
# Export std1 ###( now RearFrame )
#======================================================================
if 1:
    quarry_ess = ExportSourceSetup(
        #shader_name                = '../../Shaders/quarry',
        #shader_name                = 'quarry',
        shader_name                = '../Graphics/SandCavity/SandCavity/quarry',
        attributes                 = [  
                                        # type:source:target
                                        'co::',
                                        'no::',
                                        'uv:UVMap:uv0',
                                        'col:Col:',
                                        ],
        groupby                    = [  # rule_name
                                        'cubic_cell:10m',
                                        '_mat_index:::',
                                        '_obj_index:::',
                                        #'major_axis:::',
                                        #'spot_binding:::',
                                        'tex:UVMap:mesh_diffuse:diffuse',
                                        ],
        material_textures          = [  # type:slot_number:target:role
                                          'mtex:0:mat_diffuse_a:diffuse',
                                          'mtex:1:mat_diffuse_b:diffuse',
                                        #  'mtex:2:mat_diffuse_c:diffuse',
                                          'mtex:2:mesh_ao:ao',
                                          'mtex:3:mesh_normal:normal',
                                          'mtex:4:mesh_alpha:diffuse',
                                        ],
        object_property_requests   = [  
                                        #ObjectPropertyRequest( 'spot_binding', 'INT',        1, -1      ),
                                        #ObjectPropertyRequest( 'light_color',  'FLOAT_VEC3', 3, (1.0,1.0,1.0) ),
                                     ],
        weld_tolerance             = 4,     # decimals,
        )
    
    xmls = [    'C:/Program Files (x86)/MeVEA/WheelLoader/WheelLoader/WheelLoader_Rocks.xml',
                'C:/Program Files (x86)/MeVEA/WheelLoader/WheelLoader/WheelLoader_Sand.xml',
                'C:/Program Files (x86)/MeVEA/WheelLoader/WheelLoader/WheelLoader_Tasks.xml',
                'C:/Program Files (x86)/MeVEA/WheelLoader/WheelLoader/WheelLoader_Logs.xml',
                ]
    
    graphics_install_path   = '../Graphics/Environment/' # use this path in XML file
    groups_quarry = [
                    #('SandCavity',     1, 'C:\Program Files (x86)\MeVEA\WheelLoader\Graphics\Environment', (None) ),
                    #('SandCavity',     1, 'D:/temp/Quarry', (None) ),
                    ('SandCavity',     1, 'C:\Program Files (x86)\MeVEA\WheelLoader\Graphics\SandCavity/', (None) ),
                    ]
                
    export_groups( groups_quarry,   quarry_ess )
    #for xml_filename in xmls:
    #    update_xml( xml_filename, groups_wl, graphics_install_path )







#====================
# Export light halos
#====================

   
    
def export_halos( lights, export_source_setup, lens_flare_stack ):
    
    for group_name, objects, ref_matrix, ask_coll, install_basedir in [ (    group_name,
                                                                            bpy.data.groups[  group_name ].objects,
                                                                            bpy.data.objects[ group_name + '.matrix' ].matrix_world,
                                                                            ask_coll,
                                                                            install_basedir
                                                                        ) for group_name, ask_coll, install_basedir, _ in groups ]:
        
        collect_dir = install_basedir + '/'+ group_name
        try:
            os.mkdir( collect_dir )
        except:
            pass
            
        oe = OsgtExporter( objects, ref_matrix, group_name, export_source_setup )
        oe.save( output_directory=collect_dir, basename=group_name )


if 0:
    halo_ess = ExportSourceSetup(
        shader_name                = 'halo',
        attributes                 = [  
                                        # type:source:target
                                        'co::',
                                        'no::',
                                        'uv:UVMap:uv0',
                                        #'col:Col:',
                                        ],
        uniforms                   = [  # type:source:target:role
                                        'mat:::',
                                        'major_axis:::',
                                        'spot_binding:::',
                                        'spot_position:::',
                                        'spot_direction:::',
                                        #'tex:UVMap:mesh_diffuse:diffuse',
                                        ],
        material_textures          = [  # type:slot_number:target:role
                                         'mtex:0:halo:diffuse',
                                         'mtex:1:dust_in_the_air:diffuse',
                                        ],
        object_property_requests   = [
                                     #   ObjectPropertyRequest( 'light_color', 'FLOAT_VEC3',        3, (1.0,1.0,1.0)   ),
                                        ],
        weld_tolerance             = 4,     # decimals,
        use_shared_attribute_array = False
        )
    
    xmls = [    'C:/Program Files (x86)/MeVEA/WheelLoader/WheelLoader/WheelLoader_Rocks.xml',
                'C:/Program Files (x86)/MeVEA/WheelLoader/WheelLoader/WheelLoader_Sand.xml',
                'C:/Program Files (x86)/MeVEA/WheelLoader/WheelLoader/WheelLoader_Tasks.xml',
                'C:/Program Files (x86)/MeVEA/WheelLoader/WheelLoader/WheelLoader_Logs.xml',
                ]
    
    graphics_install_path   = '../Graphics/WheelLoader/' # use this path in XML file
    
    groups_halo = [
                    ('FrontLightHalo',      0, 'C:\Program Files (x86)\MeVEA\WheelLoader\Graphics\WheelLoader', (None) ),
                    ('RearLightHalo',       0, 'C:\Program Files (x86)\MeVEA\WheelLoader\Graphics\WheelLoader', (None) ),
                ]
    
    
    
    oe = OsgtExporter(  bpy.data.objects['LightStack.matrix'].matrix_world,
                        'LightStack',
                        halo_ess
                        )
    
    IR = bpy.data.objects['RearFrame.matrix'].matrix_world.to_3x3().inverted()
    IM = bpy.data.objects['RearFrame.matrix'].matrix_world.to_4x4().inverted()
    
    for obj in bpy.data.groups['LightStack'].objects:
        pos = ( IM * obj.matrix_world.col[3].to_4d() ).to_3d()
        direction = ( IR * obj.matrix_world.col[1].to_3d() ).normalized()
        
        
        oe.feed_object(     bpy.data.objects['lens_flare_stack'],
                            [
                                DrawableProperty( 'spot_rot_binding',  'INT',        obj['spot_rot_binding']   ), 
                                DrawableProperty( 'spot_binding',      'INT',        obj['spot_binding']       ), 
                                DrawableProperty( 'light_color',       'FLOAT_VEC3', obj['light_color']        ),
                                DrawableProperty( 'light_position',    'FLOAT_VEC3', pos  ),
                                DrawableProperty( 'light_direction',   'FLOAT_VEC3', direction ),
                            ]
                        )
    oe.run()
    
    collect_dir = 'C:/Program Files (x86)/MeVEA/WheelLoader/Graphics/WheelLoader/LightStack/'
    try:
        os.mkdir( collect_dir )
    except:
        pass
    
    oe.save(    output_directory=collect_dir,
                basename='LightStack' )
    
    #export_groups( groups_halo, halo_ess )
    #for xml_filename in xmls:
    #    update_xml( xml_filename, groups_halo, graphics_install_path )













#======================================================================
# Export inner glass and window dirt
#======================================================================

if 0:
    innerglass_ess = ExportSourceSetup(
        shader_name                = 'innerglass',
        attributes                 = [  
                                        # type:source:target
                                        'co::',
                                        'no::',
                                        'uv:UVMap:uv0',
                                        ],
        uniforms                   = [  # type:source:target:role
                                        'mat:::',
                                        'major_axis:::',
                                        #'tex:UVMap:mesh_diffuse:diffuse',
                                        ],
        material_textures          = [  # type:slot_number:target:role
                                         'mtex:0:grease:grease',
                                         'mtex:1:dust:dust',
                                         'mtex:2:fracture:fracture',
                                        ],
        weld_tolerance             = 4,     # decimals,
        use_shared_attribute_array = False
        )
    
    xmls = [    'C:/Program Files (x86)/MeVEA/WheelLoader/WheelLoader/WheelLoader_Rocks.xml',
                'C:/Program Files (x86)/MeVEA/WheelLoader/WheelLoader/WheelLoader_Sand.xml',
                'C:/Program Files (x86)/MeVEA/WheelLoader/WheelLoader/WheelLoader_Tasks.xml',
                'C:/Program Files (x86)/MeVEA/WheelLoader/WheelLoader/WheelLoader_Logs.xml',
                ]
    
    graphics_install_path   = '../Graphics/WheelLoader/' # use this path in XML file
    
    groups = [
                ('InnerGlass',        0, 'C:\Program Files (x86)\MeVEA\WheelLoader\Graphics\WheelLoader', (None) ),
             ]
    
    export_groups( groups, innerglass_ess )
    for xml_filename in xmls:
        update_xml( xml_filename, groups, graphics_install_path )

