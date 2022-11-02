from sys import path
from numpy import zeros ,int16
from pygame import mixer ,sndarray ,time
from pylibpd import *

prnt = ''
def pd_receive(*s):
	global prnt
	if len(s[0]):
		prnt += s[0]
		if prnt[-1] == '\n':
			print(f'Pd:{prnt}' ,end='')
			prnt = ''
libpd_set_print_callback(pd_receive)

chIn ,chOut ,samplerate ,ticks = \
1    ,2     ,48000      ,1
m = PdManager(chIn ,chOut ,samplerate ,ticks)

dir = f'{path[0]}/../pylibpd/pd'
libpd_add_to_search_path(dir)

mixer.init(frequency = samplerate)
blocksize = libpd_blocksize()
dummy = array.array('h' ,range(blocksize))
bufsize = blocksize * 64
sounds = [mixer.Sound(zeros((bufsize ,chOut) ,int16)) for _ in range(2)]
samples = [sndarray.samples(s) for s in sounds]
mixer.quit()

blk = blocksize * chOut
clock = time.Clock()
playing = False
selector = 0

def open(patch='main.pd' ,volume=1 ,play=True):
	volume = max(-1 ,min(volume ,1))
	patch = libpd_open_patch(patch ,path[0])
	if patch:
		libpd_float(f'{patch}vol' ,volume)
		if play:
			libpd_bang(f'{patch}play')
	return patch

def loop():
	global selector
	i = blk
	mixer.init(frequency = samplerate)
	ch = mixer.Channel(0)
	while playing:
		if not ch.get_queue() or not ch.get_busy():
			for j in range(bufsize):
				if i >= blk:
					outbuf = m.process(dummy)
					i = 0
				# de-interlace the data coming from libpd
				for c in range(chOut):
					samples[selector][j][c] = outbuf[i + c]
				i += chOut
			# queue up the buffer we just filled to be played by pygame
			ch.queue(sounds[selector])
			# next time we'll do the other buffer
			selector = int(not selector)
		# cap the framerate
		clock.tick(20)
	mixer.quit()
