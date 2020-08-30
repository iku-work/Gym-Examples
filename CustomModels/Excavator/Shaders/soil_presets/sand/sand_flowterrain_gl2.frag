#version 130
#extension GL_EXT_gpu_shader4 : enable
#extension GL_ARB_gpu_shader5 : enable
#extension GL_ARB_uniform_buffer_object : enable
#line 5 "flowterrain_gl2.frag"

#include ../../common/combine.frag
float linmap( float v, float s0, float s1, float d0, float d1 );
float linmap_c( float v, float s0, float s1, float d0, float d1 );
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

uniform mat4 osg_ModelViewMatrix;
uniform mat3 osg_NormalMatrix;
uniform mat4 osg_ProjectionMatrix;
uniform mat4 osg_ViewMatrixInverse;
uniform uint osg_FrameNumber;

uniform ivec2 flowTerrainSize;
uniform vec2 flowTerrainMetric;

uniform sampler2D		s_elevation;
uniform samplerCube		s_environment;
uniform sampler2DShadow	shadowTexture;

uniform sampler2D s_input_00;
uniform sampler2D s_input_01;
uniform sampler2D s_input_02;

in vec4 VS_es_pos;
in vec3 VS_es_normal;
in vec3 VS_es_tangent;
in vec3 VS_es_bitangent;
in vec2 VS_uv_mesh;
in vec4 VS_uv_shadow;
in vec4 VS_color;





vec4 terrainNormal( vec2 uv )
{
	const float ELEVATION_LOD = 0.5;
    float s11 = texture2DLod( s_elevation, uv, ELEVATION_LOD ).x;
    float s01 = texture2DLodOffset( s_elevation, uv, ELEVATION_LOD, ivec2( -1,  0 )  ).x;
    float s21 = texture2DLodOffset( s_elevation, uv, ELEVATION_LOD, ivec2(  1,  0 )  ).x;
    float s10 = texture2DLodOffset( s_elevation, uv, ELEVATION_LOD, ivec2(  0, -1 )  ).x;
    float s12 = texture2DLodOffset( s_elevation, uv, ELEVATION_LOD, ivec2(  0,  1 )  ).x;

    vec2 s  = pow( flowTerrainMetric / vec2( flowTerrainSize ) * vec2( 2.0 ), vec2( ELEVATION_LOD ) );
    vec3 va = normalize( vec3( s.x, 0,   s21 - s01 ) );
    vec3 vb = normalize( vec3( 0,   s.y, s12 - s10 ) );
    vec4 bump = vec4( cross( va, vb ), s11 );
    return bump;
}

float parabola01( float x )
{
	return clamp( 1.0 - pow( x * 2.0 - 1.0, 2.0 ), 0.0, 1.0 );
}

void tonemap( inout vec4 color )
{
	color = pow( color, vec4( 0.454545, 0.454545, 0.454545, 1.0 ) );
}


vec3 getDiffuseColor()
{
	// blend diffuse color
	vec2 uv_meters = VS_uv_mesh * vec2( flowTerrainSize );
	vec3 gravel = pow( texture2D( s_input_01, uv_meters * ( 1.0 / 64.0 ) ).rgb, vec3( 2.2 ) );
	gravel      = mix( gravel, vec3( 0.579, 0.329, 0.170 ), 0.25 );
	return gravel;
}

void main() 
{
 	// float debug_a = ( sin( float( osg_FrameNumber ) * 0.1 ) * 0.5 + 0.5 );
 	float debug_a = sin( float( osg_FrameNumber ) * 0.1 );
 	//=================================================================

	vec2 uv_meters = VS_uv_mesh * vec2( flowTerrainSize );

	vec3 input_0    = pow( texture2D( s_input_00, uv_meters * ( 1.0 / 4.0  ) ).rgb, vec3( 2.2 ) );	// normal
	vec3 input_1    = pow( texture2D( s_input_01, uv_meters * ( 1.0 / 16.0 ) ).rgb, vec3( 2.2 ) );	// diffuse
	vec3 input_1_2  = pow( texture2D( s_input_01, uv_meters * ( 1.0 / 128.0 ) ).rgb, vec3( 2.2 ) );	// diffuse
	vec3 input_2    = pow( texture2D( s_input_02, uv_meters * ( 1.0 / 128.0  ) ).rgb, vec3( 2.2 ) );	// ao
	vec3 diff_color = vec3( 0.0, 0.0, 0.0 );

	diff_color = getDiffuseColor();
	float ao   = 1.0;

	float normal_scale    = length( gl_NormalMatrix[0] );
	vec4 normal_elevation = terrainNormal( VS_uv_mesh );
	mat3 NormalMatrix     = gl_NormalMatrix / normal_scale;
	vec3 N = NormalMatrix * normal_elevation.xyz;


	float normal_falloff = clamp( 1.0 / sqrt( length( VS_es_pos.xyz ) ), 0.0, 1.0 );
	float alpha_falloff  = clamp( 2.00 / sqrt( length( VS_es_pos.xyz ) ), 0.0, 1.0 );

	alpha_falloff *= alpha_falloff;
	alpha_falloff *= alpha_falloff;
	alpha_falloff *= 32.0;
	alpha_falloff = clamp( alpha_falloff, 0.0, 1.0 );

	//=================
	// Mesh Normal map
	//=================
	#if 0
	{
		//=============
		// Mesh Normal
		//=============
		vec3 mesh_normal = texture2D( s_input_00, uv_meters * 0.01 ).rgb;
		mesh_normal.xy -= vec2( 0.50 );
		mesh_normal.xy *= vec2( 0.50 );
		mesh_normal = normalize( mesh_normal );
		
		float Tz = dot( normal_elevation.xyz, vec3( 1.0, 0.0, 0.0 ) );
		float Bz = dot( normal_elevation.xyz, vec3( 0.0, 1.0, 0.0 ) );
		vec3 T   = normalize( vec3( 1.0, 0.0, -Tz * 20.0 ) );
		vec3 B   = normalize( vec3( 0.0, 1.0, -Bz * 20.0 ) );

		vec3 es_T = gl_NormalMatrix * T;
		vec3 es_B = gl_NormalMatrix * B;

		mesh_normal = mat3( es_T, es_B, N )	* mesh_normal;	
		
		N = mesh_normal;
		N = normalize( N );
	}
	#endif
	N = normalize( N );

	gl_FragColor.rgb = world_combine(	N,   			// vec3 es_N,
										VS_es_pos,      // vec4 es_pos,
										diff_color,     // vec3 diff_color,
										1.0,            // float shadow,
										ao              // float ao
										);

	gl_FragColor.a = 1.0;
} 

