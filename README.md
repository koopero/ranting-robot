ranting-robot
=============

The Ranting Robot, a simple application that uses YouTube &amp; Reddit to create insane, randomly generated music videos. 

# Installation

For The Ranting Robot to do its job, the following applications must be installed and available at the command line:

* [youtube-dl](http://rg3.github.io/youtube-dl/)
* [ffmpeg](http://ffmpeg.org)
* [ffprobe](http://ffmpeg.org/ffprobe.html)
* [aubioonset](http://aubio.org/aubioonset.html)
* [mogrify](http://www.imagemagick.org/script/mogrify.php) ( from [ImageMagick](http://www.imagemagick.org/) )

To install these lovely tools, it should be sufficient to run something like this:

	sudo port install ffmpeg youtube-dl aubio imagemagick
	sudo youtube-dl -U
	