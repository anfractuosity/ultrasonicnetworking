# Copyright 2008,2009,2012-2013 Free Software Foundation, Inc.
#
# This file is part of GNU Radio
#
# GNU Radio is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
#
# GNU Radio is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with GNU Radio; see the file COPYING.  If not, write to
# the Free Software Foundation, Inc., 51 Franklin Street,
# Boston, MA 02110-1301, USA.
#

from gnuradio import gr, digital
from gnuradio import blocks
from gnuradio.digital import packet_utils
import gnuradio.gr.gr_threading as _threading
import numpy
import array
import pmt

##payload length in bytes
DEFAULT_PAYLOAD_LEN = 512

##how many messages in a queue
DEFAULT_MSGQ_LIMIT = 2

##threshold for unmaking packets
DEFAULT_THRESHOLD = 12

##################################################
## Options Class for OFDM
##################################################
class options(object):
    def __init__(self, **kwargs):
        for key, value in kwargs.iteritems(): setattr(self, key, value)

##################################################
## Packet Encoder
##################################################
class _packet_encoder_thread(_threading.Thread):

    def __init__(self, msgq, payload_length, send):
        self._msgq = msgq
        self._payload_length = payload_length
        self._send = send
        _threading.Thread.__init__(self)
        self.setDaemon(1)
        self.keep_running = True
        self.start()

    def run(self):
        sample = '' #residual sample
        while self.keep_running:
            msg = self._msgq.delete_head() #blocking read of message queue
            sample = sample + msg.to_string() #get the body of the msg as a string
            while len(sample) >= self._payload_length:
                payload = sample[:self._payload_length]
                sample = sample[self._payload_length:]
                self._send(payload)



class packet_encoder(gr.basic_block):
    """
    Hierarchical block for wrapping packet-based modulators.
    """

    def __init__(self, samples_per_symbol, bits_per_symbol, preamble='', access_code='', pad_for_usrp=True):
        """
        packet_mod constructor.
        
        Args:
            samples_per_symbol: number of samples per symbol
            bits_per_symbol: number of bits per symbol
            access_code: AKA sync vector
            pad_for_usrp: If true, packets are padded such that they end up a multiple of 128 samples
            payload_length: number of bytes in a data-stream slice

        """

	print "here1"
	gr.basic_block.__init__(self,name="packet_encoder",in_sig=[numpy.uint8],out_sig=[numpy.uint8])
        #setup parameters
        self._samples_per_symbol = samples_per_symbol
        self._bits_per_symbol = bits_per_symbol
        self._pad_for_usrp = pad_for_usrp
        if not preamble: #get preamble
            preamble = packet_utils.default_preamble
        if not access_code: #get access code
            access_code = packet_utils.default_access_code
        if not packet_utils.is_1_0_string(preamble):
            raise ValueError, "Invalid preamble %r. Must be string of 1's and 0's" % (preamble,)
        if not packet_utils.is_1_0_string(access_code):
            raise ValueError, "Invalid access_code %r. Must be string of 1's and 0's" % (access_code,)

        self._preamble = preamble
        self._access_code = access_code
        self._pad_for_usrp = pad_for_usrp
        #create blocks
        msg_source = blocks.message_source(gr.sizeof_char, DEFAULT_MSGQ_LIMIT)
        self._msgq_out = msg_source.msgq()

	


	#self.in_sig=[numpy.uint8]
	#self.out_sig=[numpy.uint8]
        #initialize hier2
       
        #connect
        
	#self.connect(msg_source, self)


    def general_work(self, input_items, output_items):

        out = output_items[0]
        num_input_items = len(input_items[0])
	nread = self.nitems_read(0)
        tags = self.get_tags_in_range(0, nread, nread+num_input_items)

        i = 0 

	in0 = input_items[0]
	#print in0
	
	a2 = []
	s = ""
	su = 0

	gi = 0
	iv = 0

	ov = 0

        for tag in tags:

	    print "K: ",tag.key," V: ",tag.value
	    o = in0[i:i+int(str(tag.value))]

	    s = ""
	    for e in o:
		s+=chr(e)

	    packet = packet_utils.make_packet(
            	s,
            	self._samples_per_symbol,
            	self._bits_per_symbol,
            	self._preamble,
            	self._access_code,
            	self._pad_for_usrp
            )	

            arr = array.array('B', packet)
	    a2 = [ int(a) for a in arr ] 

	    ov += len(a2)

            for z in a2:
                out[gi] = z
                gi = gi + 1

	    self.consume(0,int(str(tag.value)))

	    return ov
        return 0

    def send_pkt(self, payload):
        """
        Wrap the payload in a packet and push onto the message queue.
        
        Args:
            payload: string, data to send
        """
        packet = packet_utils.make_packet(
            payload,
            self._samples_per_symbol,
            self._bits_per_symbol,
            self._preamble,
            self._access_code,
            self._pad_for_usrp
        )
        msg = gr.message_from_string(packet)
        self._msgq_out.insert_tail(msg)

