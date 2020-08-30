#version 130
#line 2 "common/combine.frag"
#extension GL_ARB_gpu_shader5 : enable
#extension GL_ARB_uniform_buffer_object : enable


uniform mat4 osg_ViewMatrixInverse;
uniform mat4 u_meveaToWorld;
uniform mat3 rotationMatrix;
uniform bool fogOn;
uniform bool shadowOn;

uniform float translucency;
uniform vec3 gravity;

// varying vec4 es_pos;
varying vec3 es_normal;


uniform sampler2DShadow shadowTexture;
uniform samplerCube	s_environment;
uniform sampler2D	s_lightData;


void saturate( inout vec3 color, float factor )
{
	float grey = ( color.r + color.g + color.b ) * 0.333333;	
	vec3 dist = vec3( grey ) - color;
	color = color - ( dist * factor );	
}

float linmap( float v, float s0, float s1, float d0, float d1 ) 
{
	return v * (d0-d1) / (s0-s1) + (d1*s0 - d0*s1) / (s0-s1);
}

float linmap_c(float v, float s0, float s1, float d0, float d1) 
{
	float result = v * (d0 - d1) / (s0 - s1) + (d1 * s0 - d0 * s1) / (s0 - s1);

	float min_limit = min(d0, d1);
	float max_limit = max(d0, d1);

	return clamp( result, min_limit, max_limit );
}




//===============================================
// Cook-Torrance
//===============================================


// geometry term
//float G( vec3 N, vec3 H, vec3 L, vec3 V, float alpha )
//{
//	// Cook-Torrance
//	//float a = ( 2.0 * dot( N, H ) * dot( N, V ) ) / dot( V, H );
//	//float b = ( 2.0 * dot( N, H ) * dot( N, L ) ) / dot( V, H );
//	//return min( 1.0, min( a, b ) );
//
//	// Heitz 2014
//	float x = dot( N, V );
//	float t = ( 1 - x * x ) / ( x * x );
//
//	return dot( N, V ) * ( 2.0 / ( 1 + sqrt( 1 + alpha * alpha * t ) ) );
//}

float G( vec3 N, vec3 H, vec3 L, vec3 V, float alpha )
{
    float VoH2 = clamp( dot( L, N ), 0.0, 1.0 );
    float chi  = VoH2 / clamp( dot( V, N ), 0.0001, 1.0 );
    if ( chi > 0 )
    	chi = 1.0;
    else
    	chi = 0.0;

    // float VoH2 = clamp( dot( N, L ), 0.0, 1.0 );
    VoH2 = VoH2 * VoH2;

    float tan2 = ( 1.0 - VoH2 ) / VoH2;
    tan2 = max( 0.0, tan2 );
    return ( chi * 2.0 ) / ( 1.0 + sqrt( 1.0 + alpha * alpha * tan2 ) );

}

// fresnel term
vec3 F( vec3 L, vec3 H, vec3 F0 )	
{
	// Schlick
	// return F0 + ( vec3( 1.0 ) - F0 ) * pow( 1.0 - ( dot( L, H ) ), 5.0 );
	return F0 + ( vec3( 1.0 ) - F0 ) * pow( dot( L, H ), 5.0 );
}

// normal distribution term
float D( vec3 N, vec3 H, float alpha )
{
	// constants
	const float pi = 3.141592653589793;

	// GGX
	float N_dot_M = dot( N, H );
	float a       = ( N_dot_M * N_dot_M ) * ( alpha * alpha - 1.0 ) + 1.0;
	float density = ( alpha * alpha ) / ( pi * a * a );
	return density;
}

vec3 half( vec3 a, vec3 b )
{
	return normalize( a + b );
}

vec3 BRDF_cook_torrance( vec3 N, vec3 L, vec3 V, vec3 F0, float alpha )
{
	vec3 H = normalize(L-V);

	float d = D( N, H, alpha );
	float g = G( N, H, L, V, alpha );
	vec3  f = F( V, half( N, V ), F0 );

	return vec3( d * f * g );
} 

vec3 BRDF_lambert( vec3 L, vec3 N )
{
	return vec3( max( 0.0, dot( L, N ) ) );
}


//===============================================
// Cook-Torrance ends
//===============================================

const int dynamic_shadow_uv_index = 0;

