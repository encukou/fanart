
serve-devel:
	pserve --reload development.ini

diff-requirements:
	colordiff -U3 <(cat *requirements.txt) <(pip freeze -r <(cat *requirements.txt))
