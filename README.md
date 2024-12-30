# Web Crawler Phrases Extractor
## Description
A crawler and scraper tool I made to extract 1, 2, 3 and 4-word long phrases from websites given a starting URL. The tool is not very polished, not super customizable, and presumably contains loads of bugs, but it works for the purpose I built it for.

### Purpose of tool
I made a hash cracking challenge for which I (naievly) thought the only solution was constructing a custom wordlist by manually grabbing seemingly interesting phrases on a wiki. It turns out someone solved the challenge with automation and programming, which was super inspiring to see. So I built my own tool which could solve the challenge. Mostly (it is able to crack 7/8 hashes, the final hash requires a rules file or similar which removes the final dot (`.`) of a certain 3-word phrase). Included in this repo are the original Argon `hashes.txt` as well as a more convenient MD5 verion `md5_hashes.txt` as well as a very basic list of rules `john.rules` which will crack the final hash.


## Usage
1. `pip install -r requirements.txt`
2. `python scraper.py`
3. The tool will crawl <https://cry-of-fear.fandom.com> and then extract phrases from the various pages it finds within the scope. This takes about 2 minutes on my machine. It then generates four wordlists called `1_words.txt`, `2_words.txt` etc. which you can use to try to crack the hashes like such: `hashcat -a 0 -m 0 md5_hashes.txt 1_words.txt --potfile-disable`.<br>

You have some customizability options in the form of global variables at the start of `scraper.py` but you can also leave everything as is and it will work.
