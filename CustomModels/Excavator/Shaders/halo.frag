#line 1 "halo.frag"
#extension GL_ARB_uniform_buffer_object : enable
//========
// Inputs
//========

uniform int			spot_binding;
uniform sampler2D	s_halo;
uniform sampler2D	s_dust_in_the_air;
uniform mat3		rotationMatrix;
uniform float		osg_SimulationTime;
uniform vec3		light_position;

varying vec2 uv_mesh;
varying vec3 es_normal;
varying vec3 light_color;
varying float energy;
varying float dist;
varying vec3 attr_position;
varying vec3 attr_direction;

/*
struct Light {
	vec3 color;
	float intensity;
	vec3 position;
	float cutoff;
	vec3 direction;
	float attenuation;
	float active;
	float radius;
	float spotfactor;
	float spotshape;
	float ambientfactor;
};


layout(std140) uniform UBOLights 
{
	Light lights[14];
};
*/



float linmap_c(float v, float s0, float s1, float d0, float d1) 
{
	float result = v * (d0 - d1) / (s0 - s1) + (d1 * s0 - d0 * s1) / (s0 - s1);

	float min_limit = min(d0, d1);
	float max_limit = max(d0, d1);

	return clamp( result, min_limit, max_limit );
}


void main()
{
	// vec3 light_position		= lights[0].position;
	// vec3 light_direction	= lights[0].direction;

	vec3 light_position		= attr_position;
	vec3 light_direction	= attr_direction;


	
	float halo = 1.0 - length( vec2(0.5, 0.5) - uv_mesh.xy ) * 2.0;
	#if 0
	float L = halo;
	//halo = 1.0 - ((1.0 - halo) * (1.0 - halo));
	
	if ( uv_mesh.x > 0.49 && uv_mesh.x < 0.51 ) halo = 0.1;
	if ( uv_mesh.y > 0.49 && uv_mesh.y < 0.51 ) halo = 0.1;
	if ( uv_mesh.x > 0.5 && uv_mesh.y > 0.5 ) halo = 0.1;
	
	if ( L < 0.1 ) {
		halo = 100.0;
	}
	
	
	halo = min( 1.0, 1.0 / ( 20.0 * halo + 0.01) );
	#endif


	gl_FragColor.rgba = vec4( halo, halo, halo, 1.0 );
	
	float dust			= 1.0;

	#if 1
	// vec3 uv_anchor = gl_NormalMatrix * light_position;
	float g = osg_SimulationTime * 0.05;
	vec2 basecoord = ( gl_FragCoord.xy - vec2( 920.0, 600.0 ) ) / vec2( 1920.0 - 1200.0 ) * vec2( 2.0, 2.0 );
	// float dust			= texture2D( s_dust_in_the_air,	basecoord ).r;
	
	gl_FragColor.rgba	= texture2D( s_halo, uv_mesh );
	//float dust			= texture2D( s_dust_in_the_air,	( gl_FragCoord.xy + vec2(720, 480) ) * dist * 0.001 ).a;
	/*
	*/
	//dust	*= texture2D( s_dust_in_the_air,	vec2(-g, g) + basecoord * uv_anchor.z * 0.05 ).r;
	dust	*= texture2D( s_dust_in_the_air,	vec2( g, g) + basecoord * 0.10 * 2.0 ).r;
	dust	*= texture2D( s_dust_in_the_air,	vec2( g,-g) + basecoord * 0.20 * 2.0 ).r;
	dust	= 1.0 - pow( 1.0 - dust, 2.0 );
	dust	+= 0.75;
	#endif
	
	float fayFactor = linmap_c( gl_LightSource[0].ambient.r, 0.0, 0.25, 1.0, 0.00 );

	gl_FragColor.rgb	*= energy * dust * light_color * fayFactor;
	// gl_FragColor.a		 = 1.0;

	// gl_FragColor.rgba = vec4( 1.0 );
	// gl_FragColor.rgba = vec4( 1.0, 0.0, 0.0, 1.0 );
	
	// gl_FragColor.rgba = vec4( 1.0, 0.0, 0.0, 1.0 );
}


















