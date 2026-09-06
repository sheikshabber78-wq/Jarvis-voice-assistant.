[app]

title = JARVIS AI
package.name = jarvisapp
package.domain = org.test

source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas,json,txt,wav,mp3

version = 1.0

requirements = python3,kivy,plyer,pyjnius,android

orientation = portrait
fullscreen = 0

android.permissions = INTERNET,RECORD_AUDIO,MODIFY_AUDIO_SETTINGS

android.api = 33
android.minapi = 21
android.ndk = 25b

android.archs = arm64-v8a

android.accept_sdk_license = True

p4a.bootstrap = sdl2
p4a.branch = master

[buildozer]

log_level = 2
warn_on_root = 1
