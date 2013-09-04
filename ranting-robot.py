#!/usr/bin/env python

import urllib2
from urllib2 import urlopen
from urlparse import urlparse
from glob import glob
from time import sleep
import random
import sys
import os
import re
import json
import subprocess
import argparse
import tempfile

parser = argparse.ArgumentParser(description='Make a procedurely cut music video from random YouTube clips found on reddit. For further documentation, see https://github.com/koopero/ranting-robot/blob/master/README.md')

parser.add_argument('subreddits', nargs='+', help='Subreddit from which to grab videos. Example: video, youtubehaiku/new')
parser.add_argument('-m', required=True, help='Source for music. Either YouTube link or subreddit.')
parser.add_argument('-r', dest='resolution', help='Resolution of output. Format [width]x[height].', default='480x360')
parser.add_argument('-p', type=int, default=1, help='Number of pages to scrape for each video subreddit.')
parser.add_argument('-o', dest='outFile',default='rant.mp4',help='Output file.')
parser.add_argument('-t', type=float, default=0.8,help='aubioonset threshold.')
parser.add_argument('-us', dest='useSong', type=float, default=0.0,help='Percentage of cuts to song video.')
parser.add_argument('-l', type=int, default=300, help='Maxium duration of music, if picking from reddit.')
parser.add_argument('-fr', dest='frame_rate', type=float, default=29.97, help='Frame rate of output. Default: 29.97' )
parser.add_argument('-d', dest='directory', help='Working directory')

parser.add_argument('-j', dest='snapshot', help='Snapshot file, also metadata output.')
parser.add_argument('-s', dest='speed', type=float, default=1.0, help='Speed. 1 = 4 cuts per second average.')
parser.add_argument('-m0', dest='moshStart', type=float, default=0.0, help='Moshing at start' )
parser.add_argument('-m1', dest='moshEnd', type=float, default=0.1, help='Moshing at end' )
parser.add_argument('-vf', dest='youTubeFormat',default='18',help='YouTube format to download.')

parser.add_argument('-kv', dest='keepVideo', action='store_true', help="Don't delete video files.")
parser.add_argument('-ki', dest='keepImages', action='store_true', help="Don't delete image files.")
parser.add_argument('-v', dest='verbose', action='store_true', help='List commands being run.')
parser.add_argument('-q', dest='quiet', action='store_true', help='Stay quiet.')


args = parser.parse_args()

def dieWithError ( error ) :
	print >> sys.stderr, error
	exit( 1 )

#
# Ensure that resolution is alright.
#
if not re.match(r"(\d+)[xX](\d+)", args.resolution ) :
	dieWithError( "Resolution must be in format [width]x[height]" )

#
# Set up working directories and globs
#
if args.directory :
	workDir = args.directory
else :
	if args.keepVideo or args.keepImages :
		dieWithError ( "Must specify working directory if keeping video or images.")

	workDir = tempfile.mkdtemp()

imageDir = os.path.join ( workDir, 'frames' )
videoDir = os.path.join ( workDir, 'videos' )

def ensureDir ( dir ) :
	if not os.path.isdir( dir ) :
		os.makedirs( dir )


ensureDir( imageDir )
ensureDir( videoDir )

seqGlob = os.path.join( imageDir, 'yyz_?????.jpg' )
seqPattern = os.path.join( imageDir, 'yyz_%05d.jpg' )
outPattern = os.path.join( imageDir, 'yvr_%05d.jpg' )
outGlob = os.path.join( imageDir, 'yvr_?????.jpg' )


#
# Set up frame rate
#

frameRate = args.frame_rate
timePerFrame = 1.0 / frameRate

#
# Declare Video class and utility functions
#

DEVNULL = open ( os.devnull, 'w' )

def parseYouTubeLink ( url ) :
	parse = re.match(r".*?(v=|youtu\.be\/|\/v\/)([^\#\?&\"'>]+)", url )
	return parse

def log ( log ) :
	if not args.quiet :
		print >> sys.stderr, log

def command ( cmd ) :
	cmd = map( str, cmd )

	if args.verbose :
		print >> sys.stderr, ' '.join( cmd )

	return subprocess.check_output ( cmd, stderr=DEVNULL )



attribution = []

