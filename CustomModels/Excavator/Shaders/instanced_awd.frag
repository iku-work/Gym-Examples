#version 120
#line 2 "instanced_awd.frag"
#extension GL_ARB_gpu_shader5 : enable
#extension GL_ARB_uniform_buffer_object : enable

#include ../Shaders/common/combine.frag
void saturate( inout vec3 color, float factor );
float linmap(float v, float s0, float s1, float d0, float d1); 
float linmap_c(float v, float s0, float s1, float d0, float d1); 
float getGamma();
float rough_mix( float control, float sharp, float bias );
float mev_DynamicShadow(vec2 u, vec4 tex);
float mev_DitheredDynamicShadow(float scale);
void mev_sun_light(	int i, inout vec3 diff_light, inout vec3 spec_light, inout vec3 ambi_light, vec3 es_normal, vec3 es_pos );
void mev_sun_light_translucent(	int i, inout vec3 diff_light, inout vec3 spec_light, inout vec3 ambi_light, vec3 es_normal, vec3 es_pos );
void fog( in vec3 es_pos, inout vec3 color );
vec3 reflection( vec3 es_N, vec3 es_R, float ao );
vec3 combine(	vec3 es_N,
				vec4 es_pos,

				vec3 diff_color,
				vec3 spec_color,
				vec3 ambi_color,
				vec3 emit_color,

				float ao,
				float reflect_factor
				);


//========
// Inputs
//========
varying vec4 ws_pos;

varying vec4 color;
varying vec4 es_pos;
varying vec2 uv_mesh;
varying vec2 uv_mat;
varying vec3 es_normal;

varying vec3 es_T;
varying vec3 es_B;
varying vec3 es_mat_T;
varying vec3 es_mat_B;

uniform sampler2D s_ao_wear_dust;
uniform sampler2D s_mat_diffuse;
uniform sampler2D s_mat_specular;
uniform sampler2D s_mat_normal;
uniform sampler2D s_mat_dirt_normal;

uniform float reflect_factor;

uniform float osg_SimulationTime;

uniform vec3 pob1;
uniform vec3 pob2;


