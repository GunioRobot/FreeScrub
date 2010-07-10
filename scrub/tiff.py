#!/usr/bin/env python
# -*- coding: utf-8 -*-
#Copyright (c) Michael McKinley, 2010
#All code is released under the simplified (two-clause) BSD license
"""Functions for removing any metadata from a TIFF file"""

from scommon import restore_pos, get_value
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

GOOD_TAGS = {
    'NewSubfileType' : 0xfe,
    'SubfileType' : 0xff,
    'ImageWidth' : 0x100,
    'ImageLength' : 0x101,
    'BitsPerSample' : 0x102,
    'Compression' : 0x103,
    'PI' : 0x106,
    'Threshholding' : 0x107,
    'CellWidth' : 0x108,
    'CellLength' : 0x109,
    'FillOrder' : 0x10a,
    'StripOffsets' : 0x111,
    'Orientation' : 0x112,
    'SamplesPerPixel' : 0x115,
    'RowsPerStrip' : 0x116,
    'StripByteCounts' : 0x117,
    'MinSampleValue' : 0x118,
    'MaxSampleValue' : 0x119,
    'XRes' : 0x11a,
    'YRes' : 0x11b,
    'PConfig' : 0x11c,
    'XPos' : 0x11e,
    'YPos' : 0x11f,
    'FreeOffsets' : 0x120,
    'FreeByteCounts' : 0x121,
    'GrayResponseUnit' : 0x122,
    'GrayResponseCurve' : 0x123,
    'ExtraSamples' : 0x152,
    }
#Tags that point to lists of offsets
OFFSET_TAGS = [GOOD_TAGS['StripOffsets'], GOOD_TAGS['FreeOffsets']]


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
        update_offsets = _walk_tiff(inp, scrubbed, byte_order)

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
    magic = get_value(inp.read(2), byte_order == 'II')
    if magic == 42:
        return byte_order
    else:
        return None


def _walk_tiff(inp, out, byte_order):
    """
    Stage 1: Walk through all the IFDs and each directory entry
    """
    offsets = []
    ifd_offset = inp.read(4)
    out.write(ifd_offset)
    
    ifd_offset = get_value(ifd_offset, byte_order == 'II')

    while ifd_offset is not None and ifd_offset != 0:
        print " IFD at: %d" % ifd_offset
        inp.seek(ifd_offset, os.SEEK_SET)
        _f_seek(out, ifd_offset)

        entries = inp.read(2)
        out.write(entries)
        entries = get_value(entries, byte_order == 'II')
        
        for i in xrange(0, entries):
            offsets += _read_entry(inp, out, byte_order)
        ifd_offset = inp.read(4)
        out.write(ifd_offset)
        ifd_offset = get_value(ifd_offset, byte_order == 'II') 
    return offsets

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

    tag = get_value(header[0:2], byte_order == 'II')
    type_ = get_value(header[2:4], byte_order == 'II')
    count = get_value(header[4:8], byte_order == 'II')

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

if __name__ == "__main__":
    if len(sys.argv) == 1:
        sys.exit("Not enough parameters")
    if len(sys.argv) == 2:
        outfile = "%s-scr" % sys.argv[1] 
    else:
        outfile = sys.argv[2]
    scrub(sys.argv[1], outfile)
