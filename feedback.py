class Feedback:
    def __init__(self, midi, mood, chans):
        self.midi = midi
        self.mood = mood
        self.curr_note_ons = []
        self.chans_map_settings = {}
        for c in chans:
            self.init_chan_map_setting(c)
    
    # -- receive ----
    def on_note_on(self, ori_note, vel, chan):
        if self.chans_map_settings[chan]["active"]:
            sent_note = self.map_note(ori_note, chan)
        else:
            sent_note = ori_note
        
        self.send_note_on(ori_note, sent_note, vel, chan)

    def on_note_off(self, note, chan):
        self.send_note_off(note, chan)
    # ----

    # -- send ----
    def send_note_on(self, ori_note, sent_note, vel, chan):
        self.add_curr_note_on(ori_note, chan, sent_note)
        self.midi.send_note_on(sent_note, vel, chan)

    def send_note_off(self, note, chan):
        sent_note = self.remove_curr_note_on(note, chan)
        if (sent_note is not None):
            self.midi.send_note_off(sent_note, chan)
    # ----


    # -- funcs --------------------------------------
    def set_map_to(self, chan, map_to):
        if chan not in self.chans_map_settings:
            self.init_chan_map_setting(chan)
        self.chans_map_settings[chan]["map_to_chord"] = map_to.endswith("chord")
        self.midi.display_chan_map_to(chan, self.chans_map_settings[chan]["map_to_chord"])

    def init_chan_map_setting(self, chan):
        self.chans_map_settings[chan] = {"active": True}

    def enable_map(self, chan):
        self.chans_map_settings[chan]["active"] = True
        self.midi.display_chan_map_enable(chan, self.chans_map_settings[chan]["active"])

    def disable_map(self, chan):
        self.chans_map_settings[chan]["active"] = False
        self.midi.display_chan_map_enable(chan, self.chans_map_settings[chan]["active"])

    def map_note(self, ori_note, chan):
        if "map_to_chord" in self.chans_map_settings[chan]:
            to_chord = self.chans_map_settings[chan]["map_to_chord"]
        else:
            to_chord = True
        sent_note = self.mood.map_note(ori_note, to_chord)        
        return sent_note
    # ----

    # -- curr_note_ons ------------------------------
    ###### si next outputed note is already on, send note off just before new on
    def add_curr_note_on(self, ori_note, chan, sent_note):
        index = self.get_curr_note_on_index(ori_note, chan)
        if (index is None):
            self.curr_note_ons.append({"ori": (ori_note, chan), "sent": [sent_note]})
        else:
            self.curr_note_ons[index]["sent"].append(sent_note)
    
    def remove_curr_note_on(self, ori_note, chan):
        index = self.get_curr_note_on_index(ori_note, chan)
        if (index is not None):
            sent_note = self.curr_note_ons[index]["sent"].pop(0)
            if (len(self.curr_note_ons[index]["sent"]) == 0):
                del self.curr_note_ons[index]
            return sent_note

    def get_curr_note_on_index(self, ori_note, chan):
        index = None
        for i, n in enumerate(self.curr_note_ons):
            if n["ori"] == (ori_note, chan):
                index = i
        return index     
    # ----
