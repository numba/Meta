'''
Decompile python byte encoded modules code. 
Created on Jul 19, 2011

@author: sean
'''

from __future__ import print_function

from argparse import ArgumentParser, FileType

import sys
import time
import struct
import marshal
import ast
from py_compile import MAGIC

from meta.decompile.instructions import make_module
from meta.asttools import print_ast, python_source
from meta.decompile.disassemble import print_code
from meta.decompile.recompile import create_pyc
import os

py3 = sys.version_info.major >= 3

def depyc(args):

    bin = args.input.read()
    magic = bin[:4]
    
    if magic != MAGIC:
        raise Exception("Python version mismatch (%r != %r) " % (magic, MAGIC))
    
    modtime = time.asctime(time.localtime(struct.unpack('i', bin[4:8])[0]))

    print("Decompiling module %r compiled on %s" % (args.input.name, modtime,), file=sys.stderr)
    
    code = marshal.loads(bin[8:])
    
    if args.output_type == 'pyc':
        if py3 and args.output is sys.stdout:
            args.output = sys.stdout.buffer
        args.output.write(bin)
        return
            
    if args.output_type == 'opcode':
        print_code(code)
        return 
    
    mod_ast = make_module(code)
    
    if args.output_type == 'ast':
        print_ast(mod_ast, file=args.output)
        return 
    
    if args.output_type == 'python':
        python_source(mod_ast, file=args.output)
        return
        
    
    raise  Exception("unknow output type %r" % args.output_type)

def src_tool(args):
    print("Analysing python module %r" % (args.input.name,), file=sys.stderr)
    
    source = args.input.read()
    mod_ast = ast.parse(source, args.input.name)
    code = compile(source, args.input.name, mode='exec')
    
    if args.output_type == 'opcode':
        print_code(code)
        return 
    elif args.output_type == 'ast':
        print_ast(mod_ast, file=args.output)
        return 
    elif args.output_type == 'python':
        print(source.decode(), file=args.output)
    elif args.output_type == 'pyc':
        
        if py3 and args.output is sys.stdout:
            args.output = sys.stdout.buffer

        try:
            timestamp = int(os.fstat(args.input.fileno()).st_mtime)
        except AttributeError:
            timestamp = int(os.stat(args.input.name).st_mtime)
        if py3 and args.output is sys.stdout:
            args.output = sys.stdout.buffer
        create_pyc(source, cfile=args.output, timestamp=timestamp)
    else:
        raise  Exception("unknow output type %r" % args.output_type)

    return
    
def setup_parser(parser):
    parser.add_argument('input', type=FileType('rb'))
    parser.add_argument('-t', '--input-type', default='from_filename', dest='input_type')
    
    parser.add_argument('-o', '--output', default='-', type=FileType('wb'))
    
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--python', default='python', action='store_const', const='python',
                        dest='output_type')
    group.add_argument('--ast', action='store_const', const='ast',
                        dest='output_type')
    group.add_argument('--opcode', action='store_const', const='opcode',
                        dest='output_type')
    group.add_argument('--pyc', action='store_const', const='pyc',
                        dest='output_type')
    
def main():
    parser = ArgumentParser(description=__doc__)
    setup_parser(parser)
    args = parser.parse_args(sys.argv[1:])
    
    input_python = args.input.name.endswith('.py') if args.input_type == 'from_filename' else args.input_type == 'python'
    
    if input_python:
        src_tool(args)
    else:
        if py3 and args.input is sys.stdin:
            args.input = sys.stdin.buffer
        depyc(args)
        
if __name__ == '__main__':
    main()
