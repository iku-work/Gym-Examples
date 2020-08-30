#line 1 "awd_leather.frag"
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
vec3 combine_foliage(	vec3 es_N,
						vec3 diff_color,
						vec3 spec_color,
						vec3 ambi_color,
						float ao
						);

//========
// Inputs
//========
varying vec4 color;
varying vec4 es_pos;
varying vec2 uv_mesh;
varying vec2 uv_mat;
varying vec3 es_normal;

varying vec3 es_T;
varying vec3 es_B;
varying vec3 es_mat_T;
varying vec3 es_mat_B;

varying float hdrDim;

uniform sampler2D s_ao_wear_dust;
uniform sampler2D s_mat_diffuse;
uniform sampler2D s_mat_specular;
uniform sampler2D s_mat_normal;




uniform bool fogOn;
uniform bool shadowOn;

uniform mat3 rotationMatrix;
//===================
// Global samplers
//===================
uniform samplerCube	s_environment;
uniform sampler2DShadow	shadowTexture;


//=======================
// function declarations
//=======================
void apply_fog( in vec3 es_pos, inout vec3 color );
float linmap_c(float v, float s0, float s1, float d0, float d1);

//===================
// Mesh samplers
//===================
// uniform sampler2D s_mesh_normal;
// uniform sampler2D s_mesh_diffuse;
// uniform sampler2D s_mesh_specular;
// uniform sampler2D s_mesh_ao;

uniform bool hasTexture;

uniform float reflect_factor;
uniform float gloss_factor;
uniform float translucency;
uniform vec3 mirror_color;
uniform vec3 gravity;
uniform float	osg_SimulationTime;




void main()
{
	// float GAMMA = 1.0 + 2.2 * gl_LightSource[0].ambient.r * 8.0;
	const float GAMMA = 2.2;
	// const float GAMMA = 1.0;
	
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
	
	float alpha      = gl_FrontMaterial.diffuse.a;
	
	//=================
	// Source material
	//=================
	
	diff_color = gl_FrontMaterial.diffuse.rgb;
	spec_color = gl_FrontMaterial.specular.rgb;
	ambi_color = gl_FrontMaterial.ambient.rgb;
	emit_color = gl_FrontMaterial.emission.rgb;
	
	
	// vec4 mD = pow( texture2D( s_mesh_diffuse,  uv_mesh ),	vec4( GAMMA,GAMMA,GAMMA, 1.0 ) );
	// vec4 MS = pow( texture2D( s_mesh_specular, uv_mesh ),	vec4( GAMMA,GAMMA,GAMMA, 1.0 ) );
	
	// alpha = max( alpha, mD.a );
	
	vec3 es_N  = es_normal;
	
	
	
	//====================
	// 3 Layered material
	//====================
	vec3 awd = texture2D( s_ao_wear_dust, uv_mesh ).rgb;
	float wear	= awd.r;
	float ao	= awd.g;
	float dust	= awd.b;
	
	
	float l1_mask = rough_mix( pow( wear, 1.1 )           -0.15,        2.0,	texture2D( s_mat_specular, uv_mat * 6.0 ).r );
	float l2_mask = rough_mix( pow( wear + ( 1.0 - dust ), 0.90 ) +0.1, 2.0,	texture2D( s_mat_specular, uv_mat * 6.0 ).r );
	// float l2_mask = rough_mix( pow( wear, 0.90 ) +0.1, 3.0,	texture2D( s_mat_specular, uv_mat * 6.0 ).r );
	// float l2_mask = max( rough_mix( pow( wear, 0.90 ) +0.1, 3.0,	texture2D( s_mat_specular, uv_mat * 6.0 ).r ), ( 1.0 - dust ));
	
	vec4 gamma_v4 = vec4( GAMMA, GAMMA, GAMMA, 1.0 );
	
	vec4 d = pow( texture2D( s_mat_diffuse,  uv_mat * 6.0 ), gamma_v4 );
	vec4 s = pow( texture2D( s_mat_specular, uv_mat * 6.0 ), gamma_v4 );
	
	// vec3 l0_diff_color = vec3( 0.0 );
	// vec3 l1_diff_color = mix( diff_color, d.rgb, d.a ) * mix( diff_color, vec3( 1.0 ), 0.0125 );
	// vec3 l2_diff_color = diff_color;
	
	vec3 l0_diff_color = vec3( 0.0 );
	vec3 l1_diff_color = diff_color * vec3( 0.0666 );
	vec3 l2_diff_color = diff_color * vec3( 0.0100 );
	
	// l0_diff_color = vec3( 0.0 );
	// l1_diff_color = vec3( 0.0 );
	// l2_diff_color = vec3( 0.0 );
	
	
	// vec3 l0_spec_color = vec3( 0.300, 0.300, 0.300 );
	vec3 l0_spec_color = vec3( 1.000, 1.000, 1.000 ) * 0.1;
	vec3 l1_spec_color = vec3( 1.000, 1.000, 1.000 ) * 0.1;
	vec3 l2_spec_color = vec3( 1.000, 1.000, 1.000 ) * 0.9;
	
	
	// float l0_shininess = 0.1;
	// float l1_shininess = 0.1;
	// float l2_shininess = 0.1;
	
	// float l0_reflect_factor = 1.0;
	// float l1_reflect_factor = 0.10;
	// float l2_reflect_factor = 0.1;
	
	// float l0_gloss_factor = 0.05;
	// float l1_gloss_factor = 0.8;
	// float l2_gloss_factor = 1.0;
	
	// float depth = l1_diff_color.r;
	
	//=================
	// Mesh Normal map
	//=================
	
	// float normal_factor = clamp( 2.0 / (1.0 + length( es_pos )), 0.250, 1.0 ) * mix( 1.0, es_normal.z, 0.55 );
	float normal_factor = 1.0;
	// float normal_factor = 1.0;
	float fresnel_factor = 1.0;
	// float normal_factor = 1.0;
	// float normal_factor = es_normal.z;
	// float normal_factor = es_normal.z;
	float l2_spec_mask = 1.0 - pow(1.0 - l2_mask, 4.0);

	vec3  masked_diff = mix( mix( l2_diff_color,   l1_diff_color,   l2_mask      ), l0_diff_color,   l1_mask ) * 1.0;
	vec3  masked_spec = mix( mix( l2_spec_color,   l1_spec_color,   l2_spec_mask ), l0_spec_color,   l1_mask ) * 1.0;
	float masked_refl = clamp( reflect_factor * 3.0, l1_mask, 1.0 );
	
	#if 1
	{
		//=============
		// Mat Normal
		//=============
		vec3 mesh_normal = texture2D( s_mat_normal, uv_mat * 6.0 ).rgb;
		mesh_normal.xy -= vec2( 0.5 );
		mesh_normal.xy *= vec2( normal_factor * ( 1.0 - wear ) * 1.0 );
		mesh_normal     = mat3( es_mat_T, es_mat_B, es_normal )	* mesh_normal;
		//=============
		
		es_N = mesh_normal;
	}
	#endif
	es_N  = normalize( es_N  );		

	//====================
	// Combine components
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













