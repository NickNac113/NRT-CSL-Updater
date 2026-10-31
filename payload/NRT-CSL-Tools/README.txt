NRT CSL VERIFICATION TOOLS

Install this folder alongside your existing NRT CSL or CSL folder.
Double-click Verify-NRT-CSL.cmd on Windows to check your installed assets.
The command prints PASS or lists missing/changed files; it makes no changes.

For another location:
powershell.exe -NoProfile -File Verify-NRT-CSL.ps1 -PackageRoot "D:\Path\NRT_CSL"

The public SkunkCrafts feed updates these tools only. It cannot repair or
download aircraft models and textures. Use your separately supplied full
NRT CSL package for those files.

A SkunkCrafts update leaves aircraft assets, variant selections and other
local files alone. Check/update while X-Plane is closed. Use the current
standalone updater, with Add folder... if your package lives outside X-Plane.

Project: https://github.com/NickNac113/NRT-CSL-Updater
