#line 1 "ltground/glass_reflection.frag"
#extension GL_ARB_gpu_shader5 : enable
#extension GL_ARB_uniform_buffer_object : enable

#include common/combine.frag
vec3 combine(	vec3 es_N,
	
				vec3 diff_color,
				vec3 spec_color,
				vec3 ambi_color,
				vec3 emit_color,

				vec3 diff_light,
				vec3 spec_light,
				vec3 ambi_light,
				
				float normal_factor,
				float fresnel_factor,
				float gloss_factor,
				float ao,
				float shininess,
				float reflect_factor,
				float depth
				);


float mev_DitheredDynamicShadow(float scale);

//========
// Inputs
//========
varying vec4 color;
varying vec4 es_pos;
varying vec2 uv_mesh;
varying vec3 es_normal;

varying vec3 es_T;
varying vec3 es_B;

varying float hdrDim;

//===================
// Mesh samplers
//===================
uniform sampler2D s_mesh_normal;
uniform sampler2D s_mesh_diffuse;
uniform sampler2D s_mesh_specular;

uniform samplerCube	s_environment;
uniform sampler2DShadow	shadowTexture;

uniform bool fogOn;
uniform bool shadowOn;

uniform mat3 rotationMatrix;
uniform float mev_alpha;
uniform float shadowIntensity;

uniform float reflect_factor;
uniform float gloss_factor;
uniform float translucency;
uniform vec3 mirror_color;

// float mev_DitheredDynamicShadow	( float scale );
// float LT_overcast_factor();
// float LT_diffuse_boost();
// float LT_specular_boost();
// float LT_ambient_boost();
// void saturate( inout vec3 color, float factor );
// void LT_fog( in vec3 es_pos, inout vec3 color );

void main()
{
	const float GAMMA = 2.2;
	float shadow = mev_DitheredDynamicShadow( 0.0004 );
		
	vec3 es_N = normalize( es_normal );
		
	vec3 E    = normalize( es_pos.xyz );
	vec3 es_R = reflect( E, es_N );
	vec3 R    = mat3( 0,1,0, 0,0,1, 1,0,0 )  * rotationMatrix * inverse( gl_NormalMatrix ) * reflect( E, es_N );
	
	// vec4 ref       = textureCube( s_environment, R, 6.0 );
	vec4 ref       = textureCubeLod( s_environment, R, 3.0 );
	vec3 ref_light = vec3( ref.rgb ) / ref.a * gl_LightSource[0].ambient.rgb * gl_LightSource[0].ambient.rgb * 4.0;
	// saturate( ref_light, -LT_overcast_factor() );
	
	//=========
	// Combine
	//=========
	float cos_rho = dot( -E, es_normal );
	float n1 = 1.000;
	float n2 = 1.500;
	float R0 = pow( ( n1 - n2 ) / ( n1 + n2 ), 2.00 );
	float fresnel_reflection = R0 + ( 1.0 - R0 ) * pow( 1.0 - cos_rho, 10.0 );
	fresnel_reflection = clamp( fresnel_reflection, 0.0, 1.0 ) * reflect_factor;

	gl_FragColor.rgb	= vec3( 0.0 )
						+ ref_light  * fresnel_reflection
						// + ref_light * 100
						// + vec3( 1.0, 0.0, 1.0 )
						;
				
	// if( fogOn )
		// LT_fog( es_pos.xyz, ret );
	
	//=======
	// Glare
	//=======
	
	// ret *= hdrDim;
	
	// ret = pow( ret, vec3( 1.0 / 2.2 ) );
	
	//====================
	// Gamma correction
	//====================
	
	gl_FragColor.rgb = pow( gl_FragColor.rgb, vec3( 1.0 / GAMMA ) );
	// gl_FragColor.rgb = pow( gl_FragColor.rgb, vec3( 1.0 / 3.0 ) );
	gl_FragColor.a   = 1.0;
	
	
}




