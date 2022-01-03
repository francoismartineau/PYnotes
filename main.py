import time
import midi, mood, feedback
import utils


if utils.already_running():
    print("Script is already running")
else:
    utils.lock_script()
    mi = midi.Midi()
    mo = mood.Mood(mi)
    fe = feedback.Feedback(mi, mo, midi.FL_TO_PY.FEEDBACK["chans"])
    mi.set_mood(mo)
    mi.set_feedback(fe)

    #for _ in range(1000):
        #time.sleep(random.randint(1, 100)/1000)
    #    time.sleep(.05)
    #    m.make_note(40, random.randint(30, 50), 1, 2)

    while utils.fl_ahk_running() and utils.still_locked():
        time.sleep(2)

    for t in mi.get_threads():
        t.join()
    
    if (utils.still_locked()):
        utils.unlock_script()
    print("Quitting")