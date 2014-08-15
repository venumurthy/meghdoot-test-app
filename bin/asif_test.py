from templatey import Generator
arguments = {
	'--help': False,
	'--version': False,
	'-a': 'setup_app.sh',
	'-b': 'setup_db.sh',
	'-i': '2'
}

print Generator().run(arguments)