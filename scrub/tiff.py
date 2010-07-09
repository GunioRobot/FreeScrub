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
#Tags we don't want to strip. http://www.awaresystems.be/imaging/tiff/tifftags.html
GOOD_TAGS = \
    [0xfe, 0xff, 0x100, 0x101, 0x102, 0x102, 0x103, 0x106, 0x107, 0x108, 0x109,
    0x10a, 0x111, 0x112, 0x115, 0x116, 0x117, 0x118, 0x119, 0x11a, 0x11b, 0x11c,
    0x120, 0x121, 0x122, 0x123, 0x128, 0x140, 0x152] + \
    [0x11d, 0x11e, 0x11f, 0x124, 0x125, 0x12d, 0x13d, 0x13e, 0x13f, 0x141,
    0x142, 0x143, 0x144, 0x145, 0x146, 0x147, 0x148, 0x14a, 0x150, 0x153, 
    0x154, 0x155, 0x156, 0x157, 0x158, 0x159, 0x15a, 0x15b, 0x190, 0x193,
    0x1b1, 0x1b2, 0x211, 0x212, 0x213, 0x214, 0x22f, 0x87ac]

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
