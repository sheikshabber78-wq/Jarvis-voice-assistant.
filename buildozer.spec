[app]

title = JARVIS V1

package.name = jarvisapp

package.domain = org.test

source.dir = .

source.include_exts = py,png,jpg,jpeg,kv,atlas

version = 1.0.0

requirements = python3,kivy,plyer,pyjnius

orientation = portrait

fullscreen = 0

android.permissions = INTERNET,RECORD_AUDIO,MODIFY_AUDIO_SETTINGS

android.api = 33

android.minapi = 21

android.ndk = 25b

android.accept_sdk_license = True

android.archs = arm64-v8a,armeabi-v7a

android.allow_backup = False

android.enable_androidx = True


[buildozer]

log_level = 2

warn_on_root = 1