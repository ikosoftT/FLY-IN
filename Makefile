PYTHON = python3
PIP = pip 

run:
	$(PYTHON) main.py

install:
	$(PIP) install -r requirements.txt

debbug:
	$(PYTHON) -m pdb main.py

clean:
	find . -type d -name "__pycache__" -exec {rm -rf} 
	find . -type d -name "__mypy__"  -exec {rm -rf} 
