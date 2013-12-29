#!/usr/bin/env python

import sys, os
os.chdir(os.path.dirname(__file__))

# Sorry a bit about the inconsistency.
# This Xcode project file is currently designed for desktop MacOSX apps. The compile script is for a static iOS lib.

import compile
compile.iOS = False
reload(compile)

from mod_pbxproj import *

proj = XcodeProject.Load("Xcode-Python-empty.xcodeproj/project.pbxproj")

proj.add_header_search_paths(paths=[
	"$PROJECT_DIR/pylib",
	"$PROJECT_DIR/CPython/Include",
	], recursive=False)

proj.add_other_cflags(flags=[
	"-DWITH_THREAD",
	"-DPLATFORM=\\\"darwin\\\"",
	"-DHAVE_DYNAMIC_LOADING",
	"-DUSE_DYLD_GLOBAL_NAMESPACE", # needed for e.g. pyobjc
	])

proj.add_other_ldflags(flags=[
	"-lssl", "-lz", "-lcrypto", "-lsasl2", "-lexpat",
	"-framework CoreFoundation",
	"-framework SystemConfiguration"
])

def add_file(fn, group, **kwargs):
	#print fn
	proj.add_file(fn, parent=group, **kwargs)

src = proj.get_or_create_group("src")

for l in ["baseFiles", "extraFiles", "modFiles", "objFiles", "parserFiles"]:
	group = proj.get_or_create_group(l, parent=src)
	
	for fn in list(getattr(compile, l)):
		add_file(fn, group=group)

def addSqlite():
	l = "sqlite"
	group = proj.get_or_create_group(l, parent=src)
	C = compile.Sqlite
	for fn in C.files:
		add_file(fn, group=group, compiler_flags=C.options)
	proj.add_header_search_paths("$PROJECT_DIR/sqlite", recursive=False)
	add_file("sqlite/sqlite3.c", group=group, compiler_flags=["-DSQLITE_ENABLE_FTS4"])
addSqlite()

def addCtypes():
	l = "ctypes"
	group = proj.get_or_create_group(l, parent=src)
	C = compile.Ctypes
	for fn in C.files:
		add_file(fn, group=group, compiler_flags=C.options)
addCtypes()

proj.saveFormat3_2(file_name="Xcode-Python.xcodeproj/project.pbxproj")

