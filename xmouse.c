#include <Python.h>
#include <X11/Xlib.h>

/* Return tuple with (x,y,width,height) of window under mouse cursor */
PyObject* xmouse_geometry(PyObject* self, PyObject* args)
{
    Display* dpy;
    int screennum = 0; 
    char* display = NULL;
    Window rootwin, childwin;
    int root_x, root_y;
    int child_x, child_y;
    int win_x, win_y;
    unsigned int win_width, win_height, win_border, win_depth;
    unsigned int mask;
    PyObject* ret = NULL;

    PyArg_ParseTuple(args, "|zi", &display, &screennum);

    dpy = XOpenDisplay(display);
    //printf("display: %s\n", display);
    //printf("dpy: %s\n", XDisplayString(dpy));
    if(!dpy)
    {  
        /* TODO is this right?? */
        PyErr_SetString(PyExc_Exception, "cannot open display");
        return NULL;
    }  

    XQueryPointer(dpy, RootWindow(dpy,0), &rootwin, &childwin, &root_x, &root_y, &child_x, &child_y, &mask);
    XGetGeometry(dpy, childwin, &rootwin, &win_x, &win_y, &win_width, &win_height, &win_border, &win_depth);
    ret = Py_BuildValue("(i,i,i,i)", win_x, win_y, win_width, win_height);

    XCloseDisplay(dpy);
    return ret;
}

PyMethodDef methods[] =
{
    {"geometry", xmouse_geometry, METH_VARARGS},
};

void initxmouse(void)
{
    Py_InitModule("xmouse", methods);
}
