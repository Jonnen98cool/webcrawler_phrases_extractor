import requests
from bs4 import BeautifulSoup, SoupStrainer


#NOTE: Without a simple rule list (in this case stripping all dots), the phrase "Sony Ericsson W610i" does not get cracked. It's found on the page but it has a dot at the end.


#TODO: Still there are newlines making their way into the final wordlists. eleiminate.
#   - looking at 4-word results from soderkulla.se, there are still some 1 and 2-word results mixed in.
#TODO: There are links on 404 pages, leading



ROOT_URL = "https://cry-of-fear.fandom.com/"   #NOTE: this is the webroot, so all relative paths go from this.
#ROOT_URL = "https://crawler-test.com/"
IN_SCOPE = "https://cry-of-fear.fandom.com/wiki"      #TODO: Is this always the same as the root diredtory?
OUT_OF_SCOPE = ["/Special:Log"] #NOTE: This list is relative to the IN_SCOPE value and needs to be custom-edited for each site.

INCLUDE_TAGS = ["p", "big", "small","span", "b", "strong", "i", "em", "mark", "del", "ins", "sub", "sup", "h1", "h2", "h3", "h4", "h5", "h6", "blockquote", "q", "code", "li", "dt", "dd"] #TODO: manually add more "text" elements to analyze here
STRIP_CHARS = ["\n", "\r", "\t"]


DISALLOWED_FILE_EXTENSIONS = [".wav", ".ogg", ".png", ".jpg", ".jpeg", ".webp", ".mp3", ".mp4"] #TODO: I want to make a whitelist instead, but then how would I allow no file extension? Instead, this solution requires user to manually modify the blacklist.
LINK_NR = 0
STOP_AFTER_X_LINKS = 3000
SITE_LINKS = [] #Dynamically filled with all links/pages on the site



def scrape_site(URL:str):
    res = requests.get(URL)
    #print(res.text)     #This is the entire HTTP response with all HTML
    soup = BeautifulSoup(res.text, "html.parser")   #Soup object

    site_contents = []   #2D list containing lists of the text contents of the various HTML elements such as <p>, <span> etc
    for i, tag in enumerate(INCLUDE_TAGS):
        tag_contents = []
        for j, element in enumerate(soup.find_all(tag)):
            stripped_string = element.text  # Get the text from the HTML tag (similar to innerHTML)
            for c in STRIP_CHARS:           #Strip unwanted characters from the string
                stripped_string = stripped_string.replace(c, "")
            tag_contents.append(stripped_string)
        site_contents.append(tag_contents)


    return site_contents



def to_wordlist(site_content, phrase_length:int, delimiter:str=' ') -> [str]:
    wordlist = []
    for tag_content in site_content:
        for phrase in tag_content:

            nr_of_words = phrase.count(delimiter) + 1   #I can see this NOT being a robust way of achieving what I wan
            delimiter_indexes = [index for index, char in enumerate(phrase) if(char == delimiter)]
            word_separator_indexes = [0] + delimiter_indexes + [len(phrase) - 1]    #Add index 0 and final index

            if(nr_of_words >= phrase_length):
                for i in range(nr_of_words - phrase_length + 1):
                    if(i == 0 and nr_of_words == phrase_length): 
                        wordlist.append(phrase[word_separator_indexes[i] + 0 : word_separator_indexes[i+phrase_length] + 1])
                    elif(i == 0 and nr_of_words != phrase_length):
                        wordlist.append(phrase[word_separator_indexes[i] + 0 : word_separator_indexes[i+phrase_length] + 0])
                    elif(i == nr_of_words - phrase_length):
                        wordlist.append(phrase[word_separator_indexes[i] + 1 : word_separator_indexes[i+phrase_length] + 1])
                    else:
                        wordlist.append(phrase[word_separator_indexes[i] + 1 : word_separator_indexes[i+phrase_length] + 0])

        #print(f"DEBUG: current wordlist: {wordlist}")
    wordlist = list(set(wordlist))
    #return "\n".join(wordlist)
    return wordlist



def write_wordlist(name:str, content:str):
    # Write to file
    try:
        wordlist = open(name, "w")
    except Exception as e:
        print(f"ERROR: could not open file for writing, exception:\n{e}")
    else:
        wordlist.write(content)
        wordlist.close()
        print(f"INFO: wrote contents to \"{name}\"")



