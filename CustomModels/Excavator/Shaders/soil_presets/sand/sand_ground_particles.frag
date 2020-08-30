#version 130
#extension GL_EXT_gpu_shader4 : enable
#extension GL_ARB_gpu_shader5 : enable
#line 4 "ground_particles.frag"

#include ../../common/combine.frag
float linmap( float v, float s0, float s1, float d0, float d1 );
float linmap_c( float v, float s0, float s1, float d0, float d1 );
vec3 terrain_combine( vec3 es_N, vec4 es_pos, vec3 diff_color, float ao );
void saturate( inout vec3 color, float factor );


uniform sampler2D s_half_space_data;

uniform uint NUM_VOLUMES;

uniform uint HALFSPACE_DATA_OFFSET_0;
uniform uint HALFSPACE_DATA_OFFSET_1;
uniform uint HALFSPACE_DATA_OFFSET_2;
uniform uint HALFSPACE_DATA_OFFSET_3;

uniform uint NUM_HALFSPACES_0;
uniform uint NUM_HALFSPACES_1;
uniform uint NUM_HALFSPACES_2;
uniform uint NUM_HALFSPACES_3;

uint HALFSPACE_DATA_OFFSET[4] = uint[4]
(
	HALFSPACE_DATA_OFFSET_0,
	HALFSPACE_DATA_OFFSET_1,
	HALFSPACE_DATA_OFFSET_2,
	HALFSPACE_DATA_OFFSET_3
);
uint NUM_HALFSPACES[4] = uint[4]
(
	NUM_HALFSPACES_0,
	NUM_HALFSPACES_1,
	NUM_HALFSPACES_2,
	NUM_HALFSPACES_3
);

//========
// Inputs
//========
in vec4 VS_es_pos;
in vec4 VS_ws_pos;
in vec4 VS_ws_group_center;
in vec2 VS_uv_mesh;
in vec3 VS_es_T;
in vec3 VS_es_B;
in vec4 VS_color;
in float VS_angle;
in float VS_death_cycles;
in float VS_velocity_magnitude;

//===================
// Mesh samplers
//===================
uniform sampler2D s_elevation;
uniform sampler2D s_diffuse;
uniform sampler2D s_normal;
uniform sampler2D s_specular;



void intersectPassiveVolume( vec4 ws_point, out bool insideAnyVolume, out bool insideAllVolumes, out float relief, float wall_offset )
{

	float _insideAnyVolume = 0.0;
	insideAllVolumes = true;

	for ( uint halfSpaceVolumeIndex = 0u; halfSpaceVolumeIndex < NUM_VOLUMES; ++halfSpaceVolumeIndex )
	{
		uint halfSpaceDataIndexOffset = HALFSPACE_DATA_OFFSET[ halfSpaceVolumeIndex ];
		const uint ROW_HALFSPACE_POS	= 0u;
		const uint ROW_HALFSPACE_NORMAL	= 1u;

		bool inCurrentVolume = true;	// initially true
		uint numHalfSpaces = NUM_HALFSPACES[ halfSpaceVolumeIndex ];
		relief = 1.0;
		// particles outside passive volume are marked as such
		for (uint halfspace_i = 0u; halfspace_i < numHalfSpaces; ++halfspace_i )
		{
			vec3 wall_nor = texelFetch( s_half_space_data, ivec2( halfspace_i + halfSpaceDataIndexOffset, ROW_HALFSPACE_NORMAL ), 0 ).rgb;
			vec3 wall_pos = texelFetch( s_half_space_data, ivec2( halfspace_i + halfSpaceDataIndexOffset, ROW_HALFSPACE_POS    ), 0 ).rgb;
			wall_pos += wall_nor * wall_offset;

			vec3 v0 = normalize( ws_point.xyz - wall_pos );
			vec3 v1 = wall_nor;

			float s = min( 1.0, length( max(0.0, dot(-wall_nor,v0)) * (ws_point.xyz - wall_pos) ) * 16.0 );

			float inside = dot( v0, v1 );

			if ( inside >= 0.0 )
			{
				inCurrentVolume = false;
				insideAllVolumes = false;
			}
			relief = min( relief, s );
		}  // for each halfspace

		if ( inCurrentVolume )
		{
			_insideAnyVolume += 1.0;
		}
		halfSpaceDataIndexOffset += numHalfSpaces;
	} // for each volume

	insideAnyVolume = _insideAnyVolume > 0.0;
}


