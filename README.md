# NRT CSL Updater Tools

Public SkunkCrafts update feed and verification tools for the NRT Silver Charcoal CSL collection.

**This repository distributes tools only.** Install your separately supplied NRT CSL collection first. Aircraft models, textures, paint kits and complete livery packages are not published here. This feed cannot download or repair those assets.

## Set up updates

1. Use the current [SkunkCrafts standalone updater](https://updater.skunkcrafts.com/).
2. Download this repository with **Code > Download ZIP** and extract it.
3. Copy the contents of `updates/stable` into the root of your existing NRT CSL package, alongside its `NRT CSL` or `CSL` folder. You need `skunkcrafts_updater.cfg`, `NRT-CSL-Tools`, and `changelog.txt`; the three remote file-list files may be omitted locally.
4. Place the NRT package directly beneath `X-Plane 12/Resources/plugins`, or use **Add folder...** in SkunkCrafts 4 to select its current location.
5. In SkunkCrafts select **NRT CSL Verification Tools** and check/update it. A repair affects only the published tool files.
6. Run `NRT-CSL-Tools/Verify-NRT-CSL.cmd` to check your locally installed models and textures.

The checker supports the 27 type-code folders from the NRT v02/v03 collection, with 52 prepared paint variants. It accepts the supplied alternate matching files. A damaged asset is reported with its path; it is not silently replaced. Copy a verified full package again if asset repair is required.

The older in-simulator updater is not the target of this integration. The current standalone client can manage a package outside the simulator when added by folder. See the [official publishing guide](https://updater.skunkcrafts.com/PUBLISHING.html).

## Public feed

`https://raw.githubusercontent.com/NickNac113/NRT-CSL-Updater/main/updates/stable/`

The feed lists only the NRT-CSL-Tools files and changelog. Its deletion list is empty. Configuration, variant choices and aircraft files are outside the managed file list. The public integrity catalog contains filenames and hashes, not aircraft data.

## Publish a tools update

1. Edit files under `payload/` and bump `version` in `release.json`.
2. Run `python tools/build_feed.py`.
3. Run `python -m unittest discover -s tests -v`, `python tools/build_feed.py --check`, and `python tools/check_public_scope.py`.
4. Commit the source, metadata and generated `updates/stable` files together, then push `main`. Publishing a single commit keeps the feed revision together.

For a starter ZIP, run `python tools/build_feed.py --zip /path/to/NRT_CSL_Updater_Tools.zip`. Extract that ZIP directly into the existing NRT package root.

The publication checks reject aircraft assets and require the exact tools-only file allowlist. Do not add complete CSL packages or third-party source assets to this repository. Adding aircraft downloads later requires a separate hosting and permissions decision.

## License

The updater tools are MIT licensed. Aircraft assets retain their original authors' terms and are not licensed or distributed by this repository.