##################################################
## Packet Decoder
##################################################
class _packet_decoder_thread(_threading.Thread):

    def __init__(self, msgq, callback):
        _threading.Thread.__init__(self)
        self.setDaemon(1)
        self._msgq = msgq
        self.callback = callback
        self.keep_running = True
        self.start()

    def run(self):
        while self.keep_running:
            msg = self._msgq.delete_head()
            ok, payload = packet_utils.unmake_packet(msg.to_string(), int(msg.arg1()))
            if self.callback:
                self.callback(ok, payload)




class packet_decoder_out(gr.basic_block):
	
	
	def __init__(self):
		self.msgs = []
		gr.basic_block.__init__(self,name="packet_decoder_out",in_sig=[],out_sig=[numpy.uint8])
		print "here"
		self.glof = 0

	def general_work(self, input_items, output_items):
		#print "some"

		out = output_items[0]

		if len(self.msgs) > 0:
			print "---------------------------------------"
			gi = 0	
			s = 0
			while True:	

				try :
					p = self.msgs.pop()
			                print "ere"
				except IndexError:
					break

				if p == None:
					break
				
				off = gi
				print ("Off ",off)				
				
				arr = numpy.frombuffer(p, numpy.uint8) 
        	    		for z in arr:
			                out[gi] = z
        	        		gi = gi + 1
	
				
				#self.add_item_tag(0, 0, pmt.string_to_symbol("packet_len"), pmt.from_long(len(arr)))
				self.add_item_tag(0, self.glof, pmt.string_to_symbol("packet_len"), pmt.from_long(len(arr)))
				self.consume(0,0)

				self.glof += len(arr)
				s += len(arr)


				return s
		self.consume(0,0)
		return 0

	def callback(self,a,b):
		if a:
			print "called"
			self.msgs.append(b)
			

class packet_decoder(gr.hier_block2):
    """
    Hierarchical block for wrapping packet-based demodulators.
    """

    def __init__(self, access_code='', threshold=-1, callback=None):
        """
        packet_demod constructor.
        
        Args:
            access_code: AKA sync vector
            threshold: detect access_code with up to threshold bits wrong (0 -> use default)
            callback: a function of args: ok, payload
        """
        #access code
        if not access_code: #get access code
            access_code = packet_utils.default_access_code
        if not packet_utils.is_1_0_string(access_code):
            raise ValueError, "Invalid access_code %r. Must be string of 1's and 0's" % (access_code,)
        self._access_code = access_code
        #threshold
        if threshold < 0: threshold = DEFAULT_THRESHOLD
        self._threshold = threshold
        #blocks
        msgq = gr.msg_queue(DEFAULT_MSGQ_LIMIT) #holds packets from the PHY
        correlator = digital.correlate_access_code_bb(self._access_code, self._threshold)
        framer_sink = digital.framer_sink_1(msgq)
        #initialize hier2
        gr.hier_block2.__init__(
            self,
            "packet_decoder",
            gr.io_signature(1, 1, gr.sizeof_char), # Input signature
            gr.io_signature(1, 1, 1) # Output signature
        )

        #connect
        self.connect(self, correlator, framer_sink)
	self.pktout = packet_decoder_out()
        self.connect(self.pktout, self)

        #start thread
        _packet_decoder_thread(msgq, self.pktout.callback)