vec4 texture2D_rot( sampler2D s )
{
	vec2 uv_01 = ( VS_uv_mesh - vec2( 0.5 ) ) * vec2( 2.0 );
	float distFromPuffCenter = length( uv_01 );
	float alphaCut = float( distFromPuffCenter < 1.0 );

	vec2 uv = VS_uv_mesh;

	// rotate texture
	mat2 R  = mat2(  cos( VS_angle ), sin( VS_angle ),
					-sin( VS_angle ), cos( VS_angle )
					);
	uv = R * ( ( uv - vec2( 0.5 )) * vec2( 2.0 ) );
	uv	   += vec2( 1.0 );
	uv	   *= vec2( 0.5 );
	return pow( texture2D( s, uv ) * alphaCut, vec4( 2.2, 2.2, 2.2, 1.0 ) );
}



void main()
{
	const vec4 TO_LINEAR = vec4( 2.200000, 2.200000, 2.200000, 1.0 );
	const vec4 TO_sRGB   = vec4( 0.454545, 0.454545, 0.454545, 1.0 );

	vec4 D = texture2D_rot( s_diffuse );
	// D = vec4( 0.36859092219748707, 0.23099812432326744, 0.07592611945626479, D.a );

	D     = vec4( 0.00, 0.00, 0.00, D.a );
	D.rgb = mix( D.rgb, vec3( 0.579, 0.329, 0.170 ), 0.20 );
	saturate( D.rgb, -0.25 );

	vec3 es_N = vec3( 0.0, 0.0, 1.0 );

    float dissolve = D.a - ( 1.0 - VS_death_cycles ) * 2.0 + 1.0;
    float alpha = 1.0;
    #if 1
	{
		//=============
		// Mesh Normal
		//=============
		vec4 mesh_normal_alpha = texture2D( s_normal, VS_uv_mesh );
		// alpha = mesh_normal_alpha.a;
		vec3 mesh_normal = mesh_normal_alpha.rgb;
		// mesh_normal.xy *= vec2( 0.5 );
		alpha = mesh_normal_alpha.a;

		mesh_normal.xy  -= vec2( 0.5 );
		mesh_normal      = mat3( VS_es_T, VS_es_B, vec3( 0.0, 0.0, 1.0 ) ) * mesh_normal;
		mesh_normal.z   *= 0.40;
		es_N             = mesh_normal;
		es_N.y += 0.3;
		es_N             = normalize( es_N );
	}
	#endif



	bool group_insideAnyVolume    = false;
	bool group_insideAllnyVolumes = false;
	float group_relief            = 0.0;
	float group_wall_offset       = 0.0;
    intersectPassiveVolume( VS_ws_group_center, group_insideAnyVolume, group_insideAllnyVolumes, group_relief, group_wall_offset );

    bool insideAnyVolume  = false;
	bool insideAllVolumes = false;
	float relief          = 0.0;
	float wall_offset     = -0.01;
    intersectPassiveVolume( VS_ws_pos, insideAnyVolume, insideAllVolumes, relief, wall_offset );

    if ( insideAllVolumes == false && group_insideAllnyVolumes == true )
    {
    	discard;
    }


    //====================
	// Combine components
	//====================

	gl_FragColor.rgb = terrain_combine( es_N, VS_es_pos, D.rgb, mix( 1.0, es_N.y + 0.5, 0.5 ) * 0.40 );

    if ( ( dissolve * alpha ) < 0.7 )
    {
    	discard;
    }
    // gl_FragColor.rgb = vec3( dissolve );
    gl_FragColor.a = 1.0;
}
