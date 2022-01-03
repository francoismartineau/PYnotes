import random

class Mood:
    french_notes = ["Do", "Do#", "Ré", "Ré#", "Mi", "Fa", "Fa#", "Sol", "Sol#", "La", "La#", "Si"]
    english_notes = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    modes = ["Major", "Dorian", "Phrygian", "Lydian", "Mixolydian", "Minor", "Locrian"]
    major_scale = [2, 2, 1, 2, 2, 2, 1]
    c5 = 60

    def __init__(self, midi):
        self.midi = midi

        self.print_set_notes = False
        self.print_notes = False
        self.print_ticks = False

        self.time = 0

        self.tonic = Mood.c5
        self.set_mode("Major")
        self.chord_len = 4
        self.set_chord(0)



    # -- get/set notes -----------------------------
    def set_chord(self, chord):
        self.chord = chord
        if self.midi is not None: self.midi.display_chord(self.chord)
        self.chord_notes = self.get_current_chord_notes()
        if self.print_set_notes:
            print("-- Chord:", chord+1)

    def set_mode(self, mode):
        self.mode = Mood.modes.index(mode)
        if self.midi is not None: self.midi.display_mode(self.mode)
        self.mode_gaps = self.get_current_mode_gaps()
        self.mode_notes = self.get_current_mode_notes()
        if self.print_set_notes:
            print("---- Mode:", mode)

    def set_tonic(self, note):
        self.tonic = note
        if self.midi is not None: self.midi.display_tonic(self.tonic)
        if self.print_set_notes:
            print("-- Tonic:", note)

    def set_chord_len(self, len):
        self.chord_len = len
        self.midi.display_chord_len(self.chord_len)

    def get_current_mode_gaps(self):
        return Mood.major_scale[self.mode:] + Mood.major_scale[:self.mode]
    
    def get_current_mode_notes(self):
        notes = [sum(self.mode_gaps[:i]) for i in range(len(self.mode_gaps))]
        return notes
    
    def get_major_scale_notes(self):
        notes = [sum(self.major_scale[:i]) for i in range(len(self.major_scale))]
        return notes

    def get_major_scale_tonic_chord_notes(self):
        notes = []
        major_scale_notes = self.get_major_scale_notes()
        for scale_degree in [i*2 for i in range(self.chord_len)]:
            n = major_scale_notes[scale_degree]
            notes.append(n)
        return notes
    
    def get_closest_degree_in_c_major_scale(self, note):
        note_offset_from_c = Mood.get_note_offset_in_oct(note)
        major_scale_notes = self.get_major_scale_notes()
        closest_degree = min(range(len(major_scale_notes)), key = lambda i: abs(major_scale_notes[i]-note_offset_from_c))
        st_delta = major_scale_notes[closest_degree]-note_offset_from_c
        return closest_degree, st_delta
    
    def get_closest_degree_in_c_major_tonic_chord(self, note):
        note_offset_from_c = Mood.get_note_offset_in_oct(note)
        major_scale_tonic_chord_notes = self.get_major_scale_tonic_chord_notes()
        major_scale_tonic_chord_notes += [12]                                       # so higher notes can be attracted by tonic
        closest_degree = min(range(len(major_scale_tonic_chord_notes)), key = lambda i: abs(major_scale_tonic_chord_notes[i]-note_offset_from_c))
        st_delta = major_scale_tonic_chord_notes[closest_degree]-note_offset_from_c
        closest_degree = closest_degree % (len(major_scale_tonic_chord_notes)-1)    # so if higher note was attracted by tonic, res = 0 (meaning tonic)
        return closest_degree, st_delta

    def get_oct_relative_to_c5(self, note):
        oct = (note-Mood.c5)//12
        return oct
    
    
    def get_current_chord_notes(self):
        curr_chord = []
        for scale_degree in [i*2 for i in range(self.chord_len)]:   # 0, 2, 4, 6, 8, 10, 12
            scale_degree += self.chord                              # si nieme accord, n+0, n+2, n+4, etc
            scale_degree %= 7                                       # wrap dans octave
            #n_oct_up = scale_degree // len(self.mode_gaps)
            #scale_degree %= 12
            note = sum(self.mode_gaps[:scale_degree]) 
            #note += n_oct_up*12
            curr_chord.append(note)

        if self.print_notes:
            print(curr_chord)
        return curr_chord

    # -----------------------------------------
    def map_c_major_note(self, note, to_chord):         
        ### Force degrees of scale/chords OR let free to escape, but white notes are the scale
        ### couleurs diffs pour ça
        # map 1 to 7
        get_degree = {
            True: self.get_closest_degree_in_c_major_tonic_chord,
            False: self.get_closest_degree_in_c_major_scale
        }[to_chord]
        degree, st_delta = get_degree(note)
        #print(Mood.midi_to_readable_note(note, True))
        notes = {
            True: self.chord_notes,
            False: self.mode_notes,
        }[to_chord]


        oct = self.get_oct_relative_to_c5(note) ###### Oct devrait, oui être déterminé par note initiale
                                                ###### mais aussi par le wrap de degree
        
        tonic_offset = Mood.get_note_offset_in_oct(self.tonic) 
        note = notes[degree] + Mood.c5 + oct*12 + tonic_offset
        return note

    def map_note(self, note, to_chord):
        """
        to_chord: if False, map to scale
        This function maps an incoming note to a close value in a chord or scale.
        It checks up, then down, then up+1, down-1, etc. Until it finds a note from the cluster.
        The octave component of every notes is removed prior to verifications and put back at the end.
        """
        # SI PROCHE TONIQUE, y aller plus facilement?
        note_offs = Mood.get_note_offset_in_oct(note)
        
        base_notes = {True: self.chord_notes, False: self.mode_notes}[to_chord]
        tonic_offs = Mood.get_note_offset_in_oct(self.tonic)
        good_note_offs = list(map(lambda n: Mood.get_note_offset_in_oct(n+tonic_offs), base_notes))

        if (note_offs not in good_note_offs):
            delta_up = 0
            delta_down = 0
            for i in range(11):         
                if (i%2 == 0):
                    delta_up += 1
                    potential_note_offs = Mood.get_note_offset_in_oct(delta_up + note_offs)
                else:
                    delta_down -= 1
                    potential_note_offs = Mood.get_note_offset_in_oct(delta_down + note_offs)
                if potential_note_offs in good_note_offs:
                    note_offs = potential_note_offs
                    break
                if i == 10:
                    print("map_note() -> couldn't map")
            note_oct = Mood.get_note_oct(note)
            note = note_offs + note_oct*12
        return note

    @staticmethod
    def get_note_offset_in_oct(note):
        return note % 12
    @staticmethod
    def get_note_oct(note):
        return note // 12

    @staticmethod
    def midi_to_readable_note(note, french=False):
        note_offs = Mood.get_note_offset_in_oct(note)
        note_oct = Mood.get_note_oct(note)
        readable_note_list = {True: Mood.french_notes, False: Mood.english_notes}[french]
        readable_note = readable_note_list[note_offs] + str(note_oct)
        return readable_note      
    # -----

    # -- time ---------------------------------
    #### Mettre ça dans seq
    def first_tick(self):
        self.time = 0
        self.eval_current_time()
        if self.print_ticks:
            print(self.time)
    
    def tick(self):
        self.time += 1
        self.eval_current_time()
        if self.print_ticks:
            print(self.time)

    def eval_current_time(self):
        if (self.time == 0):
            self.gen_chord()
    #def play_current(self):
    #    if len(self.seq) <= self.time:
    #        return

    #    for data in self.seq[self.time]:
    #        print(data)
    # -----

    # -- gen ---------------------------------
    def gen_chord(self):
        #random.seed(self.time)
        for n in self.chord_notes:
            n += self.tonic
            if self.midi is not None: self.midi.make_note(n, 100, 1, .5)

    # -----

def f(note):
    oct = (note-60)//12
    return oct

if __name__ == "__main__":
    note = 40
    print(f(note))
    exit()
    m = Mood(None)
    note = Mood.french_notes.index("Si") + 12*3
    note, delta = m.get_closest_degree_in_c_major_tonic_chord(note)
    print(note, delta)
    #print(Mood.midi_to_readable_note(note, True))

    pass