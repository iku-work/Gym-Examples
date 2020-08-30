#version 130
#line 2 "ground_particles.vert"
#extension GL_EXT_gpu_shader4 : enable
#extension GL_ARB_gpu_shader5 : enable


//=========
// Outputs
//=========
out vec4 VS_es_pos;
out vec4 VS_ws_pos;
out vec4 VS_ws_group_center;
out vec2 VS_uv_mesh;
out vec3 VS_es_T;
out vec3 VS_es_B;
out vec4 VS_color;
out float VS_angle;
out float VS_death_cycles;
out float VS_velocity_magnitude;

uniform uint MAX_PARTICLES;			// texture u resolution
uniform uint NUM_CHANNELS;			// texture v resolution
uniform uint MULTIPLE_PARTICLES;	// how many times each particle is duplicated
uniform uint PARTICLE_DEATH_CYCLES; // how many frames a particle will remain visible after it has died
uniform uint osg_FrameNumber;

uniform sampler2D s_particle_data;
uniform sampler2D s_half_space_data;
uniform sampler2D s_random;


//==================================
// random texture unpack parameters
//==================================
#define COMPONENT_NOISE_BINARY   0u
#define COMPONENT_NOISE_01       1u
#define COMPONENT_NOISE_11       2u
#define COMPONENT_NOISE_GAUSSIAN 3u
//==================================
// particle data unpack paramters
//==================================
#define ROW_POSITION_ID    0u
#define ROW_VELOCITY_AGE   1u
//==================================

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


mat2 projectToXYPlane( vec4 ws_point0, vec4 ws_vel, out float stretch )
{	
	ws_point0.w = 1.0;
	ws_vel.w = 0.0;

	vec2 viewportTransform = vec2( 1918.0, 1136.0 ) / vec2(1918.0);	//XXX: magic viewport size

	// to clip space
	vec4 ps_point0 = gl_ProjectionMatrix * gl_ModelViewMatrix *  ws_point0;
	vec4 ps_point1 = gl_ProjectionMatrix * gl_ModelViewMatrix * (ws_point0 + normalize(ws_vel));

	// transform to NDC
	vec4 ndc_point0 = ps_point0 / ps_point0.w;
	vec4 ndc_point1 = ps_point1 / ps_point1.w;

	// to screen space
	vec2 ss_point0 = (ndc_point0.xy * viewportTransform);
	vec2 ss_point1 = (ndc_point1.xy * viewportTransform);

	vec2 ss_x	= normalize(ss_point1 - ss_point0);

	float d = length(ss_point0 - ss_point1);

	mat3 NM = gl_NormalMatrix;	//XXX: check
	NM[0] = normalize( NM[0] );
	NM[1] = normalize( NM[1] );
	NM[2] = normalize( NM[2] );

	stretch = 1.0 / length( (NM * ws_vel.xyz).xy );
	stretch = max( stretch, 0.0 );
	stretch = min( stretch, 1.0 );

	mat2 R = mat2(	vec2(  ss_x.x, -ss_x.y ),
					vec2(  ss_x.y,  ss_x.x )
					);
	return R;
}


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

mat4 meveaToWorld = mat4(   1.0,  0.0,  0.0,  0.0,
						    0.0,  0.0,  1.0,  0.0,
						    0.0, -1.0,  0.0,  0.0,
						    0.0,  0.0,  6.5,  1.0
							);

float linmap_c(float v, float s0, float s1, float d0, float d1) 
{
	float result = v * (d0 - d1) / (s0 - s1) + (d1 * s0 - d0 * s1) / (s0 - s1);

	float min_limit = min(d0, d1);
	float max_limit = max(d0, d1);

	return clamp( result, min_limit, max_limit ); 
}

vec2 abs_uv( uint c, uint r )
{
	return vec2(	float(c) / float(MAX_PARTICLES) + (0.5 / float(MAX_PARTICLES)),
					float(r) / float(NUM_CHANNELS)  + (0.5 / float(NUM_CHANNELS)) 
					);
}

vec4 getParticleData( uint particle_id, uint datatype_index )
{
	return texture2D( s_particle_data, abs_uv( particle_id, datatype_index ) );
}

vec4 getRandom( uint particle_id )
{
	return texture2D( s_random, abs_uv( particle_id, 0u ) );
}

const int dynamic_shadow_uv_index = 0;

//void mev_DynamicShadow( in vec4 ecPosition )
//{                                        
//    // generate coords for shadow mapping
//    gl_TexCoord[dynamic_shadow_uv_index].s = dot( ecPosition, gl_EyePlaneS[dynamic_shadow_uv_index] );
//    gl_TexCoord[dynamic_shadow_uv_index].t = dot( ecPosition, gl_EyePlaneT[dynamic_shadow_uv_index] );
//    gl_TexCoord[dynamic_shadow_uv_index].p = dot( ecPosition, gl_EyePlaneR[dynamic_shadow_uv_index] );
//    gl_TexCoord[dynamic_shadow_uv_index].q = dot( ecPosition, gl_EyePlaneQ[dynamic_shadow_uv_index] );
//}



