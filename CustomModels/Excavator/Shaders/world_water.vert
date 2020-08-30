#version 120
#line 2 "world.vert"

// varyings
varying vec4 color;
varying vec4 es_pos;
varying vec4 ws_pos;
varying vec2 uv_mesh;
varying vec3 es_normal;

void main()
{
	gl_Position = gl_ProjectionMatrix * gl_ModelViewMatrix * gl_Vertex;
	es_pos      = gl_ModelViewMatrix * gl_Vertex;
	ws_pos      = gl_Vertex;
	es_normal   = gl_NormalMatrix * gl_Normal;
	uv_mesh     = gl_MultiTexCoord0.xy;
	color       = gl_Color;
}

