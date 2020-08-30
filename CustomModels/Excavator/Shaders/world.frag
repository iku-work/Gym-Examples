#version 120
#line 2 "world.frag"

#include ../Shaders/common/combine.frag
vec3 terrain_combine(	vec3 es_N,
						vec4 es_pos,
						vec3 diff_color,
						float ao
						);
vec3 world_combine(	vec3 es_N,
					vec4 es_pos,
					vec3 diff_color,
					float shadow,
					float ao
					);
float linmap( float v, float s0, float s1, float d0, float d1 );
float linmap_c(float v, float s0, float s1, float d0, float d1);
float rough_mix( float control, float sharp, float bias );
void saturate( inout vec3 color, float factor );
void toneMap( inout vec3 color );

// varyings
varying vec4 color;
varying vec4 es_pos;
varying vec4 ws_pos;
varying vec2 uv_world;
varying vec3 es_normal;

// samplers
uniform sampler2D s_ground_normal;
uniform sampler2D s_ground_light;
uniform sampler2D s_ground_masks;
uniform sampler2D s_ground_grass;
uniform sampler2D s_ground_gravel;
uniform sampler2D s_ground_sand;
uniform sampler2D s_ground_rock_major;
uniform sampler2D s_ground_rock_minor;
uniform sampler2D s_ground_grass_mask;

const float GAMMA = 2.2;

vec3 ambientLightColor = pow( vec3( 0.5311306, 0.6244575, 0.7947322 ), vec3( 2.2 ) ) * 0.75;

void fog2( in vec3 es_pos, inout vec3 color )
{
	float L = length( es_pos );
	float e = 2.718281828459045;
	float transmittance = pow( e, ( -0.1 * gl_Fog.density ) * L );
	vec3 fog_color = vec3( 1.0 );
	color = mix( fog_color, color, transmittance );
}

vec3 getWsNormal()
{
	vec3 source_N = texture2D( s_ground_normal, uv_world ).xyz;
	vec3 ws_N = vec3( 0.0, 0.0, 0.0 );

	ws_N.x = 1.0 - source_N.y;
	ws_N.y = 1;
	ws_N.z = source_N.x;

	ws_N -= vec3( 0.5 );
	ws_N *= vec3( 2.0 );

	ws_N = normalize( ws_N );
	return ws_N;	
}

vec3 getEsNormal()
{
	vec3 es_N = gl_NormalMatrix * getWsNormal();
	return es_N;
}

vec3 triplanar( sampler2D sampler, float scale )
{
	vec3 ws_N = getWsNormal();

	float x_bias = abs( ws_N.x );
	float y_bias = abs( ws_N.y );
	float z_bias = abs( ws_N.z );
	x_bias = pow( x_bias,  8.0 );
	y_bias = pow( y_bias, 32.0 );
	z_bias = pow( z_bias,  8.0 );

	float bias_sum = x_bias + y_bias + z_bias;
	x_bias /= bias_sum;
	y_bias /= bias_sum;
	z_bias /= bias_sum;

	vec4 x_tex = pow( texture2D( sampler, ws_pos.zy * scale ), vec4( GAMMA ) ) * x_bias;
	vec4 y_tex = pow( texture2D( sampler, ws_pos.xz * scale ), vec4( GAMMA ) ) * y_bias;
	vec4 z_tex = pow( texture2D( sampler, ws_pos.xy * scale ), vec4( GAMMA ) ) * z_bias;

	return vec3( x_tex + y_tex + z_tex );
}

float getGrassMask()
{
	float grass_mask = 0.0;
	grass_mask += pow( texture2D( s_ground_grass_mask,  ws_pos.xz / vec2( 48.0 ) ).r, GAMMA );
	grass_mask += pow( texture2D( s_ground_grass_mask,  ws_pos.xz / vec2( 16.0 ) ).r, GAMMA );
	grass_mask *= 0.5;

	float curvature            = pow( texture2D( s_ground_masks, uv_world ).r, GAMMA );
	float world_elevation_term = ( ws_pos.y * 0.15 + 0.9 ) * 0.2;

	float a = ( grass_mask * 2.30 ) + ( curvature * 3.5 ) + world_elevation_term;
	return linmap_c( a, 0.425, 1.0, 0.0, 1.0 );
}



