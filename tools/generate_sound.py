"""Generate the original upbeat, futuristic audio used by the Canvas hero.

Requires numpy. Run from the repository root, then encode the WAV to MP3 with
ffmpeg; the website itself has no build-time dependencies.
"""
from pathlib import Path
import wave
import numpy as np

RATE=44100
DURATION=30
COUNT=RATE*DURATION
mix=np.zeros(COUNT,dtype=np.float64)
rng=np.random.default_rng(20260924)

def add(at,signal,level=1):
    start=int(at*RATE)
    if start>=COUNT:return
    length=min(len(signal),COUNT-start)
    if length>0:mix[start:start+length]+=level*signal[:length]

def tones(at,freqs,length,level=.1,attack=.025,release=.3):
    n=int(length*RATE);t=np.arange(n)/RATE
    envelope=np.minimum(1,t/max(attack,.001))*np.minimum(1,(length-t)/max(release,.001))
    wave=sum(np.sin(2*np.pi*f*t+.25*np.sin(2*np.pi*1.8*t))/len(freqs) for f in freqs)
    add(at,envelope*wave,level)

# A new, original 120 BPM synth cue. Eight-beat chords: Cmaj7, Gmaj7,
# Am7, Fmaj7, repeated. Harmonic rhythm follows the motion scenes.
chords=[(130.81,[261.63,329.63,392.0,493.88]),
        (98.0,[246.94,293.66,392.0,493.88]),
        (110.0,[220.0,261.63,329.63,392.0]),
        (87.31,[220.0,261.63,349.23,440.0])]
for start in range(0,DURATION,4):
    root,notes=chords[(start//4)%4]
    tones(start,[n/2 for n in notes],min(4,DURATION-start),.105,.33,.68)

for i in range(DURATION*4):
    at=i*.25
    root,notes=chords[(int(at)//4)%4]
    freq=notes[(i*3+int(at//4))%4]*(2 if i%8==7 else 1)
    n=int(.45*RATE);t=np.arange(n)/RATE
    envelope=(1-np.exp(-t*75))*np.exp(-t*10)
    pluck=np.sin(2*np.pi*freq*t)+.22*np.sin(2*np.pi*freq*2*t)
    add(at,pluck*envelope,.115)

for i in range(DURATION*2):
    at=i*.5
    root,_=chords[(int(at)//4)%4]
    n=int(.38*RATE);t=np.arange(n)/RATE
    bass=np.sin(2*np.pi*root*t)*np.exp(-t*6)
    add(at,bass,.145)
    # Soft four-on-the-floor kick with a downward pitch sweep.
    kick=np.sin(2*np.pi*(58*t+48*(1-np.exp(-t*28))/28))*np.exp(-t*17)
    add(at,kick,.18 if i%4==0 else .12)

for i in range(DURATION*4):
    at=i*.25
    n=int(.09*RATE);t=np.arange(n)/RATE
    noise=rng.normal(size=n)
    high=noise-np.convolve(noise,np.ones(9)/9,mode='same')
    add(at,high*np.exp(-t*47),.024 if i%2 else .037)

for i in range(DURATION//2):
    at=i*2+.5
    n=int(.2*RATE);t=np.arange(n)/RATE
    noise=rng.normal(size=n)
    high=noise-np.convolve(noise,np.ones(31)/31,mode='same')
    clap=high*np.exp(-t*28)*(1+.35*np.sin(2*np.pi*35*t))
    add(at,clap,.06)

# Small celebratory rises on story transitions.
for at in [3.5,8.5,14,22,26]:
    n=int(.9*RATE);t=np.arange(n)/RATE
    sweep=np.sin(2*np.pi*(380*t+430*t*t))
    env=np.sin(np.pi*t/.9)**2
    add(at,sweep*env,.055)

# Sparkling resolving chord behind the final lockup.
tones(26,[261.63,329.63,392.0,523.25,659.26],3.85,.19,.06,1.1)
fade=np.minimum(1,np.arange(COUNT)/(RATE*.3))*np.minimum(1,(COUNT-np.arange(COUNT))/(RATE*.95))
mix*=fade
mix=np.tanh(mix*1.3)
mix*=.78/max(.78,float(np.max(np.abs(mix))))
out=Path('assets/sound.wav')
with wave.open(str(out),'wb') as handle:
    handle.setnchannels(1)
    handle.setsampwidth(2)
    handle.setframerate(RATE)
    handle.writeframes(np.asarray(mix*32767,dtype=np.int16).tobytes())
print(out)
