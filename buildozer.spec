[app]

title = JARVIS V1
package.name = jarvisapp
package.domain = org.test

source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas

version = 0.4

requirements = python3,kivy,plyer,pyjnius

orientation = portrait
fullscreen = 0

android.permissions = INTERNET,RECORD_AUDIO

android.api = 33
android.minapi = 21
android.ndk = 25b


[buildozer]

log_level = 2
warn_on_root = 1