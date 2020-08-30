#line 1 "halo.vert"
#extension GL_ARB_gpu_shader5 : enable
#extension GL_ARB_uniform_buffer_object : enable

float linmap_c(float v, float s0, float s1, float d0, float d1) 
{
	float result = v * (d0 - d1) / (s0 - s1) + (d1 * s0 - d0 * s1) / (s0 - s1);

	float min_limit = min(d0, d1);
	float max_limit = max(d0, d1);

	return clamp( result, min_limit, max_limit );
}





varying vec2	uv_mesh;
varying vec3	es_normal;
varying vec3	light_color;
varying float	energy;
varying float	dist;
varying vec3	attr_position;
varying vec3	attr_direction;


uniform float	osg_SimulationTime;
uniform int		_obj_counter;


const int Num_Lights = 50;


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
	Light lights[Num_Lights];
};




vec3 to_projection_space( vec3 v )
{
	vec4 vv = gl_ProjectionMatrix * vec4( v, 1.0 );
	vv.xyz /= vv.w;
	return vv.xyz;
}

float linmap_c(float v, float s0, float s1, float d0, float d1);


void main()
{
	float base_scale  = 0.140 * lights[_obj_counter].radius;
	// float base_energy = 0.070 * lights[_obj_counter].intensity;
	float base_energy = mix( 0.140 * lights[_obj_counter].intensity, 0.140, 0.75);
	// float base_energy = 0.330;

	if (gl_Vertex.z > 0.45)
	{
		base_scale *= 1.3;
	}
	base_energy *= 1.0 / ( clamp(gl_Vertex.z, 0.01, 1.0) + 0.5);

	
	uv_mesh		= gl_MultiTexCoord0.xy;
	// light_color	= pow( lights[_obj_counter].color, vec3( 1.0 / 2.0 ) );
	light_color	= lights[_obj_counter].color;
	// light_color	= pow( lights[_obj_counter].color, vec3(2.2) );
	
	float z 	= gl_Vertex.z;
	es_normal	= -lights[_obj_counter].direction;
	
	vec4 offset = vec4( 0, -0.0, 0, 0 );
	
	//vec4 offset = vec4( 0 );
	//offset = ( gl_ModelViewMatrix )[3];
	
	vec4 es_light_origin	= vec4(  lights[_obj_counter].position, 1.0 );
	vec4 es_light_vector	= vec4( -lights[_obj_counter].direction, 0.0 );
	
	//float scale = max( 0.0, dot( es_normal, -normalize( es_light_origin.xyz ) ) );
	// float scale = max( 0.0, dot( es_normal, -normalize( es_light_origin.xyz ) ) );
	
	
	vec4 ps_origin = gl_ProjectionMatrix * es_light_origin;
	vec4 ps_vector = gl_ProjectionMatrix * ( es_light_origin + es_light_vector );
	
	ps_origin.xyz /= ps_origin.w;
	ps_vector.xyz /= ps_vector.w;
	
	float aspect = ( 1920.0 / 1200.0 );
	
	
	vec4 es_puff_position = es_light_origin + es_light_vector * (z * base_scale * 2.2 + 0.066 );

	
	vec4 ps_puff_position = gl_ProjectionMatrix * es_puff_position;
	ps_puff_position.xyz /= ps_puff_position.w;
	dist = es_puff_position.z;
	
	vec2  ps_ldir = normalize( ( ps_vector.xy - ps_puff_position.xy ) * vec2( aspect, 1.0 ) ).xy;
	
	float perp = dot(	normalize(  (es_light_vector.xyz ) ),
						normalize(  -(es_light_origin.xyz ) )
					);
	
	float halo_aspect = mix( 1.00, 0.25, 1.0 - pow( abs( perp ), 16.0 )  );
	
	
	
	mat2 R = mat2( 	( vec2(  ps_ldir.x, ps_ldir.y )) , 
					( vec2( -ps_ldir.y, ps_ldir.x )) 
	);
	
	

	
	float scale = (z + 0.01) * base_scale * linmap_c( halo_aspect, 0.25, 1.0, 0.40, 1.0 );
	// scale *= mix( 1.0, 2.0, spotAngle );
	
	vec2 rotated_vertex = ( gl_Vertex.xy - offset.xy ) * vec2( scale / halo_aspect, scale );
	vec4 v = vec4( R * rotated_vertex, 0.0, 1.0 );
	
	
	vec4 p = v + es_puff_position;

	energy = base_energy * ( 0.008 / max( 0.015, z*z ) );		// inverse square intensity
	energy *= linmap_c( halo_aspect, 0.25, 1.0, 0.4, 1.00);	// sideways fade
	energy *= linmap_c( p.z, -0.0, -1.0, 0.0, 1.0 );			// near fade
	energy *= linmap_c( perp, -1.0, 0.0, 0.25, 1.0 );			// away fade
	
	
	
	vec4 ps_light = gl_ProjectionMatrix * p;
	ps_light.xyz /= ps_light.w;	
	
	
	// puff depth
	vec4 ps_puff = gl_ProjectionMatrix * es_puff_position;
	ps_puff.xyz /= ps_puff.w;
	float z_depth = ps_puff.z;
	
	// bloom depth ( little offset from emitting lamp )
	vec4 ps_ambi = gl_ProjectionMatrix * ( es_light_origin + es_light_vector * 2.5 );	// brings streak closer to eye, reduces depth test artefacts
	ps_ambi.xyz /= ps_ambi.w;
	float z_ambi = ps_ambi.z;
	
	ps_light.z	= z_depth;
	
	
	
	
	//float z_depth = linmap_c( gl_LightSource[0].diffuse.a, 0.0, 1.0, 0.0, 2.0 );
	float dist_dim = linmap_c( -dist, 3.0, 64.0, 1.0, 0.0 );
	//========
	// Streak
	//========
	#if 1
	if ( gl_Vertex.z < -0.0499 )
	{
		float width = linmap_c( perp, 0.95, 1.0, 1.0, 3.0 );
		vec4 v = ( gl_Vertex * vec4( width, 0.02125, 0.0, 1.0 ) );
		
		ps_light	  = gl_ProjectionMatrix * ( v + es_light_origin );
		ps_light.xyz /= ps_light.w;	
		ps_light.z	= z_ambi;
		//energy = base_energy * 0.1 * linmap_c( perp, 0.95, 0.951, 0.0, 1.0 ) * linmap_c( z_ambi, 0.00, 0.999, 1.0, 0.0 );
		energy = base_energy * 0.1 * linmap_c( perp, 0.95, 0.951, 0.0, 1.0 ) * dist_dim;
	}
	#endif
	
	//=======
	// Bloom
	//=======
	#if 1
	if ( gl_Vertex.z < -0.3000 )
	{	
		float bloom_scale = 0.0405;
		//float bloom_aspect = linmap_c( perp, 0.0, 1.0, 0.0, 0.50 );
		vec2 rotated_vertex = ( gl_Vertex.xy - offset.xy ) * vec2( bloom_scale / 1.0, bloom_scale );
		//vec2 rotated_vertex = ( gl_Vertex.xy - offset.xy ) * bloom_scale;
		vec4 v = vec4( R * rotated_vertex, 0.0, 1.0 );
		//vec4 v = ( gl_Vertex * vec4( 0.1, 0.1, 0.0, 1.0 ) );
		
		ps_light	  = gl_ProjectionMatrix * ( v + es_light_origin + es_light_vector * 0.02 );
		ps_light.xyz /= ps_light.w;	
		ps_light.z	= z_ambi;
		energy = base_energy * 2.05 * linmap_c( perp, 0.5, 1.0, 0.2, 1.0 ) * dist_dim;
	}
	#endif
	
	
	if ( ps_light.w < 0.0 )
	{
		energy = 0.0;
	}

	//energy *= ( 0.01 / pow( gl_LightSource[0].ambient.b + 0.04, 1.2 ) );

	// if ( perp > 0.6 )
	// {
		// ps_light.z -= 0.05;
	// }

	gl_Position = vec4( ps_light.xyz, 1.00 );
	

	if( lights[_obj_counter].active == 0.0 ) {
		gl_Position *= 0.0;
	}


}
