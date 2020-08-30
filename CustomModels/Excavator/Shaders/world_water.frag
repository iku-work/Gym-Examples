#version 120
#line 2 "world.frag"

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
float linmap( float v, float s0, float s1, float d0, float d1 );
float linmap_c(float v, float s0, float s1, float d0, float d1);
float rough_mix( float control, float sharp, float bias );
vec3 BRDF_cook_torrance( vec3 N, vec3 L, vec3 V, vec3 F0, float alpha );
vec3 F( vec3 L, vec3 H, vec3 F0 );
vec3 mev_ambient_light();
void fog( in vec3 es_pos, inout vec3 color );

// varyings
varying vec4 color;
varying vec4 es_pos;
varying vec4 ws_pos;
varying vec2 uv_mesh;
varying vec3 es_normal;

// samplers
uniform sampler2D s_water_normal;
uniform float osg_SimulationTime;

const float GAMMA = 2.2;

vec3 ambientLightColor = pow( vec3( 0.5311306, 0.6244575, 0.7947322 ), vec3( 2.2 ) ) * 0.3;

void fog2( in vec3 es_pos, inout vec3 color )
{
	float L = length( es_pos );
	float e = 2.718281828459045;
	float transmittance = pow( e, ( -0.2 * gl_Fog.density ) * L );
	vec3 fog_color = vec3( 1.0 );
	color = mix( fog_color, color, transmittance );
}

vec3 getWsNormal()
{
	vec3 source_N = vec3( 0.0 );
	source_N += texture2D( s_water_normal, uv_mesh.xy * 16.0 + vec2( osg_SimulationTime * 0.005 ) ).xyz;
	source_N += texture2D( s_water_normal, uv_mesh.yx * 16.0 + vec2( osg_SimulationTime * -0.005 ) ).xyz;
	source_N *= 0.5;
	vec3 ws_N = vec3( 0.0, 0.0, 0.0 );

	ws_N.x = source_N.y;
	ws_N.y = 1;
	ws_N.z = source_N.x;

	ws_N -= vec3( 0.5 );
	ws_N *= vec3( 2.0 );
	ws_N.t *= 4.0;

	ws_N = normalize( ws_N );
	return ws_N;	
}

vec3 getEsNormal()
{
	return gl_NormalMatrix * getWsNormal();
}

void main()
{
	vec3 ws_N = getWsNormal();
	vec3 es_N = getEsNormal();
	vec3 es_E = normalize( -es_pos.xyz );
	vec3 ws_R = transpose( gl_NormalMatrix ) * reflect( es_E, es_N );
	vec3 ws_H = normalize( es_E + ws_R );
	// vec3 es_L = normalize( gl_LightSource[0].position.xyz );
	vec3 es_L = gl_NormalMatrix * normalize( vec3( 0.708, 0.2167, 0.671 ) );
	// gl_FragColor.rgb = mix( vec3( 0.25 ), ambientLightColor, abs( ws_R.y ) ) * 4.0;

	float alpha = mix( 0.025, 0.005, pow( ws_N.y, 256.0 ) ) * 2.5;
	// alpha *= alpha;
	alpha = pow( alpha, 1.8 );
	vec3 spec_light = BRDF_cook_torrance( es_N, es_L, -es_E, vec3( 0.04 ), alpha );


	gl_FragColor.rgb = mev_ambient_light() * 0.005
					 + spec_light * 200;


	fog( es_pos.xyz * 0.25, gl_FragColor.rgb );

	gl_FragColor.rgb = pow( gl_FragColor.rgb, vec3( 1.0 / GAMMA ) );
	gl_FragColor.a = 0.98;
}

