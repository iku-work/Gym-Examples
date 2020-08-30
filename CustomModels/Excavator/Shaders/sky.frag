#version 120
#line 2 "sky.frag"

varying vec2 uv_mesh;
varying vec3 skyDir;
varying vec3 ws_direction;
varying vec3 ws_sunDirection;
varying vec3 es_pos;

uniform bool fogOn;
uniform samplerCube s_environment;
uniform sampler2D   s_panorama;
uniform sampler2D   texture;	// ephemeris

#include common/combine.frag
float linmap(float v, float s0, float s1, float d0, float d1); 
float linmap_c(float v, float s0, float s1, float d0, float d1);
vec3 mev_ambient_light();
vec3 sampleSunHalo( vec3 ws_direction, vec3 ws_sunDirection );
void fog( in vec3 es_pos, inout vec3 color );
void toneMap( inout vec3 color );



void main() 
{
	gl_FragColor = vec4( 0.0, 0.0, 0.0, 1.0 );

	float skyGradient = linmap( dot( -ws_sunDirection, ws_direction ), -1.0, 0.0, 0.250, 1.0 );

	vec2 ws_sunDirectionXZ = normalize( ws_sunDirection.xz );
	float sun_angle = -atan( ws_sunDirectionXZ.x, ws_sunDirectionXZ.y ) - 0.1;

	vec2 uv_panorama = uv_mesh;
	uv_panorama.y        = linmap_c( uv_panorama.y, 0.5, 1,  1.0, 0.0 );
	uv_panorama.x       += sun_angle / 3.141592653589793;
	float panorama_blend = linmap_c( uv_panorama.y, 0.25, 0.75,  0.0, 1.0 );
	float haze_blend     = linmap_c( uv_panorama.y, 0.0, 0.08,  1.0, 0.0 );
	haze_blend     		*= haze_blend;
	
	vec3 panorama	= vec3( 0.0 );
	panorama		+= pow( texture2D( s_panorama, uv_panorama ).rgb, vec3(  2.2 ) );
	panorama		+= pow( texture2D( s_panorama, uv_panorama + vec2(3.4, 0.0) ).rgb, vec3(  2.2 ) );
	panorama = mix( panorama, vec3( 0.40, 0.40, 0.40 ) * 1.0, haze_blend * haze_blend );
	panorama = mix( panorama, vec3( 0.20, 0.25, 0.35 ) * 2.0, panorama_blend );
	panorama *= mev_ambient_light();
	
	vec3 halo = sampleSunHalo( ws_direction, ws_sunDirection );
	panorama += halo * 0.2;
	
	gl_FragColor.rgb = panorama;
	// gl_FragColor.rgb *= skyGradient;


	vec3 es_pos_fog = es_pos;
	es_pos_fog = normalize( es_pos_fog );
	es_pos_fog *= linmap_c( haze_blend, 0.0, 1.0, 2000.0, 5000.0 );

	fog( es_pos_fog, gl_FragColor.rgb );
	toneMap( gl_FragColor.rgb );

	gl_FragColor.a = 1.0;
}