void main()
{
	// clever trick (not) to get scale relative to world
	float world_scale = 1.0 / length( gl_ModelViewMatrix[0].xyz );

	uint nth_group		= gl_InstanceID / MULTIPLE_PARTICLES;	// Unrelated to actual IDs. These will fluctuate as particle numbers vary.
	uint nth_particle	= gl_InstanceID % MULTIPLE_PARTICLES;	// Unrelated to actual IDs. These will fluctuate as particle numbers vary.

	//=========================================================================================================================
	// unpack input data
	//=========================================================================================================================
	vec4 _data_position_id	= texelFetch( s_particle_data, ivec2( nth_group, ROW_POSITION_ID  ), 0 );	// extract actual group properties
	vec4 _data_velocity_age	= texelFetch( s_particle_data, ivec2( nth_group, ROW_VELOCITY_AGE ), 0 );	// extract actual group properties
	uint _group_id			= ( uint( _data_position_id.w )                ) % MAX_PARTICLES;
	uint _particle_id		= ( uint( _data_position_id.w ) + nth_particle ) % MAX_PARTICLES;
	//=========================================================================================================================
	vec4 instance_velocity	 = vec4( _data_velocity_age.xyz, 0.0 );
	vec4 instance_position   = vec4( _data_position_id.xyz,  1.0 );
	float age                = _data_velocity_age.w;
	float velocity_magnitude = length( instance_velocity.xyz );
	//=========================================================================================================================
	vec4 group_noise01       = texelFetch( s_random, ivec2( _group_id,         COMPONENT_NOISE_01       ), 0 );			// linear noise [ 0, 1]
	vec4 group_noise11       = texelFetch( s_random, ivec2( _group_id,         COMPONENT_NOISE_11       ), 0 );			// linear noise [-1, 1]
	vec4 group_noise2        = texelFetch( s_random, ivec2( _group_id,         COMPONENT_NOISE_GAUSSIAN ), 0 );			// gaussian noise
	vec4 particle_noise01    = texelFetch( s_random, ivec2( _particle_id + 13, COMPONENT_NOISE_01       ), 0 );			// linear noise [ 0, 1]
	vec4 particle_noise11    = texelFetch( s_random, ivec2( _particle_id + 13, COMPONENT_NOISE_11       ), 0 );			// linear noise [-1, 1]
	vec4 particle_noise2     = texelFetch( s_random, ivec2( _particle_id + 50, COMPONENT_NOISE_GAUSSIAN ), 0 );			// gaussian noise
	//=========================================================================================================================

	bool group_insideAllnyVolumes = false;
	{
		bool group_insideAnyVolume    = false;
		float group_relief            = 0.0;
		float group_wall_offset       = 0.0;
    	intersectPassiveVolume( instance_position, group_insideAnyVolume, group_insideAllnyVolumes, group_relief, group_wall_offset );
	}

	age = abs( age );
	float death_cycle = linmap_c( age, 0.0, PARTICLE_DEATH_CYCLES, 1.0, 0.0 );

	float directional_stretch_multiplier = 1.0;
	mat2 R = projectToXYPlane( instance_position, instance_velocity, directional_stretch_multiplier );

	vec4 es_instance_pos  = gl_ModelViewMatrix * instance_position;
	es_instance_pos.w     = 1.0;

	// float scale = 0.02 * particle_noise2.w + 0.1;
	float scale	= abs( 0.010 * ( particle_noise01.w + 0.05 ) );
	if ( nth_particle == 0 && group_insideAllnyVolumes )
	{
		scale = 0.10 * group_noise01.r + 0.02;// + linmap_c( velocity_magnitude, 0.02, 4.0, 0.0, 0.4 );
	}
	else if ( ! group_insideAllnyVolumes )
	{
		// scale *= 0.25;//1linmap_c( velocity_magnitude, 0.02, 4.0, 1.0, 1 );
		scale = 0.04;
	}

	scale = mix( scale, 0.04, 0.55 );

	// if ( velocity_magnitude <= 2.1 + particle_noise11.x )
		R = mat2( 	 cos( particle_noise2.z * 3.14 ), -sin( particle_noise2.z * 3.14 ),
					 sin( particle_noise2.z * 3.14 ),  cos( particle_noise2.z * 3.14 )
					 );

//	vec4 es_noise_offset = vec4( vec2(	0.0 + ( 0.0500 + velocity_magnitude * .0120 ) * particle_noise2.x,
//										0.0 + ( 0.0100 + velocity_magnitude * .0050 ) * particle_noise11.z  
//										) * R,
//								 ( 0.0120 + velocity_magnitude * 0.006 ) * particle_noise2.y,
//								 0.0 
//								 );


	vec4 es_noise_offset = vec4( vec2(	0.0 + ( 0.0700 + instance_velocity.x * .0120 ) * particle_noise2.x,
										0.0 + ( 0.0700 + instance_velocity.y * .0150 ) * particle_noise11.z  
										) * R,
									( 0.070 + instance_velocity.z * 0.006 ) * particle_noise2.y,
									0.0 
									);

								 
	//===================================================================
	// TRANSFORM
	//===================================================================

	//===============
	// modify vertex
	//===============
	mat2 R_I    = transpose(R);
	VS_es_T     = vec3( R_I[0].xy, 0.0 );
	VS_es_B     = vec3( R_I[1].xy, 0.0 );
	vec4 vertex = gl_Vertex * vec4( vec3(scale), 1.0 );
	vertex.w    = 1.0;
	// vertex.x   *= min( 2.0, 1.00 / directional_stretch_multiplier );		// stretch
	// vertex.y   *= max( 1.0,        directional_stretch_multiplier );		// stretch
	vertex.xy   = vertex.xy * R;		



	vec4 es_Position = ( es_instance_pos + es_noise_offset );
	es_Position.xy += vertex.xy;	// apply geometry position



	gl_Position           = gl_ProjectionMatrix * es_Position;
	VS_es_pos	          = es_Position;
	VS_ws_pos             = inverse( gl_ModelViewMatrix ) * es_Position;
	VS_ws_group_center    = instance_position;
	VS_uv_mesh	          = gl_Vertex.xy * 0.5 + vec2( 0.5 );
	VS_color	          = vec4( 0.0, 0.0, 0.0, 1.0 );
	VS_death_cycles       = death_cycle;
	VS_velocity_magnitude = velocity_magnitude;

}



