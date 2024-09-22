''' This script contains a collection of midi helper and utility functions. '''

#import copy
#import pprint
#from collections import defaultdict
from math import log, floor, ceil
from mido import MidiFile, MidiTrack, Message, MetaMessage
import numpy as np
import random
import time
import enum
import os

DEBUG = False

class PitchFollower:
    def __init__(self, pitch):
        self.pitch = pitch
        self.quantity = 0

    def increment_quantity(self):
        self.quantity += 1

class Midi_Util:

    ''' Delete old/unused code
    def quantize_tick(self, tick, ticks_per_quarter, quantization):
        # Quantize the timestamp or tick.
        #
        # Arguments:
        # tick -- An integer timestamp
        # ticks_per_quarter -- The number of ticks per quarter note
        # quantization -- The note duration, represented as 1/2**quantization

        assert (ticks_per_quarter * 4) % 2 ** quantization == 0, \
            'Quantization too fine. Ticks per quantum must be an integer.'
        ticks_per_quantum = (ticks_per_quarter * 4) / float(2 ** quantization)
        quantized_ticks = int(
            round(tick / float(ticks_per_quantum)) * ticks_per_quantum)
        return quantized_ticks

    def quantize_track(self, track, ticks_per_quarter, quantization):
        # Return the differential time stamps of the note_on, note_off, and
        # end_of_track events, in order of appearance, with the note_on events
        # quantized to the grid given by the quantization.

        # Arguments:
        # track -- MIDI track containing note event and other messages
        # ticks_per_quarter -- The number of ticks per quarter note
        # quantization -- The note duration, represented as
        # 1/2**quantization.

        pp = pprint.PrettyPrinter()

        # Message timestamps are represented as differences between
        # consecutive events. Annotate messages with cumulative timestamps.

        # Assume the following structure:
        # [header meta messages] [note messages] [end_of_track message]
        first_note_msg_idx = None
        for i, msg in enumerate(track):
            if msg.type == 'note_on':
                first_note_msg_idx = i
                break

        cum_msgs = zip(
            np.cumsum([msg.time for msg in track[first_note_msg_idx:]]),
            [msg for msg in track[first_note_msg_idx:]])
        end_of_track_cum_time = cum_msgs[-1][0]

        quantized_track = MidiTrack()
        quantized_track.extend(track[:first_note_msg_idx])
        # Keep track of note_on events that have not had an off event yet.
        # note number -> message
        open_msgs = defaultdict(list)
        quantized_msgs = []
        for cum_time, msg in cum_msgs:
            if DEBUG:
                print ('Message:', msg)
                print ('Open messages:')
                pp.pprint(open_msgs)
            if msg.type == 'note_on' and msg.velocity > 0:
                # Store until note off event. Note that there can be
                # several note events for the same note. Subsequent
                # note_off events will be associated with these note_on
                # events in FIFO fashion.
                open_msgs[msg.note].append((cum_time, msg))
            elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                assert msg.note in open_msgs, \
                    'Bad MIDI. Cannot have note off event before note on event'
                note_on_open_msgs = open_msgs[msg.note]
                note_on_cum_time, note_on_msg = note_on_open_msgs[0]
                open_msgs[msg.note] = note_on_open_msgs[1:]
                # Quantized note_on time
                quantized_note_on_cum_time = self.quantize_tick(
                    note_on_cum_time, ticks_per_quarter, quantization)
                # The cumulative time of note_off is the quantized
                # cumulative time of note_on plus the orginal difference
                # of the unquantized cumulative times.
                quantized_note_off_cum_time = quantized_note_on_cum_time + (cum_time - note_on_cum_time)
                quantized_msgs.append((min(end_of_track_cum_time, quantized_note_on_cum_time), note_on_msg))
                quantized_msgs.append((min(end_of_track_cum_time, quantized_note_off_cum_time), msg))

                if DEBUG:
                    print ('Appended', quantized_msgs[-2:])
            elif msg.type == 'end_of_track':
                quantized_msgs.append((cum_time, msg))

            if DEBUG:
                print ('\n')

        # Now, sort the quantized messages by (cumulative time,
        # note_type), making sure that note_on events come before note_off
        # events when two event have the same cumulative time. Compute
        # differential times and construct the quantized track messages.
        quantized_msgs.sort(
            key=lambda cum_time, msg : cum_time
            if (msg.type=='note_on' and msg.velocity > 0) else cum_time + 0.5)

        diff_times = [quantized_msgs[0][0]] + list(
            np.diff([ msg[0] for msg in quantized_msgs ]))
        for diff_time, (cum_time, msg) in zip(diff_times, quantized_msgs):
            quantized_track.append(msg.copy(time=diff_time))
        if DEBUG:
            print ('Quantized messages:')
            pp.pprint(quantized_msgs)
            pp.pprint(diff_times)
        return quantized_track

    def quantize(self, mid, quantization=5):
        # Return a midi object whose notes are quantized to
        # 1/2**quantization notes.
        #
        # Arguments:
        # mid -- MIDI object
        # quantization -- The note duration, represented as
        # 1/2**quantization.

        quantized_mid = copy.deepcopy(mid)
        # By convention, Track 0 contains metadata and Track 1 contains
        # the note on and note off events.
        note_track_idx, note_track = self.get_note_track(mid)
        quantized_mid.tracks[note_track_idx] = self.quantize_track(
            note_track, mid.ticks_per_beat, quantization)
        return quantized_mid
    '''

    class Pitches(enum.IntEnum):
        C_minus2 = 0
        Cis_minus2 = 1
        D_minus2 = 2
        Dis_minus2 = 3
        E_minus2 = 4
        F_minus2 = 5
        Fis_minus2 = 6
        G_minus2 = 7
        Gis_minus2 = 8
        A_minus2 = 9
        Ais_minus2 = 10
        B_minus2 = 11
        C_minus1 = 12
        Cis_minus1 = 13
        D_minus1 = 14
        Dis_minus1 = 15
        E_minus1 = 16
        F_minus1 = 17
        Fis_minus1 = 18
        G_minus1 = 19
        Gis_minus1 = 20
        A_minus1 = 21
        Ais_minus1 = 22
        B_minus1 = 23
        C0 = 24
        Cis0 = 25
        D0 = 26
        Dis0 = 27
        E0 = 28
        F0 = 29
        Fis0 = 30
        G0 = 31
        Gis0 = 32
        A0 = 33
        Ais0 = 34
        B0 = 35
        C1 = 36
        Cis1 = 37
        D1 = 38
        Dis1 = 39
        E1 = 40
        F1 = 41
        Fis1 = 42
        G1 = 43
        Gis1 = 44
        A1 = 45
        Ais1 = 46
        B1 = 47
        C2 = 48
        Cis2 = 49
        D2 = 50
        Dis2 = 51
        E2 = 52
        F2 = 53
        Fis2 = 54
        G2 = 55
        Gis2 = 56
        A2 = 57
        Ais2 = 58
        B2 = 59
        C3 = 60
        Cis3 = 61
        D3 = 62
        Dis3 = 63
        E3 = 64
        F3 = 65
        Fis3 = 66
        G3 = 67
        Gis3 = 68
        A3 = 69
        Ais3 = 70
        B3 = 71
        C4 = 72
        Cis4 = 73
        D4 = 74
        Dis4 = 75
        E4 = 76
        F4 = 77
        Fis4 = 78
        G4 = 79
        Gis4 = 80
        A4 = 81
        Ais4 = 82
        B4 = 83
        C5 = 84
        Cis5 = 85
        D5 = 86
        Dis5 = 87
        E5 = 88
        F5 = 89
        Fis5 = 90
        G5 = 91
        Gis5 = 92
        A5 = 93
        Ais5 = 94
        B5 = 95
        C6 = 96
        Cis6 = 97
        D6 = 98
        Dis6 = 99
        E6 = 100
        F6 = 101
        Fis6 = 102
        G6 = 103
        Gis6 = 104
        A6 = 105
        Ais6 = 106
        B6 = 107
        C7 = 108
        Cis7 = 109
        D7 = 110
        Dis7 = 111
        E7 = 112
        F7 = 113
        Fis7 = 114
        G7 = 115
        Gis7 = 116
        A7 = 117
        Ais7 = 118
        B7 = 119
        C8 = 120
        Cis8 = 121
        D8 = 122
        Dis8 = 123
        E8 = 124
        F8 = 125
        Fis8 = 126
        G8 = 127

    class RawPitch(enum.IntEnum):
        C = 0
        Cis = enum.auto()
        D = enum.auto()
        Dis = enum.auto()
        E = enum.auto()
        F = enum.auto()
        Fis = enum.auto()
        G = enum.auto()
        Gis = enum.auto() 
        A = enum.auto()
        Ais = enum.auto() 
        B = enum.auto()
    
    Rhythms = ["", # rhythms to string
               "32th note", 
               "16th note",
               "3x32th note",
               "8th note",
               "5x32th note",
               "6x32th note",
               "7x32th note",
               "4th note",
               "9x32th note",
               "10x32th note",
               "11x32th note",
               "12x32th note",
               "13x32th note",
               "14x32th note",
               "15x32th note",
               "half note",
               "17x32th note",
               "18x32th note",
               "19x32th note",
               "20x32th note",
               "21x32th note",
               "22x32th note",
               "23x32th note",
               "24x32th note",
               "25x32th note",
               "26x32th note",
               "27x32th note",
               "28x32th note",
               "29x32th note",
               "30x32th note",
               "31x32th note",
               "whole note",
               "33x32th note",
               "34x32th note",
               "35x32th note",
               "36x32th note",
               "37x32th note",
               "38x32th note",
               "39x32th note",
               "40x32th note",
               "41x32th note",
               "42x32th note",
               "43x32th note",
               "44x32th note",
               "45x32th note",
               "46x32th note",
               "47x32th note",
               "48x32th note",
               "49x32th note",
               "50x32th note",
               "51x32th note",
               "52x32th note",
               "53x32th note",
               "54x32th note",
               "55x32th note",
               "56x32th note",
               "57x32th note",
               "58x32th note",
               "59x32th note",
               "60x32th note",
               "61x32th note",
               "62x32th note",    
               "63x32th note",    
               "double note",    
               "65x32th note",
               "66x32th note",
               "67x32th note",
               "68x32th note",
               "69x32th note",
               "70x32th note",
               "71x32th note",
               "72x32th note",
               "73x32th note",
               "74x32th note",
               "75x32th note",
               "76x32th note",
               "77x32th note",
               "78x32th note",
               "79x32th note",
               "80x32th note",
               "81x32th note",
               "82x32th note",
               "83x32th note",
               "84x32th note",
               "85x32th note",
               "86x32th note",
               "87x32th note",
               "88x32th note",
               "89x32th note",
               "90x32th note",
               "91x32th note",
               "92x32th note",
               "93x32th note",
               "94x32th note",
               "95x32th note",
               "96x32th note",
               "97x32th note",
               "98x32th note",
               "99x32th note",
               "100x32th note",
               "101x32th note",
               "102x32th note",
               "103x32th note",
               "104x32th note",
               "105x32th note",
               "106x32th note",
               "107x32th note",
               "108x32th note",
               "109x32th note",
               "110x32th note",
               "111x32th note",
               "112x32th note",
               "113x32th note",
               "114x32th note",
               "115x32th note",
               "116x32th note",
               "117x32th note",
               "118x32th note",
               "119x32th note",
               "120x32th note",
               "121x32th note",
               "122x32th note",
               "123x32th note",
               "124x32th note",
               "125x32th note",
               "126x32th note",
               "127x32th note",
               "long note",
               "129x32th note",
               "130x32th note",
               "131x32th note",
               "132x32th note",
               "133x32th note",
               "134x32th note",
               "135x32th note",
               "136x32th note",
               "137x32th note",
               "138x32th note",
               "139x32th note",
               "140x32th note",
               "141x32th note",
               "142x32th note",
               "143x32th note",
               "144x32th note",
               "145x32th note",
               "146x32th note",
               "147x32th note",
               "148x32th note",
               "149x32th note",
               "150x32th note",
               "151x32th note",
               "152x32th note",
               "153x32th note",
               "154x32th note",
               "155x32th note",
               "156x32th note",
               "157x32th note",
               "158x32th note",
               "159x32th note",
               "160x32th note",
               "161x32th note",
               "162x32th note",
               "163x32th note",
               "164x32th note",
               "165x32th note",
               "166x32th note",
               "167x32th note",
               "168x32th note",
               "169x32th note",
               "170x32th note",
               "171x32th note",
               "172x32th note",
               "173x32th note",
               "174x32th note",
               "175x32th note",
               "176x32th note",
               "177x32th note",
               "178x32th note",
               "179x32th note",
               "180x32th note",
               "181x32th note",
               "182x32th note",
               "183x32th note",
               "184x32th note",
               "185x32th note",
               "186x32th note",
               "187x32th note",
               "188x32th note",
               "189x32th note",
               "190x32th note",
               "191x32th note",
               "192x32th note",
               "193x32th note",
               "194x32th note",
               "195x32th note",
               "196x32th note",
               "197x32th note",
               "198x32th note",
               "199x32th note",
               "200x32th note",
               "201x32th note",
               "202x32th note",
               "203x32th note", 
               "204x32th note",
               "205x32th note",
               "206x32th note",
               "207x32th note",
               "208x32th note",
               "209x32th note",
               "210x32th note",
               "211x32th note",
               "212x32th note",
               "213x32th note",
               "214x32th note",
               "215x32th note",
               "216x32th note",
               "217x32th note",
               "218x32th note",
               "219x32th note",
               "220x32th note",
               "221x32th note",
               "222x32th note",
               "223x32th note",
               "224x32th note",
               "225x32th note",
               "226x32th note",
               "227x32th note",
               "228x32th note",
               "229x32th note",
               "230x32th note", 
               "231x32th note", 
               "232x32th note", 
               "233x32th note", 
               "234x32th note",
               "235x32th note",
               "236x32th note",
               "237x32th note",
               "238x32th note",
               "239x32th note",
               "240x32th note",
               "241x32th note",
               "242x32th note",
               "243x32th note",
               "244x32th note",
               "245x32th note",
               "246x32th note",
               "247x32th note",
               "248x32th note",
               "249x32th note",
               "250x32th note",
               "251x32th note",
               "252x32th note",
               "253x32th note",
               "254x32th note",
               "255x32th note",
               "256x32th note",] 

    # Konstruktor
    def __init__(self): 
        self.MAX_NOTES = 128 # highest midi note number (pitch G8)
        self.MAX_BREAK_TIME = 128 # maximum break time = 128 x 32th intervals
        self.MIDI_STEPS_LENGTH = 256 # length of a 8 bar loop
        self.MIDI_ARRAY_LENGTH = 32768

        self.locked_steps = []

        # Pitches are followed by a defined other pitch
        self.pitch_followers = []
        self.pitch_followers.append ([]) # followers of C
        self.pitch_followers.append ([]) # followers of Cis
        self.pitch_followers.append ([]) # followers of D
        self.pitch_followers.append ([]) # followers of Dis
        self.pitch_followers.append ([]) # followers of E
        self.pitch_followers.append ([]) # followers of F
        self.pitch_followers.append ([]) # followers of Fis
        self.pitch_followers.append ([]) # followers of G
        self.pitch_followers.append ([]) # followers of Gis
        self.pitch_followers.append ([]) # followers of A
        self.pitch_followers.append ([]) # followers of Ais
        self.pitch_followers.append ([]) # followers of B

        # Pitches are followed by a defined other pitch at each step
        self.pitch_followers_at_step = []
        for i in range (self.MIDI_STEPS_LENGTH):
            self.pitch_followers_at_step.append (-1)

        # This list is a helper list for rhythm randomization and represents the exact pitch sequence in the file (similar to pitch followers)
        self.pitch_sequence = []

        # Notes are followed by a defined rhythm at each step
        self.rhythm_intervals_at_step = []
        for i in range (self.MIDI_STEPS_LENGTH):
            self.rhythm_intervals_at_step.append ([])
            for j in range (self.MAX_NOTES):
                self.rhythm_intervals_at_step[i].append (0)

        self.num_of_notes = 0 # amount of notes in the pattern (maximum 256 steps or self.MIDI_STEPS_LENGTH)
        self.note_rhythms = [] # quantities of found rhythms of the notes (break intervals in multiples of 32th steps)
        for i in range (self.MAX_BREAK_TIME + 1):
            self.note_rhythms.append (0)

        random.seed(hash (tuple (time.strftime("%d.%m.%Y %H:%M:%S")))) # random timestamp

    def get_note_track(self, mid):
        ''' Given a MIDI object, return the first track with note events.'''

        for i, track in enumerate(mid.tracks):
            for msg in track:
                if msg.type == 'note_on':
                    return i, track
        raise ValueError(
            'MIDI object does not contain any tracks with note messages.')

    def midi_to_array(self, mid, quantization, pitch_offset=12):
        ''' Return array representation of a 4/4 time signature, MIDI object.

        Normalize the number of time steps in track to a power of 2. Then
        construct a T x N array A (T = number of time steps, N = number of
        MIDI note numbers) where A(t,n) is the velocity of the note number
        n at time step t if the note is active, and 0 if it is not.

        Arguments:
        mid -- MIDI object with a 4/4 time signature
        quantization -- The note duration, represented as 1/2**quantization. '''

        time_sig_msgs = [ msg for msg in mid.tracks[0] if msg.type == 'time_signature' ]
        assert len(time_sig_msgs) == 1, 'No time signature found'
        time_sig = time_sig_msgs[0]
        assert time_sig.numerator == 4 and time_sig.denominator == 4, 'Not 4/4 time.'

        # Convert the note timing and velocity to an array.
        _, track = self.get_note_track(mid)
        ticks_per_quarter = mid.ticks_per_beat

        time_msgs = [msg for msg in track if hasattr(msg, 'time')]
        cum_times = np.cumsum([msg.time for msg in time_msgs])
        track_len_ticks = cum_times[-1]
        if DEBUG:
            print ('Track len in ticks:', track_len_ticks)
            print ('Track len in ticks:', track_len_ticks)
        notes = [
            (time * (2**quantization/4) / (ticks_per_quarter), msg.note, msg.velocity)
            for (time, msg) in zip(cum_times, time_msgs)
            if msg.type == 'note_on' ]
        num_steps = int(round(track_len_ticks / float(ticks_per_quarter)*2**quantization/4))
        normalized_num_steps = int(self.nearest_pow2(num_steps))

        if DEBUG:
            print (num_steps)
            print (normalized_num_steps)

        step_array = np.zeros((normalized_num_steps, self.MAX_NOTES))
        for (position, note_num, velocity) in notes:
            if position == normalized_num_steps:
                #print 'Warning: truncating from position {} to {}'.format(position, normalized_num_steps - 1)
                continue
                #position = normalized_num_steps - 1
            if position > normalized_num_steps:
                #print 'Warning: skipping note at position {} (greater than {})'.format(position, normalized_num_steps)
                continue
            step_array[int(position), note_num+pitch_offset] = velocity

        return step_array

    def array_to_midi(self, step_array,
                    name,
                    quantization=5,
                    pitch_offset=-12,
                    midi_type=1,
                    midi_ticks_per_quarter=480,
                    midi_tempo=600000):
        ''' Convert an array into a MIDI object.

        When an MIDI object is converted to an array, information is
        lost. That information needs to be provided to create a new MIDI
        object from the array. For this application, we don't care about
        this metadata, so we'll use some default values.

        Arguments:
        array -- An array A[time_step, note_number] = 1 if note on, 0 otherwise.
        quantization -- The note duration, represented as 1/2**quantization.
        pitch_offset -- Offset the pitch number relative to the array index.
        midi_type -- Type of MIDI format.
        ticks_per_quarter -- The number of MIDI timesteps per quarter note. '''

        mid = MidiFile()
        meta_track = MidiTrack()
        note_track = MidiTrack()
        mid.tracks.append(meta_track)
        mid.tracks.append(note_track)

        meta_track.append(MetaMessage('track_name', name=name, time=0))
        meta_track.append(MetaMessage('time_signature',
                                    numerator=4,
                                    denominator=4,
                                    clocks_per_click=24,
                                    notated_32nd_notes_per_beat=8,
                                    time=0))
        meta_track.append(MetaMessage('set_tempo', tempo=midi_tempo, time=0))
        meta_track.append(MetaMessage('end_of_track', time=0))

        ticks_per_quantum = midi_ticks_per_quarter * 4 / 2**quantization

        note_track.append(MetaMessage('track_name', name=name, time=0))
        cumulative_events = []
        for t, time_slice in enumerate(step_array):
            for i, pitch_on in enumerate(time_slice):
                if pitch_on > 0:
                    cumulative_events.append(dict(
                        type = 'note_on',
                        pitch = i + pitch_offset,
                        time = ticks_per_quantum * t
                    ))
                    cumulative_events.append(dict(
                        type = 'note_off',
                        pitch = i + pitch_offset,
                        time = ticks_per_quantum * (t+1)
                    ))

        cumulative_events.sort(
            key=lambda msg: msg['time'] if msg['type']=='note_on' else msg['time'] + 0.5)
        last_time = 0
        for msg in cumulative_events:
            note_track.append(Message(type=msg['type'],
                                    channel=1,
                                    note=msg['pitch'],
                                    velocity=100,
                                    time=int(msg['time']-last_time)))
            last_time = msg['time']
        note_track.append(MetaMessage('end_of_track', time=0))
        return mid

    def nearest_pow2(self, x):
        ''' Normalize input to nearest power of 2, or midpoints between
        consecutive powers of two. Round down when halfway between two
        possibilities. '''

        low = 2**int(floor(log(x, 2)))
        high = 2**int(ceil(log(x, 2)))
        mid = (low + high) / 2

        if x < mid:
            high = mid
        else:
            low = mid
        if high - x < x - low:
            nearest = high
        else:
            nearest = low
        return nearest

    def get_raw_pitch(self, pitch):
        modulo = pitch % 12
        if modulo == 0:
            return self.RawPitch.C
        elif modulo == 1:
            return self.RawPitch.Cis
        elif modulo == 2:
            return self.RawPitch.D
        elif modulo == 3:
            return self.RawPitch.Dis
        elif modulo == 4:
            return self.RawPitch.E
        elif modulo == 5:
            return self.RawPitch.F
        elif modulo == 6:
            return self.RawPitch.Fis
        elif modulo == 7:
            return self.RawPitch.G
        elif modulo == 8:
            return self.RawPitch.Gis
        elif modulo == 9:
            return self.RawPitch.A
        elif modulo == 10:
            return self.RawPitch.Ais
        elif modulo == 11:
            return self.RawPitch.B        

    def get_pitch_from_pitch_array(self, pitch_array):
        ''' Returns the pitch inside the pitch array with velocity > 0.
            The assumption is that the midi is monophonic. '''
        return self.Pitches (np.argmax(pitch_array))

    def set_pitch(self, pitch_array, target_pitch):
        ''' Sets the target pitch inside the pitch array with velocity 100 '''
        for i in range(len(pitch_array)):
            pitch_array[i] = 0 # set all velocities to 0
        pitch_array[target_pitch] = 100 # set the target velocity to 100
        return pitch_array
    
    def clear_pitch(self, pitch_array):
        ''' Clears the pitch inside the pitch array (sets all velocities to 0) '''
        for i in range(len(pitch_array)):
            pitch_array[i] = 0 # set all velocities to 0
        return pitch_array

    def pitch_transpose(self, pitch_array, note, transposition):
        ''' Transpose the target note in the pitch array by x semitones. '''
        if note + transposition > 0 and note + transposition <= self.MAX_NOTES:
            if pitch_array[note] != 0:
                pitch_array[note + transposition] = pitch_array[note]
                pitch_array[note] = 0
        return pitch_array
    
    def calc_pitch_followers(self, step_array):
        ''' Save the pitch of the notes that follow a certain pitch. '''
        first_step = -1
        first_note = -1
        last_note = -1
        last_step = -1        
        for step in range(len(step_array)):
            for note in range(self.MAX_NOTES):
                if step_array[step][note] > 0: # velocity > 0
                    if last_note >= 0:
                        found = False
                        for pitch_follower in self.pitch_followers[self.get_raw_pitch(last_note)]:
                            if pitch_follower.pitch == note:
                                found = True
                                pitch_follower.increment_quantity()
                        if not found:
                            p = PitchFollower(note)
                            p.increment_quantity()
                            self.pitch_followers[self.get_raw_pitch(last_note)].append (p)
                    last_note = note
                    if first_step == -1:
                        first_step = step # remember the first step that contained a note on event
                        first_note = note
                    if last_step >= 0:
                        self.pitch_followers_at_step[last_step] = note
                    last_step = step # last step that contained a note on event
                    
        # Connect the last and the first note followers as a loop            
        self.pitch_followers_at_step[last_step] = first_note
        found = False
        for pitch_follower in self.pitch_followers[self.get_raw_pitch(last_note)]:
            if pitch_follower.pitch == first_note:
                found = True
                pitch_follower.increment_quantity()
        if not found:
            p = PitchFollower(first_note)
            p.increment_quantity()
            self.pitch_followers[self.get_raw_pitch(last_note)].append (p)        

        #for i in range (len(self.pitch_followers)): # filter duplicates from the pitch followers list by using set method
        #    self.pitch_followers[i] = list(set(self.pitch_followers[i])) 
            
        return self.pitch_followers

    def calc_rhythm_intervals(self, step_array):
        ''' Save the rhythm values of the notes and breaks between them. '''
        first_step = -1
        last_step = -1
        for step in range(len(step_array)):
            for note in range(self.MAX_NOTES):
                if step_array[step][note] > 0: # velocity > 0
                    if first_step == -1:
                        first_step = step # remember the first step that contained a note on event
                    if last_step >= 0:
                        if DEBUG:
                            print (step - last_step)
                        self.note_rhythms[step-last_step] += 1
                        self.rhythm_intervals_at_step[last_step][step-last_step] = 1
                    self.num_of_notes += 1
                    last_step = step # last step that contained a note on event

    def print_rhythm_info(self):
        ''' Prints the rhythm information of the midi pattern. '''
        print ("Rhythm information")
        print ("  Total number of notes = " + str(self.num_of_notes))
        for i in reversed(range(len(self.note_rhythms))):
            if i == 128:
                print ("  Number of long notes = " + str(self.note_rhythms[128]))
            elif i == 64:
                print ("  Number of double notes = " + str(self.note_rhythms[64]))
            elif i == 32:
                print ("  Number of whole notes = " + str(self.note_rhythms[32]))
            elif i == 16:
                print ("  Number of half notes = " + str(self.note_rhythms[16]))
            elif i == 8:
                print ("  Number of 4th notes = " + str(self.note_rhythms[8]))
            elif i == 4:
                print ("  Number of 8th notes = " + str(self.note_rhythms[4]))
            elif i == 2:
                print ("  Number of 16th notes = " + str(self.note_rhythms[2]))
            elif i == 1:
                print ("  Number of 32th notes = " + str(self.note_rhythms[1]))
            elif self.note_rhythms[i] > 0:
                print ("  Number of " + str(i) + "x32th notes = " + str(self.note_rhythms[i]))
        print ()
    
    def print_pitch_followers(self, raw_pitch):
        ''' Prints the pitch followers of a certain raw pitch. '''
        for tag in self.RawPitch:
            if tag == raw_pitch:
                raw_pitch_name = tag.name        
        print(raw_pitch_name + " followers")
        for pitch_follower in self.pitch_followers[raw_pitch]:
            for tag in self.Pitches:
                if tag == pitch_follower.pitch:
                    notename = tag.name
            print ("  " + raw_pitch_name + " is followed by " + notename + " with quantity " + str(pitch_follower.quantity))
        print()

    def print_array_binary(self, step_array):
        ''' Print an array representing midi notes in binary format. '''
        print ("Binary note array")

        res = ''
        for slice in step_array:
            for pitch in slice:
                if pitch > 0:
                    res += 'O'
                else:
                    res += '-'
            res += '\n'
        # Take out the last newline
        print (res[:-1])

    def print_array_notes(self, step_array):
        ''' Print an array representing midi notes in chromatic notation. '''
        print ("Note array")
        notename = ""
        for step in range(len(step_array)):
            for note in range(self.MAX_NOTES):
                if step_array[step][note] > 0:
                    for tag in self.Pitches:
                        if tag == note:
                            notename = tag.name
                    # Add different amount of tabs depending on the tag length
                    if (len(str(note) + " " + notename)) > 6: 
                        tabs ='\t'
                    else:
                        tabs = '\t\t'
                    print ("  Step = " + str(step) + " \t Note = " + str(note) + " " + notename + " " + tabs + " Velocity: " + str(step_array[step][note]))
        print()
        
    def notes_to_min_max(self, step_array, pitch_min, pitch_max):
        ''' Transposes notes in the step array to be inside of min and max by using +- 12 semitones transposition '''
        for step in range(len(step_array)):
            if step in self.locked_steps:
                continue            
            for pitch in range(self.MAX_NOTES):
                if step_array[step][pitch] > 0 and pitch > pitch_max:
                    step_array[step] = self.pitch_transpose(step_array[step], pitch, -12)                
                if step_array[step][pitch] > 0 and pitch < pitch_min:
                    step_array[step] = self.pitch_transpose(step_array[step], pitch, +12)
        return step_array

    def notes_transpose(self, step_array, transpose_algorithm, transpose_probability, transpose_same=False):
        ''' Transpose notes in the step array in octaves by using one of the transpose algorithms '''
        if transpose_algorithm == 0: # no transpose
            print ("  Transposition: no transposition")
        elif transpose_algorithm > 0 and transpose_algorithm <= 1: # 0 - 1 transpose down when followed by same
            if transpose_same:
                print ("  Transposition: -1 octave when followed by same and transpose-same = " + str(transpose_same))
            else:
                print ("  Transposition: -1 octave when followed by same")
            for step in range(len(step_array)):
                if step in self.locked_steps:
                    continue                
                if self.pitch_followers_at_step[step] == self.get_pitch_from_pitch_array(step_array[step]):
                    if transpose_same or random.random() < transpose_probability:
                        step_array[step] = self.pitch_transpose(step_array[step], self.get_pitch_from_pitch_array(step_array[step]), -12) # transpose down
        elif transpose_algorithm > 1 and transpose_algorithm <= 2: # 1 - 2 random transpose notes by +1 octave
            if transpose_same:            
                print ("  Transposition: random transpose notes by +1 octave and transpose-same = " + str(transpose_same))
            else:
                print ("  Transposition: random transpose notes by +1 octave")
            for step in range(len(step_array)):
                if step in self.locked_steps:
                    continue                
                if transpose_same and self.pitch_followers_at_step[step] == self.get_pitch_from_pitch_array(step_array[step]): # transpose same
                    if random.random() + 1 >= transpose_algorithm:
                        step_array[step] = self.pitch_transpose(step_array[step], self.get_pitch_from_pitch_array(step_array[step]), -12) # transpose down
                    else:
                        step_array[step] = self.pitch_transpose(step_array[step], self.get_pitch_from_pitch_array(step_array[step]), +12) # transpose up
                elif random.random() < transpose_probability:
                    if random.random() + 1 >= transpose_algorithm:
                        if self.pitch_followers_at_step[step] == self.get_pitch_from_pitch_array(step_array[step]):
                            step_array[step] = self.pitch_transpose(step_array[step], self.get_pitch_from_pitch_array(step_array[step]), -12) # transpose down
                    else:
                        step_array[step] = self.pitch_transpose(step_array[step], self.get_pitch_from_pitch_array(step_array[step]), +12) # transpose up
        elif transpose_algorithm > 2 and transpose_algorithm <= 3: # 2 - 3 random transpose notes by -1 octave
            if transpose_same:            
                print ("  Transposition: random transpose notes by -1 octave and transpose-same = " + str(transpose_same))
            else:
                print ("  Transposition: random transpose notes by -1 octave")
            for step in range(len(step_array)):
                if step in self.locked_steps:
                    continue                
                if transpose_same and self.pitch_followers_at_step[step] == self.get_pitch_from_pitch_array(step_array[step]): # transpose same
                    if random.random() + 2 >= transpose_algorithm:
                        step_array[step] = self.pitch_transpose(step_array[step], self.get_pitch_from_pitch_array(step_array[step]), -12) # transpose down
                    else:
                        step_array[step] = self.pitch_transpose(step_array[step], self.get_pitch_from_pitch_array(step_array[step]), -12) # transpose down
                elif random.random() < transpose_probability:
                    if random.random() + 2 >= transpose_algorithm:
                        if self.pitch_followers_at_step[step] == self.get_pitch_from_pitch_array(step_array[step]):
                            step_array[step] = self.pitch_transpose(step_array[step], self.get_pitch_from_pitch_array(step_array[step]), -12) # transpose down
                    else:
                        step_array[step] = self.pitch_transpose(step_array[step], self.get_pitch_from_pitch_array(step_array[step]), -12) # transpose down 
        elif transpose_algorithm > 3 and transpose_algorithm <= 4: # 3 - 4 random transpose notes by +-1 octave 
            if transpose_same:            
                print ("  Transposition: random transpose notes by +-1 octave and transpose-same = " + str(transpose_same))
            else:
                print ("  Transposition: random transpose notes by +-1 octave")
            for step in range(len(step_array)):
                if step in self.locked_steps:
                    continue                
                if transpose_same and self.pitch_followers_at_step[step] == self.get_pitch_from_pitch_array(step_array[step]): # transpose same
                    if random.random() >= 0.5:
                        step_array[step] = self.pitch_transpose(step_array[step], self.get_pitch_from_pitch_array(step_array[step]), -12) # transpose down
                    else:
                        step_array[step] = self.pitch_transpose(step_array[step], self.get_pitch_from_pitch_array(step_array[step]), -12) # transpose down   
                elif random.random() < transpose_probability:
                    if random.random() >= 0.5:
                        step_array[step] = self.pitch_transpose(step_array[step], self.get_pitch_from_pitch_array(step_array[step]), -12) # transpose down
                    else:
                        step_array[step] = self.pitch_transpose(step_array[step], self.get_pitch_from_pitch_array(step_array[step]), -12) # transpose down   
        return step_array

    def notes_random_pitch_followers(self, step_array, random_algorithm):
        ''' Randomly pitch up or down notes by using one of the transpose algorithms '''
        if random_algorithm == 0: # no random
            print ("  Random notes: no randomization")
        elif random_algorithm > 0 and random_algorithm <= 1: # 0 - 1 randomize by choosing one of the pitch followers (file-based)
            print ("  Random notes: choose random followers (file-based)")
            for step in range(len(step_array)):
                if step in self.locked_steps:
                    continue
                if self.get_pitch_from_pitch_array(step_array[step]) > 0: # check if there is a note on event at this step
                    if random.random() <= random_algorithm:                    
                        current_pitch = self.get_pitch_from_pitch_array(step_array[step])
                        random_follower = self.pitch_followers[self.get_raw_pitch(current_pitch)][random.randint(0, len(self.pitch_followers[self.get_raw_pitch(current_pitch)])-1)] # choose randomly from the pitch followers
                        step_array[step] = self.set_pitch(step_array[step], random_follower.pitch)
        elif random_algorithm > 1 and random_algorithm <= 2: # 1 - 2 randomize by choosing C major random between C5 and C6
            print ("  Random notes: choose random followers of C major")
            Cmajor = [0, 2, 4, 5, 7, 9, 11, 12, 14, 16, 17, 19, 21, 23] # C major 2 octaves
            for i in range(len(Cmajor)):
                Cmajor[i] += 7*12 # shift to octaves C5 and C6
            for step in range(len(step_array)):
                if step in self.locked_steps:
                    continue                
                if self.get_pitch_from_pitch_array(step_array[step]) > 0: # check if there is a note on event at this step
                    if random.random() > random_algorithm - 1:
                        current_pitch = self.get_pitch_from_pitch_array(step_array[step])
                        random_follower = self.pitch_followers[self.get_raw_pitch(current_pitch)][random.randint(0, len(self.pitch_followers[self.get_raw_pitch(current_pitch)])-1)] # choose randomly from the pitch followers
                        step_array[step] = self.set_pitch(step_array[step], random_follower.pitch)
                    else:
                        step_array[step] = self.set_pitch(step_array[step], Cmajor[random.randint(0, len(Cmajor)-1)])
        elif random_algorithm > 2 and random_algorithm <= 3: # 2 - 3 randomiize by choosing one of the pitch followers (file-based) and by using each of their quantities
            print ("  Random notes: choose random followers by quantity (file-based)")
            Cmajor = [0, 2, 4, 5, 7, 9, 11, 12, 14, 16, 17, 19, 21, 23] # C major 2 octaves
            for i in range(len(Cmajor)):
                Cmajor[i] += 7*12 # shift to octaves C5 and C6            
            for step in range(len(step_array)):
                if step in self.locked_steps:
                    continue                
                if self.get_pitch_from_pitch_array(step_array[step]) > 0: # check if there is a note on event at this step
                    if random.random() < random_algorithm - 2:                        
                        current_pitch = self.get_pitch_from_pitch_array(step_array[step])
                        random_follower = self.get_pitch_follower_by_quantity (current_pitch)
                        step_array[step] = self.set_pitch(step_array[step], random_follower.pitch)
                    else:
                        step_array[step] = self.set_pitch(step_array[step], Cmajor[random.randint(0, len(Cmajor)-1)])                    
        return step_array

    def get_pitch_follower_by_quantity(self, current_pitch):
        ''' Randomly returns a pitch follower by taking into account it's percental quantity '''
        random_indices = []
        for i in range(len(self.pitch_followers[self.get_raw_pitch(current_pitch)])):
            for q in range(self.pitch_followers[self.get_raw_pitch(current_pitch)][i].quantity):
                random_indices.append (i)
        return self.pitch_followers[self.get_raw_pitch(current_pitch)][random_indices[random.randint(0, len(random_indices)-1)]]

    def notes_random_rhythm_intervals(self, step_array, random_algorithm):
        ''' Randomly change the rhythm intervals inside the midi pattern '''

        # Get the exact pitch sequence and use it as base for the rhythm randomization
        for step in range(len(step_array)):
            if self.get_pitch_from_pitch_array(step_array[step]) > 0: # check if there is a note on event at this step
                self.pitch_sequence.append(self.get_pitch_from_pitch_array(step_array[step]))

        if random_algorithm == 0: # no random
            print ("  Random rhythm: no randomization")
        elif random_algorithm > 0 and random_algorithm <= 1: # 0 - 1 randomize by choosing one of the found rhythms (file-based)
            print ("  Random rhythm: choose random rhythm (file-based)")
            self.calc_rhythm_intervals(step_array)
            for step in range(len(step_array)):
                if step in self.locked_steps:
                    continue
                step_array[step] = self.clear_pitch(step_array[step]) # clear all note on events
            # filter only those elements that are > 0 from the note rhythms list by using list comprehension
            rhythms = []
            for rhythm in range(len(self.note_rhythms)):
                if self.note_rhythms[rhythm] > 0:
                    for j in range(self.note_rhythms[rhythm]):
                        rhythms.append(rhythm)
            step = 0
            seq_counter = 0
            step_array[step] = self.set_pitch(step_array[step], self.pitch_sequence[seq_counter])
            while step < len(step_array):
                random_rhythm = rhythms[random.randint(0, len(rhythms)-1)] # choose randomly from the rhythms
                step = step + random_rhythm
                seq_counter += 1
                if step >= len(step_array):
                    break
                if step in self.locked_steps:
                    continue
                step_array[step] = self.set_pitch(step_array[step], self.pitch_sequence[seq_counter%len(self.pitch_sequence)])
        elif random_algorithm > 1 and random_algorithm <= 2: # 1 - 2 randomize by choosing file random by (rhythm-)quantity.md (step-based)
            print ("  Random rhythm: choose random rhythm (step-based)")
            self.calc_rhythm_intervals(step_array)            
            for step in range(len(step_array)):
                if step in self.locked_steps:
                    continue                
                step_array[step] = self.clear_pitch(step_array[step]) # clear all note on events
            step = 0
            seq_counter = 0
            step_array[step] = self.set_pitch(step_array[step], self.pitch_sequence[seq_counter])
            while step < len(step_array):
                # filter only those elements that are > 0 from the note rhythms list by using list comprehension
                rhythms = []
                for rhythm in range(len(self.rhythm_intervals_at_step[step])):
                    if self.rhythm_intervals_at_step[step][rhythm] > 0:
                        for quantity in range(self.rhythm_intervals_at_step[step][rhythm]):
                            rhythms.append(rhythm)
                random_rhythm_at_step = rhythms[random.randint(0, len(rhythms)-1)] # choose randomly from the rhythms
                if random_rhythm_at_step == 0: # fill unknown rhythms with random rhythms
                    rhythms = []
                    for rhythm in range(len(self.note_rhythms)):
                        if self.note_rhythms[rhythm] > 0:
                            for j in range(self.note_rhythms[rhythm]):
                                rhythms.append(rhythm)
                    random_rhythm_at_step = rhythms[random.randint(0, len(rhythms)-1)] # choose randomly from the rhythms
                step = step + random_rhythm_at_step
                seq_counter += 1
                if step >= len(step_array):
                    break
                if step in self.locked_steps:
                    continue
                step_array[step] = self.set_pitch(step_array[step], self.pitch_sequence[seq_counter%len(self.pitch_sequence)])
        return step_array

    def load_info(self, pitch_quantity_path, rhythm_quantity_path):
        ''' Optionally the info can be loaded from a .md file '''
        f = open(pitch_quantity_path, "rt", encoding="latin-1")
        s = f.read() # read the complete file (till the end)
        f.close()
        for line in s.split('\n'):
            if line.lstrip().startswith('#') or line.lstrip() == '': # skip heading
                continue
            if line.strip() == "":
                continue
            line = line.split ('/')[0]
            raw_pitch = int(line.split('>')[0])
            pitch_follower = int(line.split('>')[1].split('=')[0])
            quantity = int(line.split('=')[1])

            p = PitchFollower(pitch_follower)
            p.quantity = quantity
            self.pitch_followers[raw_pitch].append (p)

        f = open(rhythm_quantity_path, "rt", encoding="latin-1")
        s = f.read() # read the complete file (till the end)
        f.close()

        start = False
        for line in s.split('\n'):
            if line.find("step-based") != -1:
                start = True
                continue
            elif line.lstrip().startswith('#') or line.lstrip() == '': # skip heading
                continue
            elif start:
                if line.strip() == "":
                    continue
                line = line.split ('/')[0]
                step = int(line.split('>')[0])
                rhythm = int(line.split('>')[1].split('=')[0])
                quantity = int(line.split('=')[1])
                if DEBUG:
                    print (str(step) + " > " + str(rhythm) + " = " + str(quantity))
                self.rhythm_intervals_at_step[step][rhythm] += quantity

    def load_locks(self, lock_steps_path):
        ''' Optionally some steps can be locked by a separate .md file '''
        if os.path.exists(lock_steps_path):
            f = open(lock_steps_path, "rt", encoding="latin-1")
            s = f.read() # read the complete file (till the end)
            f.close()
            for line in s.split('\n'):
                if line.lstrip().startswith('#') or line.lstrip() == '': # skip heading
                    continue
                if line.strip() == "":
                    continue
                self.locked_steps.append(int(line))

    def save_info(self, pitch_quantity_path, rhythm_quantity_path):
        ''' Save pitch followers info and rhythm info to a separate .md file '''
        f = open(pitch_quantity_path, "wt", encoding="latin-1")
        f.write("# Desired pitch distribution probabilities\n")
        f.write("## Pitch > Pitch-Follower = Quantity // Comment\n")
        for raw_pitch in self.RawPitch:
            for tag in self.RawPitch:
                if tag == raw_pitch:
                    raw_pitch_name = tag.name            
            for pitch_follower in self.pitch_followers[raw_pitch]:
                for tag in self.Pitches:
                    if tag == pitch_follower.pitch:
                        pitch_follower_name = tag.name      
                f.write(str(raw_pitch) + " \t> " + str(pitch_follower.pitch) + "\t = " + str(pitch_follower.quantity) + "\t // " + raw_pitch_name + " > " + pitch_follower_name + "\n")
        f.close()

        f = open(rhythm_quantity_path, "wt", encoding="latin-1")
        f.write("# Desired rhythmic distribution probabilities\n")
        f.write("  Total number of notes = " + str(self.num_of_notes) + "\n")
        for i in reversed(range(len(self.note_rhythms))):
            if i == 128:
                f.write("  Number of long notes = " + str(self.note_rhythms[128]) + "\n")
            elif i == 64:
                f.write("  Number of double notes = " + str(self.note_rhythms[64]) + "\n")
            elif i == 32:
                f.write("  Number of whole notes = " + str(self.note_rhythms[32]) + "\n")
            elif i == 16:
                f.write("  Number of half notes = " + str(self.note_rhythms[16]) + "\n")
            elif i == 8:
                f.write("  Number of 4th notes = " + str(self.note_rhythms[8]) + "\n")
            elif i == 4:
                f.write("  Number of 8th notes = " + str(self.note_rhythms[4]) + "\n")
            elif i == 2:
                f.write("  Number of 16th notes = " + str(self.note_rhythms[2]) + "\n")
            elif i == 1:
                f.write("  Number of 32th notes = " + str(self.note_rhythms[1]) + "\n")
            elif self.note_rhythms[i] > 0:
                f.write("  Number of " + str(i) + "x32th notes = " + str(self.note_rhythms[i]) + "\n")

        f.write("\n# Desired rhythmic distribution probabilities (step-based)\n")
        f.write("## Step > Multiples of 32th = Quantity // Comment \n")
        for i in range(len(self.rhythm_intervals_at_step)):
            if i < 10:
                if np.argmax(self.rhythm_intervals_at_step[i]) < 10:
                    f.write(str(i) + " \t> " + str(np.argmax(self.rhythm_intervals_at_step[i])) + " \t = 1 // " + self.Rhythms[np.argmax(self.rhythm_intervals_at_step[i])] + "\n")
                else:
                    f.write(str(i) + " \t> " + str(np.argmax(self.rhythm_intervals_at_step[i])) + "\t = 1 // " + self.Rhythms[np.argmax(self.rhythm_intervals_at_step[i])] + "\n")
            else:
                if np.argmax(self.rhythm_intervals_at_step[i]) < 10:
                    f.write(str(i) + "\t> " + str(np.argmax(self.rhythm_intervals_at_step[i])) + " \t = 1 // " + self.Rhythms[np.argmax(self.rhythm_intervals_at_step[i])] + "\n")
                else:
                    f.write(str(i) + "\t> " + str(np.argmax(self.rhythm_intervals_at_step[i])) + "\t = 1 // " + self.Rhythms[np.argmax(self.rhythm_intervals_at_step[i])] + "\n")
        f.close()

    def save_global_info(self, pitch_quantity_path, global_pitch_info):
        ''' Save global pitch followers info to a separate .md file '''
        if len(global_pitch_info) > 1:
            f = open(pitch_quantity_path, "wt", encoding="latin-1")
            f.write("# Global pitch distribution probabilities\n")
            f.write("## Pitch > Pitch-Follower = Quantity // Comment\n")
            for raw_pitch in self.RawPitch:
                for tag in self.RawPitch:
                    if tag == raw_pitch:
                        raw_pitch_name = tag.name            
                for pitch_follower in global_pitch_info[raw_pitch]:
                    for tag in self.Pitches:
                        if tag == pitch_follower.pitch:
                            pitch_follower_name = tag.name      
                    f.write(str(raw_pitch) + " \t> " + str(pitch_follower.pitch) + "\t = " + str(pitch_follower.quantity) + "\t // " + raw_pitch_name + " > " + pitch_follower_name + "\n")
            f.close()

    def merge_pitch_info(self, pitch_info1, pitch_info2):
        ''' Merge two pitch followers lists '''
        for raw_pitch1 in range(len(pitch_info1)):
            if len(pitch_info2) > 1:
                for pitch2 in range(len(pitch_info2[raw_pitch1])):
                    found = False
                    for pitch1 in range(len(pitch_info1[raw_pitch1])):
                        if pitch_info1[raw_pitch1][pitch1].pitch == pitch_info2[raw_pitch1][pitch2].pitch:
                            found = True
                            pitch_info1[raw_pitch1][pitch1].quantity += pitch_info2[raw_pitch1][pitch2].quantity
                    if not found:
                        pitch_info1[raw_pitch1].append(pitch_info2[raw_pitch1][pitch2])
        return pitch_info1
    
    pass