float rough_mix( float control, float sharp, float bias )
{	
	// TODO: should sharp be -sharp?
	return clamp( ( ( control - bias ) * sharp ) + bias, 0.0, 1.0 );
}

float mev_DynamicShadow(vec2 u, vec4 tex)
{
	if( shadowOn == false )
		return 1.0;
	
	return shadow2DProj( shadowTexture, tex + u.xyxy ).r;
}

float mev_DitheredDynamicShadow(float scale)
{
	if( shadowOn == false )
		return 1.0;
	
	// dithered shadowmap
	float dither = scale;
	float shadow = 0.0;
	vec4 tex = normalize( gl_TexCoord[ dynamic_shadow_uv_index ] );
	float shadow1 = mev_DynamicShadow( vec2( -dither, -dither ), tex);
	float shadow2 = mev_DynamicShadow( vec2(  dither, -dither ), tex);
	float shadow3 = mev_DynamicShadow( vec2( -dither,  dither ), tex);
	float shadow4 = mev_DynamicShadow( vec2(  dither,  dither ), tex);

	return ( shadow1 + shadow2 + shadow3 + shadow4 ) / 4.0;
}

vec3 getSunIntensity()
{
	// return pow( vec3( 1.000, 0.953, 0.915 ), vec3( 8.0 ) ) * 100.0;
	return pow( vec3( 1.000 ), vec3( 8.0 ) ) * 140.0;
}

vec3 sampleSunHalo( vec3 ws_direction, vec3 ws_sunDirection )
{
	float sunDiscRadius = 0.008726646259971648;
	float sunDisc	    = sunDiscRadius  / ( dot( normalize( ws_direction ), ws_sunDirection) + 1.00001 );
	float sunHalo	    = dot( normalize( ws_direction ), -ws_sunDirection );
	sunDisc             = clamp(sunDisc, 0, 2);
	sunHalo             = clamp(sunHalo, 0, 5);
	sunHalo             = linmap_c( sunHalo, 0.50, 1, 0, .15);
	sunHalo            *= sunHalo * 2.0;
	vec3 sunColor       = (sunDisc + sunHalo) * getSunIntensity();
	sunColor           *= gl_LightSource[0].diffuse.rgb;

	return sunColor * 1.0;
}

vec3 sampleSkyColor( vec3 ws_direction, vec3 ws_sunDirection, float sunFactor )
{
	return vec3( 1.0, 1.0, 1.0 );
}

vec3 mev_ambient_light()
{
	return getSunIntensity().r * gl_LightSource[0].ambient.rgb * vec3( 0.5, 0.8, 1.0 ) * 0.5;
}



void fog( in vec3 es_pos, inout vec3 color )
{
	float L = length( es_pos );
	float e = 2.718281828459045;
	float transmittance = pow( e, ( -0.03 * gl_Fog.density ) * L );
	vec3 fog_color = mev_ambient_light();
	color = mix( fog_color, color, transmittance );
}


float getOutputGamma()
{
	return 2.2;
}


void toneMap( inout vec3 color )
{
	// render dimmer reflection, non-tonemapped reflection
	// if ( gl_ClipPlane[0].w < 0.0 )
	// {	
	// 	color *= 1.0 / 32.0;
	// }
	// else
	{
		// saturate( color, 0.50 );
		color = pow( color, vec3(	1.0 / getOutputGamma(),
									1.0 / getOutputGamma(),
									1.0 / getOutputGamma()
									));
		color *= 0.3;	// for tonemap
		// saturate( color, 0.50 );
	}
}





void mev_sun_light(	int i,
				inout vec3 diff_light, 
				inout vec3 spec_light,
				inout vec3 ambi_light,
				vec3 es_N,
				vec3 es_pos )
{
	vec3 sunLight = gl_LightSource[ i ].diffuse.rgb * getSunIntensity();
	vec3 L        = gl_LightSource[ i ].spotDirection;

	if ( gl_LightSource[ i ].position.w == 0.0 )
	{
		L = normalize( gl_LightSource[ i ].position.xyz );
	}
	
	diff_light += BRDF_lambert( L, es_N ) * sunLight;

	//========================
	// Cook-Torrance specular
	//========================
	
	vec3 N  = es_N;
	vec3 V  = normalize( es_pos );
	vec3 F0 = vec3( 0.04 );	// educated guess of F0 for non metals

	//NOTE: transform blender shininess value to alpha roughness
	float alpha = 1.0 - gl_FrontMaterial.shininess;
	alpha *= alpha;
	alpha = max( 0.002, alpha );

	spec_light += BRDF_cook_torrance( N, L, V, F0, alpha ) * sunLight;
}

