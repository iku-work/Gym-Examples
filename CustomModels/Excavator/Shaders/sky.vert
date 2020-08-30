#line 1 "sky .vert"
#extension GL_ARB_gpu_shader5 : enable

varying vec2	uv_mesh;
varying vec3	skyDir;
varying vec3	ws_direction;
varying vec3	ws_sunDirection;
varying vec3	es_pos;

uniform mat3 rotationMatrix;

void main()
{
	gl_Position	    = gl_ModelViewProjectionMatrix * ( gl_Vertex * vec4( 1.0, 1.0, 1.0, 0.250 ) );
	uv_mesh	        = gl_MultiTexCoord0.xy;
	ws_direction	= normalize( gl_Vertex.xyz );
	ws_sunDirection	= normalize( transpose( gl_NormalMatrix ) * -gl_LightSource[0].position.xyz );
	es_pos          = gl_ModelViewMatrix * gl_Vertex;

	if ( gl_ClipPlane[0].w < 0.0 )
	{
		ws_sunDirection *= vec3( 1.0, 1.0, 1.0 );
	}
}