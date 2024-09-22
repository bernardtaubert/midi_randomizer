'''
This script converts midi files to an array and back.
The input midi must be quantized and 8 bars long.
Furthermore the input midi must be monophonic and transposed to C Major.

Optionally, it can randomize the MIDI files to create new melodies.
The goal is to create guitar or synth lead riffs.

'''

import os
import argparse
import numpy as np
import midi_util
from mido import MidiFile


DEBUG = True


if __name__ == "__main__":

    util = midi_util.Midi_Util()

    global_pitch_info = []
    global_pitch_info.append ([]) # followers of C
    global_pitch_info.append ([]) # followers of Cis
    global_pitch_info.append ([]) # followers of D
    global_pitch_info.append ([]) # followers of Dis
    global_pitch_info.append ([]) # followers of E
    global_pitch_info.append ([]) # followers of F
    global_pitch_info.append ([]) # followers of Fis
    global_pitch_info.append ([]) # followers of G
    global_pitch_info.append ([]) # followers of Gis
    global_pitch_info.append ([]) # followers of A
    global_pitch_info.append ([]) # followers of Ais
    global_pitch_info.append ([]) # followers of B    

    # Argument parsing
    parser = argparse.ArgumentParser(
        description='Save a directory of MIDI files as arrays and back. \
                     The input midi must be quantized and 8 bars long. \
                     Furthermore the input midi must be monophonic and transposed to C Major. \
                     Optionally, it can randomize the MIDI files to create new melodies. \
                     The goal is to create guitar or synth lead riffs.')
    parser.add_argument('path', help='Input path', default='')
    parser.add_argument(
        '--lock-steps',
        dest='lock_steps',
        action='store_true',
        help='lock certain steps specified by the lock_steps.md file')    
    parser.add_argument(
        '--use-cached',
        dest='use_cached',
        action='store_true',
        help='use cached instead of overwriting existing files')
    parser.add_argument(
        '--quantization',
        default=5,
        help='defines a 1/2**quantization note quantization grid')    
    parser.add_argument(
        '--amount',
        dest='amount',
        default=1,
        help='create a certain amount of variations')
    parser.add_argument(
        '--random-notes',
        dest='random_notes',
        default=0,
        help='0 = no random (default), 1 file random followers, 2 C major random between C5 and C6, 3 file random followers by (pitch-)quantity.md') # file random means that if a C is followed by a D in the file, then this sequence(s) might be randomly applied to other steps, while random followers by quantity means that the probability of certain notes is controlled by the pitch-quantity.md file. Please keep in mind that every occuring raw_pitch note event needs a pitch follower otherwise you get a index out of bounds.
    parser.add_argument(
        '--random-rhythm',
        dest='random_rhythm',        
        default=0,
        help='0 = no random (default), 1 file random, 2 file random by (rhythm-)quantity.md (step-based)') # file random means that only the rhythm timing in the file are used but are put into different order, while step-based means that the rhythm randomization at each step is controlled by the rhythm-quantity.md file.
    parser.add_argument(
        '--note-min',
        dest='note_min',
        default=0,
        help='0 = no note minimum, > 0 any notes lower than the minimum will be transposed up by 1 octave') # ensures that the randomly created notes wont get too low
    parser.add_argument(
        '--note-max',
        dest='note_max',
        default=127,
        help='127 = no note maximum, < 127 any notes higher than the maximum will be transposed down by 1 octave') # ensures that the randomly created notes wont get too high
    parser.add_argument(
        '--transpose-algorithm',
        dest='transpose_algorithm',
        default=0,
        help='0 = no transpose, 1 transpose by -1 octave when followed by same, 2 random transpose notes by +1 octave, 3 random transpose notes by -1 octave, 4 random transpose notes by +-1 octave') # widens the pattern
    parser.add_argument(
        '--transpose-probability',
        dest='transpose_probability',
        default=0,
        help='0 = no transpose, 1 = transpose on every note event')
    parser.add_argument(
        '--transpose-same',
        dest='transpose_same',
        action='store_true',
        help='always transpose notes that are followed by the same note')
    parser.set_defaults(use_cached=False)
    parser.set_defaults(transpose_same=False)
    args = parser.parse_args()

    # Get paths
    MIDI_IN_PATH = 'midi_in'
    path_prefix, path_suffix = os.path.split(args.path)
    if args.path == '' or args.path == MIDI_IN_PATH:
        if len(path_suffix) == 0: # Handle case where a trailing / requires two splits.
            path_prefix, path_suffix = os.path.split(path_prefix)
    else:
        path_prefix = ''
    base_path_out_pitch_quantity = os.path.join(path_prefix, 'pitch_quantity')
    base_path_out_rhythm_quantity = os.path.join(path_prefix, 'rhythm_quantity')
    base_path_out_lock_steps = os.path.join(path_prefix, 'lock_steps')
    base_path_out_arrays = os.path.join(path_prefix, 'array')
    base_path_out_midi_out = os.path.join(path_prefix, 'midi_out')

    for root, dirs, files in os.walk(args.path):
        if 'archive' in root: # skip files in the 'archive'
            continue
        for file in files:
            if '.mid' in file and file.split('.')[-1] == 'mid':
                print (os.path.join(root, file))

                # Get output file path
                if (args.path == '' or args.path == 'midi_in'):
                    suffix = root.split(args.path)[-1]
                else:
                    suffix = path_suffix.split(MIDI_IN_PATH)[-1]
                out_dir_arrays = base_path_out_arrays + '/' + suffix
                out_dir_midi_out = base_path_out_midi_out + '/' + suffix

                # Create the array file
                out_file_array = '{}.npy'.format(os.path.join(out_dir_arrays, file)) # Get output path + filename of the array
                if not args.use_cached: 

                    # Read Midi file
                    mid = MidiFile(os.path.join(root,file))

                    time_sig_msgs = [ msg for msg in mid.tracks[0] if msg.type == 'time_signature' ]
                    if len(time_sig_msgs) == 1:
                        time_sig = time_sig_msgs[0]
                        if not (time_sig.numerator == 4 and time_sig.denominator == 4):
                            print ('Time signature not 4/4. Skipping...')
                            continue
                    else:
                        print ('No time signature. Skipping...')
                        continue

                    array = util.midi_to_array(mid, args.quantization) # get the midi 'step array'

                    if not os.path.exists(out_dir_arrays):
                        os.makedirs(out_dir_arrays)                
                    if not os.path.exists(out_dir_midi_out):
                        os.makedirs(out_dir_midi_out)

                    np.save(out_file_array, array) # Write or 'Save' the array to the out_file
                elif os.path.exists(out_file_array):
                    array = np.load(out_file_array) # load the cached file
                else:
                    print ("Error: File " + out_file_array + " not found.")

                # Get output file path and save info to .md files
                if (args.path == '' or args.path == 'midi_in'):
                    suffix = root.split(args.path)[-1]
                else:
                    suffix = path_suffix.split(MIDI_IN_PATH)[-1]
                out_dir_pitch_quantity = base_path_out_pitch_quantity + '/' + suffix
                out_dir_rhythm_quantity = base_path_out_rhythm_quantity + '/' + suffix
                out_dir_lock_steps = base_path_out_lock_steps + '/' + suffix

                # Calculate midi info such as pitches and rhythms
                if not args.use_cached:
                    if not os.path.exists(out_dir_pitch_quantity):
                        os.makedirs(out_dir_pitch_quantity)            
                    if not os.path.exists(out_dir_rhythm_quantity):
                        os.makedirs(out_dir_rhythm_quantity)
                    if not os.path.exists(out_dir_lock_steps):
                        os.makedirs(out_dir_lock_steps)

                    util.__init__()
                    pitch_info = util.calc_pitch_followers(array)
                    util.calc_rhythm_intervals(array)

                    global_pitch_info = util.merge_pitch_info(global_pitch_info, pitch_info)

                    util.save_info(os.path.join(out_dir_pitch_quantity,file).replace(".mid",".md"), os.path.join(out_dir_rhythm_quantity,file).replace(".mid",".md"))

                # Load info from cached files
                elif args.use_cached and os.path.exists(os.path.join(out_dir_pitch_quantity,file).replace(".mid",".md")) and os.path.exists(out_dir_rhythm_quantity):
                    # Info will be loaded in the 'for loop' below
                    #util.load_info(os.path.join(out_dir_pitch_quantity,file).replace(".mid",".md"), os.path.join(out_dir_rhythm_quantity,file).replace(".mid",".md"))
                    pass

                for i in range(int(args.amount)):
                    print()      
                    util.__init__()           
                    util.load_info(os.path.join(out_dir_pitch_quantity,file).replace(".mid",".md"), os.path.join(out_dir_rhythm_quantity,file).replace(".mid",".md"))
                    if args.lock_steps and os.path.join(out_dir_lock_steps,file).replace(".mid",".md"):
                        util.load_locks(os.path.join(out_dir_lock_steps,file).replace(".mid",".md"))                                   
                    temp_array = util.notes_random_pitch_followers(array, float(args.random_notes))
                    temp_array = util.notes_transpose (temp_array, float(args.transpose_algorithm), float(args.transpose_probability), args.transpose_same) # potentially correct notes that are followed by the same note by octaving them
                    temp_array = util.notes_to_min_max (temp_array, int(args.note_min), int(args.note_max))
                    temp_array = util.notes_random_rhythm_intervals(temp_array, float(args.random_rhythm))
                    print()

                    if DEBUG:
                        util.print_array_notes(temp_array)
                        util.print_pitch_followers(util.RawPitch.A)
                        util.print_rhythm_info()

                    mid = util.array_to_midi (temp_array, "Track1")
                    output_file = file.split('.')
                    output_file = output_file[0:len(output_file)-1]
                    mid.save(os.path.join(out_dir_midi_out, "".join(output_file) + str(i+1) + ".mid"))

    # Save global info
    util.save_global_info(os.path.join(base_path_out_pitch_quantity,"global_pitch_quantity.md"), global_pitch_info)
