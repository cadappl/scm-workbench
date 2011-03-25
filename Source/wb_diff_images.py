'''
 ====================================================================
 Copyright (c) 2003-2006 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================


    wb_diff_images.py

'''

import cPickle
import cStringIO
import zlib
import wx

#----------------------------------------------------------------------
def getDownArrowData():
    return cPickle.loads(zlib.decompress(
'x\xdae\xcc=\x0e\xc3 \x0c\x86\xe1=\xa7\xf8\xa4\x0etBEIPw$.\x90\x85\xb5\xca\
\x1a\x89\xdc\x7f\x8a\xcd\x8fcR\x8b\xc1\xef#\xe0}\x9cn\xda\x8c[Ag\x813\xd3o3\
\xc0\x8eW\xf0a\x0e\xbet\xe6\xfe\xd0\xc4X\xdar\xc7\xc8R:q\x7f\x17i\x00\xb6N\
\xca\xb4\x8f\x96\xf2\x9f\x11=\x8d\xe9a\x85F\xab4X#1Z;\xf1\xd4{YO\x7f\xabI\
\xfeS$\x86\x9bn\x83\x902t\xd2\x86Fl\xf6\x02\x96\x15\\\xc5' ))

def getDownArrowBitmap():
    return wx.BitmapFromXPMData(getDownArrowData())

def getDownArrowImage():
    return wx.ImageFromBitmap(getDownArrowBitmap())

#----------------------------------------------------------------------
def getUpArrowData():
    return cPickle.loads(zlib.decompress(
'x\xdae\xcd\xb1\n\x80 \x10\xc6\xf1\xbd\xa78h\xb0\xe9#\xa9\xa4]\xf0\x05\\\\\
\xa35\xb0\xf7\x9f\xf2\xd4L\xedP\x8e\xffo\xd0\xe9\xba\xe5`\x85\xdc(\x9c\x95\
\xa4\x18\x0e+\x88N\x1a\xb5\xd2\x8bV\xb1\xc1=\x871&\xb6\xe76\x86%\xb6\xe3\xde\
\xd7\xd2\x94\x06yW\x06\xa07\xe0\xc5b@\xc1\xd7\x80\x0f\xb3\x01\x15&C=\xc9*p\
\xe1v\xef9\xff\xfb\xc3\xf9\x9f\x05\xea\x8d\xa9\xb3H\xad%j,S6<\xba>L\xc6' ))

def getUpArrowBitmap():
    return wx.BitmapFromXPMData(getUpArrowData())

def getUpArrowImage():
    return wx.ImageFromBitmap(getUpArrowBitmap())

#----------------------------------------------------------------------
def getWhiteSpaceData():
    return cPickle.loads(zlib.decompress(
'x\xda\xd3\xc8)0\xe4\nV74S\x00"c\x05Cu\xae\xc4`\xf5\x08\x85d\x05\xa7\x9c\xc4\
\xe4l0O\x01\xc8Sv6s6v6\x03\xf3\xf5@|\x0b\x13\x03\x03\x0b\x13\xa8<*\xa0\xb2\
\xa0\x1e\x01A===\xb8 \x90\tu"T\x89\x02HHA\x0f\xae\x12\xc8\x89\x88\x80\xc8\
\xe9!\xab\xc4\x10\xd4\xc3\xa6\x1dn&\xdc"\xea\xfb]\x0f\x00\xb6(B\x0c' ))

def getWhiteSpaceBitmap():
    return wx.BitmapFromXPMData(getWhiteSpaceData())

def getWhiteSpaceImage():
    return wx.ImageFromBitmap(getWhiteSpaceBitmap())

