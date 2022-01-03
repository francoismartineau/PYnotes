from dataclasses import dataclass
import threading, time
import rtmidi
import rtmidi.midiutil
# pip install python-rtmidi

# 7e, 9e (avec velocité de chord)

# inversions:  hum...

# melodies: note entrante pour timing
#           selon timing et accord, choix de note
#           gammes pentatoniques, quelles?

# repetitions: modulo sur time

@dataclass
class FL_TO_PY:
    """
    Modes:
        chan 1      c2 major        ---
                    d2 lydian       -
                    e2 mixolydian
                    f2 dorian       -
                    g2 minor        ---
                    a2 phrygian     -
                    b2 locrian
    """
    MODES = {"chan": 1, 24: "Major", 26: "Lydian", 28: "Mixolydian", 29: "Dorian", 31: "Minor", 33: "Phrygian", 35:"Locrian"}

    """
    Chords:
        chan 1      c3 ... b3
        Vel 0: set chord len 1 2 3 4 5 6 7
        Vel X: set chord number I ... vii`
    """
    CHORDS = {"chan": 1}
    CHORDS["chord_num"] = {36: 0, 38: 1, 40: 2, 41: 3, 43: 4, 45: 5, 47: 6}
    CHORDS["chord_len"] = {36: 1, 38: 2, 40: 3, 41: 4, 43: 5, 45: 6, 47: 7}

    """
    Tonic: any note on chan 2
    """
    TONIC = {"chan": 2}

    """
    Metronome:
        chan 3              tick: 13/c1#         1st tick: 12/c1   
    """
    METRONOME = {"chan": 3, "tick_note": 13, "first_tick_note": 12}
    
    FEEDBACK = {"chans": [10, 11, 12]}
    """
    FEEDBACK_SETTINGS:
        Vel: 0, disable mapping for chan associated with note
        Vel: 127, enable mapping for chan associated with note
    """
    FEEDBACK_SETTINGS = {"chan": 1, "notes": {}, "vels": {}}
    FEEDBACK_SETTINGS["notes"][12] = {"setting": "map_to_chord", "chan": FEEDBACK["chans"][0]}   # C1
    FEEDBACK_SETTINGS["notes"][13] = {"setting": "map_to_scale", "chan": FEEDBACK["chans"][0]}   # C1#
    FEEDBACK_SETTINGS["notes"][14] = {"setting": "map_to_chord", "chan": FEEDBACK["chans"][1]}   # D1
    FEEDBACK_SETTINGS["notes"][15] = {"setting": "map_to_scale", "chan": FEEDBACK["chans"][1]}   # D1#
    FEEDBACK_SETTINGS["notes"][16] = {"setting": "map_to_chord", "chan": FEEDBACK["chans"][2]}   # E1
    FEEDBACK_SETTINGS["notes"][17] = {"setting": "map_to_scale", "chan": FEEDBACK["chans"][2]}   # E1#
    
@dataclass
class PY_TO_FL:
    MODE = {"all": 1, "notes": 2, "cc": 3, "none": 4}

@dataclass
class AHK:
    CHAN = 15


