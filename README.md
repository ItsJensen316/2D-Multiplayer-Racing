# APEX / Local Racing

A local two-player, top-down arcade racing game built with Python and Pygame.
Race on six circuits, use rechargeable boost, trade bumper-to-bumper contact,
and compete for saved lap and race records on one keyboard.

## Download and play

[![Download for Windows](https://img.shields.io/badge/Download-Windows_EXE-5865F2?style=for-the-badge&logo=windows&logoColor=white)](https://github.com/ItsJensen316/2D-Multiplayer-Racing/releases/latest/download/ApexRacing.exe)

Download **ApexRacing.exe**, save it anywhere convenient, and double-click to play.
No installation, Python, or separate asset files are required on compatible Windows PCs.
Both players use the same keyboard.

<!-- Replace YOUR_REPOSITORY above with this GitHub repository's exact name.
The download becomes available after ApexRacing.exe is uploaded to a published
GitHub Release marked as the latest release. Keep the asset filename unchanged. -->

![Main menu](docs/screenshots/menu.webp)

## Features

- Six circuits ordered from beginner to expert.
- Two players on one keyboard; configurable races from 1 to 99 laps.
- Shared fixed-step physics, acceleration, braking, reversing and steering.
- Car-to-car collisions, road boundaries and wall sliding.
- Rechargeable boost with separate meters for each player.
- Safe recovery with a time penalty and cooldown.
- Ordered checkpoints and direction-aware lap counting.
- Current, previous and best lap times, plus race results.
- Saved track records, including player-slot bests and race distances.
- Synthesized engine loops with pitch crossfades, tyre/brake sounds, impacts,
  countdown beeps, lap cues and a finish jingle. No audio downloads needed.
- Fading tyre marks, collision sparks and a start indicator.
- Pause, restart, track selection, results and audio settings.
- Resizable window, mouse/keyboard menus and saved volume/mute preferences.
- Silent play when an audio device is unavailable.

This is local multiplayer, with both players using the same computer.

## Screenshots

### Track selection

![Race setup and track difficulty](docs/screenshots/race-setup.webp)

### Racing

![Dockyard Run starting grid, timing HUD and boost meters](docs/screenshots/race.webp)

## Controls

### Driving

| Action | Player 1 | Player 2 |
| --- | --- | --- |
| Accelerate | Up arrow | W |
| Brake / reverse | Down arrow | S |
| Steer left / right | Left / Right arrows | A / D |
| Boost while accelerating | Hold Right Shift | Hold Left Shift |
| Recover | Enter | R |

### Menus and audio

| Action | Control |
| --- | --- |
| Pause / resume; back from other screens | Esc |
| Select a menu button | Tab, Shift+Tab, Up / Down |
| Activate selected button | Enter / Space, or mouse click |
| Change track on Race Setup | Q / E, or `<` / `>` buttons |
| Adjust laps on Race Setup | Left / Right arrows, or minus / plus buttons |
| Toggle mute | M |
| Lower volume | `[` |
| Raise volume | `]` |

In a race, Enter recovers Player 1; in menus, it activates a button.

## Circuits

| Circuit | Difficulty | Route |
| --- | --- | --- |
| Meadow Loop | 1/5 — Beginner | Wide lanes and sweeping corners |
| Club Circuit | 2/5 — Easy | Fast outer loop with an infield detour |
| Quarry Bend | 3/5 — Intermediate | Deep horseshoe and tightening bends |
| Classic Circuit | 3/5 — Intermediate | Long straight and a tight infield bend |
| Dockyard Run | 4/5 — Hard | Narrow bays and short straights |
| Ridge Switchbacks | 5/5 — Expert | Repeated hairpins and an S-bend |

## Race rules

Follow the arrows and pass every sector in order before crossing the finish line.
The race ends when a player completes the selected number of laps. Finishes on
the same simulation step count as a dead heat. A player who has not finished when
the winner crosses is marked DNF; completed laps can still qualify for lap records.

Boost lasts up to two seconds from a full charge and refills when released. A full
refill takes about 6.25 seconds. After emptying the meter, release and refill at
least 30% before boosting again. Boost is unavailable while braking or reversing.

Recovery places the car behind its last passed checkpoint, facing the route. It
only succeeds if there is a safe, unoccupied position. A successful recovery causes
a two-second stop while the clock continues and has a five-second cooldown. It
does not refill boost or advance checkpoints. Pausing stops the race and penalty
clocks; restarting resets the race.

## Run from source

Python 3.13 and Pygame 2.6.1 are the Windows setup used for this project. From the
folder containing `main.py`, run these commands in Command Prompt:

```bat
py -3.13 -m pip install -r requirements.txt
py -3.13 main.py
```

For IDLE, open `main.py` with IDLE 3.13 and press **F5**. Keep `racing/` and `data/`
next to `main.py`. Run the root entry point rather than `racing/app.py`.

## Build a Windows executable

Build on Windows, using the same Python installation that runs the game.
PyInstaller packages Python, Pygame and the game assets into a single executable.
Players do not need Python installed.

1. Extract the project to a writable folder and close the running game.
2. Open that folder in File Explorer, type `cmd` into the address bar and press Enter.
3. Install the build dependencies:

```bat
py -3.13 -m pip install -r requirements.txt
py -3.13 -m pip install --upgrade pyinstaller
```

4. Build the executable:

```bat
py -3.13 -m PyInstaller --noconfirm --clean --onefile --windowed --name ApexRacing --add-data "data:data" main.py
```

Alternatively, after installing the dependencies, double-click `build_windows.bat`.
It changes to the project folder and runs the same build command.

5. The result is **`dist/ApexRacing.exe`**. Copy it to another folder and test it.
   A one-file executable can be distributed by itself; no separate `data/` folder
   is needed. Its first startup can take a little longer while it unpacks.
6. Check all tracks, audio, boost/recovery, restart and saved records in the built
   executable. Close/reopen it to verify persistence.

`--add-data "data:data"` includes both the images and `data/tracks/circuits.json`.
The existing file-relative asset paths work with that bundle layout. No game
source changes are required. Use the root `main.py` as the entry point.

If a windowed build fails to launch, build a separate console version to see errors:

```bat
py -3.13 -m PyInstaller --noconfirm --clean --onefile --console --name ApexRacingDebug --add-data "data:data" main.py
```

Then run `dist\ApexRacingDebug.exe` from Command Prompt and inspect the error.

Generated `build/`, `dist/`, `.spec` and `__pycache__/` items do not belong in the
source repository. Distribute the executable as a release download, alongside
this README if desired. Keep the screenshot folder with the README when posting
the source project to GitHub.

Packaging references: [PyInstaller usage](https://pyinstaller.org/en/stable/usage.html)
and [bundled asset paths](https://pyinstaller.org/en/stable/runtime-information.html).

## Records and settings

Track records and audio preferences are saved automatically outside the game folder:

```text
Windows: %APPDATA%\ApexRacing\records.json
Linux:   ~/.local/share/apex-racing/records.json
```

On Windows, press **Win+R**, enter `%APPDATA%\ApexRacing`, and press Enter
to open the save folder. This normally resolves to
`C:\Users\<username>\AppData\Roaming\ApexRacing`.

`records.json` stores best lap times, race records, player-slot bests, volume
and mute preferences. It stores records rather than a complete history of every lap.
Saves belong to the current computer and Windows user; they do not travel with the
executable or sync online. To transfer them, close the game and copy `records.json`
to the same save folder on the other PC. Back it up before replacing an existing save.
Deleting this file while the game is closed resets records and audio preferences.

`XDG_DATA_HOME` is respected on Linux. `APEX_RACING_DATA_DIR` can override the
save location. Replacing the executable does not remove these records.

Race records are separated by track and lap count. P1/P2 refer to
keyboard slots, not named accounts. The first lap includes the standing start;
later laps are flying laps. Pausing does not add to lap times.

## Tests

```bat
py -3.13 -m unittest discover -s tests -v
```

The suite contains 37 automated checks for tracks, collisions, timing, persistence,
boost, recovery and audio behavior. Tests use temporary record folders and dummy
video/audio drivers. They do not replace testing the Windows executable or listening
on real speakers.

## Project layout

| Path | Purpose |
| --- | --- |
| `main.py` | Game entry point |
| `racing/` | Menus, simulation, tracks, records, effects and sound |
| `data/` | Images and circuit definitions |
| `docs/screenshots/` | Current README screenshots |
| `tests/` | Automated regression checks |
| `requirements.txt` | Runtime dependency |
| `build_windows.bat` | Windows packaging command |
| `.gitignore` | Excludes generated builds, caches and local files |
| `.gitattributes` | Consistent text line endings |

## Publish a Windows release

Keep the local build at `dist/ApexRacing.exe`. The `dist/` directory is ignored
by Git; distribute the executable through GitHub Releases.

1. Push the source project to GitHub.
2. Open the repository's **Releases** page and choose **Draft a new release**.
3. Create a version tag such as `v1.0.0` targeting `main`.
4. Give the release a title, then attach `dist/ApexRacing.exe` as a release asset.
5. Publish the release and ensure it is marked as the latest release.
6. Replace `YOUR_REPOSITORY` in the download button near the top of this README
   with the exact repository name.

The button links directly to the latest release's `ApexRacing.exe`. For future
releases, upload the executable with that same filename to keep the link working.

[GitHub release download links](https://docs.github.com/en/repositories/releasing-projects-on-github/linking-to-releases)
