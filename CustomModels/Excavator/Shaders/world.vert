#version 120
#line 2 "world.vert"

// varyings
varying vec4 color;
varying vec4 es_pos;
varying vec4 ws_pos;
varying vec2 uv_world;
varying vec3 es_normal;

void main()
{
	gl_Position = gl_ProjectionMatrix * gl_ModelViewMatrix * gl_Vertex;
	es_pos      = gl_ModelViewMatrix * gl_Vertex;
	ws_pos      = gl_Vertex;
	es_normal   = gl_NormalMatrix * gl_Normal;

	// uv_world     = gl_MultiTexCoord0.xy;
	// uv_world     = ( ws_pos.zx + vec2( 255.5, 767.5 ) ) / vec2( 2048.0 );
	uv_world     = ( ws_pos.zx + vec2( 256.0, 768.0 ) ) / vec2( 2048.0 );
	// uv_world     = ( ws_pos.zx + vec2( 256.5, 768.5 ) ) / vec2( 2048.0 );

	color       = gl_Color;
}

