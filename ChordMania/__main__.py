"""
ChordMania is a module for generating random chord progressions for practice,
using the music21 library. The generated chords can be limited by a specified
key signature, number of measures, number of notes per chord, and the option to
include chords for both hands.
"""

import argparse
import logging
import random
import music21
from music21.musicxml import m21ToXml

us = music21.environment.UserSettings()
us['musicxmlPath'] = "~/Applications/MuseScore 3.app/Contents/MacOS/mscore"
us['musescoreDirectPNGPath'] = "~/Applications/MuseScore 3.app/Contents/MacOS/mscore"

# I'm not interested in performance, I just want to eliminate duplicates
# in one line by using a python set
music21.chord.Chord.__hash__ = lambda self: 0

logger = logging.getLogger("ChordMania")

def has_adjacent_notes_exceeding_max_length(chord, max_length):
    """
    Check if a music21 chord has more than `max_length` adjacent notes.

    Args:
        chord (music21.chord.Chord): A music21 chord to check for adjacent notes.
        max_length (int): The maximum length of adjacent notes allowed.

    Returns:
        bool: True if more than `max_length` adjacent notes are found, False otherwise.
    """
    sorted_notes = sorted(chord.pitches, key=lambda p: p.midi)

    for i in range(1, len(sorted_notes)):
        adjacent_notes_count = 1
        for j in range(i, len(sorted_notes)):
            if sorted_notes[j].midi == sorted_notes[j - 1].midi + 1:
                adjacent_notes_count += 1
                if adjacent_notes_count > max_length:
                    return True
            else:
                break

    return False


class CMFourFiveStreamGenerator():
    """
    Generates a random stream of intervals for practice using the music21 library.
    The intervals are either 4 or 5 white notes apart and are close together.

    Attributes:
        score (music21.stream.Score): The music21 score containing the generated music.
    """

    def __init__(self, num_measures):
        """
        Initialize the CMFourFiveStreamGenerator with the specified number of measures.

        Args:
            num_measures (int): The number of measures in the generated stream.
        """

        self.score = music21.stream.Score()

        metadata = music21.metadata.Metadata()
        metadata.title = "4/5 Stream Practice"
        metadata.composer = "ChordMania"
        self.score.append(metadata)

        time_signature = music21.meter.TimeSignature('4/4')

        right_hand = music21.stream.Part()
        right_hand.insert(0, music21.instrument.Piano())
        right_hand.insert(0, music21.clef.TrebleClef())
        right_hand.insert(0, time_signature)

        white_notes = self.get_white_notes_between('C4', 'C6')

        current_root = music21.note.Note('C5')

        for _ in range(num_measures):
            for _ in range(8):
                # Select next root note
                step = random.choice([-2, -1, 0, 1, 2])
                next_index = white_notes.index(current_root) + step
                if 0 <= next_index < len(white_notes) - 5:
                    pass
                else:
                    next_index = int(len(white_notes)/2)
                current_root = white_notes[next_index]

                # Generate random chord
                interval = random.choice([3, 4])
                chord = music21.chord.Chord([current_root, white_notes[next_index+interval]])
                chord.quarterLength = 0.5
                right_hand.append(chord)

        self.score.insert(0, right_hand)

    @staticmethod
    def get_white_notes_between(start, end):
        """
        Get all white notes (notes without accidentals) between the given start
        and end notes.

        Args:
            start (str): The starting note, as a string (e.g., 'C4').
            end (str): The ending note, as a string (e.g., 'C6').

        Returns:
            list: A list of music21.note.Note objects representing the white
            notes between the start and end notes.
        """

        white_notes = []
        current = music21.note.Note(start)
        while current <= music21.note.Note(end):
            if current.pitch.accidental is None:
                white_notes.append(current)
            current = music21.note.Note(current.pitch).transpose(1)
        return white_notes

    def render(self):
        """
        Render the score as MusicXML, and print the output to STDOUT.

        This method converts the music21 stream (self.score) to MusicXML format and
        prints the output to STDOUT.  If the logger's effective level is set to
        logging.DEBUG, it will also display the score as an image using the
        "musicxml.png" format and output the music21 stream representation to STDERR.
        """

        # Convert the music21 stream to MusicXML format and print to STDOUT
        musicxml_exporter = m21ToXml.GeneralObjectExporter(self.score)
        musicxml_str = musicxml_exporter.parse().decode('utf-8')
        print(musicxml_str)

        # Debug stuff
        logger.debug(self.score._reprText()) # pylint: disable=protected-access
        if logger.getEffectiveLevel() <= logging.DEBUG:
            self.score.show(fmt="musicxml.png")

