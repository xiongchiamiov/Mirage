#include "Python.h"
/**
 * copy length chars from source to dest
 */
void copy(char *dest, const char *source, const int length)
{
	int i;
	for(i=0; i< length; i++, dest++, source++)
		*dest = *source;
}

/* Wrapper methods */
PyObject *rotate_right(PyObject *self, PyObject *args)
{
	char *a1;
	char *a2;
	int length;
	int w1, w2;
	int h1, h2;
	int rws1, rws2;
	int psz;
	int i1, i2;
	int x1, y1;
	PyObject *ret;
	
	/* Get Python Arguments */
	if(!PyArg_ParseTuple(args, "z#iiii", &a1, &length, &w1, &h1, &rws1, &psz)) 
	{
		return NULL;
	}
	
	/* Do the mirroring */
	w2 = h1;
	h2 = w1;
	
	if(w2 % 4 != 0)
		rws2 = ((w2/4 + 1) * 4) * psz;
	else
		rws2 = w2 * psz;

	length = rws2 * h2;
	a2 = malloc(length);
	
	for(x1=0; x1<w1; x1++)
	{
		for(y1=0; y1<h1; y1++)
		{
			i1 = y1 * rws1 + x1 * psz;
			i2 = (h1 - 1 - y1) * psz + rws2 * x1;
			copy(a2 + i2, a1 + i1, psz);
		}
	}
	
	ret = Py_BuildValue("z#iii", a2, length, w2, h2, rws2);
	free(a2);
	
	return ret;
}

PyObject *rotate_left(PyObject *self, PyObject *args)
{
	char *a1;
	char *a2;
	int length;
	int w1, w2;
	int h1, h2;
	int rws1, rws2;
	int psz;
	int i1, i2;
	int x1, y1;
	PyObject *ret;
	
	/* Get Python Arguments */
	if(!PyArg_ParseTuple(args, "z#iiii", &a1, &length, &w1, &h1, &rws1, &psz)) 
	{
		return NULL;
	}
	
	/* Do the mirroring */
	w2 = h1;
	h2 = w1;

	if(w2 % 4 != 0)
		rws2 = ((w2/4 + 1) * 4) * psz;
	else
		rws2 = w2 * psz;

	length = rws2 * h2;
	a2 = malloc(length);
	
	for(x1=0; x1<w1; x1++)
	{
		for(y1=0; y1<h1; y1++)
		{
			i1 = y1 * rws1 + x1 * psz;
			i2 = y1 * psz + rws2 * (w1 - 1 - x1);
			copy(a2 + i2, a1 + i1, psz);
		}
	}
	
	ret = Py_BuildValue("z#iii", a2, length, w2, h2, rws2);
	free(a2);
	
	return ret;
}

PyObject *rotate_mirror(PyObject *self, PyObject *args)
{
	char *a1;
	char *a2;
	int length;
	int w1, w2;
	int h1, h2;
	int rws1, rws2;
	int psz;
	int i1, i2;
	int x1, y1;
	PyObject *ret;
	
	/* Get Python Arguments */
	if(!PyArg_ParseTuple(args, "z#iiii", &a1, &length, &w1, &h1, &rws1, &psz)) 
	{
		return NULL;
	}
	
	/* Do the mirroring */
	w2 = w1;
	h2 = h1;
	rws2 = rws1;

	length = rws2 * h2;
	a2 = malloc(length);
	
	for(x1=0; x1<w1; x1++)
	{
		for(y1=0; y1<h1; y1++)
		{
			i1 = y1 * rws1 + x1 * psz;
			i2 = (w1 - 1 - x1) * psz + rws2 * (h1 - 1 - y1);
			copy(a2 + i2, a1 + i1, psz);
		}
	}
	
	ret = Py_BuildValue("z#iii", a2, length, w2, h2, rws2);
	free(a2);
	
	return ret;
}

PyObject *flip_vert(PyObject *self, PyObject *args)
{
	char *a1;
	char *a2;
	int length;
	int w1, w2;
	int h1, h2;
	int rws1, rws2;
	int psz;
	int i1, i2;
	int x1, y1;
	PyObject *ret;
	
	/* Get Python Arguments */
	if(!PyArg_ParseTuple(args, "z#iiii", &a1, &length, &w1, &h1, &rws1, &psz)) 
	{
		return NULL;
	}
	
	/* Do the mirroring */
	w2 = w1;
	h2 = h1;
	rws2 = rws1;

	length = rws2 * h2;
	a2 = malloc(length);
	
	for(x1=0; x1<w1; x1++)
	{
		for(y1=0; y1<h1; y1++)
		{
			i1 = y1 * rws1 + x1 * psz;
			i2 = x1 * psz + rws2 * (h1 - 1 - y1);
			copy(a2 + i2, a1 + i1, psz);
		}
	}
	
	ret = Py_BuildValue("z#iii", a2, length, w2, h2, rws2);
	free(a2);
	
	return ret;
}

PyObject *flip_horiz(PyObject *self, PyObject *args)
{
	char *a1;
	char *a2;
	int length;
	int w1, w2;
	int h1, h2;
	int rws1, rws2;
	int psz;
	int i1, i2;
	int x1, y1;
	PyObject *ret;
	
	/* Get Python Arguments */
	if(!PyArg_ParseTuple(args, "z#iiii", &a1, &length, &w1, &h1, &rws1, &psz)) 
	{
		return NULL;
	}
	
	/* Do the mirroring */
	w2 = w1;
	h2 = h1;
	rws2 = rws1;

	length = rws2 * h2;
	a2 = malloc(length);
	
	for(x1=0; x1<w1; x1++)
	{
		for(y1=0; y1<h1; y1++)
		{
			i1 = y1 * rws1 + x1 * psz;
			i2 = (w1 - 1 - x1) * psz + rws2 * y1;
			copy(a2 + i2, a1 + i1, psz);
		}
	}
	
	ret = Py_BuildValue("z#iii", a2, length, w2, h2, rws2);
	free(a2);
	
	return ret;
}

/* Method table mapping names to wrappers */
static PyMethodDef imgfuncs_methods[] = {
	{"left", rotate_left, METH_VARARGS},
	{"right", rotate_right, METH_VARARGS},
	{"mirror", rotate_mirror, METH_VARARGS},
	{"vert", flip_vert, METH_VARARGS},
	{"horiz", flip_horiz, METH_VARARGS},
	{NULL, NULL, 0}
};

/* Module initialization function */
void initimgfuncs(void)
{
	Py_InitModule("imgfuncs", imgfuncs_methods);
}