vec3 getAmbientLight()
{
	vec4 light_data    = pow( texture2D( s_ground_light,  uv_world ), vec4( GAMMA, GAMMA, GAMMA, 1.0 ) );
	float static_light = light_data.y;

	float static_ao = light_data.g;
	static_ao *= static_ao;
	static_ao *= static_ao;
	vec3 ambi_light = ambientLightColor * static_ao;
	return ambi_light;
}

float getCurvature()
{
	return pow( texture2D( s_ground_masks, uv_world ).r, GAMMA );
}

vec3 getDiffuseColor()
{
	// blend diffuse color
	vec3 sand       = pow( texture2D( s_ground_sand,    uv_world * vec2( 256.0 ) ).rgb, vec3( GAMMA ) );
	vec3 gravel     = pow( texture2D( s_ground_gravel,  uv_world * vec2( 256.0 ) ).rgb, vec3( GAMMA ) );
	vec3 grass      = pow( texture2D( s_ground_grass,   uv_world * vec2( 128.0 ) ).rgb, vec3( GAMMA ) );
	vec3 rock_major = triplanar( s_ground_rock_major, 0.06125 );
	vec3 rock_minor = triplanar( s_ground_rock_minor, 0.06125 );

	// saturate( grass, -0.5 );
	// saturate( rock_major, -0.5 );
	// saturate( rock_minor, -0.5 );
	// saturate( gravel, 2.5 );
	// rock_major *= 0.5;
	// rock_minor *= 0.5;
	// grass *= 0.5;
	saturate( grass, 0.25 );
	grass = mix( grass, vec3( 0.1, 0.1, 0.01 ), 0.65 );

	gravel = mix( gravel, vec3( 0.579, 0.329, 0.170 ), 0.25 );

	float grass_mask = getGrassMask();
	grass_mask *= color.r;
	vec3 default_terrain_color = mix( gravel, grass, grass_mask );


	float mask_cliff    = texture2D( s_ground_masks,    uv_world ).b;
	// float mask_slipface = texture2D( s_ground_mask_slipface, uv_world ).r;
	mask_cliff    = clamp( mask_cliff + ( 1.0 - color.r ), 0.0, 1.0 );
	// mask_slipface *= ( 1.0 - color.r );


	vec3 diff_color = default_terrain_color;
	diff_color = mix( rock_major, diff_color, mask_cliff );

	float curvature = getCurvature();
	// mix in rock based on curvature
	
	float mask_edge = linmap_c( curvature, 0.056, 0.233, 0.0, 1.0 );
	mask_edge *= color.r;

	diff_color = mix( diff_color, rock_minor, mask_edge );


	// return vec3( mask_cliff ); 
	return diff_color;
}


void main()
{
	vec3 diff_light = vec3( 1.0 );
	vec3 ambi_light = getAmbientLight();
	vec3 diff_color = getDiffuseColor();
	vec3 es_N       = getEsNormal();

	//// combine light and color
	//gl_FragColor.rgb = diff_color * diff_light * 10.0
	//                + diff_color * ambi_light * 10.0;
	//fog2( es_pos.xyz, gl_FragColor.rgb );
	//gl_FragColor.rgb *= 16.0;
	//toneMap( gl_FragColor.rgb );
	

	vec4 light_data     = pow( texture2D( s_ground_light,  uv_world ), vec4( GAMMA, GAMMA, GAMMA, 1.0 ) );
	float static_shadow = light_data.x;
	float static_ao     = light_data.y;

	gl_FragColor.rgb   = world_combine( es_N,           // vec3 es_N,
										es_pos,         // vec4 es_pos,
										diff_color,     // vec3 diff_color,
										static_shadow,  // float shadow,
										static_ao       // float ao
										);
	// gl_FragColor.rgb = diff_light;
	gl_FragColor.a = 1.0;

}

