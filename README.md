# VideoCutter

Copyright (C) 2022 Julien Férard <https://github.com/jferard>

A woodcutter video editing tool.

Under GPL v3.

## Summary

Small piece of Python code using VOSK Offline Speech Recognition
API (https://alphacephei.com/vosk/) to edit a video using its text transcription.

* *Step 1* extract the text of a video:

```
video_cutter$ python3 main.py -e fixture/Distance_d_un_point_a_une_droite_dans_le_plan.theora.ogv.480p.webm 
LOG (VoskAPI:ReadDataFiles():model.cc:213) Decoding params beam=13 max-active=7000 lattice-beam=6
...
LOG (VoskAPI:ReadDataFiles():model.cc:312) Loading CARPA model from models/fr/rescore/G.carpa
Please edit file fixture/Distance_d_un_point_a_une_droite_dans_le_plan.theora.ogv.480p.txt before assembling.
```

* *Step 2* remove uninteresting lines of the video in the text file

```
video_cutter$ nano fixture/Distance_d_un_point_a_une_droite_dans_le_plan.theora.ogv.480p.txt.
```

* *Step 3* assemble the remainder into a new video:

```
video_cutter$ python3 main.py -a fixture/Distance_d_un_point_a_une_droite_dans_le_plan.theora.ogv.480p.webm 
```

## Installation

```bash
sudo apt install ffmpeg
sudo python3 -m pip install vosk
wget https://alphacephei.com/vosk/models/vosk-model-fr-0.6-linto-2.2.0.zip
mkdir -p models/fr
unzip vosk-model-fr-0.6-linto-2.2.0.zip
mv vosk-model-fr-0.6-linto-2.2.0/* models/fr
```

## Notes

The example comes from: 
https://commons.wikimedia.org/wiki/File:Distance_d%27un_point_%C3%A0_une_droite_dans_le_plan.theora.ogv

Nicostella, CC BY-SA 3.0 <https://creativecommons.org/licenses/by-sa/3.0>, via

Wikimedia Commons.