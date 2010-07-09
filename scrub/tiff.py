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
TYPE_L = [1, 1, 1, 2, 4, 8, 1, 1, 2, 4, 8, 4, 8]
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
    #Verify file_out is writeable before we try scrubbing file_in
    open(file_out, 'wb').close()
    
    scrubbed = cStringIO.StringIO()
    with file(file_in, 'rb') as inp:
        byte_order = validate_tiff(inp)
        if byte_order is None:
            raise Exception("Invalid TIFF!")
        walk_tiff(inp, byte_order)

    with file(file_out, 'wb') as output:
        output.write(scrubbed.getvalue())
    scrubbed.close()

def validate_tiff(inp):
    """Validate the given file
    
    If valid, the endiananess is returned. Otherwise, None is returned
    """
    byte_order = inp.read(2)
    if byte_order != 'II' and byte_order != 'MM':
        return None
    magic = get_value(read(inp, 2), byte_order)
    if magic == 42:
        return byte_order
    else:
        return None


def walk_tiff(inp, byte_order):
    ifd_offset = get_value(read(inp, 4), byte_order)
    while ifd_offset is not None and ifd_offset != 0:
        print " IFD at: %d" % ifd_offset
        inp.seek(ifd_offset, os.SEEK_SET)
        entries = get_value(read(inp, 2), byte_order)
        print "\n# Directory entries: %d" % entries
        for i in xrange(0, entries):
#            print "Entry %d" % i
            read_field(inp, byte_order)
        ifd_offset = get_value(read(inp, 4), byte_order) 

def read_field(inp, byte_order):
    tag = get_value(read(inp, 2),byte_order)
    val_type = get_value(read(inp, 2), byte_order)
    count = get_value(read(inp, 4), byte_order) #Vals
    length = count * TYPE_L[val_type] #Length in bytes of data
    offset = read(inp, 4)
    print "Tag: 0x%x" % tag 
    if False:   #Don't do this right now
        if length <= 4:
            print "Value: %s " % offset
        else:
            at_in_file = inp.tell()
            inp.seek(get_value(offset, byte_order), os.SEEK_SET)
            for i in xrange(0, count):
                data = read(inp, TYPE_L[val_type])
                print data, ", ",
            print ""        
            inp.seek(at_in_file, os.SEEK_SET)

def read(inp, count):
    """Read <count> bytes from the file object <inp>"""
    data = inp.read(count)
    if len(data) == 0:
        return None
    return data

def write_value(out, value, byte_order):
    """Write <value> to <out> in the appropriate byte order
    """
    to_write = ""
    while(value):
        byte = chr(value & 0xff)
        if byte_order == "MM":
            to_write = "%s%s" % (byte, to_write)
        elif byte_order == "II":
            to_write = "%s%s" % (to_write, byte)
        value >>= 8
    out.write(to_write)


def get_value(bytes_, byte_order):
    """Converts a <bytes_>, a string of hexidecimal values into an integer
       <byte_order> is either "II" or "MM", representing the endianness of bytes_
    """
    if bytes_ is None:
        return None
    if byte_order == "II":
        bytes_ = reduce(lambda acc, new: "%s%s" % (new, acc), bytes_)
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
