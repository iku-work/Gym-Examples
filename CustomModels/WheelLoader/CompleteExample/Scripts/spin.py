from math import sin, cos

def initScript():
    print( 'Hello from Python' )
    
    # Retrieve objects current position
    GObject.data[ 'pos' ] = GObject.getPosition()
    
    # Initialize local variable used for rotating to zero
    GObject.data[ 'ori' ] = 0.0
    return 0
    
def callScript( deltaTime, simulationTime ):
    # Set objects position according to simulationTime
    # Use script instanceID to make them move at different speeds
    GObject.setPosition( GObject.data[ 'pos' ] + MVec3( 0, ( GObject.instanceID + 1 ) * sin( simulationTime ), 0 ) )
    
    # Rotate objects by creating a quaternion
    GObject.data[ 'ori' ] += 0.02 * (GObject.instanceID + 1)
    q = MQuat()
    q.setOrientation( 0, GObject.data[ 'ori' ] + 0.0001, 0 ) 
    GObject.setQuat( q )
    
    return 0
