#!/usr/bin/env python
# -*- coding: utf-8 -*-
#Copyright (c) Michael McKinley, 2010
#All code is released under the simplified (two-clause) BSD license
"""Functions for removing any metadata from a TIFF file"""

import cStringIO
import os

if __name__ == "__main__":
    import sys

def scrub(file_in, file_out):
    open(file_out, 'wb').close()
    stripped = cStringIO.StringIO()
    with open(file_in, 'rb') as input_:
        byte_order = input_.read(2)
        if byte_order != 'II' and byte_order != 'MM':
            raise Exception("Invalid TIFF file")
        magic = read(input_, 2, byte_order)
        if magic != '\x00\x2A': #42 in decimal
            raise Exception("Invalid TIFF file")

    with open(file_out, 'wb') as output:
        output.write(stripped.getvalue())
    stripped.close()

def read(stream, count, b_order):
    """Read <count> bytes from the file object <stream> with
       an the given endianness (MM for big, II for little)
       
       Data is returned in big-endian format
       """
    data = stream.read(count)
    if b_order == 'MM':
        return data
    elif b_order == 'II':
        return reduce(lambda acc, new: "%s%s" % (new, acc), data)
    else:
        raise Exception("Invalid byte-order passed")

if __name__ == "__main__":
    if len(sys.argv) == 1:
        sys.exit("Not enough parameters")
    if len(sys.argv) == 2:
        outfile = "%s-scr" % sys.argv[1] 
    else:
        outfile = sys.argv[2]
    scrub(sys.argv[1], outfile)
