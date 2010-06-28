#include <Python.h>
#include <ctype.h>
/* $Id: numacomp.c,v 1.2 2002/02/22 01:45:37 gregs Exp $
 * numacomp.c -
 * python extension module 'numacomp' for
 * numerically aware string compares
 * Greg Smith Toronto Feb 2002
 * This code is released under the GNU General Public;
 * See the file COPYING.
 */
/* 2010/06/24 Fredric Johansson
 * Introduced a case insensitive version of the compare function
*/
/*-------------------------------------- */
static char numacomp_docs[] = 
"numacomp(s1,s2): compare two strings with case sensitive numerically aware comparison\n"
"    e.g. \"A1\" < \"A3\" < \"A3x\" < \"A10\" < \"A30x\" < \"B1\"\n"
;
static char numacompi_docs[] = 
"numacompi(s1,s2): compare two strings with case insensitive numerically aware comparison\n"
"    e.g. \"A1\" < \"A3\" < \"a3x\" < \"A10\" < \"a30x\" < \"B1\"\n"
;
/*
 * things to do:
 *    - support unicode
 */
#define ISDIGIT(x)  ((unsigned)((x)-'0')<(unsigned)10)

/*#define CASE(x) printf("--case{%c}--\n", x ) */
#define CASE(x)
/*
 * this is the 'core' compare routine
 * it returns <0, 0, >0
 */
static int
numacomp( unsigned char const *sa,		/* string a */
		  int lena,			/* len of string a */
		  unsigned char const *sb,	/* string b */
		  int lenb,			/* len of string b */
		  int case_sensitive)					
{
	int lenmin,i;
	int za,zb,na,nb;

	lenmin = (lena<lenb)? lena: lenb;
	i = 0;
	/*
	 * skip any common prefix
	 */
	if (case_sensitive){
		while( i < lenmin && sa[i] == sb[i]) {
			++i;
		}
	}
	else{
		while( i < lenmin && tolower(sa[i]) == tolower(sb[i])) {
			++i;
		}
	}
	/*
	 * some cases to get out of the way. If sa[i]
	 * and sb[i] are both non-digit (incl eos) we
	 * can declare a winner
	 */
	if( (i == lena || !ISDIGIT(sa[i]))
	   && (i == lenb || !ISDIGIT(sb[i])) ){
		if( i == lena ){
			CASE('A');		/* strings match if i==lenb or */
			return i-lenb;  /* a is prefix of b if i < lenb */
								
		}
		if ( i == lenb){
			CASE('B');
			return 1;				/* b is prefix of a */
		}
		CASE('C');
		if (case_sensitive)
			return sa[i]-sb[i];	/* compare the chars */
		else
			return tolower(sa[i])-tolower(sb[i]);	/* compare the chars */
	}
	/* at least one of sa[i], sb[i] is a digit.
	 * look back for more... */
	if(  i > 0 && ISDIGIT(sa[i-1]) ){
		do{
			--i;
		}while( i > 0 && ISDIGIT(sa[i-1]));
	}else if( i == lenmin ){	
		/* reached the end of one of the strings && didn't
		 * --i at all. So one is a prefix of the other and
		 * the prefix doesn't end in a digit. Eg:
		 * "KE8" vs "KE"  or  "" vs "12"
		 */
		CASE('D');
		return lena-lenb;
	}
	/* i < lenmin here.
	 * sa[i] and sb[i] could be both digits, or one each.
	 * Unless they are both digits, we can just do a lexical comp.
	 */
	if(!ISDIGIT(sa[i]) || !ISDIGIT(sb[i])){
		CASE('E');
		if(case_sensitive)
			return sa[i]-sb[i];
		else
			return tolower(sa[i])-tolower(sb[i]);
	}
	/* sa[i] and sb[i] are both digits, and are preceded by
	 * a common prefix which does not end in a digit.
	 * here's where we do an actual numeric compare...
	 */
	lena -= i;   /* discard common prefix... */
	lenb -= i;
	sa += i;
	sb += i;
	za = 0; na = 0;
	/* count any leading zeroes. */
	while( lena > 0 && *sa == '0'){
		++sa;
		++za;
		--lena;
	}
	/* count the digits */
	while( lena > 0 && ISDIGIT(*sa)){
		++sa;
		++na;
		--lena;
	}
	/* same for b */
	zb = 0; nb = 0;
	while( lenb > 0 && *sb == '0'){
		++sb;
		++zb;
		--lenb;
	}
	/* count the digits */
	while( lenb > 0 && ISDIGIT(*sb)){
		++sb;
		++nb;
		--lenb;
	}
	if( na != nb){		/* different # sig. digits */
		CASE('F');
		return na-nb;
	}
	i = 0;
	sa -= na;
	sb -= nb;		/* back up to 1st non-zero */
	while( i < na ){ /* note na cld be zero! "X00" vs "X000" */
		if(case_sensitive){
			if(sa[i] != sb[i]){
				CASE('G');	/* was a difference */
				return sa[i]-sb[i];
			}
		}else{
			if( tolower(sa[i]) != tolower(sb[i])){
				CASE('G');	/* was a difference */
				return tolower(sa[i])-tolower(sb[i]);
			}
		} /* else */
		++i;
	}
	CASE('H');
	return za-zb; 	/* most zeroes wins */
}

static PyObject*
C_numacomp(PyObject* self, PyObject* args)
{
	unsigned char *sa, *sb;
	int lena,lenb;
	int k;

	if (!PyArg_ParseTuple(args,"s#s#:numacomp",&sa, &lena,&sb,&lenb)) 
		return NULL;
	k = numacomp( sa, lena, sb, lenb, 1); /* case sensitive version */
	
	/*
	 * python compare may only return -1,0,1
	 */
	if (k < 0 ) 
		k = -1;
	else
		k = (k>0);

	return PyInt_FromLong(k);
}

static PyObject*
C_numacomp_i(PyObject* self, PyObject* args)
{
	unsigned char *sa, *sb;
	int lena,lenb;
	int k;

	if (!PyArg_ParseTuple(args,"s#s#:numacomp",&sa, &lena,&sb,&lenb)) 
		return NULL;
	k = numacomp( sa, lena, sb, lenb, 0 ); /* case insensitive version */
	
	/*
	 * python compare may only return -1,0,1
	 */
	if (k < 0 ) 
		k = -1;
	else
		k = (k>0);

	return PyInt_FromLong(k);
}

static PyMethodDef numacomp_methods[] = {
	{"numacomp", C_numacomp, METH_VARARGS, numacomp_docs },
	{"numacompi", C_numacomp_i, METH_VARARGS, numacompi_docs },
	{NULL, NULL, 0, NULL}
};

DL_EXPORT(void)
initmirage_numacomp(void) 
{
	Py_InitModule("mirage_numacomp", numacomp_methods);
}

