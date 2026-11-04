# game_player characters

The player's rhythm performer supports a Spine character or an XML TextureAtlas.
The rival and seated spectator keep their existing built-in characters.

## Importing

The installed engine does **not** expose raw XML/file reading or an asset-import
hook to CSL. A project-side import step is therefore required; dropping files
alone is not supported by this engine version.

From the project directory run:

```
python tools/import_game_player.py
```

Or keep `python tools/import_game_player.py --watch` running in your development
terminal to regenerate metadata when files change. This tool only edits generated
game metadata; it never starts/stops the editor or changes engine APIs. After an
import, compile and restart the **game** to rebuild character instances (hotload
does not replay startup). Include the generated CSL in the published project;
players do not need Python.

## Selection and playback

- Any `.spine` in this folder takes priority and uses the existing Spine renderer.
- Otherwise an XML atlas is selected. `character.*` is preferred, then `player.*`,
  then the alphabetically first candidate. One default character is selected.
- To use XML, remove/move the existing `player.spine` out of this folder first.
- XML `imagePath` resolves relative to the XML file; if omitted the matching PNG
  filename is used. Texture paths must stay inside `res`.
- No `.spine` or `.atlas` is generated/required for XML characters. Quads sample
  the original PNG at the XML coordinates.
- Trailing decimal digits are stripped to form animation names. Numeric frame
  suffixes determine playback order (so 2 precedes 10). Unnumbered names are
  single-frame animations. All animation names are preserved exactly.
- `frameX/Y` restore trimmed placement within `frameWidth/Height`. Missing trim
  attributes default to zero offset and source width/height.
- Default playback is 24 fps, scaled by the song's animation speed. The rhythm
  controller selects `Idle`/`idle` and `singLEFT/DOWN/UP/RIGHT` or `Left/Down/Up/Right`
  when present, falling back to the first animation. Arbitrary animations can
  be played through `Game_Player_Character.play("Exact name", loop=true)`.
- XML artwork uses 240 pixels per world unit and an untrimmed bottom-center pivot.
  Atlas characters keep their authored artwork rather than stock bone-based
  mouth/microphone overlays. Rotated packed frames are explicitly rejected.

Importer errors identify malformed XML, missing PNGs and invalid frame bounds.
Importer and runtime logs list discovered animations and frame counts. Failed
imports return a nonzero exit code and leave the last good generated file intact;
fix the input before publishing. The watcher retries on the next file change.

Tests: `python -m unittest discover -s tests -p "test_game_player_import.py"`

Validation: nine importer tests passed. CSL compilation succeeded with both the
default Spine metadata and XML-generated animation/frame metadata. Asset
diagnostics are clean after removing an empty nested placeholder text asset.
The connection timeout resolved on a subsequent test. A temporary XML fixture
loaded in a connected client with `active: true`, a loaded Texture_Asset, three
Idle frames, and an advancing animation clock; server/client error logs were
empty. The original Spine selection was restored and the fixture removed.
Full visual playback verification remains outstanding: the live world view
showed a blue grid rather than the stage/performers. The project compiles and
all 7609 assets validate after cleanup. The default player rig now uses the
built-in character, so removing player.spine for an XML character does not
leave a broken scene-config asset reference.
