#line 1 "diffuse.frag"

#include ../Shaders/common/combine.frag
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
varying vec4 color;
varying vec4 es_pos;
varying vec2 uv_mesh;
varying vec2 uv_mat;
varying vec3 es_normal;

varying vec3 es_T;
varying vec3 es_B;

//===================
// Mesh samplers
//===================
uniform sampler2D s_mesh_diffuse;
uniform sampler2D s_mesh_specular;
uniform sampler2D s_mesh_ao;

uniform float reflect_factor;
uniform float gloss_factor;




void main()
{
	const float GAMMA = 2.2;
	
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
	
	float ao         = 1.0;	//texture2D( s_mesh_ao, uv_mesh ).r;
	float alpha      = gl_FrontMaterial.diffuse.a;
	
	//=================
	// Source material
	//=================
	
	diff_color = gl_FrontMaterial.diffuse.rgb;
	spec_color = gl_FrontMaterial.specular.rgb;
	ambi_color = gl_FrontMaterial.ambient.rgb;
	emit_color = gl_FrontMaterial.emission.rgb;
	
	vec4 mD = pow( texture2D( s_mesh_diffuse,  uv_mat  ),	vec4( GAMMA,GAMMA,GAMMA, 1.0 ) );
	vec4 mS = pow( texture2D( s_mesh_specular, uv_mat  ),	vec4( GAMMA,GAMMA,GAMMA, 1.0 ) );
	ao      = pow( texture2D( s_mesh_ao,       uv_mesh ).r, GAMMA );
	
	
	diff_color  = mix( diff_color, mD.rgb, mD.a );
	spec_color  = vec3( mS.r );
	
	alpha = max( alpha, mD.a );
	vec3 es_N = es_normal;
	es_N = normalize( es_N );

	
	//====================
	// Combine components
	//====================

	gl_FragColor.rgb	= combine(	es_N,           	// vec3 es_N
									es_pos,				// vec4 es_pos
									diff_color,     	// vec3 diff_color
									spec_color * 4.0,   // vec3 spec_color
									ambi_color,     	// vec3 ambi_color
									emit_color,     	// vec3 emit_color
									ao,            		// float ao
									reflect_factor		// float reflect_factor
									);
	// gl_FragColor.rgb = vec3( ao );
	// gl_FragColor.rgb = vec3( mD );
	gl_FragColor.a   = 1.0;
}



