def initScript():
    print( 'Hello from Python' )
    return 0
    
def callScript( deltaTime, simulationTime ):
    #print( 'Hello again', GObject.getInputValue() )
    GDict[ 'Tilt_Input' ].setInputValue( GObject.getInputValue() ) 
    return 0
