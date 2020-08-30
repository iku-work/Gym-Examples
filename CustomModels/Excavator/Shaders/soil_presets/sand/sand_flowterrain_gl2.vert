#version 130
#extension GL_EXT_gpu_shader4 : enable
#extension GL_ARB_gpu_shader5 : enable
#line 3 "flowterrain_gl2.vert"

uniform sampler2D s_elevation;
uniform sampler2D s_diffuse;
uniform sampler2D s_normal;
uniform sampler2D s_specular;

uniform ivec2 flowTerrainSize;

varying vec4 VS_es_pos;
varying vec3 VS_es_normal;
varying vec3 VS_es_tangent;
varying vec3 VS_es_bitangent;
varying vec2 VS_uv_mesh;
varying vec4 VS_uv_shadow;
varying vec4 VS_color;

const int dynamic_shadow_uv_index = 0;

void mev_DynamicShadow( in vec4 ecPosition )
{                                        
    // generate coords for shadow mapping
    gl_TexCoord[ dynamic_shadow_uv_index ].s = dot( ecPosition, gl_EyePlaneS[ dynamic_shadow_uv_index ] );
    gl_TexCoord[ dynamic_shadow_uv_index ].t = dot( ecPosition, gl_EyePlaneT[ dynamic_shadow_uv_index ] );
    gl_TexCoord[ dynamic_shadow_uv_index ].p = dot( ecPosition, gl_EyePlaneR[ dynamic_shadow_uv_index ] );
    gl_TexCoord[ dynamic_shadow_uv_index ].q = dot( ecPosition, gl_EyePlaneQ[ dynamic_shadow_uv_index ] );
}

void main()
{
	float half_x = 0.5 / float( flowTerrainSize.x );
	float half_y = 0.5 / float( flowTerrainSize.y );
	vec2 uv = vec2(	gl_Vertex.x / float( flowTerrainSize.x ) + half_x,
					gl_Vertex.y / float( flowTerrainSize.y ) + half_y );

	vec4 pos = gl_Vertex;
	const float ELEVATION_LOD = 0;
	float local_elevation = texture2D( s_elevation, uv, ELEVATION_LOD ).x;
	pos.z = local_elevation;

	gl_Position	 = gl_ProjectionMatrix * gl_ModelViewMatrix * pos;
	VS_uv_mesh	 = uv;
	VS_es_pos    = gl_ModelViewMatrix * pos;
	VS_es_normal = normalize( gl_NormalMatrix * gl_Normal );
	VS_color     = vec4( 0.5, 0.5, 0.5, 1.0 );
	
	mev_DynamicShadow( VS_es_pos );
}