#----------------------------------------------------------------------
def getDinoData():
    return cPickle.loads(zlib.decompress(
'x\xda\x85\xd2\xbbn\x830\x14\x06\xe0=Oa\t\x0cU\x8et\xc4-\xb4#4m\xc7z\xc8\xe2\
5\x8a25\xea\xe9\xfbO\xf5\x85\x8b\xed\xd8pD\x86_\xf9\xf4\xdb\x18\xbf<\xfe\xea\
\xc3\xa5l[\xa6\x9e\xbaauy\xb8^Jd7\xf6\xfe\xb8\xde~L\x02\x95\xb2\xf146\xe3\
\xc9d\xd2\xb9o\xab\xea\xad3\xf9hsSU\x95\xc9B\xe7s\xff\xf1u\xeeM\xceu\xfe|\
\x1d\x9b)\x0f:w\xcd\xe2\xb9\xed_\xfa\xe4\x9c\'\xcfT\xfe\xa6\xdf\xbb\t\x85-\
\xeb\xeb\tgv\xf1\xbe\xee\x9a\t\xefLB!\xea\x1fn+D\x9f%\xbb\x94\xd8Uf\xcd\x1d5\
7m\xef\x0b\xe7a\xfb+\xaehS\xed\x9d\x97"\x92ho_B\x10\x91\x94\xb4\xf5\x8e(\x98\
 \x10\x0e\x8b\xab\x01H0XYD!e\x03\x12\xa0.\x93)\x85@4\x10e\x98ie\xcb\x9e\x14\
\x02(\xa6\x1et^ P\x88\x90\x9bQ\x8cs\xc5bJ\x15\xe5\xce(\xfa\xac\x96"=\xc5\xc4\
B\xe5\x17\x01/\x8a\x88\nV\xcb\xe1\x18\xe9\n\x91Q\x14\x9e*B\xc1SU\xae\xb2\x1b\
v\xd4\x82\xbc}\xe97\x9b\xfb\x00s\x88+\x98\x0f \x87\xc2C\xf1\x93\x00\xb4\xdf)\
z\xbf\xcc\x7fj\x10\xb9F\xeb%\x0c\xbf\x90\x19m8\xcd\xb7&y\xbf\xc8\xbf\xcfI%=\
\x94PR\xba\xeb%\x94\x0c\xaa\xb4\xc2\x7f\xe4\xb0\x02J' ))

def getDinoBitmap():
    return wx.BitmapFromXPMData(getDinoData())

def getDinoImage():
    return wx.ImageFromBitmap(getDinoBitmap())

#----------------------------------------------------------------------
def getCollapseData():
    return cPickle.loads(zlib.decompress(
'x\xda\xd3\xc8)0\xe4\nV74S\x00"\x13\x05Cu\xae\xc4`\xf5\x08\x85d\x05e#C#\x03\
\x0b\x130_\x0f\xc47\x00\x02(?\x1f\xc4w\x03\x030_\x01\xc8\xf7\xcb\xcfK\x85r\
\xf4@@\x01\x06\x90\x05\xf50\x05#\x10\xa2H\x82\x08Q\x14\xed0QtA=\xac\x82zH\
\x82\xf90\x00\x12\xc5+\x88U;\x04D`\xb7\x08\x9b\x93\xb0\xf9\x08\x9b\xdf\xb1\
\x85\x12r\xd0\xe9\x01\x00\xf6.O\xc0' ))

def getCollapseBitmap():
    return wx.BitmapFromXPMData(getCollapseData())

def getCollapseImage():
    return wx.ImageFromBitmap(getCollapseBitmap())

#----------------------------------------------------------------------
def getExpandData():
    return cPickle.loads(zlib.decompress(
'x\xda\xd3\xc8)0\xe4\nV74S\x00"\x13\x05Cu\xae\xc4`\xf5\x08\x85d\x05e#C#\x03\
\x0b\x130_\x0f\xc47\x00\x02(?\x1f\xc4w\x03\x030_\x01\xc8\xf7\xcb\xcfK\x85r\
\xf4@@\x01\x06\x90\x05\xf50\x05#\x10\xa2H\x82\x08Q$\xed\xf9\xf9\xf9PQtA=\xac\
\x82zH\x82\xf90\x00\x12\xc5+\x88U;D0\x02\xbbE\x98\xde\xc4t|D\x046ob\x0b\x10\
\xd4\xa0\xd3\x03\x00\x01\xa7TR' ))

