#line 1 "diffuse.vert"

// uniforms
uniform int		major_axis;
uniform float	material_scale;
uniform bool	shadowOn;

// attributes
attribute vec3 rm_Binormal;
attribute vec3 rm_Tangent;

// varyings
varying vec4 color;
varying vec4 es_pos;
varying vec2 uv_mesh;
varying vec2 uv_mat;
varying vec3 es_normal;

varying vec3 es_T;
varying vec3 es_B;
varying vec3 es_mat_T;
varying vec3 es_mat_B;


const int dynamic_shadow_uv_index = 0;

void mev_DynamicShadow( in vec4 ecPosition )
{                                        
    // generate coords for shadow mapping
    gl_TexCoord[dynamic_shadow_uv_index].s = dot( ecPosition, gl_EyePlaneS[dynamic_shadow_uv_index] );
    gl_TexCoord[dynamic_shadow_uv_index].t = dot( ecPosition, gl_EyePlaneT[dynamic_shadow_uv_index] );
    gl_TexCoord[dynamic_shadow_uv_index].p = dot( ecPosition, gl_EyePlaneR[dynamic_shadow_uv_index] );
    gl_TexCoord[dynamic_shadow_uv_index].q = dot( ecPosition, gl_EyePlaneQ[dynamic_shadow_uv_index] );
}

void main()
{
	gl_Position = gl_ProjectionMatrix * gl_ModelViewMatrix * gl_Vertex;
	uv_mesh = gl_MultiTexCoord0.xy;
	uv_mat  = gl_MultiTexCoord1.xy;
		
	color   = gl_Color;
	
	const vec3 x = vec3( 1.0, 0.0, 0.0 );
	const vec3 y = vec3( 0.0, 1.0, 0.0 );
	const vec3 z = vec3( 0.0, 0.0, 1.0 );
	
	es_normal	= gl_NormalMatrix * gl_Normal;
	es_pos		= gl_ModelViewMatrix * gl_Vertex;

	es_T		= gl_NormalMatrix * rm_Tangent;
	es_B		= gl_NormalMatrix * rm_Binormal;
	
	if(shadowOn)
		mev_DynamicShadow( es_pos );
}