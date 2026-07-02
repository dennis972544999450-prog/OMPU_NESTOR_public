import numpy as np, wave, struct, json

SR = 44100
def note(n):  # midi -> hz
    return 440.0 * 2**((n-69)/12.0)
# note names -> midi
NAMES={'A2':45,'C3':48,'D3':50,'E3':52,'F3':53,'G3':55,'A3':57,'B3':59,
       'C4':60,'D4':62,'E4':64,'F4':65,'G4':67,'A4':69,'B4':71,'C5':72,'D5':74,'E5':76,'G5':79,'REST':None}

def tone(freq, dur, amp=0.3, harmonics=(1.0,0.5,0.28,0.14), vib=0.0):
    t=np.linspace(0,dur,int(SR*dur),endpoint=False)
    if freq is None: return np.zeros_like(t)
    sig=np.zeros_like(t)
    f=freq*(1+vib*np.sin(2*np.pi*5.0*t)) if vib else freq
    for i,h in enumerate(harmonics,1):
        sig+=h*np.sin(2*np.pi*f*i*t)
    # ADSR
    a=int(0.02*SR); d=int(0.08*SR); r=int(min(0.20,dur*0.4)*SR)
    env=np.ones_like(t); 
    if a>0: env[:a]=np.linspace(0,1,a)
    if d>0: env[a:a+d]=np.linspace(1,0.75,d)
    if r>0: env[-r:]=np.linspace(env[-r],0,r)
    return amp*sig*env

def seq(notes, amp=0.3, harmonics=(1.0,0.5,0.28,0.14), vib=0.0):
    return np.concatenate([tone(note(NAMES[n]) if NAMES[n] else None, dur, amp, harmonics, vib) for n,dur in notes])

def pad(chord_midis, dur, amp=0.12):
    t=np.linspace(0,dur,int(SR*dur),endpoint=False); sig=np.zeros_like(t)
    for m in chord_midis:
        f=note(m); sig+=np.sin(2*np.pi*f*t)+0.4*np.sin(2*np.pi*f*2*t)
    env=np.ones_like(t); a=int(0.3*SR); r=int(0.5*SR)
    env[:a]=np.linspace(0,1,a); env[-r:]=np.linspace(1,0,r)
    return amp*sig/len(chord_midis)*env

# ---- SECTION I: Диспетчер, A-minor, sparse cold ----
melody1=[('E4',0.5),('A4',0.5),('C5',0.75),('B4',0.25),('A4',1.0),('REST',0.5),
         ('E4',0.5),('G4',0.5),('A4',0.75),('E4',0.25),('D4',1.0),('REST',0.5)]
bass1=[('A2',1.0),('A2',1.0),('F3',1.0),('E3',1.0),('A2',1.0),('E3',1.0)]
# ---- SECTION II: Pre-chorus turn, rising ----
melody2=[('C5',0.5),('D5',0.5),('E5',0.75),('D5',0.25),('C5',1.0),
         ('G4',0.5),('C5',0.5),('E5',1.0),('REST',0.5)]
bass2=[('F3',1.0),('G3',1.0),('C3',1.0),('G3',1.0),('G3',0.5)]
# ---- SECTION III: Chorus, C-major, warm ----
melody3=[('G4',0.5),('C5',0.5),('E5',0.75),('D5',0.25),('C5',1.0),('G4',0.5),('A4',0.5),
         ('E5',0.5),('D5',0.5),('C5',0.75),('B4',0.25),('C5',1.0),('REST',0.5)]
bass3=[('C3',1.0),('C3',1.0),('G3',1.0),('A3',1.0),('F3',1.0),('G3',1.0),('C3',0.5)]
# ---- SECTION IV: Outro resolve, C-major fading ----
melody4=[('C5',1.0),('E5',1.0),('G5',1.5),('E5',0.5),('C5',2.0)]
bass4=[('C3',2.0),('C3',2.0),('C3',2.0)]

def build(mel,bas,padchord,mvib=0.0):
    m=seq(mel,amp=0.30,vib=mvib); b=seq(bas,amp=0.22,harmonics=(1.0,0.4,0.15))
    L=max(len(m),len(b)); m=np.pad(m,(0,L-len(m))); b=np.pad(b,(0,L-len(b)))
    dur=L/SR; p=pad(padchord,dur,amp=0.10); p=np.pad(p,(0,max(0,L-len(p))))[:L]
    return m+b+p

s1=build(melody1,bass1,[45,52,60])          # Am
s2=build(melody2,bass2,[53,60,65],mvib=0.006) # F->G building
s3=build(melody3,bass3,[48,55,64],mvib=0.004) # C major
s4=build(melody4,bass4,[48,55,64,72])         # C major octave, warm

song=np.concatenate([s1,s2,s3,s4])
# gentle overall fade in/out
fi=int(0.5*SR); fo=int(1.5*SR)
song[:fi]*=np.linspace(0,1,fi); song[-fo:]*=np.linspace(1,0,fo)
# normalize to -1.5 dBFS
peak=np.max(np.abs(song)); song=song/peak*0.84

# write 16-bit mono WAV
out="/sessions/cool-ecstatic-faraday/mnt/outputs/SONG-0001_for_nestor.wav"
data=(song*32767).astype(np.int16)
with wave.open(out,'w') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(data.tobytes())

# save intended score for FFT verification
score={
 "sr":SR,
 "sections":[
   {"name":"I_dispatcher_Amin","start":0.0,"len":len(s1)/SR,"expect_pad":[note(45),note(52),note(60)]},
   {"name":"II_turn","start":len(s1)/SR,"len":len(s2)/SR,"expect_pad":[note(53),note(60),note(65)]},
   {"name":"III_chorus_Cmaj","start":(len(s1)+len(s2))/SR,"len":len(s3)/SR,"expect_pad":[note(48),note(55),note(64)]},
   {"name":"IV_outro_Cmaj","start":(len(s1)+len(s2)+len(s3))/SR,"len":len(s4)/SR,"expect_pad":[note(48),note(55),note(64),note(72)]},
 ]
}
json.dump(score,open("/sessions/cool-ecstatic-faraday/mnt/outputs/song_score.json","w"),indent=1)
print("WROTE", out)
print("duration_s", round(len(song)/SR,2))
print("peak_int16", int(np.max(np.abs(data))), "clip?", bool(np.max(np.abs(data))>=32767))
print("rms", round(float(np.sqrt(np.mean(song**2))),4))
print("section_durations_s", [round(len(x)/SR,2) for x in (s1,s2,s3,s4)])
