import nltk
from g2p_en import G2p

# Make sure required model is downloaded
nltk.download('averaged_perceptron_tagger_eng')

texts = [
    "I have $250 in my pocket.",
    "popular pets, e.g. cats and dogs",
    "I refuse to collect the refuse around here.",
    "I'm an activationist."
]

g2p = G2p()
for text in texts:
    out = g2p(text)
    print(out)
