from math import sin, cos

def initScript():
    # Fetch an instance of MVariable class and store it as local parameter
    GObject.data[ 'w' ] = GSolver.getParameter( 'Volvo_D6E_LBE3', 'w' )
    return 0
    
def callScript( deltaTime, simulationTime ):
    # Initialize quaternions for pillar, lift and tilt
    qpillar = MQuat()
    qlift = MQuat()
    qtilt = MQuat()

    # Rotate pillar according to sin( simulationTime )
    qpillar.setOrientation( 0, sin( simulationTime ) * 25, 0 )
    
    # Get motor w value and divide
    w = GObject.data[ 'w' ].value() / 10.0
    
    qlift.setOrientation( 0, 0, w )
    qtilt.setOrientation( 0, 0, w )

    GObject.setQuat( qpillar )
    GDict[ 'SO_LiftBoom' ].setQuat( qlift )
    GDict[ 'SO_TiltBoom' ].setQuat( qtilt )
    
    print( GSolver.getParameter( 'Volvo_D6E_LBE3', 'w' ).value() )
    return 0
