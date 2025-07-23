import eng_to_ipa as ipa

#text = "The curious boy saw a white goat chewing a toy near the blue fire outside the hall and ran after it in fear, loudly uttering a bitter oath."
text = 'good morning. How are you'


# text = """The old lighthouse keeper had warned her about the storms that came without warning, 
# how they could turn the placid bay into a churning cauldron of white-capped fury in mere minutes. 
# But Sarah had lived by the ocean her entire life, had watched its moods shift like a temperamental child, 
# and she thought she understood its rhythms.
# She was wrong.
# The first drops began as she rounded the rocky outcropping that sheltered the small cove 
# where her father's fishing boat lay anchored. What had been a gentle breeze that morning now howled 
# through the pine trees that clung precariously to the cliff face above, 
# their branches whipping back and forth like desperate arms reaching for salvation. 
# The sky, which had been the color of faded denim just an hour before, 
# now bore the ominous purple-black bruises of an approaching tempest.
# Sarah quickened her pace along the narrow path that wound down to the water's edge. 
# Her grandmother's worn leather satchel bounced against her hip with each hurried step, 
# the glass jars inside clinking together like wind chimes in a gale. 
# She had promised to gather kelp and sea lettuce for the old woman's arthritis remedy, 
# but now she wondered if she would make it back to the cottage before the storm unleashed its full fury.
# The waves were already beginning to crash against the barnacle-encrusted rocks with increasing violence, 
# sending sprays of salt water high into the air where they mingled with the first fat raindrops. 
# In the distance, she could see her father's boat straining against its anchor line, 
# the small vessel bucking and rolling like a wild horse trying to break free from its tether."""


phonemes = ipa.convert(text)
print(phonemes)  # Output: hɛloʊ wɜrld

