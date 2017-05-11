# Detecting Diachronic Meaning Shifts in Dutch
This is the source code for the work presented in the [CLIN](http://www.ccl.kuleuven.be/CLIN27) talk _''Can we spot meaning shifts in diachronic representations?''_ ([abstract](http://www.ccl.kuleuven.be/CLIN27/abstracts.html#Abstract01) | [slides](http://www.let.rug.nl/haagsma/papers/clin2017slides.pdf))

You can use this code to create diachronic meaning representations based on any significantly large diachronic corpus of Dutch, and investigate and analyse those representations to detect known meaning shifts. 

## Requirements 
To run this code, you'll need:
* Python 2.7.6
* gensim 0.13.2
* scipy 0.18.1
* matplotlib 2.0.0

Different versions might work just as well, but cannot be guaranteed. Most scripts also expect there to be a folder called `working` in the main code directory.

In addition, we made use of:
* The [Elephant](https://github.com/ParallelMeaningBank/elephant) tokenizer
* The [LASSY](https://www.let.rug.nl/vannoord/Lassy/) Small corpus 

## Contact
E-mail me at hessel.haagsma@rug.nl
