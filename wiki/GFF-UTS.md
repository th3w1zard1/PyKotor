# UTS (Sound)

Part of the [GFF File Format Documentation](GFF-File-Format).

UTS files define [sound object templates](GFF-File-Format#uts-sound) for ambient and environmental audio. These can be positional 3D sounds or global stereo sounds, with looping, randomization, and volume control.

**Official Bioware Documentation:** For the authoritative Bioware Aurora Engine Sound Object format specification, see [Bioware Aurora Sound Object Format](Bioware-Aurora-SoundObject).

**Reference**: [`Libraries/PyKotor/src/pykotor/resource/generics/uts.py`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/uts.py)

## Core Identity fields

| field | type | Description |
| ----- | ---- | ----------- |
| `TemplateResRef` | [ResRef](GFF-File-Format#gff-data-types) | Template identifier for this sound |
| `Tag` | [CExoString](GFF-File-Format#gff-data-types) | Unique tag for script references |
| `LocName` | [CExoLocString](GFF-File-Format#gff-data-types) | Sound name (unused) |
| `Comment` | [CExoString](GFF-File-Format#gff-data-types) | Developer comment/notes |

## Playback Control

| field | type | Description |
| ----- | ---- | ----------- |
| `Active` | Byte | Sound is currently active |
| `Continuous` | Byte | Sound plays continuously |
| `Looping` | Byte | Individual samples loop |
| `Positional` | Byte | Sound is 3D positional |
| `Random` | Byte | Randomly select from Sounds list |
| `Volume` | Byte | Volume level (0-127) |
| `VolumeVary` | Byte | Random volume variation |
| `PitchVary` | Byte | Random pitch variation |

## Timing & Interval

| field | type | Description |
| ----- | ---- | ----------- |
| `Interval` | Int | Delay between plays (seconds) |
| `IntervalVary` | Int | Random interval variation |
| `Times` | Int | Times to play (unused) |

**Playback Modes:**

- **Continuous**: Loops one sample indefinitely (machinery, hum)
- **Interval**: Plays samples with delays (birds, random creaks)
- **Random**: Picks different sample each time

## Positioning

| field | type | Description |
| ----- | ---- | ----------- |
| `Elevation` | Float | Height offset from ground |
| `MaxDistance` | Float | Distance where sound becomes inaudible |
| `MinDistance` | Float | Distance where sound is at full volume |
| `RandomPosition` | Byte | Randomize emitter position |
| `RandomRangeX` | Float | X-axis random range |
| `RandomRangeY` | Float | Y-axis random range |

**3D Audio:**

- **Positional=1**: Sound attenuates with distance and pans
- **Positional=0**: Global stereo sound (music, voiceover)
- **Min/Max Distance**: Controls falloff curve

## Sound List

| field | type | Description |
| ----- | ---- | ----------- |
| `Sounds` | List | List of [WAV](WAV-File-Format)/MP3 files to play |

**Sounds Struct fields:**

- `Sound` ([ResRef](GFF-File-Format#gff-data-types)): Audio file resource

**Randomization:**

- If `Random=1`, engine picks one sound from list each interval
- Allows for varied ambience (e.g., 5 different bird calls)
