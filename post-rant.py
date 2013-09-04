import argparse
import datetime

parser = argparse.ArgumentParser(description='')

parser.add_argument('-r', dest='subreddit', default='TheRantingRobot',help='')
parser.add_argument('-u', dest='user', required=True,help='')
parser.add_argument('-p', dest='password', required=True,help='')
parser.add_argument('-id', dest='id')

args = parser.parse_args()


import jinja2

templateEngine = jinja2.Environment(loader=jinja2.FileSystemLoader('templates'))

def t ( template, context ) :
	tmplt = templateEngine.get_template( template )
	return tmplt.render( context )


import praw

r = praw.Reddit(user_agent='The Ranting Robot')

r.login(args.user, args.password )

submissions = r.get_subreddit(args.subreddit).get_top(limit=25)

for post in submissions :
	if str(post.author) == args.user : 
		continue

	break


if not post :
	exit()


videoSubreddits = [ 'amv' ]


rantId = datetime.datetime.now().strftime('%y%m%d%H%M')

rant = {}
rant['id'] = rantId
rant['musicPost'] = post
rant['musicTitle'] = post.title
rant['videoSubreddits'] = videoSubreddits

'''
cmd = [
	os.path.join( os.path.dirname(__file__), 'ranting-robot.py' ),
	'-m', post.url,
	'-o', f(rantId),
	'-d', f('tmp')
]
cmd = cmd + rant['videoSubreddits']

'''





#startComment = post.add_comment ( t('startProcessComment', rant ) )


print rant

print t('rantTitle', rant )



