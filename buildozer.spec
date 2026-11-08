[app]

title = KHUSHBO
package.name = khushbo
package.domain = org.afaq

source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas,ttf,wav,mp3,json

version = 1.0

requirements = python3,kivy,requests,pyjnius

orientation = portrait
fullscreen = 0

android.permissions = INTERNET,CAMERA,RECORD_AUDIO

android.api = 34
android.minapi = 23
android.ndk = 25b

android.archs = arm64-v8a

android.accept_sdk_license = True

p4a.bootstrap = sdl2

[buildozer]

log_level = 2
warn_on_root = 1
