#!/bin/sh
rm -rf copy_paste
mkdir -p copy_paste/repos

svnadmin create --fs-type fsfs copy_paste/repos
R=file://$PWD/copy_paste/repos

svn mkdir -m "Init" $R/trunk
svn checkout $R/trunk copy_paste/wc

svn mkdir copy_paste/wc/original
echo orig file 1 >copy_paste/wc/original/file1
echo orig file 2 >copy_paste/wc/original/file2
echo orig file 3 >copy_paste/wc/original/file3
svn add copy_paste/wc/original/*

svn commit copy_paste/wc -m "populate"