# ------------------------------------------------------------------------------
class Midi:
    def __init__(self):
        self.midi_inputs = {}
        self.midi_outputs = {}

        self.down_notes = []
        self.down_notes_threads = []
        self.thread_lock = threading.Lock()
        
        self.print_incoming_messages = False
        self.print_incoming_note_ons = False
        self.print_outcoming_messages = False
        self.print_exec_funcs = True
        
        self.add_midi_input('FL_TO_PY')
        self.add_midi_input('AHK_TO_PY')
        self.add_midi_output('PY_TO_FL')
        self.PY_TO_FL_OUTPUTE_MODE = PY_TO_FL.MODE["all"]
        self.add_midi_output('PY_TO_AHK')


    def add_midi_input(self, name):
        midi_input = rtmidi.MidiIn()
        names = midi_input.get_ports()
        for i, val in enumerate(names):
            if name in val:
                id = i
                break
        if id == None:
            print("Could not open input port {}".format(name))
        else:
            midi_input.open_port(id)  
            midi_input.set_callback(self.on_midi_input)
            self.midi_inputs[name] = midi_input

    def add_midi_output(self, name):
        self.midi_outputs[name] = rtmidi.MidiOut()
        names = self.midi_outputs[name].get_ports()
        for i, val in enumerate(names):
            if name in val:
                id = i
                break
        if id == None:
            print("Could not open output port {}".format(name))
        else:
            self.midi_outputs[name].open_port(id)

    def set_mood(self, mood):
        self.mood = mood

    def set_feedback(self, feedback):
        self.feedback = feedback
    # ----



    # -- INPUT --------------------------------------------------------------------
    def on_midi_input(self, data, _):
        [status, data1, data2], _ = data
        chan = Midi.get_chan(status)
        if Midi.is_cc(status):
            self.on_cc(data1, data2, chan)
        elif Midi.is_note_on(status):
            self.on_note_on(data1, data2, chan)
        elif Midi.is_note_off(status):
            self.on_note_off(data1, chan)

    def on_note_on(self, note, vel, chan):
        if self.print_incoming_messages or self.print_incoming_note_ons:
            print("on:   chan: {}  n: {}   v:{}".format(chan, note, vel))        
        if Midi.is_mode_setter(note, chan):
            self.set_mode(note)
        elif Midi.is_chord_setter(note, chan):
            if (vel > 0):
                self.set_chord(note)
            else:
                self.set_chord_len(note)
        elif Midi.is_tonic_setter(chan):
            self.set_tonic(note)
        elif Midi.is_feedback(chan):
            self.feedback.on_note_on(note, vel, chan)
        elif Midi. is_feedback_setting(note, chan):
            self.apply_feedback_setting(note, vel)
            pass
          
    def on_note_off(self, note, chan):
        if self.print_incoming_messages:
            print("off:   chan: {}   n:{}".format(chan, note))        
        if Midi.is_tick(note, chan):
            self.mood.tick()  
        elif Midi.is_first_tick(note, chan):
            self.mood.first_tick()
        elif Midi.is_feedback(chan):
            self.feedback.on_note_off(note, chan)
            pass

    def on_cc(self, cc, val, chan):
        if chan == AHK.CHAN:
            self.on_ahk_func(cc, val)
        if self.print_incoming_messages:
            print("chan: {}   cc: {}   val:{}".format(chan, cc, val))

    def on_ahk_func(self, cc, val):
        funcs = {
            30: self.set_PY_TO_FL_OUTPUT_MODE,
        }
        if (cc in funcs):
            funcs[cc](val)
    # -----------------------------------------------------------------------------

    # -- funcs -------------------------------
    @staticmethod
    def is_tick(note, chan):
        return chan == FL_TO_PY.METRONOME["chan"] and note == FL_TO_PY.METRONOME["tick_note"]
    
    @staticmethod
    def is_first_tick(note, chan):
        return chan == FL_TO_PY.METRONOME["chan"] and note == FL_TO_PY.METRONOME["first_tick_note"]

    @staticmethod
    def is_mode_setter(note, chan):
        return chan == FL_TO_PY.MODES["chan"] and note in FL_TO_PY.MODES.keys()
    
    def set_mode(self, note):
        self.mood.set_mode(FL_TO_PY.MODES[note])

    @staticmethod
    def is_chord_setter(note, chan):
        return chan == FL_TO_PY.CHORDS["chan"] and note in FL_TO_PY.CHORDS["chord_num"]

    def set_chord(self, note):
        self.mood.set_chord(FL_TO_PY.CHORDS["chord_num"][note])

    def set_chord_len(self, note):
        self.mood.set_chord_len(FL_TO_PY.CHORDS["chord_len"][note])

    @staticmethod
    def is_tonic_setter(chan):
        return chan == FL_TO_PY.TONIC["chan"]

    def set_tonic(self, note):
        self.mood.set_tonic(note)

    @staticmethod
    def is_feedback(chan):
        return chan in FL_TO_PY.FEEDBACK["chans"]

    @staticmethod
    def is_feedback_setting(note, chan):
        return chan == FL_TO_PY.FEEDBACK_SETTINGS["chan"] and note in FL_TO_PY.FEEDBACK_SETTINGS["notes"].keys()

    def apply_feedback_setting(self, note, vel):
        chan = FL_TO_PY.FEEDBACK_SETTINGS["notes"][note]["chan"]
        if (vel == 0):
            self.feedback.disable_map(chan)
            return
        if (vel == 127):
            self.feedback.enable_map(chan)
        setting = FL_TO_PY.FEEDBACK_SETTINGS["notes"][note]["setting"]
        if setting.startswith("map_to"):
            self.feedback.set_map_to(chan, setting)
        
    # ---
    @staticmethod
    def is_cc(status):
        return status>>4 == 0xB
    
    @staticmethod
    def is_note_on(status):
        return status>>4 == 0x9

    @staticmethod
    def is_note_off(status):
        return status>>4 == 0x8

    @staticmethod
    def get_chan(status):
        return status - (status>>4<<4) + 1

    def set_PY_TO_FL_OUTPUT_MODE(self, val):
        self.PY_TO_FL_OUTPUTE_MODE = val
        print("output mode: ", val)
        return          
    # ----------------------------------------

    # -- OUTPUT ---------------------------------------------------------------------------

    # -- AHK ---------------
    def display_mode(self, mode_index):
        self.call_ahk_func("displayMode", mode_index+1)
        return

    def display_chord(self, chord_index):
        self.call_ahk_func("displayChord", chord_index+1)
        return      

    def display_tonic(self, tonic):
        self.call_ahk_func("displayTonic", tonic)
        return    

    def display_chan_map_to(self, chan, map_to_chord):
        self.call_ahk_func("displayChanMapTo", (chan<<1)+map_to_chord)

    def display_chan_map_enable(self, chan, enable):
        self.call_ahk_func("displayChanMapEnable", (chan<<1)+enable)

    def display_chord_len(self, len):
        self.call_ahk_func("displayChordLen", len)

    def call_ahk_func(self, func, val):
        status = Midi.get_cc_status(AHK.CHAN)
        cc = {
            "displayMode": 30,
            "displayChord": 31,
            "displayTonic": 32,
            "displayChanMapTo": 33,
            "displayChanMapEnable": 34,
            "displayChordLen": 35,
        }[func]
        self.__send_midi_msg("PY_TO_AHK", [status, cc, val])
    # ----

    # -- FL ---------------
    def cc_out(self, cc, val, chan):
        if self.PY_TO_FL_OUTPUTE_MODE not in [PY_TO_FL.MODE["all"], PY_TO_FL.MODE["cc"]]:
            return        
        status = 0xB<<4 + chan-1
        msg = [status, cc, val]
        self.__send_midi_msg("PY_TO_FL", msg)
        if self.print_outcoming_messages:
            print("chan: {}   cc:{}".format(chan, cc))
    
    def make_note(self, note, vel, chan, dur):
        if self.PY_TO_FL_OUTPUTE_MODE not in [PY_TO_FL.MODE["all"], PY_TO_FL.MODE["notes"]]:
            return
        self.send_note_on(note, vel, chan)
        self.__make_note_start_thread(note, chan, dur)        
    
    def __make_note_start_thread(self, note, chan, dur):
        self.__cleanup_threads()
        delay_before_off = dur
        f = Midi.make_note_note_off
        args = (self, note, chan, delay_before_off)
        t = threading.Thread(target=f, args=args)
        self.down_notes_threads.append(t)
        t.start()

    def send_note_on(self, note, vel, chan):
        if self.PY_TO_FL_OUTPUTE_MODE not in [PY_TO_FL.MODE["all"], PY_TO_FL.MODE["notes"]]:
            return         
        if ((note, chan) in self.down_notes):
            self.send_note_off(note, chan)
        self.down_notes.append((note, chan))
        status = (0x9<<4) + chan-1
        msg = [status, note, vel]
        self.__send_midi_msg("PY_TO_FL", msg)
        if self.print_outcoming_messages:
            print("on:   chan: {}  n: {}   v:{}".format(chan, note, vel))

    def make_note_note_off(self, note, chan, delay):
        if (delay):
            self.thread_lock.acquire()
            note_is_down = (note, chan) in self.down_notes
            self.thread_lock.release()
            if (note_is_down):
                time.sleep(delay)
        self.thread_lock.acquire()
        self.send_note_off(note, chan)
        self.thread_lock.release()
    
    def send_note_off(self, note, chan):
        if self.PY_TO_FL_OUTPUTE_MODE not in [PY_TO_FL.MODE["all"], PY_TO_FL.MODE["notes"]]:
            return                
        if ((note, chan) in self.down_notes):
            status = (0x8<<4) + chan-1
            msg = [status, note, 0]
            self.__send_midi_msg("PY_TO_FL", msg)
            self.down_notes.remove((note, chan))
            if self.print_outcoming_messages:
                print("off:   chan: {}   n:{}".format(chan, note))

    def __send_midi_msg(self, device_name, msg):
        self.midi_outputs[device_name].send_message(msg)

    @staticmethod
    def get_cc_status(chan):
        return (0xb<<4) + chan-1
    # ----------------------------------

    # -- threads ----
    def get_threads(self):
        return self.down_notes_threads + []

    def __cleanup_threads(self):
        self.down_notes_threads = list(filter(lambda t: t.is_alive(), self.down_notes_threads))
    # ----