class Feedback:
    def __init__(self, midi, mood):
        self.midi = midi
        self.mood = mood
        self.curr_note_ons = []  #ex: [{"ori": 10, "sent": [12, 13]}]
        ## liste des notes ons (ori note, sent notes en ordre)
        ## si note off correspond à ori, envoyer first sent note et retirer de liste
        ## si on retire le dernier sent note, on retire ce "note one"
        pass
    
    # -- receive ----
    def on_note_on(self, ori_note, vel, chan):
        sent_note = self.mood.map_note(ori_note, False)
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

    # -- curr_note_ons ------------------------------
    ###### si output already on, send off just before new on
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
