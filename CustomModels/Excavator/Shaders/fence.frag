#line 1 "self_contained/mesh_ao.frag"

#include common/combine.frag
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
varying vec3 es_normal;

varying vec3 es_T;
varying vec3 es_B;

//===================
// Mesh samplers
//===================
uniform sampler2D s_mesh_normal;
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
	
	vec4 mD = pow( texture2D( s_mesh_diffuse,  uv_mesh ),	vec4( GAMMA,GAMMA,GAMMA, 1.0 ) );
	vec4 MS = pow( texture2D( s_mesh_specular, uv_mesh ),	vec4( GAMMA,GAMMA,GAMMA, 1.0 ) );
	
	
	diff_color  = mix( diff_color, mD.rgb, mD.a );
	spec_color  *= MS.rgb;
	
	alpha = max( alpha, mD.a );
	vec3 es_N = es_normal;
	

	ao = min( color.r, pow( texture2D( s_mesh_ao, uv_mesh ).r, GAMMA ) );
	
	//=================
	// Mesh Normal map
	//=================
	
	// float normal_factor = clamp( 4.0 / (1.0 + length( es_pos )), 0.125, 1.0 );
	float normal_factor = 1.0;
	
	#if 0
	{
		//=============
		// Mesh Normal
		//=============
		vec3 mesh_normal = texture2D( s_mesh_normal, uv_mesh ).rgb;
		mesh_normal.xy -= vec2( 0.5 );
		mesh_normal.xy *= vec2( normal_factor * 2.0 );
		
		mesh_normal     = mat3( es_T, es_B, es_normal )	* mesh_normal;	
		
		es_N = mesh_normal;
	}
	#endif
	es_N = normalize( es_N );

	
	//====================
	// Combine components
	//====================

	gl_FragColor.rgb	= combine(	es_N,           	// vec3 es_N
									es_pos, 			// vec4 es_pos,
									diff_color * mix( ao, 1.0, 0.75 ),     	// vec3 diff_color
									spec_color,     	// vec3 spec_color
									ambi_color,     	// vec3 ambi_color
									emit_color,     	// vec3 emit_color
									ao,            		// float ao
									reflect_factor		// float reflect_factor
									);
	//====================
	// Gamma correction
	//====================

	// gl_FragColor.rgb	= texture2D( s_mesh_normal, uv_mesh ).rgb;
	// gl_FragColor.rgb	= vec3( pow( ao, 0.454545 ) );
	// gl_FragColor.rgb	= color.rgb;
	gl_FragColor.a		= mD.a;
	
}



