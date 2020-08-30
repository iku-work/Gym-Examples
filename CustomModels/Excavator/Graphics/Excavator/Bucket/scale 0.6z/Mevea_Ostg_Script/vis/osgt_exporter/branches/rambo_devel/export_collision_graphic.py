import bpy

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

