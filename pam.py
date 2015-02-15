import scipy.signal as sp
import numpy as np
import math
from scipy.fftpack import fft, ifft
from math import log, ceil, log10, pi

def rate_map(x,lowcf,highcf,numchans,fs,ti_decay=8.0,hopsize_ms=10.0):
	cf = make_erb_cfs(lowcf,highcf,numchans)
	hop_samples = ms_to_samples(fs,hopsize_ms)
	frame_centers = np.arange(0,x.size,hop_samples)
	ratemap = np.zeros((numchans,frame_centers.size))
	tp = 2.0*pi
	tpt = tp/fs
	wcf = 2.0*pi*cf
	kt = np.arange(0,x.size)/float(fs)
	bw = erb(cf)*1.014
	asc = np.exp(-bw*tpt)
	gain = np.power((bw*tpt),4.0)/3.0
	intdecay = np.exp(-(1000.0/(fs*ti_decay)))
	intgain = 1.0-intdecay
	for c in range(0,numchans):
		a = asc[c]
		q = np.exp(-1j*wcf[c]*kt)*x
		p = sp.lfilter([1,0],[1,-4*a,6*a*a,-4*a*a*a,a*a*a*a],q)
		u = sp.lfilter([1,4*a,4*a*a,0],[1,0],p)
		env = gain[c]*np.abs(u)
		smooth_env = sp.lfilter([1],[1,-intdecay],env)
		ratemap[c,:] = intgain*smooth_env[frame_centers]
	ratemap[ratemap<0] = 0.0
	ratemap = np.power(ratemap,0.3)
	return ratemap
	
def make_erb_cfs(lowf,highf,n):
    return erb_rate_to_hz(np.linspace(hz_to_erb_rate(lowf),hz_to_erb_rate(highf),n))

def erb(x):
    return 24.7*(4.37e-3*x+1)

def erb_rate_to_hz(x):
    return (pow(10,x/21.4)-1)/4.37e-3

def hz_to_erb_rate(x):
    return 21.4*log10(4.37e-3*x+1)

def hw_rectify(x):
	x[x<0]=0
	return x
	
def find_peaks(x):
	mid = x[1:x.size-1]
	lft = x[0:x.size-2]
	rgt = x[2:x.size]
	p = (lft<mid) & (rgt<mid)
	return np.where(p)[0]+1
	
def cross_correlation(x,y,maxlag):
	sig1 = np.append(y,np.zeros((1,maxlag)))
	sig2 = np.append(np.zeros((1,maxlag)),x)
	ccf = ifft(np.conj(fft(sig1))*fft(sig2))
	return ccf[0:2*maxlag+1].real
	
def auto_correlation(x):
	h = abs(fft(x))
	acf = (ifft(h*h)).real
	return acf[0:acf.size/2]
	
def normalise(x,maxval=1.0):
	return maxval*x/float(max(abs(x)))
	
def nearest_power_of_two(n):
	return pow(2,int(log(n,2)+0.5))
	
def next_power_of_two(n):
	return int(pow(2,ceil(log(n,2))))
	
def ms_to_samples(fs,ms):
	return int(round(ms*fs/1000.0))
	
def spectrogram(x,winsize,hopsize):
	n = int((x.size-winsize)/hopsize)
	h = np.zeros((winsize/2,n))
	win = sp.hann(winsize)
	for i in range(1,n):
		st = 0+hopsize*(i-1)
		fn = st+winsize
		y=abs(fft(x[st:fn]*win))
		h[:,i]=y[0:winsize/2]
	return np.log10(h+0.00000001)
	
def preemph(x,c=0.95):
	"""Apply preemphasis filter to a signal
	Parameters:
	x : array_like
		the signal to apply preemphasis to 
	c : float
		the preemphasis coefficient (default 0.95)
	Returns:
		the filtered signal
	"""
	return sp.lfilter([1,c],[1],x)
