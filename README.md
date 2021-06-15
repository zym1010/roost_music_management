# roost_music_management
a music management frontend for CLI-enabled music players

## Goal

The goal of this project is NOT to reinvent the wheel and create a new music player like Audirvana, Roon, or iTunes; instead, this project tries to do a better job on **library management** than others and **delegate** the actual music playing to other players

## Some pain points of existing music players on library management

### Audirvana 3.5

* Random track duplication --- https://community.audirvana.com/t/duplicate-tracks-3-5/8052
* No true support of multi artists --- https://community.audirvana.com/t/poor-handling-of-flac-multiple-same-field-tags/20752
* Otherwise it's a great player with iOS support.

### iTunes (Music in Mac OS Catalina+)

* Artwork occasionally get lost --- https://forums.macrumors.com/threads/solutions-to-missing-album-art-in-catalina-music-app.2226353/
* Inconsisent file naming --- for example, a track with title "Star: Deluxe Edition" and track number 5 of disc 2 might be named as one of the following, somehow randomly.
	* `2-05 Star_ Deluxe Edition.m4a`
	* `05 Star_ Deluxe Edition.m4a`
	* `05 - Star_ Deluxe Edition.m4a`
	* `05 - Star： Deluxe Edition.m4a` (yes a full-width comma)
	* and so on.
* Improper handling of files of super long title. For example, a track with 250 or so characeters in the title might have an extension `.m` with the `4a` part trunacted off -- this can be a serious issue for some classical music tracks.
* No multi-artist support.

### Roon

It's a well-rounded software; it's just packed with too many features I don't necessarily value and overly complex.
