#line 1 "ltground/glass_dim.frag"
#extension GL_ARB_gpu_shader5 : enable
#extension GL_ARB_uniform_buffer_object : enable

//========
// Inputs
//========
varying vec4 color;
varying vec4 es_pos;
varying vec2 uv_mesh;
varying vec3 es_normal;

varying vec3 es_T;
varying vec3 es_B;

//===================
// Mesh samplers
//===================
uniform sampler2D s_mesh_normal;
uniform sampler2D s_mesh_diffuse;
uniform sampler2D s_mesh_specular;




uniform mat3 rotationMatrix;
uniform float mev_alpha;
uniform float shadowIntensity;

uniform float reflect_factor;
uniform float gloss_factor;
uniform float translucency;
uniform vec3 mirror_color;


void main()
{
	vec3 E = normalize( es_pos.xyz );

	float cos_rho = dot( -E, es_normal );
	float n1 = 1.000;
	float n2 = 1.500;
	float R0 = pow( ( n1 - n2 ) / ( n1 + n2 ), 2.0 );
	float fresnel_reflection = R0 + ( 1.0 - R0 ) * pow( 1.0 - cos_rho, 2.0 );
	fresnel_reflection = clamp( fresnel_reflection, 0.95, 1.0 );

	
	gl_FragColor.rgba = vec4( vec3( 1.0 - fresnel_reflection ), 0.97 );
	
}
























