from collections import Counter

def analyze( filepath ):
    
    ids    = [ int(line.strip().split()[1]) for line in open( filepath ).readlines() if 'UniqueID' in line ]
    counts = Counter( ids )
    
    max_id = max( ids )
    
    print( 'max_id:', max_id )
    
    id_table = { id:0 for id in range( max_id + 1 ) }
    
    for id in ids:
        id_table[id] += 1
    
    for id, count in id_table.items():
        if count == 0:
            print( 'UniqueID %3i : %3i' % ( id, count ) )
    
    

analyze('D:/temp/Quarry/RearFrame/RearFrame.osgt')