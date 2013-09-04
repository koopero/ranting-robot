# I dislike ruby, as much as I like...
require 'aviglitch'

inFile = ARGV[0]
outFile = ARGV[1]
glitchStart = ARGV[2].to_f
glitchEnd = ARGV[3].to_f

a = AviGlitch.open inFile

frames = 0
a.glitch :keyframe do |fr|
  frames = frames + 1
end

a = AviGlitch.open inFile
frame = 0
a.glitch :keyframe do |fr|
	t = frame.to_f / frames.to_f
	frame = frame + 1
	glitch = glitchStart + ( glitchEnd - glitchStart ) * t
	glitch = Random.rand() < glitch 


	( glitch ? nil : fr ) 
end

a.output outFile

