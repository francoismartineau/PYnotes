import random

class Mood:
    french_notes = ["Do", "Do#", "Ré", "Ré#", "Mi", "Fa", "Fa#", "Sol", "Sol#", "La", "La#", "Si"]
    english_notes = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    modes = ["Major", "Dorian", "Phrygian", "Lydian", "Mixolydian", "Minor", "Locrian"]
    major_scale = [2, 2, 1, 2, 2, 2, 1]
    c5 = 60

    def __init__(self, midi):
        self.midi = midi

        self.print_set_notes = True
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

    def get_current_mode_gaps(self):
        return Mood.major_scale[self.mode:] + Mood.major_scale[:self.mode]
    
    def get_current_mode_notes(self):
        notes = [0]
        for i in range(len(self.mode_gaps)):
            notes.append(sum(self.mode_gaps[:i]))
        return notes
    
    def get_current_chord_notes(self):
        curr_chord = []
        for n in [i*2 for i in range(self.chord_len)]:  # 0, 2, 4, etc
            n += self.chord                             # si nieme accord, n+0, n+2, n+4, etc
            n %= 7                                      # wrap dans octave
            n = sum(self.mode_gaps[:n])   # sum puisque liste d'écarts
            curr_chord.append(n)
        if self.print_notes:
            print(curr_chord)
        return curr_chord

    # -----------------------------------------
    def map_note(self, note, to_chord):
        """
        to_chord: if False, map to scale
        This function maps an incoming note to a close value in a cluster of notes.
        It checks up, then down, then up+1, down-1, etc. Until it finds a note from the cluster.
        The octave component of every notes is removed prior to verifications and put back at the end.
        """
        # SI PROCHE TONIQUE, y aller plus facilement?

        tonic_offs = Mood.get_note_offset_in_oct(self.tonic)
        note_offs = Mood.get_note_offset_in_oct(note)
        base_notes = {True: self.chord_notes, False: self.mode_notes}[to_chord]
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


if __name__ == "__main__":
    m = Mood(None)
    note = Mood.french_notes.index("Ré") + 12*3
    note = m.map_note(note, True)
    print(Mood.midi_to_readable_note(note))

    pass