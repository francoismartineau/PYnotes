import math
#pip install crepe
import crepe
from scipy.io import wavfile

class Sound:
    @staticmethod
    def freq_to_note(f):
        return int(12 * math.log10(f/220) / math.log10(2) + 57.01)


if __name__ == "__main__":
    print(Sound.freq_to_note(440))