#version 130
#extension GL_EXT_draw_instanced : enable
#extension GL_EXT_gpu_shader4 : enable
#line 5 "instanced_awd.vert"

uniform int	  major_axis;
uniform float material_scale;
uniform bool  shadowOn;

// attributes
attribute vec3 rm_Binormal;
attribute vec3 rm_Tangent;

// varyings
out vec4 color;
out vec4 es_pos;
out vec2 uv_mesh;
out vec2 uv_mat;
out vec3 es_normal;
out vec4 ws_pos;

out vec3 es_T;
out vec3 es_B;
out vec3 es_mat_T;
out vec3 es_mat_B;

uniform samplerBuffer s_instancedModelMatrixData;



const int dynamic_shadow_uv_index = 0;

void mev_DynamicShadow( in vec4 ecPosition )
{                                        
    // generate coords for shadow mapping
    gl_TexCoord[dynamic_shadow_uv_index].s = dot( ecPosition, gl_EyePlaneS[dynamic_shadow_uv_index] );
    gl_TexCoord[dynamic_shadow_uv_index].t = dot( ecPosition, gl_EyePlaneT[dynamic_shadow_uv_index] );
    gl_TexCoord[dynamic_shadow_uv_index].p = dot( ecPosition, gl_EyePlaneR[dynamic_shadow_uv_index] );
    gl_TexCoord[dynamic_shadow_uv_index].q = dot( ecPosition, gl_EyePlaneQ[dynamic_shadow_uv_index] );
}

vec3 project_onto_plane(	vec3 p, 	// projection direction
							vec3 v,		// projected vector
							vec3 N		// Normal
						)
{
	float x = - ( N.z * v.z + N.y * v.y + N.x * v.x ) 
	          / ( N.z * p.z + N.y * p.y + N.x * p.x );
	
	return ( v + x * p );
	
}


mat4 getObjectModelMatrix( int instanceID )
{
	vec4 x = texelFetch( s_instancedModelMatrixData, instanceID * 4 + 0 );
	vec4 y = texelFetch( s_instancedModelMatrixData, instanceID * 4 + 1 );
	vec4 z = texelFetch( s_instancedModelMatrixData, instanceID * 4 + 2 );
	vec4 w = texelFetch( s_instancedModelMatrixData, instanceID * 4 + 3 );
	return mat4( x, y, z, w );
}



void main()
{
	gl_Position = gl_ProjectionMatrix * gl_ModelViewMatrix * getObjectModelMatrix( gl_InstanceID ) * gl_Vertex;
	// gl_Position = gl_ProjectionMatrix * gl_ModelViewMatrix * gl_Vertex;
	uv_mesh 	= gl_MultiTexCoord0.xy;
	color   	= gl_Color;
	color   	= vec4( gl_InstanceID );
	
	
	const vec3 x = vec3( 1.0, 0.0, 0.0 );
	const vec3 y = vec3( 0.0, 1.0, 0.0 );
	const vec3 z = vec3( 0.0, 0.0, 1.0 );
	
	
	if ( major_axis == 0 ) {	es_mat_T	= gl_NormalMatrix * project_onto_plane( x,  y, gl_Normal );
								es_mat_B	= gl_NormalMatrix * project_onto_plane( x,  z, gl_Normal );	}
	if ( major_axis == 1 ) {	es_mat_T	= gl_NormalMatrix * project_onto_plane( y,  z, gl_Normal );
								es_mat_B	= gl_NormalMatrix * project_onto_plane( y,  x, gl_Normal );	}
	if ( major_axis == 2 ) {	es_mat_T	= gl_NormalMatrix * project_onto_plane( z,  x, gl_Normal );
								es_mat_B	= gl_NormalMatrix * project_onto_plane( z,  y, gl_Normal );	}
	
	//uv_mat = gl_Vertex.yz + 0.5;
	if ( major_axis == 0 ) uv_mat = ( gl_Vertex.yz + 0.5 ) * material_scale * 1.0 + vec2( gl_InstanceID * 0.025 );
	if ( major_axis == 1 ) uv_mat = ( gl_Vertex.zx + 0.5 ) * material_scale * 1.0 + vec2( gl_InstanceID * 0.025 );
	if ( major_axis == 2 ) uv_mat = ( gl_Vertex.xy + 0.5 ) * material_scale * 1.0 + vec2( gl_InstanceID * 0.025 );
	
	
	
	es_normal	= gl_NormalMatrix * gl_Normal;
	es_pos		= gl_ModelViewMatrix * gl_Vertex;

	es_T		= gl_NormalMatrix * rm_Tangent;
	es_B		= gl_NormalMatrix * rm_Binormal;
	
	if(shadowOn)
		mev_DynamicShadow( es_pos );
	
}