class CMChordGenerator():
    """
    A class for generating random chord progressions using the music21
    library.

    Attributes:
        stream (music21.stream.Stream): The music21 stream containing the
        generated chords.
    """

    def __init__(self, notes_per_chord, num_chords, key, both_hands):
        """
        Initialize the CMChordGenerator with the specified parameters.

        Args:
            notes_per_chord (int): The number of notes per chord.
            num_chords (int): The number of chords to generate.
            key (music21.key.Key): The key signature for the chords.
            both_hands (bool): Whether to generate chords for both hands.
        """

        # Create our stream!
        self.stream = music21.stream.Stream()
        metadata = music21.metadata.Metadata()
        metadata.title = f"Random {key.name.replace('-', 'b')} Practice"
        metadata.composer = "ChordMania"
        metadata.movementName = f"{num_chords} Chords"
        self.stream.append(metadata)

        parts = [self._generate_part(notes_per_chord, num_chords, key, False)]
        if both_hands:
            parts.append(self._generate_part(notes_per_chord, num_chords, key, True))
            staff_group = music21.layout.StaffGroup(parts,
                                                    name='Piano',
                                                    abbreviation='Pno.',
                                                    symbol='brace')
            staff_group.barTogether = 'Mensurstrich'
            self.stream.append(staff_group)

        self.stream.append(parts)

    def _generate_part(self, notes_per_chord, num_chords, key, left_hand):
        part = music21.stream.PartStaff()
        instrument = music21.instrument.Piano()
        instrument.partName = "Piano"
        part.append(instrument)

        for measure_number in range(num_chords):
            measure = music21.stream.Measure()
            measure.number = measure_number + 1

            # Set the first measure's Clef, TimeSignature, and KeySignature
            if measure_number == 0:
                if left_hand:
                    measure.append(music21.clef.BassClef())
                else:
                    measure.append(music21.clef.TrebleClef())
                measure.append(music21.meter.TimeSignature('4/4'))

                measure.append(key)

            # Generate a random chord and transpose it
            random_chord = self.generate_chord(['4', '5'], key, notes_per_chord)
            if left_hand:
                # First move it down a bunch before we move it right back up
                random_chord = random_chord.transpose(-24)

            # Update the measure with a ChordSymbol if possible.
            # Only include ChordSymbols for the right hand at the moment.
            if not left_hand:
                cs_string = music21.harmony.chordSymbolFigureFromChord(random_chord)
                if cs_string != 'Chord Symbol Cannot Be Identified':
                    try:
                        # Sometimes you get a weird exception like:
                        # "-poweradda is not a supported accidental type" or
                        # "#m/aadde- is not a supported accidental type"
                        # I don't know exactly what the problem is, but let's just
                        # not annotate those chords
                        measure.append(music21.harmony.ChordSymbol(cs_string))
                    except music21.pitch.AccidentalException:
                        pass

            # Finally add the chord to the measure, and the measure to the stream
            measure.append(random_chord)
            part.append(measure)

        return part

    @staticmethod
    def generate_chord(octaves, key, num_notes):
        """
        Generate a random chord with the given number of notes within the specified octaves and key.

        Args:
            octaves (list): A list of octave numbers in which the chord's notes should be selected.
            key (music21.key.Key): The key signature for the generated chord.
            num_notes (int): The number of notes in the chord.

        Returns:
            music21.chord.Chord: A randomly generated chord satisfying the given conditions.
        """

        pitch_classes = ['C', 'D', 'E', 'F', 'G', 'A', 'B']
        accidentals = ['', '-', '#']
        all_pitches = [f'{pc}{acc}{octave}' for pc in pitch_classes
                                            for acc in accidentals
                                            for octave in octaves]

        while True:
            chord_pitches = random.sample(all_pitches, num_notes)
            random_chord = music21.chord.Chord(chord_pitches, quarterLength=4)
            random_chord = random_chord.sortChromaticAscending().simplifyEnharmonics(keyContext=key)

            if random_chord.hasAnyRepeatedDiatonicNote():
                continue

            # hasAnyRepeatedDiatonicNote() doesn't actually check to see if there
            # are identical notes.
            if len(set(n.pitch.midi for n in random_chord)) != num_notes:
                continue

            chord_span = random_chord[-1].pitch.midi - random_chord[0].pitch.midi
            if chord_span < 5 or chord_span > 12:
                continue

            # Until Synthesia/MoonPiano/etc... can render better sheet music, disallow
            # too many adjacent notes
            if has_adjacent_notes_exceeding_max_length(random_chord, 2):
                continue

            # We've found a good chord to use!
            break

        return random_chord

    def _get_all_chords(self, parent):
        """
        Get all chords contained within the given parent music21 object.

        Args:
            parent (music21.base.Music21Object): A music21 object containing chords.

        Returns:
            list: A list of music21.chord.Chord objects found within the parent object.
        """

        # ChordSymbol derives from Chord, so we need to filter out only
        # the Chords since getElementsByClass will return both.
        return [e for e in parent.recurse().getElementsByClass(music21.chord.Chord)
                if e.__class__ is music21.chord.Chord]

    def _get_unique_chords(self, parent):
        """
        Get all unique chords contained within the given parent music21 object.

        Args:
            parent (music21.base.Music21Object): A music21 object containing chords.

        Returns:
            set: A set of unique music21.chord.Chord objects found within the parent object.
        """

        return set(self._get_all_chords(parent))

    def render(self):
        """
        Render the score as MusicXML, and print the output to STDOUT.

        This method converts the music21 stream (self.score) to MusicXML format and
        prints the output to STDOUT.  If the logger's effective level is set to
        logging.DEBUG, it will also display the score as an image using the
        "musicxml.png" format and output the music21 stream representation to STDERR.
        """

        # Finalize some metadata
        metadata = self.stream.getElementsByClass(music21.metadata.Metadata).stream().next()
        metadata["description"] = (
                f"{len(self._get_unique_chords(self.stream))}/"
                f"{len(self._get_all_chords(self.stream))} chords are unique."
                )

        # Convert the music21 stream to MusicXML format and print to STDOUT
        musicxml_exporter = m21ToXml.GeneralObjectExporter(self.stream)
        musicxml_str = musicxml_exporter.parse().decode('utf-8')
        print(musicxml_str)

        # Debug stuff
        logger.debug(self.stream._reprText()) # pylint: disable=protected-access
        if logger.getEffectiveLevel() <= logging.DEBUG:
            self.stream.show(fmt="musicxml.png")

if __name__== "__main__":
    parser = argparse.ArgumentParser(
            prog='ChordMania',
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-k", "--key", type=music21.key.Key,
                        help="Key Signature.  Use '-' for flats and lowercase letters for minor.")
    parser.add_argument("-m", "--measures", default=100, type=int, help="Number of measures")
    parser.add_argument("-n", "--notes", default=4, type=int, help="Number of notes per chords")
    parser.add_argument("-b", "--both_hands", action='store_true', help="Include both hands")
    parser.add_argument("-d", "--debug", help="Debug mode",
                        action="store_const", dest="loglevel", const=logging.DEBUG,
                        default=logging.WARNING)
    args = parser.parse_args()

    logging.basicConfig()
    logger.setLevel(level=args.loglevel)

    # Just pick a random Key if nothing is provided on the command line
    all_keys = range(-6, 7)  # Every key (negatives=flats, positives=sharps)
    if not args.key:
        args.key = music21.key.KeySignature(random.choice(all_keys)).asKey()

#    cg = CMChordGenerator(args.notes, args.measures, key=args.key, both_hands=args.both_hands)
    cg = CMFourFiveStreamGenerator(args.measures)
    cg.render()