void main()
{
	float GAMMA = 2.2;

	//==================================
	// Define lighting model components
	//==================================
	
	vec3  diff_color = vec3( 1.0, 1.0, 1.0 );
	vec3  spec_color = vec3( 1.0, 1.0, 1.0 );
	vec3  ambi_color = vec3( 1.0, 1.0, 1.0 );
	vec3  emit_color = vec3( 0.0, 0.0, 0.0 );
	
	vec3  diff_light = vec3( 0.0, 0.0, 0.0 );
	vec3  spec_light = vec3( 0.0, 0.0, 0.0 );
	vec3  ambi_light = vec3( 0.0, 0.0, 0.0 );
	
	float alpha = gl_FrontMaterial.diffuse.a;
	
	//=================
	// Source material
	//=================
	
	diff_color = gl_FrontMaterial.diffuse.rgb;
	spec_color = gl_FrontMaterial.specular.rgb;
	ambi_color = gl_FrontMaterial.ambient.rgb;
	emit_color = gl_FrontMaterial.emission.rgb;
	
	vec3 es_N  = es_normal;
	
	//====================
	// 3 Layered material
	//====================
	vec3 awd = texture2D( s_ao_wear_dust, uv_mesh ).rgb;
	float wear	= awd.r;			// NOTE: using gamma corrected value
	float ao	= awd.g;			// NOTE: using gamma corrected value
	float dust	= awd.b;			// NOTE: using gamma corrected value

	float sp = texture2D( s_mat_specular, uv_mat ).r;

	float l1_wear_power  = pob1.r;
	float l1_wear_offset = pob1.g;
	float l1_wear_bias   = pob1.b;
	float l2_wear_power  = pob2.r;
	float l2_wear_offset = pob2.g;
	float l2_wear_bias   = pob2.b;

	#if 1
	// l1_wear_power  =  2.00;		// bare metal override
	// l1_wear_offset = -2.00;		// bare metal override
	// l1_wear_bias   =  2.00;		// bare metal override
	#endif
	#if 1
	// l2_wear_power  =   1.50;		// worn override
	// l2_wear_offset =  -0.60;		// worn override
	// l2_wear_bias   =   1.00;		// worn override
	#endif


	float l1_mask = rough_mix( pow( wear,                  l1_wear_power ) + l1_wear_offset, l1_wear_bias, sp );
	float l2_mask = rough_mix( pow( wear + ( 1.0 - dust ), l2_wear_power ) + l2_wear_offset, l2_wear_bias, sp );
	// float l1_mask = rough_mix( pow( wear, 1.1                   ) - 0.15, 4.0,	sp );
	// float l2_mask = rough_mix( pow( wear + ( 1.0 - dust ), 0.90 ) + 0.30, 2.6,	sp );

	vec4 gamma_v4 = vec4( GAMMA, GAMMA, GAMMA, 1.0 );
	
	vec4 d = pow( texture2D( s_mat_diffuse,  uv_mat * 2.0 ), gamma_v4 );// * vec4(0.20, 0.20, 0.20, 1.0 );
	vec4 s = pow( texture2D( s_mat_specular, uv_mat ), gamma_v4 );
	
	


	// float depth = l1_diff_color.r;
	
	//=================
	// Mesh Normal map
	//=================
	
	float normal_factor = 1.0;
	float fresnel_factor = 1.0;
	
	
	vec3 mesh_normal = texture2D( s_mat_normal, uv_mat ).rgb;
	mesh_normal = mix( mesh_normal, texture2D( s_mat_dirt_normal, uv_mat * 3.0 ).rgb, (l2_mask - l1_mask) * 0.3 );
	#if 1
	{
		//=============
		// Mat Normal
		//=============
		mesh_normal.xy -= vec2( 0.5 );
		mesh_normal.xy *= vec2( normal_factor * 1.00 );
		mesh_normal     = mat3( es_mat_T, es_mat_B, es_normal )	* mesh_normal;
		//=============
		
		es_N = mesh_normal;
	}
	#endif
	es_N  = normalize( es_N  );


	vec3 l0_diff_color = diff_color * vec3( 0.10 );	// bottom layer
	vec3 l1_diff_color = mix( diff_color * 0.6, d.rgb * 0.5, d.a ); // worn paint
	vec3 l2_diff_color = diff_color * vec3( 1.00 );	// fine paint

	vec3 l0_spec_color = vec3( 1.000, 1.000, 1.000 ) * s.rgb;
	vec3 l1_spec_color = vec3( 0.005, 0.005, 0.005 );
	vec3 l2_spec_color = vec3( 0.990, 0.990, 0.990 ) * ao * ao * ao;

	//====================
	// Combine components
	//====================
	float l2_spec_mask = 1.0 - pow(1.0 - l2_mask, 4.0);

	vec3  masked_diff = mix( mix( l2_diff_color,   l1_diff_color,   l2_mask      ), l0_diff_color,   l1_mask ) * 1.0;
	vec3  masked_spec = mix( mix( l2_spec_color,   l1_spec_color,   l2_spec_mask ), l0_spec_color,   l1_mask ) * 1.0;
	float masked_refl = clamp( reflect_factor * 3.0, l1_mask, 1.0 );

	masked_diff *= vec3( linmap_c( texture2D( s_mat_diffuse, vec2( color.r * 0.001 ) ).r, 0.5, 0.75, 0.0, 1.0) );

	gl_FragColor.rgb	= combine(	es_N,        // vec3 es_N,
									es_pos,      // vec4 es_pos,
									masked_diff, // vec3 diff_color,
									masked_spec, // vec3 spec_color,
									ambi_color,  // vec3 ambi_color,
									emit_color,  // vec3 emit_color,
									ao,          // float ao,
									masked_refl  // float reflect_factor
									);
	gl_FragColor.a   = 1.0;
}