class Video :

	def __init__ ( self, info ) :
		if isinstance(info, basestring) :
			self.url = info
		else :
			self.url = info['url']


		parse = parseYouTubeLink( self.url )
		self.videoId = parse.group(2)
		self.cleanUrl = 'http://youtu.be/' + self.videoId

		self.attribution = {}
		self.attribution['url'] = self.cleanUrl

		if 'permalink' in info :
			self.attribution["reddit"] = 'http://reddit.com'+info['permalink']
			
		if 'title' in info :
			self.attribution['title'] = info['title']

		global attribution
		attribution.append ( self.attribution )
		self.attributionId = len(attribution) - 1
		




	def getFileName ( self, extension = 'mp4' ) :
		filename = self.videoId + '.' + extension
		filename = os.path.join ( videoDir, filename )
		return filename

	def getVideoFile ( self ) :

		if hasattr( self, 'error' ):
			return False

		filename = self.getFileName()
		if not os.path.isfile( filename ) :
			log ( "Downloading %s" % ( self.cleanUrl ) )
			command ( [
				'youtube-dl',
				self.cleanUrl,
				'-f', args.youTubeFormat,
				'-o', filename
				
			])

		return filename

	def getAudioFile ( self ) :
		video = self.getVideoFile()
		filename = self.getFileName( 'wav' )

		if video == False :
			return False

		if not os.path.isfile( filename ) :
			command ( [
				'ffmpeg',
				'-i', video,
				filename
			])
		return filename

	def getMeta ( self ) :
		if hasattr( self, 'meta' ) :
			return self.meta

		video = self.getVideoFile()

		if video == False :
			return False

		meta = command( [
			'ffprobe',
			'-i', video,
			'-show_format',
			'-print_format', 'json'
			])
		meta = json.loads( meta )
		self.meta = meta
		return meta

	def getDuration ( self ) :

		meta = self.getMeta ()

		if meta == False :
			return 0

		return float( meta['format']['duration'])

	def getCut ( self, duration ) :
		myDuration = self.getDuration ()
		if duration > myDuration or duration == 0 :
			return False

		return random.random() * ( myDuration - duration )

	def makeImageSequence ( self, start, length ) :
		video = self.getVideoFile()
		command ( [
			'ffmpeg',
			'-i', video,
			'-ss', str(start),
			'-t', str(length),
			'-an',
			'-r', str(frameRate),
			'-f', 'image2',
			'-q', '0',
			seqPattern
		])

	def deleteFiles ( self ) :
		for ext in [ 'mp4', 'wav' ] :
			filename = self.getFileName ( ext )
			if os.path.isfile( filename ) :
				os.remove( filename )


def getVideosFromReddit ( subreddit, pages = 1, after = False ) :
	url = 'http://www.reddit.com/r/'+subreddit+'.json'

	if after :
		url = url + '?after='+after

	
	tries = 15;
	while True :
		log( "Fetching %s" % ( url ) )
		try :
			reddit = json.load( urlopen( url ) )
			after = reddit['data']['after']
			videoListing = reddit['data']['children']
			break
		except urllib2.HTTPError as e :
			tries = tries - 1
			if tries == 0 :
				dieWithError( "HTTP error getting %s (reddit is under heavy load, I guess)" % ( url ) )
				exit(1)
			else :
				log( "Reddit choked. Retrying." )
				sleep(2 )


	ret = []

	for video in videoListing :
		video = video['data']
		url = video['url']

		if urlparse( url ).netloc not in ['www.youtube.com','youtube.com','youtu.be' ] :
			continue

		parse = parseYouTubeLink ( url )

		if not parse :
			continue

		ret.append ( Video ( video ) )

	if pages > 1 :
		ret = ret + getVideosFromReddit( subreddit, pages - 1, after )


	return ret


def pushSeq () :
	global frame

	seq = glob ( seqGlob );
	numFrames = 0
	for src in seq :
		dest = outPattern % ( frame )
		if os.path.isfile ( dest ) :
			os.unlink ( dest )

		os.rename ( src, dest )

		frame = frame + 1
		numFrames = numFrames + 1

	return numFrames

#
# Get song
#

if parseYouTubeLink( args.m ) :
	song = Video ( args.m )
else:
	# Pick a random song from reddit.
	songs = getVideosFromReddit ( args.m )

	while True :
		song = random.choice( songs )
		song.getAudioFile()

		if song.getDuration () > args.l :
			continue

		break