def getExpandBitmap():
    return wx.BitmapFromXPMData(getExpandData())

def getExpandImage():
    return wx.ImageFromBitmap(getExpandBitmap())

#----------------------------------------------------------------------
def getAppIconData():
    return zlib.decompress(
'x\xda\x01!\x04\xde\xfb\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00 \x00\
\x00\x00 \x08\x06\x00\x00\x00szz\xf4\x00\x00\x00\x04sBIT\x08\x08\x08\x08|\
\x08d\x88\x00\x00\x03\xd8IDATx\x9c\xed\x97\xbfk\xe3f\x18\xc7?\n\x06\x0f1\xc4\
r\xd6K\x08\xaf\n\xed\xc1\x95\x96JCq!\rT\x1a\xca\r]j\r\xe1\x86\xe0AZ\x1a\xb8L\
V\x97\x0eG\x07\xbfS\x0cI\x06{\x08\xdcp\xc39\x8b\x0bwt\xb0:\xa4\xc3\xd1!*\x94\
\x1e\xa4\x85Z\x7f\x82\x95\x0e7\x04\no\x07Y\xba8\x8e/"\xa1\xd7\xe5\x9eE\xef\
\x0bz\x9f\xef\xf7\xfd>\xbf$\xadZ\xad\xf2\x7f\xda\xc2m\x1d8\x8e\xa3,\xcbRo\
\x9d\x80eYJ\xd34\x05\x10E\xd1M\xdd\xdc\x8c\x80\xef\xfb*\x8ec\xda\xed6\xb6m\
\xdf\x18<\'\xd0\xe9\xec\xabNg\xbf\xb0\x8cRJZ\xadV\xbe\x17B\xe4\xebNg_\xd5j5e\
\x18F!\x7f\x0b\x00/^\xfc\xcc\xe9\xe9\xefX\x96\xa5\x06\x83\xc1\xb5\x07M\xd3\
\x9c\xda\x0b!\xb0,KI)\xd5\xde\xde.\x87\x87\x87x\x9eW\xe82\xa5\xcc\xa1m\xdb\
\x84I\xc2\x8fGG\xf8\xbe\xaf\xba\xdd\xaeV\xc4A\xb9\xbc\xc8\xfd\xfb_q~\xfe\x8a\
8\x8e9\xf9\xe5\'(-qppP\x88\xc0\x02@\xab\xd5\xd2\xa4\x94x\x1f\xbd\x87\xe7y$I\
\x82\xef\xfbs\x95\xd0u}j\xbf\xb6v\x07\xd34i\x7f\xff-\x94\x968>>.\x9c\x98\xa5\
l\xd1\xef\xf7\xb58\x8e\x95\x10"\x070\x0cCmo\xef\xf0\xf0\xe17Sjd1/\x97\x17\
\x01\xa8T*\xf9\x99(\x8ah6\x9b\x8c\xc7\xe3B\nj\xf3\x1a\x91\xe38*\x03\n\xc3\
\x90\x8c\xc8`0P\x1b\x1b\x1bt\xbb]\xca\xe5E\xd6\xd6\xee\xb0\xb2\xb2\x82X]\xc6\
\xfa\xf4\x0bF\xa3Q!\xe0\xcc\xe6\x96\xe1p8\xd4\xee\xde\xfd\x90(\x8a\xd8\xde\
\xde\xc9\x93\xb4\xd9l\xd2h4r\xf0J\xa5\x02\xc0\xe3\'\xcf\xa6\xaa\xa1\xa8\xcdU\
\xe0\xa29\x8e\xa3l\xdb\xa6\\^dgg\x9b\xdd\xdd=\x00\xee\xdd\xfb \x97\xdeq\x9c\
\xc2\xb2_\xb4B\x8dh8\x1cj\xe5\xf2"[[\x0fh4\x1a@\x9ax\x00bu\x19)\xe5\x8d\xc0\
\x0b\x13\x008?\x7f\x85\x10\x82z}=\x97^\xd7u\x1e?y\xf6vZq\x10\x04S\xdd/\x93\
\xfe\xd1\xa3\xef\xf2\xd8w:\xfb\xea\xacv\xa6\xa4\x94\x85\xbbj\xe9\xfaW\xd2\
\xc1#\x84\x98J<\xb1\xba\x8c\xf3\xe5\xd7\xd8\xb6\x9d\x11S[\xa7\x0f\xa0\x0f\
\xbd\xc8\x07\x8a\x8d\xf97* \xa5T\xae\xeb\xaa$I\xa8\xd7\xd7\x81\xd75\xdf;|\
\x8a\xae\xeb\xd4\xeb\xeb\x04A@\xac\xc7\x90\xa6\x07Q\x02\xae\xeb*H\x07\xd7\
\x9b\xe6\xcc\x95U\xe0\xfb\xbe\x92R\x925%\xcf\xf3\xa6j>I\x12\\\xd7\xcd\x13OJ\
\xa9|\xdd\x87\x8bU\xd8\x03\x12RR=h\x99-\xaej\xef3\x04\xa4\x94\xca\xf7}<\xcf\
\xcb\x87\xceE\xe9u]GJI\xbd\xbe\x9ew\xc8Z\xad\xa6\xe2v\x0c\xf1\x04\xb8\x05d\
\xf3*\x01\x8e\x80\x18llNNN\xa6H\xcc\x84\xe02x\x96\xe1\x19\xb8X]fss\x93\xe7\
\xcf\x7f\xc8\xcf\x8c\xc7c\xcd\x0b=\xaa\xed\xaaV\x1dW5z\x17\xc0C J\xd7\xa1\
\x1erf\x9d)\xdf\xf7\x951\t\xd1\x0c\x01!\x04\xa6i\x12\x86!A\x10\x90$\t{{\xbb\
\xbc|\xf9\x07bu\x19JK|\xfe\xd9\xc73\xa5\xd7\xef\xf7_\xdf\xac\x91\xde\x18\x1f\
\xd0\'\x8a0Q\x02\x90\xba\xc4\xf4\xe6\x84\xc00\x0c%\x84 \x8a\xa2\xa9\xe6bY\
\x96\x1a\x0e\x87\xe9\xe6\x9f\xbf1\xde\xffdn\xf31\x0cCE\x8d(\rCoB\xc6\x9b<% @\
 \x18\x8f\xc7\xda\x8c\x02\xa3\xd1H\xbb\x0c\x0e\x10\xc7q\xbe\xee\x1d>\x9d\xf9\
(\xb9\xec\xa3\x95\xb4R0{\xa2\xc0$\x0f\xe8\xa6\xefd}\xa4\xd0,\x804\xd1F\x7f\
\xfeJ\xf4\xdb_8\x8e\x83R\xaaP\xebu]W\xf5\xa2^^\xa2\x84\xe0\t/\x0fY!\x02\x96e\
\xa9l\x06\x04A\x80\xe7yW\x96\xd4u>BB\x00\xaa\'\xd5\xfcl\xe1i\x18\xc71\xba\
\xae\xcf\x94\xd1m\xadp\x08\xfe+\xbb\xf5\x9f\xd1;\x02\xef\x08\xdc\xd6\xfe\x05\
\x1f\x13\x86\xf5J2\x91\x15\x00\x00\x00\x00IEND\xaeB`\x82\xc4\x9f\xf5}' )


def getAppIconBitmap():
    return wx.BitmapFromImage(getAppIconImage())

def getAppIconImage():
    stream = cStringIO.StringIO(getAppIconData())
    return wx.ImageFromStream(stream)

def getAppIconIcon():
    icon = wx.EmptyIcon()
    icon.CopyFromBitmap(getAppIconBitmap())
    return icon