void mev_sun_light2(	int i,
						inout vec3 diff_light, 
						inout vec3 spec_light,
						vec3 es_N,
						vec3 es_pos,
						float alpha )
{
	vec3 sunLight = gl_LightSource[ i ].diffuse.rgb * getSunIntensity();
	vec3 L        = gl_LightSource[ i ].spotDirection;

	if ( gl_LightSource[ i ].position.w == 0.0 )
	{
		L = normalize( gl_LightSource[ i ].position.xyz );
	}
	
	diff_light += BRDF_lambert( L, es_N ) * sunLight;

	//========================
	// Cook-Torrance specular
	//========================
	
	vec3 N  = es_N;
	vec3 V  = normalize( es_pos );
	vec3 F0 = vec3( 0.04 );	// educated guess of F0 for non metals

	spec_light += BRDF_cook_torrance( N, L, V, F0, alpha ) * sunLight;
}


//=====================
// compute spot lights
//=====================

uniform int u_numLights;
vec3 computeSpotLights( vec4 es_pos, vec3 es_N, inout vec3 spec_light )
{
	vec3 ret = vec3( 0.0, 0.0, 0.0 );

	float nightFactor = ( 1.0 - min( 1.0, gl_LightSource[0].ambient.r * 5.0 ) );
	if ( nightFactor == 0.0 )
	{
		return vec3( 0.0 );
	}

	for ( int i=0; i < u_numLights; ++i )
	{
		//===================
		// unpack light data
		//===================

		const int POSITION_CUTOFF									= 0;
		const int COLOR											    = 1;
		const int DIRECTION_RADIUS								    = 2;
		const int ATTENUATION_SPOTFACTOR_SPOTSHAPE_AMBIENTFACTOR	= 3;

		vec4 _data0 = texelFetch( s_lightData, ivec2( i, POSITION_CUTOFF                                 ), 0 );
		vec4 _data1 = texelFetch( s_lightData, ivec2( i, COLOR                                           ), 0 );
		vec4 _data2 = texelFetch( s_lightData, ivec2( i, DIRECTION_RADIUS                                ), 0 );
		vec4 _data3 = texelFetch( s_lightData, ivec2( i, ATTENUATION_SPOTFACTOR_SPOTSHAPE_AMBIENTFACTOR  ), 0 );

		// unpack
		vec3  position      = _data0.xyz;
		vec3  direction     = _data2.xyz;
		vec3  color         = _data1.xyz;
		float cutoff        = _data0.w;
		float radius        = 50.0;//_data2.w;
		float attenuation   = _data3.x;
		float spotfactor    = _data3.y;
		float spotshape     = _data3.z;
		float ambientfactor = _data3.w;

		// compute diffuse light
		vec3 ws_pos = vec3( osg_ViewMatrixInverse * vec4( es_pos.xyz, 1.0 ) );
		vec3 ws_N   = vec3( osg_ViewMatrixInverse * vec4( es_N,       0.0 ) );

		vec3  s                 = ws_pos - position;
		vec3  L                 = normalize( s );
		float l_2               = s.x * s.x + s.y * s.y + s.z * s.z;
		// if ( l_2 > radius * radius )
			// continue;
		float inverse_quadratic	= ( radius / sqrt( l_2 ) );
		float linear            = max( 0.0, radius - length(s) ) / radius;
		float lambertian        = max( 0.0, dot( ws_N, -L ) );
		
		
		cutoff = 0.80;
		float C1         = mix( cutoff + 0.01, 1.0, 0.8 );
		float spot_blend = dot( -L, direction );
		// spot_blend       = linmap_c( spot_blend, cutoff, C1, 0.0, 1.0 );
		spot_blend       = linmap_c( spot_blend, cutoff, C1, 0.0, 1.0 );
		spot_blend      *= spot_blend;
		
		float fac = mix( 1.0, spot_blend, 0.995 ) * 
					linear *
					mix( 1.0, inverse_quadratic, attenuation )
					;
		spot_blend = mix( spot_blend, 1.0, 0.05 );
		ret	+= linear * inverse_quadratic * spot_blend * lambertian * color;

		vec3 es_L   = mat3( transpose( osg_ViewMatrixInverse ) ) * L;
		vec3 es_V   = normalize( -es_pos.xyz );
		spec_light += BRDF_cook_torrance( es_N, -es_L, es_V, vec3( 0.05 ), gl_FrontMaterial.shininess ) * color * spot_blend * 0.1;

	}

	return ret;
}