targetCuts = int( song.getDuration() * args.speed * 4 )

#
# Parse audio file to get cut information
#

threshold = args.t
while True :
	log ( 'Running beat detection with threshold %f' % ( threshold ) )
	cuts = command( [ 
		'aubioonset', 
		'-i', song.getAudioFile(),
		'-t', str(threshold) 
	] )
	cuts = cuts.split()
	cuts.append ( song.getDuration() )

	log ( "%d cuts from aubioonset ( want %d )" % ( len(cuts), targetCuts ) )

	if len(cuts) >= targetCuts or threshold < 0.1 :
		break

	threshold = threshold - 0.05





while len(cuts) > targetCuts :
	i = random.randrange( 0, len( cuts ) - 1 )
	cuts.pop( i )

log ( "%d cuts after trim" % ( len(cuts) ) )

#
#
#


#
# Get source video links
#
videos = []
log ( "Gettting videos")
for subreddit in args.subreddits :
	videos = videos + getVideosFromReddit ( subreddit, args.p )


frame = 1
totalFramesEst = int( frameRate * song.getDuration() )
time  = 0.0

edl = []


def saveSnapshot ( stage, frame = 0 ) :
	if args.snapshot :
		f = open( args.snapshot, 'w' )
		json.dump ( {
			"stage": stage,
			"frame": frame,
			"videos": attribution,
			"edl": edl
		}, f )
		f.close()

for cut in cuts :
	cut = float(cut)
	cutlength = cut - time

	if cutlength < timePerFrame :
		continue

	useSong = random.random() * 100.0 < args.useSong

	if useSong :
		video = song
		cutstart = time
	else :
		while True :
			videoId = random.randrange( 0, len( videos ) )
			video = videos[ videoId ]
			try :
				video.getVideoFile()
			except :
				log ( "Problem downloading %s ( won't try again ) " % ( video.cleanUrl ))
				videos.pop( videoId )
				continue

			cutstart = video.getCut ( cutlength )

			if cutstart != False :
				break

	log ( "Frame %d / %d" % ( frame, totalFramesEst ) )
	video.makeImageSequence( cutstart, cutlength )
	frames = pushSeq()
	
	cutlength = float( frames ) * timePerFrame

	edl.append( {
		"i": time,
		"o": time + cutlength,
		"t": cutstart,
		"a": video.attributionId
	} )

	time = time + cutlength

	saveSnapshot ( 'cut',frame )



#
# Resize frames and perform pixel-space effects.
#
mogrify = [
	'mogrify',
	'-resize', args.resolution + '^',
	'-gravity', 'center',
	'-extent', args.resolution
]

#mogrify = mogrify + ['-auto-level']

mogrify = mogrify + [ outGlob ]

command ( mogrify )

#
# Compile intermediary video video
#

aviFile = os.path.join ( imageDir, 'toMosh.avi' )


command ( [
	'ffmpeg',
	'-y',
	'-r', str( frameRate ),
	'-f', 'image2', '-i', outPattern,
	'-an', 
	'-vcodec', 'libxvid',
	aviFile
])

moshedFile = os.path.join ( imageDir, 'moshed.avi' )

command ( [
	'ruby',
	os.path.join( os.path.dirname(__file__), 'mosh.rb' ),
	aviFile,
	moshedFile,
	args.moshStart,
	args.moshEnd
])


def makeFinal ( base, extension ) :
	cmd = [
		'ffmpeg',
		'-y',
		'-i', moshedFile,
		'-i', song.getAudioFile()
	]

	# Put format specific conversion here


	cmd = cmd + [ base +'.'+extension ]
	command( cmd )

( dir, file ) = os.path.split( args.outFile )
( base, ext ) = os.path.splitext( file )
base = os.path.join( dir, base )

if not ext :
	makeFinal ( base, 'mp4' )
	makeFinal ( base, 'ogg' )
else :
	makeFinal ( base, ext )

#
#	Clean up
#
if not args.keepImages :
	for delete in glob(outGlob) :
		os.remove(delete)

if not args.keepVideo :
	for video in videos :
		video.deleteFiles()

def softRmDir ( dir ) :
	try :
		os.rmdir( dir )
	except :
		pass

softRmDir ( imageDir )
softRmDir ( videoDir )
softRmDir ( workDir )