#Given a URL, gather all href's from it and visit each URL if it hasn't already been visited. Recursive.
#NOTE: one commented-out href on CoF wiki start page literally looks like this:   href="//cry-of-fear.fandom.com"  (it's not a bug in your program)
#TODO: why does /register get included, it doesn't start with with /wiki
def build_sitemap(URL:str, link_nr:int):
    global LINK_NR
    if(LINK_NR >= STOP_AFTER_X_LINKS):    #TODO: temporary
        return
        
    res = requests.get(URL)
    links_on_url = []
    print(f"\tINFO: processing link {link_nr}, code = {res.status_code}, URL = {URL}")

    if(res.status_code == 404): #TODO: will miss any important links on 404 sites.
        return

    for link in BeautifulSoup(res.text, 'html.parser').find_all("a"):
        if link.has_attr('href'):
            link_text = link["href"]
            if(link_text.startswith(IN_SCOPE) or link_text.startswith("/")):
                blacklisted_extension = False
                for extension in DISALLOWED_FILE_EXTENSIONS: #Filter out URL's with disallowed file extensions
                    if(link_text.endswith(extension)):
                        blacklisted_extension = True
                        break

                if(not blacklisted_extension): 
                    to_visit = None
                    if(link_text.startswith("/")):    #Handle relative links.
                        to_visit = ROOT_URL[:-1] + link_text if(ROOT_URL.endswith("/")) else ROOT_URL + link_text   #domain + the relative link  TODO: always assumes a relative URL start with /
                    else: to_visit = link_text

                    #If path is blacklisted
                    path_is_blacklisted = False
                    for bad in OUT_OF_SCOPE:
                        if(to_visit.startswith(IN_SCOPE + bad)):
                            path_is_blacklisted = True
                            break
                            
                    if(not path_is_blacklisted):
                        if(to_visit not in SITE_LINKS): #If not already visited, visit link and extract recursively
                            SITE_LINKS.append(to_visit)
                            #global LINK_NR
                            LINK_NR += 1
                            #print(f"\t\tDEBUG: link I will visit now: {to_visit}")
                            build_sitemap(to_visit, LINK_NR)



#TODO: Time measruement for how long it takes to extract all links
if __name__=="__main__":
    #Enumerate the website structure/sitemap
    start_URL = "https://cry-of-fear.fandom.com/wiki/Cry_of_Fear_Wiki"
    build_sitemap(start_URL, LINK_NR)
    site_links_string = "\n".join(SITE_LINKS)
    #print(f"\nDEBUG: Website complete sitemap:\n\n{site_links_string}")

    #Build the lists which will contain all words/phrases
    delimiter = " "
    words1 = []
    words2 = []
    words3 = []
    words4 = []
    for i, link in enumerate(SITE_LINKS):
        print(f"INFO: Extracting from link nr {i}: \"{link}\":")
        if(i <= 10000):
            link_contents = scrape_site(link)
            words1 += (to_wordlist(link_contents, 1, delimiter))
            words2 += (to_wordlist(link_contents, 2, delimiter))
            words3 += (to_wordlist(link_contents, 3, delimiter))
            words4 += (to_wordlist(link_contents, 4, delimiter))
            
            #print(f"DEBUG: here is what's returned from scrape_site(): \n\n{link_contents}")

    #Remove duplicates
    words1 = list(set(words1))
    words2 = list(set(words2))
    words3 = list(set(words3))
    words4 = list(set(words4))

    #Write the lists to files
    write_wordlist("1_words.txt", "\n".join(words1))
    write_wordlist("2_words.txt", "\n".join(words2))
    write_wordlist("3_words.txt", "\n".join(words3))
    write_wordlist("4_words.txt", "\n".join(words4))
        


#    testing_list = [["One", "word", "phrases"], ["Now we're", "starting two", "word phrases"], ["Three word phrases", "are now incoming", "so brace yourself!"], ["11 12 13 14", "21 22 23 24", "31 32 33 34"]]
#    single_words = to_wordlist(testing_list, 1, ' ')
#    print(f"\nDEBUG: starting doulbe words now\n")
#    double_words = to_wordlist(testing_list, 2, ' ')
#    print(f"\nDEBUG: starting TRIPLE words now\n")
#    tripple_words = to_wordlist(testing_list, 3, ' ')


