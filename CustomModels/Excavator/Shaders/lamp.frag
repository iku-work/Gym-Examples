#line 1 "lamp.frag"

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
float linmap_c(float v, float s0, float s1, float d0, float d1);
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
uniform sampler2D s_mat_normal;
uniform sampler2D s_mat_diffuse;
uniform sampler2D s_mat_specular;

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
	
	float ao         = 1.0;	//texture2D( s_mat_ao, uv_mesh ).r;
	float alpha      = gl_FrontMaterial.diffuse.a;
	
	//=================
	// Source material
	//=================
	
	diff_color = gl_FrontMaterial.diffuse.rgb;
	spec_color = gl_FrontMaterial.specular.rgb;
	ambi_color = gl_FrontMaterial.ambient.rgb;
	emit_color = gl_FrontMaterial.emission.rgb;
	
	vec2 uv = uv_mesh * 10.0;
	vec4 mD = pow( texture2D( s_mat_diffuse,  uv ),	vec4( GAMMA,GAMMA,GAMMA, 1.0 ) );
	vec4 MS = pow( texture2D( s_mat_specular, uv ),	vec4( GAMMA,GAMMA,GAMMA, 1.0 ) );
	
	
	// diff_color  = mix( diff_color, mD.rgb, mD.a );
	spec_color  *= MS.rgb;
	
	alpha = max( alpha, mD.a );
	vec3 es_N = es_normal;
	
	
	//=================
	// Mesh Normal map
	//=================
	
	float normal_factor = clamp( 0.5 / (1.0 + length( es_pos )), 0.0, 1.0 );
	// float normal_factor = 0.250;
	
	#if 1
	{
		//=============
		// Mesh Normal
		//=============
		vec3 mesh_normal = texture2D( s_mat_normal, uv ).rgb;
		mesh_normal.xy -= vec2( 0.5 );
		mesh_normal.xy *= vec2( normal_factor * -1.50 );
		
		mesh_normal     = mat3( es_T, es_B, es_normal )	* mesh_normal;
		
		es_N = mesh_normal;
	}
	#endif
	es_N = normalize( es_N );

	
	//====================
	// Combine components
	//====================
	float directional = dot( normalize( -es_pos.xyz ), es_N );
	// emit_color = vec3(1.0, 0.0, 0.0) * mix( mD.r, 1.0, 0.1 ) * pow( linmap_c( es_N.z, 0.8, 0.9, 0.4, 1.0 ), 2.0) * 2.0;
	emit_color = gl_FrontMaterial.diffuse.rgb * mix( mD.r, 1.0, 0.1 ) * pow( linmap_c( directional, 0.0, 0.4, 0.4, 1.0 ), 2.0) * 1.0;
	
	vec3 es_r = refract( normalize(-es_pos.xyz), es_N, 1.0);

	// vec3 es_r = refract( normalize(-es_pos.xyz), es_N, 0.82);
	float refract_light_intensity = (-es_r.z * 0.5 + 0.5);
	// float refract_light_intensity = max( 0.0, -es_r.z );
	refract_light_intensity *= refract_light_intensity;
	refract_light_intensity *= refract_light_intensity;
	refract_light_intensity *= 4.0;
	emit_color = diff_color * vec3(refract_light_intensity);
	// emit_color = vec3(refract_light_intensity);

	float intensity = 1.0;
	float ref = 0.8;
	// if ( length( es_r ) == 0 )
	{
		intensity = 1.0 - clamp( normalize( es_normal ).z, 0.0, 1.0 );
		intensity *= intensity;
		intensity *= intensity;
		// intensity *= intensity;
		intensity *= 8.0;
		// intensity = 1.0 - intensity;
		// intensity = min( intensity, 1.0 );

		emit_color += diff_color * vec3(intensity);
		// ref = 1.0;
	}
	emit_color = mix( emit_color, diff_color * 0.1, 0.5 );
	// emit_color *= vec3(1.0, 0.7, 0.3);

	gl_FragColor.rgb	= combine(	normalize( es_N ), // vec3 es_N
									es_pos,				// vec4 es_pos
									vec3(0.0),			// vec3 diff_color
									vec3(1.0),    		// vec3 spec_color
									vec3(0.0),     		// vec3 ambi_color
									emit_color,			// vec3 emit_color
									ao,            		// float ao
									0.09				// float reflect_factor
									);
	//====================
	// Gamma correction
	//====================

	gl_FragColor.a   = 1.0;
	// gl_FragColor.rgb   =  texture2D( s_mat_normal, uv_mesh ).rgb;
	// gl_FragColor.rgb   = es_B;
	// gl_FragColor.rgb   = es_N;

	// gl_FragColor.rgb   = mD.rgb;
	// gl_FragColor.rgb   = mD.rgb;
	// gl_FragColor.rgb   = diff_color.rgb;
	// gl_FragColor.rgb   = r.rgb;
	// gl_FragColor.rgb   = vec3(emit_color);
	// gl_FragColor.rgb   = vec3(intensity);
	// gl_FragColor.rgb   = vec3(1.0);
	
}



