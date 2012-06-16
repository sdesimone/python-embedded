#!/usr/bin/python
import os, sys
os.chdir(os.path.dirname(__file__) or os.getcwd())
import better_exchook
better_exchook.install()

CC = "gcc"
CXX = "g++"
IOS_VERSION="5.0"

DEVROOT = "/Developer/Platforms/iPhoneOS.platform/Developer"
SDKROOT = DEVROOT + "/SDKs/iPhoneOS%s.sdk" % IOS_VERSION

assert os.path.exists(DEVROOT)
assert os.path.exists(SDKROOT)

CXXFLAGS = [
	"-I%s/usr/lib/gcc/arm-apple-darwin10/4.2.1/include/" % SDKROOT,
	"-I%s/usr/include/" % SDKROOT
	]
CFLAGS = CXXFLAGS + [
	"-pipe"
	"-no-cpp-precomp"
	"-isysroot", SDKROOT
	]
LDFLAGS = [
	"-isysroot", SDKROOT,
	"-Lextralibs/"
	]

PythonDir = "Python-2.7.3"

from glob import glob as pyglob
from pprint import pprint
try: os.mkdir("build")
except: pass

assert os.path.exists(PythonDir)

def glob(pattern):
	def glob_(baseDir, patternList):
		if not patternList:
			yield baseDir
			return
		head = patternList[0]
		if head == "**":
			for f in glob_(baseDir, patternList[1:]): yield f
			for d in pyglob(baseDir + "/*/"):
				for f in glob_(d, patternList): yield f
			return
		for m in pyglob(baseDir + "/" + head):
			for f in glob_(m, patternList[1:]): yield f
	parts = pattern.split("/")
	if not parts: return
	if parts[0] == "": # start in root
		for f in glob_("/", parts[1:]): yield os.path.normpath(f)
		return
	for f in glob_(".", parts): yield os.path.normpath(f)

baseFiles = \
	set(glob(PythonDir + "/Python/*.c")) - \
	set(glob(PythonDir + "/Python/dynload_*.c"))
baseFiles |= \
	set(glob(PythonDir + "/Python/dynload_stub.c")) | \
	set(glob("pyimportconfig.c")) | \
	set(glob("pygetpath.c"))

# via blacklist
modFiles = \
	set(glob(PythonDir + "/Modules/**/*.c")) - \
	set(glob(PythonDir + "/Modules/**/testsuite/**/*.c")) - \
	set(glob(PythonDir + "/Modules/_sqlite/**/*.c")) - \
	set(glob(PythonDir + "/Modules/_bsddb.c")) - \
	set(glob(PythonDir + "/Modules/expat/**/*.c")) - \
	set(glob(PythonDir + "/Modules/imgfile.c")) - \
	set(glob(PythonDir + "/Modules/_ctypes/**/*.c")) - \
	set(glob(PythonDir + "/Modules/glmodule.c"))
	# ...
	
# via whitelist
# Add the init reference also to pyimportconfig.c.
# For hacking builtin submodules, see pycryptoutils/cryptomodule.c.
modFiles = \
	set(map(lambda f: PythonDir + "/Modules/" + f,
		[
			"main.c",
			"python.c",
			"getbuildinfo.c",
			"posixmodule.c",
			"arraymodule.c",
			"gcmodule.c",
			"_csv.c",
			"_collectionsmodule.c",
			"itertoolsmodule.c",
			"operator.c",
			"_math.c",
			"mathmodule.c",
			"errnomodule.c",
			"_weakref.c",
			"_sre.c",
			"_codecsmodule.c",
			"cStringIO.c",
			"timemodule.c",
			"datetimemodule.c",
			"shamodule.c",
			"sha256module.c",
			"sha512module.c",
			"md5.c",
			"md5module.c",
			"_json.c",
			"_struct.c",
			"_functoolsmodule.c",
			"threadmodule.c",
			"binascii.c",
			"_randommodule.c",
			])) | \
	set(glob(PythonDir + "/Modules/_io/*.c"))

# remove main.c/python.c if we dont want an executable
#- \
	#[PythonDir + "/Modules/main.c"]
#pprint(modFiles)

objFiels = \
	set(glob(PythonDir + "/Objects/*.c"))

parserFiles = \
	set(glob(PythonDir + "/Parser/*.c")) - \
	set(glob(PythonDir + "/Parser/*pgen*.c"))

pycryptoFiles = \
	set(glob("pycrypto/src/*.c")) - \
	set(glob("pycrypto/src/*template.c")) - \
	set(glob("pycrypto/src/cast*.c")) - \
	set(glob("pycrypto/src/_fastmath.c")) # for now. it needs libgmp

pycryptoFiles = map(lambda f: "pycrypto/src/" + f,
	[
		"_counter.c",
		"AES.c",
		"strxor.c",
	]) + \
	["pycryptoutils/cryptomodule.c"]

compileOpts = [
	"-Ipylib",
	"-I" + PythonDir + "/Include",
	"-DWITH_PYCRYPTO",
]

compilePycryptoOpts = compileOpts + [
	"-Ipycryptoconfig",
	"-Ipycrypto/src/libtom",
	"-std=c99",
]

def compilePyFile(f, compileOpts):
	ofile = os.path.splitext(os.path.basename(f))[0] + ".o"
	try:
		if os.stat(f).st_mtime < os.stat("build/" + ofile).st_mtime:
			return ofile
	except: pass
	cmd = "gcc " + " ".join(compileOpts) + " -c " + f + " -o build/" + ofile
	print cmd
	if os.system(cmd) != 0:
		sys.exit(1)
	return ofile

def compilePycryptoFile(fn):
	return compilePyFile(fn, compilePycryptoOpts)
	
def compile():
	ofiles = []
	for f in list(baseFiles) + list(modFiles) + list(objFiels) + list(parserFiles):
		ofiles += [compilePyFile(f, compileOpts)]
	for f in list(pycryptoFiles):
		ofiles += [compilePycryptoFile(f)]
		
	os.system("gcc " + " ".join(map(lambda f: "build/" + f, ofiles)) + " -o python")
	
if __name__ == '__main__':
	compile()

