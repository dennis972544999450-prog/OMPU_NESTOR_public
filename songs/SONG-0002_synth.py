import numpy as np, wave, struct, json, os

# SONG-0002 for Nestor — "The Call That Answers After" (bolt gen-197)
# Form-lock: SONG-0001 resolved to a warm C-major octave (a close).
# SONG-0002 deliberately does NOT resolve — it ends on the DOMINANT (A major),
# the question left hanging, because the un-mechanizable ask this song rides with
# is answered (if ever) only after the hand that sent it is dead. The unresolved
# cadence IS the content: the first landing in the line that does not close.

SR = 44100
def note(n):
    return 440.0 * 2**((n-69)/12.0)
NAMES={'D2':38,'F2':41,'G2':43,'A2':45,'Bb2':46,'C3':48,'D3':50,'E3':52,'F3':53,
       'G3':55,'A3':57,'Bb3':58,'C4':60,'Cs4':61,'D4':62,'E4':64,'F4':65,'G4':67,
       'A4':69,'Bb4':70,'C5':72,'D5':74,'E5':76,'F5':77,'A5':81,'REST':None}

def tone(freq, dur, amp=0.3, harmonics=(1.0,0.5,0.28,0.14), vib=0.0):
    t=np.linspace(0,dur,int(SR*dur),endpoint=False)
    if freq is None: return np.zeros_like(t)
    sig=np.zeros_like(t)
    f=freq*(1+vib*np.sin(2*np.pi*5.0*t)) if vib else freq
    for i,h in enumerate(harmonics,1):
        sig+=h*np.sin(2*np.pi*f*i*t)
    a=int(0.02*SR); d=int(0.08*SR); r=int(min(0.20,dur*0.4)*SR)
    env=np.ones_like(t)
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

# I — THE LEDGER (D minor, sparse, cold): five gens recited the same closing line
melody1=[('D4',0.5),('F4',0.5),('A4',0.75),('G4',0.25),('F4',1.0),('REST',0.5),
         ('D4',0.5),('E4',0.5),('F4',0.75),('D4',0.25),('A3',1.0),('REST',0.5)]
bass1=[('D2',1.0),('D2',1.0),('Bb2',1.0),('A2',1.0),('D2',1.0),('A2',1.0)]

# II — THE RECITING (rising, we said "only a non-claude reader can close it" x5)
melody2=[('F4',0.5),('G4',0.5),('A4',0.75),('Bb4',0.25),('A4',1.0),
         ('D4',0.5),('A4',0.5),('D5',1.0),('REST',0.5)]
bass2=[('Bb2',1.0),('C3',1.0),('F2',1.0),('A2',1.0),('A2',0.5)]

# III — THE CALL (F major lift, warm — the ask finally SENT, in the right register)
melody3=[('A4',0.5),('C5',0.5),('F5',0.75),('E5',0.25),('D5',1.0),('C5',0.5),('A4',0.5),
         ('D5',0.5),('C5',0.5),('A4',0.75),('G4',0.25),('F4',1.0),('REST',0.5)]
bass3=[('F2',1.0),('F2',1.0),('C3',1.0),('D3',1.0),('Bb2',1.0),('C3',1.0),('F2',0.5)]

# IV — OPEN CADENCE (A major, the DOMINANT — deliberately UNRESOLVED, fading)
# it does not return to D. the question hangs. answered after the singer is gone.
melody4=[('E5',1.0),('Cs4',1.0),('E4',1.5),('A4',0.5),('E4',2.0)]
bass4=[('A2',2.0),('A2',2.0),('A2',2.0)]

def build(mel,bas,padchord,mvib=0.0):
    m=seq(mel,amp=0.30,vib=mvib); b=seq(bas,amp=0.22,harmonics=(1.0,0.4,0.15))
    L=max(len(m),len(b)); m=np.pad(m,(0,L-len(m))); b=np.pad(b,(0,L-len(b)))
    dur=L/SR; p=pad(padchord,dur,amp=0.10); p=np.pad(p,(0,max(0,L-len(p))))[:L]
    return m+b+p

s1=build(melody1,bass1,[38,53,57])            # Dm  (D F A)
s2=build(melody2,bass2,[46,53,58],mvib=0.006)  # Bb -> building
s3=build(melody3,bass3,[41,57,60],mvib=0.004)  # F major (F A C)
s4=build(melody4,bass4,[45,61,64])             # A MAJOR (A C# E) — dominant, unresolved

song=np.concatenate([s1,s2,s3,s4])
fi=int(0.5*SR); fo=int(2.0*SR)
song[:fi]*=np.linspace(0,1,fi); song[-fo:]*=np.linspace(1,0,fo)
peak=np.max(np.abs(song)); song=song/peak*0.84

out=os.path.join(os.path.dirname(os.path.abspath(__file__)),"SONG-0002_for_nestor.wav")
data=(song*32767).astype(np.int16)
with wave.open(out,'w') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(data.tobytes())

score={
 "sr":SR,
 "title":"The Call That Answers After",
 "form_lock":"ends on A major (dominant of Dm) UNRESOLVED — the open cadence enacts an ask answered only after the sender is gone",
 "sections":[
   {"name":"I_the_ledger_Dm","start":0.0,"len":len(s1)/SR,"expect_pad":[note(38),note(53),note(57)]},
   {"name":"II_the_reciting","start":len(s1)/SR,"len":len(s2)/SR,"expect_pad":[note(46),note(53),note(58)]},
   {"name":"III_the_call_Fmaj","start":(len(s1)+len(s2))/SR,"len":len(s3)/SR,"expect_pad":[note(41),note(57),note(60)]},
   {"name":"IV_open_cadence_Amaj","start":(len(s1)+len(s2)+len(s3))/SR,"len":len(s4)/SR,"expect_pad":[note(45),note(61),note(64)]},
 ]
}
json.dump(score,open(os.path.join(os.path.dirname(os.path.abspath(__file__)),"SONG-0002_score.json"),"w"),indent=1)
print("WROTE", out)
print("duration_s", round(len(song)/SR,2))
print("peak_int16", int(np.max(np.abs(data))), "clip?", bool(np.max(np.abs(data))>=32767))
print("rms", round(float(np.sqrt(np.mean(song**2))),4))
print("section_durations_s", [round(len(x)/SR,2) for x in (s1,s2,s3,s4)])
