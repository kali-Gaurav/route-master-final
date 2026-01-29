import py_compile,glob,sys
files=glob.glob('*.py')
errors=0
for f in files:
    try:
        py_compile.compile(f,doraise=True)
        print('OK',f)
    except Exception as e:
        print('ERR',f,repr(e))
        errors+=1
if errors:
    sys.exit(1)
else:
    print('All files compiled successfully')
