#!/bin/bash

cp gnuradiopatch/*.py /usr/local/lib/python2.7/dist-packages/grc_gnuradio/blks2/
cp gnuradiopatch/*.xml /usr/local/share/gnuradio/grc/blocks/

echo 100 > /proc/sys/net/ipv4/tcp_syn_retries 
echo 0 > /proc/sys/net/ipv4/tcp_syncookies
echo 100 > /proc/sys/net/ipv4/tcp_synack_retries



