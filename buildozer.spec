[app]

title = FileDrop
package.name = filedrop
package.domain = org.filedrop

source.dir = .
source.include_exts = py,png,jpg,kv,atlas

version = 1.0
requirements = python3,kivy

icon.filename = %(source.dir)s/icon.png
presplash.filename = %(source.dir)s/icon.png
presplash.color = #FF751F

orientation = portrait
fullscreen = 0

android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE
android.api = 33
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a,armeabi-v7a
android.allow_backup = True

[buildozer]

log_level = 2
warn_on_root = 1