vec3 terrain_combine(	vec3 es_N,
						vec4 es_pos,
						vec3 diff_color,
						float ao
						)
{
	float shadow = 1.0;
	shadow = mix( mev_DitheredDynamicShadow( 0.0004 ), 1.0, 0.10 );
	//=================
	// Source lighting
	//=================
	vec3 diff_light = vec3( 0.0 );
	vec3 spec_light = vec3( 0.0 );
	vec3 ambi_light = vec3( 0.0 );

	mev_sun_light( 0, diff_light, spec_light, ambi_light, es_N, es_pos.xyz );
	diff_light *= shadow;

	ambi_light += mev_ambient_light() * 4.0;

	diff_light += computeSpotLights( es_pos, es_N, spec_light );

	vec3 ret	= vec3( 0.0 )
				+ diff_color * diff_light * pow( min( 1.0, ao + 0.5 ), 2.0 )
				+ diff_color * ambi_light * ao
				;

	// ret = diff_color;
	fog( es_pos.xyz, ret );
	toneMap( ret );

	return ret;
}


vec3 world_combine(	vec3 es_N,
					vec4 es_pos,
					vec3 diff_color,
					float shadow,
					float ao
					)
{
	shadow *= mix( mev_DitheredDynamicShadow( 0.0004 ), 1.0, 0.00001 );

	mat3 I = mat3( osg_ViewMatrixInverse );
	vec3 ws_static_sunDirection = normalize( vec3( 0.708, 0.2167, 0.671 ) );
	vec3 diff_light             = vec3( max( 0.0, dot( I * es_N, ws_static_sunDirection ) ) );
	// diff_light *= diff_light;

	vec3 ret = vec3( 0.0 );
	diff_color *= 1.4;

	// saturate( diff_color, 0.5 );

	ret = vec3( 0.0 )
		+ diff_color  * diff_light * shadow * getSunIntensity() * diff_color
	    // + vec3( 1.0 ) * spec_light * shadow
	    + diff_color  * mev_ambient_light() * ao
	    ;

	fog( es_pos.xyz, ret );
	toneMap( ret );
	return ret;
}


vec3 combine(	vec3 es_N,
				vec4 es_pos,

				vec3 diff_color,
				vec3 spec_color,
				vec3 ambi_color,
				vec3 emit_color,

				float ao,
				float reflect_factor
				)
{
	float shadow = 1.0;
	shadow = mix( mev_DitheredDynamicShadow( 0.0004 ), 1.0, 0.00001 );
	// shadow = mix( shadow, 1.0, ao );
	//=================
	// Source lighting
	//=================
	vec3 diff_light = vec3( 0.0 );
	vec3 spec_light = vec3( 0.0 );
	vec3 ambi_light = vec3( 0.0 );

	float alpha = pow( 1.0 - gl_FrontMaterial.shininess, 2.0 );
	// alpha = linmap_c( spec_color.r * spec_color.r, 0.00, 0.015, 0.6, 0.4 );
	alpha = pow( alpha, 16.0 );

	mev_sun_light2( 0, diff_light, spec_light, es_N, es_pos.xyz, alpha );
	diff_light *= shadow;
	spec_light *= shadow;

	//==========================
	// compute all other lights
	//==========================
	diff_light += computeSpotLights( es_pos, es_N, spec_light ) * ao;

	//====================
	// Fresnel reflection
	//====================
	vec3 E  = normalize( es_pos.xyz );
	vec3 F0 = vec3( 0.04 );

	vec3 fresnel = F( E, half( E, es_N ), F0 );
	
	vec3 ret	= vec3( 0.0 )
				+ diff_color * diff_light * ao
				+ spec_color * spec_light * ao
				+ diff_color * mev_ambient_light() * ao
				+ emit_color
				;

	vec3 total_reflection = mev_ambient_light();
	ret += total_reflection * fresnel * ao * spec_color;

	// ret = vec3( diff_color );
	fog( es_pos.xyz, ret );
	toneMap( ret );
	return ret;
}

