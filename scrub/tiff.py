#!/usr/bin/env python
# -*- coding: utf-8 -*-
#Copyright (c) Michael McKinley, 2010
#All code is released under the simplified (two-clause) BSD license
"""Functions for removing any metadata from a TIFF file"""

import cStringIO
import os

if __name__ == "__main__":
    import sys

#How many bytes each type takes up (there is no 0-type)
TYPEL = [1, 1, 1, 2, 4, 8, 1, 1, 2, 4, 8, 4, 8]

def scrub(file_in, file_out):
    open(file_out, 'wb').close()
    stripped = cStringIO.StringIO()
    with open(file_in, 'rb') as inp:
        b_ord = inp.read(2)
        if b_ord != 'II' and b_ord != 'MM':
            raise Exception("Invalid TIFF file")
        magic = read(inp, 2, b_ord)
        if magic != '\x00\x2A': #42 in decimal
            raise Exception("Invalid TIFF file")

        print "TIFF file"
        print " Byte order: %s" % b_ord
        ifd_offset = get_value(read(inp, 4, b_ord))
        while ifd_offset is not None and ifd_offset != 0:
            print " IFD at: %d" % ifd_offset
            inp.seek(ifd_offset, os.SEEK_SET)
            entries = get_value(read(inp, 2, b_ord))
            print "\n# Directory entries: %d" % entries
            for i in xrange(0, entries):
                print "Entry %d" % i
                tag = get_value(read(inp, 2, b_ord))
                print " - Tag: %d" % tag
                
                vtype = get_value(read(inp, 2, b_ord))
                print " - Type: %d" % vtype
                
                val_count = get_value(read(inp, 4, b_ord))
                print " - Count: %d" % val_count
                
                val_offset = get_value(read(inp, 4, b_ord))
                print " - Offset: %d" % val_offset
            ifd_offset = get_value(read(inp, 4, b_ord)) 

    with open(file_out, 'wb') as output:
        output.write(stripped.getvalue())
    stripped.close()

def read(stream, count, b_order):
    """Read <count> bytes from the file object <stream> with
       an the given endianness (MM for big, II for little)
       
       Data is returned in big-endian format
       """
    data = stream.read(count)
    if len(data) == 0:
        return None
    if b_order == 'MM':
        return data
    elif b_order == 'II':
        return reduce(lambda acc, new: "%s%s" % (new, acc), data)
    else:
        raise Exception("Invalid byte-order passed")

def get_value(bytes_):
    if bytes_ is None:
        return None
    sum_ = 0
    for byte in bytes_:
        sum_ = (sum_ << 8) + ord(byte)
    return sum_

if __name__ == "__main__":
    if len(sys.argv) == 1:
        sys.exit("Not enough parameters")
    if len(sys.argv) == 2:
        outfile = "%s-scr" % sys.argv[1] 
    else:
        outfile = sys.argv[2]
    scrub(sys.argv[1], outfile)
