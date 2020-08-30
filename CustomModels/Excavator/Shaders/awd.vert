#line 1 "awd.vert"

varying vec4 ws_pos;

#include common/default.vert
void defaultVert();
void defaultVertMat();

void main()
{
	ws_pos = gl_Vertex;
	defaultVertMat();
}
