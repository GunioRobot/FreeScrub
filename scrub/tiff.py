#!/usr/bin/env python
# -*- coding: utf-8 -*-
#Copyright (c) Michael McKinley, 2010
#All code is released under the simplified (two-clause) BSD license
"""Functions for removing any metadata from a TIFF file"""

from scrubdec import restore_pos
import cStringIO
import os

if __name__ == "__main__":
    import sys

###How many bytes each type takes up (there is no 0-type)
#1  Byte (unsigned)
#2  ASCII (\0-terminated)
#3  Short (unsigned)
#4  Long (unsigned)
#5  Rational
#6  Signed byte
#7  Undefined (generic byte)
#8  Signed short
#9  Signed long
#10 Signed rational
#11 Float
#12 Double

TYPE_L = [1, 1, 1, 2, 4, 8, 1, 1, 2, 4, 8, 4, 8]

#Tags we don't want to strip.
GOOD_TAGS = \
    [0xfe, 0xff, 0x100, 0x101, 0x102, 0x102, 0x103, 0x106, 0x107, 0x108, 0x109,
    0x10a, 0x111, 0x112, 0x115, 0x116, 0x117, 0x118, 0x119, 0x11a, 0x11b, 0x11c,
    0x120, 0x121, 0x122, 0x123, 0x128, 0x140, 0x152] + \
    [0x11d, 0x11e, 0x11f, 0x124, 0x125, 0x12d, 0x13d, 0x13e, 0x13f, 0x141,
    0x142, 0x143, 0x144, 0x145, 0x146, 0x147, 0x148, 0x14a, 0x150, 0x153, 
    0x154, 0x155, 0x156, 0x157, 0x158, 0x159, 0x15a, 0x15b, 0x190, 0x193,
    0x1b1, 0x1b2, 0x211, 0x212, 0x213, 0x214, 0x22f, 0x87ac]


def scrub(file_in, file_out):
    """Scrubs a TIFF of any unnecessary metadata"""
    open(file_out, 'wb').close()
    
    scrubbed = cStringIO.StringIO()
    with file(file_in, 'rb') as inp:
        byte_order = _validate_tiff(inp)
        if byte_order is None:
            raise Exception("Invalid TIFF!")
        scrubbed.write(byte_order)
        _write_value(scrubbed, 42, 2, byte_order)
        _walk_tiff(inp, scrubbed, byte_order)

    with file(file_out, 'wb') as output:
        output.write(scrubbed.getvalue())
    scrubbed.close()

def _validate_tiff(inp):
    """Check if the file's magic number indicates TIFFness
    If valid, the endiananess is returned. Otherwise, None is returned
    """
    byte_order = inp.read(2)
    if byte_order != 'II' and byte_order != 'MM':
        return None
    magic = _get_value(inp.read(2), byte_order)
    if magic == 42:
        return byte_order
    else:
        return None


def _walk_tiff(inp, out, byte_order):
    """
    Walk through all the IFDs and each directory entry
    """
    ifd_offset = inp.read(4)
    out.write(ifd_offset)
    
    ifd_offset = _get_value(ifd_offset, byte_order)

    while ifd_offset is not None and ifd_offset != 0:
        print " IFD at: %d" % ifd_offset
        inp.seek(ifd_offset, os.SEEK_SET)
        _f_seek(out, ifd_offset)

        entries = inp.read(2)
        out.write(entries)
        entries = _get_value(entries, byte_order)
        
        for i in xrange(0, entries):
            _read_entry(inp, out, byte_order)
        ifd_offset = inp.read(4)
        out.write(ifd_offset)
        ifd_offset = _get_value(ifd_offset, byte_order) 

def _f_seek(out, where):
    """Seek to the given point. If it's beyond the end of the file,
    flood that area with \xff"""
    out.seek(0, os.SEEK_END)
    end = out.tell()
    if (where > end):
        out.write('\xff' * (where - end))
    else:
        out.seek(where, os.SEEK_SET)


def _read_entry(inp, out, byte_order):
    """
    Parse a directory entry
    """
    header = inp.read(12)
    data = inp.read(4)

    tag = _get_value(header[0:2], byte_order)
    type_ = _get_value(header[2:4], byte_order)
    count = _get_value(header[4:8], byte_order)

    length = count * TYPE_L[type_]
    
    out.write(header)
    out.write(data)

def _write_value(out, value, length, byte_order):
    """
    Write <value> to <out> in the appropriate byte order
    into a field of <length> bytes
    """
    to_write = ""
    
    #Build the string
    while(value):
        byte = chr(value & 0xff)
        if byte_order == "MM":
            to_write = "%s%s" % (byte, to_write)
        else:
            to_write = "%s%s" % (to_write, byte)
        value >>= 8

    #Add padding
    if len(to_write) < length:
        if byte_order == "MM":
            to_write = "%s%s" % ('\x00' * (length - len(to_write)), to_write)
        else:
            to_write = "%s%s" % (to_write, '\x00' * (length - len(to_write)))


    out.write(to_write)


def _get_value(bytes_, byte_order):
    """Converts a <bytes_>, a string of hexidecimal values into an integer
       <byte_order> is either "II" or "MM", representing the endianness of 
       bytes_
    """
    if bytes_ is None:
        return None
    print bytes_ 
    #Reverse the order of bytes_ if it is little-endian
    if byte_order == "II":
        bytes_ = reduce(lambda acc, new: "%s%s" % (new, acc), bytes_, "")
    
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