"""
class packet_decoder(gr.basic_block):


    def me():
	print "msg"

    def __init__(self, access_code='', threshold=-1, callback=None):

        #access code
        if not access_code: #get access code
            access_code = packet_utils.default_access_code
        if not packet_utils.is_1_0_string(access_code):
            raise ValueError, "Invalid access_code %r. Must be string of 1's and 0's" % (access_code,)
        self._access_code = access_code
        #threshold
        if threshold < 0: threshold = DEFAULT_THRESHOLD
        self._threshold = threshold

	#gr.sync_block.__init__(self,name="packet_decoder",in_sig=[numpy.uint8],out_sig=[numpy.uint8])
	gr.basic_block.__init__(self,name="packet_decoder",in_sig=[numpy.uint8],out_sig=[numpy.uint8])
        #blocks
      
        #connect
        #self.connect(self, correlator, framer_sink)
        #start thread
        
	#_packet_decoder_thread(msgq, me)





	
    def general_work(self, input_items, output_items):
        out = output_items[0]
	msg = ""
	gi = 0
	for v in input_items[0]:
		msg = msg + chr(v)
	
	if(len(msg)!=0):
	    print ("len ",len(msg))



        num_input_items = len(input_items[0])
	if num_input_items != 0 :
		print num_input_items

	msg = ""

	msgl = len(input_items[0])
	for v in input_items[0][0:9]:
		msg = msg + chr(v)


            

	a2 = []


	off = 0
	while True:

		if off > 0:
			print("OFF: ",off)

		msg = ""
		for v in input_items[0][off:off+9]:
			msg = msg + chr(v)

		if len(input_items[0][off:]) > 0:
			print len(input_items[0][off:])
		
		
		ok, payload = packet_utils.unmake_packet(msg,0) #/*, num_input_items)
			


		if ok:
			a2 = numpy.frombuffer(payload, numpy.uint8) 
			print "ok"
			gi = 0
			for z in a2:
		            out[gi] = z
		            gi = gi + 1
	
			off = off + len(a2)
			
		else:
			off = off + 1
			
		if off >= msgl:
			break
		
	self.consume(0,len(input_items[0]))
		
		
	#self.consume(0,len(msg))
	return len(a2)*2

"""



##################################################
## Packet Demod for OFDM Demod and Packet Decoder
##################################################
class packet_demod_base(gr.hier_block2):
    """
    Hierarchical block for wrapping packet sink block.
    """

    def __init__(self, packet_sink=None):
        #initialize hier2
        gr.hier_block2.__init__(
            self,
            "ofdm_mod",
            gr.io_signature(1, 1, 1), # Input signature
            gr.io_signature(1, 1, 1) # Output signature
        )
        #create blocks
        """msg_source = blocks.message_source(self._item_size_out, DEFAULT_MSGQ_LIMIT)
        self._msgq_out = msg_source.msgq()
        #connect
        self.connect(self, packet_sink)
        """
	##self.connect(self, packet_sink)
	#self.connect(packet_sink,self)



        msg_in = blocks.message_source(1, DEFAULT_MSGQ_LIMIT)
        msgq = msg_in.msgq()


	#msgq = gr.msg_queue(DEFAULT_MSGQ_LIMIT)
	correlator = digital.correlate_access_code_bb(packet_sink._access_code, packet_sink._threshold)
        framer_sink = digital.framer_sink_1(msgq)
        self.connect(self, packet_sink)
        self.connect(packet_sink, self)

"""
        self.connect(self, correlator)
        self.connect(correlator,framer_sink)
	self.connect(msg_in,packet_sink)
        self.connect(packet_sink,self)


    def recv_pkt(self, ok, payload):
        msg = gr.message_from_string(payload, 0, self._item_size_out,
                                     len(payload)/self._item_size_out)
        if ok: self._msgq_out.insert_tail(msg)
"""

class packet_demod_b(packet_demod_base): _item_size_out = gr.sizeof_char
class packet_demod_s(packet_demod_base): _item_size_out = gr.sizeof_short
class packet_demod_i(packet_demod_base): _item_size_out = gr.sizeof_int
class packet_demod_f(packet_demod_base): _item_size_out = gr.sizeof_float
class packet_demod_c(packet_demod_base): _item_size_out = gr.sizeof_gr_complex

